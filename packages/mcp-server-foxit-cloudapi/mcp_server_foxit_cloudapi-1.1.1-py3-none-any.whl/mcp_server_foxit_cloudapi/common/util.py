from typing import Union
import os


def is_path(path: Union[str, list]) -> bool:
    return isinstance(path, str) and not path.startswith("http://") and not path.startswith("https://")


def get_download_path():
    download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(download_path):
        os.makedirs(download_path, exist_ok=True)
    return download_path
