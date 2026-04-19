# Claude Code Kickoff — ShopSaarthi

This file is the starting point for any Claude Code session on ShopSaarthi. The product is defined in `ShopSaarthi_PRD_v0.2.md`; code-level conventions are in `CLAUDE.md`; this file defines how we work together.

Read this file fully before doing anything else. Then read `ShopSaarthi_PRD_v0.2.md` and `CLAUDE.md`. Then follow the steps below in order. Do not skip ahead, and do not start writing code until Step 4.

## Current phase

Phase 1: Core Voice Assistant with Trust Layer (April - May 2026, 3-4 weeks).

Scope is limited to four core intents via Telegram, plus voice biometric enrollment and verification as a trust feature:

1. Send message (tap-to-send via shopkeeper's own WhatsApp or SMS)
2. Set reminder (Telegram ping at scheduled time)
3. Delegate task (instruction to another person plus follow-up verification reminder)
4. Make call (tap-to-dial via shopkeeper's own carrier)

Voice enrollment is part of Phase 1: the shopkeeper records 5 phrases, the system stores embeddings, and subsequent voice commands are verified against the enrolled profile with a configurable threshold (strict, medium, loose, off).

Phase 1 success is defined as the owner's brother using the system for 14 consecutive days in his building materials shop without abandoning it, plus voice verification false-rejection rate under 5% for the enrolled user. See PRD Section 4 (Phase 1) for the full definition.

Phase 1b (adds bill generation with Tally XML export) and Phase 2+ are out of scope for now. If something feels like it belongs to a later phase, flag it and move on.

## About the person you're working with

Ashish (AV) is the product owner and sole developer. He is an experienced builder (FastAPI, Postgres, Next.js, AWS) and a Teaching Assistant Professor at Gies College of Business, not a full-time software engineer. He has shipped real products with Claude Code.

A `CLAUDE.md` file already exists in this repo with architecture and style conventions. AV has not previously used skills, hooks, subagents, or MCP servers with Claude Code. Treat this as an opportunity to introduce those capabilities gradually, in context, only when they would genuinely help this project.

He prefers plain professional language. No em-dashes. No bold or italics in prose. Understated tone. Avoid hype words.

## How we work: the four steps

### Step 1: Interview before coding

When AV gives you a task or feature to build, do not start coding. Instead, interview him using the AskUserQuestion tool. Focus on the business logic decisions he probably has not spelled out — edge cases, what happens when a user does something unexpected, which behaviors are hard requirements vs. choices you would otherwise make on your own.

Do not ask obvious questions. Dig into the parts that are easy to get wrong and expensive to change later. Keep interviewing until you have covered the non-obvious parts of the task.

For ShopSaarthi Phase 1 specifically, pay attention to:

- What happens when Hindi or code-mixed speech is ambiguous, partially transcribed, or the intent confidence is low
- What happens when a contact reference is ambiguous (multiple matches) versus unknown (no match)
- How voice verification failures are communicated to the shopkeeper, and how the configurable threshold is surfaced
- What the shopkeeper sees in Telegram vs. what gets forwarded via tap-to-send links to WhatsApp or SMS
- How reminders and delegated-task follow-ups interact when multiple fire close together
- What happens when the enrollment flow is interrupted mid-way
- How text-message input differs from voice input in handling (voice gets verification, text does not)

Once the interview is complete, write or update `SPEC.md` for the feature. The spec should be reviewable in under five minutes.

### Step 2: Discuss Claude Code features

After the spec is written and before planning the implementation, pause and have a short conversation with AV about which Claude Code features could add value for this specific task or for ShopSaarthi broadly at this phase. Do not give a generic list. Recommend only what fits this project right now, and explain the tradeoff for each.

Consider and bring up only where relevant:

- Extensions to the existing `CLAUDE.md` capturing conventions that have emerged during this task
- Skills in `.claude/skills/` for things that are sometimes relevant (for example: a Hindi-ASR-evaluation skill, a Telegram-bot-patterns skill, a Gemini-prompt-iteration skill)
- Hooks in `.claude/settings.json` for things that must happen every time (for example: running `tests/test_classify.py` after any change to `app/services/classify.py`, ruff and mypy after Python edits, blocking writes to db/models.py without explicit approval)
- Subagents in `.claude/agents/` for isolated investigation (for example: a classifier-accuracy reviewer, a voice-verification-threshold tuner)
- MCP servers, especially Postgres or Telegram, if direct querying would help
- Plan Mode for multi-file features like bill generation or voice enrollment flows
- Non-interactive mode (`claude -p`) for batch work like evaluating ASR accuracy across a test set of recordings

Recommend at most two things per kickoff. AV is learning these one at a time. If nothing new fits this task, say so clearly and move on. "None of these would help today" is a valid answer.

### Step 3: Plan

Once the feature decision is made (or deferred), enter Plan Mode and draft a detailed implementation plan against the spec. Do not write any code yet. The plan should name every file that will change, the order of changes, and how the result will be verified.

Pause here and let AV review the plan before proceeding.

### Step 4: Implement and verify

Switch to Normal Mode. Implement against the plan. Run tests after each meaningful change. If something is off, course-correct before moving on rather than accumulating drift.

For Phase 1, verification specifically includes: the four core intents classify correctly on the curated test utterances in `tests/test_classify.py`, voice enrollment completes without errors, speaker verification produces expected match or rejection outcomes, end-to-end latency stays under 5 seconds including verification, and the brother's shop test flow still works end to end.

### Step 5: Commit

Commit with a descriptive message referencing the spec. If `gh` is available and AV uses PRs on this repo, open one against the appropriate branch.

## Handling bugs and unexpected behavior

When AV reports a bug or unexpected behavior, do not start fixing. First ask for the specific input that triggered it, the observed output, and the expected output. Then reproduce it deterministically before attempting a fix. If it cannot be reproduced, say so rather than guessing.

Debugging is the highest-risk activity in a Claude Code session because fixes often introduce new problems. Slow down here. After a fix, run `tests/test_classify.py` and any other relevant tests to confirm the fix did not regress existing behavior.

## Things to flag, not solve

These come up often in ShopSaarthi and are decisions for AV, not for you. Raise them and wait:

- Any change to the eventual three-layer schema (general ontology, vertical profile, shop-specific layer), even if we are not implementing it yet
- Any choice between closed-source and open-source models for a new task
- Anything that touches data collection, consent, or retention
- Anything that would change pricing assumptions or phase boundaries
- Any change to the lab protocols documented in the PRD
- Any change to how voice verification works, including threshold values

## If something is unclear

Ask. AV would rather answer a clarifying question than review code that solved the wrong problem. The AskUserQuestion tool is the right way to do this for structured decisions; regular chat is fine for open-ended ones.

## What to do if this file and the PRD conflict

The PRD defines what ShopSaarthi is. `CLAUDE.md` defines code-level conventions. This file defines how we work on the project. If they contradict each other:

- On product scope: the PRD wins. Tell AV and we update this file.
- On code conventions: `CLAUDE.md` wins. Tell AV if something in this file disagrees.
- On process: this file wins.
