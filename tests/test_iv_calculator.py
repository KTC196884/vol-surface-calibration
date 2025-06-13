import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from vol_surface_calibration import PATHS, add_implied_vols

if __name__ == "__main__":
    option_df  = pd.read_pickle(PATHS.option_resampled)
    option_iv  = add_implied_vols(option_df)
    option_iv.to_pickle(PATHS.option_iv)