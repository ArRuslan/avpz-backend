import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel
from tests.conftest import create_token


@pytest.mark.asyncio
async def test_create_hotel_insufficient_privileges(client: AsyncClient):
    token = await create_token(UserRole.USER)

    response = await client.post("/hotels", headers={"authorization": token}, json={
        "name": "test",
        "address": "test address",
    })
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_create_hotel(client: AsyncClient):
    token = await create_token(UserRole.STAFF_MANAGE)

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


@pytest.mark.asyncio
async def test_get_hotel(client: AsyncClient):
    token = await create_token(UserRole.STAFF_MANAGE)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/{hotel.id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    hotel_resp = response.json()
    assert hotel_resp["name"] == "test"
    assert hotel_resp["address"] == "test address"
    assert hotel_resp["description"] is None

    response = await client.get(f"/hotels/{hotel.id+100}", headers={"authorization": token})
    assert response.status_code == 404, response.json()


@pytest.mark.asyncio
async def test_edit_hotel(client: AsyncClient):
    token = await create_token(UserRole.STAFF_MANAGE)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.patch(f"/hotels/{hotel.id}", headers={"authorization": token}, json={
        "description": "desc",
        "name": "test123",
    })
    assert response.status_code == 200, response.json()
    hotel_resp = response.json()
    assert hotel_resp["name"] == "test123"
    assert hotel_resp["address"] == "test address"
    assert hotel_resp["description"] == "desc"
