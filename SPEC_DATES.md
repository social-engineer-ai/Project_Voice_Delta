# SPEC: Bill-generation prototype for a dates trader (Dates branch)

Author: AV (via Claude Code)
Date: 2026-04-22 (branch: `Dates`)
Scope: Urgent demo prototype. Voice command on Telegram → structured
bill rendered as a message + PDF → Tally-importable Sales Voucher XML.
Seeded with dates-product catalog for a dates wholesaler demo.

## Context

This branch is a side-quest off `main` for a specific demo. The
existing `main` branch is the ShopSaarthi voice-agent prototype scoped
for Phase 1 (message / reminder / delegate / call + biometric) plus
the 2026-04-22 intent-taxonomy expansion (12 intents total).

The demo ask is a narrower pitch: "show a Telegram bot that listens
to a shopkeeper's voice, builds a bill, and hands the shopkeeper both
a readable bill and a Tally-importable file". This is ShopSaathi PRD
Phase 1b territory — bill generation — pulled forward as a focused
demo cut rather than a fully-wired phase release.

The branch name `Dates` captures the domain: the first demo is for a
dates trader, where the line items are varieties like "Date crown
fard" and "Date crown premium fard". The core flow is product-agnostic
— a different branch later could seed cement / pharmaceuticals /
hardware products and reuse everything else.

## Goal

End-to-end demo flow works locally on AV's laptop:

1. AV sends a Telegram voice message in Hindi/Hinglish like:
   *"Rajesh ke liye 5 carton Date crown fard bill banao, rate 3000 per
   carton"*
2. Bot responds within ~5 seconds with:
   - A readable bill in the Telegram chat (customer, line items, total).
   - A PDF attachment of the same bill.
   - An XML attachment that Tally ERP 9 / Prime can import as a Sales
     Voucher.
3. The Products table has seeded dates varieties so product-name
   fuzzy-matching works (e.g., if ASR produces "date crown fardh" or
   "crown phard", we still match to the right product).
4. Bill rows persist in a `bills` table so a follow-up "aaj ka total
   bill kitna hua" could later query it (not implemented in this
   demo, but the DB is ready).

## Defaults used (per AV's "just start with defaults")

1. **Voice input**: natural Hindi/Hinglish, not a strict template.
   The classifier extracts customer + items + rates.
2. **Line items per command**: support 1-3 items in a single voice
   message. Prompt guides the classifier to emit a list.
3. **Display format**: plain-text Telegram message on screen
   immediately + PDF attachment. Both always.
4. **Tally XML**: target Tally ERP 9 / Prime compatible Sales Voucher.
   Ledger names in the XML are placeholders the shop would replace
   to match their real chart of accounts. File delivered as a
   Telegram attachment.
5. **Tax**: CGST 9% + SGST 9% = 18% total, configurable per product
   via `Product.gst_rate` but defaulting to 18 for dates. No
   composition scheme, no reverse charge, no exemption handling in
   v1.
6. **Demo environment**: AV's laptop. Bot runs via `python -m
   app.main`. No deployment.

## Out of scope (for this branch, this session)

- Deployment of any kind. Screen-share from laptop only.
- Real Tally connection (ODBC push to port 9000). File-attachment
  delivery only.
- Bill amendment / cancellation voice commands.
- Inventory tracking tied to bills. The Tally XML would move stock
  on import; our DB does not track it.
- Multi-branch / multi-company / multi-tenant considerations.
- Payment collection flow from the bill (future_phase `collection`
  intent covers the query shape, not the bill creation).
- PDF with shop logo / letterhead. Plain functional template only.
- Bhaiya-shop integration (his shop is building materials, not
  dates — a separate seed file swap).

## The 12 + 1 intent taxonomy

Adds a 13th intent: `bill` (scope=`in_scope`). New entries to maintain:

- `IntentValue` adds `"bill"`.
- `IN_SCOPE_INTENTS` adds `"bill"`.
- `SYSTEM_PROMPT` gets a BILL block with 2-3 Hindi examples.
- `voice.py` handler dict adds `"bill": handle_bill_intent`.
- `INTENT_LABEL_HINDI` doesn't need an entry (that's for future_phase
  echoes; bill is in-scope).

## Schema additions

### `IntentClassification` — new nested field `bill_items`

```python
class BillItemExtracted(BaseModel):
    product_name: Optional[str] = Field(
        default=None,
        description="The product as spoken (e.g., 'Date crown fard'). "
                    "Fuzzy-matched against the Products table downstream."
    )
    quantity: Optional[float] = Field(default=None)
    unit: Optional[str] = Field(
        default=None,
        description="Unit of the quantity: carton, box, kg, packet, piece, etc."
    )
    rate: Optional[float] = Field(
        default=None,
        description="Price per unit in INR, as spoken."
    )

class IntentClassification(BaseModel):
    # ... existing fields ...
    bill_items: Optional[list[BillItemExtracted]] = Field(
        default=None,
        description="For 'bill' intent only: up to 3 line items extracted "
                    "from the voice command."
    )
```

The schema cleaner (`_to_gemini_schema`) must resolve the nested
`BillItemExtracted` $ref — existing cleaner already does this for
any nested model. Verify empirically.

### New tables in `app/db/models.py`

- `Product` — master list of sellable items. Seeded with dates in
  this branch.
- `Bill` — header row (customer, date, totals).
- `BillItem` — line rows (product_name, quantity, unit, rate, amount).

Keeping `BillItem.product_name` as free-text (not a hard FK) so that
products the classifier extracts but haven't been seeded still get a
bill row — we fuzzy-match to `Product` where possible but don't fail
the bill if a product doesn't match exactly. This keeps the demo
resilient to ASR quirks.

## Seeded dates catalog

The two AV specified plus four well-known traded varieties in
India/Gulf (defaults — AV can edit the seed script):

| Name | Aliases (for fuzzy match) | Default unit | Default GST % |
|---|---|---|---|
| Date crown fard | crown fard, date crown, crown date | carton | 18 |
| Date crown premium fard | crown premium, date crown premium, premium fard | carton | 18 |
| Ajwa dates | ajwa, ajwah, ajwa khajoor | box | 18 |
| Mabroom dates | mabroom, mabrum | box | 18 |
| Medjool dates | medjool, majdool, majool | box | 18 |
| Kimia dates | kimia, kimiya | carton | 18 |
| Safawi dates | safawi, saffawi | carton | 18 |

No default_rate — rates vary by season/batch and the shopkeeper
speaks the rate in every bill command. Forcing a default would be
misleading.

## Tally XML — exact shape produced

Sales Voucher, compatible with Tally ERP 9 / Tally Prime. Minimum
required fields only. Ledger names below are placeholders the demo
audience should understand as "replace with your actual Tally
ledgers":

```xml
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>{company}</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Invoice Voucher View">
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
            <VOUCHERNUMBER>{bill_number}</VOUCHERNUMBER>
            <PARTYLEDGERNAME>{customer_name}</PARTYLEDGERNAME>
            <BASICBUYERNAME>{customer_name}</BASICBUYERNAME>
            <ISINVOICE>Yes</ISINVOICE>
            <ALLINVENTORYENTRIES.LIST>
              <!-- one per line item -->
            </ALLINVENTORYENTRIES.LIST>
            <ALLLEDGERENTRIES.LIST>
              <!-- debit: customer ledger (=grand total) -->
              <!-- credit: sales ledger (=subtotal) -->
              <!-- credit: CGST / SGST ledgers -->
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

Ledger names defaulted:
- `Sales` — sales ledger
- `Output CGST @ 9%`, `Output SGST @ 9%` — tax ledgers
- Customer ledger = the customer name spoken
- Company = `ShopSaarthi Demo Co` (env-overridable)

## Files this branch touches

| # | File | Change |
|---|---|---|
| 1 | `SPEC_DATES.md` | This file |
| 2 | `app/db/models.py` | Add `Product`, `Bill`, `BillItem` |
| 3 | `app/services/classify.py` | Add `bill` intent, `BillItemExtracted` nested model, `bill_items` field, SYSTEM_PROMPT block |
| 4 | `app/handlers/bill.py` | New; orchestrates extraction → DB → format → PDF → Tally XML → Telegram |
| 5 | `app/services/bill_format.py` | New; message + PDF rendering |
| 6 | `app/services/tally_export.py` | New; XML generation |
| 7 | `app/handlers/voice.py` | Add `bill` to handler dict |
| 8 | `scripts/seed_dates_products.py` | Populate `Product` table |
| 9 | `requirements.txt` | Add `reportlab` |
| 10 | `tests/test_classify.py` | 3-4 bill cases |
| 11 | `DATES_DEMO.md` | Step-by-step demo runbook for AV |

## Verification

Before calling the prototype demo-ready:

1. `tests/test_schema_cleaner.py` passes.
2. `tests/test_classify.py` — bill cases classify correctly and
   `bill_items` is populated with >=1 item.
3. End-to-end dry run on AV's laptop:
   - Send Telegram voice: "Rajesh ke liye 5 carton Date crown fard
     ka bill banao, rate 3000"
   - Bot replies with message + PDF + XML within 5 seconds.
   - XML passes a basic well-formedness check (`xmllint --noout`
     equivalent).
   - PDF opens and displays line items + total.
4. Manual XML inspection — lineitem count and totals match the
   message and PDF.

## Rollback

If anything is broken at demo time, `git checkout main` reverts
everything to the prototype-handover state. `Dates` branch stays
separate.

## Commit plan

Two-part on `Dates` branch, then push:

1. **Code**: classify.py, models.py, voice.py, handlers/bill.py,
   services/bill_format.py, services/tally_export.py, scripts/
   seed_dates_products.py, tests.
2. **Docs**: SPEC_DATES.md, DATES_DEMO.md.
