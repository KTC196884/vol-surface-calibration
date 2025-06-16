import numpy as np
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from iv_calibration.svi_calibrator import compute_svi_total_ivar, construct_valid_mask

def build_svi_total_ivar_curve(
    k_min: float,
    k_max: float,
    vol_slice: pd.Series,
    n_grid: int = 200
):
    k_grid = np.linspace(k_min, k_max, n_grid)
    a, b, rho, m, sigma = vol_slice[['a', 'b', 'rho', 'm', 'sigma']]
    total_ivar = compute_svi_total_ivar(k_grid, a, b, rho, m, sigma)
    return k_grid, total_ivar

def build_svi_iv_curve(k_min, k_max, vol_slice, n_grid=200):
    k_grid = np.linspace(k_min, k_max, n_grid)
    a, b, rho, m, sigma = vol_slice[['a', 'b', 'rho', 'm', 'sigma']]
    time_to_expiry = vol_slice['time_to_expiry']
    total_ivar = compute_svi_total_ivar(k_grid, a, b, rho, m, sigma)
    iv = np.sqrt(total_ivar / time_to_expiry)
    return k_grid, iv

def scale_volumes(vol_array, min_size=8, max_size=22):
    if vol_array.size == 0:
        return np.array([], dtype=float)
    vmin = vol_array.min()
    vmax = vol_array.max()
    if vmax == vmin:
        return np.full_like(vol_array, (min_size + max_size) / 2, dtype=float)
    return (vol_array - vmin) / (vmax - vmin) * (max_size - min_size) + min_size

def plot_with_slider(
    option_resampled_df: pd.DataFrame,
    vol_surface_svi_df: pd.DataFrame,
    y_calibration_func,
    y_column_name: str,
    y_title: str,
    output_path: Path,
    window: int = 20
) -> None:
    ts_list = vol_surface_svi_df.index.tolist()
    
    k_ranges, y_ranges = [], []
    for idx, ts in enumerate(ts_list):
        start, end = max(0, idx-window), min(len(ts_list), idx+window+1)
        all_k, all_y = [], []
        for nts in ts_list[start:end]:
            mkt = option_resampled_df.xs(nts, level="ts")
            forward = mkt["forward_price"].to_numpy(dtype=float)
            strike = mkt.index.get_level_values("strike").astype(float)
            k_vals = np.log(strike / forward)
            y_vals = mkt[y_column_name].to_numpy(dtype=float)
            all_k.append(k_vals)
            all_y.append(y_vals)
        all_k = np.concatenate(all_k)
        all_y = np.concatenate(all_y)
        k_min, k_max = all_k.min(), all_k.max()
        margin = (k_max - k_min) * 0.05
        k_ranges.append((k_min - margin, k_max + margin))
        y_min, y_max = all_y.min(), all_y.max()
        margin = (y_max - y_min) * 0.05
        y_ranges.append((y_min - margin, y_max + margin))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="lines", line=dict(width=2, color="#d62728", dash="dashdot"),
        name="SVI calibrated", legendgroup="svi",
        visible="legendonly", showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers", marker=dict(symbol="circle", size=12, color="#1f77b4"),
        name="Call", legendgroup="call",
        visible="legendonly", showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers", marker=dict(symbol="circle-open", size=12, color="#1f77b4"),
        name="Call (weight zero)", legendgroup="call",
        visible="legendonly", showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers", marker=dict(symbol="circle", size=12, color="#ff7f0e"),
        name="Put", legendgroup="put",
        visible="legendonly", showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers", marker=dict(symbol="circle-open", size=12, color="#ff7f0e"),
        name="Put (weight zero)", legendgroup="put",
        visible="legendonly", showlegend=True
    ))
    
    dynamic_count = 5 
    
    for i, ts in enumerate(ts_list):
        mkt = option_resampled_df.xs(ts, level="ts")
        strike = mkt.index.get_level_values("strike").astype(float)
        forward = mkt["forward_price"].to_numpy(dtype=float)
        k_vals = np.log(strike / forward)
        y_vals = mkt[y_column_name].to_numpy(dtype=float)
        volume = mkt["volume"].to_numpy(dtype=float)
        opt_type = mkt.index.get_level_values("option_type").to_numpy(dtype=str)
        total_ivar = mkt["total_ivar"].to_numpy(dtype=float)
        valid_mask = construct_valid_mask(
            opt_type,
            k_vals,
            total_ivar,
            volume
        )
        
        scatter_size = np.zeros_like(volume, dtype=float)
        scatter_size[valid_mask] = scale_volumes(volume[valid_mask])
        
        kmin, kmax = k_ranges[i]
        k_curve, calibrated_curve = y_calibration_func(kmin, kmax, vol_surface_svi_df.loc[ts])
        fig.add_trace(go.Scatter(
            x = k_curve,
            y = calibrated_curve,
            mode="lines", 
            line=dict(width=2, color="#d62728", dash="dashdot"),
            opacity=0.6,
            name="SVI",
            showlegend=False,
            visible=(i==0)
        ))
        
        call_mask = (opt_type == 'C')
        fig.add_trace(go.Scatter(
            x = k_vals[call_mask & valid_mask],
            y = y_vals[call_mask & valid_mask],
            mode="markers",
            marker=dict(
                symbol="circle",
                size=scatter_size[call_mask & valid_mask],
                opacity=0.7,
                color="#1f77b4"
            ),
            name="Call",
            legendgroup="call",
            showlegend=False,
            visible=(i==0)
        ))
        fig.add_trace(go.Scatter(
            x = k_vals[call_mask & (~valid_mask)],
            y = y_vals[call_mask & (~valid_mask)],
            mode="markers",
            marker=dict(
                symbol="circle-open",
                size=12,
                opacity=1.0,
                color="#1f77b4"
            ),
            name="Call (weight zero)",
            legendgroup="call",
            showlegend=False,
            visible=(i==0)
        ))
        
        put_mask = (opt_type == 'P')
        fig.add_trace(go.Scatter(
            x = k_vals[put_mask & valid_mask], 
            y = y_vals[put_mask & valid_mask],
            mode="markers",
            marker=dict(
                symbol="circle",
                size=scatter_size[put_mask & valid_mask],
                opacity=0.7,
                color="#ff7f0e"),
            name="Put",
            legendgroup="put",
            showlegend=False,
            visible=(i==0)
        ))
        fig.add_trace(go.Scatter(
            x = k_vals[put_mask & (~valid_mask)], 
            y = y_vals[put_mask & (~valid_mask)],
            mode="markers",
            marker=dict(
                symbol="circle-open",
                size=12,
                opacity=1.0,
                color="#ff7f0e"),
            name="Put (weight zero)",
            legendgroup="put",
            showlegend=False,
            visible=(i==0)
        ))
    
    steps = []
    for i, ts in enumerate(ts_list):
        xmin, xmax = k_ranges[i]
        ymin, ymax = y_ranges[i]
        visible = [True] * 5 + [
            (j // dynamic_count) == i
            for j in range(dynamic_count * len(ts_list))
        ]
        steps.append(dict(
            method="update",
            label=ts.strftime("%H:%M"),
            args=[
                {"visible": visible},
                {"title": f"{y_title}: calibration via SVI (volume-weighted) @ {ts}",
                 "xaxis.range": [xmin, xmax],
                 "yaxis.range": [ymin, ymax]}
            ]
        ))
    
    fig.update_layout(
        title=f"{y_title}: calibration via SVI (volume-weighted) @ {ts_list[0]}",
        xaxis=dict(title="Log-moneyness ln(K_i/F_i)", range=k_ranges[0]),
        yaxis=dict(title=f"{y_title}", range=y_ranges[0]),
        template="plotly_white",
        sliders=[dict(
            active=0, 
            currentvalue=dict(prefix="Selected time: "), 
            pad={"t":50}, 
            steps=steps
        )]
    )
    
    fig.show()
    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"已儲存：{Path(output_path).resolve()}")