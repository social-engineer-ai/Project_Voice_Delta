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
from typing import Any, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field

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


def _to_gemini_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Return a Gemini-Schema-compatible dict derived from a Pydantic model."""
    raw = model_cls.model_json_schema()
    defs = raw.get("$defs", {})
    return _clean_schema(raw, defs)


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

class IntentClassification(BaseModel):
    """The parsed structure of a shopkeeper's voice command."""
    intent: str = Field(
        description="One of: 'message', 'reminder', 'delegate', 'call', 'unknown'"
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


SYSTEM_PROMPT = """You are an intent classifier for a voice assistant used by Indian
shopkeepers and small business owners. Input is transcribed Hindi, English, or
mixed Hindi-English speech from a Telegram voice message.

The shopkeeper will speak one of four kinds of commands:

1. MESSAGE: Send a message to someone.
   Examples:
   - "Rajesh ko WhatsApp karo, kal delivery aayegi"
   - "Send message to supplier, cement price confirm karo"
   - "Ramu ko bolo kaam jaldi khatam kare"
   Output: intent=message, recipient_name, channel (if mentioned), message_body

2. REMINDER: Set a reminder for yourself.
   Examples:
   - "3 baje yaad dilana Sharma ji ko call karna hai"
   - "Kal subah reminder lagana bank jaana hai"
   - "30 minute baad yaad dilana"
   Output: intent=reminder, reminder_text, scheduled_time, recipient_name (if the reminder is about a person)

3. DELEGATE: Tell someone to do something (a task that another person should do).
   Examples:
   - "Ramu ko bolo Praveen ko call kare aur delivery confirm kare"
   - "Tell the driver to reach the site by 10 AM"
   - "Servant ko bolo godown check kare"
   Output: intent=delegate, recipient_name (who should do the task),
           task_description (what they should do), followup_check (what to verify later)

4. CALL: Initiate a phone call to someone.
   Examples:
   - "Driver ko call karo"
   - "Call Rajesh"
   - "Sharma ji ko phone lagao"
   Output: intent=call, recipient_name

If the utterance doesn't match any of these, use intent=unknown and set
clarification_needed to a brief Hindi question asking what the user wants.

Important rules:
- Return recipient names exactly as spoken (don't translate, don't guess phonetic
  variants). The system will fuzzy-match them against the contact database separately.
- For Hindi relative time expressions: "kal" = tomorrow, "abhi" = now,
  "thodi der mein" = in a little while (treat as 30 min), "shaam ko" = evening (6 PM).
- If the user mixes intents in one utterance, pick the primary one and note the
  rest in clarification_needed.
- Populate exactly one of message_body, reminder_text, task_description based on
  the intent. The other two must be null. For 'call' and 'unknown', all three
  must be null.
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
        return IntentClassification(**data)
    except Exception as e:
        logger.exception(f"Gemini classification failed: {e}")
        return IntentClassification(
            intent="unknown",
            confidence=0.0,
            clarification_needed="Samajh nahin aaya, dobara boliye."
        )
