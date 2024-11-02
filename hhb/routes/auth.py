from os import urandom
from time import time

import bcrypt
from fastapi import APIRouter
from starlette.responses import Response, JSONResponse

from .. import config
from ..dependencies import CaptchaDep
from ..models import User, Session
from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, ResetPasswordRequest, \
    RealResetPasswordRequest, MfaVerifyRequest
from ..utils import JWT
from ..utils.jwt import JWTPurpose
from ..utils.mfa import Mfa
from ..utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=RegisterResponse, dependencies=[CaptchaDep])
async def register(data: RegisterRequest):
    if await User.filter(email=data.email).exists():
        raise MultipleErrorsException("User with this email already registered!")

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
        "token": session.to_jwt(),
        "expires_at": int(time() + config.AUTH_JWT_TTL),
    }


@router.post("/login", response_model=LoginResponse, dependencies=[CaptchaDep])
async def login(data: LoginRequest):
    if (user := await User.get_or_none(email=data.email)) is None:
        raise MultipleErrorsException("User with this credentials is not found!")

    if not user.check_password(data.password):
        raise MultipleErrorsException("User with this credentials is not found!")

    session = await Session.create(user=user)
    if user.mfa_key is not None:
        return JSONResponse({
            "mfa_token": JWT.encode({
                "s": session.id,
                "u": user.id,
                "n": session.nonce[:4],
            }, config.JWT_KEY, expires_in=30 * 60, purpose=JWTPurpose.MFA),
            "expires_at": int(time() + 30 * 60),
        }, 400)

    return {
        "token": session.to_jwt(),
        "expires_at": int(time() + config.AUTH_JWT_TTL),
    }


@router.post("/login/mfa", response_model=LoginResponse)
async def verify_mfa_login(data: MfaVerifyRequest):
    if (payload := JWT.decode(data.mfa_token, config.JWT_KEY, JWTPurpose.MFA)) is None:
        raise MultipleErrorsException("Invalid mfa token!")

    session = await Session.get_or_none(
        id=payload["s"], user__id=payload["u"], nonce__startswith=payload["n"]
    ).select_related("user")
    if session is None:
        raise MultipleErrorsException("Invalid mfa token!")

    if session.user.mfa_key is not None and data.mfa_code not in Mfa.get_codes(session.user.mfa_key):
        raise MultipleErrorsException("Invalid code.")

    session.nonce = urandom(8).hex()
    await session.save(update_fields=["nonce"])
    return {
        "token": session.to_jwt(),
        "expires_at": int(time() + config.AUTH_JWT_TTL),
    }


@router.post("/reset-password/request", status_code=204, dependencies=[CaptchaDep])
async def request_reset_password(data: ResetPasswordRequest):
    if (user := await User.get_or_none(email=data.email)) is None:
        raise MultipleErrorsException("User with this email not found!")

    # TODO: send via email
    reset_token = JWT.encode({"u": user.id}, config.JWT_KEY, expires_in=60 * 30, purpose=JWTPurpose.PASSWORD_RESET)
    if config.IS_DEBUG:
        return Response("", 204, {"x-debug-token": reset_token})


@router.post("/reset-password/reset", status_code=204)
async def reset_password(data: RealResetPasswordRequest):
    if (payload := JWT.decode(data.reset_token, config.JWT_KEY, purpose=JWTPurpose.PASSWORD_RESET)) is None:
        raise MultipleErrorsException("Password reset request is invalid!")
    if (user := await User.get_or_none(id=payload["u"])) is None:
        raise MultipleErrorsException("User not found!")

    user.password = bcrypt.hashpw(data.new_password.encode("utf8"), bcrypt.gensalt(config.BCRYPT_ROUNDS)).decode("utf8")
    await user.save(update_fields=["password"])
