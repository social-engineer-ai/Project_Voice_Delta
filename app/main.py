"""ShopSaarthi Bot entry point.

Wires up:
- Telegram Application with polling
- APScheduler for reminders and follow-ups (with SQLAlchemy job store
  so scheduled jobs survive restarts)
- Command handlers (/start, /help, contact management)
- Voice and text message handlers
- Callback query handler for inline keyboard picks (contact disambiguation)

Run with: python -m app.main
"""
import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.db.session import SessionLocal
from app.db.models import User, Contact
from app.handlers.contacts import (
    add_contact_command,
    delete_contact_command,
    list_contacts_command,
)
from app.handlers.enrollment import (
    build_enrollment_handler,
    reset_voice_command,
    set_security_command,
    voice_status_command,
)
from app.handlers.entities import (
    add_dalal_command,
    add_transporter_command,
    list_dalals_command,
    list_transporters_command,
)
from app.handlers.voice import (
    _get_or_create_user,
    handle_text_message,
    handle_voice_message,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.log_level),
)
logger = logging.getLogger(__name__)


WELCOME_TEXT = (
    "Namaste! Main ShopSaarthi hoon — aapka voice assistant.\n\n"
    "*Kya kar sakta hoon:*\n"
    "📝 *Message bhejna* — 'Rajesh ko WhatsApp karo, kal aao'\n"
    "⏰ *Reminder lagana* — '3 baje yaad dilana Sharma ji ko call karna hai'\n"
    "👥 *Kaam delegate karna* — 'Ramu ko bolo godown check kare'\n"
    "📞 *Call karna* — 'Driver ko call karo'\n\n"
    "*Shuru karne ke liye:*\n"
    "1. /enroll — apni voice enroll kariye (trust ke liye)\n"
    "2. /addcontact Ramu 9876543210 servant — contacts add kariye\n"
    "3. Voice message bhejiye ya type kariye\n\n"
    "*Commands:*\n"
    "/enroll — voice enrollment\n"
    "/reenroll — voice profile improve karo\n"
    "/security — strict/medium/loose/off\n"
    "/voicestatus — voice settings dekho\n"
    "/contacts — saare contacts\n"
    "/addcontact — naya contact\n"
    "/deletecontact — contact hatao\n"
    "/help — yeh message dobara"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /start."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    await _get_or_create_user(chat_id, username)
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /help."""
    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")


async def handle_contact_picked(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """User tapped a disambiguation button. Re-run the intent with the chosen contact.

    Callback data format: "pick_contact:<contact_id>:<intent_type>"
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "pick_contact":
        return

    contact_id = int(parts[1])
    intent_type = parts[2]

    pending = context.user_data.pop("pending_intent", None)
    if not pending:
        await query.edit_message_text(
            "Context khatam ho gaya. Dobara voice message bhejiye."
        )
        return

    db = SessionLocal()
    try:
        contact = db.query(Contact).get(contact_id)
        if not contact:
            await query.edit_message_text("Contact nahi mila.")
            return

        # Replace recipient_name with the picked contact's exact name so
        # downstream resolution is unambiguous
        pending["recipient_name"] = contact.name

        # Re-import the classified intent
        from app.services.classify import IntentClassification
        intent = IntentClassification(**pending)

        # Find the user
        user = db.query(User).filter(
            User.telegram_chat_id == update.effective_chat.id
        ).first()
        if not user:
            await query.edit_message_text("User nahi mila. /start kariye.")
            return

        # We need an update-like object for the handler. Use the callback query's
        # message as the reply target.
        class _FakeUpdate:
            def __init__(self, message, effective_chat, effective_user):
                self.message = message
                self.effective_chat = effective_chat
                self.effective_user = effective_user

        fake_update = _FakeUpdate(
            message=query.message,
            effective_chat=update.effective_chat,
            effective_user=update.effective_user,
        )

        # Remove the disambiguation keyboard
        await query.edit_message_reply_markup(reply_markup=None)

        # Route to the right handler
        from app.handlers.message import handle_message_intent
        from app.handlers.delegate import handle_delegate_intent
        from app.handlers.call import handle_call_intent

        handlers = {
            "message": handle_message_intent,
            "delegate": handle_delegate_intent,
            "call": handle_call_intent,
        }
        handler = handlers.get(intent_type)
        if handler:
            await handler(fake_update, context, user, intent)

    finally:
        db.close()


def build_application() -> Application:
    """Construct the Telegram Application with all handlers registered."""
    app = Application.builder().token(settings.telegram_bot_token).build()

    # Scheduler with persistent job store
    jobstore = SQLAlchemyJobStore(url=settings.database_url)
    scheduler = AsyncIOScheduler(jobstores={"default": jobstore})
    app.bot_data["scheduler"] = scheduler

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addcontact", _with_user_async(add_contact_command)))
    app.add_handler(CommandHandler("contacts", _with_user_async(list_contacts_command)))
    app.add_handler(CommandHandler("deletecontact", _with_user_async(delete_contact_command)))

    # Voice enrollment flow (ConversationHandler - must be registered before
    # the general voice MessageHandler so enrollment voices get intercepted)
    app.add_handler(build_enrollment_handler())

    # Voice-related commands (not part of the enrollment conversation)
    app.add_handler(CommandHandler("security", set_security_command))
    app.add_handler(CommandHandler("voicestatus", voice_status_command))
    app.add_handler(CommandHandler("resetvoice", reset_voice_command))

    # Dalal + Transporter catalog management (Dates branch).
    app.add_handler(CommandHandler("add_dalal", add_dalal_command))
    app.add_handler(CommandHandler("add_transporter", add_transporter_command))
    app.add_handler(CommandHandler("list_dalals", list_dalals_command))
    app.add_handler(CommandHandler("list_transporters", list_transporters_command))

    # Voice and text messages (after enrollment handler so enrollment voices
    # are captured by the conversation first)
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    # Inline keyboard callbacks (contact disambiguation)
    app.add_handler(CallbackQueryHandler(handle_contact_picked, pattern=r"^pick_contact:"))

    # Start scheduler when the app starts
    async def post_init(application: Application) -> None:
        scheduler.start()
        logger.info("Scheduler started")

    async def post_shutdown(application: Application) -> None:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    return app


def _with_user_async(handler):
    """Wrap a handler that expects (update, context, user) so it fits the
    python-telegram-bot signature (update, context)."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username
        user = await _get_or_create_user(chat_id, username)
        await handler(update, context, user)
    return wrapper


def main() -> None:
    """Run the bot."""
    logger.info(f"Starting ShopSaarthi bot (model: {settings.gemini_model})")
    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
