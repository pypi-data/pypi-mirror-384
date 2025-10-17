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

## Filtering samples and features
