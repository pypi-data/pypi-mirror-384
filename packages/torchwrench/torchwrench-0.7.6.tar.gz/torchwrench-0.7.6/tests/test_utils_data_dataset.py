#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from typing import Iterator
from unittest import TestCase

from torchwrench.utils.data.dataset import IterableSubset, IterableTransformWrapper


class TestDataset(TestCase):
    def test_advanced_example_1(self) -> None:
        class Dummy:
            def __iter__(self) -> Iterator[int]:
                yield from range(len(self))

            def __len__(self) -> int:
                return 100

        ds = Dummy()
        subset = IterableSubset(ds, [2, 4, 6])

        assert list(subset) == [2, 4, 6]

    def test_wrapper_example_1(self) -> None:
        wrapped = IterableTransformWrapper(list(range(10)), lambda x: x * 2)
        assert list(wrapped) == list(range(0, 20, 2))


if __name__ == "__main__":
    unittest.main()
