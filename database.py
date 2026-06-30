from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL, is_postgresql_url, is_sqlite_url


def _prepare_sqlite_path(database_url: str) -> None:
    if not is_sqlite_url(database_url):
        return

    db_path = database_url.removeprefix("sqlite:///")
    if db_path == ":memory:":
        return

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def _build_engine(database_url: str):
    _prepare_sqlite_path(database_url)

    engine_kwargs: dict = {}

    if is_sqlite_url(database_url):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    elif is_postgresql_url(database_url):
        engine_kwargs["pool_pre_ping"] = True

    return create_engine(database_url, **engine_kwargs)


engine = _build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
