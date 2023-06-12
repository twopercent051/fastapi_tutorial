import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("room_id, date_from, date_to, status_code", [
    (3, "2023-07-01", "2023-07-10", 200),
    (3, "2023-07-01", "2023-07-30", 200),
    (3, "2023-07-01", "2023-08-12", 400),
    (3, "2023-07-01", "2023-06-12", 400),
    (3, "2023-07-01", "2023-02-12", 400),
])
async def test_add_wrong_date_booking(
        room_id,
        date_from,
        date_to,
        status_code,
        authenticated_ac: AsyncClient
):
    response = await authenticated_ac.post("/bookings", params={
        "room_id": room_id,
        "date_from": date_from,
        "date_to": date_to
    })

    assert response.status_code == status_code
