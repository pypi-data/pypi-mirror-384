from ._orm import orm
from ._algo import algo
from ._core import register_daemon
import time
import random
import sqlalchemy as sa
import asyncio

class LockModel(orm.Base):
    __tablename__ = "_vetainc_lock_v1"
    lock: int = sa.Column(sa.BigInteger(), primary_key=True)
    myname: int = sa.Column(sa.BigInteger())
    expire: int = sa.Column(sa.BigInteger())

class MutexLocks:
    class ConflictError(Exception):
        pass
    async def acquire(self, lock: str, ttl: int = 3600) -> int:
        lock: int = algo.calc_hash("VetaINC", "Lock", lock)
        myname = random.randint(0, 0x7fff_ffff) * 0xffff_ffff + random.randint(0, 0xffff_ffff)
        try:
            async with orm.Session() as session:
                await session.execute(sa.insert(LockModel).values(lock=lock, myname=myname, expire=int(time.time()) + ttl))
                await session.commit()
            return myname
        except Exception:
            raise self.ConflictError()
    async def __release(self, lock: str, myname: int) -> bool:
        lock: int = algo.calc_hash("VetaINC", "Lock", lock)
        try:
            async with orm.Session() as session:
                await session.execute(sa.delete(LockModel).where(LockModel.lock == lock).where(LockModel.myname == myname))
                await session.commit()
            return True
        except Exception:
            return False
    async def __try_to_release(self, lock: str, myname: int):
        for retry_time in range(0, 7):
            await asyncio.sleep(1 << retry_time)
            if await self.__release(lock, myname):
                return
    async def release(self, lock: str, myname: int):
        if not await self.__release(lock, myname):
            asyncio.create_task(self.__try_to_release(lock, myname))
    # Context controller
    class MutexContext:
        def __init__(self, lock: str, ttl: int):
            self.__lock = lock
            self.__ttl = ttl
            self.__entranced = False
            self.__myname = 0
        async def __aenter__(self, *args, **kwargs):
            if not self.__entranced:
                self.__myname = await mutex.acquire(self.__lock, ttl=self.__ttl)
            self.__entranced = True
            return self
        async def __aexit__(self, *args, **kwargs):
            await mutex.release(self.__lock, self.__myname)
            self.__entranced = False
    def __call__(self, lock: str, ttl: int = 3600):
        return self.MutexContext(lock, ttl)

mutex = MutexLocks()

@register_daemon()
async def listen_mutex_expires():
    await asyncio.sleep(random.uniform(0.5, 3.0))
    while True:
        try:
            async with orm.Session() as session:
                await session.execute(sa.delete(LockModel).where(LockModel.expire <= int(time.time())))
            await asyncio.sleep(random.uniform(40.0, 60.0))
        except Exception:
            await asyncio.sleep(random.uniform(1.0, 2.0))