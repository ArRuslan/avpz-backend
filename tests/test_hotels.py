from time import time

import pytest
from httpx import AsyncClient

from PROJECT.models import User, Session, UserRole


@pytest.mark.asyncio
async def test_create_hotel_insufficient_privileges(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
    })
    assert response.status_code == 200, response.json()
    assert response.json().keys() == {"token"}
    token = response.json()["token"]

    response = await client.post("/hotels", headers={"authorization": token}, json={
        "name": "test",
        "address": "test address",
    })
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_create_hotel(client: AsyncClient):
    user = await User.create(
        email=f"test{time()}@gmail.com", password="", first_name="", last_name="", role=UserRole.STAFF_MANAGE,
    )
    session = await Session.create(user=user)
    token = session.to_jwt()

    response = await client.get("/hotels", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 0

    response = await client.post("/hotels", headers={"authorization": token}, json={
        "name": "test",
        "address": "test address",
    })
    assert response.status_code == 200, response.json()
    hotel_resp = response.json()
    assert hotel_resp["name"] == "test"
    assert hotel_resp["address"] == "test address"
    assert hotel_resp["description"] is None

    response = await client.get("/hotels", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 1
    assert response.json() == [hotel_resp]
