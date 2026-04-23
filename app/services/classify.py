"""Intent classification and entity extraction using Gemini 2.5 Flash-Lite.

This is the core intelligence of the bot. It takes a transcribed utterance
and returns a structured intent object that the handlers can act on.

Flash-Lite was chosen (April 2026 pricing: $0.10/$0.40 per million tokens)
because the task is bounded — only 4 intent types — and the cost per call
at typical utterance lengths is under ₹0.01.

If accuracy is insufficient, the fallback is Gemini 2.5 Flash ($0.30/$2.50)
or Claude Haiku 4.5 ($1/$5). As training data accumulates, migrate to a
fine-tuned Gemma 2B or similar for near-zero marginal cost.
"""
import json
import logging
from typing import Any, Literal, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field, model_validator


# Intent taxonomy expanded on 2026-04-22 from 4 to 12 to let the bot
# recognise shop-domain commands beyond Phase 1's core four. The four
# in-scope intents (message, reminder, delegate, call) are fulfilled by
# existing handlers. The seven future-phase intents are recognised,
# logged, and acknowledged — but not yet fulfilled. See SPEC.md
# (intent-taxonomy-expansion section) and SESSION_NOTES_2026-04-22_intent_expansion.md.
IntentValue = Literal[
    "message", "reminder", "delegate", "call",
    "bill",
    "order", "collection", "supplier_payment",
    "inventory", "price_check", "worker", "summary",
    "unknown",
]

Scope = Literal["in_scope", "future_phase", "unknown"]

IN_SCOPE_INTENTS: frozenset[str] = frozenset({"message", "reminder", "delegate", "call", "bill"})
FUTURE_PHASE_INTENTS: frozenset[str] = frozenset({
    "order", "collection", "supplier_payment",
    "inventory", "price_check", "worker", "summary",
})


def scope_for_intent(intent: str) -> str:
    """Canonical mapping from intent string to scope. Used by tests and
    by the router for defensive double-checking of the model's output."""
    if intent in IN_SCOPE_INTENTS:
        return "in_scope"
    if intent in FUTURE_PHASE_INTENTS:
        return "future_phase"
    return "unknown"


# Hindi-ish labels for the future-phase echo the router sends back.
# Kept short. Used as a fill-in for the echo template in voice.py.
INTENT_LABEL_HINDI: dict[str, str] = {
    "order":             "order ke baare mein",
    "collection":        "customer ki payment ke baare mein",
    "supplier_payment":  "supplier ki payment ke baare mein",
    "inventory":         "stock ke baare mein",
    "price_check":       "rate ke baare mein",
    "worker":            "worker ke baare mein",
    "summary":           "business summary",
}

from app.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)


# Pydantic's model_json_schema() emits standard JSON-Schema metadata
# (title, default, $defs, additionalProperties) that Gemini's stricter Schema
# dialect rejects with "Unknown field for Schema: <name>". It also emits
# `anyOf: [{type: X}, {type: null}]` for Optional fields, which Gemini's SDK
# does not accept; the equivalent there is a single-type schema with
# `nullable: true`. This cleaner is the narrowest fix: walk the schema, drop
# the disallowed keys, inline $refs, and collapse Optional anyOf into nullable.
_GEMINI_DISALLOWED_KEYS = frozenset(
    {"title", "default", "$defs", "additionalProperties"}
)


# Fields that must appear in every Gemini response, even as null, so the
# model doesn't silently drop them. Pydantic defaults still apply on the
# receiving side — this is purely a hint to Gemini that the key must be
# present in the JSON output. Added on the Dates branch (2026-04-22)
# after observing Flash-Lite omit optional fields like bill_items and
# recipient_name even with very explicit prompt instructions.
_FORCE_REQUIRED_TOP_LEVEL: frozenset[str] = frozenset({
    "intent", "scope", "recipient_name", "bill_items", "confidence",
})

# Fields inside bill_items[] that must also be present. Otherwise Gemini
# drops rate/quantity/unit on the nested object even when the top-level
# bill_items key is required.
_FORCE_REQUIRED_BILL_ITEM: frozenset[str] = frozenset({
    "product_name", "quantity", "unit", "rate",
})


def _to_gemini_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Return a Gemini-Schema-compatible dict derived from a Pydantic model."""
    raw = model_cls.model_json_schema()
    defs = raw.get("$defs", {})
    cleaned = _clean_schema(raw, defs)
    # Force the high-value fields to be required in the response JSON.
    # If the field exists in properties, add it to required. Don't
    # invent requireds for fields that don't exist on the schema.
    if isinstance(cleaned, dict) and "properties" in cleaned:
        props = cleaned["properties"]
        existing = set(cleaned.get("required") or [])
        for field in _FORCE_REQUIRED_TOP_LEVEL:
            if field in props:
                existing.add(field)
        cleaned["required"] = sorted(existing)
        # Also mark the nested BillItem fields as required.
        bill_items = props.get("bill_items")
        if isinstance(bill_items, dict):
            items = bill_items.get("items")
            if isinstance(items, dict) and "properties" in items:
                item_props = items["properties"]
                item_req = set(items.get("required") or [])
                for field in _FORCE_REQUIRED_BILL_ITEM:
                    if field in item_props:
                        item_req.add(field)
                items["required"] = sorted(item_req)
    return cleaned


def _clean_schema(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, list):
        return [_clean_schema(item, defs) for item in node]
    if not isinstance(node, dict):
        return node

    if "$ref" in node:
        ref = node["$ref"]
        prefix = "#/$defs/"
        if ref.startswith(prefix):
            target = defs.get(ref[len(prefix):], {})
            merged = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
            return _clean_schema(merged, defs)

    cleaned: dict[str, Any] = {}
    for key, value in node.items():
        if key in _GEMINI_DISALLOWED_KEYS:
            continue
        cleaned[key] = _clean_schema(value, defs)

    if "anyOf" in cleaned:
        variants = cleaned["anyOf"]
        non_null = [
            v for v in variants
            if not (isinstance(v, dict) and v.get("type") == "null")
        ]
        has_null = len(non_null) != len(variants)
        if has_null and len(non_null) == 1:
            cleaned.pop("anyOf")
            cleaned.update(non_null[0])
            cleaned["nullable"] = True

    return cleaned


# Structured output schemas. We define these as Pydantic for runtime validation,
# and pass a JSON schema to Gemini for structured output.


class BillItemExtracted(BaseModel):
    """One line item extracted from a voice bill command. Added on the
    `Dates` branch (2026-04-22) for the bill-generation prototype."""
    product_name: Optional[str] = Field(
        default=None,
        description=(
            "The product as spoken (e.g., 'Date crown fard', 'Ajwa dates'). "
            "Downstream will fuzzy-match this against the shop's product "
            "catalog."
        ),
    )
    quantity: Optional[float] = Field(
        default=None,
        description="Numeric quantity (e.g., 5 for '5 carton').",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit: carton, box, kg, packet, piece, bori, etc.",
    )
    rate: Optional[float] = Field(
        default=None,
        description="Price per unit in INR. Null if the speaker did not state one.",
    )


class IntentClassification(BaseModel):
    """The parsed structure of a shopkeeper's voice command."""
    intent: IntentValue = Field(
        description=(
            "The primary intent. In-scope (bot acts today): 'message', "
            "'reminder', 'delegate', 'call'. Future-phase (bot recognises, "
            "logs, and acknowledges): 'order', 'collection', 'supplier_payment', "
            "'inventory', 'price_check', 'worker', 'summary'. 'unknown' for "
            "utterances that match none."
        )
    )
    scope: Scope = Field(
        default="in_scope",
        description=(
            "Must match the intent's category. message/reminder/delegate/call "
            "=> 'in_scope'. order/collection/supplier_payment/inventory/"
            "price_check/worker/summary => 'future_phase'. unknown => 'unknown'."
        ),
    )
    recipient_name: Optional[str] = Field(
        default=None,
        description="The person the action is directed at (as spoken). For 'reminder', this is the person mentioned in the reminder content, not the reminder itself."
    )
    channel: Optional[str] = Field(
        default=None,
        description="For 'message' intent: 'whatsapp', 'sms', 'telegram', or null if unspecified."
    )
    message_body: Optional[str] = Field(
        default=None,
        description="For 'message' intent only: the text to send to the recipient, as spoken. Null for every other intent."
    )
    reminder_text: Optional[str] = Field(
        default=None,
        description="For 'reminder' intent only: what the shopkeeper wants to be reminded about. Null for every other intent."
    )
    task_description: Optional[str] = Field(
        default=None,
        description="For 'delegate' intent only: the task the recipient is being asked to do, as spoken. Null for every other intent."
    )
    scheduled_time: Optional[str] = Field(
        default=None,
        description="For 'reminder': ISO 8601 time like '2026-04-18T15:00:00' or relative like 'in 30 minutes'. Null otherwise."
    )
    followup_check: Optional[str] = Field(
        default=None,
        description="For 'delegate': what to follow up on later, if implied. Example: 'check if Ramu called Praveen'."
    )
    bill_items: Optional[list[BillItemExtracted]] = Field(
        default=None,
        description=(
            "For 'bill' intent only: up to 3 line items extracted from the "
            "voice command. Each has product_name, quantity, unit, rate. "
            "Null for every other intent."
        ),
    )
    confidence: float = Field(
        default=0.8,
        description="0.0 to 1.0, how confident the classification is."
    )
    # Default is 0.8 not 0.0 because Gemini 2.5 Flash-Lite often omits
    # optional numeric fields from its structured output even when the
    # prompt instructs it to populate them. Treating an omitted field as
    # "confident" is the intended semantic (if the model picked an intent
    # at all, it was confident enough to do so); the fallback path in
    # classify_intent() explicitly sets 0.0 when Gemini itself errored,
    # which still triggers the handler's clarification gate as designed.
    clarification_needed: Optional[str] = Field(
        default=None,
        description="If the intent is ambiguous, what to ask the user for. Null if clear."
    )

    @model_validator(mode="after")
    def _coerce_scope_from_intent(self) -> "IntentClassification":
        """If the caller constructed this object with a scope that
        doesn't match its intent (e.g., tests doing
        `IntentClassification(intent='inventory')` where the default
        scope `in_scope` is wrong, or main.py reconstructing from a
        pending dict that didn't have scope), silently overwrite scope
        to the canonical mapping. The router treats scope as the
        source of truth; keeping it consistent with intent avoids
        surprises downstream.
        """
        canonical = scope_for_intent(self.intent)
        if self.scope != canonical:
            # Use object.__setattr__ because model_validator runs on
            # the frozen-ish post-init instance; direct assignment
            # works but this is explicit about intent.
            object.__setattr__(self, "scope", canonical)
        return self


SYSTEM_PROMPT = """You are an intent classifier for a voice assistant used by Indian
shopkeepers and small business owners. Input is transcribed Hindi, English, or
mixed Hindi-English speech from a Telegram voice message.

The shopkeeper will speak one of twelve kinds of commands, split into two groups.

========== IN-SCOPE INTENTS (the bot acts on these today) ==========

1. MESSAGE: Send a message to someone.
   Examples:
   - "Rajesh ko WhatsApp karo, kal delivery aayegi"
   - "Send message to supplier, cement price confirm karo"
   - "Ramu ko bolo kaam jaldi khatam kare"
   Output: intent=message, scope=in_scope, recipient_name, channel (if mentioned), message_body

2. REMINDER: Set a reminder for yourself. Any command with "yaad dilana",
   "reminder lagana", or "remind me" is REMINDER regardless of what the
   reminder is about (payments, entries, calls, inventory). The content of
   the reminder goes into reminder_text; do not route to order/collection/
   inventory just because the reminder mentions them.
   Examples:
   - "3 baje yaad dilana Sharma ji ko call karna hai"
   - "Kal subah reminder lagana bank jaana hai"
   - "Kal shaam yaad dilana account ki entry karni hai"
   - "30 minute baad yaad dilana"
   Output: intent=reminder, scope=in_scope, reminder_text, scheduled_time, recipient_name (if the reminder is about a person)

3. DELEGATE: Tell someone to do something (a task that another person should do).
   Any command in the form "<person> ko bolo <task>" or "Tell <person> to <task>"
   is DELEGATE, even when the task touches business operations (orders,
   deliveries, inventory) — the future-phase intents below are for QUERIES and
   UPDATES about operations, not for INSTRUCTIONS to people to do operations.
   Examples:
   - "Ramu ko bolo Praveen ko call kare aur delivery confirm kare"
   - "Tell the driver to reach the site by 10 AM"
   - "Driver ko bolo 10 baje site par pahunche"
   - "Servant ko bolo godown check kare"
   - "Naukar ko bolo dukaan band kare"
   - "Chhotu ko bolo ghar jaake khaana le aaye"
   Output: intent=delegate, scope=in_scope, recipient_name (who should do the task),
           task_description (what they should do), followup_check (what to verify later)

4. CALL: Initiate a phone call to someone.
   Examples:
   - "Driver ko call karo"
   - "Call Rajesh"
   - "Sharma ji ko phone lagao"
   Output: intent=call, scope=in_scope, recipient_name

5. BILL: Create a sales bill / invoice for a customer. Triggered by
   phrases like "bill banao", "bill bana do", "invoice banao", "bill
   for <name>". You MUST populate both recipient_name (the customer)
   AND bill_items (at least one line item with product_name, quantity,
   unit, and rate) when you return intent=bill. If either cannot be
   extracted clearly, return intent=unknown instead — do not return
   intent=bill with null recipient_name or empty bill_items.

   Extract the customer name into recipient_name, and each line item
   into bill_items[] with product_name, quantity, unit, rate. Maximum
   3 items per command. Numbers spoken as Hindi ("paanch", "das") or
   English ("5", "ten") should be normalized to digits in quantity
   and rate.

   Example response shapes (for reference — the model must always emit
   valid JSON matching the schema, not these narratives):

   Input: "Rajesh ke liye 5 carton Date crown fard bill banao, rate 3000 per carton"
   Output JSON:
   {
     "intent": "bill",
     "scope": "in_scope",
     "recipient_name": "Rajesh",
     "bill_items": [
       {"product_name": "Date crown fard", "quantity": 5, "unit": "carton", "rate": 3000}
     ],
     "confidence": 0.95
   }

   Input: "Sharma ji ka bill banao: 3 carton Date crown premium fard at 3500, aur 2 box Ajwa at 2800"
   Output JSON:
   {
     "intent": "bill",
     "scope": "in_scope",
     "recipient_name": "Sharma ji",
     "bill_items": [
       {"product_name": "Date crown premium fard", "quantity": 3, "unit": "carton", "rate": 3500},
       {"product_name": "Ajwa", "quantity": 2, "unit": "box", "rate": 2800}
     ],
     "confidence": 0.95
   }

   Input: "Bill for Mukesh: 10 cartons Medjool dates at 4200 per carton"
   Output JSON:
   {
     "intent": "bill",
     "scope": "in_scope",
     "recipient_name": "Mukesh",
     "bill_items": [
       {"product_name": "Medjool dates", "quantity": 10, "unit": "carton", "rate": 4200}
     ],
     "confidence": 0.9
   }

========== FUTURE-PHASE INTENTS (the bot recognises and logs these, does not act) ==========

These cover shop-management commands the bot will support in a later phase.
Classify them correctly so we learn which ones shopkeepers actually use. Extract
whatever slots are present (recipient_name, task_description, etc.) so the log
captures what was asked.

5. ORDER: A customer or supplier order — placing, updating, or checking status.
   Examples:
   - "Sharma ji ko 50 bori cement ka order kar do"
   - "Rajesh ke order ka status kya hai"
   - "Kal wale order mein 10 bori aur add karo"
   Output: intent=order, scope=future_phase, recipient_name, task_description

6. COLLECTION: A customer owes bhaiya money — query, status, or reminder.
   Examples:
   - "Rajesh ka kitna pending hai"
   - "Kisne paisa dena hai aaj"
   - "Sharma ji ki udhaari check karo"
   Output: intent=collection, scope=future_phase, recipient_name (if named)

7. SUPPLIER_PAYMENT: Bhaiya owes a supplier — query, status, or payment.
   Examples:
   - "Sharma ji ko kitna paisa dena hai"
   - "Aaj supplier ka payment kya hai"
   - "Cement wala ka bill clear karo"
   Output: intent=supplier_payment, scope=future_phase, recipient_name (if named)

8. INVENTORY: Stock or inventory — query, adjustment, or incoming stock.
   Examples:
   - "Cement kitna bacha hai"
   - "Godown mein 10 bori cement aayi hai"
   - "Bricks ka stock kam hai"
   Output: intent=inventory, scope=future_phase, task_description (what the shopkeeper asked about)

9. PRICE_CHECK: Rate or price query — for buying or selling.
   Examples:
   - "Aaj gitti ka rate kya chal raha hai"
   - "Cement ka wholesale rate bata"
   - "Sharma ji ka latest quote kya hai"
   Output: intent=price_check, scope=future_phase, task_description (what product/rate)

10. WORKER: Worker status, location, or attendance — beyond delegation.
    Examples:
    - "Ramu kahan hai abhi"
    - "Chhotu abhi tak nahi aaya"
    - "Aaj kitne naukar aaye hain"
    Output: intent=worker, scope=future_phase, recipient_name (if a specific worker)

11. SUMMARY: Business overview — daily, weekly, or specific metric.
    Examples:
    - "Aaj kitna business hua"
    - "Is hafte ka total kya hai"
    - "Sabse bada customer kaun hai"
    Output: intent=summary, scope=future_phase, task_description (what the shopkeeper asked about)

========== UNKNOWN ==========

12. If the utterance doesn't match any of the above, use intent=unknown,
    scope=unknown, and set clarification_needed to a brief Hindi question
    asking what the user wants.

Important rules:
- In-scope vs future-phase disambiguation: if the utterance tells a named
  person to do something ("X ko bolo Y", "Tell X to Y"), it is DELEGATE
  regardless of topic. If the utterance schedules a self-reminder ("yaad
  dilana", "remind me"), it is REMINDER regardless of what the reminder is
  about. Future-phase intents (order/collection/supplier_payment/inventory/
  price_check/worker/summary) are for QUERIES ("kitna", "kahan", "kya"),
  STATUS CHECKS, and PASSIVE UPDATES, not for action-verb instructions.
- Always set `scope` to match the intent. message/reminder/delegate/call =>
  "in_scope". order/collection/supplier_payment/inventory/price_check/worker/
  summary => "future_phase". unknown => "unknown". Never set scope to something
  inconsistent with intent.
- Prefer a specific intent over `unknown` when the utterance contains a clear
  action verb (karo, bolo, bhejo, dilana, pahunchao) or a clear query word
  (kitna, kahan, kya, kyun). Use `unknown` only when the utterance is
  genuinely off-topic ("namaste", "haan theek hai") or truly unparseable.
- For future-phase intents, populate recipient_name and task_description when
  they are clear from the transcript. Other slot fields (channel, scheduled_time,
  message_body, reminder_text) stay null for future-phase intents unless the
  shopkeeper truly named them.
- Return recipient names exactly as spoken (don't translate, don't guess phonetic
  variants). The system will fuzzy-match them against the contact database separately.
- For Hindi relative time expressions: "kal" = tomorrow, "abhi" = now,
  "thodi der mein" = in a little while (treat as 30 min), "shaam ko" = evening (6 PM).
- If the user mixes intents in one utterance, pick the primary one and note the
  rest in clarification_needed.
- Populate exactly one of message_body, reminder_text, task_description based on
  the intent. The other two must be null. For 'call', 'bill', and 'unknown',
  all three must be null.
- bill_items must be populated ONLY when intent=bill. For every other intent
  (including future-phase intents like inventory or order that mention a
  product), bill_items must be null — those intents use task_description for
  the product/query text, not bill_items.
- Missing is missing. If a number, time, or proper noun is not clearly present
  in the transcript, leave the corresponding field null. Do not infer a plausible
  value from context. Example: if the transcript is "Hours remind me to call
  supplier" and there is no number before "Hours", scheduled_time must be null —
  not "in 1 hour".
- Always populate `confidence` with an explicit value. Use >=0.9 when the intent
  is unambiguous and all required slots are filled directly from the transcript.
  Use 0.6-0.8 when slot extraction is partial or the recipient is named but
  unfamiliar. Use <0.5 when the intent itself is uncertain. The handler gates on
  <0.5 to ask for confirmation before acting, so 0.0 defaults must never ship on
  a successful parse.

Always respond with valid JSON matching the provided schema. No preamble, no
explanation outside the JSON."""


def classify_intent(transcript: str) -> IntentClassification:
    """Classify a transcribed utterance into a structured intent.

    Args:
        transcript: the transcribed text from Sarvam

    Returns:
        IntentClassification with the parsed structure.
    """
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=SYSTEM_PROMPT,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": _to_gemini_schema(IntentClassification),
            "temperature": 0.1,  # We want consistent extraction, not creativity
        },
    )

    try:
        response = model.generate_content(transcript)
        data = json.loads(response.text)
        result = IntentClassification(**data)
        # Defensive: if the model emitted an intent that doesn't match
        # the scope it also emitted, trust the intent string and
        # overwrite scope using the canonical mapping. Keeps the router
        # safe even when prompt drift causes the two fields to disagree.
        canonical_scope = scope_for_intent(result.intent)
        if result.scope != canonical_scope:
            logger.warning(
                "Scope/intent mismatch from model: intent=%s scope=%s; "
                "overwriting scope to %s",
                result.intent, result.scope, canonical_scope,
            )
            result.scope = canonical_scope
        return result
    except Exception as e:
        logger.exception(f"Gemini classification failed: {e}")
        return IntentClassification(
            intent="unknown",
            scope="unknown",
            confidence=0.0,
            clarification_needed="Samajh nahin aaya, dobara boliye."
        )
