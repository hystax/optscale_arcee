import concurrent.futures
from io import StringIO
import sys
from typing import Dict

from optscale_arcee.utils import run_async


class StdProxy:
    def __init__(self, std_stream, on_op_cbs):
        self._std_stream = std_stream
        self._on_op_cbs = on_op_cbs

    def __getattr__(self, name):
        return self._wrapped(name)

    def _wrapped(self, name):
        cb_op = self._on_op_cbs.get(name)
        if not cb_op:
            return getattr(self._std_stream, name)

        def inner(*args, **kwargs):
            cb_op(*args, **kwargs)
            return getattr(self._std_stream, name)(*args, **kwargs)

        return inner


class WritesCollector:
    def __init__(self, std_stream):
        self.stream = StringIO()
        self.cb_map = {
            'write': self.handle_write()
        }
        self.proxy = StdProxy(std_stream, self.cb_map)

    def handle_write(self):
        def inner(*args, **kwargs):
            for arg in args:
                # print typically writes args
                self.stream.write(arg)

        return inner

    def get_writes(self):
        return self.stream.getvalue()


stdout_writes = WritesCollector(sys.stdout)
stderr_writes = WritesCollector(sys.stderr)


def acquire_console():
    sys.stdout = stdout_writes.proxy
    sys.stderr = stderr_writes.proxy


def release_console():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


class Collector:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    @classmethod
    def _collect(cls) -> Dict[str, str]:
        return {
            "output": stdout_writes.get_writes(),
            "error": stderr_writes.get_writes()
        }

    @classmethod
    async def collect(cls):
        return await run_async(cls._collect, executor=cls.executor)
