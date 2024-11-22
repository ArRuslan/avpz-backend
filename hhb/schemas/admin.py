from hhb.models import UserRole
from hhb.schemas.common import PaginationQuery


class GetUsersQuery(PaginationQuery):
    role: UserRole | None = None


class GetHotelsQuery(PaginationQuery):
    ...
