#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase

import pythonwrench as pw
import torch

import torchwrench as tw
from torchwrench.core.packaging import _NUMPY_AVAILABLE
from torchwrench.extras.numpy import (
    ndarray_to_tensor,
    np,
    numpy_is_complex,
    numpy_is_complex_dtype,
    numpy_item,
    numpy_topk,
    numpy_view_as_complex,
    numpy_view_as_real,
    tensor_to_ndarray,
)


class TestNumpy(TestCase):
    def test_example_1(self) -> None:
        if not _NUMPY_AVAILABLE:
            return None

        x_tensor = torch.rand(3, 4, 5)
        x_array = tensor_to_ndarray(x_tensor)
        result = ndarray_to_tensor(x_array)

        assert torch.equal(x_tensor, result)

    def test_complex(self) -> None:
        if not _NUMPY_AVAILABLE:
            return None

        complex_dtypes = [np.complex64, np.complex128]
        x_complex = [
            np.array(
                np.random.rand(1) * 1j,
                dtype=complex_dtypes[np.random.randint(0, len(complex_dtypes))],
            )
            for _ in range(1000)
        ]
        assert all(numpy_is_complex(xi) for xi in x_complex)
        assert all(numpy_is_complex_dtype(xi.dtype) for xi in x_complex)

        x_real = [numpy_view_as_real(xi) for xi in x_complex]
        assert all(not numpy_is_complex(xi) for xi in x_real)
        assert all(not numpy_is_complex_dtype(xi.dtype) for xi in x_real)

        result = [numpy_view_as_complex(xi) for xi in x_real]
        assert all(numpy_is_complex(xi) for xi in result)
        assert all(numpy_is_complex_dtype(xi.dtype) for xi in result)
        assert x_complex == result

    def test_numpy_item(self) -> None:
        x = np.array(1.2)
        result = numpy_item(x)
        assert isinstance(result, np.generic)

        x = np.array([1, 2])[1]
        result = numpy_item(x)
        assert isinstance(result, np.generic)

        x = 10.99
        result = numpy_item(x)
        assert isinstance(result, np.generic)

    def test_numpy_topk(self) -> None:
        x = np.array([0, 2, 0, 1, 2])
        result = numpy_topk(x, k=3)
        expected = np.array([2, 2, 1]), np.array([1, 4, 3])
        assert tw.deep_equal(result, expected)


class TestReduceCompat(TestCase):
    def test_example_1(self) -> None:
        x1 = np.random.rand(10) > 0.5
        x2 = np.random.rand(10) > 0.5
        expected = x1 | x2

        result = pw.reduce_or(x1, x2)
        assert tw.deep_equal(result, expected)

        result = pw.reduce_or([x1, x2], start=False)
        assert tw.deep_equal(result, expected)

        result = pw.reduce_or(np.array([x1, x2]), start=False)
        assert tw.deep_equal(result, expected)


if __name__ == "__main__":
    unittest.main()
