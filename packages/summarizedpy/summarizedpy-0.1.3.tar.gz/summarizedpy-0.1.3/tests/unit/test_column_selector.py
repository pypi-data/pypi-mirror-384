#!/usr/bin/env python

"""Unit tests for ColumnSelector helper class."""
import pytest
import pandas as pd
from depy.column_selector import ColumnSelector

@pytest.mark.unit
def test_column_selector_constructor(test_df):
    """Test the ColumnSelector class constructor."""
    cs = ColumnSelector()

    assert isinstance(cs, ColumnSelector)

@pytest.mark.unit
def test_column_selector_select_cols(test_df):
    """Test the ColumnSelector class method."""
    test_df = test_df
    sub = ColumnSelector(names=["proteinID"], regex="sample").select_cols(test_df)

    assert isinstance(sub, pd.DataFrame)
    assert sub.shape == test_df.shape
