"""Create database tables. Run once before starting the bot."""
from app.db.models import Base
from app.db.session import engine


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()
