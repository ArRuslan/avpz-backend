from time import time

from httpx import AsyncClient

from .. import config


class PayPal:
    _access_token: str | None = None
    _access_token_expires_at: int = 0

    BASE = "https://api-m.sandbox.paypal.com"
    AUTHORIZE = f"{BASE}/v1/oauth2/token"
    CHECKOUT = f"{BASE}/v2/checkout/orders"
    CAPTURES = f"{BASE}/v2/payments/captures"

    @classmethod
    async def _get_access_token(cls) -> str:
        if cls._access_token is None or cls._access_token_expires_at < time():
            async with AsyncClient() as client:
                resp = await client.post(
                    cls.AUTHORIZE,
                    content="grant_type=client_credentials",
                    auth=(config.PAYPAL_ID, config.PAYPAL_SECRET),
                )
                j = resp.json()

                cls._access_token = j["access_token"]
                cls._access_token_expires_at = time() + j["expires_in"]

        return cls._access_token

    @classmethod
    async def create(cls, price: float, currency: str = "USD") -> str:
        async with AsyncClient() as client:
            resp = await client.post(
                cls.CHECKOUT, headers={"Authorization": f"Bearer {await cls._get_access_token()}"},
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [{
                        "amount": {
                            "currency_code": currency,
                            "value": f"{price:.2f}",
                        },
                    }],
                },
            )
            return resp.json()["id"]

    @classmethod
    async def capture(cls, order_id: str) -> str | None:
        async with AsyncClient() as client:
            resp = await client.post(
                f"{cls.CHECKOUT}/{order_id}/capture",
                headers={"Authorization": f"Bearer {await cls._get_access_token()}"},
                json={},
            )

            j_resp = resp.json()
            if resp.status_code >= 400 or j_resp["status"] != "COMPLETED":
                return

            try:
                return j_resp["purchase_units"][0]["payments"]["captures"][0]["id"]
            except (KeyError, IndexError):
                return

    @classmethod
    async def refund(cls, capture_id: str, amount: float, currency: str = "USD") -> bool:
        async with AsyncClient() as client:
            resp = await client.post(
                f"{cls.CAPTURES}/{capture_id}/refund",
                headers={"Authorization": f"Bearer {await cls._get_access_token()}"},
                json={
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}",
                    },
                },
            )

            return resp.status_code == 200 and resp.json()["status"] == "COMPLETED"