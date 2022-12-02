import pandas as pd
import talib
from talib import abstract
import numpy as np
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt

plt.rcParams['figure.figsize'] = [12, 7]
plt.rc('font', size=14)

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

## function to get indicator values in dataframe
def indicator(data):
    stock_data = data.copy()
    stock_data['rsi'] = abstract.RSI(data, timeperiod=14) # type: ignore # Relative Strength Index
    stock_data['ema'] = abstract.EMA(data, timeperiod=10) # type: ignore # Exponential Moving Average
    stock_data['sma'] = abstract.SMA(data, timeperiod=20) # type: ignore # Simple Moving Average
    stock_data['UP_BB'], stock_data['MID_BB'], stock_data['LOW_BB'] = talib.BBANDS(stock_data['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0) # type: ignore # Bollinger Bands of upper, middle and lower bands
    return stock_data

## function to get all indicator in dataframe
def get_indicators(data):
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
    nifty_ppsr_monthly['month-year'] = nifty_ppsr_monthly.index.strftime('%Y-%m')  # type: ignore

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
    data['engulfing'] = abstract.CDLENGULFING(data)  # type: ignore
    data['harami'] = abstract.CDLHARAMI(data)  # type: ignore
    data['hammer'] = abstract.CDLHAMMER(data)  # type: ignore
    data['shooting_star'] = abstract.CDLSHOOTINGSTAR(data)  # type: ignore
    data['doji'] = abstract.CDLDOJI(data)  # type: ignore
    data['dragonfly_dogi'] = abstract.CDLDRAGONFLYDOJI(data)   # type: ignore
    data['gravestone_dogi'] = abstract.CDLGRAVESTONEDOJI(data)   # type: ignore
    return data

# Create two functions to calculate if a level is SUPPORT or a RESISTANCE level through fractal identification
def is_Suppport_Level(df, i):
    support = df['low'][i] < df['low'][i - 1] and df['low'][i] < df['low'][i + 1] and df['low'][i + 1] < df['low'][i + 2] and df['low'][i - 1] < df['low'][i - 2]
    return support


def is_Resistance_Level(df, i):
    resistance = df['high'][i] > df['high'][i - 1] and df['high'][i] > df['high'][i + 1] and df['high'][i + 1] > df['high'][i + 2] and df['high'][i - 1] > df['high'][i - 2]
    return resistance

# Plotting the data
def plot_support_resistance_levels(df, levels, level_types):
    fig, ax = plt.subplots()
    candlestick_ohlc(ax, df.values, width=0.6, colorup='green', colordown='red', alpha=0.8)
    date_format = mpl_dates.DateFormatter('%d %b %Y')
    ax.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    fig.tight_layout()

    for level, level_type in zip(levels, level_types):
        plt.hlines(level[1],
                xmin = df['Date'][level[0]],
                xmax = max(df['Date']),
                colors = 'blue')
        plt.text(df['Date'][level[0]], level[1], (str(level_type) + ': ' + str(level[1]) + ' '), ha='right', va='center', fontweight='bold', fontsize='x-small')
        plt.title('Support and Resistance levels', fontsize=24, fontweight='bold')
        fig.show()

# This function, given a price value, returns True or False depending on if it is too near to some previously discovered key level.
def distance_from_mean(df, level,levels):
    # Clean noise in data by discarding a level if it is near another
    # (i.e. if distance to the next level is less than the average candle size for any given day - this will give a rough estimate on volatility)
    mean = np.mean(df['high'] - df['low'])
    return np.sum([abs(level - y) < mean for y in levels]) == 0

def get_support_resistance(df):
    df = df.set_index("datetime")
    df['Date'] = pd.to_datetime(df.index)
    df['Date'] = df['Date'].apply(mpl_dates.date2num)
    df = df.loc[:,['Date', 'open', 'high', 'low', 'close']]
    # Optimizing the analysis by adjusting the data and eliminating the noise from volatility that is causing multiple levels to show/overlapp
    lst = []
    levels = []
    level_types = []
    for i in range(2, df.shape[0] - 2):
        if is_Suppport_Level(df, i):
            level = df['low'][i].round(2)

            if distance_from_mean(df, level,levels):
                lst.append((df.index[i], level, 'Support'))
                levels.append((i, level))
                level_types.append('Support')

        elif is_Resistance_Level(df, i):
            level = df['high'][i].round(2)

            if distance_from_mean(df, level,levels):
                lst.append((df.index[i], level, 'Resistance'))
                levels.append((i, level))
                level_types.append('Resistance')
    plot_support_resistance_levels(df, levels, level_types)
    df1 = pd.DataFrame(lst)
    df1.columns = ['datetime', 'level', 'level_type']
    df1 = df1.set_index('datetime')
    df2 = df.join(df1)
    df2 = df2.drop(['Date'], axis=1)
    return df2