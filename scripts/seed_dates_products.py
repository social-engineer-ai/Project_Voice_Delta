"""Populate the Products table with a dates-trader catalog.

Used by the `Dates` branch bill-generation prototype. Run after
`python -m app.db.init_db` to populate the initial product set.

Naming convention (set 2026-04-22, second pass): every canonical name
starts with "Date " so the printed bill always reads "Date Ajwa",
"Date Crown Fard", etc., regardless of whether the shopkeeper said
"Ajwa" or "Date Ajwa" in the voice command. The aliases for each
product include both forms.

Idempotency: running this script deactivates every existing Product
row not in CATALOG (sets is_active=0), then upserts each CATALOG
entry as is_active=1. Existing BillItem.product_id FKs remain intact
so historical bills continue to link to the product rows they were
created against, even if that product later gets renamed.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Product
from app.db.session import SessionLocal


# Each entry: name (canonical, with "Date " prefix), aliases, default_unit,
# gst_rate. Aliases cover bare name + "date <name>" + common ASR drift.
CATALOG: list[dict] = [
    # User-specified branded items.
    {
        "name": "Date Crown Fard",
        "aliases": [
            "date crown fard", "crown fard", "date crown", "crown date",
            "date crown fardh", "crown phard", "date crown farad",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Crown Premium Fard",
        "aliases": [
            "date crown premium fard", "crown premium", "date crown premium",
            "premium fard", "date crown premium phard", "crown premium farad",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Jafri",
        "aliases": [
            "date jafri", "jafri", "jaffri", "jaffari", "jafri dates",
            "date jaffri", "date jaffari",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    # User-added 2026-04-22 second pass.
    {
        "name": "Date Al-Jafri",
        "aliases": [
            "date al-jafri", "date al jafri", "al-jafri", "al jafri",
            "aljafri", "al jaffri", "aljaffri",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Royal Dessert",
        "aliases": [
            "date royal dessert", "royal dessert", "royal desert",
            "date royal desert", "royal", "date royal",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Buman",
        "aliases": [
            "date buman", "buman", "booman", "boman", "date booman",
            # ASR drift: saaras:v3 transcribes "Buman" as "women" on
            # some takes (acoustic confusion bu->wo, man->men). Include
            # the misheard form and several phonetic neighbours so the
            # fuzzy-match resolves cleanly instead of sending the line
            # to an unmatched-product rejection.
            "women", "date women", "vomen", "bomen", "booman dates",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Ajwa",
        "aliases": [
            "date ajwa", "ajwa", "ajwah", "ajwa dates", "ajwa khajoor",
            "date ajwah",
        ],
        "default_unit": "box",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Saudi",
        "aliases": [
            "date saudi", "saudi", "saudi dates", "saudi khajoor",
            "date saudia",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Tetco",
        "aliases": [
            "date tetco", "tetco", "tetco dates", "tetko", "date tetko",
            # ASR drift: saaras:v3 returns "टेट को" (two words) on some
            # takes, which the classifier then transliterates as
            # "Tet ko" / "Tet Ko". Covering both the joined and spaced
            # forms so the fuzzy-match threshold (0.70) is comfortably
            # exceeded.
            "tet ko", "tet-ko", "tetko dates", "tatko", "tat ko",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Jahidi",
        "aliases": [
            "date jahidi", "jahidi", "jahedi", "zahidi", "date zahidi",
            "jahidi dates",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    # Previously seeded varieties renamed to canonical "Date <X>" form so
    # the printed bill always carries the prefix.
    {
        "name": "Date Mabroom",
        "aliases": [
            "date mabroom", "mabroom", "mabrum", "mabroum", "mabroom dates",
        ],
        "default_unit": "box",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Medjool",
        "aliases": [
            "date medjool", "medjool", "majdool", "majool", "madjool",
            "medjool dates", "date majdool",
        ],
        "default_unit": "box",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Kimia",
        "aliases": [
            "date kimia", "kimia", "kimiya", "kimia dates",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
    {
        "name": "Date Safawi",
        "aliases": [
            "date safawi", "safawi", "saffawi", "safawi dates",
            "safawi khajoor",
        ],
        "default_unit": "carton",
        "gst_rate": 18.0,
    },
]


def seed() -> None:
    catalog_names = {entry["name"] for entry in CATALOG}

    db = SessionLocal()
    try:
        # Deactivate any existing products that are no longer in the catalog.
        # Keeps the rows around so historical BillItem.product_id FKs don't
        # dangle, but excludes them from future fuzzy-matching (which
        # filters is_active == 1).
        orphaned = (
            db.query(Product)
            .filter(~Product.name.in_(catalog_names))
            .all()
        )
        deactivated = 0
        for p in orphaned:
            if p.is_active:
                p.is_active = 0
                deactivated += 1

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

        print(f"Seeded dates catalog: {created} created, {updated} updated, "
              f"{deactivated} old rows deactivated.")
        print()
        print("Active catalog:")
        for p in db.query(Product).filter(Product.is_active == 1).order_by(Product.id).all():
            print(f"  [{p.id}] {p.name}  unit={p.default_unit}  gst={p.gst_rate}%  "
                  f"aliases={p.aliases}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
