import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.leave import LeaveType
from app.core.security import hash_password, create_access_token

# SQLite in-memory engine with StaticPool for thread-safe test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables in memory once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    """Provide clean database session for test execution."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(test_db: Session) -> Generator[TestClient, None, None]:
    """TestClient configured with dependency override for get_db."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def founder_user(test_db: Session) -> User:
    """Create a founder user in test database."""
    user = User(
        email="founder@jyohartech.com",
        password_hash=hash_password("Jyohar@2024"),
        role=UserRole.founder,
        is_active=True,
        email_verified=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def founder_token(founder_user: User) -> str:
    """JWT access token for founder user."""
    return create_access_token(
        {"sub": founder_user.id, "email": founder_user.email, "role": "founder"}
    )


@pytest.fixture
def test_employee(test_db: Session, founder_user: User) -> Employee:
    """Create an employee user and employee record."""
    user = User(
        email="employee@jyohartech.com",
        phone="+919876543210",
        password_hash=hash_password("Employee@123"),
        role=UserRole.employee,
        is_active=True,
        email_verified=True,
    )
    test_db.add(user)
    test_db.flush()

    emp = Employee(
        user_id=user.id,
        employee_id="JT-001",
        full_name="Pooja Sharma",
        designation="Software Engineer",
        is_active=True,
        created_by=founder_user.id,
    )
    test_db.add(emp)
    test_db.commit()
    test_db.refresh(emp)
    return emp


@pytest.fixture
def employee_token(test_employee: Employee) -> str:
    """JWT access token for employee user."""
    return create_access_token(
        {"sub": test_employee.user_id, "email": test_employee.user.email, "role": "employee"}
    )
