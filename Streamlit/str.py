import sys
sys.path.insert(0, 'C:\\Users\\amrit\\Intrade_ai')
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import utils.data_manipulation as dm
import utils.data_cleaning as dc
import mplfinance as mpf
import talib
from talib import abstract

st.title('Stock Data Visualization')

timeframes = {
    '1 minute': '1T',
    '2 minutes': '2T',
    '3 minutes': '3T',
    '5 minutes': '5T',
    '10 minutes': '10T',
    '15 minutes': '15T',
    '30 minutes': '30T',
    '1 hour': '1h',
    '2 hours': '2h',
    '3 hours': '3h',
    '4 hours': '4h',
    '1 day': '1D',
    '1 week': '1W',
    '1 month': '1M',
    '1 year': '1Y'
}

indicators = {
    'Simple Moving Average': 'SMA',
    'Exponential Moving Average': 'EMA',
    'Relative Strength Index': 'RSI',
    'Average Directional Movement Index': 'ADX',
    'Bollinger Bands': 'BBANDS'
}

fields = ['open','close','high','low']

timeperiods = [10,14,20,100,150,200]

with st.sidebar:
    st.header('Setting up of stock data')
    stock_name = st.radio(
        "Choose an instrument",
        ("Nifty", "Reliance")
    )
    timeframe = st.radio(
        "Choose a timeframe",
        ("1min", "1day")
    )
    #set date range
    start_date = st.date_input("Start date", value=datetime.date(2011, 1, 3), min_value=datetime.date(2011, 1, 3))
    end_date = st.date_input("End date", value=datetime.date(2012, 1, 3))

    #set graph field
    graph_type = st.selectbox(
        "Choose a graph field",fields
    )
    st.header('Choose timeframe for conversion')
    convert_timeframe = st.selectbox(
        "Choose a timeframe",
        list(timeframes.keys())
    )
    st.header('Choose indicator for plotting')
    indicator = st.selectbox(
        "Choose an indicator",
        list(indicators.keys())
    )
    field = st.selectbox(
        "Choose a field",
        fields
    )
    timeperiod = st.selectbox(
        "Choose a timeperiod",
        timeperiods
    )

NIFTY_MIN_FILE = 'Streamlit/nifty_min_continous.csv'
NIFTY_DAILY_FILE = 'Streamlit/nifty_daily_continous.csv'
RELIANCE_MIN_FILE = 'Streamlit/reliance_min_continous.csv'
RELIANCE_DAILY_FILE = 'Streamlit/reliance_daily_continous.csv'

@st.cache_data
def load_data(stock_name,timeframe,start_date,end_date):
    try:
        if stock_name == "Nifty":
            if timeframe == "1min":
                data = pd.read_csv(NIFTY_MIN_FILE)
            else:
                data = pd.read_csv(NIFTY_DAILY_FILE)
        else:
            if timeframe == "1min":
                data = pd.read_csv(RELIANCE_MIN_FILE)
            else:
                data = pd.read_csv(RELIANCE_DAILY_FILE)
    except FileNotFoundError:
        print(f"Error: File not found for {stock_name} {timeframe}")
    except pd.errors.EmptyDataError:
        print(f"Error: Empty data found for {stock_name} {timeframe}")
    # convert the "Date" column to datetime format
    data['datetime'] = pd.to_datetime(data['datetime'], infer_datetime_format=True)
    # set the index to be the "Date" column
    data.set_index('datetime', inplace=True)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    # filter the data based on the date range
    filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
    # return the filtered data
    return filtered_data

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
df = load_data(stock_name,timeframe,start_date,end_date)
# Notify the reader that the data was successfully loaded.
data_load_state.text("Done!")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.dataframe(df)

if st.checkbox(f'Show line graph for {graph_type} values'):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'])])
    st.plotly_chart(fig)

if st.checkbox('Convert data into desire timeframe'):
    if timeframe=='1min':
        cnvt_tf = dm.convert_timeframe_min(df, timeframes[convert_timeframe])
        st.subheader(f'{convert_timeframe} timeframe data')
        st.dataframe(cnvt_tf)
    else:
        cnvt_tf = dm.convert_timeframe_daily(df, timeframes[convert_timeframe])
        st.subheader(f'{convert_timeframe} timeframe data')
        st.dataframe(cnvt_tf)

if st.checkbox(f'Get indicator graph'):
    stock_data = df.copy()
    if timeframe == "1day":
        st.subheader(f'{indicator} graph for {field} field having {timeperiod} timeperiod')
        if indicator=='Bollinger Bands':
            stock_data['UP_BB'], stock_data['MID_BB'], stock_data['LOW_BB'] = getattr(talib, indicators[indicator])(stock_data[field], timeperiod=int(timeperiod), nbdevup=2, nbdevdn=2, matype=0)
            st.line_chart(stock_data[['close','UP_BB','MID_BB','LOW_BB']])
        else:
            stock_data[indicators[indicator]] = getattr(talib, indicators[indicator])(stock_data[field], timeperiod=int(timeperiod))
            st.line_chart(stock_data[['close',indicators[indicator]]])
    else:
        st.text('Choose 1day for plotting')
if st.checkbox('Check'):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'])])

    # Define empty lists to store buy and sell annotations
    buy_dates = []
    sell_dates = []

    # Add button to clear annotations
    if st.button('Clear Annotations'):
        buy_dates = []
        sell_dates = []

    # Define callback function for clicking on chart
    def annotate_point(trace, points, state):
        if state == 'buy':
            buy_dates.append(points.xs[0])
        elif state == 'sell':
            sell_dates.append(points.xs[0])
        else:
            pass

    # Add callback to handle buy and sell clicks
    fig.add_trace(go.Scatter(x=[], y=[], mode='markers', marker=dict(size=8, color='green'), name='Buy'))
    fig.add_trace(go.Scatter(x=[], y=[], mode='markers', marker=dict(size=8, color='red'), name='Sell'))
    fig.data[1].on_click(annotate_point)
    fig.data[2].on_click(annotate_point)

    # Update buy and sell annotations
    fig.data[1].x = buy_dates
    fig.data[1].y = df.loc[df.index.isin(buy_dates)]['high']
    fig.data[2].x = sell_dates
    fig.data[2].y = df.loc[df.index.isin(sell_dates)]['low']

    fig.update_layout(title='My Candlestick Chart')

    st.plotly_chart(fig)

    # Add radio buttons to select annotation state
    current_state = st.radio("Select Annotation", ['None', 'Buy', 'Sell'])