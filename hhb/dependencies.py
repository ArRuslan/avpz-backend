import warnings
from typing import Annotated

from fastapi import HTTPException, Body
from fastapi.params import Header, Depends
from httpx import AsyncClient

from . import config
from .models import UserRole, Session, User, Hotel
from .schemas.common import CaptchaExpectedRequest


class JWTAuthSession:
    async def __call__(
            self,
            authorization: str | None = Header(default=None),
            x_token: str | None = Header(
                default=None, description=(
                        "Use this as authorization header here. "
                        "Do not use it in real application! "
                        "It exists ONLY because openapi is not allowing to use authorization header in web docs."
                )
            ),
    ) -> Session:
        authorization = authorization or x_token
        if not authorization or (session := await Session.from_jwt(authorization)) is None:
            raise HTTPException(401, "Invalid session.")

        return session


class JWTAuthUser:
    def __init__(self, min_role: UserRole):
        self._min_role = min_role

    async def __call__(self, session: Session = Depends(JWTAuthSession())) -> User:
        if session.user.role < self._min_role:
            raise HTTPException(403, "Insufficient privileges.")

        return session.user


JwtAuthUserDep = Annotated[User, Depends(JWTAuthUser(UserRole.USER))]
JwtAuthStaffRoDepN = Depends(JWTAuthUser(UserRole.STAFF_VIEWONLY))
JwtAuthStaffRoDep = Annotated[User, JwtAuthStaffRoDepN]
JwtAuthStaffRwDepN = Depends(JWTAuthUser(UserRole.STAFF_MANAGE))
JwtAuthStaffRwDep = Annotated[User, JwtAuthStaffRwDepN]


async def hotel_dep(hotel_id: int) -> Hotel:
    if (hotel := await Hotel.get_or_none(id=hotel_id)) is None:
        raise HTTPException(404, "Unknown hotel.")

    return hotel


HotelDep = Annotated[Hotel, Depends(hotel_dep)]


async def captcha_dep(data: CaptchaExpectedRequest) -> None:
    if config.RECAPTCHA_SECRET is None:  # pragma: no cover
        warnings.warn("RECAPTCHA_SECRET is not set, verification is skipped!")
        return

    if not data.captcha_key:
        raise HTTPException(400, "Wrong captcha data.")

    async with AsyncClient() as client:
        resp = await client.post("https://www.google.com/recaptcha/api/siteverify", data={
            "secret": config.RECAPTCHA_SECRET, "response": data.captcha_key
        })
        if not resp.json()["success"]:
            raise HTTPException(400, "Wrong captcha data.")


CaptchaDep = Depends(captcha_dep)
