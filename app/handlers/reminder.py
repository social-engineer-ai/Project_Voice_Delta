"""Handler for 'reminder' intent: schedule a reminder ping.

Uses APScheduler with the database-backed job store so reminders survive
bot restarts. When the scheduled time arrives, the bot sends a Telegram
message to the user with the reminder content.
"""
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from app.db.session import SessionLocal
from app.db.models import Task, User
from app.services.classify import IntentClassification

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def parse_scheduled_time(time_str: str) -> datetime | None:
    """Parse the scheduled_time field from Gemini output.

    Gemini returns either ISO 8601 or relative expressions. This handles both.
    Returns a timezone-aware datetime in IST, or None if unparseable.
    """
    if not time_str:
        return None

    time_str = time_str.strip().lower()

    # Try ISO 8601 first
    try:
        dt = datetime.fromisoformat(time_str.replace("z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt
    except ValueError:
        pass

    # Relative: "in 30 minutes", "in 2 hours"
    now = datetime.now(IST)
    m = re.match(r"in (\d+)\s*(minute|minutes|hour|hours|min|hr)", time_str)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "min" in unit:
            return now + timedelta(minutes=n)
        else:
            return now + timedelta(hours=n)

    # Hindi-ish relative: "30 minute baad", "2 ghante baad"
    m = re.match(r"(\d+)\s*(minute|min|ghante|ghanta|hour)\s*baad", time_str)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "min" in unit:
            return now + timedelta(minutes=n)
        else:
            return now + timedelta(hours=n)

    # "kal" = tomorrow 9 AM (default)
    if "kal" in time_str or "tomorrow" in time_str:
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

    return None


async def send_reminder_ping(
    application, chat_id: int, reminder_content: str, task_id: int
) -> None:
    """Called by the scheduler when a reminder fires."""
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text=f"⏰ *Reminder*\n\n{reminder_content}",
            parse_mode="Markdown",
        )
        # Mark task completed
        db = SessionLocal()
        try:
            task = db.query(Task).get(task_id)
            if task:
                task.status = "sent"
                db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.exception(f"Failed to send reminder {task_id}: {e}")


async def handle_reminder_intent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    intent: IntentClassification,
) -> None:
    """Handle a 'set reminder' command."""
    db = SessionLocal()
    try:
        if not intent.reminder_text:
            await update.message.reply_text(
                "Kya yaad dilana hai? Content bataiye."
            )
            return

        scheduled = parse_scheduled_time(intent.scheduled_time or "")
        if not scheduled:
            await update.message.reply_text(
                "Samay samajh nahin aaya. Example: '3 baje', 'kal subah', '30 minute baad'."
            )
            return

        # Don't allow past times
        if scheduled < datetime.now(IST):
            await update.message.reply_text(
                "Yeh time toh beet gaya. Aage ka time bataiye."
            )
            return

        task = Task(
            user_id=user.id,
            task_type="reminder",
            status="scheduled",
            raw_transcript=context.user_data.get("last_transcript"),
            payload={"reminder_text": intent.reminder_text},
            scheduled_at=scheduled,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Schedule with APScheduler
        scheduler = context.application.bot_data.get("scheduler")
        if scheduler:
            scheduler.add_job(
                send_reminder_ping,
                trigger="date",
                run_date=scheduled,
                args=[context.application, user.telegram_chat_id, intent.reminder_text, task.id],
                id=f"reminder_{task.id}",
            )

        display_time = scheduled.strftime("%d %b, %I:%M %p")
        await update.message.reply_text(
            f"✅ Reminder set: *{display_time}*\n\n_{intent.reminder_text}_",
            parse_mode="Markdown",
        )

    finally:
        db.close()
