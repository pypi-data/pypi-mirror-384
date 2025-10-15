#!/usr/bin/env python
"""Independent test of load_example_data method, as it is required for other tests"""
import pandas as pd
import numpy as np
from depy.summarized_py import SummarizedPy

def test_load_data():
    obj = SummarizedPy().load_example_data()
    assert isinstance(obj, SummarizedPy)
    assert isinstance(obj.samples, pd.DataFrame)
    assert isinstance(obj.features, pd.DataFrame)
    assert obj.data.shape == (3709,12)
    assert np.any(np.isnan(obj.data))
