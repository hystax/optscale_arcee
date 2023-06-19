import asyncio
import time
import threading

from optscale_arcee.sender.sender import Sender
from optscale_arcee.name_generator import NameGenerator


def single(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


class Job(threading.Thread):
    def __init__(self, shutdown_flag, *args, **kwargs):
        # TODO: typing
        threading.Thread.__init__(self)
        self.__shutdown_flag = shutdown_flag
        self.__kw = kwargs

    def s_noblock(self, sender, run, token):
        return asyncio.run(sender.send_proc_data(run, token))

    def job(self):
        args = self.__kw.get("meth_args", list())
        self.s_noblock(*args)

    def run(self):
        sleep = self.__kw.get("sleep")
        if not sleep or not isinstance(sleep, int):
            # 1 second by default
            sleep = 1
        while not self.__shutdown_flag.is_set():
            self.job()
            time.sleep(sleep)


@single
class Arcee:
    def __init__(
        self, token=None, model_key=None, endpoint_url=None, ssl=True
    ):
        self.shutdown_flag = threading.Event()
        self.token = token
        self.model_key = model_key
        self.sender = Sender(endpoint_url, ssl, self.shutdown_flag)
        self.hb = None
        self._run = None
        self._tags = {}
        self._name = None

    @property
    def run(self):
        return self._run

    @run.setter
    def run(self, value):
        self._run = value

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        k, v = value
        self._tags.update({k: v})

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            finish()
        else:
            error()
        return exc_type is None


def init(
    token, model_key, run_name=None, endpoint_url=None, ssl=True, period=1
):
    arcee = Arcee(token, model_key, endpoint_url, ssl)
    name = (
        run_name if run_name is not None else NameGenerator.get_random_name()
    )
    run_id = asyncio.run(arcee.sender.get_run_id(model_key, token, name))["id"]
    arcee.run = run_id
    arcee.name = name
    arcee.hb = Job(
        meth_args=(arcee.sender, run_id, token),
        sleep=period,
        shutdown_flag=arcee.shutdown_flag,
    )
    arcee.hb.start()
    asyncio.run(
        arcee.sender.send_stats(
            arcee.token,
            {"project": arcee.model_key, "run": arcee.run, "data": {}},
        )
    )
    return arcee


def tag(key, value):
    arcee = Arcee()
    arcee.tags = (key, value)
    asyncio.run(arcee.sender.add_tags(arcee.run, arcee.token, arcee.tags))


def milestone(value):
    arcee = Arcee()
    asyncio.run(arcee.sender.add_milestone(arcee.run, arcee.token, value))


def stage(name):
    arcee = Arcee()
    asyncio.run(arcee.sender.create_stage(arcee.run, arcee.token, name))


def finish():
    arcee = Arcee()
    try:
        asyncio.run(
            arcee.sender.change_state(
                arcee.run,
                arcee.token,
                2,
                True,
            )
        )
    finally:
        arcee.shutdown_flag.set()
        arcee.hb.join()


def error():
    arcee = Arcee()
    try:
        asyncio.run(
            arcee.sender.change_state(
                arcee.run,
                arcee.token,
                3,
                True,
            )
        )
    finally:
        arcee.shutdown_flag.set()
        arcee.hb.join()


def info():
    arcee = Arcee()
    return arcee.__dict__


def send(data):
    arcee = Arcee()
    asyncio.run(
        arcee.sender.send_stats(
            arcee.token,
            {"project": arcee.model_key, "run": arcee.run, "data": data},
        )
    )
