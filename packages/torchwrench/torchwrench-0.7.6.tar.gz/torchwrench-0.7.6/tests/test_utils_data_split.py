#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase

import torchwrench as tw
from torchwrench.utils.data.split import balanced_monolabel_split, random_split


class TestSplit(TestCase):
    def test_balanced_monolabel_split(self) -> None:
        num_classes = 5
        targets_indices = tw.randint(0, num_classes, (100,))
        splitted = balanced_monolabel_split(targets_indices, num_classes, [0.1, 0.2])

        assert len(splitted) == 2
        assert len(splitted[0]) <= 10
        assert len(splitted[1]) <= 20

    def test_random_split(self) -> None:
        splitted = random_split(100, [0.1, 0.2])

        assert len(splitted) == 2
        assert len(splitted[0]) <= 10
        assert len(splitted[1]) <= 20


if __name__ == "__main__":
    unittest.main()
