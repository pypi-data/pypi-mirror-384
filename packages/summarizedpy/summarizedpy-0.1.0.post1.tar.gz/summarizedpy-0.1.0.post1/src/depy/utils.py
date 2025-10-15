"""Helper to annotate DEA results with 'Up', 'Down', 'ns' for volcano_plot method"""
import pandas as pd
import numpy as np

def _annotate_features_reg(res):
    res = res.copy()
    up = ((res["adj_p_val"] < 0.05) & (res["logfc"] > 0))
    down = ((res["adj_p_val"] < 0.05) & (res["logfc"] < 0))
    res["reg"] = np.select([up, down], ["Up", "Down"], "ns")
    res["reg"] = pd.Categorical(res["reg"], categories=["Up", "Down", "ns"], ordered=True)

    return res
