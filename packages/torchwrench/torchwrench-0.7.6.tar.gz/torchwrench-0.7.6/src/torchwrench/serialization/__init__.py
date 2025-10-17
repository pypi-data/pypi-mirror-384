#!/usr/bin/env python
# -*- coding: utf-8 -*-

from torch.serialization import *  # type: ignore

from .common import as_builtin
from .csv import dump_csv, load_csv
from .dump_fn import dump, save
from .json import dump_json, load_json
from .load_fn import load
from .pickle import dump_pickle, load_pickle
from .torch import dump_torch, load_torch
