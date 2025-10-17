#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Any, Generic, Iterable, List, Tuple, TypeVar, Union, overload

import pythonwrench as pw
import torch
from pythonwrench.typing.classes import SupportsGetitemLen
from torch.utils.data.dataset import Dataset
from typing_extensions import TypeAlias

from torchwrench.extras.numpy import np
from torchwrench.extras.numpy.functional import is_numpy_bool_array
from torchwrench.nn.functional.transform import as_tensor
from torchwrench.types._typing import BoolTensor1D, Tensor1D, TensorOrArray
from torchwrench.types.guards import is_number_like, is_tensor_or_array
from torchwrench.utils.data.dataset import Wrapper

T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)

Indices: TypeAlias = Union[
    Iterable[bool], Iterable[int], None, slice, Tensor1D, np.ndarray
]


class DatasetSlicer(Generic[T], ABC, Dataset[T]):
    def __init__(
        self,
        *,
        add_slice_support: bool = True,
        add_indices_support: bool = True,
        add_mask_support: bool = True,
        add_none_support: bool = True,
    ) -> None:
        Dataset.__init__(self)
        self._add_slice_support = add_slice_support
        self._add_indices_support = add_indices_support
        self._add_mask_support = add_mask_support
        self._add_none_support = add_none_support

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_item(self, idx, /, *args, **kwargs) -> Any:
        raise NotImplementedError

    @overload
    def __getitem__(self, idx: int, /) -> T:  # type: ignore
        ...

    @overload
    def __getitem__(self, idx: Indices, /) -> List[T]:  # type: ignore
        ...

    @overload
    def __getitem__(self, idx: Tuple[Any, ...], /) -> Any:  # type: ignore
        ...

    def __getitem__(self, idx) -> Any:
        if isinstance(idx, tuple) and len(idx) > 1:
            idx, *args = idx
        else:
            args = ()

        if is_number_like(idx):
            return self.get_item(idx, *args)

        elif isinstance(idx, slice):
            return self.get_items_slice(idx, *args)

        elif (
            pw.isinstance_generic(idx, Iterable[bool])
            or isinstance(idx, BoolTensor1D)
            or (is_numpy_bool_array(idx) and idx.ndim == 1)
        ):
            return self.get_items_mask(idx, *args)

        elif pw.isinstance_generic(idx, Iterable[int]) or is_tensor_or_array(idx):
            return self.get_items_indices(idx, *args)

        elif idx is None:
            return self.get_items_none(idx, *args)

        else:
            raise TypeError(f"Invalid argument type {type(idx)=} with {args=}.")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def get_items_indices(
        self,
        indices: Union[Iterable[int], TensorOrArray],
        *args,
    ) -> List[T]:
        if self._add_indices_support:
            return [self.get_item(idx, *args) for idx in indices]
        else:
            return self.get_item(indices, *args)

    def get_items_mask(
        self,
        mask: Union[Iterable[bool], TensorOrArray],
        *args,
    ) -> List[T]:
        if self._add_mask_support:
            mask = as_tensor(mask, dtype=torch.bool)
            if len(mask) > 0 and len(mask) != len(self):  # type: ignore
                msg = f"Invalid mask size {len(mask)}. (expected {len(self)})"
                raise ValueError(msg)

            indices = torch.where(mask)[0]
            return self.get_items_indices(indices, *args)
        else:
            return self.get_item(mask, *args)

    def get_items_slice(
        self,
        slice_: slice,
        *args,
    ) -> List[T]:
        if self._add_slice_support:
            return self.get_items_indices(range(len(self))[slice_], *args)
        else:
            return self.get_item(slice_, *args)

    def get_items_none(
        self,
        none: None,
        *args,
    ) -> List[T]:
        if self._add_none_support:
            return self.get_items_slice(slice(None), *args)
        else:
            return self.get_item(none, *args)


class DatasetSlicerWrapper(Generic[T], DatasetSlicer[T], Wrapper[T]):
    def __init__(
        self,
        dataset: SupportsGetitemLen[T],
        *,
        add_slice_support: bool = True,
        add_indices_support: bool = True,
        add_mask_support: bool = True,
        add_none_support: bool = True,
    ) -> None:
        """Wrap a sequence to support slice, indices and mask arguments types."""
        DatasetSlicer.__init__(
            self,
            add_slice_support=add_slice_support,
            add_indices_support=add_indices_support,
            add_mask_support=add_mask_support,
            add_none_support=add_none_support,
        )
        Wrapper.__init__(self, dataset)

    def __len__(self) -> int:
        return len(self.dataset)

    def get_item(self, idx: int, *args) -> T:
        # note: we need to split calls here, because self.dataset[idx] give an int as argument while self.dataset[idx, *args] always gives a tuple even if args == ()
        if len(args) == 0:
            return self.dataset[idx]
        else:
            # equivalent to self.dataset[idx, *args], but only in recent python versions
            return self.dataset.__getitem__((idx,) + args)
