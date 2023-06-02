from datetime import date

from sqlalchemy import select, and_, or_, func, insert

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker, engine
from app.hotels.rooms.models import Rooms


class BookingDAO(BaseDAO):
    model = Bookings

    @classmethod
    async def add(cls, user_id: int, room_id: int, date_from: date, date_to: date):
        """
        WITH booked_rooms AS (
            SELECT * FROM bookings
            WHERE room_id = 1 AND
            (date_from >= '2023-05-15' AND date_from <= '2023-06-20') OR
            (date_from <= '2023-05-15' AND date_to > '2023-06-20')
        )
        """
        async with async_session_maker() as session:

            booked_rooms = select(Bookings.__table__.columns).where(
                and_(
                    Bookings.room_id == room_id,
                    or_(
                        and_(
                            Bookings.date_from >= date_from,
                            Bookings.date_from <= date_to
                        ),
                        and_(
                            Bookings.date_from <= date_from,
                            Bookings.date_to > date_from
                        )
                    )
                )
            ).cte('booked_rooms')

            """
           SELECT rooms.quantity - COUNT(booked_rooms.room_id) FROM rooms
           LEFT JOIN booked_rooms ON booked_rooms.room_id = rooms.id
           WHERE rooms.id = 1
           GROUP BY rooms.quantity, booked_rooms.room_id;
           """
            get_rooms_left = select(
                Rooms.quantity - func.count(booked_rooms.c.room_id).label('rooms_left')
            ).select_from(Rooms).join(
                booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True
            ).where(Rooms.id == room_id).group_by(Rooms.quantity, booked_rooms.c.room_id)

            rooms_left = await session.execute(get_rooms_left)
            rooms_left: int = rooms_left.scalars().one_or_none()
            # print(get_rooms_left.compile(engine, compile_kwargs={"literal_binds": True}))

            if rooms_left > 0:
                get_price = select(Rooms.price).where(Rooms.id == room_id)
                price = await session.execute(get_price)
                price: int = price.scalars().one_or_none()
                add_bookings = insert(Bookings).values(
                    room_id=room_id,
                    user_id=user_id,
                    date_from=date_from,
                    date_to=date_to,
                    price=price
                ).returning(Bookings)

                new_booking = await session.execute(add_bookings)
                await session.commit()
                new_booking = new_booking.scalar()
                return new_booking
            else:
                return None
