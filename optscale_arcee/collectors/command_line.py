import concurrent.futures
import psutil

from optscale_arcee.utils import run_async


class Collector:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    @classmethod
    def _collect(cls) -> str:
        return ' '.join(psutil.Process().cmdline())

    @classmethod
    async def collect(cls):
        return await run_async(cls._collect, executor=cls.executor)
