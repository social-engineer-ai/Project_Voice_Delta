"""Report / summary service.

Added 2026-04-23 on the Dates branch to back the `summary` intent and
the `/report` slash command. Runs SQLAlchemy queries against the Bill
table and returns a ReportResult the formatters turn into a chat
message, a PDF, and an HTML file.

Supported subjects:
    'dalal'        - filter by Bill.dalal_id (or fallback to name ILIKE)
    'transporter'  - filter by Bill.transporter_id (or fallback to name)
    'customer'     - filter by Bill.customer_name ILIKE (no entity yet)
    'overall'      - no filter

Supported periods (resolved to [start, end) datetimes):
    today           - 00:00 today -> 00:00 tomorrow
    yesterday       - 00:00 yesterday -> 00:00 today
    this_week       - Monday 00:00 -> next Monday 00:00
    last_7_days     - now-7d -> now
    this_month      - day 1 00:00 -> first of next month 00:00
    last_30_days    - now-30d -> now
    custom          - explicit from/to dates

Customer and "anyone not in catalog" names do name-substring matching
(case-insensitive) instead of failing; the user typically types a
partial name. Dalal / transporter first try the catalog via
fuzzy-match (threshold from bill.py), falling back to name substring
only if catalog lookup fails.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Bill, Dalal, Transporter


VALID_SUBJECTS = frozenset({"dalal", "transporter", "customer", "overall"})
VALID_PERIODS = frozenset({
    "today", "yesterday", "this_week", "last_7_days",
    "this_month", "last_30_days", "custom",
})


@dataclass
class ReportResult:
    """Aggregated report data, rendered downstream into message / PDF / HTML."""
    subject: str              # 'dalal' | 'transporter' | 'customer' | 'overall'
    filter_name: Optional[str]  # canonical name after fuzzy match, or None
    filter_matched: bool      # True if the spoken filter resolved to a catalog entity
    period_label: str         # human-readable: 'Today', 'Last 7 days', '20-23 Apr'
    period_key: str           # original key: 'today', 'last_7_days', 'custom', ...
    start: datetime
    end: datetime             # half-open: [start, end)

    bill_count: int = 0
    subtotal: float = 0.0
    tax_amount: float = 0.0
    bhada: float = 0.0
    dalali_amount: float = 0.0  # meaningful for dalal subject
    total: float = 0.0          # sum of Bill.total
    bills: list[Bill] = field(default_factory=list)

    # Breakdowns — useful for overall reports.
    by_dalal: list[tuple[str, int, float]] = field(default_factory=list)         # (name, count, total)
    by_transporter: list[tuple[str, int, float]] = field(default_factory=list)   # (name, count, total)


# ---------------- Period resolution ----------------

def _today() -> date:
    return datetime.utcnow().date()


def resolve_period(
    period: str,
    from_str: Optional[str] = None,
    to_str: Optional[str] = None,
) -> tuple[datetime, datetime, str]:
    """Given a period key (and optional from/to for 'custom'), return
    (start, end, label). `end` is exclusive (half-open range) so the
    SQL filter reads `bill_date < end`."""
    if period == "today":
        start = datetime.combine(_today(), datetime.min.time())
        end = start + timedelta(days=1)
        return start, end, "Today"

    if period == "yesterday":
        end = datetime.combine(_today(), datetime.min.time())
        start = end - timedelta(days=1)
        return start, end, "Yesterday"

    if period == "this_week":
        today = _today()
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, datetime.min.time())
        end = start + timedelta(days=7)
        return start, end, "This week"

    if period == "last_7_days":
        now = datetime.utcnow()
        start = now - timedelta(days=7)
        return start, now, "Last 7 days"

    if period == "this_month":
        today = _today()
        start = datetime.combine(today.replace(day=1), datetime.min.time())
        # First of next month: add ~31 days then snap to day 1.
        nxt = (start + timedelta(days=32)).replace(day=1)
        return start, nxt, f"{today.strftime('%B %Y')}"

    if period == "last_30_days":
        now = datetime.utcnow()
        start = now - timedelta(days=30)
        return start, now, "Last 30 days"

    if period == "custom":
        if not from_str or not to_str:
            raise ValueError("custom period requires from and to dates")
        start = datetime.fromisoformat(from_str)
        end_date = datetime.fromisoformat(to_str) + timedelta(days=1)
        label = f"{start.strftime('%d %b')} — {(end_date - timedelta(days=1)).strftime('%d %b %Y')}"
        return start, end_date, label

    raise ValueError(f"unknown period: {period!r}")


# ---------------- Query helpers ----------------

def _base_bill_query(db: Session, start: datetime, end: datetime):
    return (
        db.query(Bill)
        .filter(Bill.bill_date >= start, Bill.bill_date < end)
        .order_by(Bill.bill_date.desc())
    )


def _resolve_filter_entity(
    db: Session, subject: str, filter_name: Optional[str]
) -> tuple[Optional[object], bool]:
    """Try to resolve the filter name to a Dalal / Transporter catalog
    row via fuzzy-match (reusing the bill handler's matchers). Returns
    (entity_or_None, matched_bool). For 'customer' and 'overall'
    subjects, always returns (None, False)."""
    if not filter_name:
        return None, False
    if subject == "dalal":
        from app.handlers.bill import _fuzzy_match_dalal
        row = _fuzzy_match_dalal(db, filter_name)
        return row, row is not None
    if subject == "transporter":
        from app.handlers.bill import _fuzzy_match_transporter
        row = _fuzzy_match_transporter(db, filter_name)
        return row, row is not None
    return None, False


def _aggregate(bills: list[Bill]) -> dict:
    return {
        "bill_count": len(bills),
        "subtotal": round(sum(b.subtotal for b in bills), 2),
        "tax_amount": round(sum(b.tax_amount for b in bills), 2),
        "bhada": round(sum(b.bhada or 0.0 for b in bills), 2),
        "dalali_amount": round(sum(b.dalali_amount or 0.0 for b in bills), 2),
        "total": round(sum(b.total for b in bills), 2),
    }


def _top_by_attr(bills: list[Bill], attr: str, limit: int = 5) -> list[tuple[str, int, float]]:
    buckets: dict[str, list[Bill]] = {}
    for b in bills:
        key = getattr(b, attr) or "(none)"
        buckets.setdefault(key, []).append(b)
    rows = [(name, len(bs), round(sum(x.total for x in bs), 2)) for name, bs in buckets.items()]
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows[:limit]


# ---------------- Public entry points ----------------

def run_report(
    db: Session,
    subject: str,
    filter_name: Optional[str],
    period: str,
    from_str: Optional[str] = None,
    to_str: Optional[str] = None,
) -> ReportResult:
    """Dispatch based on subject; return a fully-populated ReportResult."""
    if subject not in VALID_SUBJECTS:
        raise ValueError(f"invalid subject {subject!r}; expected one of {VALID_SUBJECTS}")
    if period not in VALID_PERIODS:
        raise ValueError(f"invalid period {period!r}; expected one of {VALID_PERIODS}")

    start, end, label = resolve_period(period, from_str, to_str)

    entity, matched = _resolve_filter_entity(db, subject, filter_name)
    q = _base_bill_query(db, start, end)

    if subject == "dalal":
        if entity is not None:
            q = q.filter(Bill.dalal_id == entity.id)
            canonical = entity.name
        elif filter_name:
            q = q.filter(Bill.dalal.ilike(f"%{filter_name}%"))
            canonical = filter_name
        else:
            canonical = None
    elif subject == "transporter":
        if entity is not None:
            q = q.filter(Bill.transporter_id == entity.id)
            canonical = entity.name
        elif filter_name:
            q = q.filter(Bill.transporter.ilike(f"%{filter_name}%"))
            canonical = filter_name
        else:
            canonical = None
    elif subject == "customer":
        if filter_name:
            q = q.filter(Bill.customer_name.ilike(f"%{filter_name}%"))
            canonical = filter_name
        else:
            canonical = None
    else:  # overall
        canonical = None

    bills = q.all()
    agg = _aggregate(bills)

    result = ReportResult(
        subject=subject,
        filter_name=canonical,
        filter_matched=matched,
        period_label=label,
        period_key=period,
        start=start,
        end=end,
        bills=bills,
        **agg,
    )

    # Breakdowns: for overall reports, show top 5 by dalal and top 5
    # by transporter so the shopkeeper can spot-check. For subject-
    # specific reports these are redundant.
    if subject == "overall" and bills:
        result.by_dalal = _top_by_attr(bills, "dalal")
        result.by_transporter = _top_by_attr(bills, "transporter")

    return result
