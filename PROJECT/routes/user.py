from fastapi import APIRouter

from ..dependencies import JwtAuthUserDep
from ..schemas.user import UserInfoResponse

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
