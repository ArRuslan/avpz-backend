from fastapi import APIRouter

from ..dependencies import JwtAuthUserDep
from ..schemas.user import UserInfoResponse, UserInfoEditRequest

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
        "mfa_enabled": False,
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
        "mfa_enabled": False,
    }
