import pandas as pd 
import os
import plotly.express as px
import talib
from talib import abstract
from datetime import *

## function to get Pivot Points, Supports and Resistances
def PPSR(df):  
    PP = pd.Series((df['high'] + df['low'] + df['close']) / 3)  # main pivot level
    # pivot supports level(S1, S2, S3) and resistances level(R1, R2, R3)
    R1 = pd.Series(2 * PP - df['low'])  
    S1 = pd.Series(2 * PP - df['high'])  
    R2 = pd.Series(PP + df['high'] - df['low'])  
    S2 = pd.Series(PP - df['high'] + df['low'])  
    R3 = pd.Series(df['high'] + 2 * (PP - df['low']))  
    S3 = pd.Series(df['low'] - 2 * (df['high'] - PP))  
    psr = {'PP':PP, 'R1':R1, 'S1':S1, 'R2':R2, 'S2':S2, 'R3':R3, 'S3':S3}  
    PSR = pd.DataFrame(psr)
    return PSR


## function to get all indicator in dataframe
def final_indicator(data):
    # converting daily data to monthly data
    nifty_df_monthly = data.groupby(pd.Grouper(freq='M')).agg({"open": "first", 
                                             "high": "max", 
                                             "low": "min", 
                                             "close": "last",
                                             "volume":"sum"})
    nifty_ppsr_monthly = PPSR(nifty_df_monthly) #calling PPSR function to get pivot points, supports and resistances for monthly data

    # getting month and year from index but in df we will take previous month as we have to calculate pivot points for next month
    data['new_date'] = data.index + pd.DateOffset(months=-1)
    data['month-year'] = data['new_date'].dt.strftime('%Y-%m')
    data = data.drop(['new_date'], axis=1)
    nifty_ppsr_monthly['month-year'] = nifty_ppsr_monthly.index.strftime('%Y-%m')

    # merging dataframe df and df1 on month-year column
    df = data.copy()
    df = df.reset_index().merge(nifty_ppsr_monthly, on='month-year')
    df = df.set_index('datetime')

    #taking out rows which are not in the month of current month
    df1 = data.copy()
    df1 = df1[~df1.index.isin(df.index)]

    #concatenating both the dataframes
    df2 = pd.concat([df, df1], axis=0)
    df2 = df2.sort_index(ascending=True)
    
    # calling indicator function to get indicator values
    df3 = indicator(df2)
    df3 = df3.drop(['month-year'], axis=1)

    return df3


def pattern_recognition(df):
    # pattern recognition
    data = df.copy()
    data['engulfing'] = abstract.CDLENGULFING(data)
    data['harami'] = abstract.CDLHARAMI(data)
    data['hammer'] = abstract.CDLHAMMER(data)
    data['shooting_star'] = abstract.CDLSHOOTINGSTAR(data)
    data['doji'] = abstract.CDLDOJI(data)
    data['dragonfly_dogi'] = abstract.CDLDRAGONFLYDOJI(data)
    data['gravestone_dogi'] = abstract.CDLGRAVESTONEDOJI(data)
    return data