import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.job_position import JobPosition
from app.models.referral import Referral, ReferralStatus
from app.services.sharepoint.mock_service import MockSharePointService
from app.services.sharepoint import get_sharepoint_service

# Use in-memory SQLite for fast, isolated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
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
def seeded_users(db_session):
    hr = User(
        id="test-hr-id-01",
        entra_user_id="entra-test-hr",
        name="HR Admin Tester",
        email="hr.test@tangentia.com",
        role=UserRole.HR_ADMIN.value,
        department="Human Resources",
    )
    emp1 = User(
        id="test-emp-id-01",
        entra_user_id="entra-test-emp-1",
        name="Employee One",
        email="emp1@tangentia.com",
        role=UserRole.EMPLOYEE.value,
        department="Engineering",
    )
    emp2 = User(
        id="test-emp-id-02",
        entra_user_id="entra-test-emp-2",
        name="Employee Two",
        email="emp2@tangentia.com",
        role=UserRole.EMPLOYEE.value,
        department="Marketing",
    )
    db_session.add_all([hr, emp1, emp2])
    db_session.commit()
    return {"hr": hr, "emp1": emp1, "emp2": emp2}


@pytest.fixture
def seeded_job(db_session):
    job = JobPosition(
        id="test-job-id-01",
        title="Software Engineer",
        department="Engineering",
        description="Write clean code and build services.",
        location="Toronto, Canada",
        employment_type="Full-time",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()
    return job
