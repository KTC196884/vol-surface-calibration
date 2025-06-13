import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from vol_surface_calibration import PATHS, compute_realized_vol, compute_rs_vol

if __name__ == '__main__':
    futures_resampled_df = pd.read_pickle(PATHS.futures_resampled)
    vol_metric_df = pd.read_pickle(PATHS.vol_metric)
    vol_metric_df = compute_realized_vol(futures_resampled_df, vol_metric_df)
    vol_metric_df = compute_rs_vol(futures_resampled_df, vol_metric_df)