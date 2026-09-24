import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if db_url.startswith("sqlite:///./"):
        filename = db_url.replace("sqlite:///./", "")
        # Resolve to project root if present
        parent_candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../", filename))
        if os.path.exists(parent_candidate):
            db_url = f"sqlite:///{parent_candidate}"
else:
    # PostgreSQL production connection pooling
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20
    })

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and perform idempotent column migrations."""
    from app.db.base import Base
    import app.models  # noqa
    from app.core.logging import logger
    from sqlalchemy import text

    # 1. On PostgreSQL, ensure required extensions exist BEFORE creating tables (e.g. pgvector for VectorType)
    if "postgres" in db_url:
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm";'))
                conn.commit()
                logger.info("Verified PostgreSQL extensions (vector, uuid-ossp, pg_trgm).")
        except Exception as e:
            logger.warning(f"PostgreSQL extension check notice: {e}")

    # 2. Create tables safely
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema tables created/verified successfully.")
    except Exception as e:
        logger.error(f"Database table creation notice: {e}")

    # 3. Perform idempotent schema migrations
    try:
        with engine.connect() as conn:
            if db_url.startswith("sqlite"):
                table_check = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
                ).fetchone()
                if table_check:
                    res = conn.execute(text("PRAGMA table_info(users);")).fetchall()
                    cols = [r[1] for r in res]
                    if "hashed_password" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255);"))
                        conn.commit()
                        logger.info("Migrated users table: added hashed_password column.")
            elif "postgres" in db_url:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);"))
                conn.execute(text("ALTER TABLE users ALTER COLUMN firebase_uid DROP NOT NULL;"))
                conn.commit()
                logger.info("PostgreSQL users table schema verified.")
    except Exception as e:
        logger.warning(f"Database migration check notice: {e}")
