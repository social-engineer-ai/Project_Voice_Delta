"""Seed a handful of realistic sample bills for demo / testing.

Creates ~10 bills spread across today, yesterday, earlier this week,
and earlier this month, with a mix of customers / dalals /
transporters / date varieties so every report filter has non-empty
results.

Run AFTER init_db, seed_dates_products.py, and seed_dalals_transporters.py:
    python -m app.db.init_db
    python scripts/seed_dates_products.py
    python scripts/seed_dalals_transporters.py
    python scripts/seed_sample_bills.py

Idempotent by bill_number prefix: removes any existing SEED-* bills
before inserting the current seed set, so reruns produce deterministic
data.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Bill, BillItem, Dalal, Product, Transporter, User
from app.db.session import SessionLocal


def _ensure_demo_user(db) -> User:
    user = db.query(User).filter(User.telegram_username == "demo_seed").first()
    if user:
        return user
    user = User(telegram_chat_id=1, telegram_username="demo_seed",
                display_name="Demo Seed User", security_threshold="off")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mk_bill(
    db, user: User, *, bill_number: str, customer: str, days_ago: int,
    dalal_name: str | None, dalali_pct: float,
    transporter_name: str, bhada: float,
    items: list[tuple[str, float, float, str]],  # (product, qty, rate, unit)
) -> None:
    subtotal = 0.0
    bill_date = datetime.utcnow() - timedelta(days=days_ago)
    bill = Bill(
        user_id=user.id,
        bill_number=bill_number,
        customer_name=customer,
        bill_date=bill_date,
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


SAMPLE_BILLS: list[dict] = [
    # ---- Today ----
    dict(bill_number="SEED-001", customer="Rajesh", days_ago=0,
         dalal_name="Praveen", dalali_pct=1.5,
         transporter_name="Sharma Transport", bhada=500,
         items=[("Date Ajwa", 5, 2800, "carton")]),
    dict(bill_number="SEED-002", customer="Mukesh", days_ago=0,
         dalal_name="Praveen", dalali_pct=1.5,
         transporter_name="Maruti Transport", bhada=800,
         items=[("Date Crown Fard", 10, 3000, "carton"),
                ("Date Medjool", 3, 4200, "box")]),
    dict(bill_number="SEED-003", customer="Suresh Bhai", days_ago=0,
         dalal_name=None, dalali_pct=0,
         transporter_name="Self", bhada=0,
         items=[("Date Medjool", 3, 4200, "box")]),
    dict(bill_number="SEED-004", customer="Bunty", days_ago=0,
         dalal_name="Kamlesh", dalali_pct=2.0,
         transporter_name="Sharma Transport", bhada=400,
         items=[("Date Tetco", 4, 2200, "carton"),
                ("Date Ajwa", 2, 2800, "carton")]),
    dict(bill_number="SEED-005", customer="Sharma ji", days_ago=0,
         dalal_name=None, dalali_pct=0,
         transporter_name="Yadav Roadways", bhada=600,
         items=[("Date Crown Premium Fard", 6, 3500, "carton")]),

    # ---- Yesterday ----
    dict(bill_number="SEED-006", customer="Rajesh", days_ago=1,
         dalal_name="Praveen", dalali_pct=1.5,
         transporter_name="Sharma Transport", bhada=500,
         items=[("Date Safawi", 8, 2600, "carton")]),
    dict(bill_number="SEED-007", customer="Dinesh", days_ago=1,
         dalal_name="Kamlesh", dalali_pct=2.0,
         transporter_name="Maruti Transport", bhada=500,
         items=[("Date Mabroom", 5, 2800, "box")]),

    # ---- 3 days ago (still this week) ----
    dict(bill_number="SEED-008", customer="Mukesh", days_ago=3,
         dalal_name="Suresh", dalali_pct=1.0,
         transporter_name="Sharma Transport", bhada=700,
         items=[("Date Kimia", 12, 3200, "carton")]),

    # ---- 6 days ago (borderline: in this_week if today is weekday high) ----
    dict(bill_number="SEED-009", customer="Rajesh", days_ago=6,
         dalal_name=None, dalali_pct=0,
         transporter_name="Self", bhada=0,
         items=[("Date Jahidi", 4, 2400, "carton")]),

    # ---- 12 days ago (this month, not this week) ----
    dict(bill_number="SEED-010", customer="Bunty", days_ago=12,
         dalal_name="Praveen", dalali_pct=1.5,
         transporter_name="Maruti Transport", bhada=900,
         items=[("Date Royal Dessert", 6, 4500, "carton")]),
]


def seed_bills() -> None:
    db = SessionLocal()
    try:
        user = _ensure_demo_user(db)

        # Purge any existing SEED-* bills + items so reruns stay idempotent.
        existing_ids = [
            b.id for b in db.query(Bill).filter(Bill.bill_number.like("SEED-%")).all()
        ]
        if existing_ids:
            db.query(BillItem).filter(BillItem.bill_id.in_(existing_ids)).delete(
                synchronize_session=False
            )
            db.query(Bill).filter(Bill.id.in_(existing_ids)).delete(
                synchronize_session=False
            )

        for spec in SAMPLE_BILLS:
            _mk_bill(db, user, **spec)
        db.commit()

        rows = db.query(Bill).filter(Bill.bill_number.like("SEED-%")).order_by(Bill.bill_date.desc()).all()
        print(f"Seeded {len(rows)} sample bills:")
        print()
        fmt = "  {:<10} {:<12} {:<14} {:<18} {:<18} {:>8} {:>10}"
        print(fmt.format("Bill#", "Date", "Customer", "Dalal", "Transporter", "Bhada", "Total"))
        print("  " + "-" * 95)
        for b in rows:
            print(fmt.format(
                b.bill_number,
                b.bill_date.strftime("%d-%b %H:%M"),
                (b.customer_name or "")[:14],
                (b.dalal or "-")[:18],
                (b.transporter or "-")[:18],
                f"{b.bhada:,.0f}",
                f"{b.total:,.0f}",
            ))
    finally:
        db.close()


if __name__ == "__main__":
    seed_bills()
