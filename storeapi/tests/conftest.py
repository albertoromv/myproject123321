import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient  # additional import

# from storeapi.routers.post import comment_table, post_table
# not needed when using the database.py

os.environ["ENV_STATE"] = "test"

from storeapi.database import database, user_table  # noqa E402
from storeapi.main import app  # noqa E402
# we don't want the import to go upper
# app --> database.py --> config.py --> environment


@pytest.fixture(
    scope="session"
)  # only runs once in the whole session (for all the tests)
def anyio_backend():
    return "asyncio"  # using asyncio for running the async tests


# decorator to make it a fixture
@pytest.fixture()  # shared between the pytest functions
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(
    autouse=True
)  # used by every pytest function, they will understand the same db
async def db() -> AsyncGenerator:
    # post_table.clear()
    await database.connect()
    # comment_table.clear()
    yield database  # test function
    await database.disconnect()  # undo whatever the test did, roll_back


@pytest.fixture()
async def async_client(
    client,
    # instead of app = app, use this to avoid the DeprecationWarning:
) -> AsyncGenerator:  # client is the fixture! the function (dependency injection)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=client.base_url
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)

    if user:
        user_details["id"] = user.id  # debug from june

    return user_details


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, registered_user: dict) -> str:
    response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]
