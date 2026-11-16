import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Configure SQLite engine with proper threading and connect args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False
)

# Enforce foreign key constraints and WAL mode for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency yielding database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def check_db_health() -> tuple[bool, str]:
    """Verify database responsiveness and integrity."""
    try:
        with engine.connect() as conn:
            # Check basic query execution
            conn.execute(text("SELECT 1"))
            
            # Check SQLite integrity if SQLite
            if settings.DATABASE_URL.startswith("sqlite"):
                result = conn.execute(text("PRAGMA integrity_check")).scalar()
                if result != "ok":
                    return False, f"Integrity check failed: {result}"
        return True, "Database operational and integrity verified"
    except Exception as e:
        return False, str(e)
