import os
from pathlib import Path
from urllib.parse import urlparse

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


def normalize_database_url(database_url: str) -> str:
    """Normalize provider URLs for SQLAlchemy + psycopg."""
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://") :]

    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://") :]

    return database_url


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def is_postgresql_url(database_url: str) -> bool:
    return database_url.startswith("postgresql")


def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        if _is_production():
            raise RuntimeError(
                "DATABASE_URL is required in production. Set it to your PostgreSQL connection string."
            )
        return DEFAULT_DATABASE_URL

    database_url = normalize_database_url(database_url)

    if _is_production() and is_sqlite_url(database_url):
        raise RuntimeError(
            "SQLite is for local development only. Set DATABASE_URL to a PostgreSQL connection string in production."
        )

    if not is_sqlite_url(database_url) and not is_postgresql_url(database_url):
        raise RuntimeError(
            "DATABASE_URL must be a SQLite or PostgreSQL connection string."
        )

    return database_url


def _get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")

    if secret_key:
        return secret_key

    if _is_development():
        return "dev-only-change-before-deploy"

    raise RuntimeError("SECRET_KEY is required in this environment. Set it in your hosting platform before deploying.")


DATABASE_URL = _get_database_url()


def get_database_info_for_health() -> dict[str, str]:
    if is_sqlite_url(DATABASE_URL):
        db_path = DATABASE_URL.removeprefix("sqlite:///")
        if db_path == ":memory:":
            resolved_path = ":memory:"
        else:
            resolved_path = str(Path(db_path).resolve())

        return {
            "database_backend": "sqlite",
            "database_path": resolved_path,
        }

    parsed = urlparse(DATABASE_URL)
    safe_netloc = parsed.hostname or "unknown-host"
    if parsed.port:
        safe_netloc = f"{safe_netloc}:{parsed.port}"

    database_name = parsed.path.lstrip("/") or "unknown"

    return {
        "database_backend": "postgresql",
        "database_host": safe_netloc,
        "database_name": database_name,
    }


SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "720"))
CORS_ORIGINS = _unique_values(
    _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000")) + DEPLOYED_FRONTEND_ORIGINS
)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
ADMIN_EMAILS = _split_lower_csv(os.getenv("ADMIN_EMAILS", ""))
