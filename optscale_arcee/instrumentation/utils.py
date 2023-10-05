import os


def get_package_name(path: str) -> str:
    return os.path.basename(os.path.dirname(path)).lower()
