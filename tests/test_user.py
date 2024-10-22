from time import time

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from hhb.models import User, Session
from hhb.utils.mfa import Mfa
from tests.conftest import PWD_HASH_123456789, recaptcha_mock_callback


@pytest.mark.asyncio
async def test_get_user_info_invalid_token(client: AsyncClient):
    response = await client.get("/user/info", headers={"authorization": "asdqwe"})
    assert response.status_code == 401, response.json()

    response = await client.get("/user/info", headers={"authorization": "as.dq.we"})
    assert response.status_code == 401, response.json()


@pytest.mark.asyncio
async def test_get_user_info(client: AsyncClient, httpx_mock: HTTPXMock):
    httpx_mock.add_callback(recaptcha_mock_callback, url="https://www.google.com/recaptcha/api/siteverify")
    email = f"test{time()}@gmail.com"

    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token"}
    token = response.json()["token"]

    response = await client.get("/user/info", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["email"] == email
    assert response.json()["first_name"] == "first"
    assert response.json()["last_name"] == "last"
    assert response.json()["phone_number"] is None
    assert response.json()["role"] == 0
    assert not response.json()["mfa_enabled"]


@pytest.mark.asyncio
async def test_edit_user_info(client: AsyncClient, httpx_mock: HTTPXMock):
    httpx_mock.add_callback(recaptcha_mock_callback, url="https://www.google.com/recaptcha/api/siteverify")
    email = f"test{time()}@gmail.com"

    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-pass-test-key",
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token"}
    token = response.json()["token"]

    response = await client.patch("/user/info", headers={"authorization": token}, json={
        "first_name": "first1",
        "last_name": "last1",
        "phone_number": "+380999999999",
    })
    assert response.status_code == 200, response.json()
    assert response.json()["email"] == email
    assert response.json()["first_name"] == "first1"
    assert response.json()["last_name"] == "last1"
    assert response.json()["phone_number"] == "+380999999999"
    assert response.json()["role"] == 0
    assert not response.json()["mfa_enabled"]

    response = await client.patch("/user/info", headers={"authorization": token}, json={
        "phone_number": "",
    })
    assert response.status_code == 200, response.json()
    assert response.json()["email"] == email
    assert response.json()["first_name"] == "first1"
    assert response.json()["last_name"] == "last1"
    assert response.json()["phone_number"] is None
    assert response.json()["role"] == 0
    assert not response.json()["mfa_enabled"]


@pytest.mark.asyncio
async def test_user_enable_mfa(client: AsyncClient):
    mfa_key = "A"*16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789, first_name="first", last_name="last"
    )
    token = (await Session.create(user=user)).to_jwt()

    response = await client.post("/user/mfa/enable", headers={"authorization": token}, json={
        "password": "123456789",
        "key": mfa_key,
        "code": Mfa.get_code(mfa_key),
    })
    assert response.status_code == 200, response.json()
    assert response.json()["mfa_enabled"]


@pytest.mark.asyncio
async def test_user_disable_mfa(client: AsyncClient):
    mfa_key = "A"*16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789,
        first_name="first", last_name="last", mfa_key=mfa_key,
    )
    token = (await Session.create(user=user)).to_jwt()

    response = await client.post("/user/mfa/disable", headers={"authorization": token}, json={
        "password": "123456789",
        "code": Mfa.get_code(mfa_key),
    })
    assert response.status_code == 200, response.json()
    assert not response.json()["mfa_enabled"]


@pytest.mark.asyncio
async def test_user_enable_mfa_errors(client: AsyncClient):
    mfa_key = "A"*16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789, first_name="first", last_name="last"
    )
    token = (await Session.create(user=user)).to_jwt()

    response = await client.post("/user/mfa/enable", headers={"authorization": token}, json={
        "password": "123456789",
        "key": mfa_key,
        "code": str(int(Mfa.get_code(mfa_key)) + 1).zfill(6)[-6:],
    })
    assert response.status_code == 400, response.json()  # Wrong code

    response = await client.post("/user/mfa/enable", headers={"authorization": token}, json={
        "password": "123456789",
        "key": mfa_key+"B",
        "code": "000000",
    })
    assert response.status_code == 422, response.json()  # Invalid key

    response = await client.post("/user/mfa/enable", headers={"authorization": token}, json={
        "password": "wrong_password",
        "key": mfa_key,
        "code": Mfa.get_code(mfa_key),
    })
    assert response.status_code == 400, response.json()  # Wrong password

    user.mfa_key = mfa_key
    await user.save()

    response = await client.post("/user/mfa/enable", headers={"authorization": token}, json={
        "password": "123456789",
        "key": mfa_key,
        "code": Mfa.get_code(mfa_key),
    })
    assert response.status_code == 400, response.json()  # Already enabled


@pytest.mark.asyncio
async def test_user_disable_mfa_errors(client: AsyncClient):
    mfa_key = "A"*16
    user = await User.create(
        email=f"test{time()}@gmail.com", password=PWD_HASH_123456789,
        first_name="first", last_name="last", mfa_key=mfa_key,
    )
    token = (await Session.create(user=user)).to_jwt()

    response = await client.post("/user/mfa/disable", headers={"authorization": token}, json={
        "password": "wrong_password",
        "code": Mfa.get_code(mfa_key),
    })
    assert response.status_code == 400, response.json()  # Wrong password

    response = await client.post("/user/mfa/disable", headers={"authorization": token}, json={
        "password": "wrong_password",
        "code": str(int(Mfa.get_code(mfa_key)) + 1).zfill(6)[-6:],
    })
    assert response.status_code == 400, response.json()  # Wrong code

    user.mfa_key = None
    await user.save()

    response = await client.post("/user/mfa/disable", headers={"authorization": token}, json={
        "password": "123456789",
        "code": Mfa.get_code(mfa_key),
    })
    assert response.status_code == 400, response.json()  # Not enabled

