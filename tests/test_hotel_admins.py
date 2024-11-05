import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel
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
    token = await create_token(UserRole.ROOM_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/admin/{hotel.id}", headers={"authorization": token})
    assert response.status_code == 403, response.json()


@pytest.mark.asyncio
async def test_hotel_get_admins_no_permissions(client: AsyncClient):
    token = await create_token(UserRole.ROOM_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")

    response = await client.get(f"/hotels/admin/{hotel.id}/admins", headers={"authorization": token})
    assert response.status_code == 403, response.json()
