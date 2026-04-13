import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _is_production() -> bool:
    return os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT", "").lower() == "production"


def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    if _is_production():
        raise RuntimeError(
            "DATABASE_URL is required in production. Set it in Render to your managed Postgres URL."
        )

    return "postgresql://postgres:postgres@localhost:5432/events_community"


def _get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")

    if secret_key:
        return secret_key

    if _is_production():
        raise RuntimeError("SECRET_KEY is required in production. Set it in Render before deploying.")

    return "events_community_secret"


DATABASE_URL = _get_database_url()
SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
