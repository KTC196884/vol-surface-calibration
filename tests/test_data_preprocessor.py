import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from iv_calibration import (
    PATHS,
    SETTINGS,
    read_twse_index,
    filter_contract_data,
    clean_option_df,
    clean_futures_df,
    calculate_iv,
    resample_option_df
)

#%%
if __name__ == "__main__":
    option_resampled_df = pd.read_parquet(PATHS.option_resampled)