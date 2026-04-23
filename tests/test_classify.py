"""Offline evaluation harness for the intent classifier.

Run this after filling in your .env to verify the Gemini prompt produces
correct classifications on realistic Hindi/code-mixed inputs. This saves
iteration time versus testing through the full Telegram bot loop.

Cases are organized by edge category. Every case carries at least one
category tag. The runner emits a per-case stdout summary plus a
machine-readable JSON report at tests/last_run.json with per-intent,
per-category, and overall accuracy rollups.

Current contract: only the intent label is hard-asserted. recipient_name
is loose-asserted when an expected value is provided. The three
intent-scoped body fields (message_body, reminder_text, task_description)
are loose-asserted for message/delegate/reminder cases via body_passed.
confidence, clarification_needed, scheduled_time, channel, and
followup_check are reported in the JSON output but not asserted, so we
can observe model behavior across edge categories before committing to
a stricter contract.

Schema friction encountered while writing test cases is logged by hand to
SCHEMA_NOTES.md at the repo root, not by this runner.

Usage:
    python -m tests.test_classify
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows terminals default to cp1252 for stdout, which can't encode the
# Unicode ellipsis we use for body truncation or arbitrary characters
# that Gemini may emit inside clarification_needed. Reconfigure to UTF-8
# at module load so the harness runs cleanly on any OS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.services.classify import classify_intent


CATEGORIES = [
    "simple_baseline",
    "honorifics",
    "role_only_references",
    "multi_intent_compound",
    "scheduled_time_iso",
    "scheduled_time_relative_hindi",
    "scheduled_time_relative_english",
    "scheduled_time_kal",
    "scheduled_time_shaam_ko",
    "ambiguous_clarification",
    "off_topic_no_match",
    # Future-phase categories added 2026-04-22 when the intent taxonomy grew
    # from 4 to 12. Each has 2 representative cases. See SPEC.md for scope.
    "future_order",
    "future_collection",
    "future_supplier_payment",
    "future_inventory",
    "future_price_check",
    "future_worker",
    "future_summary",
    # Bill intent added on the Dates branch (2026-04-22) — bill-generation
    # prototype. Scope=in_scope, exercises nested bill_items extraction.
    "bill_single_item",
    "bill_multi_item",
]


# Maps the three intents that carry a body to the intent-scoped field
# that should hold it after the content-split spec (2026-04-19).
BODY_FIELD_BY_INTENT = {
    "message": "message_body",
    "delegate": "task_description",
    "reminder": "reminder_text",
}


# Each case: {input, categories, expected_intent, expected_recipient (optional)}
# Intent is the only hard-asserted field. Recipient is loose-asserted via
# substring match when expected_recipient is provided and intent != "unknown".
TEST_CASES: list[dict] = [
    # ---- Existing 12 cases, retroactively tagged ----

    {
        "input": "Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye",
        "categories": ["scheduled_time_kal"],
        "expected_intent": "message",
        "expected_recipient": "Rajesh",
    },
    {
        "input": "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo",
        "categories": ["role_only_references"],
        "expected_intent": "message",
        "expected_recipient": "supplier",
    },
    {
        "input": "Send message to Sharma ji that payment will be done next week",
        "categories": ["honorifics"],
        "expected_intent": "message",
        "expected_recipient": "Sharma",
    },
    {
        "input": "3 baje yaad dilana Rajesh ko call karna hai",
        "categories": ["scheduled_time_iso"],
        "expected_intent": "reminder",
    },
    {
        "input": "Kal subah reminder lagana bank jaana hai",
        "categories": ["scheduled_time_kal"],
        "expected_intent": "reminder",
    },
    {
        "input": "30 minute baad yaad dilana godown check karna hai",
        "categories": ["scheduled_time_relative_hindi"],
        "expected_intent": "reminder",
    },
    {
        "input": "Ramu ko bolo Praveen ko call kare aur delivery confirm kare",
        "categories": ["multi_intent_compound"],
        "expected_intent": "delegate",
        "expected_recipient": "Ramu",
    },
    {
        # delegate intent that contains a time. The schema's scheduled_time
        # field is documented as reminder-only; logged in SCHEMA_NOTES.md.
        "input": "Driver ko bolo 10 baje site par pahunche",
        "categories": ["role_only_references", "scheduled_time_iso"],
        "expected_intent": "delegate",
        "expected_recipient": "driver",
    },
    {
        "input": "Driver ko call karo",
        "categories": ["role_only_references"],
        "expected_intent": "call",
        "expected_recipient": "driver",
    },
    {
        "input": "Rajesh ji ko phone lagao",
        "categories": ["honorifics"],
        "expected_intent": "call",
        "expected_recipient": "Rajesh",
    },
    {
        "input": "Call Ramu",
        "categories": ["simple_baseline"],
        "expected_intent": "call",
        "expected_recipient": "Ramu",
    },
    {
        "input": "Haan theek hai",
        "categories": ["off_topic_no_match"],
        "expected_intent": "unknown",
    },

    # ---- New cases ----

    # honorifics
    {
        "input": "Sharma sahab ko WhatsApp karo, kal milte hain shop par",
        "categories": ["honorifics"],
        "expected_intent": "message",
        "expected_recipient": "Sharma",
    },
    {
        "input": "Ramu bhaiya ko bolo godown ki chaabi laao",
        "categories": ["honorifics"],
        "expected_intent": "delegate",
        "expected_recipient": "Ramu",
    },

    # role_only_references
    {
        "input": "The driver ko call karo abhi",
        "categories": ["role_only_references"],
        "expected_intent": "call",
        "expected_recipient": "driver",
    },
    {
        "input": "Naukar ko bolo dukaan band kare",
        "categories": ["role_only_references"],
        "expected_intent": "delegate",
        "expected_recipient": "naukar",
    },

    # multi_intent_compound
    {
        "input": "Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana",
        "categories": ["multi_intent_compound"],
        "expected_intent": "message",
        "expected_recipient": "Rajesh",
    },
    {
        "input": "Driver ko bolo godown jaaye aur ek ghante baad yaad dilana follow up karna hai",
        "categories": ["multi_intent_compound"],
        "expected_intent": "delegate",
        "expected_recipient": "driver",
    },
    {
        "input": "Sharma ji ko call karo aur baad mein yaad dilana payment ka pucha tha",
        "categories": ["multi_intent_compound"],
        "expected_intent": "call",
        "expected_recipient": "Sharma",
    },

    # scheduled_time_iso
    {
        "input": "Subah 8:30 baje yaad dilana shop kholne ka",
        "categories": ["scheduled_time_iso"],
        "expected_intent": "reminder",
    },

    # scheduled_time_relative_hindi
    {
        "input": "Thodi der mein yaad dilana cement order karna hai",
        "categories": ["scheduled_time_relative_hindi"],
        "expected_intent": "reminder",
    },
    {
        "input": "Abhi yaad dilana driver ko payment dena hai",
        "categories": ["scheduled_time_relative_hindi"],
        "expected_intent": "reminder",
    },

    # scheduled_time_relative_english
    {
        "input": "In 30 minutes remind me to close the shop",
        "categories": ["scheduled_time_relative_english"],
        "expected_intent": "reminder",
    },
    {
        "input": "Remind me in two hours to call the supplier",
        "categories": ["scheduled_time_relative_english"],
        "expected_intent": "reminder",
    },

    # scheduled_time_kal
    {
        "input": "Kal shaam yaad dilana account ki entry karni hai",
        "categories": ["scheduled_time_kal"],
        "expected_intent": "reminder",
    },

    # scheduled_time_shaam_ko
    {
        "input": "Shaam ko yaad dilana godown band karna hai",
        "categories": ["scheduled_time_shaam_ko"],
        "expected_intent": "reminder",
    },
    {
        "input": "Raat ko 9 baje yaad dilana ledger check karna hai",
        "categories": ["scheduled_time_shaam_ko", "scheduled_time_iso"],
        "expected_intent": "reminder",
    },

    # ambiguous_clarification
    {
        # Subtle: could be message ("tell Rajesh at 5"), delegate ("instruct
        # Rajesh to do something at 5"), or reminder ("remind me at 5 about
        # Rajesh"). Classifier should refuse and ask for clarification.
        "input": "Rajesh ko 5 baje bolo",
        "categories": ["ambiguous_clarification"],
        "expected_intent": "unknown",
        "expected_recipient": "Rajesh",
    },
    {
        # Reminder intent is clear but scheduled_time is too vague to act on.
        # Tests whether classifier surfaces the missing-detail through
        # clarification_needed (reported, not asserted today).
        "input": "Yaad dilana aaj",
        "categories": ["ambiguous_clarification"],
        "expected_intent": "reminder",
    },
    {
        "input": "Kuch karo",
        "categories": ["ambiguous_clarification"],
        "expected_intent": "unknown",
    },

    # off_topic_no_match
    {
        "input": "Namaste",
        "categories": ["off_topic_no_match"],
        "expected_intent": "unknown",
    },
    {
        "input": "Kya haal hai",
        "categories": ["off_topic_no_match"],
        "expected_intent": "unknown",
    },

    # ---- Future-phase intent cases (added 2026-04-22) ----
    # These test that the 7 new shop-domain intents are correctly
    # recognised. Hard-asserts intent + scope. Body extraction is not
    # required for future-phase cases — slot extraction quality will
    # get attention after real usage data accumulates.

    # future_order
    {
        "input": "Sharma ji ko 50 bori cement ka order kar do",
        "categories": ["future_order", "honorifics"],
        "expected_intent": "order",
        "expected_scope": "future_phase",
        "expected_recipient": "Sharma",
    },
    {
        "input": "Rajesh ke order ka status kya hai",
        "categories": ["future_order"],
        "expected_intent": "order",
        "expected_scope": "future_phase",
        "expected_recipient": "Rajesh",
    },

    # future_collection
    {
        "input": "Rajesh ka kitna pending hai",
        "categories": ["future_collection"],
        "expected_intent": "collection",
        "expected_scope": "future_phase",
        "expected_recipient": "Rajesh",
    },
    {
        "input": "Kisne paisa dena hai aaj",
        "categories": ["future_collection"],
        "expected_intent": "collection",
        "expected_scope": "future_phase",
    },

    # future_supplier_payment
    {
        "input": "Sharma ji ko kitna paisa dena hai",
        "categories": ["future_supplier_payment", "honorifics"],
        "expected_intent": "supplier_payment",
        "expected_scope": "future_phase",
        "expected_recipient": "Sharma",
    },
    {
        "input": "Aaj supplier ka payment kya hai",
        "categories": ["future_supplier_payment", "role_only_references"],
        "expected_intent": "supplier_payment",
        "expected_scope": "future_phase",
    },

    # future_inventory
    {
        "input": "Cement kitna bacha hai",
        "categories": ["future_inventory"],
        "expected_intent": "inventory",
        "expected_scope": "future_phase",
    },
    {
        "input": "Godown mein 10 bori cement aayi hai",
        "categories": ["future_inventory"],
        "expected_intent": "inventory",
        "expected_scope": "future_phase",
    },

    # future_price_check
    {
        "input": "Aaj gitti ka rate kya chal raha hai",
        "categories": ["future_price_check"],
        "expected_intent": "price_check",
        "expected_scope": "future_phase",
    },
    {
        "input": "Cement ka wholesale rate bata",
        "categories": ["future_price_check"],
        "expected_intent": "price_check",
        "expected_scope": "future_phase",
    },

    # future_worker
    {
        "input": "Ramu kahan hai abhi",
        "categories": ["future_worker"],
        "expected_intent": "worker",
        "expected_scope": "future_phase",
        "expected_recipient": "Ramu",
    },
    {
        "input": "Aaj kitne naukar aaye hain",
        "categories": ["future_worker", "role_only_references"],
        "expected_intent": "worker",
        "expected_scope": "future_phase",
    },

    # future_summary
    {
        "input": "Aaj kitna business hua",
        "categories": ["future_summary"],
        "expected_intent": "summary",
        "expected_scope": "future_phase",
    },
    {
        "input": "Is hafte ka total kya hai",
        "categories": ["future_summary"],
        "expected_intent": "summary",
        "expected_scope": "future_phase",
    },

    # ---- Bill intent cases (added 2026-04-22, Dates branch) ----
    # These test nested bill_items extraction.

    {
        "input": "Rajesh ke liye 5 carton Date crown fard bill banao, rate 3000 per carton",
        "categories": ["bill_single_item"],
        "expected_intent": "bill",
        "expected_scope": "in_scope",
        "expected_recipient": "Rajesh",
    },
    {
        "input": "Bill for Mukesh: 10 cartons Medjool dates at 4200 per carton",
        "categories": ["bill_single_item"],
        "expected_intent": "bill",
        "expected_scope": "in_scope",
        "expected_recipient": "Mukesh",
    },
    {
        "input": "Sharma ji ka bill banao, 3 carton Date crown premium fard rate 3500, aur 2 box Ajwa rate 2800",
        "categories": ["bill_multi_item", "honorifics"],
        "expected_intent": "bill",
        "expected_scope": "in_scope",
        "expected_recipient": "Sharma",
    },
    {
        "input": "Suresh ke liye 4 box Mabroom 2800, aur 2 carton Kimia 3200 ka bill banao",
        "categories": ["bill_multi_item"],
        "expected_intent": "bill",
        "expected_scope": "in_scope",
        "expected_recipient": "Suresh",
    },
]


REPORT_PATH = Path(__file__).parent / "last_run.json"


def evaluate_case(case: dict) -> dict:
    """Run one case through the classifier and build the per-case record."""
    expected_intent = case["expected_intent"]
    expected_recipient = case.get("expected_recipient")

    expected_scope = case.get("expected_scope")

    record: dict = {
        "input": case["input"],
        "categories": list(case["categories"]),
        "expected": {
            "intent": expected_intent,
            "recipient": expected_recipient,
            "scope": expected_scope,
        },
        "actual": None,
        "intent_passed": False,
        "recipient_passed": None,
        "scope_passed": None,
        "body_passed": None,
        "latency_ms": None,
        "error": None,
    }

    t0 = time.perf_counter()
    try:
        result = classify_intent(case["input"])
        record["latency_ms"] = int((time.perf_counter() - t0) * 1000)
        record["actual"] = result.model_dump()
        record["intent_passed"] = result.intent == expected_intent

        if expected_scope is not None:
            record["scope_passed"] = result.scope == expected_scope

        if expected_recipient is not None and expected_intent != "unknown":
            actual_rec = (result.recipient_name or "").lower()
            exp_rec = expected_recipient.lower()
            record["recipient_passed"] = (
                exp_rec in actual_rec or (actual_rec != "" and actual_rec in exp_rec)
            )

        # Loose-asserted (reported, not gated): for message/delegate/reminder,
        # verify the corresponding intent-scoped body field is non-empty.
        body_field = BODY_FIELD_BY_INTENT.get(expected_intent)
        if body_field is not None:
            actual_body = getattr(result, body_field, None)
            record["body_passed"] = bool(actual_body and actual_body.strip())
    except Exception as e:
        record["latency_ms"] = int((time.perf_counter() - t0) * 1000)
        record["error"] = f"{type(e).__name__}: {e}"

    return record


def build_per_intent(records: list[dict]) -> dict[str, dict]:
    by_intent: dict[str, dict] = {}
    for r in records:
        intent = r["expected"]["intent"]
        bucket = by_intent.setdefault(intent, {"count": 0, "passed": 0})
        bucket["count"] += 1
        if r["intent_passed"]:
            bucket["passed"] += 1
    for bucket in by_intent.values():
        bucket["accuracy"] = (
            round(bucket["passed"] / bucket["count"], 3) if bucket["count"] else 0.0
        )
    return dict(sorted(by_intent.items()))


def build_per_category(records: list[dict]) -> dict[str, dict]:
    # Preserve CATEGORIES order in the JSON output for stable diffs.
    rollup: dict[str, dict] = {c: {"count": 0, "passed": 0} for c in CATEGORIES}
    for r in records:
        for c in r["categories"]:
            if c not in rollup:
                # Unknown category in a test case. Surface but do not crash.
                rollup[c] = {"count": 0, "passed": 0}
            rollup[c]["count"] += 1
            if r["intent_passed"]:
                rollup[c]["passed"] += 1
    for bucket in rollup.values():
        bucket["accuracy"] = (
            round(bucket["passed"] / bucket["count"], 3) if bucket["count"] else 0.0
        )
    return rollup


def build_body_populated(records: list[dict]) -> dict[str, dict]:
    """Rollup of body-field population for message/delegate/reminder cases.

    Separate from intent accuracy: a case can have the right intent but miss
    its body field (or vice versa). Reported but not gated.
    """
    rollup: dict[str, dict] = {
        "message": {"populated": 0, "total": 0},
        "delegate": {"populated": 0, "total": 0},
        "reminder": {"populated": 0, "total": 0},
    }
    for r in records:
        intent = r["expected"]["intent"]
        if intent not in rollup:
            continue
        rollup[intent]["total"] += 1
        if r.get("body_passed") is True:
            rollup[intent]["populated"] += 1
    for bucket in rollup.values():
        bucket["accuracy"] = (
            round(bucket["populated"] / bucket["total"], 3)
            if bucket["total"] else 0.0
        )
    return rollup


def build_scope_rollup(records: list[dict]) -> dict:
    """Rollup of scope accuracy on cases that declared expected_scope.
    Skips cases that didn't declare one (older cases added before the
    2026-04-22 expansion). Reported in the JSON + stdout summary."""
    total = 0
    passed = 0
    for r in records:
        if r.get("scope_passed") is None:
            continue
        total += 1
        if r["scope_passed"]:
            passed += 1
    return {
        "count": total,
        "passed": passed,
        "accuracy": round(passed / total, 3) if total else 0.0,
    }


def build_overall(records: list[dict]) -> dict:
    count = len(records)
    passed = sum(1 for r in records if r["intent_passed"])
    return {
        "count": count,
        "passed": passed,
        "accuracy": round(passed / count, 3) if count else 0.0,
    }


def print_case_line(i: int, record: dict) -> None:
    status = "OK" if record["intent_passed"] else "FAIL"
    cats = ",".join(record["categories"]) or "-"
    print(f"[{status}] case {i:>2} [{cats}]: {record['input']}")

    if record["error"]:
        print(f"    error: {record['error']}")
        return

    actual = record["actual"] or {}
    intent = actual.get("intent")
    confidence = actual.get("confidence")
    recipient = actual.get("recipient_name")
    sched = actual.get("scheduled_time")
    clarif = actual.get("clarification_needed")

    pieces = [f"intent={intent}", f"confidence={confidence:.2f}" if confidence is not None else "confidence=?"]
    if recipient is not None:
        pieces.append(f"recipient={recipient}")
    if sched is not None:
        pieces.append(f"sched={sched}")

    # Body indicator: first non-null of the three intent-scoped body fields.
    # Truncation rule: strip whitespace first, then if > 40 chars keep the
    # first 39 and append a Unicode ellipsis.
    body_label = "none"
    for field in ("message_body", "task_description", "reminder_text"):
        value = actual.get(field)
        if value:
            stripped = value.strip()
            if len(stripped) > 40:
                stripped = stripped[:39] + "\u2026"
            body_label = f'{field}:"{stripped}"'
            break
    pieces.append(f"body={body_label}")

    pieces.append(f"latency={record['latency_ms']}ms")
    print(f"    {'  '.join(pieces)}")

    if clarif:
        print(f"    clarification_needed: {clarif}")

    if not record["intent_passed"]:
        print(f"    expected intent={record['expected']['intent']}, got {intent}")
    if record["recipient_passed"] is False:
        print(
            f"    expected recipient~={record['expected']['recipient']}, got {recipient}"
        )


def print_per_intent_block(per_intent: dict[str, dict]) -> None:
    print("\nPer-intent accuracy:")
    if not per_intent:
        print("  (none)")
        return
    width = max(len(k) for k in per_intent)
    for intent, b in per_intent.items():
        pct = b["accuracy"] * 100
        print(f"  {intent.ljust(width)}  {b['passed']}/{b['count']}  {pct:5.1f}%")


def print_per_category_block(per_category: dict[str, dict]) -> None:
    """Stdout-only: order ascending by accuracy (worst first), ties by name.
    Categories with zero cases are skipped."""
    print("\nPer-category accuracy (worst first):")
    rows = [(name, b) for name, b in per_category.items() if b["count"] > 0]
    if not rows:
        print("  (none)")
        return
    rows.sort(key=lambda x: (x[1]["accuracy"], x[0]))
    width = max(len(name) for name, _ in rows)
    for name, b in rows:
        pct = b["accuracy"] * 100
        print(f"  {name.ljust(width)}  {b['passed']}/{b['count']}  {pct:5.1f}%")


def print_body_populated_block(body_rollup: dict[str, dict]) -> None:
    print("\nBody fields populated:")
    width = max(len(k) for k in body_rollup)
    for intent_name in ("message", "delegate", "reminder"):
        b = body_rollup[intent_name]
        pct = b["accuracy"] * 100
        print(f"  {intent_name.ljust(width)}  {b['populated']}/{b['total']}  {pct:5.1f}%")


def print_scope_block(scope_rollup: dict) -> None:
    if scope_rollup["count"] == 0:
        return
    pct = scope_rollup["accuracy"] * 100
    print(
        f"\nScope accuracy (on cases asserting expected_scope): "
        f"{scope_rollup['passed']}/{scope_rollup['count']} ({pct:.1f}%)"
    )


def print_overall_block(overall: dict) -> None:
    pct = overall["accuracy"] * 100
    print(f"\nOverall: {overall['passed']}/{overall['count']} ({pct:.1f}%)")


def run() -> int:
    started = datetime.now(timezone.utc).isoformat()
    print(f"Run started at {started}")
    print(f"Cases: {len(TEST_CASES)}\n")

    records: list[dict] = []
    for i, case in enumerate(TEST_CASES, 1):
        record = evaluate_case(case)
        records.append(record)
        print_case_line(i, record)

    per_intent = build_per_intent(records)
    per_category = build_per_category(records)
    body_populated = build_body_populated(records)
    scope_rollup = build_scope_rollup(records)
    overall = build_overall(records)

    print("\n" + "=" * 60)
    print_per_intent_block(per_intent)
    print_per_category_block(per_category)
    print_body_populated_block(body_populated)
    print_scope_block(scope_rollup)
    print_overall_block(overall)

    report = {
        "run_started_at": started,
        "cases": records,
        "per_intent": per_intent,
        "per_category": per_category,
        "body_populated": body_populated,
        "scope_rollup": scope_rollup,
        "overall": overall,
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nJSON report written to {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(run())
