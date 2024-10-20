import bcrypt
from fastapi import APIRouter, HTTPException
from starlette.responses import Response

from .. import config
from ..models import User, Session
from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, ResetPasswordRequest, \
    RealResetPasswordRequest
from ..utils import JWT
from ..utils.jwt import JWTPurpose

router = APIRouter(prefix="/auth")


# TODO: add recaptcha
@router.post("/register", response_model=RegisterResponse)
async def register(data: RegisterRequest):
    if await User.filter(email=data.email).exists():
        raise HTTPException(400, "User with this email already registered!")

    password = bcrypt.hashpw(data.password.encode("utf8"), bcrypt.gensalt(config.BCRYPT_ROUNDS)).decode("utf8")
    user = await User.create(
        email=data.email,
        password=password,
        first_name=data.first_name,
        last_name=data.last_name,
        phone_number=data.phone_number,
    )
    if config.IS_DEBUG:
        user.role = data.role
        await user.save(update_fields=["role"])
    session = await Session.create(user=user)

    return {
        "token": session.to_jwt()
    }


# TODO: add recaptcha
@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    if (user := await User.get_or_none(email=data.email)) is None:
        raise HTTPException(400, "User with this credentials is not found!")

    if not user.check_password(data.password):
        raise HTTPException(400, "User with this credentials is not found!")

    session = await Session.create(user=user)
    return {
        "token": session.to_jwt()
    }


# TODO: add recaptcha
@router.post("/reset-password/request", status_code=204)
async def request_reset_password(data: ResetPasswordRequest):
    if (user := await User.get_or_none(email=data.email)) is None:
        raise HTTPException(400, "User with this email not found!")

    # TODO: send via email
    reset_token = JWT.encode({"u": user.id, "p": JWTPurpose.PASSWORD_RESET}, config.JWT_KEY, expires_in=60 * 30)
    if config.IS_DEBUG:
        return Response("", 204, {"x-debug-token": reset_token})


# TODO: add recaptcha
@router.post("/reset-password/reset", status_code=204)
async def reset_password(data: RealResetPasswordRequest):
    if (payload := JWT.decode(data.reset_token, config.JWT_KEY)) is None or payload["p"] != JWTPurpose.PASSWORD_RESET:
        raise HTTPException(400, "Password reset request is invalid!!")
    if (user := await User.get_or_none(id=payload["u"])) is None:
        raise HTTPException(400, "User not found!")

    user.password = bcrypt.hashpw(data.new_password.encode("utf8"), bcrypt.gensalt(config.BCRYPT_ROUNDS)).decode("utf8")
    await user.save(update_fields=["password"])
