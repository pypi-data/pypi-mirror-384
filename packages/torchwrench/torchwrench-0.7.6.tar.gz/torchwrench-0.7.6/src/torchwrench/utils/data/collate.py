#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from typing import Any, Dict, List, Optional, TypeVar

import torch
from pythonwrench.collections.collections import KeyMode, list_dict_to_dict_list
from pythonwrench.re import PatternListLike, match_patterns

from torchwrench.nn.functional.padding import pad_and_stack_rec
from torchwrench.nn.functional.predicate import is_convertible_to_tensor, is_stackable

K = TypeVar("K")
V = TypeVar("V")


class CollateDict:
    """Collate object for :class:`~torch.utils.data.dataloader.DataLoader`.

    Merge lists in dicts into a single dict of lists. No padding is applied.
    """

    def __init__(self, key_mode: KeyMode = "same") -> None:
        super().__init__()
        self.key_mode: KeyMode = key_mode

    def __call__(self, batch_lst: List[Dict[K, V]]) -> Dict[K, List[V]]:
        result = list_dict_to_dict_list(
            batch_lst,
            key_mode=self.key_mode,
        )
        return result  # type: ignore


class AdvancedCollateDict:
    """Advanced collate object for :class:`~torch.utils.data.dataloader.DataLoader`.

    Merge lists in dicts into a single dict of lists.
    Audio will be padded if a fill pad_values is given in `__init__`.

    .. code-block:: python
        :caption:  Example

        >>> collate = AdvancedCollate({"audio": 0.0})
        >>> loader = DataLoader(..., collate_fn=collate)
        >>> next(iter(loader))
        ... {"audio": tensor([[...]]), ...}

    """

    def __init__(
        self,
        pad_values: Optional[Dict[str, Any]] = None,
        include_keys: Optional[PatternListLike] = None,
        exclude_keys: Optional[PatternListLike] = None,
        key_mode: KeyMode = "same",
    ) -> None:
        """Collate list of dict into a dict of list WITH auto-padding for given keys."""
        if pad_values is None:
            pad_values = {}

        super().__init__()
        self.pad_values = pad_values
        self.include_keys = include_keys
        self.exclude_keys = exclude_keys
        self.key_mode: KeyMode = key_mode

    def __call__(self, batch_lst: List[Dict[str, Any]]) -> Dict[str, Any]:
        batch_dict = list_dict_to_dict_list(
            batch_lst,
            key_mode=self.key_mode,
        )
        batch_keys = [
            k
            for k in batch_dict.keys()
            if match_patterns(
                k,
                self.include_keys,
                exclude=self.exclude_keys,
                match_fn=re.match,
            )
        ]
        batch_dict = {k: batch_dict[k] for k in batch_keys}
        result = {}

        for key, values in batch_dict.items():
            if key in self.pad_values:
                values = pad_and_stack_rec(values, self.pad_values[key])
            elif is_stackable(values):
                values = torch.stack(values)
            elif is_convertible_to_tensor(values):
                values = torch.as_tensor(values)

            result[key] = values

        return result
