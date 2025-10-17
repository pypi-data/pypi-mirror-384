#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any

from pythonwrench.importlib import Placeholder


class DynamicItemDataset(Placeholder):
    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, *args, **kwargs) -> Any:
        raise NotImplementedError
