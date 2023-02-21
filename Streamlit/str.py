import sys
sys.path.insert(0, 'C:\\Users\\amrit\\Intrade_ai')
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
from streamlit_plotly_events import plotly_events
import utils.data_manipulation as dm
import utils.data_cleaning as dc

st.title('Stock Data Visualization')
'''data_min = dm.get_data("Nifty",'1min')
stock_data = dc.get_continuous_1min_data("Nifty",data_min)
st.dataframe(stock_data)'''
with st.sidebar:
    st.title('Setting up of stock data')
    stock_name = st.radio(
        "Choose an instrument",
        ("Nifty", "Reliance")
    )
    timeframe = st.radio(
        "Choose an instrument",
        ("1min", "1day")
    )
    #set date range
    start_date = st.date_input("Start date", min_value=datetime.date(2011, 1, 3))
    end_date = st.date_input("End date")

    #set graph field
    graph_type = st.selectbox(
        "Choose a graph field",('open','close','high','low')
    )

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_data(start_date,end_date):
    '''data_min = dm.get_data(stock_name,'1min')
    stock_data = dc.get_continuous_1min_data(stock_name,data_min)'''
    # load the data from a file or database
    data = pd.read_csv('Streamlit/nifty_daily_continous.csv')
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
data = load_data(start_date,end_date)
# Notify the reader that the data was successfully loaded.
data_load_state.text("Done!")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.dataframe(data)

if st.checkbox('Show close graph'):
    st.line_chart(data[graph_type])












'''# create the candlestick chart using Plotly
candlestick = go.Candlestick(x=data.index,
                                open=data['open'],
                                high=data['high'],
                                low=data['low'],
                                close=data['close'])

# create the list of annotations
annotations = []

# add a "Buy" annotation at the first candlestick
annotations.append(dict(x=data.index[0],
                        y=data['low'][0],
                        xref='x',
                        yref='y',
                        text='Buy',
                        showarrow=True,
                        arrowhead=1,
                        ax=0,
                        ay=-40))

# add a "Sell" annotation at the last candlestick
annotations.append(dict(x=data.index[-1],
                        y=data['high'][-1],
                        xref='x',
                        yref='y',
                        text='Sell',
                        showarrow=True,
                        arrowhead=1,
                        ax=0,
                        ay=40))

# create the Plotly figure and layout
fig = go.Figure(data=[candlestick])
fig.update_layout(title="Candlestick Chart with Annotations",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    annotations=annotations)

# display the candlestick chart using Plotly
plot = st.plotly_chart(fig)

# add an interactive buy/sell annotation on click
def on_plotly_event(data):
    if data:
        x, y = data['points'][0]['x'], data['points'][0]['y']
        text = st.text_input("Enter annotation text:")
        if text:
            annotations = plot.figure.layout.annotations or []
            annotations.append(dict(x=x,
                                    y=y,
                                    xref='x',
                                    yref='y',
                                    text=text,
                                    showarrow=True,
                                    arrowhead=1,
                                    ax=0,
                                    ay=40 if text == "Buy" else -40))
            plot.update_layout(annotations=annotations)

plotly_events(plot, on_plotly_event)'''