import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import talib
pio.renderers.default='browser'

def get_candlestick_plot(
        df: pd.DataFrame,
        ind1: str,
        ind2: str,
        time1: int,
        time2: int,
        ticker: str
):
    fig = make_subplots(
        rows = 2,
        cols = 1,
        shared_xaxes = True,
        vertical_spacing = 0.1,
        #subplot_titles = (f'{ticker} Stock Price', 'Volume Chart'),
        subplot_titles = (f'{ticker} Stock Price', 'RSI Chart'),
        row_width = [0.3, 0.7]
    )
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name = 'Candlestick chart'
        ),
        row = 1,
        col = 1,
    )
    
    fig.add_trace(
        go.Line(x = df.index, y = df['indicator1'], name = f'{time1} {ind1}'),
        row = 1,
        col = 1,
    )
    
    fig.add_trace(
        go.Line(x = df.index, y = df['indicator2'], name = f'{time2} {ind2}'),
        row = 1,
        col = 1,
    )
    
    fig.add_trace(
            go.Line(x = df.index, y = talib.RSI(df['close'], timeperiod=14), name = 'RSI'),
            row = 2,
            col = 1,
        )
    
    '''try:
        fig.add_trace(
            go.Bar(x = df.index, y = df['volume'], name = 'Volume'),
            row = 2,
            col = 1,
        )
    except:
        pass'''
    
    fig['layout']['xaxis2']['title'] = 'Date'
    fig['layout']['yaxis']['title'] = 'Price'
    fig['layout']['yaxis2']['title'] = 'RSI'
    
    fig.update_xaxes(
        rangebreaks = [{'bounds': ['sat', 'mon']}],
        rangeslider_visible = False,
    )
    
    return fig