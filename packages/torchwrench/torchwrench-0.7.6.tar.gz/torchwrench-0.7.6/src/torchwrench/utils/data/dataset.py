#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import abstractmethod
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Optional,
    TypeVar,
    Union,
)

from pythonwrench.collections import is_sorted
from pythonwrench.typing.classes import (
    SupportsGetitemIterLen,
    SupportsGetitemLen,
    SupportsIterLen,
)
from torch.utils.data.dataset import Dataset, IterableDataset
from torch.utils.data.dataset import IterableDataset as TorchIterableDataset
from torch.utils.data.dataset import Subset as TorchSubset

from torchwrench.types.tensor_subclasses import LongTensor1D

T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)

SizedDatasetLike = SupportsGetitemLen

T_Dataset = TypeVar("T_Dataset", bound=Dataset)
T_SizedDatasetLike = TypeVar("T_SizedDatasetLike", bound=SupportsGetitemLen)
T_SupportsIterLenDataset = TypeVar(
    "T_SupportsIterLenDataset",
    bound=SupportsGetitemIterLen,
)


class EmptyDataset(Dataset[None]):
    """Dataset placeholder. Raises StopIteration if __getitem__ is called."""

    def __getitem__(self, idx, /) -> None:  # type: ignore
        raise StopIteration

    def __len__(self) -> int:
        return 0


class _WrapperBase(Generic[T], Dataset[T]):
    def __init__(self, dataset: Any) -> None:
        Dataset.__init__(self)
        self.dataset = dataset

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    def unwrap(self, recursive: bool = True) -> Union[SupportsGetitemLen, Dataset]:
        dataset = self.dataset
        continue_ = recursive and isinstance(
            dataset, (_WrapperBase, TorchSubset, TorchIterableDataset)
        )
        while continue_:
            dataset = dataset.dataset  # type: ignore
            continue_ = isinstance(dataset, _WrapperBase)
        return dataset  # type: ignore

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.dataset)})"


class Wrapper(Generic[T], _WrapperBase[T]):
    @abstractmethod
    def __getitem__(self, idx, /) -> T:  # type: ignore
        raise NotImplementedError


class IterableWrapper(Generic[T], IterableDataset[T], _WrapperBase[T]):
    def __init__(
        self, dataset: Union[SupportsGetitemLen[T], SupportsIterLen[T]]
    ) -> None:
        IterableDataset.__init__(self)
        _WrapperBase.__init__(self, dataset)
        self.dataset: Union[SupportsGetitemLen[T], SupportsIterLen[T]]

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        raise NotImplementedError

    def _get_dataset_iter(self) -> Iterator[T]:
        if hasattr(self.dataset, "__iter__"):
            it = iter(self.dataset)
        else:
            it = (self.dataset[i] for i in range(len(self.dataset)))  # type: ignore
        return it


class TransformWrapper(Generic[T, U], Wrapper[T]):
    def __init__(
        self,
        dataset: SupportsGetitemLen[T],
        transform: Optional[Callable[[T], U]],
        condition: Optional[Callable[[T, int], bool]] = None,
    ) -> None:
        super().__init__(dataset)
        self._transform = transform
        self._condition = condition
        self.dataset: SupportsGetitemLen[T]

    def __getitem__(self, idx) -> Union[T, U]:  # type: ignore
        assert isinstance(idx, int)
        item = self.dataset[idx]
        if self._transform is not None and (
            self._condition is None or self._condition(item, idx)
        ):
            item = self._transform(item)
        return item

    def __len__(self) -> int:
        return len(self.dataset)

    @property
    def transform(self) -> Optional[Callable[[T], U]]:
        return self._transform

    @property
    def condition(self) -> Optional[Callable[[T, int], bool]]:
        return self._condition


class IterableTransformWrapper(IterableWrapper[T], Generic[T, U]):
    def __init__(
        self,
        dataset: Union[SupportsGetitemLen[T], SupportsIterLen[T]],
        transform: Optional[Callable[[T], U]],
        condition: Optional[Callable[[T, int], bool]] = None,
    ) -> None:
        super().__init__(dataset)
        self._transform = transform
        self._condition = condition

    def __iter__(self) -> Iterator[Union[T, U]]:  # type: ignore
        it = super()._get_dataset_iter()
        for i, item in enumerate(it):
            if self._transform is not None and (
                self._condition is None or self._condition(item, i)
            ):
                item = self._transform(item)
            yield item
        return

    def __len__(self) -> int:
        return len(self.dataset)

    @property
    def transform(self) -> Optional[Callable[[T], U]]:
        return self._transform

    @property
    def condition(self) -> Optional[Callable[[T, int], bool]]:
        return self._condition


class IterableSubset(IterableWrapper[T], Generic[T]):
    def __init__(
        self,
        dataset: Union[SupportsGetitemLen[T], SupportsIterLen[T]],
        indices: Union[Iterable[int], LongTensor1D],
    ) -> None:
        if isinstance(indices, LongTensor1D):
            indices = indices.tolist()
        else:
            indices = list(indices)

        if not all(idx >= 0 for idx in indices) or not is_sorted(indices):
            msg = f"Invalid argument {indices=}. (expected a sorted list of positive integers)"
            raise ValueError(msg)

        super().__init__(dataset)
        self._indices = indices

    def __iter__(self) -> Iterator[T]:
        it = super()._get_dataset_iter()

        cur_idx = 0
        item = next(it)

        for idx in self._indices:
            if cur_idx == idx:
                yield item
                continue

            while cur_idx < idx:
                cur_idx += 1
                item = next(it)

            yield item
        return

    def __len__(self) -> int:
        return len(self._indices)


class Subset(Generic[T], TorchSubset[T], Wrapper[T]):
    def __init__(self, dataset: SizedDatasetLike[T], indices: Iterable[int]) -> None:
        indices = list(indices)
        TorchSubset.__init__(self, dataset, indices)  # type: ignore
        Wrapper.__init__(self, dataset)
