import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db
from app.main import app
from app.models import User, Customer, Service
from app.auth import hash_password, create_access_token

# Use in-memory SQLite with StaticPool for fast, isolated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the test database once per session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    """Yield a database session rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def seed_test_users(db_session):
    """Seed test users into database."""
    admin = User(
        email="admin@test.local",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin Test",
        role="admin",
        is_active=True
    )
    staff = User(
        email="staff@test.local",
        hashed_password=hash_password("StaffPass123!"),
        full_name="Staff Test",
        role="staff",
        is_active=True
    )
    customer_user = User(
        email="customer@test.local",
        hashed_password=hash_password("CustomerPass123!"),
        full_name="Customer Test",
        role="customer",
        is_active=True
    )
    inactive_user = User(
        email="inactive@test.local",
        hashed_password=hash_password("InactivePass123!"),
        full_name="Inactive Test",
        role="customer",
        is_active=False
    )
    
    db_session.add_all([admin, staff, customer_user, inactive_user])
    db_session.commit()
    for u in [admin, staff, customer_user, inactive_user]:
        db_session.refresh(u)

    # Seed linked customer profile
    customer_profile = Customer(
        name="Customer Test",
        email="customer@test.local",
        phone="555-0100",
        address="100 Test St",
        user_id=customer_user.id
    )
    db_session.add(customer_profile)

    # Seed test service
    service = Service(
        name="Initial IT Setup",
        description="Initial workstation configuration",
        price=100.0,
        duration_minutes=60,
        is_active=True
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(customer_profile)
    db_session.refresh(service)

    return {
        "admin": admin,
        "staff": staff,
        "customer_user": customer_user,
        "inactive_user": inactive_user,
        "customer_profile": customer_profile,
        "service": service
    }

@pytest.fixture
def admin_headers(seed_test_users):
    token = create_access_token({"sub": "admin@test.local", "role": "admin", "user_id": seed_test_users["admin"].id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def staff_headers(seed_test_users):
    token = create_access_token({"sub": "staff@test.local", "role": "staff", "user_id": seed_test_users["staff"].id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def customer_headers(seed_test_users):
    token = create_access_token({"sub": "customer@test.local", "role": "customer", "user_id": seed_test_users["customer_user"].id})
    return {"Authorization": f"Bearer {token}"}
