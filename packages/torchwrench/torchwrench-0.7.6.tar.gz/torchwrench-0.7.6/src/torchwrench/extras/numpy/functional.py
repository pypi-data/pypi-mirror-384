#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Iterable, List, Literal, Tuple, Union, overload

import torch
from pythonwrench import (
    BuiltinScalar,
    function_alias,
    get_current_fn_name,
    is_builtin_scalar,
    prod,
    reduce_and,
    reduce_or,
)
from pythonwrench.semver import Version
from torch import Tensor
from typing_extensions import TypeGuard

from torchwrench.core.make import DeviceLike, DTypeLike, as_device, as_dtype
from torchwrench.extras.numpy.definitions import NumpyNumberLike, NumpyScalarLike, np


def to_ndarray(
    x: Union[Tensor, np.ndarray, Iterable, BuiltinScalar],
    *,
    dtype: Union[str, np.dtype, None] = None,
    force: bool = False,
) -> np.ndarray:
    """Convert input to numpy array. Works with any arbitrary object."""
    if isinstance(x, Tensor):
        return tensor_to_ndarray(x, dtype=dtype, force=force)
    else:
        return np.array(x, dtype=dtype)  # type: ignore


def tensor_to_ndarray(
    x: Tensor,
    *,
    dtype: Union[str, np.dtype, None] = None,
    force: bool = False,
) -> np.ndarray:
    """Convert PyTorch tensor to numpy array."""
    if Version(str(torch.__version__)) >= Version("1.13.0"):
        kwargs = dict(force=force)
    elif not force:
        kwargs = dict()
    else:
        msg = f"Invalid argument {force=} for {get_current_fn_name()}. (expected True because torch version is below 1.13)"
        raise ValueError(msg)

    x_arr: np.ndarray = x.detach().cpu().numpy(**kwargs)
    if dtype is not None:  # supports older numpy version
        x_arr = x_arr.astype(dtype=dtype)  # type: ignore
    return x_arr


def ndarray_to_tensor(
    x: Union[np.ndarray, np.number],
    *,
    device: DeviceLike = None,
    dtype: DTypeLike = None,
) -> Tensor:
    """Convert numpy array to PyTorch tensor."""
    device = as_device(device)
    dtype = as_dtype(dtype)
    return torch.from_numpy(x).to(dtype=dtype, device=device)


def numpy_view_as_real(x: np.ndarray) -> np.ndarray:
    """Convert complex array to float array.

    Args:
        x: The input complex array of any shape (...,)
    Returns:
        x_real: The same data in a float array of shape (..., 2)
    """
    assert numpy_is_complex(x)
    float_dtype = numpy_complex_dtype_to_float_dtype(x.dtype)
    if x.ndim > 0:
        return x.view(float_dtype).reshape(*x.shape, 2)
    else:
        # note: rebuild array here because view does not work on 0d arrays
        return np.array([x.real, x.imag], dtype=float_dtype)  # type: ignore


def numpy_complex_dtype_to_float_dtype(dtype: np.dtype) -> np.dtype:
    """Returns the associated float dtype from complex dtype. If input dtype is not complex, it just returns the same dtype."""
    return np.empty((0,), dtype=dtype).real.dtype  # type: ignore


def numpy_view_as_complex(x: np.ndarray) -> np.ndarray:
    """Convert complex array to float array.

    Args:
        x: The input float array of any shape (..., 2)
    Returns:
        x_real: The same data in a complex array of shape (...,)
    """
    assert not numpy_is_complex(x)
    return x[..., 0] + x[..., 1] * 1j


def numpy_is_floating_point(x: Union[np.ndarray, np.generic]) -> bool:
    return x.dtype.kind == "f"


def numpy_is_complex(x: Union[np.ndarray, np.generic]) -> bool:
    return np.iscomplexobj(x)


def numpy_is_complex_dtype(dtype: np.dtype) -> bool:
    return np.iscomplexobj(np.empty((0,), dtype=dtype))


def is_numpy_bool_array(x: Any) -> TypeGuard[Union[np.bool_, np.ndarray]]:
    return isinstance(x, (np.generic, np.ndarray)) and x.dtype.kind == "b"


def is_numpy_str_array(x: Any) -> TypeGuard[Union[np.str_, np.ndarray]]:
    return isinstance(x, (np.generic, np.ndarray)) and x.dtype.kind in ("U", "S")


def is_numpy_integral_array(x: Any) -> TypeGuard[Union[np.ndarray, np.generic]]:
    return isinstance(x, (np.generic, np.ndarray)) and issubclass(x.dtype, np.integer)


def is_numpy_number_like(x: Any) -> TypeGuard[NumpyNumberLike]:
    """Returns True if x is an instance of a numpy number type, a np.bool_ or a zero-dimensional numpy array.
    If numpy is not installed, this function always returns False.
    """
    return isinstance(x, (np.number, np.bool_)) or (
        isinstance(x, np.ndarray) and x.ndim == 0 and np.issubdtype(x.dtype, np.number)
    )


def is_numpy_scalar_like(x: Any) -> TypeGuard[NumpyScalarLike]:
    """Returns True if x is an instance of a numpy number type or a zero-dimensional numpy array.
    If numpy is not installed, this function always returns False.
    """
    return isinstance(x, np.generic) or (isinstance(x, np.ndarray) and x.ndim == 0)


def numpy_topk(
    x: np.ndarray,
    k: int,
    dim: int = -1,
    largest: bool = True,
    sorted: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    x_pt = ndarray_to_tensor(x)
    values, indices = x_pt.topk(k=k, dim=dim, largest=largest, sorted=sorted)
    values = tensor_to_ndarray(values)
    indices = tensor_to_ndarray(indices)
    return values, indices


def numpy_item(x: Union[np.ndarray, np.generic, BuiltinScalar]) -> np.generic:
    if isinstance(x, np.generic):
        return x
    if is_builtin_scalar(x, strict=True):
        return np.array(x)[()]  # type: ignore
    if prod(x.shape) != 1:
        msg = f"Invalid argument shape {x.shape=}. (expected nd-array with 1 element)"
        raise ValueError(msg)

    indices = tuple([0] * x.ndim)
    return x[indices]  # type: ignore


@overload
def numpy_all_eq(
    x: Union[np.generic, np.ndarray],
    dim: Literal[None] = None,
) -> bool: ...


@overload
def numpy_all_eq(
    x: Union[np.generic, np.ndarray],
    dim: int,
) -> np.ndarray: ...


def numpy_all_eq(
    x: Union[np.generic, np.ndarray],
    dim: Union[int, None] = None,
) -> Union[bool, np.ndarray]:
    if isinstance(x, np.generic):
        return True

    elif dim is None:
        if x.ndim == 0 or prod(x.shape) == 0:
            return True
        else:
            return (x.flat[0] == x.flat[1:]).all()

    else:
        indexer: List[Union[int, slice, None]] = [slice(None) for _ in range(x.ndim)]
        indexer[dim] = 0
        indexer.insert(dim + 1, None)
        indexer_tuple = tuple(indexer)
        return (x == x[indexer_tuple]).all(dim)


def numpy_all_ne(x: Union[np.generic, np.ndarray]) -> bool:
    return len(np.unique(x)) == x.size


@function_alias(reduce_and)
def logical_and_lst(*args, **kwargs): ...


@function_alias(reduce_or)
def logical_or_lst(*args, **kwargs): ...


@function_alias(to_ndarray)
def to_numpy(*args, **kwargs): ...


@function_alias(tensor_to_ndarray)
def tensor_to_numpy(*args, **kwargs): ...


@function_alias(ndarray_to_tensor)
def numpy_to_tensor(*args, **kwargs): ...
