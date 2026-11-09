"""Test configuration: real PostgreSQL (TEST_DATABASE_URL), per-test transaction rollback."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://oncoai:oncoai@localhost:5432/oncoai_test"
)
_UPLOAD_ROOT = tempfile.mkdtemp(prefix="oncoai-test-uploads-")
os.environ.update(
    {
        "DATABASE_URL": TEST_DATABASE_URL,
        "ENVIRONMENT": "test",
        "RATE_LIMIT_ENABLED": "false",
        "MODEL_WARMUP": "false",
        "SEED_SAMPLE_DATA": "false",
        "ANALYZER_KIND": "heuristic",
        "UPLOAD_DIR": _UPLOAD_ROOT,
        "BCRYPT_ROUNDS": "4",
        "ANTHROPIC_API_KEY": "",
        "IMAGE_ENCRYPTION_KEY": "",
        "LOG_LEVEL": "WARNING",
        "LOG_JSON": "false",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.ml import registry  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import Role  # noqa: E402
from app.services.seed import seed_dermatologists  # noqa: E402
from tests.synthetic import irregular_spot, regular_spot, to_jpeg  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Iterator[None]:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db() -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    seed_dermatologists(session)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "uploads")
    limiter.reset()
    registry.reset_analyzer()
    yield
    registry.reset_analyzer()
    limiter.reset()


@pytest.fixture()
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class Account:
    def __init__(self, client: TestClient, email: str, password: str = "Passw0rd!x", name: str = "Test User") -> None:
        response = client.post(
            "/api/v1/auth/register", json={"email": email, "password": password, "full_name": name}
        )
        assert response.status_code == 201, response.text
        body = response.json()
        self.id: int = body["user"]["id"]
        self.email = email
        self.password = password
        self.token: str = body["access_token"]
        self.refresh: str = body["refresh_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}


@pytest.fixture()
def alice(client: TestClient) -> Account:
    return Account(client, "alice@example.com", name="Alice Walker")


@pytest.fixture()
def bob(client: TestClient) -> Account:
    return Account(client, "bob@example.com", name="Bob Stone")


@pytest.fixture()
def make_account(client: TestClient):  # noqa: ANN201
    counter = {"n": 0}

    def factory(role: Role = Role.user, db: Session | None = None) -> Account:
        counter["n"] += 1
        account = Account(client, f"user{counter['n']}@example.com", name=f"User Number{counter['n']}")
        if role != Role.user:
            assert db is not None
            user = db.get(User, account.id)
            assert user is not None
            user.role = role.value
            db.commit()
        return account

    return factory


@pytest.fixture()
def moderator(make_account, db: Session) -> Account:  # noqa: ANN001
    return make_account(Role.moderator, db)


@pytest.fixture(scope="session")
def regular_jpeg() -> bytes:
    return to_jpeg(regular_spot())


@pytest.fixture(scope="session")
def irregular_jpeg() -> bytes:
    return to_jpeg(irregular_spot())


def upload(client: TestClient, account: Account, data: bytes, **form: str) -> dict:
    response = client.post(
        "/api/v1/scans/",
        headers=account.headers,
        files={"image": ("spot.jpg", data, "image/jpeg")},
        data=form,
    )
    assert response.status_code == 201, response.text
    return response.json()
