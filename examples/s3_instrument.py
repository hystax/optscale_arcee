import asyncio
import json
import os

import boto3

from optscale_arcee.instrumentation.boto3 import s3
from optscale_arcee.instrumentation.collector import Collector

access_key_id = 'access_key_id'
secret_access_key = 'secret_access_key'
bucket = 'bucket'

s3.instrument()

session = boto3.Session(
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key
)
s3_client = session.client('s3')

s3_client.list_objects_v2(Bucket=bucket, Prefix='')

# sizes to try simple and multipart operations
for filesize in [1024, 10 * 1024 ** 2]:
    filename = f'random_file_{filesize}'

    print(f'Creating {filename}')
    with open(filename, 'wb') as f:
        f.write(os.urandom(filesize))

    print(f'Uploading {filename} to {bucket}/{filename}')
    s3_client.upload_file(filename, bucket, filename)

    print(f'Downloading {bucket}/{filename} to {filename}')
    s3_client.download_file(bucket, filename, filename)

    print(f'Removing {bucket}/{filename}')
    s3_client.delete_object(Bucket=bucket, Key=filename)

    os.remove(filename)

print('Printing instrumentation result:')
print(json.dumps(asyncio.run(Collector().get()), indent=2))
