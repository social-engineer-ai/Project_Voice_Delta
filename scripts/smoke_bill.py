"""Smoke test the bill-generation pipeline without Telegram.

Constructs a mock Bill from a hardcoded IntentClassification and
exercises the full render path: DB write, text format, PDF render,
Tally XML generation. Writes the artifacts to a tmp dir and prints
paths so AV can inspect them before the demo.

Usage:
    python scripts/smoke_bill.py
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Bill, BillItem, Product, User
from app.db.session import SessionLocal
from app.services.bill_format import format_bill_message, render_bill_pdf
from app.services.tally_export import build_sales_voucher_xml, write_sales_voucher_xml


def main() -> int:
    db = SessionLocal()
    try:
        # Ensure a test user exists.
        user = db.query(User).first()
        if not user:
            user = User(telegram_chat_id=999999, telegram_username="smoke_test")
            db.add(user)
            db.commit()
            db.refresh(user)

        # Fuzzy-match products. Alternatively, look up by seeded name.
        crown_fard = db.query(Product).filter(Product.name == "Date Crown Fard").first()
        crown_premium = db.query(Product).filter(
            Product.name == "Date Crown Premium Fard"
        ).first()
        ajwa = db.query(Product).filter(Product.name == "Ajwa Dates").first()

        if not crown_fard:
            print("Products not seeded. Run: python scripts/seed_dates_products.py")
            return 1

        # Build a mock bill with 2 line items (multi-item test).
        bill = Bill(
            user_id=user.id,
            bill_number=f"DEMO-{datetime.utcnow().strftime('%Y%m%d')}-SMOKE",
            customer_name="Sharma Ji",
            bill_date=datetime.utcnow(),
        )
        db.add(bill)
        db.flush()

        item1 = BillItem(
            bill_id=bill.id,
            product_id=crown_premium.id if crown_premium else None,
            product_name=crown_premium.name if crown_premium else "Date Crown Premium Fard",
            quantity=3, unit="carton", rate=3500, amount=10500,
            gst_rate=18.0,
        )
        item2 = BillItem(
            bill_id=bill.id,
            product_id=ajwa.id if ajwa else None,
            product_name=ajwa.name if ajwa else "Ajwa Dates",
            quantity=2, unit="box", rate=2800, amount=5600,
            gst_rate=18.0,
        )
        db.add(item1)
        db.add(item2)

        # Compute totals.
        subtotal = item1.amount + item2.amount
        bill.subtotal = subtotal
        bill.tax_amount = round(subtotal * 0.18, 2)
        bill.total = round(subtotal + bill.tax_amount, 2)

        db.commit()
        db.refresh(bill)
        # Trigger relationship load.
        _ = bill.items

        # 1. Message.
        print("=" * 60)
        print("TELEGRAM MESSAGE PREVIEW")
        print("=" * 60)
        print(format_bill_message(bill))
        print()

        # 2. PDF.
        tmpdir = Path(tempfile.mkdtemp(prefix="smoke_bill_"))
        pdf_path = tmpdir / f"{bill.bill_number}.pdf"
        render_bill_pdf(bill, pdf_path)
        print(f"PDF written: {pdf_path}")
        print(f"  size: {pdf_path.stat().st_size} bytes")
        print()

        # 3. Tally XML.
        xml_path = tmpdir / f"{bill.bill_number}.xml"
        write_sales_voucher_xml(bill, xml_path)
        print(f"Tally XML written: {xml_path}")
        print(f"  size: {xml_path.stat().st_size} bytes")
        print()
        print("=" * 60)
        print("TALLY XML CONTENT (first 2000 chars)")
        print("=" * 60)
        xml_str = xml_path.read_text(encoding="utf-8")
        print(xml_str[:2000])
        print()
        print("=" * 60)
        print(f"Artifacts in: {tmpdir}")
        print("Open the PDF to check layout; open the XML to review Tally structure.")
        print("=" * 60)
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
