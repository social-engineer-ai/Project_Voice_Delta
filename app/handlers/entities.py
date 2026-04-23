"""Slash-command handlers for Dalal + Transporter catalog management.

Added 2026-04-23 on the Dates branch. Complements the bill-flow
password-gated add: these let the shopkeeper proactively seed the
catalog before making bills, or list what's already there.

Commands (first arg after the command is the password for write ops):
    /add_dalal 121 <name>
    /add_transporter 121 <name>
    /list_dalals
    /list_transporters
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.db.models import Dalal, Transporter
from app.db.session import SessionLocal
from app.handlers.bill import CATALOG_ADD_PASSWORD

logger = logging.getLogger(__name__)


def _parse_add_args(args: list[str]) -> tuple[bool, str | None, str | None]:
    """Return (password_ok, name_or_None, error_message_or_None).

    Expected: first token = password, remaining tokens = entity name.
    Rejects if the password doesn't match or the name is empty.
    """
    if not args:
        return (False, None, (
            "Usage: /add_dalal <password> <name>. "
            "Example: /add_dalal 121 Praveen\n\n"
            "जैसे: /add_dalal 121 Praveen"
        ))
    password = args[0]
    if password != CATALOG_ADD_PASSWORD:
        return (False, None, (
            "Password galat hai. Sahi password pehle bhejo.\n\n"
            "Password गलत है। सही password पहले भेजिए।"
        ))
    name = " ".join(args[1:]).strip()
    if not name:
        return (False, None, (
            "Name nahi mila. Usage: /add_dalal 121 <name>\n\n"
            "Name नहीं मिला। Usage: /add_dalal 121 <name>"
        ))
    return (True, name, None)


async def add_dalal_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    ok, name, err = _parse_add_args(list(context.args or []))
    if not ok:
        await update.message.reply_text(err)
        return
    canonical = name.title()

    db = SessionLocal()
    try:
        existing = db.query(Dalal).filter(Dalal.name == canonical).first()
        if existing:
            if not existing.is_active:
                existing.is_active = 1
                db.commit()
                await update.message.reply_text(
                    f"Dalal '{canonical}' pehle se exist karta tha, "
                    f"reactivate kar diya.\n\n"
                    f"Dalal '{canonical}' पहले से exist करता था, "
                    f"reactivate कर दिया।"
                )
            else:
                await update.message.reply_text(
                    f"Dalal '{canonical}' pehle se catalog mein hai.\n\n"
                    f"Dalal '{canonical}' पहले से catalog में है।"
                )
            return
        row = Dalal(
            name=canonical,
            aliases=[name.lower(), canonical.lower()],
            is_active=1,
        )
        db.add(row)
        db.commit()
        logger.info("Dalal added via slash command: %s", canonical)
        await update.message.reply_text(
            f"Dalal '{canonical}' catalog mein add ho gaya.\n\n"
            f"Dalal '{canonical}' catalog में add हो गया।"
        )
    finally:
        db.close()


async def add_transporter_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    ok, name, err = _parse_add_args(list(context.args or []))
    if not ok:
        # Rewrite the usage example for the transporter command
        # (args parser's example text mentions /add_dalal).
        err = err.replace("/add_dalal", "/add_transporter").replace(
            "Praveen", "Sharma Transport"
        )
        await update.message.reply_text(err)
        return
    canonical = name.title()

    db = SessionLocal()
    try:
        existing = db.query(Transporter).filter(
            Transporter.name == canonical
        ).first()
        if existing:
            if not existing.is_active:
                existing.is_active = 1
                db.commit()
                await update.message.reply_text(
                    f"Transporter '{canonical}' pehle se exist karta tha, "
                    f"reactivate kar diya.\n\n"
                    f"Transporter '{canonical}' पहले से exist करता था, "
                    f"reactivate कर दिया।"
                )
            else:
                await update.message.reply_text(
                    f"Transporter '{canonical}' pehle se catalog mein hai.\n\n"
                    f"Transporter '{canonical}' पहले से catalog में है।"
                )
            return
        row = Transporter(
            name=canonical,
            aliases=[name.lower(), canonical.lower()],
            is_active=1,
        )
        db.add(row)
        db.commit()
        logger.info("Transporter added via slash command: %s", canonical)
        await update.message.reply_text(
            f"Transporter '{canonical}' catalog mein add ho gaya.\n\n"
            f"Transporter '{canonical}' catalog में add हो गया।"
        )
    finally:
        db.close()


async def list_dalals_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    db = SessionLocal()
    try:
        rows = db.query(Dalal).filter(Dalal.is_active == 1).order_by(Dalal.name).all()
    finally:
        db.close()
    if not rows:
        await update.message.reply_text(
            "Koi dalal catalog mein nahi hai abhi.\n\n"
            "कोई दलाल catalog में नहीं है अभी।"
        )
        return
    lines = ["*Active Dalals:*"]
    for d in rows:
        dp = f" ({d.default_percent:g}%)" if d.default_percent else ""
        lines.append(f"  • {d.name}{dp}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def list_transporters_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    db = SessionLocal()
    try:
        rows = (
            db.query(Transporter)
            .filter(Transporter.is_active == 1)
            .order_by(Transporter.name)
            .all()
        )
    finally:
        db.close()
    if not rows:
        await update.message.reply_text(
            "Koi transporter catalog mein nahi hai abhi.\n\n"
            "कोई transporter catalog में नहीं है अभी।"
        )
        return
    lines = ["*Active Transporters:*"]
    for t in rows:
        lines.append(f"  • {t.name}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
