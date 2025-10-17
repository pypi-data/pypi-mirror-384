#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any

from pythonwrench.importlib import Placeholder
from pythonwrench.inspect import get_current_fn_name


class DataFrame(Placeholder):
    def __getitem__(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __setitem__(self, *args, **kwargs) -> Any:
        raise NotImplementedError


class Series(Placeholder): ...


class RangeIndex(Placeholder): ...


class Index(Placeholder): ...


def read_csv(*args, **kwargs) -> DataFrame:
    msg = f"Cannot call function '{get_current_fn_name()}' because optional dependency 'pandas' is not installed. Please install it using 'pip install torchwrench[extras]'"
    raise NotImplementedError(msg)
