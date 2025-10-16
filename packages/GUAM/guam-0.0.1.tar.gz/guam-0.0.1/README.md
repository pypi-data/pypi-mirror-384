# GUAM : GPU-based Auto ML for Robust Large Scale Computation.


## Install

Before start, Enviroments must be installed  RAPIDS-23.08 and NVTrabular-23.08(Lastest Version)

```cmd
conda create -n rapids-nvt -c rapidsai -c conda-forge -c nvidia   rapids=23.08 nvtabular=23.08 python=3.10 lightgbm xgboost catboost triton tritonclient grpcio tensorflow tensorflow-gpu cudatoolkit=11.8 -y
```

And, Activate Conda enviroments.

```cmd
conda activate rapids-nvt
```

The latest stable version can always be installed or updated via pip:
```cmd
pip install --upgrade guam
```

## Documentation

## Examples
[LINK]('./examples')