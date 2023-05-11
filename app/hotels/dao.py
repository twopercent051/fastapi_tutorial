from datetime import date

from app.dao.base import BaseDAO
from app.hotels.models import Hotels


class HotelDAO(BaseDAO):
    model = Hotels

    @classmethod
    async def find_free_by_location(cls, location: str, date_from: date, date_to: date):

