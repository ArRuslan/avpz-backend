from time import time

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_info_invalid_token(client: AsyncClient):
    response = await client.get("/user/info", headers={"authorization": "asdqwe"})
    assert response.status_code == 401, response.json()

    response = await client.get("/user/info", headers={"authorization": "as.dq.we"})
    assert response.status_code == 401, response.json()


@pytest.mark.asyncio
async def test_get_user_info(client: AsyncClient):
    email = f"test{time()}@gmail.com"

    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
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
async def test_edit_user_info(client: AsyncClient):
    email = f"test{time()}@gmail.com"

    response = await client.post("/auth/register", json={
        "email": email,
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
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
