from fastapi import APIRouter
from pydantic import EmailStr

from hhb.dependencies import UserDep, JwtAuthGlobalDepN
from hhb.models import UserRole, User
from hhb.schemas.admin import UserListResponse
from hhb.schemas.user import UserInfoResponse
from hhb.utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/users")


@router.get("", response_model=UserListResponse, dependencies=[JwtAuthGlobalDepN])
async def get_users(role: UserRole | None = None, page: int = 1, page_size: int = 50):
    page -= 1
    if page < 0:
        page = 0
    if page_size < 5:
        page_size = 5
    if page_size > 100:
        page_size = 100

    query = User.filter(**({"role": role} if role is not None else {}))
    count = await query.count()
    users = await query.order_by("id").offset(page * page_size).limit(page_size)

    return {
        "count": count,
        "result": [
            user.to_json()
            for user in users
        ],
    }


@router.get("/search", response_model=UserInfoResponse, dependencies=[JwtAuthGlobalDepN])
async def get_user_by_email(email: EmailStr):
    if (user := await User.get_or_none(email=email)) is None:
        raise MultipleErrorsException("Unknown user.", 404)

    return user.to_json()


@router.get("/{user_id}", response_model=UserInfoResponse, dependencies=[JwtAuthGlobalDepN])
async def get_user(user: UserDep):
    return user.to_json()
