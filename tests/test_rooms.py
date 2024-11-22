import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel, Room
from tests.conftest import create_token


@pytest.mark.asyncio
async def test_get_room(client: AsyncClient):
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(type="test", hotel=hotel, price=123)

    response = await client.get(f"/rooms/{room.id}")
    assert response.status_code == 200, response.json()
    hotel_resp = response.json()
    assert hotel_resp["type"] == "test"
    assert hotel_resp["hotel_id"] == hotel.id
    assert hotel_resp["price"] == 123

    response = await client.get(f"/rooms/{room.id+100}")
    assert response.status_code == 404, response.json()


@pytest.mark.asyncio
async def test_search_rooms(client: AsyncClient):
    hotel1 = await Hotel.create(name="1", address="test address")
    hotel2 = await Hotel.create(name="2", address="test address")
    await Room.bulk_create([
        Room(type="test", hotel=hotel1, price=100),
        Room(type="test1", hotel=hotel1, price=200),
        Room(type="test123", hotel=hotel1, price=300),
        Room(type="qwe", hotel=hotel2, price=400),
    ])

    response = await client.get(f"/rooms", params={"type": "test"})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 1
    assert len(response.json()["result"]) == 1

    response = await client.get(f"/rooms", params={"type": "test1", "hotel_id": hotel2.id})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 0
    assert len(response.json()["result"]) == 0

    response = await client.get(f"/rooms", params={"type": "test1", "hotel_id": hotel1.id})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 1
    assert len(response.json()["result"]) == 1

    response = await client.get(f"/rooms", params={"hotel_id": hotel1.id})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 3
    assert len(response.json()["result"]) == 3

    response = await client.get(f"/rooms", params={"hotel_id": hotel2.id})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 1
    assert len(response.json()["result"]) == 1

    response = await client.get(f"/rooms", params={"price_min": 200})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 3
    assert len(response.json()["result"]) == 3
    assert set([room["price"] for room in response.json()["result"]]) == {200, 300, 400}

    response = await client.get(f"/rooms", params={"price_min": 150, "price_max": 300})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 2
    assert len(response.json()["result"]) == 2
    assert set([room["price"] for room in response.json()["result"]]) == {200, 300}
