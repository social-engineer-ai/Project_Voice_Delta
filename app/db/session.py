"""Database session factory."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """Yield a database session. Use in FastAPI or as a context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
