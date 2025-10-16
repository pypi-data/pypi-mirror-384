
import cupy as cp
import cudf as cd

import dask
import dask.dataframe as dd

from omegaconf import OmegaConf


from typing import Optional, Dict, List
from ..datalibs.base import DataLoader
from ..utils import *

class AutoML:
    def __init__(
            self,
            data_source:str,
            workflow_config:Optional[str] = './config/workflow_config.yaml',
            models:Optional[List[str]] = ['XGB', 'RF', 'LGBM'],
            state:Optional[str] = None,
            gpus:Optional[bool] =True
    ):
        assert workflow_config is None or workflow_config.endswith('.yaml'), f"Check Pipelines Config now {workflow_config}"

        # Make Using Dask Backend cudf
        if gpus:
            dask.config.set({"dataframe.backend": "cudf"})

        # If user inputs the worflow config, make worfklow
        if workflow_config:
            wconfig = OmegaConf.load(workflow_config).workflow

        # Make DataLoader

        self.DataLoader = DataLoader()