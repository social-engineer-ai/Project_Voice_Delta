"""Resolve a spoken name to a contact in the shopkeeper's address book.

Spoken names are messy. "Ramu" might be stored as "Ramesh". "The driver" is
a role reference, not a name. "Rajesh ji" is "Rajesh" with an honorific.
This module handles all that.

Strategy:
1. Check aliases (exact match against stored alternate names)
2. Check role (if the spoken name matches a role like "driver", return contacts with that role)
3. Fuzzy match on name (rapidfuzz, threshold 75%)
4. If multiple matches, return all for disambiguation
5. If no match, return empty
"""
import logging
import re
from typing import List

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from app.db.models import Contact

logger = logging.getLogger(__name__)


# Common Hindi/Indian English role words that might be used instead of names
ROLE_KEYWORDS = {
    "driver": ["driver", "ड्राइवर", "drayvar"],
    "servant": ["servant", "naukar", "नौकर", "ramu", "chhotu"],
    "accountant": ["accountant", "CA", "munim", "मुनीम"],
    "supplier": ["supplier", "vendor"],
    "wife": ["wife", "patni", "पत्नी", "biwi"],
    "brother": ["bhai", "भाई", "brother"],
}

# Honorifics to strip before matching
HONORIFICS = ["ji", "sahab", "bhaiya", "bhai", "sir", "madam", "saab"]


def normalize_spoken_name(spoken: str) -> str:
    """Strip honorifics and extra whitespace from a spoken name."""
    name = spoken.strip().lower()
    # Remove honorifics from end
    for h in HONORIFICS:
        pattern = rf"\s+{re.escape(h)}\s*$"
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)
    # Also handle "the driver" → "driver"
    name = re.sub(r"^(the|wo|yeh|that|this)\s+", "", name)
    return name.strip()


def resolve_contact(
    db: Session, user_id: int, spoken_name: str
) -> List[Contact]:
    """Find contacts matching the spoken name.

    Returns a list. Empty if no match, one if unambiguous, multiple if ambiguous.
    """
    contacts = db.query(Contact).filter(Contact.user_id == user_id).all()
    if not contacts:
        return []

    normalized = normalize_spoken_name(spoken_name)
    if not normalized:
        return []

    # 1. Check if spoken name matches a role keyword
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            role_matches = [c for c in contacts if c.role and c.role.lower() == role]
            if role_matches:
                return role_matches

    # 2. Check exact alias match
    for contact in contacts:
        aliases = contact.aliases or []
        if any(normalize_spoken_name(a) == normalized for a in aliases):
            return [contact]
        if normalize_spoken_name(contact.name) == normalized:
            return [contact]

    # 3. Fuzzy match on name
    name_to_contact = {normalize_spoken_name(c.name): c for c in contacts}
    candidates = list(name_to_contact.keys())
    matches = process.extract(
        normalized, candidates, scorer=fuzz.WRatio, limit=5
    )
    # matches is list of (matched_string, score, index) tuples
    good_matches = [name_to_contact[m[0]] for m in matches if m[1] >= 75]

    return good_matches
