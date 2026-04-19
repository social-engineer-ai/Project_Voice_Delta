"""Unit test for the Pydantic-to-Gemini schema cleaner.

The cleaner must strip keys that Gemini's Schema dialect rejects and must
not leave any $ref pointers behind. A single test walks the cleaned dict
recursively and asserts none of the forbidden keys survive anywhere in the
tree. Run directly (no pytest dependency): python -m tests.test_schema_cleaner
"""
import sys
from typing import Any

from app.services.classify import (
    IntentClassification,
    _GEMINI_DISALLOWED_KEYS,
    _to_gemini_schema,
)


FORBIDDEN_KEYS = _GEMINI_DISALLOWED_KEYS | {"$ref"}


def _find_forbidden(node: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in FORBIDDEN_KEYS:
                hits.append(f"{path}.{k}")
            hits.extend(_find_forbidden(v, f"{path}.{k}"))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            hits.extend(_find_forbidden(item, f"{path}[{i}]"))
    return hits


def run() -> int:
    schema = _to_gemini_schema(IntentClassification)

    if not isinstance(schema, dict) or schema.get("type") != "object":
        print(f"FAIL: root schema is not an object: {schema!r}")
        return 1

    if "properties" not in schema or not schema["properties"]:
        print("FAIL: cleaned schema is missing properties")
        return 1

    offenders = _find_forbidden(schema)
    if offenders:
        print("FAIL: forbidden keys remain in cleaned schema:")
        for path in offenders:
            print(f"  {path}")
        return 1

    # Optional fields must survive as nullable single-type, not anyOf-with-null.
    recipient = schema["properties"].get("recipient_name")
    if not isinstance(recipient, dict) or not recipient.get("nullable"):
        print(f"FAIL: recipient_name did not collapse to nullable: {recipient!r}")
        return 1
    if "anyOf" in recipient:
        print(f"FAIL: recipient_name still carries anyOf: {recipient!r}")
        return 1

    print(f"OK: cleaned schema passes all checks ({len(schema['properties'])} fields)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
