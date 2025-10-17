#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
from pathlib import Path

from pythonwrench.functools import function_alias
from torch.hub import get_dir


def get_tmp_dir(mkdir: bool = False, make_parents: bool = True) -> Path:
    """Returns torchwrench temporary directory.

    Defaults is `/tmp/torchwrench`.
    Can be overriden with 'TORCHWRENCH_TMPDIR' environment variable.
    """
    default = tempfile.gettempdir()
    result = os.getenv("TORCHWRENCH_TMPDIR", default)
    result = Path(result).joinpath("torchwrench").resolve().expanduser()
    if mkdir:
        result.mkdir(parents=make_parents, exist_ok=True)
    return result


def get_cache_dir(mkdir: bool = False, make_parents: bool = True) -> Path:
    """Returns torchwrench cache directory for storing checkpoints, data and models.

    Defaults is `~/.cache/torchwrench`.
    Can be overriden with 'TORCHWRENCH_CACHEDIR' environment variable.
    """
    default = Path.home().joinpath(".cache", "torchwrench")
    result = os.getenv("TORCHWRENCH_CACHEDIR", default)
    result = Path(result).resolve().expanduser()
    if mkdir:
        result.mkdir(parents=make_parents, exist_ok=True)
    return result


@function_alias(get_dir)
def get_torch_cache_dir(*args, **kwargs): ...
