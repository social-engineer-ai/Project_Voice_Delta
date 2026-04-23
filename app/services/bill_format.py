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
    if bill.dalal and bill.dalal.lower() != "none":
        lines.append(f"Dalal: {bill.dalal} ({bill.dalali_percent:g}%)")
    lines.append(f"Subtotal:   ₹{bill.subtotal:,.2f}")
    lines.append(f"GST:        ₹{bill.tax_amount:,.2f}")
    if bill.bhada and bill.bhada > 0:
        lines.append(f"Bhada:      ₹{bill.bhada:,.2f}")
    lines.append(f"*Total:      ₹{bill.total:,.2f}*")
    # Dalali is informational, not added to customer total — show below
    # the total with a note so the shopkeeper knows it's their payable
    # to the dalal, not the customer's receivable.
    if bill.dalali_amount and bill.dalali_amount > 0:
        lines.append(
            f"_Dalali payable: ₹{bill.dalali_amount:,.2f} "
            f"({bill.dalali_percent:g}% of subtotal, not in customer total)_"
        )
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
    if bill.dalal and bill.dalal.lower() != "none":
        elements.append(Paragraph(
            f"<b>Dalal:</b> {bill.dalal} ({bill.dalali_percent:g}%)",
            small_style,
        ))
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
    # Remember the Total row's index before optionally appending the
    # dalali line, so the bold + line-above styling lands on the right
    # row even when dalali is present.
    total_row_idx = len(totals_data) - 1
    if bill.dalali_amount and bill.dalali_amount > 0:
        totals_data.append([
            f"Dalali ({bill.dalali_percent:g}%, not in total)",
            f"₹ {bill.dalali_amount:,.2f}",
        ])
    totals_table = Table(totals_data, hAlign="RIGHT", colWidths=[40 * mm, 30 * mm])
    style = [
        ("FONTNAME", (0, 0), (-1, -1), unicode_font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        # Total row gets bold + a line above it.
        ("FONTNAME", (0, total_row_idx), (-1, total_row_idx), unicode_font_bold),
        ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 0.5, colors.black),
        ("TOPPADDING", (0, total_row_idx), (-1, total_row_idx), 3),
    ]
    # Style the dalali row (if any) in muted grey italic so visually it
    # reads as informational, not part of the customer's bill.
    if bill.dalali_amount and bill.dalali_amount > 0:
        style.extend([
            ("FONTSIZE", (0, -1), (-1, -1), 8),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.grey),
            ("TOPPADDING", (0, -1), (-1, -1), 2),
        ])
    totals_table.setStyle(TableStyle(style))
    elements.append(totals_table)

    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(
        "This is a system-generated bill. Thank you for your business.",
        small_style,
    ))

    doc.build(elements)
    return output_path
