import asyncio
import time
import threading

from optscale_arcee.sender.sender import Sender
from optscale_arcee.collectors.console import (
    acquire_console, release_console)
from optscale_arcee.name_generator import NameGenerator
from optscale_arcee.utils import single


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
        self, token=None, task_key=None, endpoint_url=None, ssl=True
    ):
        self.shutdown_flag = threading.Event()
        self.token = token
        self.task_key = task_key
        self.sender = Sender(endpoint_url, ssl, self.shutdown_flag)
        self.hb = None
        self._run = None
        self._tags = dict()
        self._name = None
        self._hyperparams = dict()
        self._dataset = None
        self._model = None
        self._model_version = None
        self._model_version_tags = dict()
        self._model_version_aliases = list()
        self._artifacts = dict()

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

    @property
    def hyperparams(self):
        return self._hyperparams

    @hyperparams.setter
    def hyperparams(self, value):
        k, v = value
        self._hyperparams.update({k: v})

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            finish()
        else:
            error()
        return exc_type is None

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def model_version(self):
        return self._model_version

    @model_version.setter
    def model_version(self, value):
        self._model_version = value

    @property
    def model_version_tags(self):
        return self._model_version_tags

    @model_version_tags.setter
    def model_version_tags(self, value):
        k, v = value
        self._model_version_tags.update({k: v})

    @property
    def model_version_aliases(self):
        return self._model_version_aliases

    @model_version_aliases.setter
    def model_version_aliases(self, value):
        aliases = set(self._model_version_aliases)
        aliases.add(value)
        self._model_version_aliases = list(aliases)

    @property
    def artifacts(self):
        return self._artifacts

    @artifacts.setter
    def artifacts(self, value):
        id_, path, tags = value
        self._artifacts[path] = {
            'id': id_,
            'tags': tags
        }


def init(
    token, task_key, run_name=None, endpoint_url=None, ssl=True, period=1
):
    acquire_console()
    arcee = Arcee(token, task_key, endpoint_url, ssl)
    name = (
        run_name if run_name is not None else NameGenerator.get_random_name()
    )
    run_id = asyncio.run(arcee.sender.get_run_id(task_key, token, name))["id"]
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
            {"project": arcee.task_key, "run": arcee.run, "data": {}},
        )
    )
    return arcee


def hyperparam(key, value):
    """
    Add hyperparameter
    Args:
        key: string
        value: float
    Returns:
    """
    arcee = Arcee()
    arcee.hyperparams = (key, value)
    asyncio.run(arcee.sender.add_hyperparams(
        arcee.run, arcee.token, arcee.hyperparams))


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


def dataset(path, name=None, description=None, labels=None):
    arcee = Arcee()
    if arcee.dataset is None:
        arcee.dataset = path
        asyncio.run(arcee.sender.register_dataset(
            arcee.token, arcee.run, arcee.name, arcee.task_key, path, name,
            description, labels
        ))


def finish():
    release_console()
    arcee = Arcee()
    try:
        asyncio.run(
            arcee.sender.send_console(
                arcee.run,
                arcee.token
            )
        )
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
    release_console()
    arcee = Arcee()
    try:
        asyncio.run(
            arcee.sender.send_console(
                arcee.run,
                arcee.token
            )
        )
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
            {"project": arcee.task_key, "run": arcee.run, "data": data},
        )
    )


def model(key, path=None):
    arcee = Arcee()
    arcee.model = asyncio.run(
        arcee.sender.add_model(
            arcee.token, key
        )
    )
    asyncio.run(
        arcee.sender.create_model_version(
            arcee.run, arcee.model, arcee.token, path=path
        )
    )


def model_version(version):
    arcee = Arcee()
    asyncio.run(
        arcee.sender.add_version(
            arcee.run, arcee.model, arcee.token, version
        )
    )


def model_version_alias(alias):
    arcee = Arcee()
    arcee.model_version_aliases = alias
    asyncio.run(
        arcee.sender.add_version_aliases(
            arcee.run, arcee.model, arcee.token, arcee.model_version_aliases
        )
    )


def model_version_tag(key, value):
    arcee = Arcee()
    arcee.model_version_tags = (key, value)
    asyncio.run(
        arcee.sender.add_version_tags(
            arcee.run, arcee.model, arcee.token, arcee.model_version_tags
        )
    )


def artifact(path, name=None, description=None, tags=None):
    arcee = Arcee()
    arcee.artifacts = asyncio.run(
        arcee.sender.add_artifact(
            arcee.token, arcee.run, arcee.name, arcee.task_key, path, name,
            description, tags
        )
    )


def artifact_tag(path, key, value):
    arcee = Arcee()
    arcee.artifacts = asyncio.run(
        arcee.sender.add_artifact_tags(
            arcee.token, arcee.artifacts, path, key, value
        )
    )
