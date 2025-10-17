# DEPy

![PyPI version](https://img.shields.io/pypi/v/DEPy.svg)

A differential expression analysis package for bulk proteomics (and metabolomics) data, which leverages transcriptomics tools.
Inspired by R tools like DEP and SummarizedExperiment, it brings the power of Bioconductor to Python.
All you need is a matrix of features and their intensity values.

* PyPI package: https://pypi.org/project/summarizedpy/
* GitHub: [SebastianDHA/DEPy](https://github.com/SebastianDHA/DEPy)
* Free software: MIT License

## Features

* SummarizedPY: A container for your -omics data, much like SummarizedExperiment or DEP in R.
* Filtering and subsetting your samples and features
* Missing value filtering
* Imputation using ImputeLCMD (many methods)
* Transforming (log, centering, standardizing, vsn)
* Leverage surrogate variable analysis (sva) to adjust for latent batch effects
* Use the flexibility and power of limma-trend to improve your DEA results and accommodate mixed effects
* Limma arrayWeights to adjust variable sample quality (often an issue in human and animal datasets)
* Visualize your DEA results with elegant volcano plots

## Installation
### conda
This is the best way to install DEPy.
```Sh
conda env create -f environment.yml
```
Note that DEPy (summarizedpy) must be run within the [depy conda environment](environment.yml) or a cloned version of it.
This is because summarizedpy needs an isolated environment to run R in due to the complex loading behavior of Bioconductor packages.

## Using pip
```Sh
pip install summarizedpy
```

## Quick start
```Py
import depy as dp

sp = dp.SummarizedPy()
sp = sp.import_from_delim_file(path=path/to/pgroup.tsv, delim="\t")
```
See the full tutorial for more.

## Credits
This package leverages amazing packages from the R and Bioconductor community, including [limma](https://bioconductor.org/packages/3.20/bioc/html/limma.html), [vsn](https://bioconductor.org/packages/release/bioc/html/vsn.html), [sva](https://bioconductor.org/packages/release/bioc/html/sva.html), [ImputeLCMD](https://cran.r-project.org/package=imputeLCMD), and [Tidyverse](https://www.tidyverse.org/).
This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
