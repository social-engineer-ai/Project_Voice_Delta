"""The voice message handler: receives a Telegram voice message, verifies
the speaker, transcribes it with Sarvam, classifies the intent with Gemini,
and routes to the appropriate handler.

This is the main orchestration point for the bot's core functionality.
Verification happens before transcription to fail fast on unauthorized voices.
"""
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.db.models import User
from app.handlers.call import handle_call_intent
from app.handlers.delegate import handle_delegate_intent
from app.handlers.message import handle_message_intent
from app.handlers.reminder import handle_reminder_intent
from app.services.classify import classify_intent
from app.services.transcribe import transcribe_audio
from app.services.verify_speaker import verify_speaker

logger = logging.getLogger(__name__)


async def _get_or_create_user(chat_id: int, username: str | None) -> User:
    """Find or create the User row for this Telegram chat."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user:
            return user
        user = User(
            telegram_chat_id=chat_id,
            telegram_username=username,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


async def handle_voice_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Main handler for voice messages.

    Flow:
    1. Download the voice file from Telegram
    2. Verify the speaker matches the enrolled profile (if user is enrolled)
    3. Transcribe via Sarvam
    4. Classify intent via Gemini
    5. Route to the appropriate intent handler
    """
    chat_id = update.effective_chat.id
    username = update.effective_user.username

    user = await _get_or_create_user(chat_id, username)

    # Step 1: Download the voice file
    voice = update.message.voice
    if not voice:
        await update.message.reply_text("Voice message nahi mila.")
        return

    file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        await file.download_to_drive(tmp_path)

        # Step 2: Verify speaker (skipped if user not enrolled or security off)
        db = SessionLocal()
        try:
            # Re-fetch user inside this session for up-to-date state
            fresh_user = db.query(User).filter(
                User.telegram_chat_id == chat_id
            ).first()
            is_match, score = verify_speaker(db, fresh_user, tmp_path)
        finally:
            db.close()

        if not is_match:
            await update.message.reply_text(
                f"Yeh awaaz match nahi hui (score: {score:.2f}).\n\n"
                f"Agar yeh aap hi hain:\n"
                f"• /security loose karke try kariye\n"
                f"• Ya /reenroll se voice profile update kariye"
            )
            return

        if not fresh_user.enrolled and fresh_user.security_threshold != "off":
            # User hasn't enrolled but security is on - remind them
            await update.message.reply_text(
                "ℹ️ Aap abhi tak voice enroll nahin hue. /enroll se enrollment kariye. "
                "Abhi ke liye command process kar raha hoon."
            )

        # Step 3: Transcribe
        await update.message.reply_chat_action("typing")
        try:
            transcript = await transcribe_audio(tmp_path)
        except Exception as e:
            logger.exception(f"Transcription failed: {e}")
            await update.message.reply_text(
                "Transcription mein dikkat hui. Dobara bhejiye."
            )
            return

        if not transcript or not transcript.strip():
            await update.message.reply_text(
                "Kuch samajh nahi aaya. Saaf bol kar dobara bhejiye."
            )
            return

        # Show the user what we heard (helps build trust)
        await update.message.reply_text(
            f"_Suna: {transcript}_", parse_mode="Markdown"
        )

        # Cache transcript for downstream handlers
        context.user_data["last_transcript"] = transcript

        # Step 4: Classify intent
        intent = classify_intent(transcript)
        logger.info(
            f"Intent: {intent.intent} (confidence {intent.confidence:.2f}) - "
            f"recipient={intent.recipient_name}, content={intent.content}"
        )

        if intent.confidence < 0.5 or intent.intent == "unknown":
            msg = intent.clarification_needed or "Samajh nahi aaya. Kya karna hai?"
            await update.message.reply_text(msg)
            return

        # Step 5: Route to handler
        handlers = {
            "message": handle_message_intent,
            "reminder": handle_reminder_intent,
            "delegate": handle_delegate_intent,
            "call": handle_call_intent,
        }
        handler = handlers.get(intent.intent)
        if not handler:
            await update.message.reply_text(
                f"Intent '{intent.intent}' abhi support nahi hai."
            )
            return

        await handler(update, context, fresh_user, intent)

    finally:
        if tmp_path.exists():
            tmp_path.unlink()


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle typed text messages the same way as voice (skip transcription
    and speaker verification since text doesn't have acoustic identity).
    """
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    user = await _get_or_create_user(chat_id, username)

    text = update.message.text.strip()
    if not text:
        return

    context.user_data["last_transcript"] = text

    intent = classify_intent(text)
    logger.info(
        f"Text intent: {intent.intent} (confidence {intent.confidence:.2f})"
    )

    if intent.confidence < 0.5 or intent.intent == "unknown":
        msg = intent.clarification_needed or "Samajh nahi aaya. Kya karna hai?"
        await update.message.reply_text(msg)
        return

    handlers = {
        "message": handle_message_intent,
        "reminder": handle_reminder_intent,
        "delegate": handle_delegate_intent,
        "call": handle_call_intent,
    }
    handler = handlers.get(intent.intent)
    if handler:
        await handler(update, context, user, intent)
