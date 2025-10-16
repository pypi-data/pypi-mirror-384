#  Intallation

```cmd
conda create -n rapids-nvt -c rapidsai -c conda-forge -c nvidia   rapids=23.08 nvtabular=23.08 python=3.10 lightgbm xgboost catboost triton tritonclient grpcio tensorflow tensorflow-gpu cudatoolkit=11.8 -y
```

```cmd
conda activate rapids-nvt
```