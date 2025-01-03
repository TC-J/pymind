from inspect import signature, Signature
import os
from pathlib import Path
import shutil
import stat
from typing import Callable
from tempfile import TemporaryDirectory


def match_kwargs_in_signature(
    fn: Callable, 
    kwargs: dict
) -> dict[str, str]:
    return {
        key: key for key in signature(fn).parameters if key in kwargs
    }


def ensure_path(
    path: TemporaryDirectory | str | Path
) -> Path:
    return \
        Path(path) \
            if not isinstance(
                path, 
                TemporaryDirectory
            ) else Path(path.name)


def rmtree(dpath):
    dpath = Path(dpath)

    def onerror(func, path, exc_info):
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
    
    shutil.rmtree(dpath, onerror=onerror)