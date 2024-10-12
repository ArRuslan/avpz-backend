from fastapi import APIRouter

from ..dependencies import JwtAuthStaffRoDepN, JwtAuthStaffRwDepN, HotelDep
from ..models import Hotel
from ..schemas.hotels import HotelResponse, HotelCreateRequest, HotelEditRequest

router = APIRouter(prefix="/hotels")


# TODO: change to JwtAuthUserDep?
@router.get("", response_model=list[HotelResponse], dependencies=[JwtAuthStaffRoDepN])
async def get_hotels(page: int = 1):
    page -= 1
    return [{
        "id": hotel.id,
        "name": hotel.name,
        "address": hotel.address,
        "description": hotel.description,
    } for hotel in await Hotel.all().order_by("id").limit(25).offset(25 * page)]


@router.post("", response_model=HotelResponse, dependencies=[JwtAuthStaffRwDepN])
async def create_hotel(data: HotelCreateRequest):
    hotel = await Hotel.create(**data.model_dump())

    return {
        "id": hotel.id,
        "name": hotel.name,
        "address": hotel.address,
        "description": hotel.description,
    }


# TODO: change to JwtAuthUserDep?
@router.get("/{hotel_id}", response_model=HotelResponse, dependencies=[JwtAuthStaffRoDepN])
async def get_hotel(hotel: HotelDep):
    return {
        "id": hotel.id,
        "name": hotel.name,
        "address": hotel.address,
        "description": hotel.description,
    }


@router.patch("/{hotel_id}", response_model=HotelResponse, dependencies=[JwtAuthStaffRwDepN])
async def edit_hotel(hotel: HotelDep, data: HotelEditRequest):
    update_fields = data.model_dump(exclude_defaults=True)

    if update_fields:
        await hotel.update_from_dict(update_fields)
        await hotel.save(update_fields=list(update_fields.keys()))

    return {
        "id": hotel.id,
        "name": hotel.name,
        "address": hotel.address,
        "description": hotel.description,
    }
