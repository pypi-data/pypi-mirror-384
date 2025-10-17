from .column_selector import ColumnSelector
from .utils import _annotate_features_reg
from typing import Optional, overload, Literal, Union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import janitor
from adjustText import adjust_text
from importlib import resources
import subprocess
import tempfile
import pyarrow.feather as feather
import pathlib
import os

class SummarizedPy:
    def __init__(self, data: Optional[np.ndarray] = None, features: Optional[pd.DataFrame] = None,
                 samples: Optional[pd.DataFrame] = None):
        self._data = data
        self.features = features
        self.samples = samples
        self._history = []
        self._results = pd.DataFrame()

        # Validate dimensions
        self._validate_dimensions()

    def _validate_dimensions(self):
        """Check that the dimensions of data match rows in features and samples."""
        if self.data is not None:
            if not (isinstance(self.data, np.ndarray) and self.data.ndim == 2):
                raise TypeError(f"Data must be a 2D numpy array, got {type(self.data)} with dimension {self.data.ndim}")
            nfeatures, nsamples = self.data.shape

        if self.features is not None:
            if not isinstance(self.features, pd.DataFrame):
                raise TypeError(f"Features must be a pandas DataFrame, got {type(self.features)}")
            if self.features.shape[0] != nfeatures:
                raise ValueError(f"Number of features ({self.features.shape[0]}) does not match number of rows in data ({nfeatures})")

        if self.samples is not None:
            if not isinstance(self.samples, pd.DataFrame):
                raise TypeError(f"Samples must be a pandas DataFrame, got {type(self.samples)}")
            if self.samples.shape[0] != nsamples:
                raise ValueError(f"Number of samples ({self.samples.shape[0]}) does not match number of columns in data ({nsamples})")

    # Read-only attribute - .data
    @property
    def data(self):
        return self._data

    # Prevent .data reassignment
    @data.setter
    def data(self, value):
        raise AttributeError(
            "Error: cannot reassign .data! Please use transformations instead or mutate entries in-place!")

    # read-only attribute - .history
    @property
    def history(self):
        return self._history

    # Prevent .history reassignment
    @history.setter
    def history(self, value):
        raise AttributeError("Error: cannot reassign .history!")

    # read-only attribute - .results
    @property
    def results(self):
        return self._results

    # Prevent .results reassignment
    @results.setter
    def results(self, value):
        raise AttributeError("Error: cannot reassign .results!")

    def __str__(self):

        hist = len(self.history)
        data_shape = self.data.shape if self.data is not None else (0, 0)
        num_feat, num_samp = data_shape
        features_meta = self.features.columns.to_list() if self.features is not None else []
        samples_meta = self.samples.columns.to_list() if self.samples is not None else []
        results = self.results.shape if not self.results.empty else (0, 0)

        features_meta_disp = features_meta if len(features_meta) <= 5 else f"{len(features_meta)} columns"
        samples_meta_disp = samples_meta if len(samples_meta) <= 5 else f"{len(samples_meta)} columns"

        return (
            f"A SummarizedPy\n"
            f"Data: {num_feat} features, {num_samp} samples\n"
            f"Feature metadata: {features_meta_disp}\n"
            f"Sample metadata: {samples_meta_disp}\n"
            f"History: {hist} steps\n"
            f"Results: {results}"
        )

    def __repr__(self):
        data_info = (f"ndarray(shape={self.data.shape}, dtype={self.data.dtype})"
                     if self.data is not None else 'None'
                     )
        feature_info = (f"DataFrame(shape={self.features.shape})"
                        if self.features is not None else 'None'
                        )
        samples_info = (f"DataFrame(shape={self.samples.shape})"
                        if self.samples is not None else 'None'
                        )

        return f"SummarizedPy(data={data_info}, features={feature_info}, samples={samples_info})"

    def __getitem__(self, key):
        """
        Implement subsetting of SummarizedPy like obj[features, samples]
        """
        fkey, skey = key if isinstance(key, tuple) else (key, slice(None))

        new_data = self.data[fkey, skey]
        new_features = self.features.iloc[fkey] if self.features is not None else None
        new_samples = self.samples.iloc[skey] if self.samples is not None else None

        # Normalize dimensionality to ensure data is 2D np.ndarray and samples/features pd.DataFrame
        if isinstance(new_data, np.ndarray) and new_data.ndim == 1:
            new_data = new_data.reshape(-1, 1) if np.isscalar(skey) else new_data.reshape(1, -1)
        if new_data.ndim == 0:
            new_data = new_data.reshape(1, 1)
        if isinstance(new_features, pd.Series):
            new_features = new_features.to_frame().T
        if isinstance(new_samples, pd.Series):
            new_samples = new_samples.to_frame().T

        new_obj = self.__class__(data=new_data, features=new_features, samples=new_samples)
        new_obj._history = self._history + [f"Subset: rows={fkey}, cols={skey}"]
        return new_obj

    @classmethod
    def import_from_delim_file(cls, path: str, delim: str,
                               data_selector: Optional[ColumnSelector] = None,
                               feature_selector: Optional[ColumnSelector] = None,
                               replace_val_with_nan: Optional[float] = None,
                               clean_column_names: Optional[bool] = False
                               ):
        """
        Alternative constructor from file.
        Import method that reads data directly from delimited file, including feature data,
        feature metadata, and sample metadata, and assigns them to data, features, and samples attributes automatically.
        This is intended for convenient import of standardized outputs like MaxQuant's proteingroups.txt or
        FragPipe/DIA-NN's diann-output.pg_matrix.tsv.
        Method uses ColumnSelector objects to assign columns to their relevant storage containers.
        If no ColumnSelector is provided, the function defaults to assigning all numerical (float64) columns to data
        and all string (object) columns to feature data. Thus, it is best to explicitly state which columns to import.
        The samples attribute is automatically populated with the column names from data.
        The original data row and columns indices are stored in features and samples 'orig_index' variables, resp., for bookkeeping.
        The read path and delimiter used will be appended to the history attribute.
        Values in data can be replaced with NaN to indicate missingness (e.g. intensity values of 0).
        Column names can be automatically cleaned with the pyjanitor clean_names function.

        Parameters
        ----------
        path : str
            Path to file to read in.
        delim : str
            Delimiter to parse file (e.g. '\t' for .txt or ',' for .csv).
        data_selector : ColumnSelector, optional
            A ColumnSelector object with specified names or regex patterns
            to extract data columns in file. If not specified,
            defaults to all 'number' dtype columns.
        feature_selector : ColumnSelector, optional
            A ColumnSelector object with specified names or regex patterns
            to extract feature metadata columns in file. If not specified,
            defaults to all object dtype columns.
        replace_val_with_nan : float, optional
            A float numeric value in data to replace with np.nan to indicate missingness (e.g. 0).
        clean_column_names : bool, optional
            Whether to clean column names in file before processing. Note that column selection
            happens on the cleaned column names! Thus, you have to account for this
            when instantiating the ColumnSelector object. Cleaning will coerce
            all string to lower case; spaces and hyphens will be replaced with underscores,
            and leading and trailing whitespace will be trimmed.


        Returns
        -------
        SummarizedPy
            A SummarizedPy object.

        """

        df = pd.read_csv(path, delimiter=delim, low_memory=False)

        if clean_column_names:
            df = df.clean_names(strip_underscores="both")

        samples = pd.DataFrame()

        if data_selector:
            data_array = data_selector.select_cols(df)
            samples["sample"] = data_array.columns.tolist()
            samples["orig_index"] = [i for i in range(len(samples))]
        else:
            data_array = df.select_dtypes(include="number")
            samples["sample"] = data_array.columns.tolist()
            samples["orig_index"] = [i for i in range(len(samples))]

        if feature_selector:
            feature_df = feature_selector.select_cols(df)
            feature_df["orig_index"] = [i for i in range(len(feature_df))]
        else:
            feature_df = df.select_dtypes(include="object")
            feature_df["orig_index"] = [i for i in range(len(feature_df))]

        if replace_val_with_nan is not None:
            data_array = data_array.replace(to_replace=replace_val_with_nan, value=np.nan)

        data_array = data_array.to_numpy()

        obj = cls(data=data_array, features=feature_df, samples=samples)
        obj._history.append(f"Imported from: path={path!r}, delim={delim!r}")

        return obj

    def _filter(self, axis, expr=None, mask=None):
        """
        Internal helper function for public filter functions.

        Parameters
        ----------
            axis : {'features', 'samples'}
                An axis on which to filter.
                - 'features' : Filter on features attribute.
                - 'samples' : Filter on samples attribute.
            expr : str, optional
                A Pandas-style query string that can be
                interpreted by pd.obj.query(expr=expr).
            mask : bool, optional
                A boolean mask for subsetting.

        Returns
        -------
            SummarizedPy
                A filtered SummarizedPy object.

        Raises
        ------
            ValueError
                If axis is invalid or no additional filter argument (i.e. 'expr' or 'mask') is supplied.
        """

        if axis == "features":
            meta = self.features
            axis_num = 0
        elif axis == "samples":
            meta = self.samples
            axis_num = 1
        else:
            raise ValueError("Error: axis must be 'features' or 'samples'")

        if expr is not None:
            keep_index = meta.query(expr).index
            tmp_str = f" with expr='{expr}'"
        elif mask is not None:
            keep_index = meta.index[mask]
            tmp_str = None
        else:
            raise ValueError("Error: must supply either expr or mask")

        new_meta = meta.iloc[keep_index]
        new_meta = new_meta.reset_index(drop=True)
        new_data = self.data.take(keep_index, axis=axis_num)

        if axis == "features":
            new_obj = self.__class__(data=new_data, features=new_meta, samples=self.samples)
        else:
            new_obj = self.__class__(data=new_data, features=self.features, samples=new_meta)

        new_obj._history = self.history + [
            f"Filtered {axis}{tmp_str if tmp_str is not None else ''}: {len(keep_index)} kept"]
        return new_obj

    def filter_samples(self, expr: Optional[str] = None, mask: Optional[bool] = None):
        """
        Filter SummarizedPy object based on sample metadata, using either Pandas-like query strings or a mask.

        Parameters
        ----------
            expr : str, optional
                A Pandas-style query string that can be
                interpreted by pd.obj.query(expr=expr).
            mask : bool, optional
                A boolean mask for subsetting.

        Returns
        -------
            SummarizedPy
                A filtered SummarizedPy object.

        Raises
        ------
            ValueError
                If no valid expr or mask argument is supplied.
        """
        new_obj = self._filter(axis="samples", expr=expr, mask=mask)
        return new_obj

    def filter_features(self, expr: Optional[str] = None, mask: Optional[bool] = None):
        """
        Filter SummarizedPy object based on feature metadata, using either Pandas-like query strings or a mask.

        Parameters
        ----------
            expr : str, optional
                A Pandas-style query string that can be
                interpreted by pd.obj.query(expr=expr).
            mask : str, optional
                A boolean mask for subsetting.

        Returns
        -------
            SummarizedPy
                A filtered SummarizedPy object.

        Raises
        ------
            ValueError
                If no valid expr or mask argument is supplied.
        """
        new_obj = self._filter(axis="features", expr=expr, mask=mask)
        return new_obj

    def filter_missingness(self, frac: float = 0.75, strategy: str = "all_conditions", condition_column: str = None):
        """
        Filter SummarizedPy object based on % feature missingness across one of:
        overall, all conditions, or any condition.

        Parameters
        ----------
        frac : float
            Minimum percentage valid values. Features with missingness
            greater than or equal to (1 - frac) will be excluded.
        strategy : {'overall', 'all_conditions', 'any_condition'}
            Filtering strategy:

            - 'overall' : Require >= frac valid values across all samples.
            - 'all_conditions' : Require >= frac valid values in *each*
              condition defined by `condition_column`.
            - 'any_condition' : Require >= frac valid values in at least
              one condition defined by `condition_column`.
        condition_column : str, optional
            Name of column in the `samples` attribute on which to base
            filtering, in case of 'all_conditions' or 'any_condition'.

        Returns
        -------
        SummarizedPy
            A filtered SummarizedPy object.

        Raises
        ------
        ValueError
            If an invalid strategy is supplied or if `condition_column`
            is required but missing.
        """

        nfeatures, _ = self.data.shape
        mask = ~np.isnan(self.data)

        if strategy == "overall":
            result = np.mean(mask, axis=1) >= frac

        elif strategy == "all_conditions" or strategy == "any_condition":

            if condition_column is None:
                raise ValueError("Must supply a valid column name in SummarizedPy samples!")

            unique_conds = np.unique(self.samples[condition_column])
            cond_mask = np.array([self.samples[condition_column] == cond for cond in unique_conds])

            miss_fracs = np.stack([np.mean(mask[:, cm], axis=1) for cm in cond_mask], axis=1)

            if strategy == "all_conditions":
                result = np.all(miss_fracs >= frac, axis=1)

            else:
                result = np.any(miss_fracs >= frac, axis=1)

        else:
            raise ValueError("Error: must choose one of 'overall', 'each_condition', or 'any_condition'")

        new_obj = self.__class__(data=self._data[result], features=self.features.iloc[result], samples=self.samples)
        new_obj._history = self._history + [
            f"Filtered features by missingness with strategy='{strategy}', frac={frac}: {new_obj.features.shape[0]} kept"]

        return new_obj

    # Transformation helper methods
    # Centering
    def _center(self, by: str = None, axis: int = None):
        if not isinstance(axis, int) or axis not in (0, 1):
            raise ValueError(
                f"Invalid argument, 'axis'={axis!r}. Must be an integer 0 (rows/features) or 1 (columns/samples).")

        if by == "mean":
            return np.subtract(self.data, np.nanmean(self.data, axis=axis, keepdims=True))
        elif by == "median":
            return np.subtract(self.data, np.nanmedian(self.data, axis=axis, keepdims=True))
        else:
            raise ValueError(
                f"Invalid argument, 'by'={by !r}. Must supply one of 'mean' or 'median' to 'by=' when using center.")

    # Log transform base N
    def _log_transform(self, base: int = 2):
        if not isinstance(base, int):
            raise ValueError(
                f"Invalid argument, 'base'={base!r}. Must supply integer to 'by=' when using log transformation.")

        return np.emath.logn(x=self.data, n=base)

    # Standardize (i.e. z-score)
    def _standardize(self, axis: int = None):
        if not isinstance(axis, int) or axis not in (0, 1):
            raise ValueError(
                f"Invalid argument, 'axis'={axis!r}. Must be an integer 0 (rows/features) or 1 (columns/samples).")

        return np.divide(np.subtract(self.data, np.nanmean(self.data, axis=axis, keepdims=True)),
                         np.nanstd(self.data, axis=axis, ddof=1, keepdims=True))

    # Helper method to run R modules
    def _run_r_module(self, module_name: str = None, extra_args: dict = None, data: bool = True, samples: bool = False,
                      features: bool = False):

        with resources.files("depy").joinpath(f"R/{module_name}.R") as rscript:
            with tempfile.TemporaryDirectory(prefix=module_name) as tmp_dir:
                tmpd = pathlib.Path(tmp_dir)
                out_path = tmpd / "out.feather"
                logs_dir = tmpd / "data" / "logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                log_path = logs_dir / f"{module_name}.log"

                # Define env for R to run in and where to look for libraries (avoids global config leak)
                env = os.environ.copy()
                env_root = env["CONDA_PREFIX"]
                r_lib = f"{env_root}/lib/R/library"
                env.update({
                    "R_HOME": f"{env_root}/lib/R",
                    "R_LIBS": r_lib,
                    "R_LIBS_USER": r_lib,
                    "R_LIBS_SITE": r_lib,
                    "DYLD_LIBRARY_PATH": f"{env_root}/lib:" + env.get("DYLD_LIBRARY_PATH", ""),
                })

                # R module call and default arguments
                cmd = ["Rscript", str(rscript),
                       "--out", str(out_path)]

                # Extra user-supplied args
                if extra_args is not None:
                    for k, v in extra_args.items():
                        if v is None:
                            continue
                        cmd.extend([f"--{k}", str(v)])

                # Write SP attributes to temp dir
                # Data
                if data:
                    expr_path = tmpd / "expr.feather"
                    feather.write_feather(pd.DataFrame(self.data), dest=expr_path)
                    cmd.extend(["--expr", str(expr_path)])

                # Samples
                if samples:
                    samples_path = tmpd / "samples.feather"
                    feather.write_feather(self.samples, dest=samples_path)
                    cmd.extend(["--samples", str(samples_path)])

                # Features
                if features:
                    features_path = tmpd / "features.feather"
                    feather.write_feather(self.features, dest=features_path)
                    cmd.extend(["--features", str(features_path)])

                # Run R module subprocess
                with open(log_path, "w") as logf:
                    print(f"Running {module_name} R module...")
                    proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT, check=False, env=env)
                    print("Done")

                # Check subprocess return code
                if proc.returncode != 0:
                    with open(log_path, "r") as f:
                        logtxt = f.read()
                    raise RuntimeError(f"R module failed (code={proc.returncode}). Log:\n{logtxt}")

                if not out_path.exists():
                    raise FileNotFoundError(f"Expected output not found: {out_path}")

                return feather.read_feather(out_path)

    @classmethod
    def load_example_data(cls):
        """
        Load a real-world example proteomics dataset for demonstration purposes.
        The function loads dataset 'PXD000438' from the ImputeLCMD package.
        The data were generated from a super-SILAC experiment of human adenocacinoma (ADC) and squamous cell carcinoma (SCC) samples.
        The dataset contains six ADC and six SCC samples and 3,709 proteomic features with raw feature intensities and missing values.
        Samples 092.1-3 and 441.1-3 are ADC and 561.1-3 and 691.1-3 are SCC.

        For more information about the dataset:
        https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD000438

        Returns
        -------
        SummarizedPy
            A summarizedPy object with 12 samples and 3,709 features.
        """
        tmp = cls()
        example_data = tmp._run_r_module(module_name="load_example_data", data=False)

        data = example_data.select_dtypes(include="float64")
        data = data.replace(to_replace=0, value=np.nan)
        features = pd.DataFrame()
        features["protein_id"] = example_data["Protein.IDs"]
        samples = pd.DataFrame()
        samples["sample"] = data.columns.tolist()

        obj = cls(data=np.array(data), features=features, samples=samples)
        obj._history.append(f"Loaded example dataset PXD000438")

        return obj

    # Public transformation method
    # Type signatures (stubs)
    @overload
    def transform_features(self, method: Literal["center"], axis: int,
                           by: Optional[Literal["mean", "median"]] = None) -> "SummarizedPy":
        pass

    @overload
    def transform_features(self, method: Literal["log"], by: Optional[int] = None) -> "SummarizedPy":
        pass

    @overload
    def transform_features(self, method: Literal["z-score"], axis: int, by: None = None) -> "SummarizedPy":
        pass

    @overload
    def transform_features(self, method: Literal["vsn"]) -> "SummarizedPy":
        pass

    # Actual implementation
    def transform_features(self, method: str, axis: Optional[int] = None, by: Optional[Union[str, int]] = None):
        """
        Mathematically transform features stored in data attribute using one of:
        log (base N), center (using mean or median subtraction), or z-score (standardize).

        Parameters
        ----------
        axis : int
            An axis to perform the transformation along:
            - 0 = rows (per-feature)
            - 1 = columns (per-sample).
        method : {'log', 'center', 'z-score', 'vsn'}
            Mathematical transformation to apply:

            - 'log' : Applies log base N (use 'by' parameter to set base) transformation
            across entire data array.
            - 'center' : Center data by subtraction (use in conjunction with 'by' parameter).
            - 'z-score' : Standardizes data using z-score transformation
            (i.e. (x_i-x_mean)/x_std).
            NB: applies Bessel's N-1 correction to estimate sample standard deviation.
            - vsn : Applies variance stabilizing normalization, as implemented Huber et al. (2004).
        by : str or int, optional
            Used in conjunction with method='center' or method='log'.
            - With 'center' : str, One of 'mean' or 'median' to subtract
            axis mean or median from each cell.
            - With 'log' : int, An integer for the base of the logarithm (defaults to 2).

        Returns
        -------
        SummarizedPy
            A transformed SummarizedPy object.

        Raises
        ------
        ValueError
            If an invalid value is supplied to either axis, method, or by.
        """
        if method == "z-score":
            new_data = self._standardize(axis=axis)
            by_str = None
            axs_str = f" along axis={axis},"
        elif method == "center":
            new_data = self._center(axis=axis, by=by)
            by_str = f", by={by}"
            axs_str = f" along axis={axis},"
        elif method == "log":
            new_data = self._log_transform(base=by)
            by_str = f", by={by}"
            axs_str = None
        elif method == "vsn":
            new_data = np.array(self._run_r_module(module_name="vsn_transform"))
            by_str = None
            axs_str = None
        else:
            raise ValueError(
                f"Invalid argument, 'method'={method!r}. Must supply a valid method: 'z-score', 'center', or 'log'.")

        new_obj = self.__class__(data=new_data, features=self.features, samples=self.samples)
        new_obj._history = self._history + [
            f"Transformed features{axs_str if axs_str is not None else ''} with method={method}{by_str if by_str is not None else ''}"]

        return new_obj

    # Imputation method using R package ImputeLCMD
    def impute_missing_values(self, method: str = None, extra_args: Optional[dict] = None):
        """
        Impute missing values using the ImputeLCMD R package.
        Several common methods are available under the assumptions of MAR (KNN, SVD, MLE),
        MNAR (QRILC, MinDet, MinProb), or both MAR and MNAR (Hybrid).
        Refer to the ImputeLCMD package documentation for further information:
        https://cran.r-project.org/web/packages/imputeLCMD/imputeLCMD.pdf

        Parameters
        ----------
        method : {'Hybrid', 'KNN', 'SVD', 'MLE', 'QRILC', 'MinDet', 'MinProb'}
            Imputation method to apply:
            - 'Hybrid' : Uses an empirical approach (quantile regression) to find a threshold
            below which missing values are imputed according to MNAR and above which values
            are imputed according to MAR. Defaults to mar='KNN' and mnar='QRILC'.
            - 'KNN' : Uses K-nearest neighbors to impute missing values
            under a MAR assumption. Defaults to k=15 neighbors.
            - 'SVD' : USes Singular Value Decomposition to impute missing values
            under a MAR assumption. Defaults to k=2 principal components.
            - MLE : Uses Maximum Likelihood Estimation (EM algorithm) top impute
            missing values under a MAR assumption.
            - QRILC : Uses Quantile Regression for Imputation of Left Censored data
            to impute missing values under an MNAR assumption.
            Defaults to a tune_sigma=1 (SD of the MNAR distribution).
            - MinDet : Uses imputation by minimum value observed to impute
            missing values under an MNAR assumption.
            Defaults to a q=0.01 (quantile to estimate minimum value).
            - MinProb : Uses imputation by random draws from a Gaussian distribution centered on
            the minimum value. Defaults to a q=0.01 (quantile to estimate minimum value) and
            tune_sigma=1 (SD of the MNAR distribution).
        extra_args : dict, optional
            Used in conjunction with methods that take additional parameters.
            Valid key-value pairs include:
            - mar : str, One of 'KNN', 'SVD', 'MLE' (for method='Hybrid').
            - mnar : str, One of 'QRILC', 'MinDet', 'MinProb' (for method='Hybrid').
            - k : int, Number of neighbors (method='KNN') or principal components (method='SVD').
            - q : float, Quantile to estimate minimum value (method='MinDet', 'MinProb').
            - tune_sigma : float, Quantile to estimate minimum value (method='QRILC', 'MinProb').

        Returns
        -------
        SummarizedPy
            A SummarizedPy object with imputed missing values.

        Raises
        ------
        ValueError
            If an invalid value is supplied to either method.
        """
        valid_methods = ['Hybrid', 'KNN', 'SVD', 'MLE', 'QRILC', 'MinDet', 'MinProb']
        valid_keys = ['q', 'k', 'tune_sigma', 'mar', 'mnar']

        if method not in valid_methods:
            raise ValueError(f"Invalid argument, 'method'={method!r}. Choose one of {', '.join(valid_methods)}.")

        if extra_args:
            if set(extra_args) - set(valid_keys):
                raise ValueError(f"Invalid extra_arg keys, {set(extra_args)}, choose one of {', '.join(valid_keys)}")
            tmp_str = ", extra_args=" + ", ".join([f"'{k}: {v}'" for k, v in extra_args.items()])
        else:
            extra_args = {}
            tmp_str = None

        extra_args["method"] = method
        new_data = np.array(self._run_r_module(module_name="impute_missing_values", extra_args=extra_args))

        new_obj = self.__class__(data=new_data, features=self.features, samples=self.samples)
        new_obj._history = self._history + [
            f"Imputed missing values with method='{method}'{tmp_str if tmp_str is not None else ''}"]

        return new_obj

    def surrogate_variable_analysis(self, mod: str = None, mod0: str = "~1", num_sv: int = None):
        """
        Run surrogate variable analysis to estimate latent factors that capture
        expression heterogeneity or hidden batch effects. The surrogate variables (SVs)
        will be added to the samples attribute and can be included as covariates in DEA.
        SVs are estimated through PCA on the residualized feature matrix after regressing out
        known experimental and technical/batch covariates. This is done by supplying the method
        with a fully parameterized model (mod), including all known covariates (experimental
        and technical; i.e. as present in the samples attribute), and a null model, including
        only technical (adjustment) covariates (mod0). The number of significant surrogate variables to estimate can then be specified using the num_sv argument;
        alternatively, the method can be run without specifying a number and allowing SVA to estimate the number empirically (using SVA's 'num.sv' function and the default 'leek' method).
        Note that this can return 0 SVs and fail. However, it is still possible to find significant SVs by forcing the method to run with a pre-specified num_sv argument.
        The mod and mod0 arguments must be specified using R formula formatting, which all start with a tilde (~) symbol and add covariates (+) and their interactions (*). Covariates must be present in the samples attribute.
        If no technical covariates are known, the method will run with the recommended default of "~1" (i.e. only using an intercept term).
        For more information, see: https://bioconductor.org/packages/3.19/bioc/vignettes/sva/inst/doc/sva.pdf

        Parameters
        ----------
        mod : str
            A formula describing the fully parameterized model (incl. all known covariates).
            Must begin with a tilde (~) and add covariates with '+'.
        mod0 : str, optional
            A formula describing the null model (incl. all known adjustment covariates).
            Must begin with a tilde (~) and add covariates with '+'. Defaults to '~1'.
        num_sv : int, optional
            The number of significant surrogate variables to estimate.

        Returns
        -------
        SummarizedPy
            A SummarizedPy object with estimate surrogate variables in the samples attribute.

        Raises
        ------
        ValueError
            If no mod formula is supplied.
        """
        if not mod:
            raise ValueError("Error: mod argument can't be empty! Supply a valid design formula.")

        extra_args = {"mod": mod, "mod0": mod0, "num_sv": num_sv}

        tmp_str = ", ".join([f"'{k}: {v}'" for k, v in extra_args.items()])

        new_samples = self._run_r_module(module_name="surrogate_variable_analysis", extra_args=extra_args, samples=True)

        new_obj = self.__class__(data=self.data, features=self.features, samples=new_samples)
        new_obj._history = self._history + [f"Ran surrogate variable analysis with {tmp_str}"]

        return new_obj

    def limma_trend_dea(self, design_formula: str = None, contrasts: dict = None, feature_id_col: Optional[str] = None,
                        robust: Optional[bool] = False, block: Optional[str] = None,
                        array_weights: Optional[bool] = False, extra_args: Optional[dict] = None):
        """
        Run differential expression analysis (DEA) with limma-trend. Limma powers its analyses by
        incorporating an empirical mean-variance trend estimated from the data as a prior.
        This alleviates the issue of estimating fold changes in the face of heteroscedasticity.
        In short, low-abundant features are prone to false positives due to inherently lower variance,
        whereas the opposite is true for high-abundant features, which are prone to false negatives.
        By modeling the overall mean-variance trend in the data and incorporating it as prior,
        information is shared across samples (which powers low-N designs) and features are effectively regularized.
        Compared to traditional parametric statistics, this Bayesian approach has consistently been found to be more powerful and
        achieve better FDR (false discovery rate) control. Additionally, a robust approximation can be used if the data contain
        hypo-/hypervariable features to avoid skewing the mean-variance trend.
        By fundamentally utilizing linear models, limma can accommodate complex designs, including fixed and random factors
        (i.e. mixed effects, such as nested factors or repeated measures) and their combination
        (i.e. to model between- and within-subjects designs). Limma can also incorporate sample quality weights, which are extremely powerful,
        especially in noisy datasets, which is often the case with human or animal samples. Using limma's arrayWeights function,
        samples are up- or down-weighted based on how variable they are compared to the average sample. Importantly, this function takes
        the experimental design into account when estimating the sample weights. Moreover, the user can provide an arbitrary design or none at all
        to estimate averaged weights for different groups of samples (i.e. in cases where sample quality is known to be especially poor according to some condition or technical covariate) or
        simply estimate sample-specific weights independent of design covariates. arrayWeights is run with the 'REML' method that allows for missing values.
        The weights are inversely proportional to sample variability (i.e. a weight of 0.5 is twice as variable as the average sample;
        weights >1 are less variable than the average and tend to reflect higher quality). The weights can be stabilized further and squeezed towards 1 by increasing the 'prior_n' parameter >10 (default);
        this tends to make weights more symmetric around 1 (average/equality), thus up- and down-weighting samples by similar magnitudes, rather disproportionately up-weighting good samples.

        Parameters
        ----------
        design_formula : str
            A formula describing the linear model. Covariates must be present in samples attribute.
            Must begin with a tilde (~) and add covariates with '+'.
            Note: formula may not contain intercept term
        contrasts : dict
            A dictionary containing contrast labels (keys) and contrast definitions (values).
            Contrasts are defined by adding or subtracting levels of the covariates
            included in the design formula. Additional scaling factors are allowed,
            such as dividing by the number of included terms to get the average.
        feature_id_col : str, optional
            The name of a column in the features attribute to name features by.
            If None, the method defaults to naming features according to their index.
        robust : bool, optional
            Whether to run limma-trend with robust approximation.
        block : str, optional
            Name of a column in samples attribute to using as a blocking variable.
            This must be used if running a model with both between- and within-subjects factors.
            The blocking variable should correspond to the column (subject)
            that gave rise to repeated values.
        array_weights : bool, optional
            Whether to estimate sample quality weights.
        extra_args : dict, optional
            Used in conjunction with array_weights to specify additional arguments.
            Valid key-value pairs include:
            - prior_n : int, The number of prior features to add (defaults to 10)
            to increase squeezing toward 1.
            - var_group : str, Name of a column in samples indicating groups (levels)
            that should be assigned different average weights.
            - sample_id_col : str, A column in samples attribute to use for sample labelling.
            This makes reading the sample weights output in limma_trend_dea.log easier.
            Note that names must be unique and may not start with numbers.
            If None, defaults to naming samples according to their index.

        Returns
        -------
        DataFrame
            A dataframe containing limma-trend DEA results with columns:
            - contrast_label : name of the contrast
            - contrast : contrast definition
            - feature : feature name
            - logfc : log2 fold change (i.e. regression coefficient)
            - ci_l : lower confidence interval for logfc
            - ci_r : upper confidence interval for logfc
            - aveexpr : average feature expression level
            - t : t-value for the associated test
            - p_value : nominal p-value for the associated test
            - adj_p_val : Benjamini-Hochberg-based false discovery rate
            - b : log-odds of differential expression

        Raises
        ------
        ValueError
            If no design_formula or contrasts arguments are provided.
        """
        if not design_formula or not contrasts:
            raise ValueError("Error: must supply valid design formula and contrasts.")

        if not extra_args:
            extra_args = {}

        extra_args["design_formula"] = design_formula
        extra_args["contrasts"] = "@".join([f"{k}:{v}" for k, v in contrasts.items()])
        extra_args["robust"] = robust
        extra_args["block"] = block
        extra_args["array_weights"] = array_weights
        extra_args["feature_id_col"] = feature_id_col

        tmp_str = ", ".join([f"'{k}: {v}'" for k, v in extra_args.items()])

        dea_results = self._run_r_module(module_name="limma_trend_dea",
                                         extra_args=extra_args,
                                         samples=True,
                                         features=True)
        dea_results = dea_results.clean_names()

        new_obj = self.__class__(data=self.data, features=self.features, samples=self.samples)
        new_obj._results = dea_results
        new_obj._history = self._history + [f"Ran limma-trend with {tmp_str}"]

        return new_obj


    def volcano_plot(self, contrasts: Optional[list] = None, top_n: Optional[int] = 3,
                     de_colors: Optional[dict] = None):
        """
        Generate volcano plots for limma-trend results, highlighting the top N up- and downregulated features.

        Parameters
        ----------
        contrasts : list, optional
            A list of strings referring to the name of contrasts to plot
            (i.e. column 'contrast_label' in results attribute). Defaults to all contrasts.
        top_n : int, optional
            Number of top up- and down-regulated features to highlight,
            ranked by adjusted p-value (FDR).
            Note: top_n up- and top_n downregulated features will be displayed,
            rather top_n in total. Defaults to top 3.
        de_colors : dict, optional
            Colors to use for upregulated, downregulated, and non-significant features.
            Must supply 'Up', 'Down', and 'ns' as keys with associated colors (str).

        Returns
        -------
        dict
            Dictionaries of matplotlib figure and axes objects for each contrast.
            - fig : `.Figure`
            - ax : `~matplotlib.axes.Axes`

        Raises
        ------
        ValueError
            If an invalid value is supplied to either contrasts or de_colors.
        """
        if contrasts:
            if set(contrasts) - set(self.results["contrast_label"]):
                raise ValueError(
                    f"Invalid contrasts {contrasts}, must supply list of valid contrast_label names from results attribute.")
        else:
            contrasts = set(self.results["contrast_label"])
        if de_colors:
            if set(de_colors) - set(["Up", "Down", "ns"]):
                raise ValueError(
                    f"Invalid de_color keys {set(de_colors)}, must supply dictionary with keys 'Up', 'Down', 'ns'.")
        else:
            de_colors = {"Up": "green", "Down": "pink", "ns": "gray"}

        figs = {}
        axs = {}
        for contr in contrasts:
            df = self.results.query(expr=f"contrast_label=='{contr}'")
            df = _annotate_features_reg(df)

            df["log_pval"] = -1 * np.log10(df["p_value"])
            log_pval = df["log_pval"]
            log_fc = df["logfc"]

            xlim = np.abs(log_fc).max() * 1.1

            size_grad = np.multiply(log_pval, np.abs(log_fc))
            size_grad = np.interp(size_grad, (np.nanmin(size_grad), np.nanmax(size_grad)), (1 / df.shape[0], 1)) * 200

            alphagrad = np.interp(df["p_value"], (np.nanmin(df["p_value"]), np.nanmax(df["p_value"])),
                                  (0.9, 1 / df.shape[0]))
            colalpha = plt.cm.colors.to_rgba_array(df["reg"].map(de_colors), alpha=alphagrad)
            edgealpha = plt.cm.colors.to_rgba_array(["black" for _ in range(df.shape[0])], alpha=alphagrad)

            fig, ax = plt.subplots()
            for reg, col in de_colors.items():
                mask = df["reg"] == reg
                reg_str = f"{reg} (n={np.sum(mask)})"
                ax.scatter(x=log_fc[mask], y=log_pval[mask], s=size_grad[mask], color=colalpha[mask],
                           edgecolors=edgealpha[mask], label=reg_str)

                if reg != "ns":
                    topn = df.loc[mask].nsmallest(top_n, "adj_p_val")
                    feature_text = [plt.text(x=x, y=y, s=s) for x, y, s in
                                    zip(topn["logfc"], topn["log_pval"], topn["feature"])]
                    adjust_text(feature_text, arrowprops=dict(arrowstyle="-", color='k', lw=0.5))

            ax.set_xlim(-xlim, xlim)
            ax.set_xlabel(r"Log$_{2}$ Fold change")
            ax.set_ylabel(r"-Log$_{10}$ p-value")
            ax.legend(frameon=False, fontsize="small")

            figs[contr] = fig
            axs[contr] = ax

        return figs, axs
