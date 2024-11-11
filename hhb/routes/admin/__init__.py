from fastapi import APIRouter

from . import hotels

router = APIRouter(prefix="/admin")
router.include_router(hotels.router)
