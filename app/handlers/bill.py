"""Bill intent handler. Takes the classified IntentClassification,
creates a Bill + BillItems in the DB, renders both a Telegram message
and a PDF, produces a Tally Sales Voucher XML, and sends all three
back to the user.

Added on the `Dates` branch (2026-04-22) for the bill-generation
prototype. See `SPEC_DATES.md` for scope and defaults.
"""
from __future__ import annotations

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path

from rapidfuzz import fuzz, process
from telegram import Update
from telegram.ext import ContextTypes

from app.db.models import Bill, BillItem, Product, User
from app.db.session import SessionLocal
from app.services.bill_format import (
    format_bill_message,
    format_dalal_memo_message,
    has_dalal,
    render_bill_pdf,
    render_dalal_memo_pdf,
)
from app.services.classify import IntentClassification, BillItemExtracted
from app.services.tally_export import write_sales_voucher_xml

logger = logging.getLogger(__name__)


# Fuzzy-match threshold (0-100). Below this, we keep the spoken name
# as-is and don't link to a Product row. Tuned loose enough to forgive
# typical ASR drift on dates names.
PRODUCT_MATCH_THRESHOLD = 70

# Hardcoded password for catalog-add confirmation. Not production auth
# — this is a demo convenience so only the shopkeeper (who knows the
# password) can mint new catalog rows by voice. For production, replace
# with a per-user PIN stored against User, or with admin-only Telegram
# bot commands.
CATALOG_ADD_PASSWORD = "121"


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
) -> tuple[
    list[BillItem],
    list[tuple[BillItemExtracted, str]],
    list[BillItemExtracted],
]:
    """Convert the classifier's extracted items into BillItem rows
    (not yet committed).

    Returns three lists:
      - accepted: BillItem rows ready to save (product matched, all fields present).
      - rejected: (item, reason) tuples that cannot be recovered in the
        current flow: unknown product, missing product name, missing
        quantity. Handler uses these to either reject the bill or hand
        off to the password-gated catalog-add flow.
      - rate_needed: items that match a catalog product and have
        quantity but are missing their rate. Handler stashes these and
        asks the shopkeeper to type the rate(s).

    Ordering of checks inside the loop is deliberate:
      1. product_name + quantity exist (can't recover by any flow if missing).
      2. product fuzzy-matches catalog (recoverable via password flow).
      3. rate exists (recoverable via type-it-in flow).
    """
    accepted: list[BillItem] = []
    rejected: list[tuple[BillItemExtracted, str]] = []
    rate_needed: list[BillItemExtracted] = []

    for x in extracted_items:
        if not x.product_name:
            rejected.append((x, "missing_product_name"))
            continue
        if x.quantity is None:
            rejected.append((x, "missing_quantity"))
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

        # Product matched — now check rate. Missing rate goes to the
        # rate-fill flow with the matched canonical name so the prompt
        # shows a name the shopkeeper will recognise.
        if x.rate is None:
            rate_needed.append(BillItemExtracted(
                product_name=product.name,
                quantity=float(x.quantity),
                unit=x.unit or product.default_unit or "carton",
                rate=None,
            ))
            continue

        unit = x.unit or product.default_unit or ""
        amount = round(x.quantity * x.rate, 2)
        accepted.append(BillItem(
            product_id=product.id,
            product_name=product.name,
            quantity=float(x.quantity),
            unit=unit,
            rate=float(x.rate),
            amount=amount,
            gst_rate=float(product.gst_rate),
        ))
    return accepted, rejected, rate_needed


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

    # Transporter, bhada, dalal, and dalali_percent are all required to
    # create a bill. Ask the shopkeeper to re-speak with those details
    # rather than filing a bill with blanks.
    missing: list[str] = []
    if not intent.transporter:
        missing.append("transporter")
    if intent.bhada is None:
        missing.append("bhada")
    if not intent.dalal:
        missing.append("dalal")
    if intent.dalali_percent is None:
        missing.append("dalali percent")
    if missing:
        missing_str = ", ".join(missing)
        await update.message.reply_text(
            f"{missing_str.capitalize()} bhi boliye. Example: "
            f"'...Sharma Transport se bhada 500, Praveen dalal ka 1.5 "
            f"percent'. Self-pickup ke liye 'self, bhada zero'. Koi "
            f"dalal nahi hai to 'no dalal, dalali zero' bolna.\n\n"
            f"{missing_str} भी बोलिए। जैसे: "
            f"'...Sharma Transport से bhada 500, Praveen दलाल का 1.5 "
            f"percent'। Self-pickup के लिए 'self, bhada zero'। कोई "
            f"दलाल नहीं है तो 'no dalal, dalali zero' बोलिए।"
        )
        return

    db = SessionLocal()
    try:
        items, rejected, rate_needed = _materialise_items(db, intent.bill_items)

        # Split rejections into unknown-products (recoverable via the
        # password-gated catalog-add flow) and genuinely incomplete
        # lines (not recoverable by adding a product). Unknown products
        # get stashed in user_data; any other rejection reason aborts.
        unknown_items = [
            x for x, reason in rejected if reason == "unknown_product"
        ]
        other_rejected = [
            (x, reason) for x, reason in rejected if reason != "unknown_product"
        ]

        if other_rejected:
            lines = [
                "Kuch items mein kami hai, bill nahi banaya.\n",
                "कुछ items में कमी है, बिल नहीं बनाया।\n",
            ]
            for x, reason in other_rejected:
                lines.append(f"  • line with missing {reason}: {x.product_name or '(no name)'}")
            await update.message.reply_text("\n".join(lines))
            return

        # Rate-fill flow: if some items are known products but missing
        # rates, ask the shopkeeper to type the rate(s) in chat. Useful
        # when the shopkeeper prefers to keep prices private (customer
        # in earshot) or when ASR dropped the number.
        if rate_needed and not unknown_items:
            # Stash the accepted items + rate_needed placeholders + the
            # rest of the bill context. On rate reply, complete the bill.
            context.user_data["pending_bill_rates"] = {
                "transcript": transcript,
                "recipient_name": intent.recipient_name,
                "transporter": intent.transporter,
                "bhada": float(intent.bhada),
                "dalal": intent.dalal,
                "dalali_percent": float(intent.dalali_percent),
                # Items that already have rates — carry as dicts.
                "accepted_items": [
                    {
                        "product_id": it.product_id,
                        "product_name": it.product_name,
                        "quantity": it.quantity,
                        "unit": it.unit,
                        "rate": it.rate,
                        "amount": it.amount,
                        "gst_rate": it.gst_rate,
                    }
                    for it in items
                ],
                # Items waiting on rates.
                "rate_needed": [
                    {
                        "product_name": x.product_name,
                        "quantity": x.quantity,
                        "unit": x.unit,
                    }
                    for x in rate_needed
                ],
            }

            lines_en = [
                "Rate(s) boli nahi gayi. Sirf number text kar ke bhejo.",
                "",
                "In products ke rate chahiye (order mein):",
            ]
            lines_hi = [
                "Rate(s) बोली नहीं गई। सिर्फ number text करके भेजिए।",
                "",
                "इन products के rate चाहिए (order में):",
            ]
            for i, x in enumerate(rate_needed, 1):
                qline = f"  {i}. {x.product_name} ({x.quantity:g} {x.unit or 'carton'})"
                lines_en.append(qline)
                lines_hi.append(qline)
            if len(rate_needed) == 1:
                tail_en = "\nEk number text karo, jaise: 2800"
                tail_hi = "\nएक number text कीजिए, जैसे: 2800"
            else:
                tail_en = (
                    f"\n{len(rate_needed)} rates order mein text karo, "
                    f"comma ya space se alag: 2800, 3000"
                )
                tail_hi = (
                    f"\n{len(rate_needed)} rates order में text कीजिए, "
                    f"comma या space से अलग: 2800, 3000"
                )
            await update.message.reply_text(
                "\n".join(lines_en) + tail_en + "\n\n" +
                "\n".join(lines_hi) + tail_hi
            )
            return

        if unknown_items:
            # Stash the full classifier output + unknown product items
            # so a subsequent "121" text can complete the flow.
            context.user_data["pending_bill_add"] = {
                "transcript": transcript,
                "recipient_name": intent.recipient_name,
                "transporter": intent.transporter,
                "bhada": float(intent.bhada),
                "dalal": intent.dalal,
                "dalali_percent": float(intent.dalali_percent),
                "all_items": [i.model_dump() for i in intent.bill_items],
                "unknown_product_names": [
                    (i.product_name, i.unit or "carton")
                    for i in unknown_items
                ],
            }
            names_desc = "\n".join(
                f"  • {x.product_name} (qty={x.quantity:g} {x.unit or 'carton'}, rate={x.rate})"
                for x in unknown_items
            )
            await update.message.reply_text(
                f"Yeh products catalog mein nahi mile:\n{names_desc}\n\n"
                f"Agar add karna chahte ho to password text kar ke bhejo "
                f"({CATALOG_ADD_PASSWORD} bhejna hai). Password bhejte hi "
                f"products add ho jaayenge aur bill ban jaayega.\n\n"
                f"Nahi to dobara clearly bolke voice bhejiye.\n\n"
                f"---\n"
                f"ये products catalog में नहीं मिले:\n{names_desc}\n\n"
                f"अगर add करना चाहते हैं तो password text करके भेजिए "
                f"({CATALOG_ADD_PASSWORD} भेजना है)। Password भेजते ही "
                f"products add हो जाएँगे और bill बन जाएगा।\n\n"
                f"नहीं तो दोबारा clearly बोलकर voice भेजिए।"
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
        bhada_amount = float(intent.bhada or 0.0)
        # Dalali: informational only — computed from subtotal but NOT
        # added to the customer's grand total. It sits on the bill so
        # the shopkeeper knows their payable to the dalal.
        dalali_pct = float(intent.dalali_percent or 0.0)
        dalali_amount = round(subtotal * dalali_pct / 100, 2)
        total = round(subtotal + tax_amount + bhada_amount, 2)

        bill = Bill(
            user_id=user.id,
            bill_number=_next_bill_number(db),
            customer_name=intent.recipient_name,
            bill_date=datetime.utcnow(),
            subtotal=round(subtotal, 2),
            tax_amount=tax_amount,
            transporter=intent.transporter,
            bhada=bhada_amount,
            dalal=intent.dalal,
            dalali_percent=dalali_pct,
            dalali_amount=dalali_amount,
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

        # 2. Customer bill PDF + Tally XML attachments.
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
                    caption="Customer bill PDF (shareable with customer)",
                )
            with open(xml_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=xml_path.name,
                    caption="Tally import file (Sales Voucher XML)",
                )

            # 3. Dalal memo — only when a real broker + commission is set.
            # Never part of the customer bill; shopkeeper-only document
            # for broker reconciliation.
            if has_dalal(bill):
                dalal_pdf_path = tmpdir / f"{bill.bill_number}-dalal.pdf"
                render_dalal_memo_pdf(bill, dalal_pdf_path)

                await update.message.reply_text(
                    format_dalal_memo_message(bill),
                    parse_mode="Markdown",
                )
                with open(dalal_pdf_path, "rb") as f:
                    await update.message.reply_document(
                        document=f,
                        filename=dalal_pdf_path.name,
                        caption="Dalal memo (shopkeeper-only — do NOT share with customer)",
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


# ---------------- Password-gated catalog-add flow ----------------

def _canonical_product_name(spoken: str) -> str:
    """Turn a free-form spoken product name into the canonical
    'Date X' catalog form. If the spoken form already starts with
    'date', capitalise each word; otherwise prefix 'Date '. Used by
    the password-add flow, not by regular catalog lookups."""
    normalized = " ".join(w for w in spoken.strip().split() if w)
    if not normalized:
        return ""
    if normalized.lower().startswith("date "):
        return normalized.title().replace("'S", "'s")
    return ("Date " + normalized).title().replace("'S", "'s")


# Regex pulls integer / decimal numbers out of free-form text, ignoring
# currency symbols, commas inside the number, and Hindi suffixes like
# 'rupaye'. "2,800" becomes 2800; "Rs 2800.50" becomes 2800.5.
_RATE_NUMBER_RE = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?!\w)")


def _parse_rates(text: str) -> list[float]:
    """Pull out all numbers from the shopkeeper's text reply. Returns
    them in order of appearance. '2,800' is treated as 2800."""
    matches = _RATE_NUMBER_RE.findall(text)
    out: list[float] = []
    for m in matches:
        cleaned = m.replace(",", "")
        try:
            out.append(float(cleaned))
        except ValueError:
            continue
    return out


async def maybe_complete_bill_rates(
    update, context, user,
) -> bool:
    """If there's a pending_bill_rates stash and the user has typed
    enough numbers to fill the missing rates, materialise the full
    bill and send the documents. Returns True if the message was
    handled, False otherwise (which lets the caller continue normal
    classification).

    Called before maybe_complete_bill_add in the text handler.
    """
    pending = context.user_data.get("pending_bill_rates")
    if not pending:
        return False

    text = (update.message.text or "").strip()
    parsed = _parse_rates(text)
    needed = pending["rate_needed"]

    if not parsed:
        # No numbers at all — assume the shopkeeper is abandoning the
        # flow (sending a different command). Clear stash and fall
        # through so normal classification handles the new message.
        context.user_data.pop("pending_bill_rates", None)
        logger.info("pending_bill_rates cleared (non-numeric reply).")
        return False

    if len(parsed) < len(needed):
        # Partial reply — ask for the rest rather than silently eating
        # the first rate.
        await update.message.reply_text(
            f"Sirf {len(parsed)} rate(s) mili, {len(needed)} chahiye. "
            f"Sab ek saath text karo, jaise: "
            f"{', '.join(str(1000 + i * 100) for i in range(len(needed)))}\n\n"
            f"सिर्फ {len(parsed)} rate(s) मिली, {len(needed)} चाहिए। "
            f"सब एक साथ text कीजिए।"
        )
        return True

    if len(parsed) > len(needed):
        # Too many numbers — use the first N.
        logger.info(
            "Got %d rates but only %d needed; using the first %d.",
            len(parsed), len(needed), len(needed),
        )
        parsed = parsed[:len(needed)]

    # Reconstruct the full intent with all rates now filled.
    all_items_dicts = list(pending["accepted_items"])
    for placeholder, rate in zip(needed, parsed):
        all_items_dicts.append({
            "product_name": placeholder["product_name"],
            "quantity": placeholder["quantity"],
            "unit": placeholder["unit"],
            "rate": float(rate),
        })

    intent = IntentClassification(
        intent="bill", scope="in_scope",
        recipient_name=pending["recipient_name"],
        transporter=pending["transporter"],
        bhada=pending["bhada"],
        dalal=pending.get("dalal"),
        dalali_percent=pending.get("dalali_percent"),
        bill_items=[
            BillItemExtracted(
                product_name=d.get("product_name"),
                quantity=d.get("quantity"),
                unit=d.get("unit"),
                rate=d.get("rate"),
            )
            for d in all_items_dicts
        ],
        confidence=0.95,
    )
    context.user_data["last_transcript"] = pending.get("transcript") or ""
    context.user_data.pop("pending_bill_rates", None)

    rates_preview = ", ".join(
        f"{p['product_name']} = ₹{r:,.0f}" for p, r in zip(needed, parsed)
    )
    await update.message.reply_text(
        f"Rates mil gaye: {rates_preview}. Bill banaya ja raha hai...\n\n"
        f"Rates मिल गए: {rates_preview}। बिल बनाया जा रहा है..."
    )
    await handle_bill_intent(update, context, user, intent)
    return True


async def maybe_complete_bill_add(
    update, context, user,
) -> bool:
    """If there's a pending_bill_add stash and the user's text matches
    the catalog-add password, add the unknown products to the catalog
    and create the bill. Returns True if the message was handled
    (caller should stop further processing), False otherwise.

    Called from the text-message router before normal classification.
    """
    pending = context.user_data.get("pending_bill_add")
    if not pending:
        return False

    text = (update.message.text or "").strip()

    if text != CATALOG_ADD_PASSWORD:
        # Any non-matching text cancels the pending add so stale state
        # doesn't accumulate. We do NOT handle the message — the caller
        # continues classifying normally so the user's command still
        # gets processed.
        context.user_data.pop("pending_bill_add", None)
        logger.info("Pending catalog-add cleared (wrong password or new command).")
        return False

    # Password matched — add the unknown products, then create the bill.
    db = SessionLocal()
    try:
        added_names: list[str] = []
        for spoken_name, unit in pending["unknown_product_names"]:
            canonical = _canonical_product_name(spoken_name)
            if not canonical:
                continue
            # Avoid dupes if the canonical already exists (possibly
            # because the shopkeeper spoke the same name twice).
            existing = db.query(Product).filter(Product.name == canonical).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = 1
                continue
            db.add(Product(
                name=canonical,
                aliases=[spoken_name.lower(), canonical.lower()],
                default_unit=unit or "carton",
                gst_rate=18.0,
                is_active=1,
            ))
            added_names.append(canonical)
        db.commit()
        logger.info(
            "Catalog-add via password: %d new products (%s)",
            len(added_names), added_names,
        )

        # Reconstruct the bill classification from the stashed state and
        # re-enter the main bill path. Use a light shim so we can call
        # handle_bill_intent with a fake intent object.
        intent = IntentClassification(
            intent="bill", scope="in_scope",
            recipient_name=pending["recipient_name"],
            transporter=pending["transporter"],
            bhada=pending["bhada"],
            dalal=pending.get("dalal"),
            dalali_percent=pending.get("dalali_percent"),
            bill_items=[BillItemExtracted(**d) for d in pending["all_items"]],
            confidence=0.95,
        )
        context.user_data["last_transcript"] = pending.get("transcript") or ""
        # Pop the pending state so a retry doesn't re-trigger.
        context.user_data.pop("pending_bill_add", None)
    finally:
        db.close()

    await update.message.reply_text(
        f"Password confirm ho gaya. {len(added_names)} product(s) catalog "
        f"mein add kar diye. Bill banaya ja raha hai...\n\n"
        f"Password confirm हो गया। {len(added_names)} product(s) catalog "
        f"में add कर दिए। बिल बनाया जा रहा है..."
    )
    # Re-enter the main handler with the reconstructed intent.
    await handle_bill_intent(update, context, user, intent)
    return True
