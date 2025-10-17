#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Iterable, Union

from pythonwrench.collections import dump_dict
from torch import Tensor

from torchwrench.nn.functional.activation import log_softmax_multidim, softmax_multidim

from .module import Module


class SoftmaxMultidim(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.activation.softmax_multidim`.
    """

    def __init__(
        self,
        dims: Union[Iterable[int], None] = (-1,),
    ) -> None:
        super().__init__()
        self.dims = dims

    def forward(
        self,
        input: Tensor,
    ) -> Tensor:
        return softmax_multidim(input, dims=self.dims)

    def extra_repr(self) -> str:
        return dump_dict(dims=self.dims)


class LogSoftmaxMultidim(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.activation.softmax_multidim`.
    """

    def __init__(
        self,
        dims: Union[Iterable[int], None] = (-1,),
    ) -> None:
        super().__init__()
        self.dims = dims

    def forward(
        self,
        input: Tensor,
    ) -> Tensor:
        return log_softmax_multidim(input, dims=self.dims)

    def extra_repr(self) -> str:
        return dump_dict(dims=self.dims)
