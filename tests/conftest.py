import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from PROJECT import config

config.BCRYPT_ROUNDS = 4
config.DB_CONNECTION_STRING = "sqlite://:memory:"

from PROJECT.main import app


@pytest_asyncio.fixture
async def app_with_lifespan() -> FastAPI:
    async with LifespanManager(app) as manager:
        yield manager.app


@pytest_asyncio.fixture
async def client(app_with_lifespan) -> AsyncClient:
    async with AsyncClient(app=app_with_lifespan, base_url="https://hhb.test") as client:
        yield client
