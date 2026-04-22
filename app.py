import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import re
import json

# LOAD DATA
df = pd.read_json('forecast_data.json')
df['ds'] = pd.to_datetime(df['ds'], format='mixed', dayfirst=False)
df['mape'] = pd.to_numeric(df['mape'], errors='coerce')
materials = df['material'].unique().tolist()

# APP INIT
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

# SIMPLE LAYOUT (for testing first)
app.layout = html.Div([
    html.H1("Dashboard is working 🚀", style={'color': 'white'}),
    dcc.Graph(
        figure={
            "data": [
                {"x": [1,2,3], "y": [4,1,2], "type": "bar"}
            ]
        }
    )
], style={'background':'#0d1117', 'height':'100vh'})

if __name__ == '__main__':
    app.run(debug=False, port=8050)
