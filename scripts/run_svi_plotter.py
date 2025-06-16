import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

import pandas as pd
from iv_calibration import (
    PATHS,
    plot_with_slider,
    build_svi_total_ivar_curve,
    build_svi_iv_curve
)

def main():
    option_resampled_df = pd.read_parquet(PATHS.option_resampled)
    vol_surface_svi_df = pd.read_parquet(PATHS.vol_surface_svi)
    
    plot_with_slider(
        option_resampled_df,
        vol_surface_svi_df,
        build_svi_total_ivar_curve,
        'total_ivar',
        'Total Implied Variance',
        PATHS.svi_total_ivar_slider
    )
    
    plot_with_slider(
        option_resampled_df,
        vol_surface_svi_df,
        build_svi_iv_curve,
        'iv',
        'Implied Volitility',
        PATHS.svi_iv_slider
    )
    
if __name__ == '__main__':
    main()