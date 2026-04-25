import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import re
import json

# ── LOAD DATA ────────────────────────────────────────────────────────────────
df = pd.read_json('forecast_data.json')
df['ds'] = pd.to_datetime(df['ds'], format='mixed', dayfirst=False)
df['mape'] = pd.to_numeric(df['mape'], errors='coerce')
materials = df['material'].unique().tolist()

comp_df = pd.read_json('comparison_april.json')
comp_df['part_code'] = comp_df['part_code'].astype(str).str.strip()

# ── HELPERS ──────────────────────────────────────────────────────────────────
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
    except: return None

def mape_color(acc):
    if acc is None: return '#8b949e'
    if acc >= 80: return '#3fb950'
    if acc >= 70: return '#d29922'
    return '#f85149'

def get_demand_pattern(cv, adi):
    try:
        cv = float(cv); adi = float(adi)
        if cv < 0.49 and adi < 1.32:    return 'Smooth',       '#3fb950'
        elif cv >= 0.49 and adi < 1.32: return 'Erratic',      '#d29922'
        elif cv < 0.49 and adi >= 1.32: return 'Intermittent', '#d29922'
        else:                            return 'Lumpy',        '#f85149'
    except: return 'Unknown', '#8b949e'

def get_trend_direction(slope):
    try:
        s = float(slope)
        if s > 10:    return '▲ Upward',   '#3fb950'
        elif s < -10: return '▼ Downward', '#f85149'
        else:         return '→ Flat',     '#8b949e'
    except: return '→ Flat', '#8b949e'

def get_trend_strength(r2):
    try:
        r = float(r2)
        if r > 0.5:   return 'Strong',   '#3fb950'
        elif r > 0.2: return 'Moderate', '#d29922'
        else:         return 'Weak',     '#f85149'
    except: return 'Unknown', '#8b949e'

def get_seasonality(flag, score):
    try:
        if str(flag).strip().lower() in ['true', '1', 'yes', 'present']:
            sc = float(score)
            if sc > 0.6:   return 'Strong',   '#f85149'
            elif sc > 0.3: return 'Moderate', '#d29922'
            else:          return 'Weak',     '#8b949e'
        return 'None', '#8b949e'
    except: return 'Unknown', '#8b949e'

# ── KPI VALUES ───────────────────────────────────────────────────────────────
mapes    = [fmt_mape(df[df['material'] == m]['mape'].iloc[0]) for m in materials]
valid_m  = [x for x in mapes if x is not None]
avg_mape = round(100 - np.mean(valid_m), 1) if valid_m else 0
n_mats   = len(materials)
mc_avg   = mape_color(avg_mape)

# ── CARD BUILDER ─────────────────────────────────────────────────────────────
def make_mat_card(mat, idx, is_selected):
    row0      = df[df['material'] == mat].iloc[0]
    part_code = str(row0['part_code'])
    dname     = clean_name(mat)
    model_raw = str(row0['model'])
    short_mdl = model_raw.split('(')[0].strip()[:16]
    mape_v    = fmt_mape(row0['mape'])
    mc        = mape_color(100 - mape_v if mape_v is not None else None)
    mape_str  = f'{mape_v:.1f}%' if mape_v else 'N/A'
    td, tdc   = get_trend_direction(row0['trend_slope'])
    ti        = td.split()[0]
    card_bg   = '#111d2e' if is_selected else '#0d1117'
    card_bl   = '2px solid #388bfd' if is_selected else '1px solid #21262d'
    name_col  = '#79c0ff' if is_selected else '#e6edf3'
    code_col  = '#388bfd' if is_selected else '#6e7681'
    mbg       = ('#0d2b1e' if mape_v and mape_v < 20
                 else '#2b1d0d' if mape_v and mape_v < 30
                 else '#2b0d0d' if mape_v
                 else '#161b22')
    return html.Div([
        html.Div(part_code, style={
            'fontSize': '9px', 'fontWeight': '700', 'color': code_col,
            'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '3px'
        }),
        html.Div(dname, style={
            'fontSize': '12px', 'fontWeight': '600', 'color': name_col,
            'marginBottom': '6px', 'lineHeight': '1.35', 'wordBreak': 'break-word'
        }),
        html.Div([
            html.Span(mape_str, style={
                'background': mbg, 'color': mc, 'border': f'1px solid {mc}44',
                'fontSize': '9px', 'fontWeight': '600', 'padding': '1px 7px',
                'borderRadius': '8px', 'marginRight': '4px'
            }),
            html.Span(short_mdl, style={
                'background': '#161b22', 'color': '#a8b4c0', 'border': '1px solid #30363d',
                'fontSize': '9px', 'padding': '1px 7px', 'borderRadius': '8px', 'marginRight': '4px'
            }),
            html.Span(ti, style={'color': tdc, 'fontSize': '11px', 'fontWeight': '700'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})
    ], id={'type': 'mat-card', 'index': idx},
    n_clicks=0,
    style={
        'background':   card_bg,
        'border':       card_bl,
        'borderRadius': '6px',
        'padding':      '10px 12px',
        'marginBottom': '4px',
        'cursor':       'pointer',
        'transition':   'all 0.15s',
    })

# ── APP INIT ─────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.DARKLY,
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
])
app.title = 'Forecasting Dashboard'
server = app.server

# ── STYLES ───────────────────────────────────────────────────────────────────
PANEL_STYLE = {
    'width':       '220px',
    'minWidth':    '220px',
    'height':      'calc(100vh - 120px)',
    'overflowY':   'auto',
    'background':  '#0d1117',
    'borderRight': '1px solid #1a2332',
    'padding':     '12 
