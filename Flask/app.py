from flask import Flask, render_template, request
import pandas as pd
import json

with open('config/config_app.json', 'r') as openfile:
    config_app = json.load(openfile)

app= Flask(__name__)

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/check', methods=['GET','POST'])
def check():
    if request.method=='POST':
        #getting values from the form
        instrument=request.form.get('instrument')
        timeframe=request.form.get('timeframe')
        date_from=request.form.get('from')
        date_to=request.form.get('to')
        
        #getting path
        path = config_app['instrument'][instrument]+instrument+'_'+config_app['timeframe'][timeframe]
        df = pd.read_csv(path)

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
        return render_template('index.html')
if __name__=='__main__':
    app.run(debug=True)
