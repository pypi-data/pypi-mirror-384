import typing
import asyncio
import sqlalchemy as sa
from ._orm import orm_engine, init_orm, init_transient
from fastapi import FastAPI
import uvicorn
import os
import random

http = FastAPI(openapi_url=None)

__all__ = [
    "http",
    "create_task",
    "register_daemon",
    "run"
]

class _State:
    is_inited: bool = False
    tasks: set[typing.Coroutine] = set()

def create_task(coro: typing.Coroutine):
    if _State.is_inited:
        asyncio.create_task(coro)
    else:
        _State.tasks.add(coro)

def register_daemon(*args, **kwargs):
    def __border(fn):
        async def __proxy():
            while True:
                try:
                    await fn(*args, **kwargs)
                except Exception:
                    pass
                await asyncio.sleep(random.uniform(0.9, 1.2))
        create_task(__proxy())
        return fn
    return __border

C = uvicorn.Config(http, host="0.0.0.0", port=int(os.environ.get("VETA_HTTP_PORT", 4516)))

async def init():
    await asyncio.gather(init_orm(), init_transient())
    _State.is_inited = True
    for coro in _State.tasks:
        asyncio.create_task(coro)
        del coro
    await uvicorn.Server(C).serve()

@register_daemon()
async def check_orm_session():
    # Connection Keeper
    while True:
        async with orm_engine.begin() as conn:
            await conn.execute(sa.text("SELECT count(1)"))
            del conn
        await asyncio.sleep(random.uniform(5.5, 17.5))

def run():
    asyncio.run(init())