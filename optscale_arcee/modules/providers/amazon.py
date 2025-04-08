import os
import aioboto3
import aiofiles
from urllib.parse import urlparse


async def get_file_info(path):
    bucket, key = await _parse_uri(path)
    session = aioboto3.Session()
    async with session.resource("s3") as s3:
        res = await s3.Object(bucket, key)
        etag = await res.e_tag
        size = await res.content_length
    return etag.strip('"'), size


async def _parse_uri(path):
    url = urlparse(path)
    bucket = url.netloc
    key = url.path[1:]
    return bucket, key


async def download(path, digest, dest_path, file_name):
    bucket, key = await _parse_uri(path)
    session = aioboto3.Session()
    async with session.resource("s3") as s3:
        s3_object = await s3.Object(bucket, key)
        etag = await s3_object.e_tag
        if etag.strip('"') != digest:
            raise ValueError(
                'Cannot download dataset file %s. Source file has been changed' %
                path)
        os.makedirs(dest_path, exist_ok=True)
        async with aiofiles.open(dest_path + file_name, 'wb') as fp:
            await s3_object.download_fileobj(fp)


async def main(bucket, key):
    session = aioboto3.Session()
    async with session.resource("s3") as s3:
        bucket = await s3.Object(bucket, key)
        async with aiofiles.open('TEST', 'wb') as fp:
            await bucket.download_fileobj(fp)
