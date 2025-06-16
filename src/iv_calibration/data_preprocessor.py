import numpy as np
import pandas as pd
from pathlib import Path
from typing import Literal
from scipy.stats import norm
from scipy.optimize import brentq
from iv_calibration.config import SETTINGS

def read_twse_index(twse_index_path: Path) -> pd.DataFrame:
    # column 0: 發行量加權股價指數
    with twse_index_path.open(encoding='big5') as f:
        raw_title = f.readline().strip()
    clean_title = raw_title.strip('="')
    date_part = clean_title.split(maxsplit=1)[0]  
    date_part = date_part.replace('年','-').replace('月','-').rstrip('日')
    roc, month, day = date_part.split('-')
    year = int(roc) + 1911
    date_str = f'{year:04d}-{month}-{day}'  # e.g. "2023-07-21"
    
    twse_index_df = pd.read_csv(
        twse_index_path,
        encoding='big5',
        header=1,
        thousands=',',
        dtype={'時間': str},
        low_memory=False,
    )
    twse_index_df['時間'] = twse_index_df['時間'].str.strip('="')
    twse_index_df = twse_index_df[twse_index_df['時間'].str.len() == 8].copy()
    
    twse_index_df['ts'] = pd.to_datetime(
        date_str + ' ' + twse_index_df['時間'],
        format='%Y-%m-%d %H:%M:%S'
    )
    twse_index_df.set_index('ts', inplace=True)
    twse_index_df.drop(columns=['時間'], inplace=True)
    return twse_index_df

def filter_contract_data(
    df: pd.DataFrame,
    contract_code: str,
    expiry: str,
    open_time: float = SETTINGS.open_time,
    close_time: float = SETTINGS.close_time
) -> pd.DataFrame:
    mask = (
        (df['contract_code'] == contract_code) &
        (df['expiry'] == expiry) &
        (df['trade_time'].between(open_time, close_time))
    )
    filtered_df = df.loc[mask].copy()
    filtered_df['ts'] = pd.to_datetime(
        filtered_df['trade_date'].astype(int).astype(str) +
        filtered_df['trade_time'].astype(int).astype(str).str.zfill(6),
        format='%Y%m%d%H%M%S'
    )
    filtered_df = (
        filtered_df
        .drop(columns=['trade_date', 'trade_time', 'contract_code', 'expiry'])
        .set_index('ts')
        .sort_index()
    )
    return filtered_df

def clean_option_df(
    option_df: pd.DataFrame,
    futures_series: pd.Series,
    underlying_series: pd.Series,
) -> pd.DataFrame:
    # Merge forward prices from futures_series
    option_df = pd.merge_asof(
        option_df,
        futures_series.rename("forward_price"),
        left_index=True,
        right_index=True,
        direction="backward",
        tolerance=pd.Timedelta("5min"),
    )

    # Merge underlying prices
    option_df = pd.merge_asof(
        option_df,
        underlying_series.rename("underlying_price"),
        left_index=True,
        right_index=True,
        direction="backward",
        tolerance=pd.Timedelta("5min"),
    )

    # Compute time to expiry
    option_df["time_to_expiry"] = (
        (SETTINGS.expiration_ts - option_df.index)
        / SETTINGS.annualization_factor
    )

    # Compute carry rate
    option_df["carry_rate"] = (
        (np.log(option_df["forward_price"]) - np.log(option_df["underlying_price"]))
         / option_df["time_to_expiry"]
    )
    option_df["carry_rate"] = option_df["carry_rate"].fillna(
        SETTINGS.carry_rate_default
    )

    return option_df

def clean_futures_df(
    futures_df: pd.DataFrame,
    underlying_series: pd.Series
) -> pd.DataFrame:
    # Filter out rows where both month prices are not available
    mask = (
        (futures_df["near_month_price"] != "-")
        & (futures_df["far_month_price"] != "-")
    )
    futures_df = futures_df[~mask]

    # Merge underlying prices
    futures_df = pd.merge_asof(
        futures_df,
        underlying_series.rename("underlying_price"),
        left_index=True,
        right_index=True,
        direction="backward",
        tolerance=pd.Timedelta("5min"),
    )

    # Compute time to expiry
    futures_df["time_to_expiry"] = (
        (SETTINGS.expiration_ts - futures_df.index)
        / SETTINGS.annualization_factor
    )

    # Compute carry rate
    futures_df["carry_rate"] = (
        (np.log(futures_df["market_price"]) - np.log(futures_df["underlying_price"]))
        / futures_df["time_to_expiry"]
    )
    futures_df["carry_rate"] = futures_df["carry_rate"].fillna(
        SETTINGS.carry_rate_default
    )
    return futures_df
    
#%%
def calculate_black_scholes_price(
    option_type: Literal['C', 'P'],
    time_to_expiry: float,
    volatility: float,
    forward_price: float,
    strike: float,
    carry_rate: float = SETTINGS.carry_rate_default,
) -> float:
    if time_to_expiry <= 0 or volatility <= 0:
        return 0.0

    sqrt_t = np.sqrt(time_to_expiry)
    d1 = (
        np.log(forward_price) - np.log(strike)
        + 0.5 * volatility**2 * time_to_expiry
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t

    discount = np.exp(-carry_rate * time_to_expiry)

    if option_type == 'C':
        return discount * (
            forward_price * norm.cdf(d1) - strike * norm.cdf(d2)
        )
    if option_type == 'P':
        return discount * (
            strike * norm.cdf(-d2) - forward_price * norm.cdf(-d1)
        )
    raise ValueError(f"Invalid option_type='{option_type}', expected 'C' or 'P'.")

def calculate_iv_scalar(
    option_type: Literal['C','P'],
    time_to_expiry: float,
    forward_price: float,
    strike: float,
    market_price: float,
    carry_rate: float = SETTINGS.carry_rate_default,
) -> float:
    def objective(vol: float) -> float:
        return calculate_black_scholes_price(
            option_type=option_type,
            time_to_expiry=time_to_expiry,
            volatility=vol,
            forward_price=forward_price,
            strike=strike,
            carry_rate=carry_rate
        ) - market_price
    f_low = objective(1e-9)
    if f_low > 0: return np.nan
    if f_low == 0: return 1e-9
    ub = 5.0
    f_up = objective(ub)
    while f_up < 0 and ub < 50.0:
        ub *= 1.5
        f_up = objective(ub)
    if f_up < 0: return np.nan
    try:
        return brentq(objective, 1e-9, ub, xtol=1e-7, maxiter=100)
    except Exception:
        return np.nan

def calculate_iv(
    option_type: list,
    time_to_expiry: list,
    forward_price: list,
    strike: list,
    market_price: list,
    carry_rate: list,
) -> list:
    return [
        calculate_iv_scalar(
            opt_type,
            tau,
            F,
            K,
            option_price,
            r,
        )
        for opt_type, tau, F, K, option_price, r in zip(
            option_type,
            time_to_expiry,
            forward_price,
            strike,
            market_price,
            carry_rate,
        )
    ]

#%%
def resample_option_df(option_df: pd.DataFrame) -> pd.DataFrame:
    df = option_df.drop(columns=['opening_call_auction'])
    agg_dict = {'volume': 'sum'}
    for col in df.columns:
        if col not in ('volume', 'strike', 'option_type'):
            agg_dict[col] = 'last'
    resampled = (
        df
        .groupby([
            pd.Grouper(
                freq=SETTINGS.demo_resample_freq,
                level='ts',
                closed='right',
                label='right'
            ),
            'option_type',
            'strike'
        ], observed=True)
        .agg(agg_dict)
    )
    return resampled