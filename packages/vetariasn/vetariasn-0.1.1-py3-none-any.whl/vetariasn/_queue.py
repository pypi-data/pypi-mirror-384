from ._orm import orm
from ._algo import algo
import sqlalchemy as sa
import typing
import time
import asyncio
from queue import Empty
import random

class QueueModel(orm.Base):
    __tablename__ = "_vetainc_queue_v1"
    seq: int = sa.Column(sa.BigInteger(), default=algo.calc_seqid, primary_key=True)
    queue: int = sa.Column(sa.BigInteger(), primary_key=True)
    content = sa.Column(sa.JSON(), nullable=False)

T = typing.TypeVar("Obj")

class _State:
    locks: set[int] = set()

class LockContext:
    def __init__(self, queue: int, timeout: int):
        self.__queue = queue
        self.__timeout = timeout
    async def __aenter__(self, *args, **kwargs):
        while self.__queue in _State.locks:
            if time.time() >= self.__timeout:
                raise Empty()
            await asyncio.sleep(0)
        _State.locks.add(self.__queue)
        return self
    async def __aexit__(self, *args, **kwargs):
        _State.locks.remove(self.__queue)

class DistQueue(typing.Generic[T]):
    def __init__(self, *openid: str, qid: typing.Optional[int] = None):
        if qid is None:
            assert len(openid) >= 1
            self.__queue = algo.calc_hash(*openid)
        else:
            self.__queue = qid
    async def get_nowait(self) -> T:
        try:
            async with orm.Session() as session:
                result = (await session.execute(sa.select(QueueModel).where(QueueModel.queue == self.__queue))).fetchone()
                if result is None:
                    raise RuntimeError()
                result = result._tuple()[0]
                R = result.content
                await session.delete(result)
                await session.commit()
                return R
        except Exception:
            raise Empty()
    async def get(self, *, timeout: int = 3600) -> T:
        timeout += int(time.time())
        async with LockContext(self.__queue, timeout):
            while True:
                if time.time() >= timeout:
                    raise Empty()
                try:
                    return await self.get_nowait()
                except Exception:
                    pass
                rt = random.uniform(3.0, 4.5)
                if time.time() >= (timeout + rt):
                    raise Empty()
                await asyncio.sleep(rt)
    async def put(self, item: T):
        async with orm.Session() as session:
            session.add(QueueModel(
                content=item,
                is_json=False
            ))
            await session.commit()
    async def put_nowait(self, item: T):
        asyncio.create_task(self.put(item))