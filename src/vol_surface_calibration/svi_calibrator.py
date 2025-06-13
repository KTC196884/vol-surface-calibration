from typing import Sequence, Optional, Union
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from vol_surface_calibration.config import SETTINGS, SVISettings

def compute_svi_total_implied_var(
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
    model_total_implied_var = compute_svi_total_implied_var(log_moneyness, a, b, rho, m, sigma)
    loss_func_value = float(np.sum(volume * (model_total_implied_var - market_total_implied_var) ** 2))
    # loss_func_value = float(np.sum(model_total_implied_var - market_total_implied_var) ** 2)
    return loss_func_value

def calibrate_svi(
    log_moneyness: np.ndarray,
    market_total_implied_var: np.ndarray,
    volume: np.ndarray,
    init_params: Sequence[float] = SVISettings.default_init_params
) -> Optional[np.ndarray]:
    try:
        res = minimize(
            raw_svi_weighted_objective,
            x0=init_params,
            args=(log_moneyness, market_total_implied_var, volume),
            bounds=SVISettings.global_bounds,
            method='L-BFGS-B',
            options={'maxiter': 100000, 'gtol': 1e-12, 'ftol': 1e-12}
        )
    except Exception:
        return None
    return res.x if res.success else None

def compute_svi_params(
    option_iv_df: pd.DataFrame,
    expiration_ts: pd.Timestamp = SETTINGS.expiration_ts
) -> pd.DataFrame:
    """
    Compute SVI parameters for each timestamp in option_iv_df.

    Parameters:
    - option_iv_df: DataFrame indexed by timestamp, containing columns:
        'forward_price', 'call_strike', 'call_total_implied_var', 'call_volume',
        'put_strike', 'put_total_implied_var', 'put_volume'.
    - expiration_ts: pandas.Timestamp of option expiry.

    Returns:
    - DataFrame of SVI parameters ['a', 'b', 'rho', 'm', 'sigma'] indexed by timestamp.
    """
    timestamps = option_iv_df.index
    num_timestamps = len(timestamps)

    # Pull data into arrays/lists once
    forward_prices = option_iv_df['forward_price'].to_numpy()
    call_strikes_list = option_iv_df['call_strike'].tolist()
    call_implied_var_list = option_iv_df['call_total_implied_var'].tolist()
    call_volume_list = option_iv_df['call_volume'].tolist()
    put_strikes_list = option_iv_df['put_strike'].tolist()
    put_implied_var_list = option_iv_df['put_total_implied_var'].tolist()
    put_volume_list = option_iv_df['put_volume'].tolist()

    # Pre-allocate buffer for [a, b, rho, m, sigma]
    svi_params_buffer = np.full((num_timestamps, 5), np.nan, dtype=float)
    previous_fitted_params = None

    for idx, current_timestamp in enumerate(timestamps):
        # Compute time to expiry in years
        time_to_expiry = (expiration_ts - current_timestamp) / pd.Timedelta(days=365)
        if time_to_expiry <= 0:
            continue

        forward_price = forward_prices[idx]

        # Convert lists to arrays for this timestamp
        call_strikes = np.asarray(call_strikes_list[idx])
        call_implied_var = np.asarray(call_implied_var_list[idx])
        call_volumes = np.asarray(call_volume_list[idx])

        put_strikes = np.asarray(put_strikes_list[idx])
        put_implied_var = np.asarray(put_implied_var_list[idx])
        put_volumes = np.asarray(put_volume_list[idx])

        # Calculate log-moneyness and apply masks
        log_moneyness_call = np.log(call_strikes / forward_price)
        valid_call_mask = (log_moneyness_call >= -0.01) & np.isfinite(call_implied_var)

        log_moneyness_put = np.log(put_strikes / forward_price)
        valid_put_mask = (log_moneyness_put <= 0.02) & np.isfinite(put_implied_var)

        # Concatenate valid data
        combined_log_moneyness = np.concatenate([
            log_moneyness_call[valid_call_mask],
            log_moneyness_put[valid_put_mask]
        ])
        combined_implied_var = np.concatenate([
            call_implied_var[valid_call_mask],
            put_implied_var[valid_put_mask]
        ])
        combined_volumes = np.concatenate([
            call_volumes[valid_call_mask],
            put_volumes[valid_put_mask]
        ])

        # Skip if insufficient data
        if combined_log_moneyness.size < 5 or combined_volumes.sum() < 10:
            continue

        # Initialize parameters for calibration
        initial_params = (
            previous_fitted_params
            if previous_fitted_params is not None
            else SVISettings.default_init_params
        )

        # Calibrate SVI and store results
        fitted_params = calibrate_svi(
            combined_log_moneyness,
            combined_implied_var,
            combined_volumes,
            initial_params
        )
        if fitted_params is None:
            continue
        
        svi_params_buffer[idx] = fitted_params
        previous_fitted_params = fitted_params

    # Build DataFrame from buffer
    svi_params_df = pd.DataFrame(
        svi_params_buffer,
        index=timestamps,
        columns=['a', 'b', 'rho', 'm', 'sigma']
    )

    return svi_params_df


def compute_svi_atm_metrics(
    svi_params_df: pd.DataFrame,
    expiration_ts: pd.Timestamp = SETTINGS.expiration_ts
) -> pd.DataFrame:
    time_index = svi_params_df.index
    a_arr     = svi_params_df['a'].to_numpy()
    b_arr     = svi_params_df['b'].to_numpy()
    rho_arr   = svi_params_df['rho'].to_numpy()
    m_arr     = svi_params_df['m'].to_numpy()
    sig_arr   = svi_params_df['sigma'].to_numpy()
    
    time_to_expiry_arr = ((expiration_ts - time_index)/ pd.Timedelta(days=365)).to_numpy(dtype=float)
    
    sqrt_term_arr = np.sqrt(m_arr**2 + sig_arr**2)
    
    atm_var = a_arr + b_arr * ( -rho_arr * m_arr + sqrt_term_arr )
    
    invalid_mask = time_to_expiry_arr <= 0
    time_to_expiry_arr[invalid_mask] = np.nan
    
    atm_iv = np.sqrt(atm_var / time_to_expiry_arr)
    
    atm_slope = (b_arr * (rho_arr - m_arr / sqrt_term_arr) / (2 * atm_iv * time_to_expiry_arr))

    atm_metrics_df = pd.DataFrame({
        'svi_atm_iv': atm_iv,
        'svi_atm_slope': atm_slope
    }, index=time_index)
    
    return atm_metrics_df