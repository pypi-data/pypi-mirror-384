#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import unittest
from unittest import TestCase

import yaml
from yaml import FullLoader, SafeLoader
from yaml.constructor import ConstructorError

from torchwrench.core.packaging import _YAML_AVAILABLE
from torchwrench.extras.yaml import (
    IgnoreTagLoader,
    SplitTagLoader,
    dump_yaml,
    load_yaml,
)


class TestYaml(TestCase):
    def test_yaml_load_examples(self) -> None:
        if not _YAML_AVAILABLE:
            return None

        dumped = "a: !!python/tuple\n- 1\n- 2"

        result = yaml.load(dumped, Loader=IgnoreTagLoader)
        expected = {"a": [1, 2]}
        assert result == expected

        result = yaml.load(dumped, Loader=FullLoader)
        expected = {"a": (1, 2)}
        assert result == expected

        with self.assertRaises(ConstructorError):
            yaml.load(dumped, Loader=SafeLoader)

        result = yaml.load(dumped, Loader=SplitTagLoader)
        expected = {"a": {"_target_": "yaml.org,2002:python/tuple", "_args_": [1, 2]}}
        assert result == expected

        data = load_yaml(io.StringIO(dumped), Loader=FullLoader)
        assert dump_yaml(data) == f"{dumped}\n", f"{data=}"
        assert dump_yaml(data, to_builtins=True) == "a:\n- 1\n- 2\n", f"{data=}"


if __name__ == "__main__":
    unittest.main()
