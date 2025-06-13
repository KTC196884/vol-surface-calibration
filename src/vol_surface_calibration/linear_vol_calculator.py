import numpy as np
import pandas as pd
from vol_surface_calibration.config import SETTINGS

def compute_rs_vol(
    futures_resampled_df: pd.DataFrame,
    vol_metric_df: pd.DataFrame
) -> pd.DataFrame:
    df = futures_resampled_df.copy()
    new_vol_metric_df = vol_metric_df.copy()
    
    period_min = pd.to_timedelta(SETTINGS.vol_resample_freq) / pd.Timedelta('1min')
    periods_per_year = (60 * 24 / period_min) * 365
    window_in_min = pd.to_timedelta(SETTINGS.vol_window) / pd.Timedelta('1min')
    window = int(window_in_min / period_min)
    
    ho = np.log(df['high'] / df['open'])
    hc = np.log(df['high'] / df['close'])
    lo = np.log(df['low'] / df['open'])
    lc = np.log(df['low'] / df['close'])
    rs_series = ho * hc + lo * lc
    rs_series = rs_series.dropna()
    
    rolling_mean_rs = rs_series.rolling(window=window, min_periods=window).mean()
    rs_vol = np.sqrt(rolling_mean_rs * periods_per_year)
    
    aligned_series = rs_vol.reindex(
        new_vol_metric_df.index,
        method='ffill',
        tolerance=pd.Timedelta('1min')
    )
    new_vol_metric_df['rs_vol'] = aligned_series
    return new_vol_metric_df

def compute_realized_vol(
    futures_resampled_df: pd.DataFrame,
    vol_metric_df: pd.DataFrame
) -> pd.DataFrame:
    df = futures_resampled_df.copy()
    new_vol_metric_df = vol_metric_df.copy()
    
    period_min = pd.to_timedelta(SETTINGS.vol_resample_freq) / pd.Timedelta('1min')
    periods_per_year = (60 * 24 / period_min) * 365
    window_in_min = pd.to_timedelta(SETTINGS.vol_window) / pd.Timedelta('1min')
    window = int(window_in_min / period_min)
    
    log_close   = np.log(df['close']).dropna()
    log_return  = log_close.diff().dropna()
    
    realized_std = log_return.rolling(window=window, min_periods=window).std()
    realized_vol = realized_std * np.sqrt(periods_per_year)
    
    aligned_series = realized_vol.reindex(
        new_vol_metric_df.index,
        method='ffill',
        tolerance=pd.Timedelta('1min')
    )
    new_vol_metric_df['realized_vol'] = aligned_series
    return new_vol_metric_df