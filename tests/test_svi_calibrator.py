import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from iv_calibration import PATHS, compute_svi_params
    
if __name__ == "__main__":
    option_resampled_df = pd.read_parquet(PATHS.option_resampled)
    vol_surface_svi = compute_svi_params(option_resampled_df)