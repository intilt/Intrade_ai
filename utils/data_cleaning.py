import pandas as pd
import numpy as np
import os
import plotly.express as px
import talib
from talib import abstract
from datetime import datetime,date,time
import json

with open('config/config_cleaning.json', 'r') as openfile:
    config_cleaning = json.load(openfile)

holidays_file = config_cleaning['file_paths']['holidays_file']
traded_on_holidays_file = config_cleaning['file_paths']['traded_on_holidays_file']
traded_on_weekends_file = config_cleaning['file_paths']['traded_on_weekends_file']
missing_data_file = config_cleaning['file_paths']['missing_data_file']
missing_data_file_1min = config_cleaning['file_paths']['missing_data_file_1min']


## Need to use for daily dataframe
## for the provided data this function captures the list of traded_on_holidays, traded_on_weekends and missing_data.
## Function also returns the continous data
def get_missing_data_dates(stock_name,stock_data):
    
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
## capture dates where there is no data atall on that day. returns list of dates
def no_traded_data_days_1min(data):
    grouped = data.groupby(data.index.date)
    no_traded_days = []
    for name, group in grouped:
        # print(name)
        if group.isnull().all().all():
            no_traded_days.append(name)
    no_traded_days = [s.strftime('%Y-%m-%d') for s in no_traded_days]
    return no_traded_days


## 1min data / intraday data
## removing extra values in others df with count on that day is less than 5
def count_above_5_days(data):
    others_count = data.groupby(pd.Grouper(freq='1D'))['open'].count().reset_index(name='counts')
    # others.to_csv("nifty_others.csv")
    others_count = others_count.set_index('datetime')
    others_count = others_count[others_count['counts']>5]
    return others_count


## 1min data / intraday data
## adjust the 1min data with conclusions made from analysis/ data captured post candle close rather than with candle creation during each minute
def time_adjustment(time_index):
    if time_index < datetime(2009,10,22,23,59,59):
        return time_index
    elif datetime(2009,10,23,00,1,1) < time_index < datetime(2009,12,31,23,59,59):
        return time_index - pd.Timedelta(minutes=1)
    elif time_index.date()==date(2010,1,4):
        return time_index - pd.Timedelta(minutes=1)
    elif datetime(2010,1,5,00,1,1) < time_index < datetime(2010,10,15,23,59,59):
        return time_index - pd.Timedelta(minutes=1)
    elif time_index > datetime(2010,10,18,00,1,1):
        return time_index - pd.Timedelta(minutes=1)


## 1min data / intraday data
## creating continous data
def get_continuous_1min_data(stock_name,data):

    data['datetime']=data['date']+" "+data['time']
    data['datetime'] =  pd.to_datetime(data['datetime'], infer_datetime_format=True)
    cols = ['datetime','open','high','low','close']
    data = data[cols]
    data = data.set_index("datetime")
    # min_data.index = min_data.index - pd.Timedelta(minutes=1)

    holidays = pd.read_csv(holidays_file)
    holidays['date'] = holidays['date'].astype('datetime64[ns]')

    # group in 1-minute chunks. 
    t = data.groupby(pd.Grouper(freq='1Min')).agg({"open": "first", 
                                                "high": "max", 
                                                "low": "min", 
                                                "close": "last"})

    ## data between regular market hours
    t_before = t[t.index.date < date(2011,1,3)]
    t_after = t[t.index.date > date(2011,1,2)]

    t_before = t_before[t_before.index.time < time(15,31)]
    t_before = t_before[t_before.index.time > time(9,54)]
    # 2010-10-18
    t_after = t_after[t_after.index.time < time(15,31)]
    t_after = t_after[t_after.index.time > time(9,15)]

    ## combined market hours data
    combined_1min = pd.concat([t_before, t_after])
    combined_1min = combined_1min.sort_index(ascending=True)

    ## Data out of market hours
    others = t[~t.isin(combined_1min)].dropna()
    ## removing extra values in others df with count on that day is less than 5
    others = others[others.index.floor('D').isin(count_above_5_days(others).index)]
    combined_1min = pd.concat([combined_1min, others], sort=False)
    combined_1min = combined_1min.sort_index(ascending=True)

    ## Data in weekends and weekdays
    combined_1min_weekdays = combined_1min[combined_1min.index.dayofweek < 5]
    combined_1min_weekends = combined_1min[combined_1min.index.dayofweek > 4]

    combined_1min_weekends = combined_1min_weekends[combined_1min_weekends.index.floor('D').isin(count_above_5_days(combined_1min_weekends).index)]
    combined_1min_weekends = first_to_last_notna_data(combined_1min_weekends)
    combined_1min = pd.concat([combined_1min_weekdays,combined_1min_weekends])
    combined_1min = combined_1min.sort_index(ascending=True)

    ## Data in holidays
    holidays_list = pd.to_datetime(holidays['date']).dt.date.unique().tolist()
    combined_1min_nonholidays = combined_1min[~combined_1min.index.floor('D').isin(holidays_list)]
    combined_1min_holidays = combined_1min[combined_1min.index.floor('D').isin(holidays_list)]
    ## removing extra values in others df with count on that day is less than 5
    combined_1min_holidays = combined_1min_holidays[combined_1min_holidays.index.floor('D').isin(count_above_5_days(combined_1min_holidays).index)]
    combined_1min_holidays = first_to_last_notna_data(combined_1min_holidays)

    combined_1min = pd.concat([combined_1min_nonholidays,combined_1min_holidays])
    combined_1min = combined_1min.sort_index(ascending=True)

    ## dropping duplicate rows
    combined_1min = combined_1min[(~combined_1min.duplicated()) | (combined_1min['open'].isnull())]

    ## removed data when trading halted
    df_halted = combined_1min.loc['2017-07-10 9:30:00':'2017-07-10 12:30:00']
    combined_1min = combined_1min.drop(df_halted.index)

    df_halted = combined_1min.loc['2021-02-24 11:40:00':'2017-07-10 15:30:00']
    combined_1min = combined_1min.drop(df_halted.index)

    ##IMP## Need to add resumed data on 2021-02-24 from 15:45 to 17:00

    ## remove lunch timings for few dates
    combined_1min_trimmed_time = combined_1min[combined_1min.index.time < time(12,10)]
    combined_1min_trimmed_time = combined_1min_trimmed_time[combined_1min_trimmed_time.index.time > time(11,25)]

    l = no_traded_data_days_1min(combined_1min_trimmed_time)
    ll = [datetime.strptime(x, "%Y-%m-%d").date() for x in l]
    lll = combined_1min_trimmed_time[combined_1min_trimmed_time.index.floor('D').isin(ll)]

    combined_1min = combined_1min.drop(lll.index)

    ## remove dates with no trading data
    no_data_days = no_traded_data_days_1min(combined_1min)
    combined_1min = combined_1min[~combined_1min.index.floor('D').isin(no_data_days)]

    ## adjust time in the data with time_adjustment function
    combined_1min['datetime']= combined_1min.index
    combined_1min['datetime'] = combined_1min['datetime'].apply(lambda x:time_adjustment(x))
    combined_1min.set_index('datetime', inplace=True)

    ## Remove data from 9:00 to 9:14 (pre-opening) from 2010-10-17
    combined_1min = combined_1min.drop(combined_1min[(time(8,59,0)<combined_1min.index.time) & (combined_1min.index.time<time(9,15,0)) & (combined_1min.index.date>date(2010,10,17))].index)
    ## Remove data with NaN at 15:30
    combined_1min = combined_1min.drop(combined_1min[(combined_1min.index.time==time(15,30,00)) & (combined_1min.open.isnull())].index)

    ## get missing data dates in 1min but not in 1 day missing data
    daily_missing_dates = pd.read_csv(missing_data_file)
    stock_daily_missing_dates = daily_missing_dates[stock_name].values.tolist()
    missing_1min_dates = list(set(no_data_days) - set(stock_daily_missing_dates))
    missing_1min_dates.sort()

    if os.path.exists(missing_data_file_1min):
        c = pd.read_csv(missing_data_file_1min)
    else:
        c = pd.DataFrame()
    if stock_name not in  c.columns:
        c[stock_name]= missing_1min_dates

    c.to_csv(missing_data_file_1min,index=False)


    return combined_1min

