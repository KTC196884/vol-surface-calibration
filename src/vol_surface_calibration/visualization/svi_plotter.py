import numpy as np
import pandas as pd
import plotly.graph_objects as go
from vol_surface_calibration import SETTINGS
from vol_surface_calibration.svi_calibrator import compute_svi_total_implied_var

def plot_total_implied_var_svi(
    option_iv_df: pd.DataFrame,
    vol_metric_df: pd.DataFrame,
    svi_params_df: pd.DataFrame,
    output_path: str
):
    ts_list = svi_params_df.index
    fig = go.Figure()
    
    shapes_by_ts = []
    grey_ref_line = dict(                  # 固定 x=0 灰線
        type="line", x0=0, x1=0,
        y0=0, y1=1, xref="x", yref="paper",
        line=dict(width=1, dash="dash", color="grey"),
        opacity=0.6
    )
    
    def scale_volumes(vol_array, min_size=8, max_size=20):
        if vol_array.size == 0:
            return np.array([], dtype=float)
        vmin = vol_array.min()
        vmax = vol_array.max()
        if vmax == vmin:
            return np.full_like(vol_array, (min_size + max_size) / 2)
        return (vol_array - vmin) / (vmax - vmin) * (max_size - min_size) + min_size
    
    for i, ts in enumerate(ts_list):
        time_to_expiry = (SETTINGS.expiration_ts - ts) / pd.Timedelta(days=365)
        if time_to_expiry <= 0:
            continue
        
        #%%
        forward = option_iv_df.at[ts, "forward_price"]
        if forward <= 0 or not np.isfinite(forward):
            shapes_by_ts.append([grey_ref_line])
            continue
        ul_price = vol_metric_df.at[ts, 'underlying_price']
        if np.isfinite(ul_price) and ul_price > 0:
            k_under = np.log(ul_price / forward)
            ul_shape = dict(
                type="line", x0=k_under, x1=k_under,
                y0=0, y1=1, xref="x", yref="paper",
                line=dict(width=1, dash="dot", color="black"),
                opacity=0.9
            )
            shapes_by_ts.append([grey_ref_line, ul_shape])
        else:
            shapes_by_ts.append([grey_ref_line])
        
        #%%
        a, b, rho, m, sigma = svi_params_df.loc[ts, ["a","b","rho","m","sigma"]]

        # build call / put arrays
        call_strike = option_iv_df.at[ts, 'call_strike'].astype(float)
        call_total_implied_var = option_iv_df.at[ts, 'call_total_implied_var'].astype(float)
        put_strike = option_iv_df.at[ts, 'put_strike'].astype(float)
        put_total_implied_var = option_iv_df.at[ts, 'put_total_implied_var'].astype(float)

        # filter out non-positive or nan strikes
        mask_call = (call_strike > 0) & np.isfinite(call_strike)
        mask_put  = (put_strike  > 0) & np.isfinite(put_strike)
        call_strike = call_strike[mask_call]
        call_total_implied_var = call_total_implied_var[mask_call]
        put_strike = put_strike[mask_put]
        put_total_implied_var = put_total_implied_var[mask_put]
        
        if call_strike.size == 0 and put_strike.size == 0:
            continue

        # compute log-moneyness
        k_call = np.log(call_strike / forward) if call_strike.size > 0 else np.array([])
        k_put  = np.log(put_strike  / forward) if put_strike.size  > 0 else np.array([])
        
        # ——— 计算过去 50 个 ts（含当前）的最小/最大 strike ———
        start_idx = max(i - 29, 0)
        window_ts = ts_list[start_idx : i + 1]
        all_strikes = []
        for t0 in window_ts:
            cs0 = option_iv_df.at[t0, 'call_strike'].astype(float)
            ps0 = option_iv_df.at[t0, 'put_strike'].astype(float)
            cs0 = cs0[(cs0 > 0) & np.isfinite(cs0)]
            ps0 = ps0[(ps0 > 0) & np.isfinite(ps0)]
            if cs0.size > 0:
                all_strikes.append(cs0)
            if ps0.size > 0:
                all_strikes.append(ps0)

        # 如果窗口里也全是空，就跳过
        if not all_strikes:
            continue

        combined = np.concatenate(all_strikes)
        min_strike = combined.min()
        max_strike = combined.max()

        grid_strikes = np.linspace(min_strike, max_strike, 300)
        grid_k = np.log(grid_strikes / forward)
        svi = compute_svi_total_implied_var(grid_k, a, b, rho, m, sigma)

        visible = (i == 0)
        
        # —— 在这里取得 call/put 的成交量，并按 mask 过滤 —— 
        call_vol = option_iv_df.at[ts, 'call_volume'].astype(float)[mask_call]
        put_vol  = option_iv_df.at[ts, 'put_volume'].astype(float)[mask_put]

        # 线性缩放到 [1,10]
        call_sizes = scale_volumes(call_vol)
        put_sizes  = scale_volumes(put_vol)
        
        # Call points
        fig.add_trace(go.Scatter(
            x=k_call, y=call_total_implied_var, mode="markers",
            name="Call",
            marker=dict(symbol="circle", size=call_sizes),
            visible=visible
        ))
        # Put points
        fig.add_trace(go.Scatter(
            x=k_put, y=put_total_implied_var, mode="markers",
            name="Put",
            marker=dict(symbol="circle", size=put_sizes),
            visible=visible
        ))
        # SVI fit
        fig.add_trace(go.Scatter(
            x=grid_k, y=svi, mode="lines",
            name="SVI fitted",
            line=dict(width=2),
            visible=visible
        ))
        # atm total implied var
        fig.add_trace(
            go.Scatter(
                x=[0.0], y=[(vol_metric_df.at[ts, 'svi_atm_iv'] ** 2) * time_to_expiry],
                mode="markers",
                name="ATM (SVI fitted)",
                marker=dict(symbol="circle", size=10, color="red"),
                visible=visible
            )
        )

    # --- Slider ---
    n_traces_per_ts = 4             # call, put, SVI, ATM　(垂直線已不是 trace)
    total_traces = n_traces_per_ts * len(ts_list)
    steps = []

    for i, ts in enumerate(ts_list):
        vis = [False] * total_traces
        start = i * n_traces_per_ts
        vis[start : start + n_traces_per_ts] = [True] * n_traces_per_ts

        steps.append(dict(
            method="update",
            args=[
                {"visible": vis},                            # traces
                {"title": f"Total Implied Variance: SVI Calibration (volume-weighted) @ {ts.strftime('%H:%M:%S')}",
                 "shapes": shapes_by_ts[i]}                 # <── shape 也一起換
            ],
            label=ts.time().strftime("%H:%M:%S")
        ))

    # -----------------------------------------------------------
    # 3) 初始 layout 掛上 shapes_by_ts[0]
    # -----------------------------------------------------------
    fig.update_layout(
        title=f"Total Implied Variance: SVI Calibration (volume-weighted) @ {ts_list[0].strftime('%H:%M:%S')}",
        xaxis_title="Log-moneyness k = ln(K/F)",
        yaxis_title="Total Implied Variance",
        template="simple_white",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        margin=dict(l=60, r=20, t=80, b=80),
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Selected time: "),
            pad=dict(t=50),
            steps=steps
        )],
        shapes=shapes_by_ts[0]          # <── 初始就顯示第一組
    )

    fig.write_html(str(output_path))
    print(f"互動圖已輸出至 {output_path}，開啟後即可用滑桿切換。")


def plot_implied_vol_svi(
    option_iv_df: pd.DataFrame,
    vol_metric_df: pd.DataFrame,
    svi_params_df: pd.DataFrame,
    output_path: str
):
    ts_list = svi_params_df.index
    fig = go.Figure()
    
    shapes_by_ts = []
    grey_ref_line = dict(                  # 固定 x=0 灰線
        type="line", x0=0, x1=0,
        y0=0, y1=1, xref="x", yref="paper",
        line=dict(width=1, dash="dash", color="grey"),
        opacity=0.6
    )
    
    def scale_volumes(vol_array, min_size=8, max_size=20):
        if vol_array.size == 0:
            return np.array([], dtype=float)
        vmin = vol_array.min()
        vmax = vol_array.max()
        if vmax == vmin:
            # 如果所有成交量都相同，统一给中间值
            return np.full_like(vol_array, (min_size + max_size) / 2)
        return (vol_array - vmin) / (vmax - vmin) * (max_size - min_size) + min_size
    
    for i, ts in enumerate(ts_list):
        time_to_expiry = (SETTINGS.expiration_ts - ts) / pd.Timedelta(days=365)
        if time_to_expiry <= 0:
            continue

        forward = option_iv_df.at[ts, "forward_price"]
        if forward <= 0 or not np.isfinite(forward):
            shapes_by_ts.append([grey_ref_line])
            continue
        ul_price = vol_metric_df.at[ts, 'underlying_price']
        if np.isfinite(ul_price) and ul_price > 0:
            k_under = np.log(ul_price / forward)
            ul_shape = dict(
                type="line", x0=k_under, x1=k_under,
                y0=0, y1=1, xref="x", yref="paper",
                line=dict(width=1, dash="dot", color="black"),
                opacity=0.9
            )
            shapes_by_ts.append([grey_ref_line, ul_shape])
        else:
            shapes_by_ts.append([grey_ref_line])
        
        
        a, b, rho, m, sigma = svi_params_df.loc[ts, ["a","b","rho","m","sigma"]]

        # build call / put arrays
        call_strike = option_iv_df.at[ts, 'call_strike'].astype(float)
        call_implied_vol = option_iv_df.at[ts, 'call_implied_vol'].astype(float)
        put_strike = option_iv_df.at[ts, 'put_strike'].astype(float)
        put_implied_vol = option_iv_df.at[ts, 'put_implied_vol'].astype(float)

        # filter out non-positive or nan strikes
        mask_call = (call_strike > 0) & np.isfinite(call_strike)
        mask_put = (put_strike > 0) & np.isfinite(put_strike)
        call_strike = call_strike[mask_call]
        call_implied_vol = call_implied_vol[mask_call]
        put_strike = put_strike[mask_put]
        put_implied_vol = put_implied_vol[mask_put]

        if call_strike.size == 0 and put_strike.size == 0:
            continue

        # compute log-moneyness
        k_call = np.log(call_strike / forward) if call_strike.size > 0 else np.array([])
        k_put  = np.log(put_strike / forward) if put_strike.size > 0 else np.array([])

        # ——— 计算过去 50 个 ts（含当前）的最小/最大 strike ———
        start_idx = max(i - 29, 0)
        window_ts = ts_list[start_idx : i + 1]
        all_strikes = []
        for t0 in window_ts:
            cs0 = option_iv_df.at[t0, 'call_strike'].astype(float)
            ps0 = option_iv_df.at[t0, 'put_strike'].astype(float)
            cs0 = cs0[(cs0 > 0) & np.isfinite(cs0)]
            ps0 = ps0[(ps0 > 0) & np.isfinite(ps0)]
            if cs0.size > 0:
                all_strikes.append(cs0)
            if ps0.size > 0:
                all_strikes.append(ps0)

        # 如果窗口里也全是空，就跳过
        if not all_strikes:
            continue

        combined = np.concatenate(all_strikes)
        min_strike = combined.min()
        max_strike = combined.max()

        grid_strikes = np.linspace(min_strike, max_strike, 50)
        grid_k = np.log(grid_strikes / forward)
        svi_total_implied_var = compute_svi_total_implied_var(grid_k, a, b, rho, m, sigma)
        svi_implied_vol = np.sqrt(svi_total_implied_var / time_to_expiry)

        visible = (i == 0)
        # —— 在这里取得 call/put 的成交量，并按 mask 过滤 —— 
        call_vol = option_iv_df.at[ts, 'call_volume'].astype(float)[mask_call]
        put_vol  = option_iv_df.at[ts, 'put_volume'].astype(float)[mask_put]

        # 线性缩放到 [1,10]
        call_sizes = scale_volumes(call_vol)
        put_sizes  = scale_volumes(put_vol)
        
        # Call points
        fig.add_trace(go.Scatter(
            x=k_call, y=call_implied_vol, mode="markers",
            name="Call",
            marker=dict(symbol="circle", size=call_sizes),
            visible=visible
        ))
        # Put points
        fig.add_trace(go.Scatter(
            x=k_put, y=put_implied_vol, mode="markers",
            name="Put",
            marker=dict(symbol="circle", size=put_sizes),
            visible=visible
        ))
        # SVI fit
        fig.add_trace(go.Scatter(
            x=grid_k, y=svi_implied_vol, mode="lines",
            name="SVI fitted",
            line=dict(width=2),
            visible=visible
        ))
        # atm total implied var
        fig.add_trace(
            go.Scatter(
                x=[0.0], y=[vol_metric_df.at[ts, 'svi_atm_iv']],
                mode="markers",
                name="ATM (SVI fitted)",
                marker=dict(symbol="circle", size=10, color="red"),
                visible=visible
            )
        )

    # --- Slider ---
    n_traces_per_ts = 4             # call, put, SVI, ATM　(垂直線已不是 trace)
    total_traces = n_traces_per_ts * len(ts_list)
    steps = []

    for i, ts in enumerate(ts_list):
        vis = [False] * total_traces
        start = i * n_traces_per_ts
        vis[start : start + n_traces_per_ts] = [True] * n_traces_per_ts

        steps.append(dict(
            method="update",
            args=[
                {"visible": vis},                            # traces
                {"title": f"Implied Volatility Smile: SVI Calibration (volume-weighted) @ {ts.strftime('%Y-%m-%d %H:%M:%S')}",
                 "shapes": shapes_by_ts[i]}                 # <── shape 也一起換
            ],
            label=ts.time().strftime("%H:%M:%S")
        ))

    # -----------------------------------------------------------
    # 3) 初始 layout 掛上 shapes_by_ts[0]
    # -----------------------------------------------------------
    fig.update_layout(
        title=f"Implied Volatility Smile: SVI Calibration (volume-weighted) @ {ts.strftime('%Y-%m-%d %H:%M:%S')}",
        xaxis_title="Log-moneyness k = ln(K/F)",
        yaxis_title="Total Implied Variance",
        template="simple_white",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        margin=dict(l=60, r=20, t=80, b=80),
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="Selected time: "),
            pad=dict(t=50),
            steps=steps
        )],
        shapes=shapes_by_ts[0]          # <── 初始就顯示第一組
    )

    fig.write_html(str(output_path))
    print(f"互動圖已輸出至 {output_path}，開啟後即可用滑桿切換。")