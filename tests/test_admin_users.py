import pytest
from httpx import AsyncClient

from hhb.models import UserRole, Hotel, HotelAdmin, Session, Room, User
from tests.conftest import create_token, create_user


@pytest.mark.asyncio
async def test_users_get(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    await User.bulk_create([
        User(
            email=f"test{i}@hhb.com",
            password="test",
            first_name="test",
            last_name="test",
        )
        for i in range(10)
    ])

    response = await client.get(f"/admin/users", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 11
    assert len(response.json()["result"]) == 11

    response = await client.get(f"/admin/users?page_size=5", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 11
    assert len(response.json()["result"]) == 5

    response = await client.get(f"/admin/users?role=0", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 10
    assert len(response.json()["result"]) == 10

    response = await client.get(f"/admin/users?page_size=1000", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 11
    assert len(response.json()["result"]) == 11

    response = await client.get(f"/admin/users?page_size=1", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 11
    assert len(response.json()["result"]) == 5

    response = await client.get(f"/admin/users?page=-1", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == 11
    assert len(response.json()["result"]) == 11


@pytest.mark.asyncio
async def test_user_get_by_email(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    user = await User.create(
        email=f"test@hhb.com",
        password="test",
        first_name="test",
        last_name="test",
    )

    response = await client.get(
        f"/admin/users/search", headers={"authorization": token}, params={"email": user.email},
    )
    assert response.status_code == 200, response.json()
    assert response.json() == user.to_json()

    response = await client.get(
        f"/admin/users/search", headers={"authorization": token}, params={"email": "1"+user.email},
    )
    assert response.status_code == 404, response.json()


@pytest.mark.asyncio
async def test_user_get_by_id(client: AsyncClient):
    token = await create_token(UserRole.GLOBAL_ADMIN)
    user = await User.create(
        email=f"test@hhb.com",
        password="test",
        first_name="test",
        last_name="test",
    )

    response = await client.get(f"/admin/users/{user.id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json() == user.to_json()

    response = await client.get(f"/admin/users/{user.id+100}", headers={"authorization": token})
    assert response.status_code == 404, response.json()
