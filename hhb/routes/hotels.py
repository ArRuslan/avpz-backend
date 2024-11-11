from fastapi import APIRouter

from ..dependencies import HotelDep
from ..models import Hotel
from ..schemas.hotels import HotelResponse

router = APIRouter(prefix="/hotels")


@router.get("", response_model=list[HotelResponse])
async def get_hotels(page: int = 1):
    page -= 1
    return [
        hotel.to_json()
        for hotel in await Hotel.all().order_by("id").limit(25).offset(25 * page)
    ]


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(hotel: HotelDep):
    return hotel.to_json()
