import os
import asyncio
import threading
from optscale_arcee.modules.providers import local_file, amazon

LOCAL_PREFIX = 'file://'
S3_PREFIX = 's3://'
BASE_PATH = 'optscale/datasets/%s/'


class DatasetThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception = None

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as e:
            self.exception = e


class Dataset(object):
    __slots__ = ('key', 'name', 'description', 'labels', 'meta',
                 'timespan_from', 'timespan_to', 'aliases',
                 '_tasks', '_files', '_version')

    def __init__(self, key: str, name: str = None, description: str = None,
                 labels: list[str] = [], meta: dict = {},
                 timespan_from: int = None, timespan_to: int = None,
                 aliases: list[str] = []):
        self._tasks: list = []
        self._files: dict = {}
        self._version: int = None
        self.key: str = key
        self.name: str = name
        self.description: str = description
        self.labels: list[str] = labels
        self.meta: dict = meta
        self.timespan_from: int = timespan_from
        self.timespan_to: int = timespan_to
        self.aliases: list[str] = aliases

    @classmethod
    def from_response(cls, response):
        version = response.pop('version', {})
        files = version.pop('files', [])
        response.update(version)
        obj = cls(**{
            k: response.get(k) for k in cls.__slots__ if k in response
        })
        obj._version = version['version']
        if files:
            obj._files = {f['path']: {
                'path': f['path'],
                'size': f['size'],
                'digest': f['digest']
            } for f in files}
        return obj

    @property
    def __dict__(self):
        res = dict()
        for k in self.__slots__:
            if k.startswith('_'):
                continue
            value = getattr(self, k)
            if value:
                res[k] = getattr(self, k)
        res['files'] = list(self._files.values())
        return res

    def _get_provider(self, path):
        if path.startswith(LOCAL_PREFIX):
            return local_file, path.strip(LOCAL_PREFIX)
        elif path.startswith(S3_PREFIX):
            return amazon, path
        else:
            raise TypeError('Unhandled path type')

    def _add_file(self, path):
        provider, local_path = self._get_provider(path)
        digest, size = asyncio.run(provider.get_file_info(local_path))
        self._files[path] = {
            'path': path,
            'size': size,
            'digest': digest
        }

    def add_file(self, path):
        if path in self._files:
            return
        self._version = None
        self._files[path] = None
        thr = DatasetThread(target=self._add_file, args=(path, ))
        thr.start()
        self._tasks.append(thr)

    def remove_file(self, path):
        if path in self._files:
            del self._files[path]

    def wait_ready(self):
        for task in self._tasks:
            task.join()
            if task.exception:
                raise task.exception

    def download(self, overwrite=True) -> dict:
        download_map = dict()
        if self._version is None:
            raise TypeError('Dataset is not logged')
        name = f'{self.key}:V{self._version}'
        print('Downloading %s' % name)
        for path, file in self._files.items():
            destination = BASE_PATH % name
            file_name = path.split('/')[-1]
            download_path = destination + file_name
            download_map[path] = download_path
            if not overwrite and os.path.isfile(download_path):
                continue
            thr = DatasetThread(
                target=self._download, args=(file, destination, file_name))
            thr.start()
            self._tasks.append(thr)
        self.wait_ready()
        print('Download completed: %s' % name)
        return download_map

    def _download(self, file, destination, file_name):
        digest = file['digest']
        path = file['path']
        provider, local_path = self._get_provider(path)
        asyncio.run(
            provider.download(
                local_path, digest, destination, file_name
            )
        )
