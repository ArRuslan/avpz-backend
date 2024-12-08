import re
from datetime import date, timedelta
from time import time

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from hhb import config
from hhb.models import Hotel, Room, BookingStatus, Booking, UserRole
from hhb.schemas.bookings import BookingType
from hhb.utils.paypal import PayPal
from tests.conftest import create_token
from tests.paypal_mock import PaypalMockState


httpx_mock_decorator = pytest.mark.httpx_mock(
    assert_all_requests_were_expected=False,
    assert_all_responses_were_requested=False,
    can_send_already_matched_responses=True,
)

async def check_bookings_counts(
        client: AsyncClient, token: str, pending_count: int, active_count: int, cancelled_count: int,
        expired_count: int,
) -> None:
    total_count = pending_count + active_count + cancelled_count + expired_count
    queries = [
        (BookingType.PENDING, pending_count),
        (BookingType.ACTIVE, active_count),
        (BookingType.CANCELLED, cancelled_count),
        (BookingType.EXPIRED, expired_count),
        (BookingType.ALL, total_count),
    ]

    for typ, count in queries:
        response = await client.get(f"/bookings?type={typ.value}", headers={"authorization": token})
        assert response.status_code == 200, response.json()
        assert response.json()["count"] == count
        assert len(response.json()["result"]) == count


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_full_booking_process(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)
    httpx_mock.add_callback(mock_state.capture_callback, method="POST", url=re.compile(r".+/v2/checkout/orders/\d+\.\d+/capture"))
    httpx_mock.add_callback(mock_state.refund_callback, method="POST", url=re.compile(r".+/v2/payments/captures/\d+\.\d+/refund"))

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.PENDING
    booking_id = response.json()["id"]
    payment_id = response.json()["payment_id"]

    await check_bookings_counts(client, token, 1, 0, 0, 0)

    response = await client.get(f"/bookings/{booking_id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.PENDING

    response = await client.get(f"/bookings/{booking_id}/verification-token", headers={"authorization": token})
    assert response.status_code == 400, response.json()

    mock_state.mark_as_payed(payment_id)

    response = await client.get(f"/bookings/{booking_id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.CONFIRMED

    await check_bookings_counts(client, token, 0, 1, 0, 0)

    await Booking.filter(id=booking_id).update(check_in=date.today())
    response = await client.get(f"/bookings/{booking_id}/verification-token", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    await Booking.filter(id=booking_id).update(check_in=date.today() + timedelta(days=1))

    response = await client.post(f"/bookings/{booking_id}/cancel", headers={"authorization": token})
    assert response.status_code == 204, response.json()

    await check_bookings_counts(client, token, 0, 0, 1, 0)

    response = await client.get(f"/bookings/{booking_id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.CANCELLED


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_cancel_twice(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)
    httpx_mock.add_callback(mock_state.capture_callback, method="POST", url=re.compile(r".+/v2/checkout/orders/\d+\.\d+/capture"))
    httpx_mock.add_callback(mock_state.refund_callback, method="POST", url=re.compile(r".+/v2/payments/captures/\d+\.\d+/refund"))

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 200, response.json()
    booking_id = response.json()["id"]
    payment_id = response.json()["payment_id"]

    mock_state.mark_as_payed(payment_id)

    response = await client.get(f"/bookings/{booking_id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.CONFIRMED

    response = await client.post(f"/bookings/{booking_id}/cancel", headers={"authorization": token})
    assert response.status_code == 204, response.json()

    response = await client.post(f"/bookings/{booking_id}/cancel", headers={"authorization": token})
    assert response.status_code == 400, response.json()


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_cancel_pending(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)
    httpx_mock.add_callback(mock_state.capture_callback, method="POST", url=re.compile(r".+/v2/checkout/orders/\d+\.\d+/capture"))
    httpx_mock.add_callback(mock_state.refund_callback, method="POST", url=re.compile(r".+/v2/payments/captures/\d+\.\d+/refund"))

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 200, response.json()
    booking_id = response.json()["id"]

    response = await client.post(f"/bookings/{booking_id}/cancel", headers={"authorization": token})
    assert response.status_code == 400, response.json()


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_twice_for_one_date(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)
    httpx_mock.add_callback(mock_state.capture_callback, method="POST", url=re.compile(r".+/v2/checkout/orders/\d+\.\d+/capture"))
    httpx_mock.add_callback(mock_state.refund_callback, method="POST", url=re.compile(r".+/v2/payments/captures/\d+\.\d+/refund"))

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 200, response.json()

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=2)),
        },
    )
    assert response.status_code == 400, response.json()


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_verify_cancelled(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)
    httpx_mock.add_callback(mock_state.capture_callback, method="POST", url=re.compile(r".+/v2/checkout/orders/\d+\.\d+/capture"))
    httpx_mock.add_callback(mock_state.refund_callback, method="POST", url=re.compile(r".+/v2/payments/captures/\d+\.\d+/refund"))

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today()),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 200, response.json()
    booking_id = response.json()["id"]
    payment_id = response.json()["payment_id"]

    mock_state.mark_as_payed(payment_id)

    response = await client.get(f"/bookings/{booking_id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.CONFIRMED

    await Booking.filter(id=booking_id).update(status=BookingStatus.CANCELLED)

    response = await client.get(f"/bookings/{booking_id}/verification-token", headers={"authorization": token})
    assert response.status_code == 400, response.json()


@pytest.mark.asyncio
async def test_booking_invalid_dates(client: AsyncClient):
    token = await create_token()

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": 123123,
            "check_in": str(date.today() - timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 400, response.json()

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": 123123,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() - timedelta(days=7)),
        },
    )
    assert response.status_code == 400, response.json()

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": 123123,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=1)),
        },
    )
    assert response.status_code == 400, response.json()


@pytest.mark.skipif(not config.IS_DEBUG, reason="Not debug")
@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_past_dates_in_debug(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() - timedelta(days=7)),
            "check_out": str(date.today() - timedelta(days=1)),
        },
    )
    assert response.status_code == 400, response.json()

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() - timedelta(days=7)),
            "check_out": str(date.today() - timedelta(days=1)),
            "DEBUG_DISABLE_PAST_DATES_CHECK": "true",
        },
    )
    assert response.status_code == 200, response.json()


@pytest.mark.asyncio
async def test_booking_get_unknown(client: AsyncClient):
    token = await create_token()

    response = await client.get(f"/bookings/123456", headers={"authorization": token})
    assert response.status_code == 404, response.json()


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_room_available_field(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)

    token = await create_token()
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.get(f"/rooms/{room.id}")
    assert response.status_code == 200, response.json()
    assert response.json()["available"]

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() - timedelta(days=7)),
            "check_out": str(date.today() + timedelta(days=1)),
            "DEBUG_DISABLE_PAST_DATES_CHECK": "true",
        },
    )
    assert response.status_code == 200, response.json()

    response = await client.get(f"/rooms/{room.id}")
    assert response.status_code == 200, response.json()
    assert not response.json()["available"]


@httpx_mock_decorator
@pytest.mark.asyncio
async def test_booking_verification(client: AsyncClient, httpx_mock: HTTPXMock):
    mock_state = PaypalMockState()
    httpx_mock.add_callback(mock_state.auth_callback, method="POST", url=PayPal.AUTHORIZE)
    httpx_mock.add_callback(mock_state.order_callback, method="POST", url=PayPal.CHECKOUT)
    httpx_mock.add_callback(mock_state.capture_callback, method="POST", url=re.compile(r".+/v2/checkout/orders/\d+\.\d+/capture"))
    httpx_mock.add_callback(mock_state.refund_callback, method="POST", url=re.compile(r".+/v2/payments/captures/\d+\.\d+/refund"))

    token = await create_token()
    token_admin = await create_token(UserRole.GLOBAL_ADMIN)
    hotel = await Hotel.create(name="test", address="test address")
    room = await Room.create(hotel=hotel, type="test", price=123)

    response = await client.post(
        f"/bookings", headers={"authorization": token}, json={
            "room_id": room.id,
            "check_in": str(date.today() + timedelta(days=1)),
            "check_out": str(date.today() + timedelta(days=7)),
        },
    )
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.PENDING
    booking_id = response.json()["id"]
    payment_id = response.json()["payment_id"]
    mock_state.mark_as_payed(payment_id)

    response = await client.get(f"/bookings/{booking_id}", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    assert response.json()["payment_id"] is not None
    assert response.json()["status"] == BookingStatus.CONFIRMED

    await Booking.filter(id=booking_id).update(check_in=date.today())
    response = await client.get(f"/bookings/{booking_id}/verification-token", headers={"authorization": token})
    assert response.status_code == 200, response.json()
    ver_token = response.json()["token"]

    response = await client.get(f"/admin/bookings/verify?token={ver_token}", headers={"authorization": token_admin})
    assert response.status_code == 200, response.json()
    assert response.json()["id"] == booking_id
    assert response.json()["room"]["id"] == room.id

    response = await client.get(f"/admin/bookings/{booking_id}", headers={"authorization": token_admin})
    assert response.status_code == 200, response.json()
    assert response.json()["id"] == booking_id
    assert response.json()["room"]["id"] == room.id
