"""SQLAlchemy models for ShopSaarthi.

The schema is deliberately simple for the prototype. Four core tables:
- User: one row per shopkeeper (identified by Telegram chat_id)
- Contact: the shopkeeper's address book (who "Ramu" or "the driver" refers to)
- Task: captured tasks with their type, content, status, and any scheduled time
- VoiceProfile: enrolled voice embeddings for speaker verification

The Task table is a single table for all four intent types. The `task_type` column
discriminates between message, reminder, delegate, and call. Intent-specific fields
go into `payload` as JSON to keep the schema simple; we can normalize later if
certain intents need their own tables.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, JSON, Index, BigInteger,
    LargeBinary, Float
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """A shopkeeper using the bot. Identified by their Telegram chat_id."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    language = Column(String(10), default="hi")  # hi, en, hi-en
    security_threshold = Column(String(16), default="medium")  # strict, medium, loose, off
    enrolled = Column(Integer, default=0)  # 0 = not enrolled, 1 = enrolled
    created_at = Column(DateTime, default=datetime.utcnow)

    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    voice_profiles = relationship(
        "VoiceProfile", back_populates="user", cascade="all, delete-orphan"
    )


class Contact(Base):
    """A person in the shopkeeper's address book.

    Aliases are stored as a JSON list so "Ramu", "servant", "naukar" can all
    resolve to the same person. Role is a free-text tag like "driver", "accountant",
    "supplier", "customer" — used to resolve references like "the driver".
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(32), nullable=False)
    role = Column(String(64), nullable=True)  # driver, accountant, supplier, etc.
    aliases = Column(JSON, default=list)  # alternate names/references
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="contacts")

    __table_args__ = (
        Index("idx_user_contact_name", "user_id", "name"),
    )


class Task(Base):
    """A captured task from a voice command.

    task_type: one of "message", "reminder", "delegate", "call"
    status: "pending", "sent", "completed", "failed", "cancelled"
    payload: JSON dict with intent-specific fields (see classify.py for schemas)
    scheduled_at: for reminders and delayed follow-ups
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(String(32), nullable=False)
    status = Column(String(32), default="pending")
    raw_transcript = Column(Text, nullable=True)  # original Sarvam transcription
    payload = Column(JSON, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("idx_user_task_status", "user_id", "status"),
        Index("idx_scheduled", "scheduled_at", "status"),
    )


class VoiceProfile(Base):
    """An enrolled voice sample for speaker verification.

    Each user can have multiple voice profiles (captured at different times or
    in different acoustic conditions) to make matching more robust. When a
    new command comes in, we compare the incoming embedding against all of
    the user's enrolled embeddings and take the maximum similarity.

    Embeddings are stored as BLOB (numpy float32 array bytes) for efficiency.
    As of 2026-04-22, the encoder is SpeechBrain's ECAPA-TDNN
    (`speechbrain/spkrec-ecapa-voxceleb`), which produces 192-dimensional
    float32 embeddings = 768 bytes each. Profiles persisted under the earlier
    Resemblyzer encoder are 256-dim (1024 bytes) and must be re-captured —
    `verify_speaker` logs a warning and skips dimension-mismatched profiles
    rather than hard-failing.
    """
    __tablename__ = "voice_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    embedding = Column(LargeBinary, nullable=False)
    sample_label = Column(String(64), nullable=True)  # optional tag: "enrollment", "reenroll-2026-06"
    quality_score = Column(Float, nullable=True)  # optional: how clean the recording was
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="voice_profiles")
