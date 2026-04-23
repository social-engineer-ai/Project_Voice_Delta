"""Report rendering — Telegram message, A5 PDF, standalone HTML.

Added 2026-04-23 on the Dates branch. Sibling to bill_format.py; same
look-and-feel conventions (A5 PDF, Unicode font fallback via
bill_format._font_name, simple visible tables). The HTML renderer
produces a single self-contained file — all CSS inline, no JS, opens
in any browser from a download or shared link. Purpose is to give a
preview of what a future web-app view would look like, without
building the web app yet.
"""
from __future__ import annotations

import html as html_escape
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from app.services.bill_format import SHOP_NAME, _font_name
from app.services.reports import ReportResult


def _subject_title(result: ReportResult) -> str:
    if result.subject == "overall":
        return "Overall"
    base = result.subject.title()
    if result.filter_name:
        return f"{base}: {result.filter_name}"
    return base


# ---------------- Telegram message ----------------

def format_report_message(result: ReportResult) -> str:
    """Chat-friendly summary. Numbers first, bill preview below."""
    lines: list[str] = []
    lines.append(f"📊 *Report — {_subject_title(result)}*")
    lines.append(f"Period: {result.period_label}")
    if result.filter_name and not result.filter_matched:
        # Warn the shopkeeper that the filter fell back to a name search
        # rather than matching a catalog entity.
        lines.append(f"_Note: no exact catalog match for '{result.filter_name}'; "
                     f"searched by name substring._")
    lines.append("")
    lines.append(f"Bills: *{result.bill_count}*")
    if result.bill_count == 0:
        lines.append("")
        lines.append("Is period mein koi bill nahi mila.")
        lines.append("इस period में कोई bill नहीं मिला।")
        return "\n".join(lines)

    lines.append(f"Subtotal: ₹{result.subtotal:,.2f}")
    lines.append(f"GST:      ₹{result.tax_amount:,.2f}")
    if result.bhada:
        lines.append(f"Bhada:    ₹{result.bhada:,.2f}")
    lines.append(f"*Total:    ₹{result.total:,.2f}*")

    if result.subject == "dalal" and result.dalali_amount:
        lines.append("")
        lines.append(f"*Dalali payable: ₹{result.dalali_amount:,.2f}*")

    # Top-5 breakdowns for overall reports.
    if result.subject == "overall" and result.by_dalal:
        lines.append("")
        lines.append("*Top dalals (by total):*")
        for name, count, tot in result.by_dalal[:3]:
            lines.append(f"  • {name}: {count} bills, ₹{tot:,.0f}")

    # Bill preview — most recent 5.
    preview = result.bills[:5]
    if preview:
        lines.append("")
        lines.append(f"*Recent bills ({min(5, result.bill_count)} of {result.bill_count}):*")
        for b in preview:
            lines.append(
                f"  • {b.bill_number} — {b.customer_name} — "
                f"₹{b.total:,.0f}"
            )
        if result.bill_count > 5:
            lines.append(f"  ...aur {result.bill_count - 5} aur bills, full detail PDF/HTML mein.")

    return "\n".join(lines)


# ---------------- PDF ----------------

def render_report_pdf(result: ReportResult, output_path: Path) -> Path:
    """A5 one-page report. Falls back to multi-page via Platypus flow
    if the bill list runs long."""
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
    elements.append(Paragraph(f"Report — {_subject_title(result)}", title_style))
    elements.append(Paragraph(
        f"{SHOP_NAME} &mdash; Generated "
        f"{datetime.utcnow().strftime('%d %b %Y, %I:%M %p')}",
        small_style,
    ))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(f"<b>Period:</b> {result.period_label}", small_style))
    if result.filter_name and not result.filter_matched:
        elements.append(Paragraph(
            f"<i>No exact catalog match for '{result.filter_name}'; "
            f"searched by name substring.</i>",
            small_style,
        ))
    elements.append(Spacer(1, 4 * mm))

    # Summary table.
    summary_rows = [
        ["Bills", f"{result.bill_count}"],
        ["Subtotal", f"₹ {result.subtotal:,.2f}"],
        ["GST", f"₹ {result.tax_amount:,.2f}"],
    ]
    if result.bhada:
        summary_rows.append(["Bhada", f"₹ {result.bhada:,.2f}"])
    summary_rows.append(["Total", f"₹ {result.total:,.2f}"])
    if result.subject == "dalal" and result.dalali_amount:
        summary_rows.append(["Dalali payable", f"₹ {result.dalali_amount:,.2f}"])
    summary_table = Table(summary_rows, hAlign="LEFT", colWidths=[40 * mm, 40 * mm])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), unicode_font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("FONTNAME", (0, -1), (-1, -1), unicode_font_bold) if result.subject != "dalal"
        else ("FONTNAME", (0, -2), (-1, -2), unicode_font_bold),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6 * mm))

    # Bills table.
    if result.bills:
        header = ["Bill #", "Date", "Customer", "Dalal", "Transp", "Total"]
        data = [header]
        for b in result.bills:
            data.append([
                b.bill_number,
                b.bill_date.strftime("%d-%b"),
                (b.customer_name or "")[:18],
                (b.dalal or "-")[:12] if b.dalal and b.dalal.lower() != "none" else "-",
                (b.transporter or "-")[:12],
                f"₹ {b.total:,.0f}",
            ])
        bills_table = Table(
            data, hAlign="LEFT",
            colWidths=[24 * mm, 14 * mm, 30 * mm, 22 * mm, 22 * mm, 20 * mm],
            repeatRows=1,
        )
        bills_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("FONTNAME", (0, 0), (-1, -1), unicode_font),
            ("FONTNAME", (0, 0), (-1, 0), unicode_font_bold),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (5, 1), (5, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(Paragraph("<b>Bills</b>", small_style))
        elements.append(Spacer(1, 2 * mm))
        elements.append(bills_table)
    else:
        elements.append(Paragraph("<i>No bills in this period.</i>", small_style))

    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph(
        "System-generated report. Figures based on bills stored in "
        "ShopSaarthi DB on the generation timestamp.",
        small_style,
    ))

    doc.build(elements)
    return output_path


# ---------------- HTML (single self-contained file) ----------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Report — {title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0; padding: 2rem; background: #f7f7f8; color: #1a1a1a;
    }}
    .card {{
      max-width: 960px; margin: 0 auto; background: white;
      border: 1px solid #e0e0e0; border-radius: 8px; padding: 2rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.5rem; }}
    .meta {{ color: #666; font-size: 0.85rem; margin-bottom: 1.5rem; }}
    .warn {{
      background: #fff8e1; border-left: 3px solid #f5a623;
      padding: 0.5rem 0.75rem; font-size: 0.85rem; margin-bottom: 1rem;
    }}
    .summary {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 0.75rem; margin-bottom: 1.5rem;
    }}
    .stat {{
      border: 1px solid #e0e0e0; border-radius: 6px; padding: 0.75rem 1rem;
    }}
    .stat .label {{ color: #666; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
    .stat .value {{ font-size: 1.4rem; font-weight: 600; margin-top: 0.25rem; }}
    .stat.total {{ background: #1a1a1a; color: white; border-color: #1a1a1a; }}
    .stat.total .label {{ color: #aaa; }}
    .stat.dalali {{ background: #e8f5e9; border-color: #a5d6a7; }}
    table {{
      width: 100%; border-collapse: collapse; margin-top: 1rem;
      font-size: 0.85rem;
    }}
    th, td {{ border: 1px solid #e0e0e0; padding: 0.5rem; text-align: left; }}
    th {{ background: #f0f0f0; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    h2 {{ font-size: 1rem; margin-top: 2rem; margin-bottom: 0.5rem; color: #333; }}
    .footer {{
      margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e0e0e0;
      font-size: 0.8rem; color: #888;
    }}
    .empty {{ color: #888; font-style: italic; margin: 2rem 0; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Report — {title}</h1>
    <div class="meta">
      {shop_name} &middot; Period: {period_label} &middot;
      Generated {generated_at}
    </div>
    {warning_block}
    <div class="summary">
      {summary_stats}
    </div>
    {bills_block}
    {breakdown_block}
    <div class="footer">
      System-generated report. Figures based on bills stored in ShopSaarthi DB
      on the generation timestamp. For broker-visible documents use the
      dalal memo PDF from the corresponding bill.
    </div>
  </div>
</body>
</html>
"""


def _html_stat(label: str, value: str, klass: str = "") -> str:
    esc_value = html_escape.escape(value)
    esc_label = html_escape.escape(label)
    return (
        f'<div class="stat {klass}"><div class="label">{esc_label}</div>'
        f'<div class="value">{esc_value}</div></div>'
    )


def render_report_html(result: ReportResult, output_path: Path) -> Path:
    """Write a standalone HTML file to output_path. Returns the path."""
    title = html_escape.escape(_subject_title(result))
    period_label = html_escape.escape(result.period_label)
    generated_at = datetime.utcnow().strftime("%d %b %Y, %I:%M %p UTC")

    warning_block = ""
    if result.filter_name and not result.filter_matched:
        warning_block = (
            f'<div class="warn">No exact catalog match for '
            f'"{html_escape.escape(result.filter_name)}"; '
            f'searched by name substring.</div>'
        )

    stats_html: list[str] = []
    stats_html.append(_html_stat("Bills", str(result.bill_count)))
    stats_html.append(_html_stat("Subtotal", f"₹ {result.subtotal:,.2f}"))
    stats_html.append(_html_stat("GST", f"₹ {result.tax_amount:,.2f}"))
    if result.bhada:
        stats_html.append(_html_stat("Bhada", f"₹ {result.bhada:,.2f}"))
    stats_html.append(_html_stat("Total", f"₹ {result.total:,.2f}", "total"))
    if result.subject == "dalal" and result.dalali_amount:
        stats_html.append(_html_stat(
            "Dalali payable", f"₹ {result.dalali_amount:,.2f}", "dalali",
        ))
    summary_stats = "\n".join(stats_html)

    if result.bills:
        rows_html = ["<h2>Bills</h2>", "<table>", "<thead><tr>",
                     "<th>Bill #</th><th>Date</th><th>Customer</th>",
                     "<th>Dalal</th><th>Transporter</th>",
                     "<th class='num'>Subtotal</th><th class='num'>Bhada</th>",
                     "<th class='num'>Total</th>",
                     "</tr></thead><tbody>"]
        for b in result.bills:
            dalal_cell = (b.dalal if b.dalal and b.dalal.lower() != "none" else "-")
            rows_html.append("<tr>")
            rows_html.append(f"<td>{html_escape.escape(b.bill_number)}</td>")
            rows_html.append(f"<td>{b.bill_date.strftime('%d-%b-%Y')}</td>")
            rows_html.append(f"<td>{html_escape.escape(b.customer_name or '')}</td>")
            rows_html.append(f"<td>{html_escape.escape(dalal_cell)}</td>")
            rows_html.append(f"<td>{html_escape.escape(b.transporter or '-')}</td>")
            rows_html.append(f"<td class='num'>₹ {b.subtotal:,.2f}</td>")
            rows_html.append(f"<td class='num'>₹ {b.bhada or 0:,.2f}</td>")
            rows_html.append(f"<td class='num'>₹ {b.total:,.2f}</td>")
            rows_html.append("</tr>")
        rows_html.append("</tbody></table>")
        bills_block = "\n".join(rows_html)
    else:
        bills_block = '<div class="empty">No bills in this period.</div>'

    breakdown_parts: list[str] = []
    if result.subject == "overall" and result.by_dalal:
        breakdown_parts.append("<h2>By Dalal</h2>")
        breakdown_parts.append("<table><thead><tr><th>Dalal</th>"
                               "<th class='num'>Bills</th><th class='num'>Total</th>"
                               "</tr></thead><tbody>")
        for name, count, tot in result.by_dalal:
            breakdown_parts.append(
                f"<tr><td>{html_escape.escape(name)}</td>"
                f"<td class='num'>{count}</td>"
                f"<td class='num'>₹ {tot:,.2f}</td></tr>"
            )
        breakdown_parts.append("</tbody></table>")
    if result.subject == "overall" and result.by_transporter:
        breakdown_parts.append("<h2>By Transporter</h2>")
        breakdown_parts.append("<table><thead><tr><th>Transporter</th>"
                               "<th class='num'>Bills</th><th class='num'>Total</th>"
                               "</tr></thead><tbody>")
        for name, count, tot in result.by_transporter:
            breakdown_parts.append(
                f"<tr><td>{html_escape.escape(name)}</td>"
                f"<td class='num'>{count}</td>"
                f"<td class='num'>₹ {tot:,.2f}</td></tr>"
            )
        breakdown_parts.append("</tbody></table>")
    breakdown_block = "\n".join(breakdown_parts)

    html_content = _HTML_TEMPLATE.format(
        title=title,
        shop_name=html_escape.escape(SHOP_NAME),
        period_label=period_label,
        generated_at=generated_at,
        warning_block=warning_block,
        summary_stats=summary_stats,
        bills_block=bills_block,
        breakdown_block=breakdown_block,
    )

    output_path.write_text(html_content, encoding="utf-8")
    return output_path
