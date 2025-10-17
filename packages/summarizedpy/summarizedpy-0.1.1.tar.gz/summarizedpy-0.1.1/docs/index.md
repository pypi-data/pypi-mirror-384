# Welcome to DEPy's documentation!
DEPy (aka **SummarizedPy**) is a Python library for bulk proteomics (and metabolomics) differential expression analysis.
It was inspired by the R packages DEP and SummarizedExperiment.
While Python containers for single-cell data exist within the scverse, tools for bulk -omics are less common, especially when it comes to proteomics.

## Contents

- [Installation](installation.md)
- [Usage](usage.md)
- [API]()
- [History](../HISTORY.md)

## The power of transcriptomics unleashed in MS-based -omics
Discovery proteomics shares a lot of statistical similarities with transcriptomics data once you have the final protein- or peptide-level intensity values (like a protein groups matrix from FragPipe or MaxQuant).

More importantly, bulk -omics often face similar issues: variable sample quality, hidden batch effects, heteroscedasticity, and complex designs.

Fortunately, several tools have been developed in the transcriptomics literature to address these very concerns!
- limma
- arrayWeights
- vsn
- sva

Additionally, there are tools to address MS-based -omics issues, such as missing value imputation (e.g. ImputeLCMD).
User-friendly software like Perseus come with easy filtering, transformation, imputation, and testing.

*Alas, none of this is available in Python...*

## Why DEPy
I spent my PhD leveraging R-based transcriptomics tools to power my proteomics and metabolomics analyses and tackle common issues associated with real-world, human and animal datasets.

As I was migrating my workflows to Python (mainly for ML), I wanted to bring all of that Bioconductor goodness with me.
So, I decided to package it - bringing the best of two worlds.

## Features
- Leverage R packages like limma, arrayWeights, vsn, sva, ImputeLCMD
- Example proteomics dataset for testing and exploring
- SummarizedPy: A container for your data and metadata
- Numpy array-based storage for faster operations and integration with the greater Python stack
- I/O using Feather for memory efficiency and speed
- Isolated R environment run as a subprocess
- Easily scales to hundreds of samples and thousands of features
- History attribute logs every step and parameter setting
- High test coverage

**If that sounds interesting, please read on!**
