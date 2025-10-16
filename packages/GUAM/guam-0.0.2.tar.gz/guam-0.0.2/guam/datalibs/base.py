import os
import numpy as np
import pandas as pd

import cupy as cp
import cudf as cd

import dask.dataframe as dd
import dask_cudf as dcd

from typing import Optional

import nvtabular as nvt
from nvtabular import ops
from ..utils import * 


class DataLoader():
    def __init__(self, 
                 data_source:INPUT_DATA_TYPE,
                 engine:str = None,
                 output_path:str = './processed_data',
                 *args, 
                 **kwargs):
        
        # Set Variable
        self.output_path = output_path

        # Set Output Dirs
        os.makedirs(self.output_path, exist_ok=True)

        # Set Dataset
        self.dataset = self._build_dataset(data_source,  engine, **kwargs)

    def _build_dataset(
            self,
            data_source: INPUT_DATA_TYPE,
            engine:str = None,
            **kwargs
    )->nvt.Dataset:
        r"""
        Args: 
           data_source:
                -
        Returns:
            nvtabular.Dataset
        """

        if isinstance(data_source, (cd.DataFrame, pd.DataFrame, dcd.DataFrame)):
            return nvt.Dataset(data_source, **kwargs)

        # 2. 입력이 Numpy 또는 CuPy 배열인 경우
        elif isinstance(data_source, (np.ndarray, cp.ndarray)):
            # cuDF DataFrame으로 변환하여 처리
            cudf_df = cd.DataFrame(data_source)
            return nvt.Dataset(cudf_df, **kwargs)

        # 3. 입력이 Dictionary인 경우
        elif isinstance(data_source, dict):
            # cuDF DataFrame으로 변환하여 처리
            cudf_df = cd.DataFrame(data_source)
            return nvt.Dataset(cudf_df, **kwargs)

        # 4. 입력이 Dask DataFrame인 경우
        elif isinstance(data_source, dd.DataFrame):
            # Dask DataFrame을 Dask-cuDF DataFrame으로 변환
            dask_cudf_df = dd.from_dask_dataframe(data_source)
            return nvt.Dataset(dask_cudf_df, **kwargs)

        # 5. 입력이 파일 경로(들)인 경우
        elif isinstance(data_source, (str, list)):
            return nvt.Dataset(data_source, engine=engine, **kwargs)

        # 6. 지원하지 않는 타입인 경우
        else:
            raise TypeError(f"Unsupported data source type: {type(data_source)}")
    def _build_workflow(self, workflows:Optional[Union[Dict[str], nvt.Workflow, None]]=None) -> nvt.Workflow:
        if workflows == None:
            return None
        
        elif isinstance(workflows, nvt.Workflow):
            return workflows
        
        elif isinstance(workflows, dict):
            all_pipelines = []

            
            for config in workflows:
                op_chain  = config.selection
                for op in config.ops:
                    pass


    def __call__(self,):
        pass