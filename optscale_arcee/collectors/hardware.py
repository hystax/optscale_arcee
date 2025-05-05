import asyncio
import math
import os
import concurrent.futures
from functools import reduce

import psutil

from optscale_arcee.libs.GPUtil import GPUtil
from optscale_arcee.utils import run_async


# tune accuracy depending on #cpus
_MEASURE_TIME = 1 - 1 / (os.cpu_count())
_TIME_INTERVALS = (_MEASURE_TIME + 0.05, _MEASURE_TIME + 0.01)

BYTES_IN_KiB = 1024


class Collector:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    @staticmethod
    def _gpu_stats():
        gpus = GPUtil.getGPUs()
        len_gpus = len(gpus)
        if len_gpus < 1:
            return {}
        avg_gpu_load = reduce(
            lambda x, y: x + y, map(lambda z: z.load, gpus)
        ) / len(gpus)
        avg_gpu_memory_free = reduce(
            lambda x, y: x + y, map(lambda z: z.memoryFree, gpus)
        ) / len(gpus)
        avg_gpu_memory_total = reduce(
            lambda x, y: x + y, map(lambda z: z.memoryTotal, gpus)
        ) / len(gpus)
        avg_gpu_memory_used = reduce(
            lambda x, y: x + y, map(lambda z: z.memoryUsed, gpus)
        ) / len(gpus)
        stats = {
            "avg_gpu_memory_free": avg_gpu_memory_free,
            "avg_gpu_memory_total": avg_gpu_memory_total,
            "avg_gpu_memory_used": avg_gpu_memory_used,
        }
        # get rid of devices with limited support
        if not math.isnan(avg_gpu_load):
            stats["avg_gpu_load"] = avg_gpu_load * 100
        return stats

    @staticmethod
    def _ps_stats(cpu_interval=0.5, proc_interval=0.5):
        load1, load5, load15 = psutil.getloadavg()
        cpu_load = psutil.cpu_percent(interval=cpu_interval, percpu=True)
        cpu_percent = round(sum(cpu_load) / psutil.cpu_count(), 2)
        # get proc pid
        process = psutil.Process(os.getpid())
        # physical mem according to https://psutil.readthedocs.io/en/latest/
        physical_mem = psutil.virtual_memory().total
        swap_mem = psutil.swap_memory().total
        # virtual memory used by process
        proc_vmem = process.memory_info().vms
        # resident state memory used by process
        proc_rss = process.memory_info().rss
        cpu_proc = min(
            [
                round(
                    process.cpu_percent(
                        interval=proc_interval) / psutil.cpu_count(),
                    2,
                ),
                cpu_percent,
            ]
        )

        ps_stats = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": cpu_percent,
            "cpu_percent_percpu": cpu_load,
            "load_average": [load1, load5, load15],
            "cpu_usage": (load15 / psutil.cpu_count()) * 100,
            "used_ram_percent": psutil.virtual_memory()[2],
            "used_ram_mb": psutil.virtual_memory()[3] / (1024 * 1024),
        }

        proc_stats = {
            # process cpu usage in % (per core)
            "cpu": cpu_proc,
            "mem": {
                # process virtual memory usage, p - percent, t - value
                "vms": {
                    "p": "{:.3f}".format(
                        proc_vmem / (physical_mem + swap_mem)
                    ),
                    "t": proc_vmem,
                },
                # process resident state memory usage, p - percent, t - value
                "rss": {
                    "p": "{:.3f}".format(proc_rss / physical_mem),
                    "t": proc_rss,
                },
            },
        }
        return ps_stats, proc_stats

    @classmethod
    def _collect_stats(cls):
        cpu_interval, proc_interval = _TIME_INTERVALS
        gpu_stats = cls._gpu_stats()
        ps_stats, ps_info = cls._ps_stats(cpu_interval, proc_interval)

        return {
            "ps_stats": ps_stats,
            "gpu_stats": gpu_stats,
            "proc": ps_info,
        }

    @staticmethod
    async def _io(interval: float = 1):
        def _get_io():
            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()
            return {
                "disk_read": disk.read_bytes,
                "disk_write": disk.write_bytes,
                "net_sent": net.bytes_sent,
                "net_recv": net.bytes_recv
            }

        before = _get_io()
        await asyncio.sleep(interval)
        after = _get_io()
        disk_read = round(
            (after['disk_read'] - before['disk_read']) / BYTES_IN_KiB, 2)
        disk_write = round(
            (after['disk_write'] - before['disk_write']) / BYTES_IN_KiB, 2)
        net_sent = round(
            (after['net_sent'] - before['net_sent']) / BYTES_IN_KiB, 2)
        net_recv = round(
            (after['net_recv'] - before['net_recv']) / BYTES_IN_KiB, 2)
        return disk_read, disk_write, net_sent, net_recv

    @classmethod
    async def collect_stats(cls):
        disk_read, disk_write, net_sent, net_recv = await cls._io()
        result = {
            # IO stats in KiB/s
            "io_stats": {
                "disk_read": disk_read,
                "disk_write": disk_write,
                "net_sent": net_sent,
                "net_recv": net_recv,
            }
        }
        ps_stats = await run_async(cls._collect_stats, executor=cls.executor)
        result.update(ps_stats)
        return result
