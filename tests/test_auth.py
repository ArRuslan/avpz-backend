from time import time

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from hhb.models import User
from hhb.utils.mfa import Mfa
from tests.conftest import recaptcha_mock_callback, PWD_HASH_123456789


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
    assert response.status_code == 204, response.json()
    assert response.headers.get("x-debug-status", None) == "email_not_found"


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


@pytest.mark.asyncio
async def test_login_mfa(client: AsyncClient):
    mfa_key = "A" * 16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789,
        first_name="first", last_name="last", mfa_key=mfa_key,
    )

    response = await client.post("/auth/login", json={
        "email": user.email,
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()
    resp = response.json()
    assert "mfa_token" in resp

    response = await client.post("/auth/login/mfa", json={
        "mfa_code": Mfa.get_code(mfa_key),
        "mfa_token": resp["mfa_token"],
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token", "expires_at"}


@pytest.mark.asyncio
async def test_login_mfa_verify_twice_error(client: AsyncClient):
    mfa_key = "A" * 16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789,
        first_name="first", last_name="last", mfa_key=mfa_key,
    )

    response = await client.post("/auth/login", json={
        "email": user.email,
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()
    resp = response.json()
    assert "mfa_token" in resp

    response = await client.post("/auth/login/mfa", json={
        "mfa_code": Mfa.get_code(mfa_key),
        "mfa_token": resp["mfa_token"],
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token", "expires_at"}

    response = await client.post("/auth/login/mfa", json={
        "mfa_code": Mfa.get_code(mfa_key),
        "mfa_token": resp["mfa_token"],
    })
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_login_mfa_wrong_code(client: AsyncClient):
    mfa_key = "A" * 16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789,
        first_name="first", last_name="last", mfa_key=mfa_key,
    )

    response = await client.post("/auth/login", json={
        "email": user.email,
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()
    resp = response.json()
    assert "mfa_token" in resp

    response = await client.post("/auth/login/mfa", json={
        "mfa_code": str((int(Mfa.get_code(mfa_key)) + 1) % 1000000).zfill(6),
        "mfa_token": resp["mfa_token"],
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@pytest.mark.asyncio
async def test_login_mfa_invalid_token(client: AsyncClient):
    response = await client.post("/auth/login/mfa", json={
        "mfa_code": "111111",
        "mfa_token": "asd.qwe.123",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_login_mfa_disabled_before_verification(client: AsyncClient):
    mfa_key = "A" * 16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789,
        first_name="first", last_name="last", mfa_key=mfa_key,
    )

    response = await client.post("/auth/login", json={
        "email": user.email,
        "password": "123456789",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 400, response.json()
    resp = response.json()
    assert "mfa_token" in resp

    user.mfa_key = None
    await user.save(update_fields=["mfa_key"])

    response = await client.post("/auth/login/mfa", json={
        "mfa_code": str((int(Mfa.get_code(mfa_key)) + 1) % 1000000).zfill(6),
        "mfa_token": resp["mfa_token"],
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token", "expires_at"}

