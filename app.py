from flask import Flask, render_template, request, redirect

import requests
from bokeh.plotting import figure
from bokeh.embed import components

import pandas as pd

app = Flask(__name__)

app.vars = {}

@app.route('/')
def main():
    return redirect('/index.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method=='GET':
        return render_template('index.html')
    else:
        app.vars['ticker'] = request.form['ticker']
        app.vars['features'] = request.form.getlist('features')
        return redirect('/graph')


@app.route('/graph')
def graph():
    api_url = 'https://www.quandl.com/api/v1/datasets/WIKI/%s.json' % app.vars['ticker']
    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    raw_data = session.get(api_url).json()

    # Pandas application
    df = pd.DataFrame(data=raw_data['data'], columns=raw_data['column_names'])

    # Bokeh application
    p = figure(title = 'Data from Quandle WIKI set',
                x_axis_label = 'date',
                x_axis_type = 'datetime')
    lg = '%s: %s  ' % (app.vars['ticker'], app.vars['features'][0])
    p.line(pd.to_datetime(df['Date']), df[app.vars['features'][0]],
                          line_color='blue', line_width=1.2, legend=lg)
    script, div = components(p)

    subt = 'Generated graph for %s' % app.vars['ticker']
    return render_template('graph.html', script=script, div=div, subtitle=subt)

if __name__ == '__main__':
    app.run(host='0.0.0.0') # The operating system listens on all public IPs.
