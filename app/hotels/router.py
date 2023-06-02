from datetime import date

from fastapi import APIRouter

from app.hotels.dao import HotelDAO
from app.hotels.schema import SHotels

router = APIRouter(
    prefix='/hotels',
    tags=['Hotels']
)


@router.get('')
async def get_free_hotels(location: str, date_from: date, date_to: date):
    return await HotelDAO.find_free_by_location(location=location, date_from=date_from, date_to=date_to)


@router.get("id/{hotel_id}")
async def get_hotel(hotel_id: int) -> SHotels:
    return await HotelDAO.find_one_or_none(id=hotel_id)
