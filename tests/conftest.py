from time import time

import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from PROJECT import config

config.BCRYPT_ROUNDS = 4
config.DB_CONNECTION_STRING = "sqlite://:memory:"

from PROJECT.main import app
from PROJECT.models import Session, User, UserRole


@pytest_asyncio.fixture
async def app_with_lifespan() -> FastAPI:
    async with LifespanManager(app) as manager:
        yield manager.app


@pytest_asyncio.fixture
async def client(app_with_lifespan) -> AsyncClient:
    async with AsyncClient(app=app_with_lifespan, base_url="https://hhb.test") as client:
        yield client


async def create_user(role: UserRole = UserRole.USER) -> User:
    user = await User.create(
        email=f"test{time()}@gmail.com", password="", first_name="first", last_name="last", role=role,
    )
    return user


async def create_token(user_role: UserRole = UserRole.USER) -> str:
    session = await Session.create(user=await create_user(user_role))
    return session.to_jwt()
