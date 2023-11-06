import concurrent.futures
import subprocess
from typing import Optional

from optscale_arcee.utils import run_async


class Collector:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    @staticmethod
    def __get_remote() -> str:
        return subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"]
        ).decode('UTF-8').strip()

    @staticmethod
    def __get_branch() -> str:
        return subprocess.check_output(
            ["git", "branch", "--show-current"]).decode('UTF-8').strip()

    @staticmethod
    def __get_commit_id() -> str:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"]).decode('UTF-8').strip()

    @staticmethod
    def __get_status() -> str:
        try:
            subprocess.check_call(["git", "diff", "--exit-code", "--quiet"])
            return "clean"
        except subprocess.CalledProcessError:
            return "dirty"

    @classmethod
    def _collect(cls) -> Optional[dict]:
        try:
            return {
                "remote": cls.__get_remote(),
                "branch": cls.__get_branch(),
                "commit_id": cls.__get_commit_id(),
                "status": cls.__get_status()
            }
        except FileNotFoundError:
            return

    @classmethod
    async def collect(cls):
        return await run_async(cls._collect, executor=cls.executor)
