from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from config import GOOGLE_CLIENT_ID
from database import get_db
from models import User
from schemas import GoogleAuthIn, Token, UserCreate, UserLogin, UserOut
from security import create_access_token, hash_password, is_admin_email, verify_password


router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        auth_provider=user.auth_provider,
        avatar_url=user.avatar_url,
        is_admin=is_admin_email(user.email),
    )


@router.post("/login", response_model=Token)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        full_name=user.full_name,
        is_admin=is_admin_email(user.email),
    )


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
        )
        db.add(user)
    else:
        user.full_name = user.full_name or full_name
        user.google_sub = google_sub
        user.auth_provider = "google"
        if picture:
            user.avatar_url = picture

    db.commit()
    db.refresh(user)

    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        full_name=user.full_name,
        is_admin=is_admin_email(user.email),
    )
