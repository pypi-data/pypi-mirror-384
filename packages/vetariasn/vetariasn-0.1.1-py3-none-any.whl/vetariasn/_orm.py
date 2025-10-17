import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import hashlib
import os

__all__ = ["orm", "transient"]

def process_name(name: str):
    result = ""
    for n in name:
        if n in "QWERTUIOPASDFGHJKLZXCVBNM":
            if result != "":
                result += "_"
            result += n.lower()
        elif n in "qwertyuiopasdfghjklzxcvbnm1234567890_":
            result += n
        elif n == "_":
            if result != "":
                result += n
        else:
            return "veta_" + hashlib.md5(name.encode("utf-8")).hexdigest()
    if result == "":
        return "veta_" + hashlib.md5(name.encode("utf-8")).hexdigest()
    return result.replace("__", "_").replace("__", "_")

orm_engine = create_async_engine(os.environ.get("VETA_DB_URL", "sqlite+aiosqlite:///./sqlitedb.bin"))

class ORM:
    op = sa
    Session = async_sessionmaker(orm_engine)
    class Base(DeclarativeBase):
        type_annotation_map = {
            str: sa.String().with_variant(sa.String(255), "mysql", "mariadb"),
            int: sa.BigInteger(),
            bool: sa.Boolean(),
            float: sa.Float(),
            bytes: sa.BLOB()
        }
        # Convention over Configuration
        def __init_subclass__(cls, **kwargs):
            try:
                getattr(cls, "__tablename__")
            except Exception:
                cls.__tablename__ = process_name(cls.__name__)
            super().__init_subclass__(**kwargs)

orm = ORM()

transient_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

class Transient:
    op = sa
    Session = async_sessionmaker(transient_engine)
    class Base(DeclarativeBase):
        type_annotation_map = {
            str: sa.String().with_variant(sa.String(255), "mysql", "mariadb"),
            int: sa.BigInteger(),
            bool: sa.Boolean(),
            float: sa.Float(),
            bytes: sa.BLOB()
        }
        # Convention over Configuration
        def __init_subclass__(cls, **kwargs):
            try:
                getattr(cls, "__tablename__")
            except Exception:
                cls.__tablename__ = process_name(cls.__name__)
            super().__init_subclass__(**kwargs)

transient = Transient()

async def init_orm():
    async with orm_engine.begin() as conn:
        await conn.run_sync(orm.Base.metadata.create_all)

async def init_transient():
    async with transient_engine.begin() as conn:
        await conn.run_sync(transient.Base.metadata.create_all)