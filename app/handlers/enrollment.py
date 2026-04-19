"""Voice enrollment flow.

Walks the user through recording 5-7 short phrases to build their voice
profile. Uses ConversationHandler states so the bot knows where in the
enrollment flow each user is.

Commands:
    /enroll       - Start first-time enrollment (required before security works)
    /reenroll     - Add additional samples to an existing profile
    /security     - Set the verification threshold (strict/medium/loose/off)
    /voicestatus  - Show current enrollment and security status
"""
import logging
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.db.models import User, VoiceProfile
from app.db.session import SessionLocal
from app.services.verify_speaker import store_enrollment, THRESHOLDS

logger = logging.getLogger(__name__)


# ConversationHandler states
AWAITING_VOICE_SAMPLE = 1

# Phrases the user is asked to speak during enrollment. Diverse in content
# and phrasing to capture acoustic range. All in simple Hindi/English.
ENROLLMENT_PHRASES = [
    "Mera naam hai, main is dukaan ka maalik hoon",
    "Aaj ka din bahut achcha hai, kaam bahut hua",
    "Rajesh ji ko call karo, kal milna hai",
    "Yaad dilana paanch baje, supplier ko phone karna hai",
    "Ramu, jaldi aao, delivery aa gayi hai",
]


async def start_enrollment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Begin the enrollment flow. /enroll command."""
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if not user:
            await update.message.reply_text(
                "Pehle /start command bhejiye."
            )
            return ConversationHandler.END

        # If already enrolled, ask whether to start over or add samples
        if user.enrolled:
            await update.message.reply_text(
                "Aap already enrolled hain. Naya profile banane ke liye pehle /resetvoice bhejiye. "
                "Profile strong karne ke liye /reenroll bhejiye."
            )
            return ConversationHandler.END

        context.user_data["enrollment_index"] = 0
        context.user_data["enrollment_mode"] = "enroll"

        first_phrase = ENROLLMENT_PHRASES[0]
        await update.message.reply_text(
            f"Voice enrollment shuru kar rahe hain.\n\n"
            f"Main aapko {len(ENROLLMENT_PHRASES)} phrases bolne ko kahunga. "
            f"Har ek ke liye ek voice message bhejiye.\n\n"
            f"*Phrase 1 of {len(ENROLLMENT_PHRASES)}:*\n"
            f"_{first_phrase}_\n\n"
            f"Ab iska voice message bhejiye.",
            parse_mode="Markdown",
        )
        return AWAITING_VOICE_SAMPLE
    finally:
        db.close()


async def start_reenrollment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Add additional samples to an existing voice profile. /reenroll command."""
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if not user or not user.enrolled:
            await update.message.reply_text(
                "Pehle /enroll command se voice enroll kariye."
            )
            return ConversationHandler.END

        context.user_data["enrollment_index"] = 0
        context.user_data["enrollment_mode"] = "reenroll"

        first_phrase = ENROLLMENT_PHRASES[0]
        await update.message.reply_text(
            f"Voice profile ko strong karenge. 3 phrases bhejiye.\n\n"
            f"*Phrase 1:*\n_{first_phrase}_",
            parse_mode="Markdown",
        )
        return AWAITING_VOICE_SAMPLE
    finally:
        db.close()


async def collect_voice_sample(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle each voice sample during enrollment. Returns next state or ENDs."""
    chat_id = update.effective_chat.id
    voice = update.message.voice
    if not voice:
        await update.message.reply_text(
            "Voice message chahiye. Text nahin. Dobara bhejiye."
        )
        return AWAITING_VOICE_SAMPLE

    index = context.user_data.get("enrollment_index", 0)
    mode = context.user_data.get("enrollment_mode", "enroll")

    # In reenroll mode, collect only 3 samples
    target_count = len(ENROLLMENT_PHRASES) if mode == "enroll" else 3

    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        await file.download_to_drive(tmp_path)
        await update.message.reply_chat_action("typing")

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
            if not user:
                await update.message.reply_text("User nahi mila. /start kariye.")
                return ConversationHandler.END

            try:
                label = f"{mode}-phrase-{index+1}"
                store_enrollment(db, user, tmp_path, label=label)
            except Exception as e:
                logger.exception(f"Enrollment failed: {e}")
                await update.message.reply_text(
                    "Voice process karne mein dikkat hui. Dobara bhejiye."
                )
                return AWAITING_VOICE_SAMPLE

            index += 1
            context.user_data["enrollment_index"] = index

            if index < target_count:
                next_phrase = ENROLLMENT_PHRASES[index]
                await update.message.reply_text(
                    f"✓ Phrase {index} record ho gaya.\n\n"
                    f"*Phrase {index+1} of {target_count}:*\n"
                    f"_{next_phrase}_",
                    parse_mode="Markdown",
                )
                return AWAITING_VOICE_SAMPLE
            else:
                # Done - mark user as enrolled
                user.enrolled = 1
                db.commit()
                await update.message.reply_text(
                    f"✅ Voice enrollment complete!\n\n"
                    f"Ab aapke voice commands verify honge. "
                    f"Security setting: *{user.security_threshold}*.\n\n"
                    f"Change karne ke liye: /security\n"
                    f"Add more samples: /reenroll",
                    parse_mode="Markdown",
                )
                context.user_data.pop("enrollment_index", None)
                context.user_data.pop("enrollment_mode", None)
                return ConversationHandler.END
        finally:
            db.close()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


async def cancel_enrollment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """User cancels with /cancel during enrollment."""
    context.user_data.pop("enrollment_index", None)
    context.user_data.pop("enrollment_mode", None)
    await update.message.reply_text(
        "Enrollment cancel ho gaya. /enroll se phir se shuru kar sakte hain."
    )
    return ConversationHandler.END


async def set_security_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Set the verification threshold. /security <strict|medium|loose|off>"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "Current security settings:\n\n"
            "*strict* — sirf aapka voice accept, rejection zyada ho sakti hai\n"
            "*medium* — balanced (default)\n"
            "*loose* — family members bhi use kar sakte hain\n"
            "*off* — koi voice verification nahi\n\n"
            "Usage: /security medium",
            parse_mode="Markdown",
        )
        return

    level = args[0].lower()
    if level not in THRESHOLDS:
        await update.message.reply_text(
            f"Galat option. Use: strict, medium, loose, off"
        )
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if not user:
            await update.message.reply_text("/start pehle bhejiye.")
            return
        user.security_threshold = level
        db.commit()
        await update.message.reply_text(
            f"✅ Security level set to *{level}*.",
            parse_mode="Markdown",
        )
    finally:
        db.close()


async def voice_status_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show current enrollment and security status. /voicestatus"""
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if not user:
            await update.message.reply_text("/start pehle bhejiye.")
            return

        profile_count = db.query(VoiceProfile).filter(
            VoiceProfile.user_id == user.id
        ).count()

        enrolled_str = "✅ enrolled" if user.enrolled else "❌ not enrolled"
        await update.message.reply_text(
            f"*Voice status:*\n"
            f"Status: {enrolled_str}\n"
            f"Samples: {profile_count}\n"
            f"Security: *{user.security_threshold}*\n\n"
            f"Change security: /security <level>\n"
            f"Add samples: /reenroll",
            parse_mode="Markdown",
        )
    finally:
        db.close()


async def reset_voice_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Delete all voice profiles and reset enrollment. /resetvoice"""
    chat_id = update.effective_chat.id
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if not user:
            return
        db.query(VoiceProfile).filter(VoiceProfile.user_id == user.id).delete()
        user.enrolled = 0
        db.commit()
        await update.message.reply_text(
            "Voice profile reset ho gaya. /enroll se phir se enrollment kariye."
        )
    finally:
        db.close()


def build_enrollment_handler() -> ConversationHandler:
    """Build the enrollment ConversationHandler.

    Used by main.py to register enrollment flow alongside other handlers.
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("enroll", start_enrollment),
            CommandHandler("reenroll", start_reenrollment),
        ],
        states={
            AWAITING_VOICE_SAMPLE: [
                MessageHandler(filters.VOICE, collect_voice_sample),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_enrollment)],
        allow_reentry=True,
    )
