import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel, HotelAdmin, Session, Room
from tests.conftest import create_token, create_user


@pytest.mark.asyncio
async def test_hotel_rooms_get(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/admin/hotels/{hotel.id}/rooms", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json() == []

    await Room.bulk_create([
        Room(hotel=hotel, type=f"test{i}", price=i)
        for i in range(10)
    ])

    response = await client.get(f"/admin/hotels/{hotel.id}/rooms", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert len(response.json()) == 10


@pytest.mark.asyncio
async def test_hotel_room_create(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.post(f"/admin/hotels/{hotel.id}/rooms", headers={"authorization": token}, json={
        "type": "test23",
        "price": 123456,
    })
    assert response.status_code == 200, response.json()
    j_resp = response.json()
    assert j_resp.items() >= {
        "type": "test23",
        "price": 123456,
        "available": True,
        "hotel_id": hotel.id,
    }.items()

    response = await client.get(f"/admin/hotels/{hotel.id}/rooms", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json() == [j_resp]


@pytest.mark.asyncio
async def test_hotel_room_edit(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.patch(f"/admin/rooms/{room.id}", headers={"authorization": token}, json={
        "type": "test23",
        "price": 123456,
    })
    assert response.status_code == 200, response.json()
    assert response.json() == (await room.to_json()) | {"type": "test23", "price": 123456}

    await room.refresh_from_db(fields=["type", "price"])
    assert room.type == "test23"
    assert room.price == 123456


@pytest.mark.asyncio
async def test_hotel_room_delete(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.delete(f"/admin/rooms/{room.id}", headers={"authorization": token})
    assert response.status_code == 204

    assert not await Room.exists(id=room.id)

