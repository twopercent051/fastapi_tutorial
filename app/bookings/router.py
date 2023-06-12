from datetime import date, timedelta

from fastapi import APIRouter, Depends
from fastapi_versioning import version
from pydantic import parse_obj_as

from app.bookings.dao import BookingDAO
from app.bookings.schema import SBooking
from app.exceptions import BookingIncorrectDate, BookingTooLong, RoomCannotBeBooked
from app.tasks.tasks import send_booking_email
from app.users.dependencies import get_current_user
from app.users.models import Users

router = APIRouter(
    prefix='/bookings',
    tags=['Bookings']
)


@router.post('')
@version(2)
async def add_booking(room_id: int, date_from: date, date_to: date, user: Users = Depends(get_current_user)):
    booking = await BookingDAO.add(user.id, room_id, date_from, date_to)
    if date_to <= date_from:
        raise BookingIncorrectDate
    if date_from + timedelta(days=30) <= date_to:
        print(date_from + timedelta(days=30))
        raise BookingTooLong
    if booking:
        booking_as_dict = parse_obj_as(SBooking, booking).dict()
        send_booking_email.delay(booking_as_dict, user.email)
    else:
        raise RoomCannotBeBooked
    return booking


@router.get("")
@version(1)
async def get_bookings(user: Users = Depends(get_current_user)):
    return await BookingDAO.get_bookings_by_user(user_id=user.id)


@router.delete("/{booking_id}", status_code=204)
@version(1)
async def drop_booking(booking_id: int, user: Users = Depends(get_current_user)):
    return await BookingDAO.drop_by_id(booking_id=booking_id, user_id=user.id)

