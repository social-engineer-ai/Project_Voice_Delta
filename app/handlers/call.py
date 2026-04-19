"""Handler for 'call' intent: look up the contact and provide a tap-to-dial link.

No Exotel. No bridged calling. No per-call cost. The shopkeeper taps the link
and their phone makes the call through their regular carrier (Jio/Airtel/Vi),
which is free on current prepaid plans.

If we ever want recorded calls or business-number calls later, we add a
premium tier with bridged calling as an opt-in feature.
"""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.db.models import Task, User
from app.services.classify import IntentClassification
from app.services.contact_resolver import resolve_contact

logger = logging.getLogger(__name__)


async def handle_call_intent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    intent: IntentClassification,
) -> None:
    """Handle a 'call someone' command."""
    db = SessionLocal()
    try:
        if not intent.recipient_name:
            await update.message.reply_text(
                "Kisko call karna hai? Naam bataiye."
            )
            return

        contacts = resolve_contact(db, user.id, intent.recipient_name)
        if not contacts:
            await update.message.reply_text(
                f"'{intent.recipient_name}' contacts mein nahin hai.\n"
                f"Add: /addcontact {intent.recipient_name} <phone>"
            )
            return

        if len(contacts) > 1:
            buttons = [
                [InlineKeyboardButton(
                    f"📞 {c.name} ({c.role or 'no role'})",
                    url=f"tel:{c.phone}",
                )]
                for c in contacts
            ]
            await update.message.reply_text(
                f"Kaun sa {intent.recipient_name}?",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return

        contact = contacts[0]

        task = Task(
            user_id=user.id,
            task_type="call",
            status="prepared",
            raw_transcript=context.user_data.get("last_transcript"),
            payload={
                "recipient_name": contact.name,
                "recipient_phone": contact.phone,
            },
        )
        db.add(task)
        db.commit()

        buttons = [[InlineKeyboardButton(
            f"📞 Call {contact.name}",
            url=f"tel:{contact.phone}",
        )]]

        await update.message.reply_text(
            f"*{contact.name}* ko call karne ke liye tap kariye:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    finally:
        db.close()
