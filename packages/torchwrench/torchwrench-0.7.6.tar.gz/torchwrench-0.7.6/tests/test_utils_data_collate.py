#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase

import torchwrench as tw
from torchwrench.utils.data.collate import AdvancedCollateDict


class TestCollate(TestCase):
    def test_advanced_example_1(self) -> None:
        collate = AdvancedCollateDict({"x": 0})

        inputs = [
            {"x": tw.as_tensor([1, 2])},
            {"x": tw.as_tensor([3, 4, 5, 6])},
            {"x": tw.as_tensor([7])},
        ]
        result = collate(inputs)
        expected = {"x": tw.as_tensor([[1, 2, 0, 0], [3, 4, 5, 6], [7, 0, 0, 0]])}
        assert tw.deep_equal(result, expected), f"{result=}"


if __name__ == "__main__":
    unittest.main()
