import codecs
import csv
from typing import Literal

from fastapi import APIRouter, UploadFile, Depends

from app.exceptions import CannotProcessCSV, CannotAddDataToDatabase
from app.importer.utils import TABLE_MODEL_MAP, convert_csv_to_postgres_format
from app.users.dependencies import get_current_user

router = APIRouter(
    prefix='/importer',
    tags=['Importer']
)


@router.post('/{table_name}', status_code=201, dependencies=[Depends(get_current_user)],)
async def get_free_hotels(table_name: Literal["hotels", "rooms", "bookings"], file: UploadFile):
    ModelDAO = TABLE_MODEL_MAP[table_name]
    # Внутри переменной file хранятся атрибуты:
    # file - сам файл, filename - название файла, size - размер файла.
    csvReader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'), delimiter=";")
    data = convert_csv_to_postgres_format(csvReader)
    file.file.close()
    if not data:
        raise CannotProcessCSV
    added_data = await ModelDAO.add_bulk(data)
    if not added_data:
        raise CannotAddDataToDatabase