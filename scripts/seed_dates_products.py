"""Populate the Products table with a dates-trader catalog.

Used by the `Dates` branch bill-generation prototype. Run after
`python -m app.db.init_db` to populate the initial product set.

The two items AV specified are first. The rest are commonly traded
dates varieties in India / Gulf markets, included so the demo can
exercise fuzzy-matching across a realistic catalog. Swap this file
for a different shop's catalog on a different branch (e.g.,
`scripts/seed_cement_products.py` for building materials).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Product
from app.db.session import SessionLocal


# Each entry: name, aliases (alternate spellings + likely ASR drift),
# default_unit, gst_rate.
# Aliases are lowercased at match time.
CATALOG: list[dict] = [
    # User-specified
    {
        "name": "Date Crown Fard",
        "aliases": ["date crown fard", "crown fard", "date crown", "crown date",
                    "date crown fardh", "crown phard", "date crown farad"],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Crown Premium Fard",
        "aliases": ["date crown premium fard", "crown premium", "date crown premium",
                    "premium fard", "date crown premium phard",
                    "crown premium farad"],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Jafri",
        "aliases": ["date jafri", "jafri", "jaffri", "jaffari", "jafri dates",
                    "date jaffri", "date jaffari"],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    # Commonly traded varieties (non-exhaustive — edit for your shop).
    {
        "name": "Ajwa Dates",
        "aliases": ["ajwa", "ajwah", "ajwa khajoor", "ajwa dates"],
        "default_unit": "box",
        "gst_rate": 18.0,
    },
    {
        "name": "Mabroom Dates",
        "aliases": ["mabroom", "mabrum", "mabroum"],
        "default_unit": "box",
        "gst_rate": 18.0,
    },
    {
        "name": "Medjool Dates",
        "aliases": ["medjool", "majdool", "majool", "madjool"],
        "default_unit": "box",
        "gst_rate": 18.0,
    },
    {
        "name": "Kimia Dates",
        "aliases": ["kimia", "kimiya"],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Safawi Dates",
        "aliases": ["safawi", "saffawi", "safawi khajoor"],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        created, updated = 0, 0
        for entry in CATALOG:
            existing = db.query(Product).filter(Product.name == entry["name"]).first()
            if existing:
                existing.aliases = entry["aliases"]
                existing.default_unit = entry["default_unit"]
                existing.gst_rate = entry["gst_rate"]
                existing.is_active = 1
                updated += 1
            else:
                db.add(Product(
                    name=entry["name"],
                    aliases=entry["aliases"],
                    default_unit=entry["default_unit"],
                    gst_rate=entry["gst_rate"],
                    is_active=1,
                ))
                created += 1
        db.commit()
        print(f"Seeded dates catalog: {created} created, {updated} updated.")
        # Verify.
        for p in db.query(Product).order_by(Product.id).all():
            print(f"  [{p.id}] {p.name}  unit={p.default_unit}  gst={p.gst_rate}%  aliases={p.aliases}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
