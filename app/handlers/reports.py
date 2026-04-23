"""Report handler — both voice/text intent and /report slash command.

Added 2026-04-23 on the Dates branch. Routes intent=summary and the
`/report` command to the reports service, renders chat/PDF/HTML, and
sends all three attachments.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from app.db.models import User
from app.db.session import SessionLocal
from app.services.classify import IntentClassification
from app.services.report_format import (
    format_report_message,
    render_report_html,
    render_report_pdf,
)
from app.services.reports import VALID_PERIODS, VALID_SUBJECTS, run_report

logger = logging.getLogger(__name__)


def _default_period() -> str:
    return "today"


async def _run_and_reply(
    update: Update,
    subject: str,
    filter_name: Optional[str],
    period: str,
    from_str: Optional[str] = None,
    to_str: Optional[str] = None,
) -> None:
    """Shared report-generation + reply path. Used by both voice
    (handle_summary_intent) and slash (/report)."""
    if subject not in VALID_SUBJECTS:
        await update.message.reply_text(
            f"Subject galat hai: '{subject}'. Options: dalal, transporter, "
            f"customer, overall.\n\n"
            f"Subject गलत है: '{subject}'। Options: dalal, transporter, "
            f"customer, overall।"
        )
        return
    if period not in VALID_PERIODS:
        await update.message.reply_text(
            f"Period galat hai: '{period}'. Options: today, yesterday, "
            f"this_week, last_7_days, this_month, last_30_days, custom.\n\n"
            f"Period गलत है: '{period}'।"
        )
        return

    db = SessionLocal()
    try:
        result = run_report(
            db, subject=subject, filter_name=filter_name,
            period=period, from_str=from_str, to_str=to_str,
        )
        # 1. Chat summary.
        await update.message.reply_text(
            format_report_message(result), parse_mode="Markdown",
        )

        if result.bill_count == 0:
            # Skip PDF + HTML when there's nothing to show.
            return

        # 2. PDF.
        tmpdir = Path(tempfile.mkdtemp(prefix="report_"))
        subject_slug = result.subject
        filter_slug = (
            result.filter_name.replace(" ", "_") if result.filter_name else "all"
        )
        base = f"report_{subject_slug}_{filter_slug}_{result.period_key}"
        pdf_path = tmpdir / f"{base}.pdf"
        html_path = tmpdir / f"{base}.html"
        render_report_pdf(result, pdf_path)
        render_report_html(result, html_path)

        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=pdf_path.name,
                caption="Report PDF",
            )
        with open(html_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=html_path.name,
                caption="Report HTML (open in browser)",
            )
    except ValueError as e:
        logger.warning(f"Report failed: {e}")
        await update.message.reply_text(f"Report nahi bana: {e}")
    except Exception as e:
        logger.exception(f"Report handler error: {e}")
        await update.message.reply_text(
            "Report banane mein dikkat hui. Dobara try kariye."
        )
    finally:
        db.close()


async def handle_summary_intent(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user: User, intent: IntentClassification,
) -> None:
    """Route intent=summary to the reports pipeline. Defaults where
    the classifier left fields null: subject='overall', period='today'."""
    subject = intent.report_subject or "overall"
    period = intent.report_period or _default_period()
    await _run_and_reply(
        update,
        subject=subject,
        filter_name=intent.report_filter,
        period=period,
        from_str=intent.report_from,
        to_str=intent.report_to,
    )


async def report_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """/report <subject> [filter] [period]  or
    /report <subject> [filter] <from_iso> <to_iso> for custom range.

    Examples:
        /report dalal Praveen today
        /report dalal Praveen 2026-04-20 2026-04-23
        /report transporter Sharma this_week
        /report customer Rajesh last_30_days
        /report overall today
        /report overall
        /report

    Argument parsing intentionally simple — positional only, no flags.
    Last token(s) get special-cased: if it's a recognised period key,
    it's the period; if the last two tokens are ISO dates, it's a
    custom range; otherwise the remaining tokens form the filter name.
    """
    args = list(context.args or [])

    if not args:
        # Zero-arg shortcut: overall today.
        await _run_and_reply(update, "overall", None, "today")
        return

    subject = args[0].lower()
    rest = args[1:]
    filter_name: Optional[str] = None
    period = "today"
    from_str: Optional[str] = None
    to_str: Optional[str] = None

    # Two trailing ISO dates -> custom period.
    if len(rest) >= 2 and _looks_like_iso_date(rest[-2]) and _looks_like_iso_date(rest[-1]):
        from_str, to_str = rest[-2], rest[-1]
        period = "custom"
        rest = rest[:-2]
    # Single trailing token matching a period key -> that period.
    elif rest and rest[-1].lower() in VALID_PERIODS and rest[-1].lower() != "custom":
        period = rest[-1].lower()
        rest = rest[:-1]

    if rest:
        filter_name = " ".join(rest).strip()
        if subject == "overall":
            # /report overall Praveen today doesn't make sense; the
            # classifier would reroute but slash users may try it —
            # politely ignore the filter for overall.
            logger.info("Filter provided for overall subject; ignoring.")
            filter_name = None

    await _run_and_reply(
        update, subject=subject, filter_name=filter_name,
        period=period, from_str=from_str, to_str=to_str,
    )


def _looks_like_iso_date(token: str) -> bool:
    if len(token) != 10:
        return False
    if token[4] != "-" or token[7] != "-":
        return False
    try:
        int(token[:4]); int(token[5:7]); int(token[8:10])
        return True
    except ValueError:
        return False
