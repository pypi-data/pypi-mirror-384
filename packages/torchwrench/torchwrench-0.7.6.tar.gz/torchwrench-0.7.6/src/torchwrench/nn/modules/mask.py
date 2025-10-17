#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Iterable, Union

from pythonwrench.collections import dump_dict
from torch import Tensor

from torchwrench.nn.functional.mask import masked_mean, masked_sum

from .module import Module


class MaskedMean(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.mask.masked_mean`.
    """

    def __init__(self, dim: Union[None, int, Iterable[int]] = None) -> None:
        super().__init__()
        self.dim = dim

    def forward(self, tensor: Tensor, non_pad_mask: Tensor) -> Tensor:
        reduced = masked_mean(tensor, non_pad_mask, dim=self.dim)
        return reduced

    def extra_repr(self) -> str:
        return dump_dict(
            dict(
                dim=self.dim,
            ),
            ignore_lst=(None,),
        )


class MaskedSum(Module):
    """
    For more information, see :func:`~torchwrench.nn.functional.mask.masked_sum`.
    """

    def __init__(self, dim: Union[None, int, Iterable[int]] = None) -> None:
        super().__init__()
        self.dim = dim

    def forward(self, tensor: Tensor, non_pad_mask: Tensor) -> Tensor:
        reduced = masked_sum(tensor, non_pad_mask, dim=self.dim)
        return reduced

    def extra_repr(self) -> str:
        return dump_dict(
            dict(
                dim=self.dim,
            ),
            ignore_lst=(None,),
        )
