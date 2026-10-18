"""
Database connection, session management, and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from config.settings import DATABASE_URL
from database.models import Base

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
ScopedSession = scoped_session(SessionFactory)


def init_db():
    """Initializes all database tables defined in Base."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Context manager for safe database session operations."""
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
