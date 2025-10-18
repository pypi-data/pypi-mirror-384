#!/usr/bin/env python
"""Unit tests for SummarizedPy class."""
from depy.summarized_py import SummarizedPy
import pytest

@pytest.mark.unit
def test_sp_constructor(toy_data):
    """Test the constructor of SummarizedPy class."""
    data, features, samples = toy_data

    obj = SummarizedPy(data=data, features=features, samples=samples)

    assert isinstance(obj, SummarizedPy)
    assert obj.data.shape == (3, 3)
    assert obj.features.shape == (3, 1)
    assert obj.samples.shape == (3, 1)
    assert hasattr(obj, "history")
    assert hasattr(obj, "results")

@pytest.mark.unit
@pytest.mark.parametrize("fkey,skey", [
    (1, 1),
    (1, slice(None)),
    (slice(None), 1),
    (slice(None), slice(None)),
    (slice(0,2), slice(0,2))

])

def test_sp_subset(toy_data_sp, fkey, skey):
    """Test subsetting SummarizedPy object."""
    import numpy as np
    import pandas as pd

    sub = toy_data_sp[fkey, skey]

    assert sub.data.ndim == 2
    assert sub.features.ndim == 2
    assert sub.samples.ndim == 2
    assert isinstance(sub.data, np.ndarray)
    assert isinstance(sub.features, pd.DataFrame)
    assert isinstance(sub.samples, pd.DataFrame)
