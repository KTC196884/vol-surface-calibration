import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import numpy as np
from vol_surface_calibration import (
    PATHS,
    SETTINGS,
    filter_contract_data,
    build_resampled_option_quotes,
    resample_market_price_and_volume,
    read_twse_index
)

#%%
def main():
    all_futures_df = pd.read_csv(
        PATHS.raw_futures_data,
        encoding='big5',
        low_memory=False
    )
    all_futures_df.columns = all_futures_df.columns.str.strip()
    all_futures_df = all_futures_df.rename(columns={
        '成交日期': 'trade_date',
        '商品代號': 'contract_code',
        '到期月份(週別)': 'expiry',
        '成交時間': 'trade_time',
        '成交價格': 'market_price',
        '成交數量(B+S)': 'volume',
        '近月價格': 'near_month_price',
        '遠月價格': 'far_month_price',
        '開盤集合競價': 'opening_call_auction'
    }).assign(
        contract_code=lambda df: df['contract_code'].str.strip(),
        expiry=lambda df: df['expiry'].str.strip()
    )
    
    all_option_df = pd.read_csv(PATHS.raw_option_data, encoding='big5', low_memory=False)
    all_option_df.columns = all_option_df.columns.str.strip()
    all_option_df = all_option_df.rename(columns={
        '成交日期': 'trade_date',
        '商品代號': 'contract_code',
        '履約價格': 'strike',
        '到期月份(週別)': 'expiry',
        '買賣權別': 'option_type',
        '成交時間': 'trade_time',
        '成交價格': 'market_price',
        '成交數量(B or S)': 'volume',
        '開盤集合競價': 'opening_call_auction'
    }).assign(
        contract_code=lambda df: df['contract_code'].str.strip(),
        expiry=lambda df: df['expiry'].str.strip(),
        option_type=lambda df: df['option_type'].str.strip()
    ).iloc[1:].reset_index(drop=True)
    
    #%%
    # Filter for target futures and options of expiry
    futures_df = filter_contract_data(
        df=all_futures_df,
        contract_code=SETTINGS.futures_code,
        expiry=SETTINGS.expiry
    )
    option_df = filter_contract_data(
        df=all_option_df, 
        contract_code=SETTINGS.option_code, 
        expiry=SETTINGS.expiry
    )
    
    #%%
    # 濾掉期貨跨月價差委託
    mask = (futures_df['near_month_price'] != '-') & (futures_df['far_month_price'] != '-')
    futures_df = futures_df[~mask]
    
    #%%
    twse_index_df = read_twse_index(PATHS.raw_twse_index_data)
    
    option_df = pd.merge_asof(
        option_df,
        futures_df['market_price'].rename('futures_price'),
        left_index=True,
        right_index=True,
        direction='backward',
        tolerance=pd.Timedelta('5min')
    )
    option_df = pd.merge_asof(
        option_df,
        twse_index_df['發行量加權股價指數'].rename('underlying_price'),
        left_index=True,
        right_index=True,
        direction='backward',
        tolerance=pd.Timedelta('5min')
    )
    option_df['time_to_expiry'] = (SETTINGS.expiration_ts - option_df.index) / pd.Timedelta(days=365)
    option_df['carry_rate'] = (np.log(option_df['futures_price']) - np.log(option_df['underlying_price'])) / option_df['time_to_expiry']
    
    futures_df = pd.merge_asof(
        futures_df,
        twse_index_df['發行量加權股價指數'].rename('underlying_price'),
        left_index=True,
        right_index=True,
        direction='backward',
        tolerance=pd.Timedelta('5min')
    )
    futures_df['time_to_expiry'] = (SETTINGS.expiration_ts - futures_df.index) / pd.Timedelta(days=365)
    futures_df['carry_rate'] = (np.log(futures_df['market_price']) - np.log(futures_df['underlying_price'])) / futures_df['time_to_expiry']
    
    #%%
    # Build resampled option
    option_resampled_df = build_resampled_option_quotes(option_df)
    
    #%%
    vol_metric_df = resample_market_price_and_volume(
        df=futures_df,
        freq=SETTINGS.demo_resample_freq,
        closed='right',
        label='right'
    )
    
    #%%
    futures_resampled_df = resample_market_price_and_volume(
        df=futures_df,
        freq=SETTINGS.vol_resample_freq,
        closed='right',
        label='right'
    )
    
    #%%
    # Save interim results
    option_resampled_df.to_pickle(PATHS.option_resampled)
    vol_metric_df.to_pickle(PATHS.vol_metric)
    futures_resampled_df.to_pickle(PATHS.futures_resampled)

if __name__ == "__main__":
    main()