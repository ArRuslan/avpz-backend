from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Header, Depends

from PROJECT.models import UserRole, Session, User


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
