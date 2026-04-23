"""Bill rendering — plain-text message for Telegram and a one-page PDF.

Added on the `Dates` branch (2026-04-22) for the bill-generation
prototype. Kept deliberately simple: no logos, no letterhead, no
multi-page, no fancy typography. The point is to show that the voice-
extracted items land correctly, not to compete with existing billing
software.
"""
from __future__ import annotations

import logging
import platform
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from app.db.models import Bill, BillItem

logger = logging.getLogger(__name__)


SHOP_NAME = "ShopSaarthi Demo Shop"
SHOP_ADDRESS = "Nagin Nagar, Indore, MP"
SHOP_PHONE = "+91 90000 00000"
SHOP_GSTIN = "23ABCDE1234F1Z5"


# Font registration for Devanagari + Latin text.
#
# ReportLab's built-in Helvetica/Times fonts don't include Devanagari
# glyphs, so ASR-produced Hindi names (e.g., "शर्मा जी", "राजेश") rendered
# as black boxes on the PDF. We register a Unicode-capable font from
# whichever source we can find: bundled first, then Windows system
# fonts, then Linux/macOS paths. Falls back to Helvetica if nothing
# works — at that point Devanagari still renders as black boxes but the
# Latin parts of the bill stay readable.
_UNICODE_FONT_NAME = "ShopSaarthiUnicode"
_UNICODE_FONT_NAME_BOLD = "ShopSaarthiUnicode-Bold"
_unicode_font_registered: bool | None = None


def _register_unicode_font() -> bool:
    """Try to register a Unicode font that supports Devanagari + Latin.
    Returns True if the font was registered (or was already registered),
    False if no suitable font found. Cached after first call."""
    global _unicode_font_registered
    if _unicode_font_registered is not None:
        return _unicode_font_registered

    # Candidate font sources, in priority order.
    # TTC files use (path, subfontIndex) tuples — Nirmala.ttc index 0 is
    # Nirmala UI Regular, index 1 is Nirmala UI Semilight.
    candidates: list[tuple[str, Path, int | None, Path | None]] = []

    # Windows: Nirmala UI (ships by default on Windows 8+).
    if platform.system() == "Windows":
        win_fonts = Path("C:/Windows/Fonts")
        nirmala_ttc = win_fonts / "Nirmala.ttc"
        if nirmala_ttc.exists():
            candidates.append((
                "Nirmala UI", nirmala_ttc, 0, None,
            ))
        mangal = win_fonts / "mangal.ttf"
        if mangal.exists():
            candidates.append(("Mangal", mangal, None, None))

    # Linux: DejaVu Sans ships with most distros and supports Devanagari.
    for p in (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
    ):
        if p.exists():
            candidates.append((p.stem, p, None, None))

    # macOS: ships with Kohinoor Devanagari.
    for p in (
        Path("/Library/Fonts/Kohinoor.ttc"),
        Path("/System/Library/Fonts/Supplemental/Kohinoor.ttc"),
    ):
        if p.exists():
            candidates.append((p.stem, p, 0, None))

    for label, path, subfont_idx, _ in candidates:
        try:
            if subfont_idx is not None:
                font = TTFont(_UNICODE_FONT_NAME, str(path), subfontIndex=subfont_idx)
            else:
                font = TTFont(_UNICODE_FONT_NAME, str(path))
            pdfmetrics.registerFont(font)
            logger.info(f"PDF unicode font registered: {label} from {path}")
            _unicode_font_registered = True
            # Don't fail if a bold variant isn't available — reportlab will
            # fake bold by thickening strokes if we reference the regular name.
            return True
        except Exception as e:
            logger.warning(f"Could not register {label} from {path}: {e}")

    logger.warning(
        "No Unicode font found for PDF rendering. Devanagari in bills "
        "will render as black boxes. Install Nirmala UI / DejaVu Sans / "
        "Noto Sans Devanagari."
    )
    _unicode_font_registered = False
    return False


def _font_name(bold: bool = False) -> str:
    """Return the font name to use for bill text. Falls back to Helvetica
    if the unicode font wasn't registered."""
    if _register_unicode_font():
        return _UNICODE_FONT_NAME  # reportlab fakes bold automatically
    return "Helvetica-Bold" if bold else "Helvetica"


def format_bill_message(bill: Bill) -> str:
    """Render a bill as a plain-text Telegram message.

    Uses simple formatting that reads cleanly in a chat. Totals are
    right-aligned with spaces because Markdown tables don't render in
    Telegram native clients.
    """
    lines: list[str] = []
    lines.append(f"🧾 *Bill {bill.bill_number}*")
    lines.append(f"Date: {bill.bill_date.strftime('%d %b %Y, %I:%M %p')}")
    lines.append(f"Customer: *{bill.customer_name}*")
    lines.append("")
    lines.append("Items:")
    for i, item in enumerate(bill.items, 1):
        unit = item.unit or ""
        lines.append(
            f"  {i}. {item.product_name} — {item.quantity:g} {unit} "
            f"× ₹{item.rate:,.0f} = ₹{item.amount:,.2f}"
        )
    lines.append("")
    if bill.transporter:
        lines.append(f"Transporter: {bill.transporter}")
    lines.append(f"Subtotal:   ₹{bill.subtotal:,.2f}")
    lines.append(f"GST:        ₹{bill.tax_amount:,.2f}")
    if bill.bhada and bill.bhada > 0:
        lines.append(f"Bhada:      ₹{bill.bhada:,.2f}")
    lines.append(f"*Total:      ₹{bill.total:,.2f}*")
    # Dalal/dalali intentionally not shown on the customer bill — broker
    # context goes into a separate dalal memo (see format_dalal_memo_message
    # / render_dalal_memo_pdf) that the shopkeeper keeps for broker
    # reconciliation and does not share with the customer.
    return "\n".join(lines)


def render_bill_pdf(bill: Bill, output_path: Path) -> Path:
    """Render a one-page A5 PDF of the bill. Returns the path written."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A5,
        topMargin=10 * mm, bottomMargin=10 * mm,
        leftMargin=10 * mm, rightMargin=10 * mm,
    )

    # Resolve the Unicode-capable font once per PDF.
    unicode_font = _font_name()
    unicode_font_bold = _font_name(bold=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"],
        fontName=unicode_font_bold, fontSize=14, alignment=1,
    )
    small_style = ParagraphStyle(
        "small", parent=styles["Normal"],
        fontName=unicode_font, fontSize=8, leading=10,
    )
    right_style = ParagraphStyle(
        "right", parent=styles["Normal"],
        fontName=unicode_font, fontSize=10, alignment=2,
    )

    elements: list = []
    elements.append(Paragraph(SHOP_NAME, title_style))
    elements.append(Paragraph(
        f"{SHOP_ADDRESS}<br/>Phone: {SHOP_PHONE}<br/>GSTIN: {SHOP_GSTIN}",
        small_style,
    ))
    elements.append(Spacer(1, 5 * mm))

    elements.append(Paragraph(f"<b>Bill:</b> {bill.bill_number}", small_style))
    elements.append(Paragraph(
        f"<b>Date:</b> {bill.bill_date.strftime('%d %b %Y, %I:%M %p')}",
        small_style,
    ))
    elements.append(Paragraph(f"<b>Customer:</b> {bill.customer_name}", small_style))
    if bill.transporter:
        elements.append(Paragraph(
            f"<b>Transporter:</b> {bill.transporter}", small_style,
        ))
    # Dalal is intentionally absent from the customer PDF — it lives on
    # the separate dalal memo only.
    elements.append(Spacer(1, 5 * mm))

    # Line items table.
    data = [["#", "Product", "Qty", "Unit", "Rate (₹)", "Amount (₹)"]]
    for i, item in enumerate(bill.items, 1):
        data.append([
            str(i),
            item.product_name,
            f"{item.quantity:g}",
            item.unit or "",
            f"{item.rate:,.0f}",
            f"{item.amount:,.2f}",
        ])

    table = Table(data, hAlign="LEFT",
                  colWidths=[8 * mm, 50 * mm, 14 * mm, 14 * mm, 22 * mm, 26 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        # Use the Unicode font across the whole table so product names in
        # Devanagari render; the header row uses the same font name
        # because reportlab fakes bold via synthetic emboldening when a
        # bold variant isn't registered.
        ("FONTNAME", (0, 0), (-1, -1), unicode_font),
        ("FONTNAME", (0, 0), (-1, 0), unicode_font_bold),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5 * mm))

    totals_data = [
        ["Subtotal", f"₹ {bill.subtotal:,.2f}"],
        [f"GST ({bill.items[0].gst_rate:g}%)" if bill.items else "GST",
         f"₹ {bill.tax_amount:,.2f}"],
    ]
    if bill.bhada and bill.bhada > 0:
        totals_data.append(["Bhada (Freight)", f"₹ {bill.bhada:,.2f}"])
    totals_data.append(["Total", f"₹ {bill.total:,.2f}"])
    totals_table = Table(totals_data, hAlign="RIGHT", colWidths=[30 * mm, 30 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), unicode_font),
        ("FONTNAME", (0, -1), (-1, -1), unicode_font_bold),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, -1), (-1, -1), 3),
    ]))
    elements.append(totals_table)

    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(
        "This is a system-generated bill. Thank you for your business.",
        small_style,
    ))

    doc.build(elements)
    return output_path


# ---------------- Dalal memo (separate from customer bill) ----------------
#
# The dalal memo is a shop-internal document the shopkeeper keeps (or shares
# with the broker) to record commission payable for a bill. It is NOT shared
# with the customer. Includes the line items, transporter + bhada, and the
# dalali amount — everything the broker needs to reconcile their commission.


def has_dalal(bill: Bill) -> bool:
    """Return True if the bill has a real broker (dalal != 'None' + dalali > 0)."""
    return bool(
        bill.dalal
        and bill.dalal.lower() != "none"
        and bill.dalali_amount
        and bill.dalali_amount > 0
    )


def format_dalal_memo_message(bill: Bill) -> str:
    """Render the dalal memo as a plain-text Telegram message. Short and
    focused on commission reconciliation, not on GST or tax breakdown."""
    lines: list[str] = []
    lines.append(f"📋 *Dalal Memo — {bill.bill_number}*")
    lines.append(f"Date: {bill.bill_date.strftime('%d %b %Y, %I:%M %p')}")
    lines.append(f"Dalal: *{bill.dalal}*")
    lines.append(f"Customer: {bill.customer_name}")
    lines.append("")
    lines.append("Items:")
    for i, item in enumerate(bill.items, 1):
        unit = item.unit or ""
        lines.append(
            f"  {i}. {item.product_name} — {item.quantity:g} {unit} "
            f"× ₹{item.rate:,.0f} = ₹{item.amount:,.2f}"
        )
    lines.append("")
    lines.append(f"Subtotal:  ₹{bill.subtotal:,.2f}")
    if bill.transporter:
        lines.append(f"Transporter: {bill.transporter}")
    if bill.bhada and bill.bhada > 0:
        lines.append(f"Bhada:     ₹{bill.bhada:,.2f}")
    lines.append("")
    lines.append(f"*Dalali ({bill.dalali_percent:g}%): ₹{bill.dalali_amount:,.2f}*")
    lines.append("")
    lines.append(f"_Customer bill total (for reference): ₹{bill.total:,.2f}_")
    return "\n".join(lines)


def render_dalal_memo_pdf(bill: Bill, output_path: Path) -> Path:
    """Render a one-page A5 PDF of the dalal memo. Similar to the customer
    bill but titled 'Dalal Memo', no shop GSTIN / tax breakdown, and the
    dalali amount presented prominently."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A5,
        topMargin=10 * mm, bottomMargin=10 * mm,
        leftMargin=10 * mm, rightMargin=10 * mm,
    )

    unicode_font = _font_name()
    unicode_font_bold = _font_name(bold=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"],
        fontName=unicode_font_bold, fontSize=14, alignment=1,
    )
    small_style = ParagraphStyle(
        "small", parent=styles["Normal"],
        fontName=unicode_font, fontSize=8, leading=10,
    )

    elements: list = []
    elements.append(Paragraph("Dalal Memo", title_style))
    elements.append(Paragraph(
        f"{SHOP_NAME} &mdash; Broker Commission Note",
        small_style,
    ))
    elements.append(Spacer(1, 5 * mm))

    elements.append(Paragraph(f"<b>Ref Bill:</b> {bill.bill_number}", small_style))
    elements.append(Paragraph(
        f"<b>Date:</b> {bill.bill_date.strftime('%d %b %Y, %I:%M %p')}",
        small_style,
    ))
    elements.append(Paragraph(f"<b>Dalal:</b> {bill.dalal}", small_style))
    elements.append(Paragraph(f"<b>Customer:</b> {bill.customer_name}", small_style))
    if bill.transporter:
        elements.append(Paragraph(
            f"<b>Transporter:</b> {bill.transporter}", small_style,
        ))
    elements.append(Spacer(1, 5 * mm))

    # Line items — same shape as the customer bill so the dalal can tie
    # the memo to the bill their customer received.
    data = [["#", "Product", "Qty", "Unit", "Rate (₹)", "Amount (₹)"]]
    for i, item in enumerate(bill.items, 1):
        data.append([
            str(i),
            item.product_name,
            f"{item.quantity:g}",
            item.unit or "",
            f"{item.rate:,.0f}",
            f"{item.amount:,.2f}",
        ])
    table = Table(data, hAlign="LEFT",
                  colWidths=[8 * mm, 50 * mm, 14 * mm, 14 * mm, 22 * mm, 26 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), unicode_font),
        ("FONTNAME", (0, 0), (-1, 0), unicode_font_bold),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5 * mm))

    # Totals — subtotal, bhada, and the prominent dalali line.
    totals_data = [["Subtotal", f"₹ {bill.subtotal:,.2f}"]]
    if bill.bhada and bill.bhada > 0:
        totals_data.append(["Bhada (Freight)", f"₹ {bill.bhada:,.2f}"])
    totals_data.append([
        f"Dalali ({bill.dalali_percent:g}%)",
        f"₹ {bill.dalali_amount:,.2f}",
    ])
    totals_table = Table(totals_data, hAlign="RIGHT", colWidths=[40 * mm, 30 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), unicode_font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        # Highlight the dalali (last) row: bold + line above.
        ("FONTNAME", (0, -1), (-1, -1), unicode_font_bold),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, -1), (-1, -1), 3),
    ]))
    elements.append(totals_table)

    elements.append(Spacer(1, 5 * mm))
    elements.append(Paragraph(
        f"<i>Customer bill total (for reference): ₹ {bill.total:,.2f}</i>",
        small_style,
    ))

    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(
        "This memo is for broker commission reconciliation. "
        "Not a customer invoice.",
        small_style,
    ))

    doc.build(elements)
    return output_path
