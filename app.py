import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import re
import json

# ── LOAD DATA ─────────────────────────────────────────────
df = pd.read_json('forecast_data.json')
df['ds'] = pd.to_datetime(df['ds'], format='mixed', dayfirst=False)
df['mape'] = pd.to_numeric(df['mape'], errors='coerce')
materials = df['material'].unique().tolist()

# ── HELPERS ───────────────────────────────────────────────
def clean_name(name):
    n = str(name).strip()
    n = re.split(r'\s*[\(\[]', n)[0].strip()
    n = re.sub(r'(?i)\bwholesale\b.*', '', n).strip()
    n = re.sub(r'(?i)\bqty\b.*', '', n).strip()
    n = re.sub(r'\s+', ' ', n).strip()
    return n.strip(' -–')

def fmt_mape(v):
    try:
        f = float(v)
        if np.isnan(f): return None
        return round(f * 100 if f <= 1.0 else f, 1)
    except:
        return None

def mape_color(v):
    if v is None: return '#8b949e'
    if v < 20: return '#3fb950'
    if v < 30: return '#d29922'
    return '#f85149'

def get_demand_pattern(cv, adi):
    try:
        cv = float(cv); adi = float(adi)
        if cv < 0.49 and adi < 1.32: return 'Smooth', '#3fb950'
        elif cv >= 0.49 and adi < 1.32: return 'Erratic', '#d29922'
        elif cv < 0.49 and adi >= 1.32: return 'Intermittent', '#d29922'
        else: return 'Lumpy', '#f85149'
    except:
        return 'Unknown', '#8b949e'

# ── APP INIT ──────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# ── SIMPLE LAYOUT (TEST FIRST) ────────────────────────────
app.layout = html.Div([
    html.H2("Forecast Dashboard"),
    dcc.Graph(id='chart')
])

# ── CALLBACK (TEST) ───────────────────────────────────────
@app.callback(
    Output('chart', 'figure'),
    Input('chart', 'id')
)
def update_chart(_):
    fig = go.Figure()

    for mat in materials[:3]:
        mdata = df[df['material'] == mat]
        fig.add_trace(go.Scatter(
            x=mdata['ds'],
            y=mdata['y'],
            mode='lines',
            name=mat
        ))

    return fig

# ── RUN ──────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False) 
