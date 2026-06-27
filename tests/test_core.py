import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "development"

from database import Base, get_db
from main import app
from models import AdminEmail, User
from security import hash_password


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)

    with TestingSessionLocal() as db:
        admin = User(
            full_name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("adminpass123"),
            auth_provider="local",
            is_admin=True,
        )
        db.add(admin)
        db.add(AdminEmail(email="admin@example.com"))
        db.commit()

    yield test_client

    app.dependency_overrides.clear()
    engine.dispose()
    Path(db_path).unlink(missing_ok=True)


def register_user(client: TestClient, email: str = "member@example.com", password: str = "password123"):
    return client.post(
        "/auth/register",
        json={"full_name": "Test Member", "email": email, "password": password},
    )


def login_user(client: TestClient, email: str = "member@example.com", password: str = "password123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def google_auth(client: TestClient, credential: str = "fake-google-credential"):
    return client.post("/auth/google", json={"credential": credential})


def google_token_info(
    *,
    email: str = "newgoogle@example.com",
    sub: str = "google-sub-new",
    name: str = "New Google User",
    picture: str = "https://example.com/photo.jpg",
    email_verified: bool = True,
):
    return {
        "email": email,
        "sub": sub,
        "name": name,
        "picture": picture,
        "email_verified": email_verified,
    }


def get_admin_token(client: TestClient):
    response = login_user(client, "admin@example.com", "adminpass123")
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_rejects_short_password(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"full_name": "Test Member", "email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 400


def test_duplicate_registration_is_blocked(client: TestClient):
    register_user(client)
    token = login_user(client).json()["access_token"]
    admin_token = get_admin_token(client)

    opportunity_response = client.post(
        "/admin/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Robotics Club",
            "description": "Build robots together every week.",
            "type": "club",
            "region_name": "Nukus",
        },
    )
    assert opportunity_response.status_code == 201
    opportunity_id = opportunity_response.json()["id"]

    payload = {
        "opportunity_id": opportunity_id,
        "first_name": "Ali",
        "last_name": "Karimov",
        "age": 18,
        "phone_number": "+998901234567",
        "telegram_username": "alikar",
    }

    first = client.post(
        "/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    second = client.post(
        "/registrations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == "Already registered"


def test_admin_can_export_registrations_csv(client: TestClient):
    register_user(client, "export@example.com")
    member_token = login_user(client, "export@example.com").json()["access_token"]
    admin_token = get_admin_token(client)

    opportunity_id = client.post(
        "/admin/opportunities",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Design Workshop",
            "description": "Learn design thinking in a hands-on workshop.",
            "type": "workshop",
            "region_name": "Nukus",
        },
    ).json()["id"]

    client.post(
        "/registrations",
        headers={"Authorization": f"Bearer {member_token}"},
        json={
            "opportunity_id": opportunity_id,
            "first_name": "Dina",
            "last_name": "Yusupova",
            "age": 20,
            "phone_number": "+998901112233",
            "telegram_username": "dinay",
        },
    )

    response = client.get(
        "/admin/registrations/export",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Design Workshop" in response.text
    assert "dinay" in response.text


def test_health_reports_database_status(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "database_path" in body
    assert "users_count" in body


def test_register_returns_token(client: TestClient):
    response = register_user(client, "token@example.com", "password123")
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["full_name"] == "Test Member"


def test_duplicate_email_signup_is_blocked(client: TestClient):
    first = register_user(client, "duplicate@example.com", "password123")
    second = register_user(client, "duplicate@example.com", "password123")

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_register_then_login_again(client: TestClient):
    register_user(client, "repeat@example.com", "password123")
    first_login = login_user(client, "repeat@example.com", "password123")
    second_login = login_user(client, "repeat@example.com", "password123")

    assert first_login.status_code == 200
    assert second_login.status_code == 200


def test_google_only_user_gets_clear_login_error(client: TestClient):
    from database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        db.add(
            User(
                full_name="Google User",
                email="google@example.com",
                password_hash=None,
                google_sub="google-sub-123",
                auth_provider="google",
            )
        )
        db.commit()
    finally:
        db.close()

    response = login_user(client, "google@example.com", "password123")
    assert response.status_code == 401
    assert "Google sign-in" in response.json()["detail"]


def test_google_only_user_can_add_password_via_register(client: TestClient):
    from database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        db.add(
            User(
                full_name="Google User",
                email="link@example.com",
                password_hash=None,
                google_sub="google-sub-456",
                auth_provider="google",
            )
        )
        db.commit()
    finally:
        db.close()

    register_response = register_user(client, "link@example.com", "password123")
    login_response = login_user(client, "link@example.com", "password123")

    assert register_response.status_code == 201
    assert register_response.json()["access_token"]
    assert login_response.status_code == 200


@patch("routers.auth.GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
@patch(
    "routers.auth.google_id_token.verify_oauth2_token",
    return_value=google_token_info(),
)
def test_google_auth_creates_new_user(mock_verify, client: TestClient):
    response = google_auth(client)

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["full_name"] == "New Google User"
    mock_verify.assert_called_once()

    from database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == "newgoogle@example.com").first()
        assert user is not None
        assert user.google_sub == "google-sub-new"
        assert user.auth_provider == "google"
        assert user.password_hash is None
        assert user.avatar_url == "https://example.com/photo.jpg"
    finally:
        db.close()


@patch("routers.auth.GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
@patch(
    "routers.auth.google_id_token.verify_oauth2_token",
    return_value=google_token_info(
        email="LinkMe@Example.com",
        sub="google-sub-link",
        name="Linked Google User",
    ),
)
def test_google_auth_links_existing_email_password_account(mock_verify, client: TestClient):
    register_user(client, "linkme@example.com", "password123")

    response = google_auth(client)

    assert response.status_code == 200
    assert response.json()["access_token"]

    from database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == "linkme@example.com").first()
        assert user is not None
        assert user.google_sub == "google-sub-link"
        assert user.password_hash is not None
        assert user.auth_provider == "local"
    finally:
        db.close()

    password_login = login_user(client, "linkme@example.com", "password123")
    assert password_login.status_code == 200


@patch("routers.auth.GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
@patch(
    "routers.auth.google_id_token.verify_oauth2_token",
    return_value=google_token_info(email="repeatgoogle@example.com", sub="google-sub-repeat"),
)
def test_google_auth_repeat_login_finds_existing_google_sub(mock_verify, client: TestClient):
    first = google_auth(client)
    second = google_auth(client)

    assert first.status_code == 200
    assert second.status_code == 200

    from database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        users = db.query(User).filter(User.email == "repeatgoogle@example.com").all()
        assert len(users) == 1
        assert users[0].google_sub == "google-sub-repeat"
    finally:
        db.close()


@patch("routers.auth.GOOGLE_CLIENT_ID", "")
def test_google_auth_returns_503_when_not_configured(client: TestClient):
    response = google_auth(client)

    assert response.status_code == 503
    assert response.json()["detail"] == "Google sign-in is not configured yet"


@patch("routers.auth.GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
@patch(
    "routers.auth.google_id_token.verify_oauth2_token",
    side_effect=ValueError("invalid token"),
)
def test_google_auth_rejects_invalid_credential(mock_verify, client: TestClient):
    response = google_auth(client)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google credential"


@patch("routers.auth.GOOGLE_CLIENT_ID", "test-google-client-id.apps.googleusercontent.com")
@patch(
    "routers.auth.google_id_token.verify_oauth2_token",
    return_value=google_token_info(email="unverified@example.com", email_verified=False),
)
def test_google_auth_rejects_unverified_email(mock_verify, client: TestClient):
    response = google_auth(client)

    assert response.status_code == 400
    assert response.json()["detail"] == "Google account is missing required verified profile data"
