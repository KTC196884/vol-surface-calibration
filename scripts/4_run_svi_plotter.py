import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

import pandas as pd
from vol_surface_calibration import (
    PATHS,
    plot_total_implied_var_svi, 
    plot_implied_vol_svi
)

def main():
    option_iv_df = pd.read_pickle(PATHS.option_iv)
    svi_params_df = pd.read_pickle(PATHS.svi_params)
    vol_metric_df = pd.read_pickle(PATHS.vol_metric)
    plot_total_implied_var_svi(option_iv_df, vol_metric_df, svi_params_df, PATHS.svi_calibration_var)
    plot_implied_vol_svi(option_iv_df, vol_metric_df, svi_params_df, PATHS.svi_calibration_iv)
    
if __name__ == '__main__':
    main()