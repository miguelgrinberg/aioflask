import pytest

from flaskr import db
from flaskr.models import User
from flaskr.models import Post


@pytest.mark.asyncio
async def test_index(client, auth):
    response = await client.get("/")
    assert b"Log In" in response.data
    assert b"Register" in response.data

    await auth.login()
    response = await client.get("/")
    assert b"test title" in response.data
    assert b"by test on 2018-01-01" in response.data
    assert b"test\nbody" in response.data
    assert b'href="/1/update"' in response.data


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ("/create", "/1/update", "/1/delete"))
async def test_login_required(client, path):
    response = await client.post(path)
    assert response.headers["Location"].startswith(
        "http://localhost/auth/login?next=")


@pytest.mark.asyncio
async def test_author_required(app, client, auth):
    # change the post author to another user
    async with app.app_context():
        (await db.session.get(Post, 1)).author = await db.session.get(User, 2)
        await db.session.commit()

    await auth.login()
    # current user can't modify other user's post
    assert (await client.post("/1/update")).status_code == 403
    assert (await client.post("/1/delete")).status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/update"' not in (await client.get("/")).data


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ("/2/update", "/2/delete"))
async def test_exists_required(client, auth, path):
    await auth.login()
    assert (await client.post(path)).status_code == 404


@pytest.mark.asyncio
async def test_create(client, auth, app):
    await auth.login()
    assert (await client.get("/create")).status_code == 200
    await client.post("/create", data={"title": "created", "body": ""})

    async with app.app_context():
        query = db.select(db.func.count()).select_from(Post)
        assert (await db.session.execute(query)).scalar() == 2


@pytest.mark.asyncio
async def test_update(client, auth, app):
    await auth.login()
    assert (await client.get("/1/update")).status_code == 200
    await client.post("/1/update", data={"title": "updated", "body": ""})

    async with app.app_context():
        assert (await db.session.get(Post, 1)).title == "updated"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ("/create", "/1/update"))
async def test_create_update_validate(client, auth, path):
    await auth.login()
    response = await client.post(path, data={"title": "", "body": ""})
    assert b"Title is required." in response.data


@pytest.mark.asyncio
async def test_delete(client, auth, app):
    await auth.login()
    response = await client.post("/1/delete")
    assert response.headers["Location"] == "http://localhost/"

    async with app.app_context():
        assert (await db.session.get(Post, 1)) is None
