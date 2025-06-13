import numpy as np
import pandas as pd
from pathlib import Path
from vol_surface_calibration.config import SETTINGS

def filter_contract_data(
    df: pd.DataFrame,
    contract_code: str,
    expiry: str,
    open_time: float = SETTINGS.open_time,
    close_time: float = SETTINGS.close_time
) -> pd.DataFrame:
    '''
    Parameters
    ----------
    df : pd.DataFrame containing at least these columns:
        - 'contract_code' (str)
        - 'expiry' (str)
        - 'trade_date' (int or str, format YYYYMMDD)
        - 'trade_time' (int or float, format HHMMSS)

    Returns
    -------
    filtered_df : pd.DataFrame
        indexed by a UTC-localized 'ts' (sorted), containing only
        the filtered rows. Columns 'trade_date', 'trade_time', 'contract_code',
        and 'expiry' are dropped.
    '''
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

def build_resampled_option_quotes(option_df: pd.DataFrame) -> pd.DataFrame:
    full_index = pd.date_range(
        start=SETTINGS.sample_start_ts,
        end=SETTINGS.sample_end_ts,
        freq=SETTINGS.demo_resample_freq
    )
    
    grouped = (
        option_df
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
        .agg(
            last_price = ('market_price', 'last'),
            total_vol = ('volume', 'sum')
        )
        .reset_index()
        .sort_values(['ts','option_type','strike'])
    )

    def _pack_arrays(sub: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            'strike': [sub['strike'].to_numpy()],
            'market_price': [sub['last_price'].to_numpy()],
            'volume' : [sub['total_vol'].to_numpy()]
        }, index=[sub.name])  # sub.name == ts
    
    EMPTY_ARR = np.array([], dtype=float)
    
    # calls
    call_df = (
        grouped[grouped['option_type']=='C']
        .drop(columns='option_type')
        .groupby('ts', observed=True)
        .apply(_pack_arrays)
        .droplevel(1)
        .reindex(full_index, fill_value=EMPTY_ARR)
    ).rename(columns={
        'strike':'call_strike',
        'market_price':'call_market_price',
        'volume':'call_volume'
    })

    # puts
    put_df = (
        grouped[grouped['option_type']=='P']
        .drop(columns='option_type')
        .groupby('ts', observed=True)
        .apply(_pack_arrays)
        .droplevel(1)
        .reindex(full_index, fill_value=EMPTY_ARR)
    ).rename(columns={
        'strike':'put_strike',
        'market_price':'put_market_price',
        'volume':'put_volume'
    })
    
    # time_to_expiry
    time_to_expiry = (
        option_df['time_to_expiry']
        .groupby(pd.Grouper(freq=SETTINGS.demo_resample_freq, level='ts', closed='right', label='right'))
        .last()
        .reindex(full_index)
        .rename('time_to_expiry')
    )
    
    # carry_eate
    carry_rate = (
        option_df['carry_rate']
        .groupby(pd.Grouper(freq=SETTINGS.demo_resample_freq, level='ts', closed='right', label='right'))
        .last()
        .reindex(full_index)
        .rename('carry_rate')
    )
    
    # futures
    futures_price = (
        option_df['futures_price']
        .groupby(pd.Grouper(freq=SETTINGS.demo_resample_freq, level='ts', closed='right', label='right'))
        .last()
        .reindex(full_index)
        .rename('forward_price')
    )
    
    # underlying
    underlying_price = (
        option_df['underlying_price']
        .groupby(pd.Grouper(freq=SETTINGS.demo_resample_freq, level='ts', closed='right', label='right'))
        .last()
        .reindex(full_index)
        .rename('underlying_price')
    )
    
    result_df = pd.concat([call_df, put_df, time_to_expiry, futures_price, underlying_price, carry_rate], axis=1)
    result_df.index.name = 'ts'
    return result_df


def resample_market_price_and_volume(
    df: pd.DataFrame,
    freq: str = SETTINGS.vol_resample_freq,
    closed: str = 'right',
    label: str = 'right'
) -> pd.DataFrame:
    '''
    Resample futures trade data into fixed intervals
    '''
    agg_dict = {
        'market_price': 'ohlc',
        'volume': 'sum',
        'underlying_price': 'last'
    }
    resampled_df = (
        df
        .resample(freq, level='ts', closed=closed, label=label)
        .agg(agg_dict)
    )
    ohlc_cols = resampled_df['market_price'].columns.tolist()
    resampled_df.columns = ohlc_cols + ['volume', 'underlying_price']
    resampled_df.index.name = 'ts'
    resampled_df = resampled_df.sort_index()
    return resampled_df

def read_twse_index(twse_index_path: Path) -> pd.DataFrame:
    # column 0: 發行量加權股價指數
    with twse_index_path.open(encoding='big5') as f:
        raw_title = f.readline().strip()
    clean_title = raw_title.strip('="')
    date_part = clean_title.split(maxsplit=1)[0]  
    date_part = date_part.replace('年','-').replace('月','-').rstrip('日')
    roc, month, day = date_part.split('-')
    year = int(roc) + 1911
    date_str = f"{year:04d}-{month}-{day}"  # e.g. "2023-07-21"
    
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