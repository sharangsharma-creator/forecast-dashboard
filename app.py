import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import re
import json

# -- LOAD DATA ----------------------------------------------------------------
df = pd.read_json('forecast_data.json')
df['ds'] = pd.to_datetime(df['ds'], format='mixed', dayfirst=False)
df['mape'] = pd.to_numeric(df['mape'], errors='coerce')
materials = df['material'].unique().tolist()

comp_df = pd.read_json('comparison_april.json')
comp_df['part_code'] = comp_df['part_code'].astype(str).str.strip()

# -- HELPERS ------------------------------------------------------------------
def clean_name(name):
    n = str(name).strip()
    n = re.split(r'\s*[\(\[]', n)[0].strip()
    n = re.sub(r'(?i)\bwholesale\b.*', '', n).strip()
    n = re.sub(r'(?i)\bqty\b.*', '', n).strip()
    n = re.sub(r'\s+', ' ', n).strip()
    return n.strip(' -')

def fmt_mape(v):
    try:
        f = float(v)
        if np.isnan(f):
            return None
        return round(f * 100 if f <= 1.0 else f, 1)
    except:
        return None

def mape_color(acc):
    if acc is None:
        return '#8b949e'
    if acc >= 80:
        return '#3fb950'
    if acc >= 70:
        return '#d29922'
    return '#f85149'

def get_demand_pattern(cv, adi):
    try:
        cv = float(cv)
        adi = float(adi)
        if cv < 0.49 and adi < 1.32:
            return 'Smooth', '#3fb950'
        elif cv >= 0.49 and adi < 1.32:
            return 'Erratic', '#d29922'
        elif cv < 0.49 and adi >= 1.32:
            return 'Intermittent', '#d29922'
        else:
            return 'Lumpy', '#f85149'
    except:
        return 'Unknown', '#8b949e'

def get_trend_direction(slope):
    try:
        s = float(slope)
        if s > 10:
            return 'Upward', '#3fb950'
        elif s < -10:
            return 'Downward', '#f85149'
        else:
            return 'Flat', '#8b949e'
    except:
        return 'Flat', '#8b949e'

def get_trend_strength(r2):
    try:
        r = float(r2)
        if r > 0.5:
            return 'Strong', '#3fb950'
        elif r > 0.2:
            return 'Moderate', '#d29922'
        else:
            return 'Weak', '#f85149'
    except:
        return 'Unknown', '#8b949e'

def get_seasonality(flag, score):
    try:
        if str(flag).strip().lower() in ['true', '1', 'yes', 'present']:
            sc = float(score)
            if sc > 0.6:
                return 'Strong', '#f85149'
            elif sc > 0.3:
                return 'Moderate', '#d29922'
            else:
                return 'Weak', '#8b949e'
        return 'None', '#8b949e'
    except:
        return 'Unknown', '#8b949e'

# -- KPI VALUES ---------------------------------------------------------------
mapes    = [fmt_mape(df[df['material'] == m]['mape'].iloc[0]) for m in materials]
valid_m  = [x for x in mapes if x is not None]
avg_mape = round(100 - np.mean(valid_m), 1) if valid_m else 0
n_mats   = len(materials)
mc_avg   = mape_color(avg_mape)

# -- CARD BUILDER -------------------------------------------------------------
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
    card_bg   = '#111d2e' if is_selected else '#0d1117'
    card_bl   = '2px solid #388bfd' if is_selected else '1px solid #21262d'
    name_col  = '#79c0ff' if is_selected else '#e6edf3'
    code_col  = '#388bfd' if is_selected else '#6e7681'
    mbg = (
        '#0d2b1e' if mape_v and mape_v < 20
        else '#2b1d0d' if mape_v and mape_v < 30
        else '#2b0d0d' if mape_v
        else '#161b22'
    )
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
            html.Span(td, style={'color': tdc, 'fontSize': '10px', 'fontWeight': '700'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})
    ],
    id={'type': 'mat-card', 'index': idx},
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

# -- APP INIT -----------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.DARKLY,
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
])
app.title = 'Forecasting Dashboard'
server = app.server

# -- STYLES -------------------------------------------------------------------
PANEL_STYLE = {
    'width':       '220px',
    'minWidth':    '220px',
    'height':      'calc(100vh - 120px)',
    'overflowY':   'auto',
    'background':  '#0d1117',
    'borderRight': '1px solid #1a2332',
    'padding':     '12px 8px',
}
CARD_STYLE = {
    'background':   '#0d1117',
    'border':       '1px solid #1a2332',
    'borderRadius': '8px',
    'overflow':     'hidden',
    'marginTop':    '10px',
}
HDR_STYLE = {
    'padding':       '8px 14px',
    'background':    '#161b22',
    'borderBottom':  '1px solid #1a2332',
    'fontSize':      '10px',
    'fontWeight':    '700',
    'color':         '#a8b4c0',
    'textTransform': 'uppercase',
    'letterSpacing': '0.7px',
}
ROW_STYLE = {
    'display':        'flex',
    'justifyContent': 'space-between',
    'alignItems':     'center',
    'padding':        '8px 14px',
    'borderBottom':   '1px solid #1a2332',
    'fontSize':       '12px',
}
LBL_STYLE = {'color': '#8b949e', 'fontSize': '11px'}
VAL_STYLE  = {'fontWeight': '600', 'color': '#e6edf3', 'fontSize': '12px'}

# -- LAYOUT -------------------------------------------------------------------
app.layout = html.Div([
    dcc.Store(id='selected-mats', data=[materials[0]]),
    dcc.Store(id='multi-mode',    data=False),
    dcc.Store(id='show-trend',    data=False),

    # TOP BAR
    html.Div([
        html.Div([
            html.Span('Forecasting Dashboard', style={
                'fontSize': '16px', 'fontWeight': '700', 'color': '#f0f6fc', 'letterSpacing': '-0.3px'
            }),
            html.Span('Ather Energy - Accessories - FY26', style={
                'fontSize': '11px', 'color': '#8b949e',
                'paddingLeft': '12px', 'marginLeft': '12px', 'borderLeft': '1px solid #21262d'
            }),
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ], style={
        'background': '#0d1117', 'borderBottom': '1px solid #1a2332',
        'padding': '0 28px', 'height': '52px',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'
    }),

    # KPI STRIP
    html.Div([
        html.Div([
            html.Div('Avg Model Accuracy', style={
                'fontSize': '10px', 'fontWeight': '600', 'color': '#8b949e',
                'textTransform': 'uppercase', 'letterSpacing': '0.8px', 'marginBottom': '5px'
            }),
            html.Div(f'{avg_mape:.1f}%', style={
                'fontSize': '28px', 'fontWeight': '700', 'color': mc_avg,
                'lineHeight': '1', 'letterSpacing': '-0.5px'
            }),
            html.Div('average model accuracy across all parts', style={
                'fontSize': '10px', 'color': '#8b949e', 'marginTop': '3px'
            }),
        ], style={
            'padding': '16px 32px', 'background': '#0d1117',
            'borderRight': '1px solid #1a2332', 'flex': '1',
            'position': 'relative', 'borderTop': '2px solid #3fb950'
        }),
        html.Div([
            html.Div('Parts Tracked', style={
                'fontSize': '10px', 'fontWeight': '600', 'color': '#8b949e',
                'textTransform': 'uppercase', 'letterSpacing': '0.8px', 'marginBottom': '5px'
            }),
            html.Div(str(n_mats), style={
                'fontSize': '28px', 'fontWeight': '700', 'color': '#bc8cff',
                'lineHeight': '1', 'letterSpacing': '-0.5px'
            }),
            html.Div('active accessories with forecast', style={
                'fontSize': '10px', 'color': '#8b949e', 'marginTop': '3px'
            }),
        ], style={
            'padding': '16px 32px', 'background': '#0d1117',
            'flex': '1', 'position': 'relative', 'borderTop': '2px solid #bc8cff'
        }),
    ], style={'display': 'flex', 'borderBottom': '1px solid #1a2332'}),

    # MAIN CONTENT
    html.Div([
        # LEFT PANEL
        html.Div([
            html.Div('Select Part', style={
                'fontSize': '10px', 'fontWeight': '600', 'color': '#8b949e',
                'textTransform': 'uppercase', 'letterSpacing': '0.8px',
                'paddingBottom': '8px', 'borderBottom': '1px solid #1a2332', 'marginBottom': '8px'
            }),
            html.Div(id='multi-btn', n_clicks=0, children='Multi-Select: OFF', style={
                'background': '#161b22', 'border': '1px solid #30363d', 'borderRadius': '5px',
                'padding': '7px 12px', 'fontSize': '11px', 'fontWeight': '600',
                'color': '#8b949e', 'cursor': 'pointer', 'marginBottom': '8px',
                'textAlign': 'center', 'userSelect': 'none'
            }),
            html.Div([make_mat_card(mat, i, i == 0) for i, mat in enumerate(materials)],
                     id='cards-container'),
        ], style=PANEL_STYLE),

        # RIGHT PANEL
        html.Div([
            # Chart header
            html.Div([
                html.Div([
                    html.Div(id='chart-title', style={
                        'fontSize': '15px', 'fontWeight': '600', 'color': '#f0f6fc'
                    }),
                    html.Div([
                        html.Span('Actual (Train)', style={
                            'color': '#388bfd', 'fontSize': '11px', 'marginRight': '12px'
                        }),
                        html.Span('Actual (Test)', style={
                            'color': '#1D9E75', 'fontSize': '11px', 'marginRight': '12px'
                        }),
                        html.Span('Forecast', style={
                            'color': '#f0883e', 'fontSize': '11px', 'marginRight': '12px'
                        }),
                        html.Span('Trend', style={
                            'color': 'rgba(255,255,255,0.4)', 'fontSize': '11px'
                        }),
                    ], style={'marginTop': '3px'}),
                ], style={'flex': '1'}),
                html.Div(id='trend-btn', n_clicks=0, children='Trendline: OFF', style={
                    'background': '#161b22', 'border': '1px solid #30363d', 'borderRadius': '6px',
                    'padding': '6px 14px', 'fontSize': '11px', 'fontWeight': '600',
                    'color': '#8b949e', 'cursor': 'pointer', 'userSelect': 'none',
                    'whiteSpace': 'nowrap', 'alignSelf': 'center',
                }),
            ], style={
                'display': 'flex', 'alignItems': 'flex-start',
                'justifyContent': 'space-between', 'padding': '10px 12px 4px 12px'
            }),

            # Main chart
            dcc.Graph(id='main-chart', config={'displayModeBar': False},
                      style={'background': '#0d1117'}),

            # Bottom panels
            html.Div([
                html.Div(id='fcast-panel',   style={**CARD_STYLE, 'flex': '1', 'marginRight': '8px'}),
                html.Div(id='stats-panel',   style={**CARD_STYLE, 'flex': '1', 'marginRight': '8px'}),
                html.Div(id='profile-panel', style={**CARD_STYLE, 'flex': '1'}),
            ], style={'display': 'flex', 'padding': '0 12px 16px 12px'}),

            # APRIL COMPARISON CHART
            html.Div([
                html.Div([
                    html.Span('April 2026 - Forecast vs Actual', style={
                        'fontSize': '10px', 'fontWeight': '700', 'color': '#a8b4c0',
                        'textTransform': 'uppercase', 'letterSpacing': '0.7px',
                    }),
                    html.Div([
                        html.Span('Forecast  ', style={
                            'color': '#f0883e', 'fontSize': '11px', 'marginRight': '16px'
                        }),
                        html.Span('Actual', style={
                            'color': '#3fb950', 'fontSize': '11px'
                        }),
                    ]),
                ], style={
                    'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                    'padding': '8px 14px', 'background': '#161b22',
                    'borderBottom': '1px solid #1a2332',
                }),
                dcc.Graph(
                    id='april-comparison-chart',
                    config={'displayModeBar': False},
                    style={'background': '#0d1117'}
                ),
            ], style={
                'background':   '#0d1117',
                'border':       '1px solid #1a2332',
                'borderRadius': '8px',
                'overflow':     'hidden',
                'margin':       '0 12px 20px 12px',
            }),

        ], style={'flex': '1', 'overflowY': 'auto', 'background': '#0d1117'}),

    ], style={
        'display': 'flex', 'flexDirection': 'row',
        'height': 'calc(100vh - 120px)', 'background': '#0d1117'
    }),

], style={'fontFamily': 'Inter,sans-serif', 'background': '#0d1117', 'minHeight': '100vh'})

# -- CUSTOM CSS ---------------------------------------------------------------
app.index_string = (
    "<!DOCTYPE html>"
    "<html>"
    "<head>"
    "{%metas%}"
    "<title>{%title%}</title>"
    "{%favicon%}"
    "{%css%}"
    "<style>"
    "* { box-sizing: border-box; margin: 0; padding: 0; }"
    "body { background: #0d1117; font-family: Inter, sans-serif; }"
    "::-webkit-scrollbar { width: 4px; height: 4px; }"
    "::-webkit-scrollbar-track { background: transparent; }"
    "::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }"
    ".js-plotly-plot .plotly { background: #0d1117 !important; }"
    "</style>"
    "</head>"
    "<body>"
    "{%app_entry%}"
    "<footer>"
    "{%config%}"
    "{%scripts%}"
    "{%renderer%}"
    "</footer>"
    "</body>"
    "</html>"
)

# -- CALLBACKS ----------------------------------------------------------------
@app.callback(
    Output('multi-mode',    'data'),
    Output('multi-btn',     'children'),
    Output('multi-btn',     'style'),
    Output('selected-mats', 'data'),
    Input('multi-btn', 'n_clicks'),
    State('multi-mode',    'data'),
    State('selected-mats', 'data'),
    prevent_initial_call=True
)
def toggle_multi(n, is_multi, sel_mats):
    new_multi = not is_multi
    new_sel   = sel_mats if new_multi else [sel_mats[0]]
    lbl   = 'Multi-Select: ON' if new_multi else 'Multi-Select: OFF'
    style = {
        'background':   '#111d2e' if new_multi else '#161b22',
        'border':       '1px solid #388bfd' if new_multi else '1px solid #30363d',
        'borderRadius': '5px', 'padding': '7px 12px',
        'fontSize': '11px', 'fontWeight': '600',
        'color':        '#79c0ff' if new_multi else '#8b949e',
        'cursor': 'pointer', 'marginBottom': '8px',
        'textAlign': 'center', 'userSelect': 'none',
    }
    return new_multi, lbl, style, new_sel


@app.callback(
    Output('selected-mats',   'data'),
    Output('cards-container', 'children'),
    Input({'type': 'mat-card', 'index': dash.ALL}, 'n_clicks'),
    State('selected-mats', 'data'),
    State('multi-mode',    'data'),
    prevent_initial_call=True
)
def card_click(n_clicks_list, sel_mats, is_multi):
    ctx = callback_context
    if not ctx.triggered:
        return sel_mats, dash.no_update
    idx = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])['index']
    mat = materials[idx]
    if is_multi:
        if mat in sel_mats:
            new_sel = [m for m in sel_mats if m != mat] if len(sel_mats) > 1 else sel_mats
        else:
            new_sel = sel_mats + [mat] if len(sel_mats) < 3 else sel_mats
    else:
        new_sel = [mat]
    cards = [make_mat_card(m, i, m in new_sel) for i, m in enumerate(materials)]
    return new_sel, cards


@app.callback(
    Output('show-trend', 'data'),
    Output('trend-btn',  'children'),
    Output('trend-btn',  'style'),
    Input('trend-btn', 'n_clicks'),
    State('show-trend',  'data'),
    prevent_initial_call=True
)
def toggle_trend(n, show):
    new_show = not show
    lbl   = 'Trendline: ON' if new_show else 'Trendline: OFF'
    style = {
        'background':   '#1c2128' if new_show else '#161b22',
        'border':       '1px solid rgba(255,255,255,0.25)' if new_show else '1px solid #30363d',
        'borderRadius': '6px', 'padding': '6px 14px',
        'fontSize': '11px', 'fontWeight': '600',
        'color':        '#f0f6fc' if new_show else '#8b949e',
        'cursor': 'pointer', 'userSelect': 'none',
        'whiteSpace': 'nowrap', 'alignSelf': 'center',
    }
    return new_show, lbl, style


@app.callback(
    Output('main-chart',    'figure'),
    Output('chart-title',   'children'),
    Output('fcast-panel',   'children'),
    Output('stats-panel',   'children'),
    Output('profile-panel', 'children'),
    Input('selected-mats',  'data'),
    Input('show-trend',     'data'),
)
def update_dashboard(sel_mats, show_trend):
    if not sel_mats:
        sel_mats = [materials[0]]
    n_sel  = len(sel_mats)
    titles = [clean_name(m) for m in sel_mats]
    fig    = make_subplots(rows=n_sel, cols=1, subplot_titles=titles, vertical_spacing=0.1)

    for idx, mat in enumerate(sel_mats):
        row   = idx + 1
        mdata = df[df['material'] == mat].sort_values('ds')
        tr    = mdata[mdata['period'] == 'Train']
        te    = mdata[mdata['period'] == 'Test']
        fc    = mdata[mdata['period'] == 'Forecast']
        sl    = (idx == 0)

        if len(tr) > 0:
            fig.add_trace(go.Bar(
                x=tr['ds'], y=tr['y'], name='Actual (Train)',
                marker_color='#388bfd', opacity=0.8, showlegend=sl,
                hovertemplate='%{x|%b %y}<br>Actual: %{y:,}<extra></extra>'
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=tr['ds'], y=tr['fitted'], name='Rolling Avg',
                line=dict(color='rgba(255,255,255,0.25)', width=1.5, dash='dot'),
                mode='lines', showlegend=sl,
                hovertemplate='%{x|%b %y}<br>Rolling: %{y:,}<extra></extra>'
            ), row=row, col=1)
        if len(te) > 0:
            fig.add_trace(go.Bar(
                x=te['ds'], y=te['y'], name='Actual (Test)',
                marker_color='#1D9E75', opacity=0.85, showlegend=sl,
                hovertemplate='%{x|%b %y}<br>Test: %{y:,}<extra></extra>'
            ), row=row, col=1)
        if len(fc) > 0:
            fig.add_trace(go.Bar(
                x=fc['ds'], y=fc['fitted'], name='Forecast',
                marker_color='#f0883e', opacity=0.9, showlegend=sl,
                hovertemplate='%{x|%b %y}<br>Forecast: %{y:,}<extra></extra>'
            ), row=row, col=1)
            fig.add_vrect(
                x0=str(fc['ds'].iloc[0]), x1=str(fc['ds'].iloc[-1]),
                fillcolor='rgba(240,136,62,0.05)', layer='below', line_width=0,
                row=row, col=1
            )
        if show_trend:
            try:
                slope = float(mdata['trend_slope'].iloc[0])
                intcp = float(mdata['trend_intercept'].iloc[0])
                act   = mdata[mdata['period'].isin(['Train', 'Test'])].sort_values('ds')
                yt    = slope * np.arange(len(act)) + intcp
                fig.add_trace(go.Scatter(
                    x=act['ds'], y=yt, name='Trendline',
                    line=dict(color='rgba(255,255,255,0.4)', width=1.5, dash='longdash'),
                    mode='lines', showlegend=sl,
                    hovertemplate='%{x|%b %y}<br>Trend: %{y:,.0f}<extra></extra>'
                ), row=row, col=1)
            except:
                pass

    ch = 360 if n_sel == 1 else 270 * n_sel
    fig.update_layout(
        paper_bgcolor='#0d1117', plot_bgcolor='#0d1117',
        font=dict(color='#8b949e', size=11, family='Inter'),
        legend=dict(
            bgcolor='rgba(0,0,0,0)', borderwidth=0,
            font=dict(color='#8b949e', size=10),
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0
        ),
        height=ch, margin=dict(l=8, r=8, t=30, b=8),
        hovermode='x unified', barmode='group',
    )
    fig.update_xaxes(gridcolor='#161b22', showgrid=True, zeroline=False,
                     tickfont=dict(color='#8b949e', size=10), tickformat='%b %y')
    fig.update_yaxes(gridcolor='#161b22', showgrid=True, zeroline=False,
                     tickfont=dict(color='#8b949e', size=10))
    for ann in fig.layout.annotations:
        ann.font.color = '#a8b4c0'
        ann.font.size  = 12

    pm   = sel_mats[0]
    pmdf = df[df['material'] == pm].iloc[0]
    pf   = df[(df['material'] == pm) & (df['period'] == 'Forecast')].sort_values('ds')
    mp_v = fmt_mape(pmdf['mape'])
    mp_c = mape_color(100 - mp_v if mp_v is not None else None)
    mp_s = f'{mp_v:.1f}%' if mp_v else 'N/A'
    tc   = len(df[(df['material'] == pm) & (df['period'] == 'Train')])
    sc   = len(df[(df['material'] == pm) & (df['period'] == 'Test')])
    ml   = {4: 'Apr 2026', 5: 'May 2026', 6: 'Jun 2026'}

    fcast_rows = []
    for _, r in pf.iterrows():
        lb = ml.get(r['ds'].month, r['ds'].strftime('%b %Y'))
        fcast_rows.append(html.Div([
            html.Span(lb, style={'color': '#a8b4c0', 'fontSize': '11px'}),
            html.Span(
                f"{int(r['fitted']):,} units",
                style={'fontWeight': '700', 'color': '#f0883e', 'fontSize': '13px'}
            ),
        ], style={**ROW_STYLE, 'borderBottom': '1px solid #1a2332'}))
    fcast_panel = html.Div(
        [html.Div('Forward Forecast', style=HDR_STYLE)] + fcast_rows,
        style=CARD_STYLE
    )

    stats_rows = [
        ('Test MAPE',    html.Span(mp_s, style={'fontWeight': '600', 'color': mp_c, 'fontSize': '12px'})),
        ('Model',        html.Span(str(pmdf['model']), style={**VAL_STYLE, 'fontSize': '10px'})),
        ('Train Months', html.Span(str(tc), style=VAL_STYLE)),
        ('Test Months',  html.Span(str(sc), style=VAL_STYLE)),
        ('CV',           html.Span(f"{float(pmdf['cv']):.3f}", style=VAL_STYLE)),
        ('ADI',          html.Span(f"{float(pmdf['adi']):.2f}", style=VAL_STYLE)),
    ]
    stats_panel = html.Div(
        [html.Div('Model Statistics', style=HDR_STYLE)] + [
            html.Div([html.Span(l, style=LBL_STYLE), v], style=ROW_STYLE)
            for l, v in stats_rows
        ],
        style=CARD_STYLE
    )

    pt,  pc2  = get_demand_pattern(pmdf['cv'], pmdf['adi'])
    td2, tdc2 = get_trend_direction(pmdf['trend_slope'])
    ts,  tsc  = get_trend_strength(pmdf['r2'])
    sn,  snc  = get_seasonality(pmdf['seasonality_flag'], pmdf['seasonality_score'])
    sv = float(pmdf['trend_slope'])
    iv = float(pmdf['trend_intercept'])
    teq = f'{sv:+.1f}x + {iv:.0f}' if iv >= 0 else f'{sv:+.1f}x - {abs(iv):.0f}'

    profile_rows = [
        ('Demand Pattern',  html.Span(pt,  style={'fontWeight': '600', 'color': pc2,  'fontSize': '12px'})),
        ('Trend Direction', html.Span(td2, style={'fontWeight': '600', 'color': tdc2, 'fontSize': '12px'})),
        ('Trend Strength',  html.Span(
            f'{ts} (R2={float(pmdf["r2"]):.3f})',
            style={'fontWeight': '600', 'color': tsc, 'fontSize': '12px'}
        )),
        ('Seasonality',     html.Span(sn,  style={'fontWeight': '600', 'color': snc,  'fontSize': '12px'})),
        ('Seasonal Score',  html.Span(f"{float(pmdf['seasonality_score']):.3f}", style=VAL_STYLE)),
        ('Trend Equation',  html.Span(teq, style={'fontWeight': '600', 'color': '#8b949e', 'fontSize': '10px'})),
    ]
    profile_panel = html.Div(
        [html.Div('Demand Profile', style=HDR_STYLE)] + [
            html.Div([html.Span(l, style=LBL_STYLE), v], style=ROW_STYLE)
            for l, v in profile_rows
        ],
        style=CARD_STYLE
    )

    title = ' - '.join([clean_name(m) for m in sel_mats])
    return fig, title, fcast_panel, stats_panel, profile_panel


@app.callback(
    Output('april-comparison-chart', 'figure'),
    Input('selected-mats', 'data'),
)
def update_comparison(sel_mats):
    labels     = []
    forecasts  = []
    actuals    = []
    errors     = []
    colors_fc  = []
    colors_ac  = []

    for mat in materials:
        row      = df[df['material'] == mat].iloc[0]
        pc       = str(row['part_code']).strip()
        selected = mat in sel_mats

        crow  = comp_df[comp_df['part_code'] == pc]
        fc_v  = int(crow['forecast_april'].iloc[0]) if len(crow) > 0 else 0
        ac_v  = (int(crow['actual_april'].iloc[0])
                 if len(crow) > 0 and pd.notna(crow['actual_april'].iloc[0]) else 0)
        er_v  = (float(crow['error_pct'].iloc[0])
                 if len(crow) > 0 and pd.notna(crow['error_pct'].iloc[0]) else None)

        labels.append(clean_name(mat))
        forecasts.append(fc_v)
        actuals.append(ac_v)
        errors.append(er_v)
        colors_fc.append('#f0883e' if selected else 'rgba(240,136,62,0.25)')
        colors_ac.append('#3fb950' if selected else 'rgba(63,185,80,0.25)')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Forecast (Apr)',
        x=labels,
        y=forecasts,
        marker_color=colors_fc,
        marker_line_width=0,
        hovertemplate='<b>%{x}</b><br>Forecast: %{y:,}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Actual (Apr)',
        x=labels,
        y=actuals,
        marker_color=colors_ac,
        marker_line_width=0,
        customdata=errors,
        hovertemplate='<b>%{x}</b><br>Actual: %{y:,}<br>Error: %{customdata:.1f}%<extra></extra>',
    ))

    fig.update_layout(
        paper_bgcolor='#0d1117',
        plot_bgcolor='#0d1117',
        font=dict(color='#8b949e', size=10, family='Inter'),
        barmode='group',
        height=300,
        margin=dict(l=8, r=8, t=12, b=90),
        legend=dict(
            bgcolor='rgba(0,0,0,0)', borderwidth=0,
            font=dict(color='#8b949e', size=10),
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
        ),
        hovermode='x unified',
        bargap=0.25,
        bargroupgap=0.05,
    )
    fig.update_xaxes(
        gridcolor='#161b22', zeroline=False,
        tickfont=dict(color='#8b949e', size=9),
        tickangle=-35,
    )
    fig.update_yaxes(
        gridcolor='#161b22', zeroline=False,
        tickfont=dict(color='#8b949e', size=10),
    )
    return fig


if __name__ == '__main__':
    app.run(debug=False, port=8050) 
