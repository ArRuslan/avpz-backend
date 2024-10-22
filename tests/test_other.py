from time import time

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from tests.conftest import recaptcha_mock_callback


@pytest_asyncio.fixture(autouse=True)
async def recaptcha_mock(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_callback(recaptcha_mock_callback, url="https://www.google.com/recaptcha/api/siteverify")
    yield


@pytest.mark.asyncio
async def test_captcha_fail_wrong_key(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "should-not-pass-test-key",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@pytest.mark.asyncio
async def test_captcha_fail_empty_key(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": "",
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@pytest.mark.asyncio
async def test_captcha_fail_none_key(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
        "captcha_key": None,
    })
    assert response.status_code == 400, response.json()


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@pytest.mark.asyncio
async def test_captcha_fail_no_key(client: AsyncClient):
    response = await client.post("/auth/register", json={
        "email": f"test{time()}@gmail.com",
        "password": "123456789",
        "first_name": "first",
        "last_name": "last",
    })
    assert response.status_code == 400, response.json()
