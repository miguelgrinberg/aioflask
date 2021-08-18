import pytest

from flaskr import db
from flaskr.models import User


@pytest.mark.asyncio
async def test_register(client, app):
    # test that viewing the page renders without template errors
    assert (await client.get("/auth/register")).status_code == 200

    # test that successful registration redirects to the login page
    response = await client.post("/auth/register",
                                 data={"username": "a", "password": "a"})
    assert "http://localhost/auth/login" == response.headers["Location"]

    # test that the user was inserted into the database
    async with app.app_context():
        query = db.select(User).filter_by(username="a")
        assert (await db.session.execute(query)).scalar() is not None


def test_user_password(app):
    user = User(username="a", password="a")
    assert user.password_hash != "a"
    assert user.check_password("a")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Username is required."),
        ("a", "", b"Password is required."),
        ("test", "test", b"already registered"),
    ),
)
async def test_register_validate_input(client, username, password, message):
    response = await client.post(
        "/auth/register", data={"username": username, "password": password}
    )
    assert message in response.data


@pytest.mark.asyncio
async def test_login(client, auth):
    # test that viewing the page renders without template errors
    assert (await client.get("/auth/login")).status_code == 200

    # test that successful login redirects to the index page
    response = await auth.login()
    assert response.headers["Location"] == "http://localhost/"

    # login request set the user_id in the session
    # check that the user is loaded from the session
    async with client:
        response = await client.get("/")
        assert b"<span>test</span>" in response.data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("username", "password", "message"),
    (("a", "test", b"Incorrect username."),
     ("test", "a", b"Incorrect password.")),
)
async def test_login_validate_input(auth, username, password, message):
    response = await auth.login(username, password)
    assert message in response.data


@pytest.mark.asyncio
async def test_logout(client, auth):
    await auth.login()

    async with client:
        await auth.logout()
        response = await client.get("/")
        assert b"Log In" in response.data
