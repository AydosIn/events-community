import re

from fastapi import HTTPException, status

PHONE_PATTERN = re.compile(r"^\+?[\d\s()-]{7,20}$")
TELEGRAM_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{4,31}$")
ALLOWED_OPPORTUNITY_TYPES = {"club", "project", "workshop"}


def normalize_telegram_username(value: str) -> str:
    return value.strip().lstrip("@")


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    return password


def validate_full_name(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 characters",
        )
    return cleaned


def validate_person_name(value: str, field_label: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} must be at least 2 characters",
        )
    return cleaned


def validate_age(age: int) -> int:
    if age < 13 or age > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age must be between 13 and 100",
        )
    return age


def validate_phone_number(value: str) -> str:
    cleaned = value.strip()
    if not PHONE_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid phone number",
        )
    return cleaned


def validate_telegram_username(value: str) -> str:
    cleaned = normalize_telegram_username(value)
    if not TELEGRAM_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram username must be 5-32 characters (letters, numbers, underscore)",
        )
    return cleaned


def validate_opportunity_type(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in ALLOWED_OPPORTUNITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be club, project, or workshop",
        )
    return cleaned


def validate_opportunity_title(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title must be at least 3 characters",
        )
    return cleaned


def validate_opportunity_description(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be at least 10 characters",
        )
    return cleaned


def validate_region_name(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Region must be at least 2 characters",
        )
    return cleaned
