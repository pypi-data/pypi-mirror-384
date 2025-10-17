#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torchwrench.core.packaging import _PANDAS_AVAILABLE

if not _PANDAS_AVAILABLE:
    from torchwrench.extras.pandas import _pandas_fallback as pd

else:
    import pandas as pd


__all__ = [
    "_PANDAS_AVAILABLE",
    "pd",
]
