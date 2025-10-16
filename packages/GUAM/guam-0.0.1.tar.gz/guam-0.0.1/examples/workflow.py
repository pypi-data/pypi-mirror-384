from typing import Optional, List
from guam.datalibs import DataLoader


workflows = {
    "featurename":Optional[str],
    "ops": Optional[List[str]],
    "output_feature_name":Optional[str]
}

dataset  = DataLoader()