import os
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-1234567890-very-secure"
os.environ["COOKIE_SECURE"] = "false"
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_EMAIL"] = "admin@freshmart.local"
os.environ["ADMIN_PASSWORD"] = "Admin@12345"

from app.config import get_settings
get_settings.cache_clear()

from app.database import Base, get_db
from app.main import app
from app.models import Product, User
from app.services.auth_service import ensure_admin_user, hash_password

# Use an in-memory SQLite database with StaticPool so all connections share the same memory DB
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(test_engine, "connect")
def enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database():
    """
    Creates fresh schema and seeds the default admin user before each test,
    then tears down tables after the test finishes.
    """
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    ensure_admin_user(session)
    session.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """
    Yields a direct session to inspect or create database fixtures.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """
    TestClient with overridden get_db dependency.
    """
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin(client):
    """
    Logs in the default admin and returns (client, csrf_token).
    """
    login_resp = client.post(
        "/api/auth/admin/login",
        json={"username_or_email": "testadmin", "password": "Admin@12345"}
    )
    assert login_resp.status_code == 200
    csrf_token = client.cookies.get("grocery_csrf")
    return client, csrf_token


@pytest.fixture
def test_customer(client):
    """
    Registers and logs in a test customer, returning (client, user_data, csrf_token).
    """
    reg_data = {
        "full_name": "Test Customer",
        "email": "customer@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_resp = client.post("/api/auth/register", json=reg_data)
    assert reg_resp.status_code == 201
    csrf_token = client.cookies.get("grocery_csrf")
    return client, reg_resp.json(), csrf_token


@pytest.fixture
def sample_product(db_session):
    """
    Creates and returns a sample grocery product in the test DB.
    """
    prod = Product(
        name="Organic Test Apples",
        price=Decimal("120.00"),
        category="Fruits",
        stock_quantity=15,
        image_url="https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6",
        description="Fresh crispy test apples"
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod
