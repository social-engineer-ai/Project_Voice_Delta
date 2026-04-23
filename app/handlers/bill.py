"""Bill intent handler. Takes the classified IntentClassification,
creates a Bill + BillItems in the DB, renders both a Telegram message
and a PDF, produces a Tally Sales Voucher XML, and sends all three
back to the user.

Added on the `Dates` branch (2026-04-22) for the bill-generation
prototype. See `SPEC_DATES.md` for scope and defaults.
"""
from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path

from rapidfuzz import fuzz, process
from telegram import Update
from telegram.ext import ContextTypes

from app.db.models import Bill, BillItem, Product, User
from app.db.session import SessionLocal
from app.services.bill_format import format_bill_message, render_bill_pdf
from app.services.classify import IntentClassification, BillItemExtracted
from app.services.tally_export import write_sales_voucher_xml

logger = logging.getLogger(__name__)


# Fuzzy-match threshold (0-100). Below this, we keep the spoken name
# as-is and don't link to a Product row. Tuned loose enough to forgive
# typical ASR drift on dates names.
PRODUCT_MATCH_THRESHOLD = 70


def _next_bill_number(db) -> str:
    """Simple monotonic bill number: DEMO-YYYYMMDD-###."""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"DEMO-{today}-"
    # Count today's bills to generate the suffix.
    count = db.query(Bill).filter(Bill.bill_number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"


def _fuzzy_match_product(db, spoken_name: str) -> Product | None:
    """Find the best-matching Product for the spoken product name.

    We build a candidate list of (canonical_name, product_id) pairs
    where canonical_name is both the Product.name and each of its
    aliases. rapidfuzz picks the best fuzzy match; if the score is
    above the threshold, we return that Product, otherwise None.
    """
    if not spoken_name:
        return None
    spoken_lower = spoken_name.strip().lower()

    candidates: dict[str, int] = {}
    for p in db.query(Product).filter(Product.is_active == 1).all():
        candidates[p.name.lower()] = p.id
        for alias in (p.aliases or []):
            candidates[str(alias).lower()] = p.id

    if not candidates:
        return None

    match = process.extractOne(
        spoken_lower, candidates.keys(), scorer=fuzz.WRatio
    )
    if not match:
        return None
    name, score, _ = match
    if score < PRODUCT_MATCH_THRESHOLD:
        logger.info(
            "Product fuzzy match below threshold: spoken=%r best=%r score=%d",
            spoken_name, name, score,
        )
        return None
    return db.query(Product).get(candidates[name])


def _materialise_items(
    db, extracted_items: list[BillItemExtracted],
) -> tuple[list[BillItem], list[tuple[BillItemExtracted, str]]]:
    """Convert the classifier's extracted items into BillItem rows
    (not yet committed). Returns (accepted_rows, rejected_with_reason).

    A line is rejected if:
      - the product_name / quantity / rate is missing, OR
      - the spoken product name does not fuzzy-match any active product
        in the catalog above PRODUCT_MATCH_THRESHOLD.

    The caller should refuse to create the bill if any item is rejected
    rather than silently filing unknown products. The shopkeeper then
    re-speaks so the bill carries only catalog-known products.
    """
    rows: list[BillItem] = []
    rejected: list[tuple[BillItemExtracted, str]] = []
    for x in extracted_items:
        if not x.product_name or x.quantity is None or x.rate is None:
            logger.warning("Rejecting incomplete item: %s", x)
            rejected.append((x, "incomplete"))
            continue
        product = _fuzzy_match_product(db, x.product_name)
        if product is None:
            logger.warning(
                "Rejecting unknown product %r (not in catalog within "
                "fuzzy threshold %d)",
                x.product_name, PRODUCT_MATCH_THRESHOLD,
            )
            rejected.append((x, "unknown_product"))
            continue
        unit = x.unit or product.default_unit or ""
        amount = round(x.quantity * x.rate, 2)
        rows.append(BillItem(
            product_id=product.id,
            product_name=product.name,
            quantity=float(x.quantity),
            unit=unit,
            rate=float(x.rate),
            amount=amount,
            gst_rate=float(product.gst_rate),
        ))
    return rows, rejected


async def handle_bill_intent(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user: User, intent: IntentClassification,
) -> None:
    """Main entry point for the bill intent.

    Flow:
      1. Validate required fields (customer + at least 1 item with qty+rate).
      2. Materialise items (fuzzy-match to products).
      3. Compute totals.
      4. Persist Bill + BillItems.
      5. Reply with the Telegram message.
      6. Attach PDF.
      7. Attach Tally XML.
    """
    transcript = context.user_data.get("last_transcript", "")

    # User-facing error messages include both Hinglish (CLAUDE.md default)
    # and Devanagari, separated by a blank line. Convention local to this
    # handler for the Dates branch demo — the target audience reads both.
    if not intent.recipient_name:
        await update.message.reply_text(
            "Customer ka naam samajh nahi aaya. Dobara boliye, jaise "
            "'Rajesh ke liye 5 carton Date Crown Fard bill banao, rate 3000'.\n\n"
            "ग्राहक का नाम समझ नहीं आया। दोबारा बोलिए, जैसे "
            "'राजेश के लिए 5 कार्टन डेट क्राउन फर्द बिल बनाओ, रेट 3000'।"
        )
        return
    if not intent.bill_items:
        await update.message.reply_text(
            "Bill ke items samajh nahi aaye. Product, quantity aur rate "
            "clearly bolke dobara bhejiye.\n\n"
            "बिल के items समझ नहीं आए। Product, quantity और rate साफ-साफ "
            "बोलकर दोबारा भेजिए।"
        )
        return

    db = SessionLocal()
    try:
        items, rejected = _materialise_items(db, intent.bill_items)

        # Reject the whole bill if any item couldn't be matched against
        # the product catalog. We prefer "ask the shopkeeper to re-speak"
        # over "file a bill with a guessed / unknown product". The
        # rejection message echoes the spoken form so the shopkeeper
        # can tell where the ASR mis-heard.
        if rejected:
            lines_en = [
                "Kuch products catalog mein nahi mile. Bill nahi banaya.",
                "",
                "Samjha nahi:",
            ]
            lines_hi = [
                "कुछ products catalog में नहीं मिले। बिल नहीं बनाया।",
                "",
                "समझ नहीं आया:",
            ]
            for x, reason in rejected:
                if reason == "unknown_product":
                    desc = f"  • '{x.product_name}'"
                    if x.quantity is not None:
                        desc += f" (qty={x.quantity:g} {x.unit or ''}, rate={x.rate})"
                    lines_en.append(desc)
                    lines_hi.append(desc)
                else:
                    lines_en.append(f"  • line with missing {reason}: {x.product_name or '(no name)'}")
                    lines_hi.append(f"  • line with missing {reason}: {x.product_name or '(no name)'}")
            tail = (
                "\nDobara clearly bolke bhejiye, sirf catalog ke products use kariye.\n\n"
                "दोबारा clearly बोलकर भेजिए, सिर्फ catalog के products use कीजिए।"
            )
            await update.message.reply_text(
                "\n".join(lines_en) + "\n\n" + "\n".join(lines_hi) + tail,
            )
            return

        if not items:
            await update.message.reply_text(
                "Items mein kuch kami hai (product, quantity, ya rate "
                "missing). Dobara boliye.\n\n"
                "Items में कुछ कमी है (product, quantity, या rate missing)। "
                "दोबारा बोलिए।"
            )
            return

        subtotal = sum(i.amount for i in items)
        # Simple GST: use the first item's rate as the bill-level rate.
        # Mixed-rate baskets aren't common at a dates trader; will
        # revisit if they show up.
        gst_pct = items[0].gst_rate
        tax_amount = round(subtotal * gst_pct / 100, 2)
        total = round(subtotal + tax_amount, 2)

        bill = Bill(
            user_id=user.id,
            bill_number=_next_bill_number(db),
            customer_name=intent.recipient_name,
            bill_date=datetime.utcnow(),
            subtotal=round(subtotal, 2),
            tax_amount=tax_amount,
            total=total,
            raw_transcript=transcript[:2000] if transcript else None,
            status="created",
        )
        db.add(bill)
        db.flush()  # get bill.id before committing
        for item in items:
            item.bill_id = bill.id
            db.add(item)
        db.commit()
        db.refresh(bill)
        # Re-fetch items now that bill.items relationship is populated.
        _ = bill.items

        # 1. Text message.
        msg = format_bill_message(bill)
        await update.message.reply_text(msg, parse_mode="Markdown")

        # 2. PDF + Tally XML attachments.
        tmpdir = Path(tempfile.mkdtemp(prefix="bill_"))
        pdf_path = tmpdir / f"{bill.bill_number}.pdf"
        xml_path = tmpdir / f"{bill.bill_number}.xml"
        try:
            render_bill_pdf(bill, pdf_path)
            write_sales_voucher_xml(bill, xml_path)

            with open(pdf_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=pdf_path.name,
                    caption="Bill PDF",
                )
            with open(xml_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=xml_path.name,
                    caption="Tally import file (Sales Voucher XML)",
                )
        finally:
            # Leave the tmpdir for now — helpful for post-demo inspection.
            # A cron or shutdown hook can clean these up in production.
            pass

        logger.info(
            "Bill created: number=%s customer=%s items=%d total=%.2f",
            bill.bill_number, bill.customer_name, len(items), bill.total,
        )

    except Exception as e:
        logger.exception(f"Bill handler failed: {e}")
        await update.message.reply_text(
            "Bill banane mein dikkat hui. Dobara try kariye.\n\n"
            "बिल बनाने में दिक्कत हुई। दोबारा try कीजिए।"
        )
    finally:
        db.close()
