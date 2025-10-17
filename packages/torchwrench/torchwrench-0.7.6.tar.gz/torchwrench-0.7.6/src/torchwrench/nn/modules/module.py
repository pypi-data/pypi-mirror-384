#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torchwrench.core.config import _REPLACE_MODULE_CLASSES
from torchwrench.nn.modules._mixins import EModule  # noqa: F401

if _REPLACE_MODULE_CLASSES:
    from torchwrench.nn.modules._mixins import EModule as Module  # noqa: F401
else:
    from torch.nn import Module  # noqa: F401
