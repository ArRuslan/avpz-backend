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
async def test_hotel_rooms_get_wrong_hotel(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    hotel2 = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel2, user=user)

    response = await client.get(f"/admin/hotels/{hotel.id}/rooms", headers={"authorization": token})
    assert response.status_code == 403, response.json()


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
async def test_hotel_room_create_wrong_hotel(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    hotel2 = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel2, user=user)

    response = await client.post(f"/admin/hotels/{hotel.id}/rooms", headers={"authorization": token}, json={
        "type": "test23",
        "price": 123456,
    })
    assert response.status_code == 403, response.json()


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
async def test_hotel_room_edit_wrong_hotel(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)
    hotel2 = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel2, user=user)

    response = await client.patch(f"/admin/rooms/{room.id}", headers={"authorization": token}, json={
        "type": "test23",
        "price": 123456,
    })
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_hotel_room_delete(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.delete(f"/admin/rooms/{room.id}", headers={"authorization": token})
    assert response.status_code == 204

    assert not await Room.exists(id=room.id)


@pytest.mark.asyncio
async def test_hotel_room_delete_wrong_hotel(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)
    hotel2 = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel2, user=user)

    response = await client.delete(f"/admin/rooms/{room.id}", headers={"authorization": token})
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_hotel_room_get(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.get(f"/admin/rooms/{room.id}", headers={"authorization": token})
    assert response.status_code == 200
    assert response.json() == await room.to_json()


@pytest.mark.asyncio
async def test_hotel_room_get_wrong_hotel(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)
    hotel2 = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel2, user=user)

    response = await client.get(f"/admin/rooms/{room.id}", headers={"authorization": token})
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_hotel_room_get_nonexistent(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)

    response = await client.get(f"/admin/rooms/123123123", headers={"authorization": token})
    assert response.status_code == 404, response.json()

