# Dates Bill-Generation Prototype — Demo Runbook

Branch: `Dates`
Audience: AV, demoing to a dates trader / potential pilot customer.

## What you will demo in 60 seconds

1. Open Telegram, send a voice message in Hindi/Hinglish:
   *"Rajesh ke liye 5 carton Date crown fard bill banao, rate 3000 per carton"*
2. Within ~5 seconds the bot replies with:
   - A neat bill summary in the chat.
   - A PDF attachment (A5, looks like a receipt).
   - An XML attachment that Tally ERP 9 or Tally Prime can import as a Sales Voucher.
3. Optionally show a multi-item command:
   *"Sharma ji ka bill banao, 3 carton Date crown premium fard rate 3500, aur 2 box Ajwa rate 2800"*

That's it. The pitch is: "the shopkeeper speaks, the bot structures the
data, and the books update in Tally."

## Setup — before the demo (one-time)

Run once on your laptop in the project directory.

```bash
# Fresh DB (optional — if you want to start with no bills in history).
rm shopsaarthi.db

# Initialise tables.
venv/Scripts/python.exe -m app.db.init_db

# Seed the dates product catalog.
venv/Scripts/python.exe scripts/seed_dates_products.py

# Start the bot. Leave this terminal open for the duration of the demo.
venv/Scripts/python.exe -m app.main
```

Make sure `.env` has a valid `TELEGRAM_BOT_TOKEN`, `SARVAM_API_KEY`,
and `GEMINI_API_KEY`.

## Pre-demo sanity check (2 minutes)

Send yourself one voice command on Telegram to confirm the end-to-end
flow works from your phone to your laptop and back. Use the example
above or any variation. Look for:

- A text bill reply in Telegram chat.
- A PDF attachment.
- An XML attachment.

If any of those don't arrive:
- Check the laptop terminal for errors.
- Most likely cause is the speaker-verification layer rejecting your
  voice. Run `/security off` in Telegram to disable verification for
  the demo, or `/enroll` to enrol your voice first.

## Demo script

### Part 1 — Single-item bill

Say into Telegram voice:

> Rajesh ke liye 5 carton Date crown fard bill banao, rate 3000 per carton

The bot will reply within ~5 seconds with three messages in this order:

1. **Text bill:**
   ```
   🧾 Bill DEMO-<date>-001
   Date: <today>
   Customer: Rajesh

   Items:
     1. Date Crown Fard — 5 carton × ₹3,000 = ₹15,000.00

   Subtotal:   ₹15,000.00
   GST:        ₹2,700.00
   Total:      ₹17,700.00
   ```

2. **PDF attachment** — a one-page A5 bill. Open and show.

3. **XML attachment** — Tally Sales Voucher. Open with any text viewer
   to show the XML structure. In real deployment, the shop opens Tally,
   navigates to Gateway of Tally → Import Data → Vouchers, selects
   this file, and the voucher is created in their books.

### Part 2 — Multi-item bill

Say into Telegram voice:

> Sharma ji ka bill banao, 3 carton Date crown premium fard rate 3500, aur 2 box Ajwa rate 2800

Same three replies, but the bill has two line items. Subtotal
₹16,100 + GST ₹2,898 = ₹18,998 total.

### Part 3 — Product variety — how fuzzy-matching works

Show that misspelled or slightly-different product names still match:

> Bill for Mukesh: 10 cartons Medjool dates at 4200 per carton

The classifier extracts "Medjool dates". The fuzzy-match in
`app/handlers/bill.py` finds the closest catalog entry (`Medjool Dates`)
and uses its canonical name on the bill. If the product isn't in the
catalog, the bill still gets created — it just doesn't link to a
Product row.

## What to say about each piece

### When the Telegram message arrives
"The shopkeeper speaks naturally. The bot is doing three things in
parallel: transcription via Sarvam's Hindi ASR, intent classification
via Gemini, and product fuzzy-matching against the catalog."

### When the PDF arrives
"This is an A5 printable version the shopkeeper can share with the
customer on WhatsApp. In production we'd add the shop logo and real
GSTIN. The structure is a real GST-compliant bill — subtotal, CGST 9%
+ SGST 9%, grand total."

### When the XML arrives
"This is a Tally Prime / ERP 9 compatible Sales Voucher. Right now
it's delivered as a file the shopkeeper downloads and imports into
Tally manually. The easy next step is a direct HTTP push to Tally on
port 9000, but many shops aren't ready for that — file import keeps
them in control."

## Talking points — questions likely to come up

**Q: Does this work in real shop noise?**
A: Our 2026-04-22 testing showed Sarvam handles ~14 dB SNR (moderate
background noise) with minimal transcription degradation. Clean
environments are trivially fine. We have recordings to demonstrate.

**Q: What about handwritten bills the shop still makes?**
A: This prototype only covers voice-originated bills. If the shop
wants to continue handwritten for some customers, the two systems
coexist — Tally receives vouchers from both sources.

**Q: What happens if the customer isn't in the shop's Tally ledger?**
A: Today's XML uses the customer name as the party ledger name. If
Tally doesn't find that ledger, Tally Prime creates it on import
(configurable); Tally ERP 9 may reject the voucher depending on the
company's "Allow accounting transactions" setting. A follow-up would
pre-create the ledger via a separate XML push before the voucher.

**Q: How does the shopkeeper edit a bill if they got something wrong?**
A: Not supported in this prototype. The deliberate scope is "generate
from voice"; editing is future-phase work. In the worst case, they
cancel the voucher in Tally directly and re-speak the correct bill.

**Q: What does this cost to run?**
A: Sarvam STT is ₹0.50 / minute of audio. Gemini Flash-Lite runs at
about ₹0.01-0.02 per classification. A typical voice bill is 5-15
seconds of audio and one classification call, so about ₹0.15 per
bill generated. At 50 bills / day, that's ₹225 / month per shop.

## Rollback if the demo goes wrong

- Bot doesn't respond: check the laptop terminal. If you see a
  Python error, `Ctrl+C` and restart with `python -m app.main`.
- Bot returns wrong intent (not bill): the fallback says "Samajh nahi
  aaya" — recover by speaking again, more slowly.
- XML looks weird: the XML is deterministic from the bill data; if
  you can see the bill text correctly in Telegram, the XML is correct
  too (just structured differently).
- If the whole branch is broken: `git checkout main` reverts you to
  the voice-agent prototype without bill generation. The demo then
  becomes a different pitch (voice commands for messages/reminders/
  delegates/calls — still impressive).

## After the demo

- Kill the bot (Ctrl+C in the terminal).
- Export any bills generated during the demo from `shopsaarthi.db`
  if you want to show them later. The `Bill` and `BillItem` tables
  have full history.
- If you committed to follow-ups, note them in `SESSION_NOTES_2026-04-22_dates.md`.

## Files to read before the demo

- `SPEC_DATES.md` — what this prototype actually is.
- `app/services/classify.py` — the prompt. Search for "BILL:" to find
  the intent block. If someone asks how the shopkeeper's speech turns
  into structured data, this prompt is the answer.
- `app/services/tally_export.py` — the XML generator. Show anyone
  with Tally experience.
- `scripts/seed_dates_products.py` — the catalog. Swap this for a
  different shop vertical and the same bot works for cement,
  pharmacy, stationery.
