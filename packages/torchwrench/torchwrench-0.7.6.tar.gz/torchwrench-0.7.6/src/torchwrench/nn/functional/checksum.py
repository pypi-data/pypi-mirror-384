#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import math
import struct
from typing import Callable, Union

import torch
from pythonwrench.checksum import (
    _cached_checksum_str,
    _checksum_iterable,
    checksum_any,  # noqa: F401
    checksum_bytes,
    checksum_dict,
    checksum_float,
    checksum_list_tuple,
    checksum_str,
    register_checksum_fn,
)
from pythonwrench.inspect import get_fullname
from torch import Tensor, nn

from torchwrench.core.packaging import _NUMPY_AVAILABLE, _PANDAS_AVAILABLE
from torchwrench.extras.numpy import np
from torchwrench.extras.pandas import pd
from torchwrench.nn.functional.predicate import is_complex, is_floating_point


@register_checksum_fn(pd.DataFrame)
def checksum_dataframe(x: pd.DataFrame, **kwargs) -> int:
    if not _PANDAS_AVAILABLE:
        msg = "Cannot call function 'checksum_dataframe' because optional dependency 'pandas' is not installed. Please install it using 'pip install torchwrench[extras]'"
        raise NotImplementedError(msg)

    kwargs["accumulator"] = kwargs.get("accumulator", 0) + _cached_checksum_str(
        get_fullname(x)
    )
    xdict = x.to_dict()
    return checksum_dict(xdict, **kwargs)  # type: ignore


@register_checksum_fn(pd.Series)
def checksum_series(x: pd.Series, **kwargs) -> int:
    if not _PANDAS_AVAILABLE:
        msg = "Cannot call function 'checksum_series' because optional dependency 'pandas' is not installed. Please install it using 'pip install torchwrench[extras]'"
        raise NotImplementedError(msg)

    kwargs["accumulator"] = kwargs.get("accumulator", 0) + _cached_checksum_str(
        get_fullname(x)
    )
    xlist = x.tolist()
    return checksum_list_tuple(xlist, **kwargs)  # type: ignore


@register_checksum_fn((torch.dtype, np.dtype))
def checksum_dtype(x: Union[torch.dtype, np.dtype], **kwargs) -> int:
    kwargs["accumulator"] = kwargs.get("accumulator", 0) + _cached_checksum_str(
        get_fullname(x)
    )
    xstr = str(x)
    return checksum_str(xstr, **kwargs)


@register_checksum_fn(nn.Module)
def checksum_module(
    x: nn.Module,
    *,
    only_trainable: bool = False,
    with_names: bool = False,
    buffers: bool = False,
    training: bool = False,
    **kwargs,
) -> int:
    """Compute a simple checksum over module parameters."""
    training = x.training
    x.train(training)

    if with_names:
        params_it = (
            (n, p)
            for n, p in x.named_parameters()
            if not only_trainable or p.requires_grad  # type: ignore
        )
    else:
        params_it = (
            param
            for param in x.parameters()
            if not only_trainable or param.requires_grad
        )

    if not buffers:
        iterator = params_it
    elif with_names:
        buffers_it = (name_buffer for name_buffer in x.named_buffers())
        iterator = itertools.chain(params_it, buffers_it)
    else:
        buffers_it = (buffer for buffer in x.buffers())
        iterator = itertools.chain(params_it, buffers_it)

    csum = _checksum_iterable(iterator, **kwargs)
    x.train(training)
    return csum


# Intermediate functions
@torch.inference_mode()
@register_checksum_fn(Tensor)
def checksum_tensor(x: Tensor, **kwargs) -> int:
    """Compute a simple checksum of a tensor. Order of values matter for the checksum."""
    return _checksum_tensor_array_like(
        x,
        nan_to_num_fn=torch.nan_to_num,
        **kwargs,
    )


@torch.inference_mode()
@register_checksum_fn((np.ndarray, np.generic))
def checksum_numpy(x: Union[np.ndarray, np.generic], **kwargs) -> int:
    """Compute a simple checksum of a tensor. Order of values matter for the checksum."""
    return _checksum_tensor_array_like(
        x,
        nan_to_num_fn=np.nan_to_num,
        **kwargs,
    )


# Private functions
def _checksum_tensor_array_like(
    x: Union[Tensor, np.ndarray, np.generic],
    *,
    nan_to_num_fn: Callable,
    **kwargs,
) -> int:
    if is_floating_point(x) or is_complex(x):
        nan_csum = checksum_float(math.nan, **kwargs)
        neginf_csum = checksum_float(-math.inf, **kwargs)
        posinf_csum = checksum_float(math.inf, **kwargs)
        x = nan_to_num_fn(
            x,
            nan=nan_csum,
            neginf=neginf_csum,
            posinf=posinf_csum,
        )

    # Ensure that accumulator exists
    kwargs["accumulator"] = kwargs.get("accumulator", 0)

    kwargs["accumulator"] += checksum_dtype(x.dtype, **kwargs)
    kwargs["accumulator"] += _checksum_iterable(x.shape, **kwargs)
    kwargs["accumulator"] += _cached_checksum_str(get_fullname(x))

    if isinstance(x, (np.ndarray, np.generic)):
        xbytes = x.tobytes()
        csum = checksum_bytes(xbytes, **kwargs)
    elif isinstance(x, Tensor):
        if _NUMPY_AVAILABLE:
            xbytes = x.detach().cpu().numpy().tobytes()
        else:
            xbytes = _serialize_tensor_to_bytes(x)
        csum = checksum_bytes(xbytes, **kwargs)
    else:
        msg = f"Invalid argument type {type(x)}. (expected ndarray or Tensor)"
        raise TypeError(msg)

    return csum


def _serialize_tensor_to_bytes(x: Tensor) -> bytes:
    """Convert tensor data to bytes, but very slow compare to numpy' tobytes() method."""
    x = x.view(torch.int8).view(-1)
    xbytes = struct.pack(f"{len(x)}b", *x)
    return xbytes
