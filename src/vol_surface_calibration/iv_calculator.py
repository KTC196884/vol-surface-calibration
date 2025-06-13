# src/vol_surface_calibration/iv/compute_iv.py
from typing import Literal
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
from vol_surface_calibration.config import SETTINGS

def calculate_black_scholes_price(
    option_type: Literal['C','P'],
    time_to_expiry: float,
    volatility: float,
    forward_price: float,
    strike: float,
    carry_rate: float = SETTINGS.carry_rate,
) -> float:
    if time_to_expiry <= 0 or volatility <= 0:
        return 0.0
    sqrt_t = np.sqrt(time_to_expiry)
    d1 = (np.log(forward_price / strike) + 0.5 * volatility**2 * time_to_expiry) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    discount = np.exp(-carry_rate * time_to_expiry)
    if option_type == 'C':
        return discount * (forward_price * norm.cdf(d1) - strike * norm.cdf(d2))
    elif option_type == 'P':
        return discount * (strike * norm.cdf(-d2) - forward_price * norm.cdf(-d1))
    else:
        raise ValueError(f"Invalid option_type='{option_type}', expected 'C' or 'P'.")

def calculate_implied_volatility_scalar(
    option_type: Literal['C','P'],
    time_to_expiry: float,
    forward_price: float,
    strike: float,
    market_price: float,
    carry_rate: float = SETTINGS.carry_rate,
) -> float:
    _IV_LOWER_BOUND: float = 1e-9
    _IV_UPPER_BOUND: float = 5.0
    _IV_MAX_SEARCH: float = 50.0
    _IV_TOLERANCE: float = 1e-7
    def objective(vol: float) -> float:
        return calculate_black_scholes_price(
            option_type=option_type,
            time_to_expiry=time_to_expiry,
            volatility=vol,
            forward_price=forward_price,
            strike=strike,
            carry_rate=carry_rate
        ) - market_price
    f_low = objective(_IV_LOWER_BOUND)
    if f_low > 0: return np.nan
    if f_low == 0: return _IV_LOWER_BOUND
    ub = _IV_UPPER_BOUND
    f_up = objective(ub)
    while f_up < 0 and ub < _IV_MAX_SEARCH:
        ub *= 1.5
        f_up = objective(ub)
    if f_up < 0: return np.nan
    try:
        return brentq(objective, _IV_LOWER_BOUND, ub, xtol=_IV_TOLERANCE, maxiter=100)
    except Exception:
        return np.nan

#%%
def add_implied_vols(option_df : pd.DataFrame) -> pd.DataFrame:
    df = option_df.copy()
    
    call_implied_vol_lst = []
    call_total_implied_var_lst = []
    put_implied_vol_lst = []
    put_total_implied_var_lst = []
    
    for ts in df.index:
        time_to_expiry = df.loc[ts, 'time_to_expiry']
        call_strike = df.loc[ts, 'call_strike']
        put_strike = df.loc[ts, 'put_strike']
        forward = df.loc[ts, 'forward_price']
        if time_to_expiry <= 0:
            nan_arr = np.full_like(call_strike, np.nan, dtype=float)
            call_implied_vol_lst.append(nan_arr)
            call_total_implied_var_lst.append(nan_arr)
            nan_arr = np.full_like(put_strike, np.nan, dtype=float)
            put_implied_vol_lst.append(nan_arr)
            put_total_implied_var_lst.append(nan_arr)
            continue
        
        if call_strike.size == 0:
            nan_arr = np.full_like(call_strike, np.nan, dtype=float)
            call_implied_vol_lst.append(nan_arr)
            call_total_implied_var_lst.append(nan_arr)
        else:
            call_implied_vol = [
                calculate_implied_volatility_scalar(
                    option_type='C',
                    time_to_expiry=time_to_expiry,
                    forward_price=forward,
                    strike=strike,
                    market_price=market_price,
                    carry_rate=SETTINGS.carry_rate,
                )
                for strike, market_price in zip(call_strike, df.loc[ts, 'call_market_price'])
            ]
            call_implied_vol_arr = np.array(call_implied_vol, dtype=float)
            call_implied_vol_lst.append(call_implied_vol_arr)
            call_total_implied_var_lst.append(time_to_expiry * (call_implied_vol_arr ** 2))
        
        if put_strike.size == 0:
            nan_arr = np.full_like(put_strike, np.nan, dtype=float)
            put_implied_vol_lst.append(nan_arr)
            put_total_implied_var_lst.append(nan_arr)
        else:
            put_implied_vol = [
                calculate_implied_volatility_scalar(
                option_type='P',
                time_to_expiry=time_to_expiry,
                forward_price=forward,
                strike=strike,
                market_price=market_price,
                carry_rate=SETTINGS.carry_rate,
                )
                for strike, market_price in zip(put_strike, df.loc[ts, 'put_market_price'])
            ]
            put_implied_vol_arr = np.array(put_implied_vol, dtype=float)
            put_implied_vol_lst.append(put_implied_vol_arr)
            put_total_implied_var_lst.append(time_to_expiry * (put_implied_vol_arr ** 2))
    
    df['call_implied_vol'] = call_implied_vol_lst
    df['call_total_implied_var'] = call_total_implied_var_lst
    df['put_implied_vol'] = put_implied_vol_lst
    df['put_total_implied_var'] = put_total_implied_var_lst
    return df