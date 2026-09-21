import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

db_url = settings.DATABASE_URL
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
