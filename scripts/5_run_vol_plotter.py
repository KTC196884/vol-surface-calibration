import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

import pandas as pd
from vol_surface_calibration import (
    PATHS,
    plot_dual_axis,
    plot_shared_axes,
    plot_standardised_scatter,
    plot_rank_scatter
)

if __name__ == '__main__':
    vol_metric_df = pd.read_pickle(PATHS.vol_metric)
    plot_dual_axis(
        x=vol_metric_df.index,
        y1=vol_metric_df['close'],
        y2=vol_metric_df['realized_vol'],
        xlabel='Time',
        y1_label='Price',
        y2_label='Realized Volatility',
        legend_labels=('TX Close','Realized Vol'),
        title='TX Close & Realized Volatility',
        output_path=PATHS.futures_realized_vol,
        color1='tab:blue',
        color2='tab:orange'
    )
    
    shared_colors=(('tab:blue','tab:orange'),
                   ('tab:blue','tab:green'),
                   ('tab:purple','tab:orange'))
    
    plot_dual_axis(
        x=vol_metric_df.index,
        y1=vol_metric_df['realized_vol'],
        y2=vol_metric_df['svi_atm_iv'],
        xlabel='Time',
        y1_label='Realized vol.',
        y2_label='ATM IV',
        legend_labels=('Realized vol.','ATM IV'),
        title='Realized vol. vs. ATM IV',
        output_path=PATHS.realized_vs_atm_iv,
        color1=shared_colors[0][0],
        color2=shared_colors[0][1],
    )
    
    plot_shared_axes(
        x=vol_metric_df.index,
        y1=vol_metric_df['realized_vol'],
        y2=vol_metric_df['rs_vol'],
        xlabel='Time',
        ylabel='Volatility',
        legend_labels=('Realized vol.','Rogers‐Satchell vol.'),
        title='Realized vol. vs. Rogers‐Satchell vol. estimator (window=5min)',
        output_path=PATHS.realized_vs_rs,
        color1=shared_colors[1][0],
        color2=shared_colors[1][1],
    )
    
    #%%
    plot_standardised_scatter(
        vol_metric_df['realized_vol'],
        vol_metric_df['svi_atm_iv'],
        xlabel='Realised vol. (Z-score)',
        ylabel='SVI ATM IV (Z-score)',
        title='Standardised Realised vol. vs. ATM IV',
        output_path=PATHS.realised_vs_svi_atm_iv_pearson
    )
    
    plot_standardised_scatter(
        vol_metric_df['realized_vol'],
        vol_metric_df['svi_atm_slope'],
        xlabel='Realised vol. (Z-score)',
        ylabel='SVI ATM slope (Z-score)',
        title='Standardised Realised vol. vs. ATM IV',
        output_path=PATHS.realised_vs_svi_atm_slope_pearson
    )
    
    plot_rank_scatter(
        vol_metric_df['realized_vol'],
        vol_metric_df['svi_atm_iv'],
        xlabel='Realised vol. (rank)',
        ylabel='SVI ATM IV (rank)',
        title='Standardised Realised vol. vs. ATM IV',
        output_path=PATHS.realised_vs_svi_atm_iv_spearman
    )
    
    plot_rank_scatter(
        vol_metric_df['realized_vol'],
        vol_metric_df['svi_atm_slope'],
        xlabel='Realised vol. (rank)',
        ylabel='SVI ATM slope (rank)',
        title='Standardised Realised vol. vs. ATM IV',
        output_path=PATHS.realised_vs_svi_atm_slope_spearman
    )