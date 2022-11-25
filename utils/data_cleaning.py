import pandas as pd
import numpy as np
import os
import plotly.express as px
import talib
from talib import abstract
from datetime import datetime

import json
with open('config/config_cleaning.json', 'r') as openfile:
    config_cleaning = json.load(openfile)

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

