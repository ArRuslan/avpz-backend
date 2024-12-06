from fastapi import APIRouter, Query
from tortoise.expressions import Subquery, Q

from ..dependencies import RoomDep
from ..models import Room, Booking
from ..schemas.common import PaginationResponse
from ..schemas.rooms import RoomResponse, SearchRoomsQuery

router = APIRouter(prefix="/rooms")


@router.get("", response_model=PaginationResponse[RoomResponse])
async def search_rooms(query: SearchRoomsQuery = Query()):
    query.page -= 1

    db_query_params = query.model_dump(exclude_defaults=True, exclude={"page", "page_size"})
    if "hotel_id" in db_query_params:
        db_query_params["hotel__id"] = db_query_params["hotel_id"]
        del db_query_params["hotel_id"]
    if "price_min" in db_query_params:
        db_query_params["price__gte"] = db_query_params["price_min"]
        del db_query_params["price_min"]
    if "price_max" in db_query_params:
        db_query_params["price__lte"] = db_query_params["price_max"]
        del db_query_params["price_max"]
    if "check_in" in db_query_params and "check_out" in db_query_params:
        check_in = db_query_params.pop("check_in")
        check_out = db_query_params.pop("check_out")
        if check_in > check_out:  # pragma: no cover
            check_in, check_out = check_out, check_in

        db_query_params["id__not_in"] = Subquery(
            Booking.filter(Q(check_in__lte=check_out) & Q(check_out__gte=check_in))\
                .select_related("room").values_list("room__id", flat=True)
        )
    elif "check_in" in db_query_params or "check_out" in db_query_params:
        db_query_params.pop("check_in", None)
        db_query_params.pop("check_out", None)

    db_query = Room.filter(**db_query_params)
    count = await db_query.count()
    rooms = await db_query.order_by("id").select_related("hotel")\
        .offset(query.page * query.page_size).limit(query.page_size)

    return {
        "count": count,
        "result": [
            await room.to_json()
            for room in rooms
        ],
    }


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room: RoomDep):
    return await room.to_json()
