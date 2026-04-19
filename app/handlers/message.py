"""Handler for 'message' intent: compose a message and give the shopkeeper a
tap-to-send link through their own WhatsApp or SMS (so they don't pay for it).

No WhatsApp Business API. No Twilio SMS. Just a deep link the shopkeeper taps
to send through their regular phone — free for them, zero cost for us.
"""
import logging
from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.db.models import Task, User
from app.services.classify import IntentClassification
from app.services.contact_resolver import resolve_contact

logger = logging.getLogger(__name__)


def _whatsapp_link(phone: str, message: str) -> str:
    """Build a wa.me link that opens WhatsApp with recipient and text pre-filled."""
    clean_phone = phone.lstrip("+").replace(" ", "").replace("-", "")
    return f"https://wa.me/{clean_phone}?text={quote(message)}"


def _sms_link(phone: str, message: str) -> str:
    """Build an sms: link that opens the SMS composer."""
    return f"sms:{phone}?body={quote(message)}"


async def handle_message_intent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    intent: IntentClassification,
) -> None:
    """Handle a 'send message' command."""
    db = SessionLocal()
    try:
        if not intent.recipient_name:
            await update.message.reply_text(
                "Kisko message bhejna hai? Naam bataiye."
            )
            return

        if not intent.content:
            await update.message.reply_text(
                f"{intent.recipient_name} ko kya message bhejna hai?"
            )
            return

        contacts = resolve_contact(db, user.id, intent.recipient_name)

        if not contacts:
            await update.message.reply_text(
                f"'{intent.recipient_name}' mere contacts mein nahin hai.\n"
                f"Add karne ke liye: /addcontact {intent.recipient_name} <phone>"
            )
            return

        if len(contacts) > 1:
            # Ambiguous - ask for disambiguation
            buttons = [
                [InlineKeyboardButton(
                    f"{c.name} ({c.role or 'no role'})",
                    callback_data=f"pick_contact:{c.id}:message"
                )]
                for c in contacts
            ]
            await update.message.reply_text(
                f"Kaun sa {intent.recipient_name}?",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            # Store pending intent for when they pick
            context.user_data["pending_intent"] = intent.model_dump()
            return

        # Unambiguous match
        contact = contacts[0]
        channel = intent.channel or "whatsapp"

        if channel == "sms":
            link = _sms_link(contact.phone, intent.content)
            channel_label = "SMS"
        else:
            link = _whatsapp_link(contact.phone, intent.content)
            channel_label = "WhatsApp"

        # Save task
        task = Task(
            user_id=user.id,
            task_type="message",
            status="prepared",
            raw_transcript=context.user_data.get("last_transcript"),
            payload={
                "recipient_name": contact.name,
                "recipient_phone": contact.phone,
                "channel": channel,
                "content": intent.content,
            },
        )
        db.add(task)
        db.commit()

        buttons = [[InlineKeyboardButton(
            f"📱 {channel_label} bhejo",
            url=link,
        )]]

        await update.message.reply_text(
            f"*{contact.name}* ko {channel_label} message:\n\n"
            f"_{intent.content}_\n\n"
            f"Tap karke bhejiye.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    finally:
        db.close()
