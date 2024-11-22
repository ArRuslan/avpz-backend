from fastapi import APIRouter, Query
from pydantic import EmailStr

from hhb.dependencies import UserDep, JwtAuthGlobalDepN
from hhb.models import User
from hhb.schemas.admin import GetUsersQuery
from hhb.schemas.common import PaginationResponse
from hhb.schemas.user import UserInfoResponse
from hhb.utils.multiple_errors_exception import MultipleErrorsException

router = APIRouter(prefix="/users")


@router.get("", response_model=PaginationResponse[UserInfoResponse], dependencies=[JwtAuthGlobalDepN])
async def get_users(query: GetUsersQuery = Query()):
    query.page -= 1

    db_query = User.filter(**({"role": query.role} if query.role is not None else {}))
    count = await db_query.count()
    users = await db_query.order_by("id").offset(query.page * query.page_size).limit(query.page_size)

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
