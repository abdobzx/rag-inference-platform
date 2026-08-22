import os

# Must be set before any app module is imported, since security.py reads
# JWT_SECRET_KEY at import time.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-do-not-use-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.database import Base, get_db
from src.main import app
from src.middleware.rate_limit import rate_limiter

# Shared in-memory SQLite engine for the whole test session. StaticPool keeps
# the same connection alive across sessions - a fresh :memory: db per
# connection would otherwise lose its schema between requests.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create the schema once for the whole test session. Dropping/recreating it
# around every single test raced with the TestClient's own request handling
# (intermittent "no such table" failures depending on test order) - clearing
# rows between tests is both simpler and avoids that race entirely.
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Empty every table before each test so tests don't see each other's rows."""
    yield
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """The rate limiter is a real, in-memory, process-global singleton (by IP).
    Without resetting it, a test suite making several requests per test from the
    same TestClient 'IP' trips its own burst limit - that's real middleware
    behavior, not something to disable, just something to isolate per test.
    """
    rate_limiter.requests.clear()
    yield
    rate_limiter.requests.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sent_emails(monkeypatch):
    """Registration sends a real email by default; tests shouldn't hit SMTP.
    Returns a list this fixture appends (to, code, username) tuples to, so
    tests can retrieve the verification code the way a real mail service
    integration test would - from what was sent, not by reaching into the DB
    from a second, separate session.
    """
    sent = []

    def fake_send(to_email, verification_code, username):
        sent.append((to_email, verification_code, username))
        return True

    monkeypatch.setattr("src.routes.auth.send_verification_email", fake_send)
    return sent


@pytest.fixture
def no_email_sending(sent_emails):
    """Back-compat alias for tests that only care that sending is mocked out."""
    return sent_emails
