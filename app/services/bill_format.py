"""Bill rendering — plain-text message for Telegram and a one-page PDF.

Added on the `Dates` branch (2026-04-22) for the bill-generation
prototype. Kept deliberately simple: no logos, no letterhead, no
multi-page, no fancy typography. The point is to show that the voice-
extracted items land correctly, not to compete with existing billing
software.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from app.db.models import Bill, BillItem


SHOP_NAME = "ShopSaarthi Demo Shop"
SHOP_ADDRESS = "Nagin Nagar, Indore, MP"
SHOP_PHONE = "+91 90000 00000"
SHOP_GSTIN = "23ABCDE1234F1Z5"


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
    lines.append(f"Subtotal:   ₹{bill.subtotal:,.2f}")
    lines.append(f"GST:        ₹{bill.tax_amount:,.2f}")
    lines.append(f"*Total:      ₹{bill.total:,.2f}*")
    return "\n".join(lines)


def render_bill_pdf(bill: Bill, output_path: Path) -> Path:
    """Render a one-page A5 PDF of the bill. Returns the path written."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A5,
        topMargin=10 * mm, bottomMargin=10 * mm,
        leftMargin=10 * mm, rightMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"], fontSize=14, alignment=1
    )
    small_style = ParagraphStyle(
        "small", parent=styles["Normal"], fontSize=8, leading=10
    )
    right_style = ParagraphStyle(
        "right", parent=styles["Normal"], fontSize=10, alignment=2
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
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5 * mm))

    totals_data = [
        ["Subtotal", f"₹ {bill.subtotal:,.2f}"],
        [f"GST ({bill.items[0].gst_rate:g}%)" if bill.items else "GST",
         f"₹ {bill.tax_amount:,.2f}"],
        ["Total", f"₹ {bill.total:,.2f}"],
    ]
    totals_table = Table(totals_data, hAlign="RIGHT", colWidths=[30 * mm, 30 * mm])
    totals_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
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
