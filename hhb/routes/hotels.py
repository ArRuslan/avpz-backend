from fastapi import APIRouter, Query

from ..dependencies import HotelDep
from ..models import Hotel
from ..schemas.common import PaginationResponse
from ..schemas.hotels import HotelResponse, SearchHotelsQuery

router = APIRouter(prefix="/hotels")


@router.get("", response_model=PaginationResponse[HotelResponse])
async def search_hotels(query: SearchHotelsQuery = Query()):
    """
    # !!! WARNING !!!
    # THIS ROUTE WAS CHANGED!
    # NOW IT RETURNS PROPER PAGINATED RESPONSE INSTEAD OF JUST ARRAY OF SOMETHING
    ## This warning will be here at least one more week (until 29.11.2024)
    # !!! WARNING !!!
    """

    query.page -= 1

    db_query_params = query.model_dump(exclude_defaults=True, exclude={"page", "page_size"})
    db_query_params = {f"{k}__icontains": v for k, v in db_query_params.items()}
    db_query = Hotel.filter(**db_query_params)
    count = await db_query.count()
    hotels = await db_query.order_by("id").offset(query.page * query.page_size).limit(query.page_size)

    return {
        "count": count,
        "result": [
            hotel.to_json()
            for hotel in hotels
        ],
    }


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(hotel: HotelDep):
    return hotel.to_json()
