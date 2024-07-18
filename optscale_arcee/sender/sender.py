import aiohttp
import threading

from optscale_arcee.platform import CollectorFactory
from optscale_arcee.collectors.command_line import (
    Collector as CommandCollector)
from optscale_arcee.collectors.git import Collector as GitCollector
from optscale_arcee.collectors.hardware import Collector as HardwareCollector
from optscale_arcee.collectors.module import Collector as ImportsCollector
from optscale_arcee.collectors.console import Collector as OutCollector


def check_shutdown_flag_set(function):
    async def inner(self, *args, **kwargs):
        if not self.shutdown_flag.is_set():
            return await function(self, *args, **kwargs)

    return inner


class Sender:
    # default OptScale url
    base_url = "https://my.optscale.com:443/arcee/v2"

    def __init__(self, endpoint_url=None, ssl=True, shutdown_flag=None):
        if endpoint_url is None:
            endpoint_url = self.base_url
        self.endpoint_url = endpoint_url
        self.shutdown_flag = shutdown_flag or threading.Event()
        self.ssl = ssl

    @staticmethod
    async def m():
        platform = await CollectorFactory.get()
        return await platform().get_platform_meta()

    @staticmethod
    async def _proc_data():
        return await HardwareCollector.collect_stats()

    @staticmethod
    async def _imports_data():
        return await ImportsCollector.get_imports()

    @staticmethod
    async def _git_data():
        return await GitCollector.collect()

    @staticmethod
    async def _self_command():
        return await CommandCollector.collect()

    @staticmethod
    async def _output():
        return await OutCollector.collect()

    async def send_get_request(self, url, headers=None, params=None) -> dict:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                url, params=params, raise_for_status=True, ssl=self.ssl
            ) as response:
                return await response.json()

    async def send_post_request(self, url, headers=None, data=None) -> dict:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url, json=data, raise_for_status=True, ssl=self.ssl
            ) as response:
                return await response.json()

    async def send_patch_request(self, url, headers=None, data=None) -> dict:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.patch(
                url, json=data, raise_for_status=True, ssl=self.ssl
            ) as response:
                return await response.json()

    @check_shutdown_flag_set
    async def get_run_id(self, task_key, token, run_name):
        uri = "%s/tasks/%s/run" % (self.endpoint_url, task_key)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        data = {
            "imports": await self._imports_data(),
            "git": await self._git_data(),
            "command": await self._self_command(),
            "name": run_name
        }
        return await self.send_post_request(uri, headers, data)

    @check_shutdown_flag_set
    async def add_milestone(self, run_id, token, value):
        uri = "%s/run/%s/milestones" % (self.endpoint_url, run_id)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        return await self.send_post_request(uri, headers, {"milestone": value})

    @check_shutdown_flag_set
    async def add_tags(self, run_id, token, tags):
        uri = "%s/run/%s" % (self.endpoint_url, run_id)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        return await self.send_patch_request(uri, headers, {"tags": tags})

    @check_shutdown_flag_set
    async def change_state(self, run_id, token, state, finish=False):
        uri = "%s/run/%s" % (self.endpoint_url, run_id)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        return await self.send_patch_request(
            uri, headers, {"state": state, "finish": finish}
        )

    @check_shutdown_flag_set
    async def create_stage(self, run_id, token, name):
        uri = "%s/run/%s/stages" % (self.endpoint_url, run_id)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        return await self.send_post_request(uri, headers, {"stage": name})

    @check_shutdown_flag_set
    async def send_stats(self, token, data):
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        meta = await self.m()
        data.update({"platform": meta.to_dict()})
        await self.send_post_request(
            "%s/%s" % (self.endpoint_url, "collect"), headers, data
        )

    @check_shutdown_flag_set
    async def send_proc_data(self, run_id, token):
        uri = "%s/run/%s/proc" % (self.endpoint_url, run_id)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        data = dict()
        meta = await self.m()
        proc = await self._proc_data()
        data.update({"platform": meta.to_dict()})
        data.update({"proc_stats": proc})
        return await self.send_post_request(uri, headers, data)

    @staticmethod
    def generate_description(task_key, run_name, run_id):
        return f"Discovered in training {task_key} - {run_name}({run_id})"

    @check_shutdown_flag_set
    async def register_dataset(self, token, run_id, run_name, task_key, path,
                               dataset_name=None, description=None,
                               labels=None):
        uri = f"{self.endpoint_url}/run/{run_id}/dataset_register"
        headers = {"x-api-key": token, "Content-Type": "application/json"}

        if dataset_name is None:
            dataset_name = path
        if not description:
            description = self.generate_description(task_key, run_name, run_id)
        if labels is not None and not isinstance(labels, list):
            labels = [labels]

        data = {
            "path": path,
            "name": dataset_name,
            "description": description,
            "labels": labels or []
        }
        await self.send_post_request(uri, headers, data)

    @check_shutdown_flag_set
    async def add_hyperparams(self, run_id, token, hyperparams):
        uri = "%s/run/%s" % (self.endpoint_url, run_id)
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        return await self.send_patch_request(
            uri, headers, {"hyperparameters": hyperparams}
        )

    async def send_console(self, run_id, token):
        uri = f"{self.endpoint_url}/run/{run_id}/consoles"
        headers = {"x-api-key": token, "Content-Type": "application/json"}

        data = await self._output()
        await self.send_post_request(uri, headers, data)

    @check_shutdown_flag_set
    async def add_model(self, token, key):
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        model = await self.send_post_request(
            self.endpoint_url + '/models', headers, {"key": key}
        )
        return model.get('_id')

    @check_shutdown_flag_set
    async def create_model_version(self, run_id, model_id, token, path=None):
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        uri = f'{self.endpoint_url}/runs/{run_id}/models/{model_id}/version'
        body = {'path': path} if path else {}
        await self.send_post_request(uri, headers, body)

    @check_shutdown_flag_set
    async def patch_model_version(self, run_id, model_id, token, params):
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        uri = f'{self.endpoint_url}/runs/{run_id}/models/{model_id}/version'
        await self.send_patch_request(uri, headers, params)

    async def add_version(self, run_id, model_id, token, version):
        body = {'version': str(version)}
        await self.patch_model_version(run_id, model_id, token, body)

    async def add_version_aliases(self, run_id, model_id, token, aliases):
        body = {'aliases': aliases}
        await self.patch_model_version(run_id, model_id, token, body)

    async def add_version_tags(self, run_id, model_id, token, tags):
        body = {'tags': tags}
        await self.patch_model_version(run_id, model_id, token, body)

    @check_shutdown_flag_set
    async def add_artifact(self, token, run_id, run_name, task_key, path,
                           name=None, description=None, tags=None):
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        body = {
            'run_id': run_id,
            'path': path
        }
        if name:
            body['name'] = name
        if not description:
            description = self.generate_description(task_key, run_name, run_id)
        body['description'] = description
        if tags:
            body['tags'] = tags
        artifact = await self.send_post_request(
            self.endpoint_url + '/artifacts', headers, body
        )
        return artifact.get('_id'), path, tags or {}

    async def add_artifact_tags(self, token, artifacts, path, key, value):
        headers = {"x-api-key": token, "Content-Type": "application/json"}
        artifact = artifacts.get(path)
        if not artifact:
            raise ValueError("Artifact doesn't exists."
                             "Use arcee.artifact() to create one")
        artifact['tags'][key] = value
        body = {'tags': artifact['tags']}
        uri = f'{self.endpoint_url}/artifacts/{artifact["id"]}'
        await self.send_patch_request(uri, headers, body)
        return artifact["id"], path, artifact['tags']
