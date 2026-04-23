"""Smoke test the report pipeline end-to-end without Telegram.

Creates three demo bills (today), then runs four reports against them
(overall/today, dalal Praveen/today, transporter Sharma/this_week,
customer Rajesh/this_month), rendering chat text + PDF + HTML for
each. Prints paths so the artifacts can be opened for inspection.

Usage:
    python scripts/smoke_report.py
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Bill, BillItem, Dalal, Product, Transporter, User
from app.db.session import SessionLocal
from app.services.report_format import (
    format_report_message,
    render_report_html,
    render_report_pdf,
)
from app.services.reports import run_report


def _ensure_user(db) -> User:
    user = db.query(User).first()
    if user:
        return user
    user = User(telegram_chat_id=1, telegram_username="smoke")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_bill(
    db, user, bill_number: str, customer: str,
    dalal_name: str | None, dalali_pct: float,
    transporter_name: str, bhada: float,
    items: list[tuple[str, float, float, str]],
) -> Bill:
    """Create a Bill + items for the smoke test. Links to catalog rows."""
    subtotal = 0.0
    bill = Bill(
        user_id=user.id,
        bill_number=bill_number,
        customer_name=customer,
        bill_date=datetime.utcnow(),
        subtotal=0.0, tax_amount=0.0, total=0.0,
        status="created",
    )
    if dalal_name:
        d = db.query(Dalal).filter(Dalal.name == dalal_name).first()
        if d:
            bill.dalal_id = d.id
        bill.dalal = dalal_name
    else:
        bill.dalal = "None"
    bill.dalali_percent = dalali_pct

    t = db.query(Transporter).filter(Transporter.name == transporter_name).first()
    if t:
        bill.transporter_id = t.id
    bill.transporter = transporter_name
    bill.bhada = bhada

    db.add(bill)
    db.flush()

    for pname, qty, rate, unit in items:
        product = db.query(Product).filter(Product.name == pname).first()
        amount = qty * rate
        subtotal += amount
        db.add(BillItem(
            bill_id=bill.id,
            product_id=product.id if product else None,
            product_name=pname,
            quantity=qty, unit=unit, rate=rate, amount=amount,
            gst_rate=18.0,
        ))

    bill.subtotal = round(subtotal, 2)
    bill.tax_amount = round(subtotal * 0.18, 2)
    bill.dalali_amount = round(subtotal * dalali_pct / 100, 2)
    bill.total = round(bill.subtotal + bill.tax_amount + bill.bhada, 2)
    db.commit()
    db.refresh(bill)
    return bill


def main() -> int:
    db = SessionLocal()
    try:
        user = _ensure_user(db)

        # Clean up any previous smoke bills so reruns stay deterministic.
        db.query(BillItem).filter(
            BillItem.bill_id.in_(
                db.query(Bill.id).filter(Bill.bill_number.like("SMOKE-%"))
            )
        ).delete(synchronize_session=False)
        db.query(Bill).filter(Bill.bill_number.like("SMOKE-%")).delete()
        db.commit()

        _make_bill(
            db, user, "SMOKE-001", "Rajesh",
            dalal_name="Praveen", dalali_pct=1.5,
            transporter_name="Sharma Transport", bhada=500,
            items=[("Date Ajwa", 5, 2800, "carton")],
        )
        _make_bill(
            db, user, "SMOKE-002", "Mukesh",
            dalal_name="Praveen", dalali_pct=1.5,
            transporter_name="Sharma Transport", bhada=600,
            items=[
                ("Date Crown Fard", 10, 3000, "carton"),
                ("Date Medjool", 3, 4200, "box"),
            ],
        )
        _make_bill(
            db, user, "SMOKE-003", "Rajesh",
            dalal_name="Kamlesh", dalali_pct=2.0,
            transporter_name="Maruti Transport", bhada=400,
            items=[("Date Tetco", 4, 2200, "carton")],
        )

        tmpdir = Path(tempfile.mkdtemp(prefix="smoke_report_"))
        print(f"Artifacts -> {tmpdir}")
        print()

        scenarios = [
            ("overall", None, "today"),
            ("dalal", "Praveen", "today"),
            ("transporter", "Sharma Transport", "this_week"),
            ("customer", "Rajesh", "this_month"),
        ]

        for subject, filt, period in scenarios:
            print("=" * 60)
            result = run_report(db, subject, filt, period)
            print(format_report_message(result))
            print()

            slug = f"{subject}_{(filt or 'all').replace(' ', '_')}_{period}"
            pdf_path = tmpdir / f"{slug}.pdf"
            html_path = tmpdir / f"{slug}.html"
            render_report_pdf(result, pdf_path)
            render_report_html(result, html_path)
            print(f"  PDF : {pdf_path} ({pdf_path.stat().st_size} bytes)")
            print(f"  HTML: {html_path} ({html_path.stat().st_size} bytes)")
            print()

        print("Smoke complete. Open the tmpdir above to inspect PDFs and HTMLs.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
