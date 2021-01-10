import requests
import simplejson as json
import pandas as pd
import time
import datetime

from bokeh.plotting import figure, output_file, show
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, BooleanFilter, CDSView, Select, Range1d, HoverTool
from bokeh.embed import components

from flask import Flask,render_template,request,redirect

app = Flask(__name__)


@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:  #request is a POST
        ticker = request.form['ticker']
        graph_type = request.form['answer_from_layout']
        return render_template('graph.html')


@app.route('/get_data',methods=['GET','POST'])
def get_data():
    # Get ticker and graph type from user
    ticker = request.form['ticker'] or None         # stock ticker
    graph_type = request.form['answer_from_layout']  # this is the requested type of plot
    
    if ticker == None: # set default ticker to AMZN
        ticker = 'AMZN'
    req = requests.get("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&datatype=json&apikey=U3DXQHI0CO5AJZGF".format(symbol=ticker))

    # Request API
    data = json.loads(req.text)
    df = pd.DataFrame(data['Time Series (Daily)']) # convert to df
    df = df.T #Transpose
    df.columns = ['Open','High','Low','Close','Adjusted close','Volume','Dividend amount','split coefficient']
    year_data = df.head(90).copy() # select last 90 days of the data
   
    year_data['Open']=year_data['Open'].astype(str).astype(float)
    year_data['High']=year_data['High'].astype(str).astype(float)
    year_data['Low']=year_data['Low'].astype(str).astype(float)
    year_data['Close']=year_data['Close'].astype(str).astype(float)
    year_data['dates']=year_data.index
    year_data['dates']=pd.to_datetime(year_data['dates'])

    # Return year_data
    fig=get_graph(year_data,graph_type)
    script, div = components(fig)
    return render_template(('graph.html'), script=script, div=div)

@app.route('/get_graph',methods=['GET','POST'])
def get_graph(df,graph_type):
    source=df
    width = 12 * 60 * 60 * 1000 # half day in ms
    ticker = request.form['ticker']

    if ticker == '':
        ticker = 'AMZN'
    p = figure()
    p = figure(title="{n} Chart of {symbol} (Past 90 Days)".format(symbol=ticker,n=graph_type),
                x_axis_type="datetime", 
                plot_height=600, 
                plot_width=1200)
    p.xaxis.formatter.days = '%m/%d/%Y'

    if graph_type == "Candlestick": #Make candlestick plot
        inc = df.Close > df.Open   #if True, price increased (green candle)
        dec = df.Open  > df.Close  #if True, price decreased (red candle)
        p.segment(source=source, x0='dates', y0='High', x1='dates', y1='Low',color='black') #that's the high-low line
        p.vbar(x=df.dates[inc],width=width, top=df.Open[inc], bottom=df.Close[inc], fill_color="GREEN")
        p.vbar(x=df.dates[dec],width=width, top=df.Open[dec], bottom=df.Close[dec], fill_color="#F2583E")
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = 'Price (USD)'

    else: # Make line plot
        p.line(source=source,x='dates', y='Open')
        p.circle(source=source,x='dates', y='Open',size = 4,color='black')
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = 'Price (USD)'

    return(p)

    
@app.errorhandler(KeyError)
def handle_bad_request(e):
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=False, use_reloader=True)

