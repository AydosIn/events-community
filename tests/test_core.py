import os
import tempfile
from pathlib import Path

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
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"
