from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from config import GOOGLE_CLIENT_ID
from database import get_db
from models import User
from schemas import GoogleAuthIn, Token, UserCreate, UserLogin, UserOut
from security import create_access_token, get_current_user, hash_password, is_admin_email, sync_admin_access, verify_password


router = APIRouter()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _is_google_only_user(user: User) -> bool:
    return not user.password_hash and bool(user.google_sub or user.auth_provider == "google")


def _user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        auth_provider=user.auth_provider,
        avatar_url=user.avatar_url,
        is_admin=user.is_admin,
    )


def _issue_token(db: Session, user: User) -> Token:
    is_admin = sync_admin_access(user, db)
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        full_name=user.full_name,
        is_admin=is_admin,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(payload.email)
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is not None:
        if _is_google_only_user(existing_user):
            existing_user.password_hash = hash_password(payload.password)
            existing_user.full_name = existing_user.full_name or payload.full_name
            db.commit()
            db.refresh(existing_user)
            return _issue_token(db, existing_user)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        auth_provider="local",
        is_admin=is_admin_email(email, db),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token(db, user)


@router.get("/me", response_model=UserOut)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    sync_admin_access(current_user, db)
    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        auth_provider=current_user.auth_provider,
        avatar_url=current_user.avatar_url,
        is_admin=current_user.is_admin,
    )


@router.post("/login", response_model=Token)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    email = _normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.password_hash:
        if _is_google_only_user(user):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account uses Google sign-in. Please use the Google button below.",
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return _issue_token(db, user)


@router.post("/google", response_model=Token)
def login_with_google(payload: GoogleAuthIn, db: Session = Depends(get_db)) -> Token:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured yet",
        )

    try:
        token_info = google_id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        ) from exc

    email = (token_info.get("email") or "").lower()
    google_sub = token_info.get("sub")
    full_name = token_info.get("name") or email.split("@")[0] or "Community Member"
    picture = token_info.get("picture")
    email_verified = token_info.get("email_verified")

    if not email or not google_sub or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account is missing required verified profile data",
        )

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if user is None:
        user = db.query(User).filter(User.email == email).first()

    if user is None:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=None,
            google_sub=google_sub,
            auth_provider="google",
            avatar_url=picture,
            is_admin=is_admin_email(email, db),
        )
        db.add(user)
    else:
        user.full_name = user.full_name or full_name
        user.google_sub = google_sub
        user.auth_provider = "google"
        if picture:
            user.avatar_url = picture

    is_admin = sync_admin_access(user, db)
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        full_name=user.full_name,
        is_admin=is_admin,
    )
