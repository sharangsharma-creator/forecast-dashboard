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

    # KPI STRIP
    html.Div([
        html.Div(id='kpi-accuracy', className='kpi-card'),
        html.Div(id='kpi-materials', className='kpi-card'),
    ], style={'display':'flex','gap':'12px','padding':'12px'}),

    # MAIN LAYOUT
    html.Div([

        # LEFT PANEL
        html.Div([
            html.H4("Materials", style={'color':'white'}),
            dcc.Dropdown(
                id='material-dropdown',
                options=[{'label':m, 'value':m} for m in materials],
                value=materials[0],
                style={'background':'#161b22','color':'black'}
            )
        ], style={'width':'25%','padding':'10px'}),

        # RIGHT PANEL
        html.Div([

            html.H3(id='material-title', style={'color':'white'}),

            dcc.Graph(id='main-chart'),

            html.Div(id='insights', style={'color':'white','padding':'10px'})

        ], style={'width':'75%','padding':'10px'})

    ], style={'display':'flex'})

], style={'background':'#0d1117','minHeight':'100vh'}) 
@app.callback(
    Output('main-chart','figure'),
    Output('material-title','children'),
    Output('insights','children'),
    Input('material-dropdown','value')
)
def update_dashboard(mat):

    dff = df[df['material'] == mat]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dff['ds'], y=dff['actual'],
        mode='lines+markers', name='Actual', line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=dff['ds'], y=dff['forecast'],
        mode='lines+markers', name='Forecast', line=dict(color='orange')
    ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d1117',
        plot_bgcolor='#0d1117'
    )

    trend = "Moderate"  # placeholder
    seasonality = "Weak"

    insights = f"Trend: {trend} | Seasonality: {seasonality}"

    return fig, f"Material: {mat}", insights

if __name__ == '__main__':
    app.run(debug=False, port=8050)
