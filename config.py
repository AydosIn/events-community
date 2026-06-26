import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BASE_DIR / "data" / "events_community.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
DEPLOYED_FRONTEND_ORIGINS = [
    "https://events-community-frontend.vercel.app",
    "https://events-community-frontend-6ks2v9vi1-aydosed-3118s-projects.vercel.app",
]


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _split_lower_csv(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _unique_values(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _is_production() -> bool:
    return any(
        (
            os.getenv("RENDER") == "true",
            os.getenv("ENVIRONMENT", "").lower() == "production",
            os.getenv("DIGITALOCEAN_APP_ID"),
        )
    )


def _is_development() -> bool:
    return os.getenv("ENVIRONMENT", "").lower() in {"", "development", "local"}


def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url and not database_url.startswith("sqlite"):
        raise RuntimeError(
            "Only SQLite is supported. Set DATABASE_URL to a sqlite:// path or leave it unset for the default."
        )
    return database_url or DEFAULT_DATABASE_URL


def _get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")

    if secret_key:
        return secret_key

    if _is_development():
        return "dev-only-change-before-deploy"

    raise RuntimeError("SECRET_KEY is required in this environment. Set it in your hosting platform before deploying.")


DATABASE_URL = _get_database_url()
SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
CORS_ORIGINS = _unique_values(
    _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000")) + DEPLOYED_FRONTEND_ORIGINS
)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
ADMIN_EMAILS = _split_lower_csv(os.getenv("ADMIN_EMAILS", ""))
