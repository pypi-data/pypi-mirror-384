#!/usr/bin/env python
import pytest

@pytest.fixture(scope="session")
def load_data_sp():
    """Load example proteomics dataset (3709, 12) for all integration tests."""
    from depy.summarized_py import SummarizedPy
    return SummarizedPy().load_example_data()

@pytest.fixture(scope="module")
def test_df():
    import pandas as pd
    """Create example dataframe to test alternative constructor from delimited file and use for ColumnSelector."""
    test_df = pd.DataFrame({
        "proteinID": ["A", "B", "C"],
        "sample1": [1, 2, 3],
        "sample2": [4, 5, 6],
        "sample3": [7, 8, 9],
    })

    return test_df

@pytest.fixture(scope="module")
def toy_data():
    """Create toy data to initialize SummarizedPy for unit testing constructor."""
    import pandas as pd
    import numpy as np
    data = np.array([[1, 2, 3],
                     [4, 5, 6],
                     [7, 8, 9]])
    features = pd.DataFrame({"proteinID": ["feature1", "feature2", "feature3"]})
    samples = pd.DataFrame({"sample": ["sample1", "sample2", "sample3"]})

    return data, features, samples

@pytest.fixture(scope="module")
def toy_data_sp(toy_data):
    """Instantiate toy SummarizedPy from toy data for unit testing subsetting."""
    from depy.summarized_py import SummarizedPy
    data, features, samples = toy_data
    return SummarizedPy(data=data, features=features, samples=samples)
