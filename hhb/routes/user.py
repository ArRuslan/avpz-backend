from fastapi import APIRouter

from ..dependencies import JwtAuthUserDep
from ..schemas.user import UserInfoResponse, UserInfoEditRequest, UserMfaEnableRequest, UserMfaDisableRequest
from ..utils.mfa import Mfa
from ..utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/user")


@router.get("/info", response_model=UserInfoResponse)
async def get_user_info(user: JwtAuthUserDep):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "mfa_enabled": user.mfa_key is not None,
    }


@router.patch("/info", response_model=UserInfoResponse)
async def edit_user_info(user: JwtAuthUserDep, data: UserInfoEditRequest):
    update_fields = data.model_dump(exclude_defaults=True)
    if not update_fields["phone_number"]:
        update_fields["phone_number"] = None

    if update_fields:
        user.update_from_dict(update_fields)
        await user.save(update_fields=list(update_fields.keys()))

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "mfa_enabled": user.mfa_key is not None,
    }


@router.post("/mfa/enable", response_model=UserInfoResponse)
async def enable_mfa(user: JwtAuthUserDep, data: UserMfaEnableRequest):
    if user.mfa_key is not None:
        raise MultipleErrorsException("Mfa already enabled.")
    if data.code not in Mfa.get_codes(data.key):
        raise MultipleErrorsException("Invalid code.")
    if not user.check_password(data.password):
        raise MultipleErrorsException("Wrong password!")

    user.mfa_key = data.key
    await user.save(update_fields=["mfa_key"])

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "mfa_enabled": user.mfa_key is not None,
    }


@router.post("/mfa/disable", response_model=UserInfoResponse)
async def disable_mfa(user: JwtAuthUserDep, data: UserMfaDisableRequest):
    if user.mfa_key is None:
        raise MultipleErrorsException("Mfa is not enabled.")
    if data.code not in Mfa.get_codes(user.mfa_key):
        raise MultipleErrorsException("Invalid code.")
    if not user.check_password(data.password):
        raise MultipleErrorsException("Wrong password!")

    user.mfa_key = None
    await user.save(update_fields=["mfa_key"])

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "mfa_enabled": user.mfa_key is not None,
    }
