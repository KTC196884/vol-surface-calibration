from typing import Sequence, Optional, Union
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from iv_calibration.config import SVISettings, SETTINGS

def compute_svi_total_ivar(
    k: Union[float, np.ndarray],
    a: float,
    b: float,
    rho: float,
    m: float,
    sigma: float
) -> Union[float, np.ndarray]:
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))

def raw_svi_weighted_objective(
    params: Sequence[float],
    log_moneyness: np.ndarray,
    market_total_implied_var: np.ndarray,
    volume: np.ndarray
) -> float:
    a, b, rho, m, sigma = params
    model_total_implied_var = compute_svi_total_ivar(log_moneyness, a, b, rho, m, sigma)
    loss_func_value = float(np.sum(volume * (model_total_implied_var - market_total_implied_var) ** 2))
    return loss_func_value

def construct_valid_mask(
    opt_type: np.ndarray,
    log_moneyness: np.ndarray,
    total_ivar: np.ndarray,
    volume: np.ndarray
) -> np.ndarray:
    # 初步過濾：去除非有限值或 volume<=0
    base_mask = (
        np.isfinite(log_moneyness) &
        np.isfinite(total_ivar) &
        (volume > 0)
    )

    # 分別計算 call / put 的 5% volume 閾值（只看 base_mask 內的點）
    is_call = (opt_type == 'C')
    is_put  = (opt_type == 'P')
    
    call_vol_threshold = None
    put_vol_threshold  = None
    
    if np.any(base_mask & is_call):
        call_vol_threshold = np.percentile(volume[base_mask & is_call], 5)
    if np.any(base_mask & is_put):
        put_vol_threshold  = np.percentile(volume[base_mask & is_put], 5)

    # 標記要剔除的 call / put
    remove_call = False
    remove_put  = False

    if call_vol_threshold is not None:
        remove_call = (
            is_call &
            base_mask &
            (log_moneyness < -0.01) &
            (volume <= call_vol_threshold)
        )
    if put_vol_threshold is not None:
        remove_put = (
            is_put &
            base_mask &
            (log_moneyness > 0.01) &
            (volume <= put_vol_threshold)
        )

    # 先符合 base_mask，再剔除上面標記的點
    keep_mask = base_mask & ~(remove_call | remove_put)
    
    # 少於 6 個就全部設為 False
    if sum(keep_mask) < 6:
        keep_mask[:] = False 
        
    return keep_mask

def calibrate_svi(
    opt_type: np.ndarray,
    log_moneyness: np.ndarray,
    total_ivar: np.ndarray,
    volume: np.ndarray,
    init_params: Sequence[float] = SVISettings.default_init_params
) -> Optional[np.ndarray]:
    valid_mask = construct_valid_mask(
        opt_type,
        log_moneyness,
        total_ivar,
        volume
    )
    
    if sum(valid_mask) < 6: return None
    
    try:
        res = minimize(
            raw_svi_weighted_objective,
            x0=init_params,
            args=(
                log_moneyness[valid_mask],
                total_ivar[valid_mask],
                volume[valid_mask]
            ),
            bounds=SVISettings.global_bounds,
            method='L-BFGS-B',
            options={'maxiter': 100000, 'gtol': 1e-12, 'ftol': 1e-12}
        )
    except Exception:
        return None
    return res.x if res.success else None

def compute_svi_params(option_resampled_df: pd.DataFrame) -> pd.DataFrame:
    params_records = []
    init_params = SVISettings.default_init_params
    for ts, group_df in option_resampled_df.groupby(level='ts'):
        opt_type = group_df.index.get_level_values('option_type').values
        strike = group_df.index.get_level_values('strike').values
        forward = group_df['forward_price'].values
        
        params = calibrate_svi(
            opt_type,
            np.log(strike / forward),
            group_df['total_ivar'].values,
            group_df['volume'].values,
            init_params
        )

        if params is None:
            a, b, rho, m, sigma = [np.nan] * 5
            init_params = SVISettings.default_init_params
        else:
            a, b, rho, m, sigma = params
            init_params = params
        
        time_to_expiry = (SETTINGS.expiration_ts - ts) / SETTINGS.annualization_factor
        params_records.append({
            'ts': ts,
            'a': a,
            'b': b,
            'rho': rho,
            'm': m,
            'sigma': sigma,
            'time_to_expiry': time_to_expiry
        })
    
    return pd.DataFrame.from_records(params_records).set_index('ts')