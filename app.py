# -*- coding: utf-8 -*-
from __future__ import print_function
from builtins import range  # pylint: disable=redefined-builtin

import collections

import dash
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import numpy as np
import uniform

# variables
MAX_NVARS = 20
variables = collections.OrderedDict([
    ('h2o', dict(label='Water', range=[1.0, 6.0], weight=1.0, unit='ml')),
    ('dmf', dict(label='DMF', range=[1.0, 6.0], weight=1.0, unit='ml')),
    ('etoh', dict(label='Ethanol', range=[1.0, 6.0], weight=1.0, unit='ml')),
    ('meoh', dict(label='Methanol', range=[1.0, 6.0], weight=1.0, unit='ml')),
    ('iproh', dict(
        label='Isopropyl alcohol', range=[1.0, 6.0], weight=1.0, unit='ml')),
    ('r_ratio', dict(
        label='Reactants ratio', range=[0.8, 1.8], weight=1.0, unit=None)),
    ('temperature', dict(
        label='Temperature', range=[100.0, 200.0], weight=1.0, unit='C')),
    ('power', dict(
        label='Microwave Power', range=[150.0, 250.0], weight=2.0, unit='W')),
    ('time', dict(
        label='Reaction time', range=[2.0, 60.0], weight=2.0, unit='min')),
])

# Fill up to MAX_NVARS (needed to define callbacks)
for i in range(len(variables), MAX_NVARS):
    k = 'variable_{}'.format(i + 1)
    variables[k] = dict(label=k, range=[0, 1], weight=1, unit=None)

labels = list(variables.keys())
nq = len(variables)

weight_range = [-1, 1]
ngrid = 5


# pylint: disable=redefined-builtin
def get_controls(id, desc, range, default_weight=0.0):
    """Get controls for one variable.

    This includes
     * the description
     * range 
     * weight
    """
    range_low = dcc.Input(
        id=id + "_low", type='number', value=range[0], className="range")
    range_high = dcc.Input(
        id=id + "_high", type='number', value=range[1], className="range")
    slider = dcc.Slider(
        id=id + "_weight",
        min=weight_range[0],
        max=weight_range[1],
        value=default_weight,
        step=0.01)
    #grid = dcc.Input(id=id + "_grid", type='number', value=ngrid)
    return html.Tr(
        [
            html.Td(desc),
            html.Td([range_low, html.Span('to'), range_high]),
            html.Td([
                html.Span(slider, className="slider"),
                html.Span('', id=id + "_weight_label")
            ])
        ],
        id=id + "_tr")


controls_dict = collections.OrderedDict()
for k, v in variables.items():
    if v['unit'] is None:
        desc = v['label']
    else:
        desc = "{} [{}]".format(v['label'], v['unit'])
    controls = get_controls(k, desc, v['range'])
    controls_dict[k] = controls

head_row = html.Tr([
    html.Th('Variable'),
    html.Th('Range'),
    html.Th('Weight'),
])
controls_html = html.Table(
    [head_row] + list(controls_dict.values()), id='controls')
low_states = [dash.dependencies.State(k + "_low", 'value') for k in labels]
high_states = [dash.dependencies.State(k + "_high", 'value') for k in labels]
weight_states = [
    dash.dependencies.State(k + "_weight", 'value') for k in labels
]

inp_nvars = html.Div([
    html.Span('Number of variables: '),
    dcc.Input(id='nvars', type='number', value=5, className="nvars range")
])

inp_nsamples = html.Div([
    html.Span('Number of samples: '),
    dcc.Input(
        id='nsamples', type='number', value=20, className="nsamples range")
])
nsamples_state = dash.dependencies.State('nsamples', 'value')

ninps = len(low_states + high_states + weight_states) + 1

btn_compute = html.Div([
    html.Button('compute', id='btn_compute'),
    html.Div('', id='compute_info')
])

css = html.Link(rel='stylesheet', href='/static/style.css')

# Creation of dash app
app = dash.Dash(__name__, static_folder='static')
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.layout = html.Div([
    css,
    inp_nvars,
    controls_html,
    inp_nsamples,
    btn_compute,
    #graph, hover_info,
    #click_info
])

# Use custom CSS
# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# Callbacks for slider labels
for k, v in controls_dict.items():

    @app.callback(
        dash.dependencies.Output(k + '_weight_label', 'children'),
        [dash.dependencies.Input(k + '_weight', 'value')])
    def slider_output(value):
        """Callback for updating slider value"""
        return "{:5.2f}".format(10**value)


for i in range(MAX_NVARS):

    @app.callback(
        dash.dependencies.Output(labels[i] + "_tr", 'style'),
        [dash.dependencies.Input('nvars', 'value')])
    def toggle_visibility(nvars, i=i):
        """Callback for setting variable visibility"""
        style = {}

        if i + 1 <= nvars:
            style['display'] = 'block'
        else:
            style['display'] = 'none'

        return style


@app.callback(
    dash.dependencies.Output('compute_info', 'children'),
    [dash.dependencies.Input('btn_compute', 'n_clicks')],
    low_states + high_states + weight_states + [nsamples_state])
# pylint: disable=unused-argument, unused-variable
def on_compute(n_clicks, *args):
    """callback for clicking compute button"""
    if n_clicks is none:
        return

    if len(args) != ninps:
        raise valueerror("expected {} arguments".format(ninps))

    low_vals = np.array([args[i] for i in range(nq)])
    high_vals = np.array([args[i + nq] for i in range(nq)])
    weight_vals = 10**np.array([args[i + 2 * nq] for i in range(nq)])
    nsamples = args[-1]

    mode = 'maxmin'
    if mode == 'uniform':
        samples = uniform.compute(
            var_lb=low_vals,
            var_ub=high_vals,
            num_samples=nsamples,
        )
        df = pd.dataframe(data=samples, columns=labels)
    elif mode == 'maxmin':
        import maxmin
        # artificially reduce number of variables for speed
        nvars = 3
        samples = maxmin.compute(
            var_importance=weight_vals[:nvars],
            var_lb=low_vals[:nvars],
            var_ub=high_vals[:nvars],
            num_samples=nsamples,
            ngrids_per_dim=ngrid,
        )
        df = pd.dataframe(data=samples, columns=labels[:nvars])

    else:
        raise valueerror("unknown mode '{}'".format(mode))

    return generate_table(df)


def generate_table(dataframe, max_rows=100):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [
            html.Tr([
                html.Td('{:.2f}'.format(dataframe.iloc[i][col]))
                for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])


if __name__ == '__main__':
    app.run_server(debug=True)
    #app.run_server()
