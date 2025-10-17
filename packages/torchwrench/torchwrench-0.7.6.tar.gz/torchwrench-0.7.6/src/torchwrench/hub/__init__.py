#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torch.hub import *  # type: ignore

from .download import download_file
from .paths import get_cache_dir, get_tmp_dir
from .registry import RegistryEntry, RegistryHub
