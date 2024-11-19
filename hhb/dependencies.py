import warnings
from typing import Annotated

from fastapi.params import Header, Depends
from httpx import AsyncClient

from . import config
from .models import UserRole, Session, User, Hotel, Room
from .schemas.common import CaptchaExpectedRequest
from .utils.multiple_errors_exception import MultipleErrorsException


class JWTAuthSession:
    async def __call__(
            self,
            authorization: str | None = Header(default=None),
            x_token: str | None = Header(
                default=None,
                description=(
                        "Use this as authorization header here. "
                        "Do not use it in real application! "
                        "It exists ONLY because openapi is not allowing to use authorization header in web docs."
                ),
            ),
    ) -> Session:
        authorization = authorization or x_token
        if not authorization or (session := await Session.from_jwt(authorization)) is None:
            raise MultipleErrorsException("Invalid session.", 401)

        return session


class JWTAuthUser:
    def __init__(self, min_role: UserRole):
        self._min_role = min_role

    async def __call__(self, session: Session = Depends(JWTAuthSession())) -> User:
        if session.user.role < self._min_role:
            raise MultipleErrorsException("Insufficient privileges.", 403)

        return session.user


JwtAuthUserDep = Annotated[User, Depends(JWTAuthUser(UserRole.USER))]
JwtAuthBookingDepN = Depends(JWTAuthUser(UserRole.BOOKING_ADMIN))
JwtAuthBookingDep = Annotated[User, JwtAuthBookingDepN]
JwtAuthRoomsDepN = Depends(JWTAuthUser(UserRole.ROOM_ADMIN))
JwtAuthRoomsDep = Annotated[User, JwtAuthRoomsDepN]
JwtAuthHotelDepN = Depends(JWTAuthUser(UserRole.HOTEL_ADMIN))
JwtAuthHotelDep = Annotated[User, JwtAuthHotelDepN]
JwtAuthGlobalDepN = Depends(JWTAuthUser(UserRole.GLOBAL_ADMIN))
JwtAuthGlobalDep = Annotated[User, JwtAuthGlobalDepN]


async def hotel_dep(hotel_id: int) -> Hotel:
    if (hotel := await Hotel.get_or_none(id=hotel_id)) is None:
        raise MultipleErrorsException("Unknown hotel.", 404)

    return hotel


HotelDep = Annotated[Hotel, Depends(hotel_dep)]


async def room_dep(room_id: int) -> Room:
    if (room := await Room.get_or_none(id=room_id).select_related("hotel")) is None:
        raise MultipleErrorsException("Unknown room.", 404)

    return room


RoomDep = Annotated[Room, Depends(room_dep)]


async def captcha_dep(data: CaptchaExpectedRequest) -> None:
    if config.RECAPTCHA_SECRET is None:  # pragma: no cover
        warnings.warn("RECAPTCHA_SECRET is not set, verification is skipped!")
        return

    if not data.captcha_key:
        raise MultipleErrorsException("Wrong captcha data.")

    async with AsyncClient() as client:
        resp = await client.post("https://www.google.com/recaptcha/api/siteverify", data={
            "secret": config.RECAPTCHA_SECRET, "response": data.captcha_key
        })
        if not resp.json()["success"]:
            raise MultipleErrorsException("Wrong captcha data.")


CaptchaDep = Depends(captcha_dep)


async def user_dep(user_id: int) -> User:
    if (user := await User.get_or_none(id=user_id)) is None:
        raise MultipleErrorsException("Unknown user.", 404)

    return user


UserDep = Annotated[User, Depends(user_dep)]
