from typing import Union, Dict, List
import numpy as np
import pandas as pd

import cupy as cp
import cudf as cd

import dask_cudf as dcd
import dask.dataframe as dd

# MODEL_DICT = {'XGB':,'':}
MODEL_TYPE = ["reg", "binary", "multi"]

INPUT_DATA_TYPE = Union[str, List[str], Dict[str, np.ndarray], np.ndarray, pd.DataFrame, cp.ndarray, cd.DataFrame, dd.DataFrame, dcd.DataFrame]