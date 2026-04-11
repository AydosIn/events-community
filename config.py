import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/events_community",
)

SECRET_KEY = os.getenv("SECRET_KEY", "events_community_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
