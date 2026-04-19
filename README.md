# ShopSaarthi Bot

Voice-first Telegram assistant for Indian small and medium businesses. Phase 1 prototype.

## What it does

Four core intents via voice (Hindi or mixed Hindi-English) through Telegram:

1. **Send message** — "ABC ko WhatsApp karo, message hai..." → composes message, provides tap-to-send link (shopkeeper sends via their own WhatsApp)
2. **Set reminder** — "3 baje yaad dilana Rajesh ko call karna hai" → schedules Telegram ping
3. **Delegate task** — "Ramu ko bolo Praveen ko call kare" → sends instruction, schedules follow-up
4. **Make call** — "Driver ko call karo" → looks up contact, provides tap-to-dial link (free via shopkeeper's own carrier)

Plus a voice biometric trust layer: the shopkeeper enrolls their voice once, and subsequent commands are verified so customers watching can see the bot responds only to the owner.

**Cost to shopkeeper:** zero for messaging and calling (uses their own WhatsApp/SMS/phone).
**Cost to operator:** Sarvam ASR + Gemini LLM + small infrastructure. Roughly ₹170-250/month per shop in Phase 1, dropping to ₹60-130/month at Phase 3-4 scale.

## Stack

- Python 3.11
- python-telegram-bot 21.6
- FastAPI (for Phase 1b accountant dashboard)
- PostgreSQL production, SQLite for local dev
- Sarvam Saarika v2.5 (Hindi ASR)
- Google Gemini 2.5 Flash-Lite (intent classification)
- Resemblyzer (speaker verification)
- APScheduler 3.10 (persistent scheduled reminders)

## Setup

```bash
cd shopsaarthi-bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python -m app.db.init_db
python -m app.main
```

## Required API keys

- `TELEGRAM_BOT_TOKEN` — from BotFather on Telegram
- `SARVAM_API_KEY` — from dashboard.sarvam.ai (₹1000 free credits on signup)
- `GEMINI_API_KEY` — from ai.google.dev (generous free tier)
- `DATABASE_URL` — Postgres URL, or SQLite path for dev

## First user setup

1. `/start` in Telegram to initialize
2. `/enroll` to record your voice (5 phrases, about 2 minutes)
3. `/addcontact Ramu 9876543210 servant` for each person you will reference
4. Send voice messages with your commands

## Commands reference

**Core flow:**
- Voice message — speak any of the four intents naturally
- Text message — same intents work via text if voice is awkward

**Voice management:**
- `/enroll` — first-time voice enrollment
- `/reenroll` — add more samples to improve profile
- `/security strict|medium|loose|off` — set verification threshold
- `/voicestatus` — check current enrollment and security
- `/resetvoice` — clear and start over

**Contacts:**
- `/addcontact <name> <phone> [role]` — add a contact
- `/contacts` — list all contacts
- `/deletecontact <name>` — remove a contact

**General:**
- `/start` — initialize the bot
- `/help` — show welcome message
- `/cancel` — cancel any ongoing flow (like enrollment)

## Architecture

```
app/
  main.py                    # Entry point, wires Telegram handlers and scheduler
  config.py                  # Settings and env vars
  handlers/
    voice.py                 # Main voice orchestrator (verify + transcribe + classify + route)
    enrollment.py            # Voice enrollment ConversationHandler
    message.py               # Send message intent
    reminder.py              # Set reminder intent
    delegate.py              # Delegate task intent
    call.py                  # Make call intent
    contacts.py              # Contact management commands
  services/
    transcribe.py            # Sarvam ASR wrapper
    classify.py              # Gemini intent classification
    contact_resolver.py      # Fuzzy name-to-contact lookup
    verify_speaker.py        # Resemblyzer speaker verification
  db/
    models.py                # User, Contact, Task, VoiceProfile
    session.py               # DB session factory
    init_db.py               # Create tables
tests/
  test_classify.py           # Offline classifier evaluation
```

## Testing

Before deploying to your brother:

```bash
# Run the offline classifier test
python -m tests.test_classify
```

Iterate on the system prompt in `app/services/classify.py` until all cases pass. Then test end-to-end via your own Telegram account.

## Phase 1 scope

What is included:
- Four core intents (message, reminder, delegate, call)
- Voice enrollment with configurable security threshold
- Contact management
- Telegram-only interface

What is coming in Phase 1b (next 2 weeks after Phase 1 works):
- Bill generation with PDF output
- Tally XML export for accountant workflow
- Minimal web dashboard for accountant access

What is deferred (Phase 2+):
- Paid beta deployment in Indore
- Multi-vertical expansion
- Intelligence features
- Multi-user support

See `ShopSaarthi_PRD_v0.2.md` (in the parent directory's shopsaarthi folder) for the full roadmap.

## For Claude Code sessions

See `CLAUDE.md` for implementation guidance when picking this up in Claude Code.
