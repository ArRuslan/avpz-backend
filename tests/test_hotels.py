import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel
from tests.conftest import create_token


@pytest.mark.asyncio
async def test_create_hotel_insufficient_privileges(client: AsyncClient):
    token = await create_token(UserRole.USER)

    response = await client.post("/admin/hotels", headers={"authorization": token}, json={
        "name": "test",
        "address": "test address",
    })
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_create_hotel(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)

    response = await client.get("/hotels", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 0
    assert len(response.json()["result"]) == 0

    response = await client.post("/admin/hotels", headers={"authorization": token}, json={
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
    assert response.json()["count"] == 1
    assert len(response.json()["result"]) == 1
    assert response.json()["result"] == [hotel_resp]


@pytest.mark.asyncio
async def test_get_hotel(client: AsyncClient):
    token = await create_token(UserRole.ROOM_ADMIN)
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
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.patch(f"/admin/hotels/{hotel.id}", headers={"authorization": token}, json={
        "description": "desc",
        "name": "test123",
    })
    assert response.status_code == 200, response.json()
    hotel_resp = response.json()
    assert hotel_resp["name"] == "test123"
    assert hotel_resp["address"] == "test address"
    assert hotel_resp["description"] == "desc"


@pytest.mark.asyncio
async def test_search_hotels(client: AsyncClient):
    await Hotel.bulk_create([
        Hotel(name="test", address="test address"),
        Hotel(name="test1", address="test address"),
        Hotel(name="test123", address="test address"),
        Hotel(name="qwe", address="some address"),
    ])

    response = await client.get(f"/hotels", params={"name": "test"})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 3
    assert len(response.json()["result"]) == 3

    response = await client.get(f"/hotels", params={"name": "qwe"})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 1
    assert len(response.json()["result"]) == 1

    response = await client.get(f"/hotels", params={"address": "address"})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 4
    assert len(response.json()["result"]) == 4

