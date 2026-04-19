"""Commands for managing the shopkeeper's contact list.

/addcontact <name> <phone> [role]  — add a new contact
/contacts                          — list all contacts
/deletecontact <name>              — remove a contact
"""
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.db.models import Contact, User

logger = logging.getLogger(__name__)


def _normalize_phone(raw: str) -> str | None:
    """Accept Indian numbers in various formats, return +91XXXXXXXXXX."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    if len(digits) == 13 and digits.startswith("091"):
        return f"+{digits[1:]}"
    return None


async def add_contact_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User
) -> None:
    """Usage: /addcontact Ramu 9876543210 servant"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /addcontact <name> <phone> [role]\n"
            "Example: /addcontact Ramu 9876543210 servant"
        )
        return

    name = args[0]
    phone = _normalize_phone(args[1])
    role = args[2].lower() if len(args) > 2 else None

    if not phone:
        await update.message.reply_text(
            "Phone number galat hai. 10 digit Indian number do."
        )
        return

    db = SessionLocal()
    try:
        # Check for duplicate
        existing = db.query(Contact).filter(
            Contact.user_id == user.id,
            Contact.name == name,
        ).first()
        if existing:
            existing.phone = phone
            if role:
                existing.role = role
            db.commit()
            await update.message.reply_text(f"✅ {name} updated ({phone})")
            return

        contact = Contact(
            user_id=user.id,
            name=name,
            phone=phone,
            role=role,
            aliases=[],
        )
        db.add(contact)
        db.commit()
        await update.message.reply_text(
            f"✅ {name} added ({phone}"
            + (f", {role}" if role else "")
            + ")"
        )
    finally:
        db.close()


async def list_contacts_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User
) -> None:
    """List all contacts for this shopkeeper."""
    db = SessionLocal()
    try:
        contacts = db.query(Contact).filter(Contact.user_id == user.id).all()
        if not contacts:
            await update.message.reply_text(
                "Abhi koi contact nahi hai.\n"
                "Add karne ke liye: /addcontact <name> <phone> [role]"
            )
            return

        lines = ["*Aapke contacts:*\n"]
        for c in contacts:
            role_str = f" — {c.role}" if c.role else ""
            lines.append(f"• {c.name}{role_str}: {c.phone}")
        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown"
        )
    finally:
        db.close()


async def delete_contact_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user: User
) -> None:
    """Usage: /deletecontact Ramu"""
    if not context.args:
        await update.message.reply_text("Usage: /deletecontact <name>")
        return

    name = context.args[0]
    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(
            Contact.user_id == user.id,
            Contact.name == name,
        ).first()
        if not contact:
            await update.message.reply_text(f"{name} nahi mila.")
            return
        db.delete(contact)
        db.commit()
        await update.message.reply_text(f"✅ {name} delete ho gaya.")
    finally:
        db.close()
