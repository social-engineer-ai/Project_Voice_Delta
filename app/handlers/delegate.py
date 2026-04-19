"""Handler for 'delegate' intent: tell someone to do something, with an
optional follow-up reminder to the shopkeeper to verify it was done.

This is a composite of message + reminder:
1. Generate a WhatsApp/SMS link to send the instruction to the delegatee
2. Schedule a follow-up ping to the shopkeeper asking if it was completed
"""
import logging
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.db.models import Task, User
from app.handlers.reminder import send_reminder_ping
from app.services.classify import IntentClassification
from app.services.contact_resolver import resolve_contact

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def _whatsapp_link(phone: str, message: str) -> str:
    clean = phone.lstrip("+").replace(" ", "").replace("-", "")
    return f"https://wa.me/{clean}?text={quote(message)}"


async def handle_delegate_intent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    intent: IntentClassification,
) -> None:
    """Handle a delegation command: 'tell Ramu to call Praveen'."""
    db = SessionLocal()
    try:
        if not intent.recipient_name or not intent.content:
            await update.message.reply_text(
                "Kisko bolna hai aur kya karna hai? Dobara bataiye."
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
                    f"{c.name} ({c.role or 'no role'})",
                    callback_data=f"pick_contact:{c.id}:delegate"
                )]
                for c in contacts
            ]
            await update.message.reply_text(
                f"Kaun sa {intent.recipient_name}?",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            context.user_data["pending_intent"] = intent.model_dump()
            return

        contact = contacts[0]
        link = _whatsapp_link(contact.phone, intent.content)

        task = Task(
            user_id=user.id,
            task_type="delegate",
            status="prepared",
            raw_transcript=context.user_data.get("last_transcript"),
            payload={
                "recipient_name": contact.name,
                "recipient_phone": contact.phone,
                "content": intent.content,
                "followup_check": intent.followup_check,
            },
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Schedule follow-up reminder in 2 hours (configurable later)
        followup_time = datetime.now(IST) + timedelta(hours=2)
        followup_text = (
            intent.followup_check
            or f"Check karo: kya {contact.name} ne kaam kiya? ({intent.content})"
        )

        scheduler = context.application.bot_data.get("scheduler")
        if scheduler:
            scheduler.add_job(
                send_reminder_ping,
                trigger="date",
                run_date=followup_time,
                args=[context.application, user.telegram_chat_id, followup_text, task.id],
                id=f"delegate_followup_{task.id}",
            )

        buttons = [[InlineKeyboardButton(
            f"📱 {contact.name} ko WhatsApp karo",
            url=link,
        )]]

        followup_display = followup_time.strftime("%I:%M %p")
        await update.message.reply_text(
            f"*{contact.name}* ko bhejne ke liye:\n\n"
            f"_{intent.content}_\n\n"
            f"⏰ {followup_display} baje yaad dilaunga check karne ke liye.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    finally:
        db.close()
