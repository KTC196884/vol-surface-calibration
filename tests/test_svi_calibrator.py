import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from vol_surface_calibration import PATHS, compute_svi_params, compute_svi_atm_metrics
    
if __name__ == "__main__":
    option_iv_df = pd.read_pickle(PATHS.option_iv)
    vol_metric_df = pd.read_pickle(PATHS.vol_metric)
    
    svi_params_df = compute_svi_params(option_iv_df)
    svi_atm_metrics_df = compute_svi_atm_metrics(svi_params_df)
    
    new_vol_metric_df = vol_metric_df.assign(**svi_atm_metrics_df.to_dict('series'))