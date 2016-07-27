from flask import Flask, render_template, request, redirect

import requests
from bokeh.plotting import figure
from bokeh.embed import components

import numpy as np
import pandas as pd
import dill

app = Flask(__name__)
app.vars = {}

@app.route('/')
def main():
    return redirect('/index.html')

MTA_API_BASE= "http://api.prod.obanyc.com/api/siri/vehicle-monitoring.json?key={0}"
MTA_API_KEY = "cad6fe64-9fbd-438f-a232-641caeb16efb"

def _flatten_dict(root_key, nested_dict, flattened_dict):
    for key, value in nested_dict.iteritems():
        next_key = root_key + "_" + key if root_key != "" else key
        if isinstance(value, dict):
            _flatten_dict(next_key, value, flattened_dict)
        else:
            flattened_dict[next_key] = value

    return flattened_dict

#This is useful for the live MTA Data
def nyc_current():
    resp = requests.get(MTA_API_BASE.format(MTA_API_KEY)).json()
    info = resp['Siri']['ServiceDelivery']['VehicleMonitoringDelivery'][0]['VehicleActivity']
    return pd.DataFrame([_flatten_dict('', i, {}) for i in info])

def count_buses_fromhistoricdata():
    with open("./static/manhattan_bus.pkl", "rb") as f:
        df=dill.load(f)
    date_format_str = "%Y-%m-%d %H:%M:%S"
    date_parser = lambda u: pd.datetime.strptime(u, date_format_str)

    init = date_parser("2015-09-"+app.vars['init_Day']+" "
                        +app.vars['init_Hour']+":00:00")
    fin = init.replace(day=init.day, hour=init.hour, minute= (init.minute + 3)%60)
    ending = date_parser("2015-09-"+app.vars['fin_Day']+" "
                        +app.vars['fin_Hour']+":00:00")
    x0=init
    t = []
    count = []
    i=0
    while x0 <= ending:
        x0 = init.replace(day=init.day + i*15//(60*24), hour=init.hour + (i*15//60)%24,
                            minute= init.minute + i*15 % 60)
        x1 = fin.replace(day=fin.day + i*15//(60*24), hour=fin.hour + (i*15//60)%24,
                            minute= fin.minute + i*15 % 60)
        t.append(x0)
        count.append(df[(df.index >= x0) * (df.index <= x1)].unique().size)
        i += 1
    t=pd.Series(t, name="time")
    count=pd.Series(count, name="count")
    app.vars["historic_time"] = t
    app.vars["historic_count"] = count
    return

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method=='GET':
        return render_template('index.html')
    else:
        app.vars['init_Day'] = request.form['init_Day']
        app.vars['init_Hour'] = request.form['init_Hour']
        app.vars['fin_Day'] = request.form['fin_Day']
        app.vars['fin_Hour'] = request.form['fin_Hour']
        count_buses_fromhistoricdata()
        return redirect('/graph')


@app.route('/graph')
def graph():
    # Bokeh application
    p = figure(title = "The number of Buses on the streets in NYC",
                x_axis_label = 'Time',
                x_axis_type = 'datetime')
    #lg = '%s: %s  ' % (app.vars['ticker'], app.vars['features'][0])
    p.line(app.vars["historic_time"], app.vars["historic_count"],
                          line_color='blue', line_width=1.2) #, legend=lg)
    script, div = components(p)

    subt = "The number of Buses from a Historic Data in NYC"
    return render_template('graph.html', script=script, div=div, subtitle=subt)


if __name__ == '__main__':
    app.run(host='0.0.0.0') # The operating system listens on all public IPs.
    #app.run(port=33507, debug=True)


    # api_url = 'https://www.quandl.com/api/v1/datasets/WIKI/%s.json' % app.vars['ticker']
    # session = requests.Session()
    # session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    # raw_data = session.get(api_url).json()
    #
    # # Pandas application
    # df = pd.DataFrame(data=raw_data['data'], columns=raw_data['column_names'])
