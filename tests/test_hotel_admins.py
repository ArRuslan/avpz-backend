import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel, HotelAdmin, Session
from tests.conftest import create_token, create_user


@pytest.mark.asyncio
async def test_hotel_get_for_admins(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/admin/{hotel.id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json() == hotel.to_json() | {"admins": []}


@pytest.mark.asyncio
async def test_hotel_get_admins(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json() == []


@pytest.mark.asyncio
async def test_hotel_get_for_admins_no_permissions(client: AsyncClient):
    token = await create_token(UserRole.HOTEL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/admin/{hotel.id}", headers={"authorization": token})
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_hotel_get_admins_no_permissions(client: AsyncClient):
    token = await create_token(UserRole.HOTEL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token})
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_hotel_add_admin_global_hotel(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    target_user = await create_user(UserRole.USER)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": target_user.id,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 200, response.json()
    await target_user.refresh_from_db(fields=["role"])
    assert response.json() == target_user.to_json()


@pytest.mark.asyncio
async def test_hotel_add_admin_nonexistent_user(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": 123123123,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 404, response.json()


@pytest.mark.asyncio
async def test_hotel_add_admin_hotel_booking(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    target_user = await create_user(UserRole.USER)
    hotel = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel, user=user)

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": target_user.id,
        "role": UserRole.BOOKING_ADMIN,
    })
    assert response.status_code == 200, response.json()
    await target_user.refresh_from_db(fields=["role"])
    assert response.json() == target_user.to_json()


@pytest.mark.asyncio
async def test_hotel_add_admin_same_role(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel, user=user)

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": user.id,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_hotel_add_global_admin(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    await HotelAdmin.create(hotel=hotel, user=user)

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": user.id,
        "role": UserRole.GLOBAL_ADMIN,
    })
    assert response.status_code == 422, response.json()


@pytest.mark.asyncio
async def test_hotel_add_admin_existing(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    target_user = await create_user(UserRole.USER)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": target_user.id,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 200, response.json()
    await target_user.refresh_from_db(fields=["role"])
    assert response.json() == target_user.to_json()

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": target_user.id,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 200, response.json()
    assert response.json() == target_user.to_json()


@pytest.mark.asyncio
async def test_hotel_add_admin_to_multiple_hotels(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    target_user = await create_user(UserRole.USER)
    hotel = await Hotel.create(name="test", address="test address")
    hotel2 = await Hotel.create(name="test2", address="test address")

    response = await client.post(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token}, json={
        "user_id": target_user.id,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 200, response.json()

    response = await client.post(f"/hotels/admin/{hotel2.id}/admins", headers={"authorization": token}, json={
        "user_id": target_user.id,
        "role": UserRole.HOTEL_ADMIN,
    })
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_hotel_add_admin_to_different_hotel(client: AsyncClient):
    user = await create_user(UserRole.HOTEL_ADMIN)
    token = (await Session.create(user=user)).to_jwt()
    hotel = await Hotel.create(name="test", address="test address")
    hotel2 = await Hotel.create(name="test2", address="test address")
    await HotelAdmin.create(hotel=hotel, user=user)

    response = await client.post(f"/hotels/admin/{hotel2.id}/admins", headers={"authorization": token}, json={
        "user_id": 123123123,
        "role": UserRole.BOOKING_ADMIN,
    })
    assert response.status_code == 403, response.json()
