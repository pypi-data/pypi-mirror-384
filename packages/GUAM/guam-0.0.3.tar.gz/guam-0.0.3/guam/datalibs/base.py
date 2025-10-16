import os
import omegaconf
import operator
import numpy as np
import pandas as pd

from operator   import add
from functools  import reduce

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
        
    def _build_workflow(self, workflows:Optional[Union[Dict[str, str], nvt.Workflow, None]]=None) -> Optional[Union[nvt.Workflow, None]]:
        if workflows == None:
            return None
        
        elif isinstance(workflows, nvt.Workflow):
            return workflows
        
        elif isinstance(workflows, omegaconf.listconfig.ListConfig):
            all_pipelines = []

            for config in workflows:
                op_chain    = list(config.get('selection'))
                ops_configs = config.get('ops')
                output      = str(config.get('output_name')) if config.get('output_name') else None

                if ops_configs:
                    op_chain = self._ops_chain_parser(op_chain, ops_configs)
                    
                if output:
                    op_chain = op_chain >> ops.Rename(name=output)

                all_pipelines.append(op_chain)

            if not all_pipelines:
                return None            
            
            return nvt.Workflow(reduce(add, all_pipelines))

        else:
            raise TypeError(f"Unsupported workflow input type: {type(workflows)}")

    def _ops_chain_parser(self, ops_chain:List[str], ops_configs:Optional[Union[omegaconf.listconfig.ListConfig,None]]=None)->None:
        for ops_config in ops_configs:
            for ops_name, ops_params in ops_config.items():
                if ops_params is None:
                    ops_params = {}
                ops_class = getattr(ops, ops_name)
                ops_instance = ops_class(**ops_params)
                ops_chain = ops_chain >> ops_instance
        return ops_chain
            

    def __call__(self, workflow_config: omegaconf.listconfig.ListConfig = None) -> Optional[Union[nvt.Workflow, str]]:
        """Executes the full data processing pipeline."""
        workflow = self._build_workflow(workflow_config)

        if workflow:
            print("Fitting and transforming dataset with the workflow...")
            workflow.fit(self.dataset)
            transformed_dataset = workflow.transform(self.dataset)
        else:
            transformed_dataset = self.dataset

        print(f"Saving processed data to {self.output_path}...")
        transformed_dataset.to_parquet(output_path=self.output_path)
        print("Processing complete.")
        return workflow, self.output_path