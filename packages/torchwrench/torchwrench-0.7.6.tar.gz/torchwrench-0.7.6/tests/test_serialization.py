#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import unittest
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple, get_args
from unittest import TestCase

import pythonwrench as pw
import torch

import torchwrench as tw
from torchwrench.core.packaging import (
    _NUMPY_AVAILABLE,
    _PANDAS_AVAILABLE,
    _SAFETENSORS_AVAILABLE,
    _YAML_AVAILABLE,
)
from torchwrench.hub.paths import get_tmp_dir
from torchwrench.nn.functional import deep_equal
from torchwrench.serialization.common import (
    SavingBackend,
    _fpath_to_saving_backend,
    as_builtin,
)


class TestSaving(TestCase):
    def test_examples(self) -> None:
        x = [
            [
                torch.arange(3)[None],
                "a",
                Path("./path"),
                Counter(["a", "b", "a", "c", "a"]),
                (),
            ],
        ]
        expected = [[[list(range(3))], "a", "path", {"a": 3, "b": 1, "c": 1}, []]]

        if _PANDAS_AVAILABLE:
            import pandas as pd

            df = pd.DataFrame({"a": [1, 2]})

            x += [
                df,
                df["a"],
            ]
            expected += [
                {"a": [1, 2]},
                [1, 2],
            ]

        result = as_builtin(x)
        assert result == expected, f"{result=}; {expected=}"

    def test_as_builtin(self) -> None:
        assert as_builtin(tw.arange(10)) == list(range(10))

        with self.assertRaises(TypeError):
            as_builtin(self)

    def test_detect_backend(self) -> None:
        tests: List[Tuple[str, str]] = [
            ("test.json", "json"),
            ("test.yaml.json", "json"),
        ]
        if _YAML_AVAILABLE:
            tests += [
                ("test.json.yaml", "yaml"),
                ("test.yml", "yaml"),
            ]

        for fpath, expected_backend in tests:
            backend = _fpath_to_saving_backend(fpath)
            assert backend == expected_backend

    def test_csv(self) -> None:
        data = {
            "a": [pw.randstr(10) for _ in range(100)],
            "b": [pw.randstr(10) for _ in range(100)],
        }

        fpath = get_tmp_dir().joinpath("tmp.csv")
        tw.dump_csv(data, fpath)
        result = tw.load_csv(fpath, orient="dict")

        assert result == data

        if _NUMPY_AVAILABLE and _PANDAS_AVAILABLE:
            import numpy as np

            n = 10
            data_matrix = dict(zip(pw.randstr(n), tw.rand(n, 100).numpy()))

            tw.dump_csv(data_matrix, fpath, backend="pandas")
            result = tw.load_csv(fpath, orient="dict", backend="pandas")

            assert all(np.allclose(v, result[k]) for k, v in data_matrix.items())

    def test_save_load(self) -> None:
        n = 1
        data_tensors = {
            "arange": tw.arange(n),
            "full": tw.full((n, 5), 9),
            "ones": tw.ones(n, 5),
            "rand": tw.rand(n),
            "randint": tw.randint(0, 100, (n,)),
            "randperm": tw.randperm(n),
            "zeros": tw.zeros(n, 1),
            "empty": tw.empty(n, 2),
        }
        data_objs: Dict[str, Any] = copy.copy(data_tensors)
        data_objs.update({"randstr": [pw.randstr(2) for _ in range(n)]})

        assert pw.is_full(map(len, data_objs.values()))

        tests: List[Tuple[str, Any, bool, dict, dict]] = [
            ("json", data_objs, True, dict(), dict()),
            ("pickle", data_objs, False, dict(), dict()),
        ]

        if _NUMPY_AVAILABLE:
            from torchwrench.extras.numpy import to_ndarray

            tests += [
                ("numpy", to_ndarray(v), False, dict(), dict())
                for k, v in data_objs.items()
            ]

        if _SAFETENSORS_AVAILABLE:
            tests += [
                ("safetensors", data_tensors, False, dict(), dict()),
            ]

        if _YAML_AVAILABLE:
            tests += [
                ("yaml", data_tensors, True, dict(), dict()),
                ("yaml", data_objs, True, dict(), dict()),
            ]

        for i, (backend, data, to_builtins, load_kwds, dump_kwds) in enumerate(tests):
            assert tw.isinstance_generic(backend, SavingBackend), (  # type: ignore
                f"{backend=}; {get_args(SavingBackend)=}"
            )

            if to_builtins:
                data = tw.as_builtin(data)
            if backend == "safetensors":
                # note: safetensors automatically sort dicts
                data = pw.sorted_dict(data)

            fpath = get_tmp_dir().joinpath(f"tmp.{backend}")
            tw.dump(data, fpath, saving_backend=backend, **dump_kwds)
            result = tw.load(fpath, saving_backend=backend, **load_kwds)

            assert deep_equal(data, result), f"{backend=}, {i=}/{len(tests)}"


if __name__ == "__main__":
    unittest.main()
