import os
import threading
from contextlib import contextmanager
from typing import List

from optscale_arcee.utils import single


def get_service_name(path: str) -> str:
    return os.path.basename(os.path.dirname(path)).lower()


def get_package_name(path: str) -> str:
    return os.path.basename(os.path.dirname(
        os.path.dirname(path))).lower()


def list_services() -> List[str]:
    services = []
    for a in os.listdir(os.path.dirname(__file__)):
        if os.path.isdir(a) and not a.startswith('_'):
            services.append(a)
    return services


@single
class ThreadedMethodsTracker:
    """
    Track what method in what thread is executed
    """
    TID_METHOD_MAP = {}
    TID_COUNTER_MAP = {}

    @contextmanager
    def manage_method(self, method: str):
        tid = threading.current_thread().native_id
        self._add(tid, method)
        try:
            yield
        finally:
            self._delete(tid)

    def _add(self, tid: int, method: str):
        if tid not in self.__class__.TID_COUNTER_MAP:
            self.__class__.TID_COUNTER_MAP[tid] = 0
            self.__class__.TID_METHOD_MAP[tid] = method
        self.__class__.TID_COUNTER_MAP[tid] += 1

    def _delete(self, tid: int):
        self.__class__.TID_COUNTER_MAP[tid] -= 1
        if self.__class__.TID_COUNTER_MAP[tid] == 0:
            self.__class__.TID_COUNTER_MAP.pop(tid)
            self.__class__.TID_METHOD_MAP.pop(tid)

    def get(self) -> str:
        tid = threading.current_thread().native_id
        return self.__class__.TID_METHOD_MAP.get(tid)
