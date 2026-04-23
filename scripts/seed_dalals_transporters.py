"""Seed a starter set of Dalal and Transporter entities.

Run after `python -m app.db.init_db` alongside `seed_dates_products.py`.
Gives the Dates demo something to fuzzy-match against from command one;
the shopkeeper can still add more via `/add_dalal 121 <name>` or
`/add_transporter 121 <name>` during the demo or live use.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Dalal, Transporter
from app.db.session import SessionLocal


DALALS: list[dict] = [
    {
        "name": "Praveen",
        "aliases": ["praveen", "parveen", "parween", "praween", "praveen dalal"],
        "default_percent": 1.5,
    },
    {
        "name": "Kamlesh",
        "aliases": ["kamlesh", "kamal", "kamlesh dalal"],
        "default_percent": 2.0,
    },
    {
        "name": "Suresh",
        "aliases": ["suresh", "sureshbhai", "suresh dalal"],
        "default_percent": 1.0,
    },
]

TRANSPORTERS: list[dict] = [
    {
        "name": "Sharma Transport",
        "aliases": [
            "sharma transport", "sharma", "sharma ji transport",
            "sharma trasport",  # ASR drift
        ],
    },
    {
        "name": "Maruti Transport",
        "aliases": [
            "maruti transport", "maruti", "maruti trasport", "maruthi transport",
        ],
    },
    {
        "name": "Yadav Roadways",
        "aliases": [
            "yadav roadways", "yadav", "yadav transport", "yadavji",
        ],
    },
    {
        "name": "Self",
        # Explicit "self" entry so self-pickup commands normalise to a
        # real Transporter row and Bill.transporter_id isn't null for
        # self-pickup bills. Easier for downstream reports.
        "aliases": ["self", "self pickup", "self-pickup", "khud", "apna", "apni"],
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        dalal_created = dalal_updated = 0
        for entry in DALALS:
            existing = db.query(Dalal).filter(Dalal.name == entry["name"]).first()
            if existing:
                existing.aliases = entry["aliases"]
                existing.default_percent = entry.get("default_percent")
                existing.is_active = 1
                dalal_updated += 1
            else:
                db.add(Dalal(
                    name=entry["name"],
                    aliases=entry["aliases"],
                    default_percent=entry.get("default_percent"),
                    is_active=1,
                ))
                dalal_created += 1

        t_created = t_updated = 0
        for entry in TRANSPORTERS:
            existing = db.query(Transporter).filter(
                Transporter.name == entry["name"]
            ).first()
            if existing:
                existing.aliases = entry["aliases"]
                existing.default_bhada = entry.get("default_bhada")
                existing.is_active = 1
                t_updated += 1
            else:
                db.add(Transporter(
                    name=entry["name"],
                    aliases=entry["aliases"],
                    default_bhada=entry.get("default_bhada"),
                    is_active=1,
                ))
                t_created += 1

        db.commit()
        print(f"Dalals:       created={dalal_created} updated={dalal_updated}")
        print(f"Transporters: created={t_created} updated={t_updated}")
        print()
        print("Active Dalals:")
        for d in db.query(Dalal).filter(Dalal.is_active == 1).order_by(Dalal.id).all():
            print(f"  [{d.id}] {d.name} (default {d.default_percent}%)  aliases={d.aliases}")
        print()
        print("Active Transporters:")
        for t in db.query(Transporter).filter(Transporter.is_active == 1).order_by(Transporter.id).all():
            print(f"  [{t.id}] {t.name}  aliases={t.aliases}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
