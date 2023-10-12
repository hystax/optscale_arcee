from typing import List

from optscale_arcee.instrumentation.collector import Collector
from optscale_arcee.instrumentation.stats import Stats


class RedshiftConnectorStats(Stats):
    __slots__ = ("queries",)

    @property
    def package(self):
        return "redshift_connector"


def count_queries(queries: List[dict]):
    Collector().add(RedshiftConnectorStats(queries=queries))
