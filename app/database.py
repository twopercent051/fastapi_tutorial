from sqlalchemy import MetaData, NullPool, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import as_declarative, sessionmaker

from app.config import settings

if settings.MODE == "TEST":
    DATABASE_URL = settings.test_database_url
    DATABASE_PARAMS = {"poolclass": NullPool}
else:
    DATABASE_URL = settings.database_url
    DATABASE_PARAMS = {}

engine = create_async_engine(DATABASE_URL, **DATABASE_PARAMS)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@as_declarative()
class Base:
    metadata = MetaData()

    # def _asdict(self):
    #     return {c.key: getattr(self, c.key)
    #             for c in inspect(self).mapper.column_attrs}
