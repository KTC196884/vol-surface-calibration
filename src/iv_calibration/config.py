# src/iv_calibration/config.py
from typing import Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@dataclass
class Paths:
    raw: Path = PROJECT_ROOT / 'data' / 'raw'
    interim: Path = PROJECT_ROOT / 'data' / 'interim'
    final: Path = PROJECT_ROOT / 'data' / 'final'
    results: Path = PROJECT_ROOT / 'results'
    
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
        return self.interim / 'option_resampled.parquet'

    @property
    def futures_resampled(self) -> Path:
        return self.interim / 'futures_resampled.parquet'

    @property
    def vol_surface_svi(self) -> Path:
        return self.final / 'vol_surface_svi.parquet'

    @property
    def svi_total_ivar_slider(self) -> Path:
        return self.results / 'svi_total_ivar_slider.html'

    @property
    def svi_iv_slider(self) -> Path:
        return self.results / 'svi_iv_slider.html'


@dataclass
class Settings:
    expiration_ts: pd.Timestamp = pd.to_datetime('2023-08-16 13:30:00')
    annualization_factor: pd.Timedelta = pd.Timedelta(days=252)
    carry_rate_default: float = 0.0
    futures_code: str = 'TX'
    option_code: str = 'TXO'
    expiry: str = '202308'
    demo_resample_freq: str = '1min'
    open_time: float = 84500.0
    close_time: float = 134500.0
    sample_start_ts: str = '2023-07-21 08:45:00'
    sample_end_ts: str = '2023-07-21 13:45:00'


@dataclass
class SVISettings:
    global_bounds: Tuple[Tuple[Optional[float], Optional[float]], ...] = (
        (1e-8, None), # a
        (1e-8, None), # b
        (-0.9999, 0.9999), # rho
        (None, None), # m
        (1e-8, None), # sigma
    )
    default_init_params: Tuple[float] = (5.535282e-06, 0.024417, -0.583708, -0.026350, 0.069624)
    call_mask_left: float = -0.01
    put_mask_right: float = 0.01

# instantiate once, import these in your modules:
PATHS    = Paths()
SETTINGS = Settings()
