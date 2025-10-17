#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Union

from torch import Tensor

from torchwrench.core.make import DeviceLike, DTypeLike
from torchwrench.core.packaging import _NUMPY_AVAILABLE
from torchwrench.extras.numpy.definitions import np
from torchwrench.extras.numpy.functional import (
    ndarray_to_tensor,
    tensor_to_ndarray,
    to_ndarray,
)
from torchwrench.nn.modules.module import Module


class ToNDArray(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.numpy.to_ndarray`.
    """

    def __init__(
        self,
        *,
        dtype: Union[str, np.dtype, None] = None,
        force: bool = False,
    ) -> None:
        if not _NUMPY_AVAILABLE:
            msg = f"Cannot use {self.__class__.__name__} because numpy dependancy is not installed."
            raise RuntimeError(msg)

        super().__init__()
        self.dtype = dtype
        self.force = force

    def forward(self, x: Union[Tensor, np.ndarray, list]) -> np.ndarray:
        return to_ndarray(x, dtype=self.dtype, force=self.force)


class TensorToNDArray(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.numpy.tensor_to_ndarray`.
    """

    def __init__(
        self,
        *,
        dtype: Union[str, np.dtype, None] = None,
        force: bool = False,
    ) -> None:
        if not _NUMPY_AVAILABLE:
            msg = f"Cannot use {self.__class__.__name__} because numpy dependancy is not installed."
            raise RuntimeError(msg)

        super().__init__()
        self.dtype = dtype
        self.force = force

    def forward(self, x: Tensor) -> np.ndarray:
        return tensor_to_ndarray(x, dtype=self.dtype, force=self.force)


class NDArrayToTensor(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.numpy.ndarray_to_tensor`.
    """

    def __init__(
        self,
        *,
        device: DeviceLike = None,
        dtype: DTypeLike = None,
    ) -> None:
        if not _NUMPY_AVAILABLE:
            msg = f"Cannot use {self.__class__.__name__} because numpy dependancy is not installed."
            raise RuntimeError(msg)

        super().__init__()
        self.device = device
        self.dtype = dtype

    def forward(self, x: np.ndarray) -> Tensor:
        return ndarray_to_tensor(x, dtype=self.dtype, device=self.device)
