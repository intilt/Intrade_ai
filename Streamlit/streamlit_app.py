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
from draw_candlestick_complex import get_candlestick_plot
import plotly.io as pio

st.title('Stock Dataframe Analysis')

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
    'Average Directional Movement Index': 'ADX'
}

fields = ['open','close','high','low']

timeperiods = [10,14,20,100,150,200]

#sidebar elements
with st.sidebar:
    st.header('Setting up of stock data')
    stock_name = st.radio(
        "Choose an instrument",
        ("Nifty", "Reliance")
    )
    tf = st.radio(
        "Choose a timeframe",
        ("1min", "1day")
    )
    #set date range
    start_date = st.date_input("Start date", value=datetime.date(2011, 1, 3), min_value=datetime.date(2011, 1, 3))
    end_date = st.date_input("End date", value=datetime.date(2011, 4, 30), min_value=datetime.date(2011, 1, 3), max_value=datetime.datetime.now())

NIFTY_MIN_FILE = 'Streamlit/nifty_min_continous.csv'
NIFTY_DAILY_FILE = 'Streamlit/nifty_daily_continous.csv'
RELIANCE_MIN_FILE = 'Streamlit/reliance_min_continous.csv'
RELIANCE_DAILY_FILE = 'Streamlit/reliance_daily_continous.csv'

#load the data and filter it, according to time interva;
@st.cache_data
def load_data(stock_name,tf,start_date,end_date):
    try:
        if stock_name == "Nifty":
            if tf == "1min":
                data = pd.read_csv(NIFTY_MIN_FILE)
            else:
                data = pd.read_csv(NIFTY_DAILY_FILE)
        else:
            if tf == "1min":
                data = pd.read_csv(RELIANCE_MIN_FILE)
            else:
                data = pd.read_csv(RELIANCE_DAILY_FILE)
    except FileNotFoundError:
        print(f"Error: File not found for {stock_name} {tf} data")
    except pd.errors.EmptyDataError:
        print(f"Error: Empty data found for {stock_name} {tf} data")
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
df = load_data(stock_name,tf,start_date,end_date)
# Notify the reader that the data was successfully loaded.
data_load_state.text("Done!")

#show raw data
#if st.checkbox('Show raw data'):
st.subheader('Raw data')
st.dataframe(df)

#show graph
#if st.checkbox(f'Show candlestick graph'):
fig = go.Figure(data=[go.Candlestick(x=df.index,
                                    open=df['open'],
                                    high=df['high'],
                                    low=df['low'],
                                    close=df['close'])])
fig.update_layout(title=f"{stock_name} {tf} data",xaxis_rangeslider_visible=False)
fig.update_xaxes(
        rangebreaks = [{'bounds': ['sat', 'mon']}],
        rangeslider_visible = False,
    )
st.plotly_chart(fig)

if st.checkbox('Convert data into desire timeframe'):
    st.header('Choose timeframe for conversion')
    convert_timeframe = st.sidebar.selectbox(
        "Choose a timeframe",
        list(timeframes.keys())
    )
    if tf=='1min':
        cnvt_tf = dm.convert_timeframe_min(df, timeframes[convert_timeframe])
        st.subheader(f'{convert_timeframe} timeframe data')
        st.dataframe(cnvt_tf)
    else:
        cnvt_tf = dm.convert_timeframe_daily(df, timeframes[convert_timeframe])
        st.subheader(f'{convert_timeframe} timeframe data')
        st.dataframe(cnvt_tf)

if st.checkbox('Show indicator graph'):
    stock_data = df.copy()
    st.sidebar.header('Choose indicator #1')
    indicator1 = st.sidebar.selectbox(
        "Choose an indicator #1",
        list(indicators.keys())
    )
    field1 = st.sidebar.selectbox(
        "Choose a field #1",
        fields
    )
    timeperiod1 = st.sidebar.selectbox(
        "Choose a timeperiod #1",
        timeperiods
    )
    st.sidebar.header('Choose indicator #2')
    indicator2 = st.sidebar.selectbox(
        "Choose an indicator #2",
        list(indicators.keys())
    )
    field2 = st.sidebar.selectbox(
        "Choose a field #2",
        fields
    )
    timeperiod2 = st.sidebar.selectbox(
        "Choose a timeperiod #2",
        timeperiods
    )

    # Get the dataframe and add the moving averages
    stock_data['indicator1'] = getattr(talib, indicators[indicator1])(stock_data[field1], timeperiod=int(timeperiod1))
    stock_data['indicator2'] = getattr(talib, indicators[indicator2])(stock_data[field2], timeperiod=int(timeperiod2))
    #stock_data = stock_data[-days_to_plot:]

    # Display the plotly chart on the dashboard
    st.plotly_chart(
        get_candlestick_plot(stock_data, indicators[indicator1], indicators[indicator2], timeperiod1, timeperiod2, stock_name),
        use_container_width = True,
    )

if st.checkbox('Annotation'):
    stock_data = df.copy()
    # Create a candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=stock_data.index,
                                        open=stock_data['open'],
                                        high=stock_data['high'],
                                        low=stock_data['low'],
                                        close=stock_data['close'])])
    fig.update_layout(xaxis_rangeslider_visible=False)
    # Create a FigureWidget from the Figure object
    fig_widget = go.FigureWidget(fig)

    # Add buttons for manual annotation
    buy_points = []
    sell_points = []
    buy_button = fig_widget.add_annotation(dict(text='Mark as Buy',
                                                showarrow=False,
                                                x=0.05,
                                                y=1.1,
                                                xref='paper',
                                                yref='paper',
                                                font=dict(size=14)))
    sell_button = fig_widget.add_annotation(dict(text='Mark as Sell',
                                                showarrow=False,
                                                x=0.2,
                                                y=1.1,
                                                xref='paper',
                                                yref='paper',
                                                font=dict(size=14)))

    # Define the callback functions for the buttons
    def on_buy_click(trace, points, state):
        # Get the current x-axis value
        x_value = points.xs[0]
        # Add the point to the list and update the chart
        buy_points.append(x_value)
        fig.add_shape(type='line', x0=x_value, y0=0, x1=x_value, y1=1, line=dict(color='green', width=2))
        fig_widget.update()

    def on_sell_click(trace, points, state):
        # Get the current x-axis value
        x_value = points.xs[0]
        # Add the point to the list and update the chart
        sell_points.append(x_value)
        fig.add_shape(type='line', x0=x_value, y0=0, x1=x_value, y1=1, line=dict(color='red', width=2))
        fig_widget.update()

    # Add the callback functions to the chart
    fig_widget.data[0].on_click(on_buy_click)
    fig_widget.data[0].on_click(on_sell_click)

    # Show the chart and the current buy/sell points
    st.plotly_chart(fig_widget)
    st.write('Buy points:', buy_points)
    st.write('Sell points:', sell_points)