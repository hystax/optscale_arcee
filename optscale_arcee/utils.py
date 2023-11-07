import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial


def single(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


async def run_async(func, *args, loop=None, executor=None, **kwargs):
    if loop is None:
        loop = asyncio.get_event_loop()
    if executor is None:
        executor = ThreadPoolExecutor(max_workers=10)
    pfunc = partial(func, *args, **kwargs)
    return await loop.run_in_executor(executor, pfunc)
