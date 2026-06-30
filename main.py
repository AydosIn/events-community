from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session

import models
from config import ADMIN_EMAILS, CORS_ORIGINS, get_database_info_for_health
from database import Base, SessionLocal, engine
from models import AdminEmail, User
from routers import admin, auth, opportunities, registrations


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_sqlite() -> bool:
    return engine.dialect.name == "sqlite"


def _timestamp_type() -> str:
    return "DATETIME" if _is_sqlite() else "TIMESTAMP"


def _boolean_default_false() -> str:
    return "0" if _is_sqlite() else "false"


def ensure_user_auth_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    with engine.begin() as connection:
        if "google_sub" not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN google_sub VARCHAR"))

        if "auth_provider" not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR DEFAULT 'local'"))
            connection.execute(text("UPDATE users SET auth_provider = 'local' WHERE auth_provider IS NULL"))

        if "avatar_url" not in existing_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))

        if "last_login_at" not in existing_columns:
            connection.execute(
                text(f"ALTER TABLE users ADD COLUMN last_login_at {_timestamp_type()}")
            )

        if "password_hash" in existing_columns:
            try:
                connection.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
            except Exception:
                # SQLite does not support altering NOT NULL in place.
                pass

        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub "
                "ON users (google_sub) WHERE google_sub IS NOT NULL"
            )
        )


def ensure_is_admin_column() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    with engine.begin() as connection:
        if "is_admin" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL "
                    f"DEFAULT {_boolean_default_false()}"
                )
            )


def bootstrap_admin_emails() -> None:
    """Seed configured admin emails and promote matching existing users."""
    if not ADMIN_EMAILS:
        return

    db: Session = SessionLocal()
    try:
        for email in ADMIN_EMAILS:
            normalized_email = email.lower()
            existing_admin_email = (
                db.query(AdminEmail).filter(AdminEmail.email == normalized_email).first()
            )
            if existing_admin_email is None:
                db.add(AdminEmail(email=normalized_email))

            db.query(User).filter(
                func.lower(User.email) == normalized_email,
                User.is_admin.is_(False),
            ).update({User.is_admin: True}, synchronize_session=False)
        db.commit()
    finally:
        db.close()


def ensure_registration_profile_columns() -> None:
    inspector = inspect(engine)
    if "registrations" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("registrations")}

    with engine.begin() as connection:
        if "first_name" not in existing_columns:
            connection.execute(text("ALTER TABLE registrations ADD COLUMN first_name VARCHAR"))
            connection.execute(text("UPDATE registrations SET first_name = '' WHERE first_name IS NULL"))

        if "last_name" not in existing_columns:
            connection.execute(text("ALTER TABLE registrations ADD COLUMN last_name VARCHAR"))
            connection.execute(text("UPDATE registrations SET last_name = '' WHERE last_name IS NULL"))

        if "age" not in existing_columns:
            connection.execute(text("ALTER TABLE registrations ADD COLUMN age INTEGER"))
            connection.execute(text("UPDATE registrations SET age = 0 WHERE age IS NULL"))

        if "phone_number" not in existing_columns:
            connection.execute(text("ALTER TABLE registrations ADD COLUMN phone_number VARCHAR"))
            connection.execute(text("UPDATE registrations SET phone_number = '' WHERE phone_number IS NULL"))

        if "telegram_username" not in existing_columns:
            connection.execute(text("ALTER TABLE registrations ADD COLUMN telegram_username VARCHAR"))
            connection.execute(
                text("UPDATE registrations SET telegram_username = '' WHERE telegram_username IS NULL")
            )


def ensure_registration_unique_index() -> None:
    inspector = inspect(engine)
    if "registrations" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_opportunity "
                "ON registrations (user_id, opportunity_id)"
            )
        )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_user_auth_columns()
    ensure_is_admin_column()
    ensure_registration_profile_columns()
    ensure_registration_unique_index()
    bootstrap_admin_emails()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    database_info = get_database_info_for_health()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            inspector = inspect(engine)
            user_count = 0
            if "users" in inspector.get_table_names():
                user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        return {
            "status": "ok",
            "database": "ok",
            **database_info,
            "users_count": user_count,
        }
    except Exception as exc:
        return {
            "status": "error",
            "database": "unavailable",
            **database_info,
            "detail": str(exc),
        }


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
app.include_router(registrations.router, prefix="/registrations", tags=["registrations"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
