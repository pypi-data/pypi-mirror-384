"""A ColumnSelector for SummarizedPy objects"""

import pandas as pd
import re
from typing import Optional, List

class ColumnSelector:
    """
    Object for selecting columns in SummarizedPy using RegEx or a list of strings.

    Parameters
    ----------
        names : list, optional
            A list of strings matching column names.
        regex : str, optional
            A string that can be interpreted as a regular expression
            by re.search. Note that the search is case-insensitive.
    """

    def __init__(self, names: Optional[List[str]] = None, regex: Optional[str] = None):
        self.names = names
        self.regex = regex

    def select_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parameters
        ----------
        df : pd.DataFrame
            A Pandas DataFrame object on which to perform column selection.

        Returns
        -------
            SummarizedPy
                A Pandas DataFrame with selected columns.

        Raises
        ------
            KeyError
                If no valid column names are supplied.
        """
        cols = self.names or []

        if self.regex:
            regex_cols = [col for col in df.columns if re.search(self.regex, col, re.IGNORECASE)]
            cols.extend(regex_cols)
        if cols:
            return df.loc[:, cols]
        else:
            raise KeyError("No valid columns selected!")
