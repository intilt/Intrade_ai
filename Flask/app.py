from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import boto3
import pandas as pd
import talib

# Creating the low level functional client
client = boto3.client(
    's3',
    aws_access_key_id = 'AKIARJFZWD4TKOK4T2VO',
    aws_secret_access_key = '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',
    region_name = 'ap-south-1'
)

with open('config/config_app.json', 'r') as openfile:
    config_app = json.load(openfile)

app= Flask(__name__)

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

'''@app.route('/check', methods=['GET','POST'])
def check():
    if request.method=='POST':
        #getting values from the form
        instrument=request.form.get('instrument')
        timeframe=request.form.get('timeframe')
        date_from=request.form.get('from')
        date_to=request.form.get('to')
        
        # Create the S3 object
        obj = client.get_object(
            Bucket = 'intrade-dev-data',
            Key = config_app['instrument'][instrument]+instrument+'_'+config_app['timeframe'][timeframe]
            )
        
        #getting path
        path = config_app['instrument'][instrument]+instrument+'_'+config_app['timeframe'][timeframe]
        df = pd.read_csv(path)

        df = pd.read_csv(obj['Body'])

        #as 1min dataframe doesn't have stock_code column
        try:
            df.drop(columns=['stock_code'],inplace=True)
        except:
            pass

        #making datetime as index
        try:
            df['datetime'] =  pd.to_datetime(df['datetime'], infer_datetime_format=True)
        except:
            df['datetime']=df['date']+" "+df['time']
            df['datetime'] =  pd.to_datetime(df['datetime'], infer_datetime_format=True)
        df = df.set_index("datetime")

        #filtering data as per the date range
        df = df.loc[date_from:date_to]
        return render_template('table.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)
    else:
        return render_template('index.html')'''

@app.route('/instruments', methods=['GET'])
def get_instruments():
    return jsonify(list(config_app['instrument'].keys()))
@app.route('/timeframes', methods=['GET'])
def get_timeframes():
    return jsonify(list(config_app['timeframe'].keys()))
@app.route('/indicators', methods=['GET'])
def get_indicators():
    return jsonify(list(config_app['indicators'].keys()))
@app.route("/indicator_params/<indicator>", methods=['GET'])
def get_indicator_params(indicator):
    return jsonify(list(config_app['indicator_params'][indicator].items()))

@app.route('/check', methods=['GET','POST'])
def check():
    if request.method=='POST':
        #getting values from the form
        instrument=request.form.get('instrument')
        timeframe=request.form.get('timeframe')
        date_from=request.form.get('from')
        date_to=request.form.get('to')
        indicators = request.form.getlist('indicator')
        fields = request.form.getlist('field')
        timeperiods = request.form.getlist('timeperiod')
        
        # Create the S3 object
        obj = client.get_object(
            Bucket = 'intrade-dev-data',
            Key = config_app['instrument'][instrument]+instrument+'_'+config_app['timeframe'][timeframe]
            )

        df = pd.read_csv(obj['Body'])

        #as 1min dataframe doesn't have stock_code column
        try:
            df.drop(columns=['stock_code'],inplace=True)
        except:
            pass

        #making datetime as index
        try:
            df['datetime'] =  pd.to_datetime(df['datetime'], infer_datetime_format=True)
        except:
            df['datetime']=df['date']+" "+df['time']
            df['datetime'] =  pd.to_datetime(df['datetime'], infer_datetime_format=True)
        df = df.set_index("datetime")
        
        #filtering data as per the date range
        df = df.loc[date_from:date_to]

        #computing indicators
        for indicator, field, timeperiod in zip(indicators, fields, timeperiods):
            if indicator=='BBANDS':
                df['UP_BB'], df['MID_BB'], df['LOW_BB'] = getattr(talib, indicator)(df[field], timeperiod=int(timeperiod), nbdevup=2, nbdevdn=2, matype=0)
            else:
                df[indicator] = getattr(talib, indicator)(df[field], timeperiod=int(timeperiod))   
        return render_template('table.html',  tables=[df.to_html(classes='data')], titles=df.columns.values)
    else:
        return render_template('index.html')

if __name__=='__main__':
    app.run(debug=True)
