# Installation

## Stable release

To install DEPy and all its dependencies, please clone the [DEPy conda environment](../environment.yml):

```sh
conda env create -f environment.yml
conda activate depy
```
This is the intended method of installation.
You *can* install  the 'summarizedpy' package on its own using pip, but please don't.

## pip
```Sh
pip install summarizedpy
```
Note that the SummarizedPy package **must** be run within the **'depy' conda environment** or one cloned from it.

*In short, this is because summarizedpy runs R as a subprocess in a highly defined environment to isolate it from the user's global R environment. This is necessary to ensure that Bioconductor packages load properly.*
