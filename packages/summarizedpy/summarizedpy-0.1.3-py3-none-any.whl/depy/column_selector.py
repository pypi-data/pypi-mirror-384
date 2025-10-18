import pandas as pd
import re
from typing import Optional, List

class ColumnSelector:
    """
    Object for pre-selecting columns when constructing SummarizedPy from file.

    Parameters
    ----------
    names : list, optional
        A list of strings matching column names.
    regex : str, optional
        A string that can be interpreted as a regular expression
        by re.search. Note that the search is case-insensitive.

    Examples
    --------
    Define columns to import from file. Assume data are in columns labeled "LFQ_intensity_*".

    >>> import depy as dp
    >>> data = dp.ColumnSelector(regex="LFQ_intensity_")
    >>> features = dp.ColumnSelector(names=["proteinID", "geneSymbol", "proteinDescription"])
    >>> sp = dp.SummarizedPy().import_from_delim_file(path="my/path/proteingroups.txt", delim='\t', data_selector=data, feature_selector=features)
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
