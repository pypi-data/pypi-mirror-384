
import pandas as pd

def create_lag_features(df, columns, lags=[1,2,3]):
    for col in columns:
        for lag in lags:
            df[f'{col}_lag{lag}'] = df[col].shift(lag)
    return df

def create_rolling_features(df, columns, windows=[3,6,12]):
    for col in columns:
        for win in windows:
            df[f'{col}_roll{win}'] = df[col].rolling(win, min_periods=1).mean()
    return df

def create_targets(df):
    # +7-day rain target
    df['rain_7day'] = (df['rain_'].shift(-168) > 0).astype(int)
    # 3-day cumulative precipitation
    df['precip_3day'] = df['precipitation_'].rolling(72, min_periods=1).sum().shift(-71)
    return df
