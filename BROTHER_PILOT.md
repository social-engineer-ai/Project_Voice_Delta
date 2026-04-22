# Brother's shop — pilot test brief

Audience: AV and brother (in Nagin Nagar, Indore)
Purpose: Run the ShopSaarthi voice agent against a real shop for the
first time, see what breaks, iterate. This is the Phase 1 acceptance
test per `CLAUDE.md` — "owner's brother using the system for 14
consecutive days without abandoning it" — with the detail added after
the 2026-04-22 prototype handoff and the ShopSaathi PRD review.

## What the bot does today (and what it doesn't)

The bot is a Telegram voice-command layer, not the full shop
management system in `ShopSaathi_PRD.md`. In plain terms:

**What it does:**
- Receives a voice message on Telegram in Hindi (or Hinglish) from you.
- Transcribes it, figures out whether you want to (a) send a message,
  (b) set a reminder, (c) delegate a task to someone, or (d) make a
  call.
- For messages and calls, gives you a one-tap link to send/dial through
  your own WhatsApp or phone — the bot doesn't send on your behalf.
- For reminders, pings you on Telegram at the time you specified.
- For delegated tasks, records the task and follows up with you later
  ("did X do Y?").
- Verifies your voice against an enrolled profile before acting
  (trust layer, not a security lock — configurable, can be turned off).

**What it doesn't do (yet):**
- Order management, inventory tracking, collections ledger, customer
  records. All that is Modules 1-6 of the ShopSaathi PRD, not in this
  prototype.
- Auto-record phone calls from customers or suppliers. That needs
  Exotel integration (Module 9), also not in this prototype.
- Reports for you as the remote owner.
- Bill printing or Tally export (Phase 1b).

So: think of this as the *voice operator* for a small slice of the
full system. If it works here, we expand. If the voice layer itself
fails, we learn before building the rest.

## What I'd like to offer bhaiya (in this order)

1. **30-minute setup call** (video or in-person).
   - Install the Telegram bot on his phone.
   - Walk through the four intents with his own examples.
   - Enroll his voice (30 seconds of him reading a short passage).
   - Confirm the bot works on his phone + his network.

2. **Pre-seed with his real contacts.**
   - Once we have his actual supplier list, worker list, and key
     family/customer contacts, I load them into the bot's database
     before he uses it.
   - This is what fixes the "Mountain G" / "Aamu" errors from our
     2026-04-22 testing — the contact resolver can match a garbled
     ASR name against his known contacts.

3. **Two-week daily use trial.**
   - He uses it for real commands during his normal day.
   - Every time it fails or does something unexpected, he forwards the
     voice message and screenshot to me on WhatsApp.
   - I review daily, fix what I can, document what I can't.

4. **Weekly 15-minute debrief.**
   - Quick call at end of each week to see what worked, what didn't,
     what he wants added.
   - End of week 2, we decide: continue and expand, or stop and fix.

## What I need from bhaiya to make this work

The more we know before he starts, the less will break in his first
week. Three buckets:

### Bucket A: Contacts (15-25 rows)

The single biggest accuracy lever. Fill this roughly — phone numbers
can be approximate if needed, we can refine later. Language doesn't
matter.

| Name (as you say it) | Role | Phone | Other names people call him/her |
|---|---|---|---|
| e.g. Sharma traders wala | Supplier (cement) | 98... | Sharma ji, cement wala |
| e.g. Ramu bhaiya | Worker | 98... | Ramu, naukar, chhotu (if used) |
| e.g. Praveen | Customer (regular contractor) | 98... | Parveen, thekedaar |
| ... | ... | ... | ... |

**Suggested mix** (matches the ShopSaathi PRD's role structure):

- 3-4 suppliers (cement, sand/reti, gitti, bricks). Include both their
  official name and how you actually address them on the phone.
- 2-3 workers (delivery, collection, helper). Include any nicknames.
- 5-6 frequent customers (contractors, builders, regulars).
- 2-3 family (papa, nephew/bhatija, accountant ji, maybe dadaji).
- 1-2 others (plumber, electrician, transporter, whoever you call
  often).

The "other names" column is the most important — that's what the
system uses to match "accountant ji" with the actual person when ASR
mangles the name.

### Bucket B: Common commands (15-20 short voice notes)

I need to hear his actual commands, not synthetic textbook Hindi.
These are the first real shopkeeper samples we'll have.

Ask him to record these as **individual voice notes on WhatsApp** (so
they come as .ogg/.m4a files we can feed to the bot):

1. Something you'd say to message a supplier about a cement rate.
2. Something you'd say to a worker about going to a customer's site.
3. Something you'd say to remind yourself about a payment due.
4. Something you'd say to call the accountant about GST.
5. Something short you'd say when you're in a hurry (like 1-2 seconds).
6. Something longer you'd say when you're not (like 10+ seconds).
7. Something with a time in it ("kal shaam", "3 baje", "30 minute
   baad") — however you actually say times.
8. Something with a product in it ("cement ki 50 bori", "gitti ki
   trolley", however you measure).
9. Something you'd say to the driver about a specific delivery.
10. Something you'd say when you want to ask him to reach somewhere.
11. Same command he'd say quietly at home vs. loudly on the shop
    counter. (Two recordings of the same thing, so we see noise
    effects.)
12. A command in English (for variety — "call Sharma ji", "message
    supplier").
13-20. Any other short commands he says multiple times a week.

**No script.** The point is to capture how he actually speaks, not a
clean reading. Mumbling, false starts, code-switching, all fine.

### Bucket C: Shop vocabulary check (5 minutes of chat)

Short conversation to catch terms the bot should know:

- What does he call cement in the shop — "cement", "simat", specific
  brand names?
- What's his word for sand — "reti", "balu", "sand"?
- What's his unit for gitti — "brass", "CFT", something local?
- What does he call the delivery truck — "gaadi", "truck", "tempo"?
- What does he call his nephew when giving commands — by name, by
  relation, by nickname?
- Any Indori-specific words we won't find in a Hindi dictionary?

This goes into the classifier's system prompt so the bot doesn't treat
local words as unknown.

## Suggested WhatsApp message to send him

Feel free to edit. Keeps it short and ask-specific:

> Bhaiya, ek chhota testing kar raha hoon apne wale voice-bot ka. Aapki
> madad chahiye 30 minute ke liye — ek baar setup, phir do hafte tak
> aap normal use kariye, jo bhi galat ho mujhe WhatsApp kar dijiye.
>
> Shuruaat mein teen cheezein chahiye:
>
> 1. Aapke top 15-20 contacts ki list — naam, role (supplier/worker/
>    customer/family), phone number. Jaise aap unko bulate hain shop
>    par (Sharma ji, accountant ji, Ramu bhaiya — wohi).
>
> 2. 15-20 chhote voice notes — jo commands aap din bhar bolte hain
>    (Rajesh ko call karo, Sharma ji ko message, kal subah reminder,
>    gitti wala ko bolo dilli road par pahunche — jo bhi aap naturally
>    bolte hain). Ek-ek alag voice note mein.
>
> 3. 5 minute baat — shop ke kuch local words jo system ko pata hone
>    chahiye (reti, gitti, brass, etc.).
>
> 30 minute ka video call ya phone karke sab ek saath nipta denge.
> Kab convenient hai aapko?

## How this rolls into our existing work

Once we have bhaiya's contacts and voice samples:

1. His contact list feeds directly into what the next session
   (`SPEC_NEXT_SESSION.md`-area work) will use to prototype the
   contact-context injection into the classifier prompt. That's the
   fix for "Mountain G" / "Aamu" / "Permanent".

2. His voice samples join the corpus in `recordings/` and can be run
   through `scripts/transcribe_folder.py`, `scripts/classify_transcripts.py`,
   and `scripts/test_biometric_ecapa.py` to benchmark how the current
   pipeline holds up on real shop audio — without leaving my desk.

3. The terminology list becomes the first entry in a shop-vocabulary
   layer that the PRD's three-layer schema (general, vertical,
   shop-specific) has always implied but we haven't built.

## What I'd push back on him doing

- **Not** recording a long continuous session of all 144 v2-brief
  phrases. That's for field recording with the market-visit team, not
  for the actual shopkeeper — he's a busy user, not a data-collection
  asset.
- **Not** enrolling family members' voices initially. Start with
  bhaiya's voice only; once verification works for him, add nephew and
  father as additional enrolled speakers (multi-user support).
- **Not** turning voice verification to `strict` on day one. Start at
  `medium`, see how often it false-rejects his real commands, tighten
  only if false-accepts become a concern.

## Success criteria (what "it worked" looks like)

At end of two weeks, any of these is a green light to continue:

- He's sent ≥ 30 voice commands with ≥ 80% producing the correct
  intent action on the first try.
- He's flagged ≤ 5 specific bugs and they're all fixable without
  schema changes.
- He says the phrase "kaam ka hai" or equivalent unprompted.

Any of these is a red flag:

- He stops using it before day 7.
- Biometric rejects his own voice on more than 3 of the first 20
  commands.
- Classifier routes messages as delegates (or vice versa) more than
  20% of the time.

If a red flag hits, pause the pilot, diagnose, and don't push him to
continue out of courtesy — the point is to find the failure, not to
save face.
