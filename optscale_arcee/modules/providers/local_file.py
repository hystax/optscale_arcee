import os
import sys
import hashlib
import shutil
import mmap
import aiofiles

_KB: int = 1_024
_CHUNKSIZE: int = 128 * _KB


async def get_file_info(path):
    digest = await _get_md5(path)
    size = await _get_size(path)
    return digest, size


async def _get_md5(path):
    if sys.version_info >= (3, 9):
        md_5_hash = hashlib.md5(usedforsecurity=False)
    else:
        md_5_hash = hashlib.md5()
    async with aiofiles.open(path, "rb") as f:
        try:
            with mmap.mmap(f.fileno(), length=0,
                           access=mmap.ACCESS_READ) as mview:
                md_5_hash.update(mview)
        except OSError:
            chunk = f.read(_CHUNKSIZE)
            while chunk:
                md_5_hash.update(chunk)
                chunk = f.read(_CHUNKSIZE)
        except ValueError:
            pass
    return md_5_hash.hexdigest()


async def _get_size(path):
    st = os.stat(path)
    return st.st_size


async def download(path, digest, dest_path, file_name):
    if not os.path.exists(path):
        raise ValueError('Failed to find file path %s' % path)
    md5 = await _get_md5(path)
    if md5 != digest:
        raise ValueError(
            'Cannot download dataset file %s. Source file has been changed' %
            path)
    os.makedirs(dest_path, exist_ok=True)
    shutil.copy(path, dest_path + file_name)
