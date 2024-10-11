import bcrypt
from fastapi import APIRouter, HTTPException

from .. import config
from ..models import User, Session
from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse

router = APIRouter(prefix="/auth")


# TODO: add recaptcha
@router.post("/register", response_model=RegisterResponse)
async def register(data: RegisterRequest):
    if await User.filter(email=data.email).exists():
        raise HTTPException(400, "User with this email already registered!")

    password = bcrypt.hashpw(data.password.encode("utf8"), bcrypt.gensalt(config.BCRYPT_ROUNDS)).decode("utf8")
    user = await User.create(email=data.email, password=password)
    session = await Session.create(user=user)

    return {
        "token": session.to_jwt()
    }


# TODO: add recaptcha
@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    if (user := await User.get_or_none(email=data.email)) is None:
        raise HTTPException(400, "User with this credentials is not found!")

    if not bcrypt.checkpw(data.password.encode("utf8"), user.password.encode("utf8")):
        raise HTTPException(400, "User with this credentials is not found!")

    session = await Session.create(user=user)
    return {
        "token": session.to_jwt()
    }
