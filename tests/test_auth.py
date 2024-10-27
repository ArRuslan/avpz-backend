from time import time

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from hhb.models import User
from tests.conftest import recaptcha_mock_callback


@pytest_asyncio.fixture(autouse=True)
async def recaptcha_mock(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_callback(recaptcha_mock_callback, url="https://www.google.com/recaptcha/api/siteverify")
    yield


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token", "expires_at"}


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@pytest.mark.asyncio
async def test_register_already_registered(client: AsyncClient):
    email = f"test{time()}@gmail.com"
    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()

    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 422, response.json()


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    email = f"test{time()}@gmail.com"
    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()

    response = await client.post("/auth/login", json={
        "email": email,
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    email = f"test{time()}@gmail.com"
    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()

    response = await client.post("/auth/login", json={
        "email": email,
        "password": "123456789qwe",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "email": f"test{time()}",
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 422, response.json()


@pytest.mark.asyncio
async def test_login_unregistered_email(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient):
    email = f"test{time()}@gmail.com"
    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()

    response = await client.post("/auth/reset-password/request", json={
        "email": email,
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 204, response.json()
    reset_token = response.headers["x-debug-token"]

    response = await client.post("/auth/reset-password/reset", json={
        "reset_token": reset_token,
        "new_password": "987654321",
    })
    assert response.status_code == 204, response.json()

    response = await client.post("/auth/login", json={
        "email": email,
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()

    response = await client.post("/auth/login", json={
        "email": email,
        "password": "987654321",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_reset_password_no_email(client: AsyncClient):
    response = await client.post("/auth/reset-password/request", json={
        "email": "doesnotexistindb@gmail.com",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    response = await client.post("/auth/reset-password/reset", json={
        "reset_token": "123.456.789",
        "new_password": "987654321",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@pytest.mark.asyncio
async def test_reset_password_no_user(client: AsyncClient):
    email = f"test{time()}@gmail.com"
    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()

    response = await client.post("/auth/reset-password/request", json={
        "email": email,
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 204, response.json()
    reset_token = response.headers["x-debug-token"]

    await User.filter(email=email).delete()

    response = await client.post("/auth/reset-password/reset", json={
        "reset_token": reset_token,
        "new_password": "987654321",
    })
    assert response.status_code == 400, response.json()
