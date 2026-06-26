from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

import models
from config import CORS_ORIGINS
from database import Base, engine
from routers import admin, auth, opportunities, registrations


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

        if "password_hash" in existing_columns:
            try:
                connection.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
            except Exception:
                # SQLite does not support altering NOT NULL in place. The application
                # still works there because Google-created users do not need a local password.
                pass


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
            connection.execute(text("UPDATE registrations SET telegram_username = '' WHERE telegram_username IS NULL"))


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_user_auth_columns()
    ensure_registration_profile_columns()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
app.include_router(registrations.router, prefix="/registrations", tags=["registrations"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
