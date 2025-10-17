# Usage
## Getting started
To use DEPy in a project, start the 'depy' conda environment:

```Sh
conda activate depy
```
Then, open a script or a Jupyter Notebook and simply:
```python
import depy as dp
```

## Example workflow
### Loading the data
Let's load the example dataset that comes with DEPy (courtesy of the ImputeLCMD package).
This is a real-world proteomics [dataset](https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD000438)
of human cancer cell lines (3,709 features, 12 samples).
Data were processed with MaxQaunt and comes in the form of protein groups and their intensities.
```Py
import depy as dp

sp = dp.SummarizedPy()
sp = sp.load_example_data()
```
### Exploring the SummarizedPy object
Data are stored in three main attributes:
- data (numpy ndarray with float or int dtype)
- features (pandas DataFrame)
- samples (pandas DataFrame)

These can be readily accessed
```Py
# Check expression data
sp.data

# Check feature metadata
sp.features

# Check sample metadata
sp.samples
```
To check current dimensions, we can simply invoke the object or call ```print()``` on it
```Py
# See current dimensions in 'repr' format
sp

# Get a user-friendly summary of the entire object
print(sp)
```
The last statement will reveal another useful attribute, the ```history``` attribute.
```Py
# Check history attribute
sp.history
```
This attribute keeps a faithful record of *everything* you do to the ```SummarizedPy``` object, including function calls and parameters.
This is incredibly handy for reproducibility.

## Subsetting and slicing
```SummarizedPy``` objects can be subset and sliced just like SummarizedExperiment in R.
The objects are indexed as ```sp[features, samples]```
Thus, we can:

```Py
# Get first feature and all samples
sp[1, :]

# Or equivalently
sp[1]

# Get first sample and all features
sp[:, 1]
```
Note that if you subset your ```SummarizedPy```, it will be reflected in the ```history``` attribute:

```Py
# Subset first feature and all samples
sp = sp[1]

# Check history
sp.history
```

### A note on dimensionality
```SummarizedPy``` enforces a 2D constraint on all three main attributes ```data features samples```
such that you always get a 2D ```numpy``` array when calling ```sp.data``` and a full ```pandas```
DataFrame when calling ```sp.features``` or ```sp.samples```

**Critically**, ```SummarizedPy``` enforces the following rules:

```Py
sp.data.shape[0] == sp.features.shape[0]
sp.data.shape[1] == sp.samples.shape[0]
```
Indeed, if you were to try
```Py
import numpy as np
import pandas as pd

data = np.array([[1, 2, 3],
                 [4, 5, 6]])
features = pd.DataFrame({"feature_id": ["feature1", "feature2", "feature3"]})
samples = pd.DataFrame({"sample_id": ["sample1", "sample2"]})

sp = dp.SummarizedPy(data=data,
                features=features,
                samples=samples)
```
You would get a ```ValueError``` saying ```Number of samples (2) does not match number of columns in data (3)```

This is because ```SummarizedPy``` maps ```samples``` and ```features``` to ```data```by indexing.
Thus, order of rows in these attributes is **the** source of truth.

As a consequence, re-assigning ```data``` is not possible and will raise an ```AttributeError```

```Py
import numpy as np
import pandas as pd

data = np.array([[1, 2, 3],
                 [4, 5, 6]])
features = pd.DataFrame({"feature_id": ["feature1", "feature2", "feature3"]})
samples = pd.DataFrame({"sample_id": ["sample1", "sample2", "sample3"]})

sp = dp.SummarizedPy(data=data,
                features=features,
                samples=samples)

# Trying to re-assign .data will raise AttributeError
sp.data = data
```

Similarly, you will not be able to re-assign ```.history``` or ```.results``` (we will see this one later)

You **can** however mutate in-place, but this will **not** be reflected in ```history```
and should therefore be done at your own peril. We like audit trails, right?
```Py
# Mutate in-place possible but not recommended
sp.data[1,1] = 10
```

## Filtering by sample and feature metadata
We can filter the entire ```SummarizedPy``` object based on variables in the ``.features`` and ``.samples`` attributes.
This is easily done using the ```filter_features``` and ``filter_samples`` methods, resp.
These functions take a ``pandas query()`` style expression or a boolean mask.
Returning to our ``load_example_data`` example, we can filter based on sample, metadata:

```Py
# Filtering samples
# Include sample condition variable (first six = ADC; last six = SCC)
sp.samples["condition"] = ["ADC"] * 6 + ["SCC"] * 6

# Filter for SCC samples using pandas query expression
sp = sp.filter_samples(expr="condition=='SCC'")

# Check dimensions
sp

# Check history
sp.history
```
Similarly, we can filter based on feature metadata:

```Py
# Filtering features
# Create boolean vector indicating reverse hits
import re
rev_hits = sp.features["protein_id"].apply(lambda x: bool(re.match("REV", x)))

# Add as feature metadata
sp.features["rev"] = rev_hits

# Filter out reverse hits using pandas query expression
sp = sp.filter_features(expr="~rev")

# Alternatively, use a boolean mask
sp.filter_features(mask=~rev_hits)

# Check dimensions
sp

# Check history
sp.history
```

## Missingness filtering
In MS-based -omics, missing data is a guarantee. Whether you have DDA or DIA, there will NA (or nan) values.
When conducting differential expression analyses, you need sufficient valid values to base your fold changes on.
It makes no sense trying to compute a fold change if one group has 90% missing values for some feature (at least not with linear models).
We will not go into all the reasons for missingness, when it is and when it is not a problem;
rather, we will simply assume that we want some ceiling on missingness.

In Perseus (and proteomics more generally), the standard approaches to missingness filtering include:
- % valid values across **all** samples
- % valid values in **at least one** experimental condition
- % valid values in **every experimental condition**

DEPy caters to all three and lets you set the threshold, expressed as the fraction of valid (i.e. non-nan) values.
Simply set the ```strategy=``` to one of
- ``overall`` (across all samples)
- ```any_condition``` (at least one condition)
- ```all_conditions``` (each condition)

Note that if you use one of the condition-based methods,
you need to set the ```condition_column``` parameter to indicate the name of the column in ``samples`` to filter on.

Finally, set the ```frac``` parameter to the fraction of minimum valid values required (default to 0.75; i.e. $\ge$75% valid value).

```Py
# Confirm the presence of nan values
import numpy as np
np.isnan(sp.data).any()

# Missingness filtering method
# Across all samples (i.e. independent of condition)
sp = sp.filter_missingness(strategy="overall", frac=0.75)

# At least one condition (i.e. as a fraction of either SCC or ADC)
sp = sp.filter_missingness(strategy="any_condition",
                      condition_column="condition",
                      frac=0.75)

# In each condition (i.e. as a fraction of both SCC and ADC)
sp = sp.filter_missingness(strategy="all_conditions",
                      condition_column="condition",
                      frac=0.75)

# Check dimensions
sp

# Check history
sp.history
```

## Transformations
There are several common data transformations and normalizations procedures in proteomics and metabolomics,
each of which can be performed in a sample- or feature-wise manner.
- **log transformation** (partly addresses the inherent heteroscedasticity in intensity data)
- **centering** (subtracting a constant such as mean or median to remove offset differences)
- **standardization** (aka z-scoring; enforces unit variance and symmetry about the mean, i.e. 0)

Another powerful transformation that addresses both heteroscedasticity and can reduce intra-group variance is the
*variance stabilizing normalization*, popularized by the R package ```vsn```.
In short, it uses a generalized logarithm with a linear transformation to remove the asymptote at 0 that otherwise occurs with the standard log transform.
The affine (linear) transformation performs a column-wise centering and scaling with parameters estimated empirically.
This method, initially introduced for microarray studies, has its roots in error models developed for gas chromatography.
Check out the original [paper](https://pubmed.ncbi.nlm.nih.gov/12169536/) by Wolfgang Huber et al.
I personally use this a lot for untargeted metabolomics and with other tools such as [MOFA](https://biofam.github.io/MOFA2/).

While many more transformations exist, the three listed ones are arguably the most common in proteomics.
DEPy gives you the ability to perform each one in a column- or row-wise manner using the ```transform_features``` method.
It uses numpy to make them blazingly fast where possible, and calls R for vsn.

The three main parameters are:
- method: one of ```'log'```, ```'center'```, ```'z-score'```, ```'vsn'```
- by: one of ```'mean'``` or ```'median'``` for ```method='center'``` or an ```int``` for ```method='log'```
- axis: ```0``` for row-wise (feature-wise),  ```1``` column-wise (sample-wise) (omitted for methods ```log``` and ```vsn```)

```Py
# Log transformation (base 2)
sp = sp.transform_features(method="log", by=2)

# Center data sample-wise by median
sp = sp.transform_features(method="center", by="median", axis=1)

# Feature-wise standardization
sp = sp.transform_features(method="z-score", axis=0)

# vsn normalization
sp = sp.transform_features(method="vsn")

# Check data
sp.data

# Check history
sp.history
```

## Imputation
Depending on whom you ask, this is either a valid or questionable idea. We will not debate it here.
I would simply note (based on having conducted systematic trials) that you should **only** impute provided you have a sufficient number of valid values to base the imputation on.
What constitutes *sufficient* is like asking 'how long is a piece of string', but if I *had to* pick a number, I would say $\ge$50% valid values per condition *at a minimum*.

For our purposes here, missingness comes in two flavors:
- MAR (missing at random): the missingness pattern is randomly distributed and independent of the features
- MNAR (missing *not* at random): usually left-censored data in MS-based -omics, whereby features are missing due to low abundance.

DEPy runs the ImputeLCMD R package under the hood. This is a great package, created by Cosmin Lazar et al.
It comes with methods for MAR, MNAR, and *critically*, hybrid MAR-MNAR assumptions.
Which assumption to use is beyond the scope of this tutorial, but check out Lazar's excellent [paper](https://pubmed.ncbi.nlm.nih.gov/26906401/) on the topic.

Accordingly, DEPy comes with all of those methods and supports all native parameters.
Exploring them all is a bit much, so we will only demonstrate the ```hybrid``` method.

```Py
# Filter excessive missinginess
sp = sp.filter_missingness(strategy="overall")

# Impute remaining missing values with hybrid approach
# MAR = KNN (default)
# MNAR = QRILC (default)
sp = sp.impute_missing_values(method="Hybrid", extra_args={"mar": "KNN", "mnar": "QRILC"})

# Check history
sp.history
```

## Surrogate variable analysis
This is an **excellent** tool for any bioinformatician to have in their toolbox. Indeed, it has proven invaluable in some of my own work,
which deals with real-world, messy data from humans and animals. The method is surprisingly intuitive for all its seeming complexity.
Check out the original [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC1994707/) by Leek et al.; it is a fantastic read.

### Why use sva
Sometimes, we have known batch effects or technical covariates that can be readily included in our models as adjustment variables.
However, sometimes, there can be *hidden* batch effects in your data that manifest as latent noise and correlations among features that we cannot account for.
How do you include something you cannot measure?

### This is why sva
In a nutshell, surrogate variable analysis (sva) performs PCA on the residuals of the data matrix after regressing out a fully parametrized models
that includes all known experimental and technical covariates. Then, it uses the resultant factors to capture latent covariation among features,
check which features associates with the factors, computes a new model on the reduced set, and returns the latent factors (aka "surrogate variables"),
which can be included as technical covariates in your subsequent model.

*neat...*

DEPy runs the ```sva``` R package with all its native arguments.
Simply specify your fully parametrized model, including all variables of interest (both experimental ones you care about, and adjustment/technical/batch variables).
Additionally, ```sva``` requires a so-called null model that includes only *known* adjustment variables. If you do not have any known ones, the default is to simply use an intercept model.
Note that you must specify the models with R-style tilde expressions; e.g. ```~var1+var2```

```Py
# Filter excessive missinginess (this is important)
sp = sp.filter_missingness(strategy="overall")

# Log transform data (important)
sp = sp.transform_features(method="log", by=2)

# Optionally, impute missing remaining values (sva excludes any feature with nan values)
sp = sp.impute_missing_values(method="Hybrid")

# Run sva
# Default null model: mod0 = '~1' (intercept-only)
sp = sp.surrogate_variable_analysis(mod="~condition")

# Surrogate variables are added to samples attribute
sp.samples

# Check history
sp.history
```

## limma-trend
Now for the actual differential expression analysis, we will use limma, brain child of Gordon Smyth
(check out the legendary [paper](https://pubmed.ncbi.nlm.nih.gov/16646809/)).
Limma leverages an empirically estimated mean-variance trend as a prior to adjust for the heteroscedastic mean-variance common to so many -omics modalities.
The Bayesian prior serves as a form shrinkage, which mitigates the inflated false positives and negatives
that come with conducting fold change analysis on low- and high-abundant features if the mean-variance is not accounted for.
This is particularly useful for small sample sizes.
Limma-trend was implemented and adapted in the proteomics R packages ```DEqMS``` and ``DEP`` for these very reasons.
Limma has been found to be more powerful and exert better FDR control than standard parametric statistics (i.e. t-test and ANOVA).
Critically, ```limma-trend``` performs about as well when adjusting for the mean-variance trend using the feature-wise intensity distribution as
when using peptide or PSM counts to adjust protein-level variance (see DEqMS [paper](https://pubmed.ncbi.nlm.nih.gov/32205417/)).

Another massive benefit to limma is that it can incorporate sample quality weights calculated by its ```arrayWeights``` function.
In my years, I have found that it makes all the difference when working with data from human and animal samples.
In short, the weights are calculated by allowing each feature to have a sample-specific source of variation.
Using the overall mean-variance trend of the dataset, each sample can be quantified in terms of how much it deviates from the average (i.e. how 'noisy' a sample is).
This information is then incorporated into the weights, which are reciprocal logarithms of that deviation
(e.g. a quality weight of 0.5 is 2x as variable as the average sample; i.e. likely low quality).
The weights take the experimental design into account and can be estimated for each sample or averaged as a function of some covariate
(e.g. if quality was found to be reliably lower due to variable).

Finally, limma is highly flexible due to being a linear model. it can incorporate mixed effects, repeated measures, and between- and within-subjects factors.

Limma is available with most of its native parameters. Simply specify the design, the contrasts, whether to include array weights, etc.
- ```design_formula``` (R-style tilde expression with covariates of interest)
- ```contrasts``` (dictionary with the names and definitions of contrasts)
- ``array_weights`` (boolean; whether to include sample quality weights)

#### A brief note on design formulae
DEPy will automatically enforce a marginal means model; that is, an intercept will **not** be included even if you specify one.
This is to keep the design matrix tidy to ensure proper matching between its column names and contrast terms.
To this end, DEPy will:
- inject a '~' if you forget one
- add a '0+' to the start of the ```design_formula```

In general, the intercept term is often of little interest (it represents the grand average) and will not affect fold changes.

````Py
# Specify design formula (including 'condition' and surrogate variables)
des = "~condition+sv_1+sv_2+sv_3"

# Define contrast (levels must be present in covariates above)
contr = {"SCCvsADC": "SCC-ADC"}

# Run limma-trend with array_weights option
sp = sp.limma_trend_dea(design_formula=des, contrasts=contr, array_weights=True)

# Check newly created results attribute
sp.results

# Check history
sp.history
````

## Volcano plots
Finally, we will plot the estimate log fold changes against the log-transformed nominal p-values per feature for each contrast.
*Better known as a volcano plot.*
This is very simple in DEPy: you can either provide a list contrast names or let DEPy produce one volcano plot per contrast.
Plots are generated with ```matplotlib``` and returned as a tuple of dictionaries with keys = contrast names
and values = ```matplotlib.Figure``` or ```matplotlib.Axes``` objects.

```Py
# Generate volcano plots for all contrasts
fig, ax = sp.volcano_plot()

# Optionally, specify the name of a contrast
sp.volcano_plot(contrasts=["SCCvsADC"])
```
By default, the function plots the top 3 up- and top 3 down-regulated features according to FDR.
This can be changed with the ```top_n``` parameter.
You can also change color scheme by providing a dictionary with names ```'Up'```, ```'Down'```, and ```'ns'```,
and hexcodes or valid color names as values.

```Py
# Highlight top up- and down-regulated features
fig, ax = sp.volcano_plot(top_n=1)

# Change colors
de_colors = {"Up": "red", "Down": "blue", "ns": "white"}
sp.volcano_plot(de_colors=de_colors)
```

There you have it!
