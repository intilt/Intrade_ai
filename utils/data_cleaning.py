import pandas as pd
import numpy as np
import os
import plotly.express as px
import talib
from talib import abstract
from datetime import datetime
import json

with open('../config/config_cleaning.json', 'r') as openfile:
    config_cleaning = json.load(openfile)

## Need to use for daily dataframe
## for the provided data this function captures the list of traded_on_holidays, traded_on_weekends and missing_data.
## Function also returns the continous data
def get_missing_data_dates(stock_name,stock_data):
    
    holidays_file = config_cleaning['file_paths']['holidays_file']
    traded_on_holidays_file = config_cleaning['file_paths']['traded_on_holidays_file']
    traded_on_weekends_file = config_cleaning['file_paths']['traded_on_weekends_file']
    missing_data_file = config_cleaning['file_paths']['missing_data_file']
    
    stock_df = stock_data.copy()
    stock_df.drop(columns=['stock_code'],inplace=True)
    ## convert date to datetime format and make it as index
    stock_df['datetime'] =  pd.to_datetime(stock_df['datetime'], infer_datetime_format=True)
    stock_df = stock_df.set_index("datetime")

    ## Convert to  daily continous data
    stock_df_continous = stock_df.groupby(pd.Grouper(freq='1D')).agg({"open": "first", 
                                             "high": "max", 
                                             "low": "min", 
                                             "close": "last",
                                             "volume":"sum"})
    ## remove null data dates from continous data and capture those rows to na_data
    na_data = stock_df_continous[~stock_df_continous['open'].notna()]
    stock_df_continous = stock_df_continous[stock_df_continous['open'].notna()]
    stock_df_continous = stock_df_continous.sort_index(ascending=True)

    ## Data present on weekends
    traded_on_weekends = stock_df_continous[stock_df_continous.index.day_name().isin(['Saturday', 'Sunday'])]
    print(traded_on_weekends.shape)

    ## Convert holidays data to datetime and make it as index
    holidays = pd.read_csv(holidays_file)
    holidays['date'] = holidays['date'].astype('datetime64[ns]')
    holidays = holidays.set_index("date")

    ## Traded on holidays
    traded_on_holidays = stock_df_continous[stock_df_continous.index.isin(holidays.index)]

    ## remove weekends from null data of continous data
    na_data = na_data[~na_data.index.day_name().isin(['Saturday', 'Sunday'])]
    missing_data = na_data[~na_data.index.isin(holidays.index)]

    if os.path.exists(traded_on_holidays_file):
        a = pd.read_csv(traded_on_holidays_file)
    else:
        a = pd.DataFrame()
    if stock_name not in  a.columns:
        a[stock_name]= pd.Series([str(t) for t in traded_on_holidays.index.date])

    if os.path.exists(traded_on_weekends_file):
        b = pd.read_csv(traded_on_weekends_file)
    else:
        b = pd.DataFrame()
    if stock_name not in  b.columns:
        b[stock_name]= pd.Series([str(t) for t in traded_on_weekends.index.date])

    if os.path.exists(missing_data_file):
        c = pd.read_csv(missing_data_file)
    else:
        c = pd.DataFrame()
    if stock_name not in  c.columns:
        c[stock_name]= pd.Series([str(t) for t in missing_data.index.date])

    a.to_csv(traded_on_holidays_file,index=False)
    b.to_csv(traded_on_weekends_file,index=False)
    c.to_csv(missing_data_file,index=False)

    return stock_df_continous


## 1min data / intraday data
## remove all the null values before first notna index (time) and last notna index (time)
def first_to_last_notna_data(data):
    grouped = data.groupby(pd.Grouper(freq='1D'))
    trimmed_df = pd.DataFrame()
    for name, group in grouped:
        # print(name)
        if group.empty:
            continue
        else:
            trimmed_df = pd.concat([trimmed_df,group[group.first_valid_index():group.last_valid_index()]])
        # print(group)    
    return trimmed_df


## 1min data / intraday data
## removing extra values in others df with count on that day is less than 5
def count_above_5_days(data):
    others_count = data.groupby(pd.Grouper(freq='1D'))['open'].count().reset_index(name='counts')
    # others.to_csv("nifty_others.csv")
    others_count = others_count.set_index('datetime')
    others_count = others_count[others_count['counts']>5]
    return others_count