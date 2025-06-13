# src/vol_surface_calibration/config.py
from typing import Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@dataclass
class Paths:
    raw: Path = PROJECT_ROOT / 'data' / 'raw'
    interim: Path = PROJECT_ROOT / 'data' / 'interim'
    figures: Path = PROJECT_ROOT / 'results' / 'figures'
    
    @property
    def raw_option_data(self) -> Path:
        return self.raw / 'OptionsDaily_2023_07_21.csv'
    
    @property
    def raw_futures_data(self) -> Path:
        return self.raw / 'Daily_2023_07_21.csv'
    
    @property
    def raw_twse_index_data(self) -> Path:
        return self.raw / 'MI_5MINS_INDEX.csv'
    
    @property
    def option_resampled(self) -> Path:
        return self.interim / 'option_resampled.pkl'

    @property
    def futures_resampled(self) -> Path:
        return self.interim / 'futures_resampled.pkl'

    @property
    def option_iv(self) -> Path:
        return self.interim / 'option_iv.pkl'

    @property
    def vol_metric(self) -> Path:
        return self.interim / 'vol_metric.pkl'

    @property
    def svi_params(self) -> Path:
        return self.interim / 'svi_params.pkl'

    @property
    def svi_calibration_var(self) -> Path:
        return self.figures / 'svi_calibration_total_implied_var.html'

    @property
    def svi_calibration_iv(self) -> Path:
        return self.figures / 'svi_calibration_iv.html'

    @property
    def futures_realized_vol(self) -> Path:
        return self.figures / 'futures_realized_vol.pdf'

    @property
    def realized_vs_atm_iv(self) -> Path:
        return self.figures / 'realized_vs_atm_implied_vol.pdf'

    @property
    def realized_vs_rs(self) -> Path:
        return self.figures / 'realized_vs_rs.pdf'
    
    @property
    def realised_vs_svi_atm_iv_pearson(self) -> Path:
        return self.figures / 'realised_vs_svi_atm_iv_pearson.pdf'
    
    @property
    def realised_vs_svi_atm_slope_pearson(self) -> Path:
        return self.figures / 'realised_vs_svi_atm_slope_pearson.pdf'
    
    @property
    def realised_vs_svi_atm_iv_spearman(self) -> Path:
        return self.figures / 'realised_vs_svi_atm_iv_spearman.pdf'
    
    @property
    def realised_vs_svi_atm_slope_spearman(self) -> Path:
        return self.figures / 'realised_vs_svi_atm_slope_spearman.pdf'


@dataclass
class Settings:
    expiration_ts: pd.Timestamp = pd.to_datetime('2023-08-16 13:30:00')
    carry_rate: float = 0.0
    futures_code: str = 'TX'
    option_code: str = 'TXO'
    expiry: str = '202308'
    demo_resample_freq: str = '1min'
    vol_resample_freq: str = '10s'
    vol_window: str = '5min'
    open_time: float = 84500.0
    close_time: float = 134500.0
    sample_start_ts: str = '2023-07-21 08:45:00'
    sample_end_ts: str = '2023-07-21 13:45:00'


@dataclass
class SVISettings:
    global_bounds: Tuple[Tuple[Optional[float], Optional[float]], ...] = (
        (5e-9, None),
        (5e-9, None),
        (-0.9999, 0.9999),
        (None, None),
        (1e-8, None),
    )
    # default_init_params: Tuple[float, ...] = (1.000000e-08, 0.024539, -0.619617, -0.031960, 0.073252)
    default_init_params: Tuple[float, ...] = (8.482627e-04, 0.012350, -0.275389, 0.016499, 0.044249)
    call_mask_left: float = -0.01
    put_mask_right: float = 0.01

# instantiate once, import these in your modules:
PATHS    = Paths()
SETTINGS = Settings()
