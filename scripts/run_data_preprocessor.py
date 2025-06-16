import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from iv_calibration import (
    PATHS,
    SETTINGS,
    read_twse_index,
    filter_contract_data,
    clean_option_df,
    clean_futures_df,
    calculate_iv,
    resample_option_df
)

#%%
def main():
    twse_index_df = read_twse_index(PATHS.raw_twse_index_data)
    
    all_futures_df = pd.read_csv(PATHS.raw_futures_data, encoding='big5', low_memory=False)
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
    )
    all_option_df = all_option_df.iloc[1:].reset_index(drop=True)
    
    #%%
    futures_df = filter_contract_data(
        df=all_futures_df,
        contract_code=SETTINGS.futures_code,
        expiry=SETTINGS.expiry
    )
    print('futures_df downloaded')
    futures_df = clean_futures_df(futures_df, twse_index_df['發行量加權股價指數'])
    print('futures_df cleaned')
    #%%
    option_df = filter_contract_data(
        df=all_option_df, 
        contract_code=SETTINGS.option_code, 
        expiry=SETTINGS.expiry
    )
    print('option_df downloaded')
    option_df = clean_option_df(option_df, futures_df['market_price'], twse_index_df['發行量加權股價指數'])
    print('option_df cleaned')
    option_df['iv'] = calculate_iv(
        option_df['option_type'],
        option_df['time_to_expiry'],
        option_df['forward_price'],
        option_df['strike'],
        option_df['market_price'],
        option_df['carry_rate']
    )
    option_df['total_ivar'] = option_df['iv'] ** 2 * option_df['time_to_expiry']
    print('iv/total ivar calculated')
    
    #%%
    option_resampled_df = resample_option_df(option_df)
    print('option_resampled_df builded')
    option_resampled_df.to_parquet(
        PATHS.option_resampled,
        engine='pyarrow',
        index=True
    )
    print('option_resampled_df restored')

#%%
if __name__ == "__main__":
    main()