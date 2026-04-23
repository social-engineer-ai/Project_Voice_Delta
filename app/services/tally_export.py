"""Tally XML Sales Voucher generation.

Added on the `Dates` branch (2026-04-22) for the bill-generation
prototype. Produces a Tally ERP 9 / Tally Prime-compatible Import Data
envelope containing one Sales Voucher per bill.

Ledger names below are placeholders the shop would replace to match
their real chart of accounts. For the demo, we document this in
DATES_DEMO.md so the audience understands "in real deployment, the
customer ledger and sales/tax ledgers would match whatever is already
configured in your Tally company".

XML structure reference:
https://help.tallysolutions.com/article/Tally.Developer9/XML_Import_Export/
https://help.tallysolutions.com/docs/te9rel66/Data_Interface/Import_Data/Creating_a_Voucher.htm

This module has no external dependencies beyond the stdlib.
"""
from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

from app.db.models import Bill


# Defaults — override via env or per-shop config in a later session.
DEFAULT_COMPANY = "ShopSaarthi Demo Co"
SALES_LEDGER = "Sales"
CGST_LEDGER = "Output CGST @ 9%"
SGST_LEDGER = "Output SGST @ 9%"
FREIGHT_LEDGER = "Freight Charges"


def _sub(parent: Element, tag: str, text: str | None = None, **attrs: str) -> Element:
    """Small helper to build elements with text + attributes cleanly."""
    elem = SubElement(parent, tag, **attrs)
    if text is not None:
        elem.text = text
    return elem


def _ledger_entry(
    parent: Element, ledger_name: str, amount: float, is_party: bool
) -> None:
    """Append one ALLLEDGERENTRIES.LIST / LEDGERENTRIES.LIST entry.

    Tally stores debits as positive amounts and credits as negative in
    the same field. For a Sales Voucher:
      - party ledger (customer) is debited for the grand total → positive
      - sales ledger is credited for the subtotal → negative
      - tax ledgers are credited for their respective amounts → negative
    """
    entry = SubElement(parent, "ALLLEDGERENTRIES.LIST")
    _sub(entry, "LEDGERNAME", ledger_name)
    _sub(entry, "ISDEEMEDPOSITIVE", "Yes" if is_party else "No")
    _sub(entry, "LEDGERFROMITEM", "No")
    _sub(entry, "REMOVEZEROENTRIES", "No")
    _sub(entry, "ISPARTYLEDGER", "Yes" if is_party else "No")
    # Tally amount: negative string for credit side, positive for debit (party).
    amt_str = f"{amount:.2f}" if is_party else f"-{amount:.2f}"
    _sub(entry, "AMOUNT", amt_str)


def build_sales_voucher_xml(
    bill: Bill,
    company: str = DEFAULT_COMPANY,
) -> str:
    """Return a pretty-printed Tally XML string for the given bill.

    The returned string is ready to be written to a .xml file and
    imported via Tally's Gateway of Tally → Import Data → Vouchers
    flow, or pushed to Tally's HTTP endpoint on port 9000.
    """
    envelope = Element("ENVELOPE")

    header = SubElement(envelope, "HEADER")
    _sub(header, "TALLYREQUEST", "Import Data")

    body = SubElement(envelope, "BODY")
    import_data = SubElement(body, "IMPORTDATA")

    request_desc = SubElement(import_data, "REQUESTDESC")
    _sub(request_desc, "REPORTNAME", "Vouchers")
    static_vars = SubElement(request_desc, "STATICVARIABLES")
    _sub(static_vars, "SVCURRENTCOMPANY", company)

    request_data = SubElement(import_data, "REQUESTDATA")
    tally_msg = SubElement(request_data, "TALLYMESSAGE", **{"xmlns:UDF": "TallyUDF"})

    voucher = SubElement(
        tally_msg, "VOUCHER",
        VCHTYPE="Sales", ACTION="Create",
        OBJVIEW="Invoice Voucher View",
    )
    # Tally date format: YYYYMMDD
    _sub(voucher, "DATE", bill.bill_date.strftime("%Y%m%d"))
    _sub(voucher, "VOUCHERTYPENAME", "Sales")
    _sub(voucher, "VOUCHERNUMBER", bill.bill_number)
    _sub(voucher, "PARTYLEDGERNAME", bill.customer_name)
    _sub(voucher, "BASICBUYERNAME", bill.customer_name)
    _sub(voucher, "ISINVOICE", "Yes")
    # Narration captures transporter + bhada so the voucher carries the
    # context even when opened outside Tally. Tally preserves NARRATION
    # on import and shows it in the voucher detail view.
    # Narration is on the shop's customer-ledger sales voucher; kept
    # dalal-free to mirror the customer-bill convention. Dalal context
    # lives on a separate dalal memo document (bill_format.render_dalal_memo_pdf)
    # that the shopkeeper keeps outside Tally.
    narration_parts = [f"Voice-generated bill for {bill.customer_name}"]
    if bill.transporter:
        narration_parts.append(f"Transporter: {bill.transporter}")
    if bill.bhada:
        narration_parts.append(f"Bhada: Rs {bill.bhada:.2f}")
    _sub(voucher, "NARRATION", " | ".join(narration_parts))

    # Inventory entries — one per line item.
    # Tally requires STOCKITEMNAME to exist in the Tally company. If it
    # doesn't, Tally imports create it on the fly (if config allows) or
    # skips the line (if config rejects unknown stock items). Demo
    # audiences should understand this.
    inv_list = SubElement(voucher, "ALLINVENTORYENTRIES.LIST")
    for item in bill.items:
        inv_entry = SubElement(inv_list, "ALLINVENTORYENTRIES.LIST")
        _sub(inv_entry, "STOCKITEMNAME", item.product_name)
        _sub(inv_entry, "ISDEEMEDPOSITIVE", "No")
        _sub(inv_entry, "RATE", f"{item.rate:.2f}/{item.unit or 'nos'}")
        _sub(inv_entry, "AMOUNT", f"-{item.amount:.2f}")
        _sub(inv_entry, "ACTUALQTY", f"{item.quantity:g} {item.unit or 'nos'}")
        _sub(inv_entry, "BILLEDQTY", f"{item.quantity:g} {item.unit or 'nos'}")
        # Link to sales ledger for accounting.
        acc_list = SubElement(inv_entry, "ACCOUNTINGALLOCATIONS.LIST")
        _sub(acc_list, "LEDGERNAME", SALES_LEDGER)
        _sub(acc_list, "ISDEEMEDPOSITIVE", "No")
        _sub(acc_list, "AMOUNT", f"-{item.amount:.2f}")

    # Ledger entries — party (debit grand total), sales (credit subtotal),
    # tax ledgers (credit tax), freight (credit bhada if > 0). The
    # party-debit sum equals subtotal + tax + bhada = grand total.
    _ledger_entry(voucher, bill.customer_name, bill.total, is_party=True)
    _ledger_entry(voucher, SALES_LEDGER, bill.subtotal, is_party=False)
    # Split tax into CGST + SGST 50/50 (common intra-state scenario).
    half_tax = bill.tax_amount / 2
    _ledger_entry(voucher, CGST_LEDGER, half_tax, is_party=False)
    _ledger_entry(voucher, SGST_LEDGER, half_tax, is_party=False)
    # Freight: only emit if bhada > 0. Self-pickup (bhada=0) skips this
    # ledger so the voucher doesn't reference a ledger that may not exist
    # in the shop's chart of accounts for cash / self-pickup sales.
    if bill.bhada and bill.bhada > 0:
        _ledger_entry(voucher, FREIGHT_LEDGER, bill.bhada, is_party=False)

    # Pretty-print.
    rough = tostring(envelope, encoding="utf-8")
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def write_sales_voucher_xml(
    bill: Bill, output_path: Path, company: str = DEFAULT_COMPANY,
) -> Path:
    """Convenience wrapper: build + write to disk. Returns the path."""
    xml_str = build_sales_voucher_xml(bill, company=company)
    output_path.write_text(xml_str, encoding="utf-8")
    return output_path
