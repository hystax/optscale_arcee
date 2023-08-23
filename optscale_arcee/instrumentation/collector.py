import json
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Type

from optscale_arcee.instrumentation.stats import Stats
from optscale_arcee.utils import single, run_async


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


@single
class Collector:
    _queue = Queue()
    _executor = ThreadPoolExecutor(max_workers=5)

    def add(self, stats: Type[Stats]):
        self._queue.put_nowait(stats)

    def _get(self) -> dict:
        stats_map = {}
        while not self._queue.empty():
            stats = self._queue.get_nowait()
            if type(stats) not in stats_map:
                stats_map[type(stats)] = stats
            else:
                stats_map[type(stats)] += stats
        res = {}
        for stats in stats_map.values():
            if stats.package not in res:
                res[stats.package] = {}
            if stats.service:
                res[stats.package][stats.service] = stats.to_dict()
            else:
                res[stats.package] = stats.to_dict()
        return json.loads(json.dumps(res, cls=Encoder))

    async def get(self) -> dict:
        return await run_async(self._get, executor=self._executor)
