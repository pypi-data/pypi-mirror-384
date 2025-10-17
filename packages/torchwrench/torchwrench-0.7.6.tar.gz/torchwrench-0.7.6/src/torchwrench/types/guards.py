#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any

import torch
from pythonwrench.typing import (
    is_builtin_number,
    is_builtin_scalar,
)
from torch import Tensor
from typing_extensions import TypeGuard, TypeIs

from torchwrench.core.make import DTypeLike, as_dtype
from torchwrench.extras.numpy import is_numpy_number_like, is_numpy_scalar_like, np

from ._typing import (
    IntegralTensor,
    NumberLike,
    ScalarLike,
    Tensor0D,
    TensorOrArray,
)


def is_number_like(x: Any) -> TypeGuard[NumberLike]:
    """Returns True if input is a scalar number.

    Accepted numbers-like objects are:
    - Python numbers (int, float, bool, complex)
    - Numpy zero-dimensional arrays
    - Numpy numbers
    - PyTorch zero-dimensional tensors
    """
    return is_builtin_number(x) or is_numpy_number_like(x) or isinstance(x, Tensor0D)


def is_scalar_like(x: Any) -> TypeGuard[ScalarLike]:
    """Returns True if input is a scalar number.

    Accepted scalar-like objects are:
    - Python scalars like (int, float, bool, complex, None, str, bytes)
    - Numpy zero-dimensional arrays
    - Numpy generic
    - PyTorch zero-dimensional tensors
    """
    return is_builtin_scalar(x) or is_numpy_scalar_like(x) or isinstance(x, Tensor0D)


def is_tensor_or_array(x: Any) -> TypeIs[TensorOrArray]:
    return isinstance(x, (Tensor, np.ndarray))


def is_integral_dtype(dtype: DTypeLike) -> bool:
    dtype = as_dtype(dtype)
    return isinstance(torch.empty((0,), dtype=dtype), IntegralTensor)
