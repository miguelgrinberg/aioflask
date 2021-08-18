import asyncio
from datetime import datetime

import pytest

from flaskr import create_app
from flaskr import db
from flaskr import init_db
from flaskr.models import User
from flaskr.models import Post


@pytest.fixture
async def app():
    """Create and configure a new app instance for each test."""
    # create the app with common test config
    app = create_app({"TESTING": True,
                      "ALCHEMICAL_DATABASE_URL": "sqlite:///:memory:"})

    # create the database and load test data
    async with app.app_context():
        await init_db()
        user = User(username="test", password="test")
        db.session.add_all(
            (
                user,
                User(username="other", password="other"),
                Post(
                    title="test title",
                    body="test\nbody",
                    author=user,
                    created=datetime(2018, 1, 1),
                ),
            )
        )
        await db.session.commit()

    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions:
    def __init__(self, client):
        self._client = client

    async def login(self, username="test", password="test"):
        return await self._client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    async def logout(self):
        return await self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
