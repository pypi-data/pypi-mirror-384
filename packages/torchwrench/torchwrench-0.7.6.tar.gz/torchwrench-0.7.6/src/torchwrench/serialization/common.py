#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from pathlib import Path
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    TypeVar,
    Union,
)

import torch
from pythonwrench.cast import as_builtin, register_as_builtin_fn
from torch import Tensor

from torchwrench.core.packaging import (
    _H5PY_AVAILABLE,
    _NUMPY_AVAILABLE,
    _OMEGACONF_AVAILABLE,
    _PANDAS_AVAILABLE,
    _SAFETENSORS_AVAILABLE,
    _TORCHAUDIO_AVAILABLE,
    _YAML_AVAILABLE,
)

T = TypeVar("T")

pylog = logging.getLogger(__name__)

SavingBackend = Literal[
    "csv",
    "json",
    "h5py",
    "numpy",
    "pickle",
    "safetensors",
    "torch",
    "torchaudio",
    "yaml",
]

# Note: order matter here: last extension of a backend is the default/recommanded one
PATTERN_TO_BACKEND: Dict[str, SavingBackend] = {
    r"^.+\.tsv$": "csv",
    r"^.+\.csv$": "csv",
    r"^.+\.json$": "json",
    r"^.+\.pkl$": "pickle",
    r"^.+\.pickle$": "pickle",
    r"^.+\.torch$": "torch",
    r"^.+\.ckpt$": "torch",
    r"^.+\.pt$": "torch",
}

if _H5PY_AVAILABLE:
    PATTERN_TO_BACKEND.update(
        {
            r"^.+\.h5$": "h5py",
            r"^.+\.hdf$": "h5py",
            r"^.+\.hdf5$": "h5py",
        }
    )


if _NUMPY_AVAILABLE:
    import numpy as np

    PATTERN_TO_BACKEND.update(
        {
            r"^.+\.npz$": "numpy",
            r"^.+\.npy$": "numpy",
        }
    )

if _SAFETENSORS_AVAILABLE:
    PATTERN_TO_BACKEND.update(
        {
            r"^.+\.safetensors$": "safetensors",
        }
    )

if _TORCHAUDIO_AVAILABLE:
    PATTERN_TO_BACKEND.update(
        {
            r"^.+\.mp3$": "torchaudio",
            r"^.+\.wav$": "torchaudio",
            r"^.+\.aac$": "torchaudio",
            r"^.+\.ogg$": "torchaudio",
            r"^.+\.flac$": "torchaudio",
        }
    )

if _YAML_AVAILABLE:
    PATTERN_TO_BACKEND.update(
        {
            r".+\.yml$": "yaml",
            r".+\.yaml$": "yaml",
        }
    )


def _fpath_to_saving_backend(
    fpath: Union[str, Path],
    verbose: int = 0,
) -> SavingBackend:
    fname = Path(fpath).name

    saving_backend: Optional[SavingBackend] = None
    for pattern, backend in PATTERN_TO_BACKEND.items():
        if re.match(pattern, fname) is not None:
            saving_backend = backend
            break

    if saving_backend is None:
        msg = f"Unknown file pattern '{fname}'. (expected one of {tuple(PATTERN_TO_BACKEND.keys())} or specify the backend argument with `to.load(..., saving_backend=\"backend\")`)"
        raise ValueError(msg)

    if verbose >= 2:
        msg = f"Loading file '{str(fpath)}' using {saving_backend=}."
        pylog.debug(msg)
    return saving_backend


BACKEND_TO_PATTERN: Dict[SavingBackend, str] = {
    backend: ext for ext, backend in PATTERN_TO_BACKEND.items()
}


@register_as_builtin_fn(Tensor)
def _tensor_to_builtin(x: Tensor) -> Any:
    return x.tolist()


@register_as_builtin_fn(torch.dtype)
def _torch_dtype_to_builtin(x: torch.dtype) -> Any:
    return str(x)


if _NUMPY_AVAILABLE:
    import numpy as np

    @register_as_builtin_fn(np.ndarray)
    def _np_ndarray_to_builtin(x: np.ndarray) -> Any:
        return x.tolist()

    @register_as_builtin_fn(np.generic)
    def _np_generic_to_builtin(x: np.generic) -> Any:
        return x.item()

    @register_as_builtin_fn(np.dtype)
    def _np_dtype_to_builtin(x: np.dtype) -> Any:
        return str(x)


if _OMEGACONF_AVAILABLE:
    from omegaconf import DictConfig, ListConfig, OmegaConf  # type: ignore

    @register_as_builtin_fn((DictConfig, ListConfig))
    def _omegaconf_to_builtin(x: Union[DictConfig, ListConfig]) -> Any:
        return as_builtin(OmegaConf.to_container(x, resolve=False, enum_to_str=True))  # type: ignore


if _PANDAS_AVAILABLE:
    import pandas as pd

    @register_as_builtin_fn(pd.DataFrame)
    def _dataframe_to_builtin(x: pd.DataFrame) -> Any:
        return as_builtin(x.to_dict("list"))
