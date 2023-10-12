from typing import Type, List

from optscale_arcee.instrumentation.stats import Stats
from optscale_arcee.instrumentation.collector import Collector

_STATS_SERVICES = {}


def register_service(service_name: str, stats_cls: Type[Stats]):
    _STATS_SERVICES[service_name] = stats_cls


def unregister_service(service_name: str):
    _STATS_SERVICES.pop(service_name, None)


def is_service_registered(service_name: str):
    return service_name in _STATS_SERVICES


class Boto3Stats(Stats):
    __slots__ = ("method_calls",)

    @property
    def package(self):
        return "boto3"


class S3Stats(Boto3Stats):
    __slots__ = (
        "bytes_downloaded",
        "bytes_uploaded",
        "files_accessed",
    )

    @property
    def service(self):
        return "s3"


class Ec2Stats(Boto3Stats):
    @property
    def service(self):
        return "ec2"


def count_uploaded_bytes(service_name: str, bytes_uploaded: int):
    stats_cls = _STATS_SERVICES.get(service_name)
    if stats_cls:
        Collector().add(stats_cls(bytes_uploaded=bytes_uploaded))


def count_downloaded_bytes(service_name: str, bytes_downloaded: int):
    stats_cls = _STATS_SERVICES.get(service_name)
    if stats_cls:
        Collector().add(stats_cls(bytes_downloaded=bytes_downloaded))


def count_method(service_name: str, method_name: str):
    stats_cls = _STATS_SERVICES.get(service_name)
    if stats_cls:
        Collector().add(stats_cls(method_calls={method_name: 1}))


def count_file(service_name: str, bucket: str, filename: str):
    stats_cls = _STATS_SERVICES.get(service_name)
    if stats_cls:
        Collector().add(stats_cls(files_accessed={bucket: {filename}}))


def count_files(service_name: str, bucket: str, filenames: List[str]):
    stats_cls = _STATS_SERVICES.get(service_name)
    if stats_cls:
        Collector().add(stats_cls(files_accessed={bucket: {*filenames}}))
