import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx, ALL, no_update
import plotly.graph_objects as go

app = dash.Dash(__name__)

DEFAULT_HALF_LIFE = 6.0
DEFAULT_KA = 1.2
TIME_POINTS = 2000

LIGHT_THEME = {
    "bg": "#ffffff",
    "paper": "#f8f9fa",
    "text": "#212529",
    "grid": "#dee2e6",
    "line": "#0d6efd",
    "dash_line": "#6ea8fe",
    "plot_bg": "#ffffff",
}

DARK_THEME = {
    "bg": "#1a1a2e",
    "paper": "#16213e",
    "text": "#e0e0e0",
    "grid": "#2d3561",
    "line": "#4cc9f0",
    "dash_line": "#a8dadc",
    "plot_bg": "#0f3460",
}

MARK_VALS = [1, 6, 12, 24, 48]


def compute_concentration(dose_times_abs, ka, ke, t_end):
    t = np.linspace(0, t_end, TIME_POINTS)
    conc = np.zeros_like(t)
    for td in dose_times_abs:
        mask = t >= td
        dt = t[mask] - td
        ka_eff = ka if abs(ka - ke) >= 1e-9 else ka + 1e-9
        segment = (ka_eff / (ka_eff - ke)) * (np.exp(-ke * dt) - np.exp(-ka_eff * dt))
        conc[mask] += segment
    return t, conc


def build_figure(dose_times_abs, half_life, ka, theme, t_range=72, xrange_override=None, delta_hl=0):
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    ke = np.log(2) / half_life

    if len(dose_times_abs) == 0:
        t_end = t_range
        t, conc = np.array([0, t_end]), np.array([0.0, 0.0])
    else:
        last_dose = max(dose_times_abs)
        t_end = max(t_range, last_dose + 3 * half_life)
        if xrange_override is not None:
            t_end = max(t_end, xrange_override)
        t, conc = compute_concentration(dose_times_abs, ka, ke, t_end)

    t_cutoff = max(dose_times_abs) if dose_times_abs else 0
    y_max = max(2.5, float(np.max(conc)) * 1.1) if len(conc) > 0 else 2.5
    x_display_end = xrange_override if xrange_override is not None else t_end

    fig = go.Figure()

    if len(dose_times_abs) > 0:
        idx_cut = np.searchsorted(t, t_cutoff)
        fig.add_trace(go.Scatter(
            x=t[:idx_cut + 1], y=conc[:idx_cut + 1],
            mode="lines",
            line=dict(color=colors["line"], width=2.5),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=t[idx_cut:], y=conc[idx_cut:],
            mode="lines",
            line=dict(color=colors["dash_line"], width=2, dash="dash"),
            showlegend=False,
        ))
        for td in dose_times_abs:
            fig.add_vline(x=td, line=dict(color=colors["text"], width=1, dash="dot"), opacity=0.4)
    else:
        fig.add_trace(go.Scatter(
            x=t, y=conc, mode="lines",
            line=dict(color=colors["line"], width=2.5),
            showlegend=False,
        ))

    # Second curve with modified half-life
    if delta_hl and delta_hl > 0 and len(dose_times_abs) > 0:
        ke2 = np.log(2) / (half_life + delta_hl)
        _, conc2 = compute_concentration(dose_times_abs, ka, ke2, t_end)
        fig.add_trace(go.Scatter(
            x=t[:idx_cut + 1], y=conc2[:idx_cut + 1],
            mode="lines",
            line=dict(color="#f59e0b", width=2),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=t[idx_cut:], y=conc2[idx_cut:],
            mode="lines",
            line=dict(color="#fcd34d", width=1.5, dash="dash"),
            showlegend=False,
        ))
        y_max = max(y_max, float(np.max(conc2)) * 1.1)

    fig.add_hline(y=0.1, line=dict(color="#888888", width=1, dash="dot"))
    fig.add_hline(y=1.0, line=dict(color="#28a745", width=1.5))
    fig.add_hline(y=2.0, line=dict(color="#dc3545", width=1.5))

    # Day markers
    day = 24
    while day <= x_display_end:
        fig.add_vline(x=day, line=dict(color="#87ceeb", width=0.8), opacity=0.6)
        fig.add_annotation(
            x=day, y=1, yref="paper",
            text=f"{day // 24}d",
            showarrow=False,
            font=dict(size=9, color="#87ceeb"),
            yanchor="bottom", xanchor="center",
        )
        day += 24

    fig.add_annotation(
        xref="paper", yref="paper", x=1.01, y=0,
        ax=-12, ay=0, axref="pixel", ayref="pixel",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
        arrowcolor=colors["text"], text=""
    )
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=1.01,
        ax=0, ay=12, axref="pixel", ayref="pixel",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
        arrowcolor=colors["text"], text=""
    )

    fig.update_layout(
        paper_bgcolor=colors["paper"],
        plot_bgcolor=colors["plot_bg"],
        font=dict(color=colors["text"]),
        showlegend=False,
        xaxis=dict(
            title="Time (h)",
            gridcolor=colors["grid"],
            range=[0, x_display_end],
            color=colors["text"],
            showline=True, linecolor=colors["text"],
        ),
        yaxis=dict(
            title="Relative concentration",
            gridcolor=colors["grid"],
            range=[0, y_max],
            color=colors["text"],
            showline=True, linecolor=colors["text"],
        ),
        margin=dict(l=60, r=80, t=30, b=50),
        height=480,
    )
    return fig


INPUT_STYLE_BASE = {
    "width": "100%",
    "padding": "0px 4px",
    "fontSize": "12px",
    "lineHeight": "1.4",
    "height": "22px",
    "borderRadius": "3px",
    "border": "1px solid #aaa",
    "boxSizing": "border-box",
}

HL_INPUT_STYLE = {
    "width": "62px",
    "padding": "0px 3px",
    "fontSize": "12px",
    "height": "20px",
    "borderRadius": "3px",
    "border": "1px solid #aaa",
    "textAlign": "center",
    "boxSizing": "border-box",
}

app.layout = html.Div(
    id="main-container",
    children=[
        dcc.Store(id="theme-store", data="light"),
        dcc.Store(id="xrange-store", data=None),
        html.Div(id="body-theme-setter", style={"display": "none"}),

        html.Div(
            style={"display": "flex", "justifyContent": "center",
                   "alignItems": "center", "padding": "10px 20px", "position": "relative"},
            children=[
                html.H2("Pharmacokinetic Simulator", style={"margin": 0}),
                html.Div(style={"display": "flex", "gap": "8px",
                                "position": "absolute", "right": "20px"}, children=[
                    html.Button("Clean", id="clean-btn",
                                style={"padding": "6px 14px", "cursor": "pointer",
                                       "borderRadius": "6px"}),
                    html.Button("Reset", id="reset-btn",
                                style={"padding": "6px 14px", "cursor": "pointer",
                                       "borderRadius": "6px"}),
                    html.Button("Theme", id="theme-btn",
                                style={"padding": "6px 14px", "cursor": "pointer",
                                       "borderRadius": "6px"}),
                ]),
            ],
        ),

        html.Div(
            style={"display": "flex", "gap": "30px", "padding": "0 20px"},
            children=[
                html.Div(
                    style={"minWidth": "160px", "maxWidth": "190px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center"},
                            children=[
                                html.Label("Half-Life (h)", style={"fontSize": "12px"}),
                                dcc.Input(
                                    id="halflife-input", type="number",
                                    value=DEFAULT_HALF_LIFE, min=0.5, max=48, step=0.5,
                                    persistence=True, persistence_type="local",
                                    style=HL_INPUT_STYLE,
                                ),
                            ],
                        ),
                        html.Div(style={"marginTop": "10px"}, children=[
                            dcc.Slider(
                                id="halflife-slider",
                                min=0.5, max=48, step=0.5, value=DEFAULT_HALF_LIFE,
                                marks={v: {"label": str(v)} for v in MARK_VALS},
                                tooltip={"always_visible": False},
                                updatemode="drag",
                                persistence=True, persistence_type="local",
                            ),
                        ]),

                        html.Label("Δt½ (h)", style={"fontSize": "12px", "display": "block",
                                                    "marginTop": "14px", "marginBottom": "4px"}),
                        dcc.Input(
                            id="delta-hl-input", type="number", value=None,
                            min=0, step=0.5, placeholder="0",
                            style={**INPUT_STYLE_BASE, "marginBottom": "10px"},
                        ),

                        html.Label("Ka (1/h)", style={"fontSize": "12px", "display": "block",
                                                       "marginTop": "10px", "marginBottom": "4px"}),
                        dcc.Input(
                            id="ka-input", type="number", value=DEFAULT_KA,
                            min=0.1, max=10, step=0.1,
                            persistence=True, persistence_type="local",
                            style={**INPUT_STYLE_BASE, "marginBottom": "12px"},
                        ),

                        html.Label("Doses (h from previous)",
                                   style={"fontSize": "12px", "display": "block",
                                          "marginTop": "12px", "marginBottom": "4px"}),
                        html.Div(
                            id="dose-slots",
                            style={"display": "flex", "flexDirection": "column", "gap": "3px"},
                            children=[
                                html.Div(
                                    style={"display": "flex", "gap": "2px", "alignItems": "center"},
                                    children=[
                                        html.Button("-", id={"type": "dose-minus", "index": i},
                                                    style={"width": "18px", "height": "22px",
                                                           "padding": "0", "cursor": "pointer",
                                                           "borderRadius": "3px", "border": "1px solid #aaa",
                                                           "fontSize": "14px", "flexShrink": "0"}),
                                        dcc.Input(
                                            id=f"dose-{i}", type="number", placeholder=f"D{i+2}",
                                            min=0, step="any",
                                            persistence=True, persistence_type="local",
                                            style={**INPUT_STYLE_BASE, "width": "auto", "flex": "1"},
                                        ),
                                        html.Button("+", id={"type": "dose-plus", "index": i},
                                                    style={"width": "18px", "height": "22px",
                                                           "padding": "0", "cursor": "pointer",
                                                           "borderRadius": "3px", "border": "1px solid #aaa",
                                                           "fontSize": "14px", "flexShrink": "0"}),
                                    ],
                                )
                                for i in range(7)
                            ],
                        ),
                    ],
                ),

                html.Div(
                    style={"flex": "1"},
                    children=[dcc.Graph(
                        id="pk-graph",
                        config={"toImageButtonOptions": {
                            "format": "png", "filename": "pk_simulation", "scale": 2,
                        }},
                    )],
                ),
            ],
        ),
    ],
    style={"fontFamily": "system-ui, sans-serif", "padding": "10px"},
)


# Slider → input (one-way, updatemode=drag so value fires continuously)
@app.callback(
    Output("halflife-input", "value"),
    Input("halflife-slider", "value"),
)
def slider_to_input(val):
    return val or DEFAULT_HALF_LIFE


@app.callback(
    Output("halflife-slider", "marks"),
    Input("theme-store", "data"),
)
def update_slider_marks(theme):
    color = DARK_THEME["text"] if theme == "dark" else LIGHT_THEME["text"]
    return {v: {"label": str(v), "style": {"color": color}} for v in MARK_VALS}


@app.callback(
    Output("theme-store", "data"),
    Input("theme-btn", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def toggle_theme(n, current):
    return "dark" if current == "light" else "light"


app.clientside_callback(
    """
    function(theme) {
        document.body.setAttribute('data-theme', theme);
        if (!document.getElementById('_no_slider_tip')) {
            var s = document.createElement('style');
            s.id = '_no_slider_tip';
            s.textContent = [
                '.rc-slider-tooltip { display:none!important; }',
                '[class*="rc-slider-tooltip"] { display:none!important; }',
                '.dash-slider-tooltip { display:none!important; }',
                '[class*="dash-slider-tooltip"] { display:none!important; }',
                '[role="tooltip"] { display:none!important; }'
            ].join(' ');
            document.head.appendChild(s);
        }
        return '';
    }
    """,
    Output("body-theme-setter", "children"),
    Input("theme-store", "data"),
)


@app.callback(
    Output("theme-btn", "style"),
    Input("theme-store", "data"),
)
def update_theme_btn_style(theme):
    if theme == "dark":
        return {"padding": "6px 14px", "cursor": "pointer", "borderRadius": "6px",
                "backgroundColor": "#2d3561", "color": "#e0e0e0", "border": "1px solid #4cc9f0"}
    return {"padding": "6px 14px", "cursor": "pointer", "borderRadius": "6px",
            "backgroundColor": "#e9ecef", "color": "#212529", "border": "1px solid #adb5bd"}


@app.callback(
    Output("main-container", "style"),
    Input("theme-store", "data"),
)
def update_container_style(theme):
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    return {
        "fontFamily": "system-ui, sans-serif",
        "padding": "10px",
        "backgroundColor": colors["bg"],
        "color": colors["text"],
        "minHeight": "100vh",
    }


@app.callback(
    [Output("halflife-input", "style"), Output("delta-hl-input", "style"),
     Output("ka-input", "style")] + [Output(f"dose-{i}", "style") for i in range(7)],
    Input("theme-store", "data"),
)
def update_input_styles(theme):
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    style = {
        **INPUT_STYLE_BASE,
        "border": f"1px solid {colors['grid']}",
        "backgroundColor": colors["paper"],
        "color": colors["text"],
    }
    hl_style = {
        **HL_INPUT_STYLE,
        "border": f"1px solid {colors['grid']}",
        "backgroundColor": colors["paper"],
        "color": colors["text"],
    }
    delta_style = dict(style, marginBottom="10px")
    return [hl_style, delta_style, dict(style, marginBottom="12px")] + [style] * 7


@app.callback(
    Output("xrange-store", "data"),
    Input("clean-btn", "n_clicks"),
    Input("halflife-input", "value"),
    Input("ka-input", "value"),
    *[Input(f"dose-{i}", "value") for i in range(7)],
    State("xrange-store", "data"),
    prevent_initial_call=True,
)
def update_xrange(n_clicks, half_life, ka, *args):
    dose_values = args[:7]
    current_xrange = args[7]

    if ctx.triggered_id != "clean-btn":
        return None

    # Toggle: second press resets
    if current_xrange is not None:
        return None

    half_life = (half_life or DEFAULT_HALF_LIFE)
    ka = (ka or DEFAULT_KA)
    ke = np.log(2) / half_life
    dose_times_abs = [0.0]
    last_t = 0.0
    for dv in dose_values:
        if dv is not None and dv >= 0:
            last_t += dv
            dose_times_abs.append(last_t)
    t_search = max(dose_times_abs) + 10 * half_life
    t, conc = compute_concentration(dose_times_abs, ka, ke, t_search)
    peak_idx = int(np.argmax(conc))
    below = np.where(conc[peak_idx:] <= 0.1)[0]
    if len(below) > 0:
        return float(t[peak_idx + below[0]])
    return float(t_search)


@app.callback(
    Output("pk-graph", "figure"),
    Input("halflife-input", "value"),
    Input("delta-hl-input", "value"),
    Input("ka-input", "value"),
    Input("theme-store", "data"),
    Input("xrange-store", "data"),
    *[Input(f"dose-{i}", "value") for i in range(7)],
)
def update_graph(half_life, delta_hl, ka, theme, xrange_override, *dose_values):
    if not half_life or half_life <= 0:
        half_life = DEFAULT_HALF_LIFE
    if not ka or ka <= 0:
        ka = DEFAULT_KA

    dose_times_abs = [0.0]
    last_t = 0.0
    for dv in dose_values:
        if dv is not None and dv >= 0:
            last_t += dv
            dose_times_abs.append(last_t)

    delta = float(delta_hl) if delta_hl and delta_hl > 0 else 0
    return build_figure(dose_times_abs, half_life, ka, theme,
                        xrange_override=xrange_override, delta_hl=delta)


@app.callback(
    [Output("halflife-input", "value"), Output("halflife-slider", "value"),
     Output("ka-input", "value")],
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_params(_):
    return [DEFAULT_HALF_LIFE, DEFAULT_HALF_LIFE, DEFAULT_KA]


@app.callback(
    [Output(f"dose-{i}", "value") for i in range(7)],
    Input("reset-btn", "n_clicks"),
    Input({"type": "dose-minus", "index": ALL}, "n_clicks"),
    Input({"type": "dose-plus", "index": ALL}, "n_clicks"),
    [State(f"dose-{i}", "value") for i in range(7)],
    prevent_initial_call=True,
)
def update_doses(reset_clicks, minus_clicks, plus_clicks, *current_values):
    triggered_id = ctx.triggered_id
    if triggered_id == "reset-btn":
        return [None] * 7
    if isinstance(triggered_id, dict):
        idx = triggered_id["index"]
        values = list(current_values)
        cur = values[idx] if values[idx] is not None else 0
        values[idx] = cur + 1 if triggered_id["type"] == "dose-plus" else max(0, cur - 1)
        return values
    return [no_update] * 7


if __name__ == "__main__":
    app.run(debug=False, port=8050)
