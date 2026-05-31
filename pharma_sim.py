import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx, ALL, no_update
import plotly.graph_objects as go

app = dash.Dash(__name__)

DEFAULT_HALF_LIFE = 6.0
DEFAULT_KA = 1.2
DEFAULT_REG_DOSES = 3
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


def parse_dose(v):
    try:
        f = float(v)
        return f if f >= 0 else None
    except (TypeError, ValueError):
        return None


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


def build_figure(dose_times_abs, half_life, ka, theme, t_range=72, xrange_override=None, delta_hl=0, show_max=False):
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
    y_max = max(2.5, float(np.max(conc)) * 1.2) if len(conc) > 0 else 2.5
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
        for td in sorted(set(dose_times_abs)):
            fig.add_vline(x=td, line=dict(color=colors["text"], width=1, dash="dot"), opacity=0.4)
    else:
        fig.add_trace(go.Scatter(
            x=t, y=conc, mode="lines",
            line=dict(color=colors["line"], width=2.5),
            showlegend=False,
        ))

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

    if show_max and len(dose_times_abs) > 1 and len(conc) > 2:
        diff = np.diff(conc)
        peak_idx_arr = np.where((diff[:-1] > 0) & (diff[1:] <= 0))[0] + 1
        if len(peak_idx_arr) >= 2:
            fig.add_trace(go.Scatter(
                x=t[peak_idx_arr], y=conc[peak_idx_arr],
                mode="lines",
                line=dict(color="#a855f7", width=1.5, shape="spline", smoothing=1.3, dash="dot"),
                showlegend=False,
            ))

    fig.add_hline(y=0.1, line=dict(color="#888888", width=1, dash="dot"))
    fig.add_hline(y=1.0, line=dict(color="#28a745", width=1.5))
    fig.add_hline(y=2.0, line=dict(color="#dc3545", width=1.5))

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
        xref="paper", yref="paper", x=0, y=1.06,
        ax=0, ay=16, axref="pixel", ayref="pixel",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
        arrowcolor=colors["text"], text=""
    )

    fig.update_layout(
        paper_bgcolor=colors["paper"],
        plot_bgcolor=colors["plot_bg"],
        font=dict(color=colors["text"]),
        showlegend=False,
        xaxis=dict(
            title=dict(text="Time (h)", standoff=5),
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
        margin=dict(l=60, r=60, t=38, b=30),
        height=360,
    )
    return fig


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
        dcc.Store(id="xrange-store-reg", data=None),
        dcc.Store(id="show-max-store", data=False),
        html.Div(id="body-theme-setter", style={"display": "none"}),

        html.Div(
            style={"display": "flex", "justifyContent": "center",
                   "alignItems": "center", "padding": "10px 20px", "position": "relative"},
            children=[
                html.H2("Pharmacokinetic Simulator", style={"margin": 0}),
                html.Div(style={"display": "flex", "gap": "8px",
                                "position": "absolute", "right": "20px"}, children=[
                    html.Button("Max", id="max-btn",
                                style={"padding": "6px 14px", "cursor": "pointer",
                                       "borderRadius": "6px"}),
                    html.Button("Show until clean", id="clean-btn",
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

        # Panel 1: arbitrary dosing
        html.Div(
            style={"display": "flex", "gap": "30px", "padding": "0 20px"},
            children=[
                html.Div(
                    style={"minWidth": "160px", "maxWidth": "190px", "overflow": "visible"},
                    children=[
                        html.Div(children=[
                            dcc.Slider(
                                id="halflife-slider",
                                min=0.5, max=48, step=0.5, value=DEFAULT_HALF_LIFE,
                                marks={v: {"label": str(v)} for v in MARK_VALS},
                                tooltip={"always_visible": False},
                                updatemode="drag",
                            ),
                        ]),
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center", "marginTop": "10px", "marginBottom": "4px"},
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

                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center", "marginTop": "14px",
                                   "marginBottom": "10px"},
                            children=[
                                html.Label("Δt½ (h)", style={"fontSize": "12px"}),
                                dcc.Input(
                                    id="delta-hl-input", type="text", inputMode="decimal",
                                    placeholder="0",
                                    style=HL_INPUT_STYLE,
                                ),
                            ],
                        ),

                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center", "marginBottom": "12px"},
                            children=[
                                html.Label("Ka (1/h)", style={"fontSize": "12px"}),
                                dcc.Input(
                                    id="ka-input", type="text", inputMode="decimal",
                                    value=str(DEFAULT_KA),
                                    persistence=True, persistence_type="local",
                                    style=HL_INPUT_STYLE,
                                ),
                            ],
                        ),

                        html.Div(
                            id="dose-slots",
                            style={"display": "flex", "flexDirection": "column", "gap": "4px",
                                   "marginTop": "14px"},
                            children=[
                                html.Div(
                                    style={"display": "flex", "justifyContent": "space-between",
                                           "alignItems": "center"},
                                    children=[
                                        html.Label(f"Dose {i+2} (h)",
                                                   style={"fontSize": "12px"}),
                                        html.Div(
                                            style={"position": "relative", "width": "62px",
                                                   "flexShrink": "0"},
                                            children=[
                                                html.Button("-", id={"type": "dose-minus", "index": i},
                                                            style={"position": "absolute",
                                                                   "right": "calc(100% + 2px)", "top": "0",
                                                                   "width": "18px", "height": "22px",
                                                                   "padding": "0", "cursor": "pointer",
                                                                   "borderRadius": "3px",
                                                                   "border": "1px solid #aaa",
                                                                   "fontSize": "14px"}),
                                                dcc.Input(
                                                    id=f"dose-{i}", type="text", inputMode="decimal",
                                                    placeholder="—",
                                                    persistence=True, persistence_type="local",
                                                    style={**HL_INPUT_STYLE, "width": "100%"},
                                                ),
                                                html.Button("+", id={"type": "dose-plus", "index": i},
                                                            style={"position": "absolute",
                                                                   "left": "calc(100% + 2px)", "top": "0",
                                                                   "width": "18px", "height": "22px",
                                                                   "padding": "0", "cursor": "pointer",
                                                                   "borderRadius": "3px",
                                                                   "border": "1px solid #aaa",
                                                                   "fontSize": "14px"}),
                                            ],
                                        ),
                                    ],
                                )
                                for i in range(7)
                            ],
                        ),
                    ],
                ),

                html.Div(
                    style={"flex": "1", "minWidth": "0"},
                    children=[dcc.Graph(
                        id="pk-graph",
                        style={"height": "360px"},
                        config={"toImageButtonOptions": {
                            "format": "png", "filename": "pk_simulation", "scale": 2,
                        }},
                    )],
                ),
            ],
        ),

        # Panel 2: regular dosing regime
        html.Div(
            style={"display": "flex", "gap": "30px", "padding": "0 20px", "marginTop": "20px"},
            children=[
                html.Div(
                    style={"minWidth": "160px", "maxWidth": "190px", "overflow": "visible"},
                    children=[
                        html.Label("N Doses", style={"fontSize": "12px", "display": "block",
                                                      "marginBottom": "4px"}),
                        dcc.Slider(
                            id="reg-doses-slider",
                            min=1, max=10, step=1, value=DEFAULT_REG_DOSES,
                            marks={v: {"label": str(v)} for v in [1, 2, 3, 5, 7, 10]},
                            tooltip={"always_visible": False},
                            persistence=True, persistence_type="local",
                        ),

                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between",
                                   "alignItems": "center", "marginTop": "20px", "marginBottom": "4px"},
                            children=[
                                html.Label("Interval (h)", style={"fontSize": "12px"}),
                                dcc.Input(
                                    id="reg-interval-input", type="text", inputMode="decimal",
                                    value=str(DEFAULT_HALF_LIFE),
                                    persistence=True, persistence_type="local",
                                    style=HL_INPUT_STYLE,
                                ),
                            ],
                        ),
                        dcc.Slider(
                            id="reg-interval-slider",
                            min=0, max=2 * DEFAULT_HALF_LIFE, step=0.5, value=DEFAULT_HALF_LIFE,
                            marks={
                                0: {"label": "0"},
                                DEFAULT_HALF_LIFE: {"label": f"{DEFAULT_HALF_LIFE:.0f}h"},
                                2 * DEFAULT_HALF_LIFE: {"label": f"{2 * DEFAULT_HALF_LIFE:.0f}h"},
                            },
                            tooltip={"always_visible": False},
                            updatemode="drag",
                        ),
                    ],
                ),

                html.Div(
                    style={"flex": "1", "minWidth": "0"},
                    children=[dcc.Graph(
                        id="pk-graph-reg",
                        style={"height": "360px"},
                        config={"toImageButtonOptions": {
                            "format": "png", "filename": "pk_simulation_regular", "scale": 2,
                        }},
                    )],
                ),
            ],
        ),
    ],
    style={"fontFamily": "system-ui, sans-serif", "padding": "10px"},
)


@app.callback(
    Output("halflife-input", "value"),
    Input("halflife-slider", "value"),
    prevent_initial_call=True,
)
def slider_to_input(val):
    return val or DEFAULT_HALF_LIFE


app.clientside_callback(
    "function(v) { var f = parseFloat(v); return (f >= 0.5 && f <= 48) ? f : window.dash_clientside.no_update; }",
    Output("halflife-slider", "value"),
    Input("halflife-input", "value"),
)


@app.callback(
    Output("reg-interval-input", "value"),
    Input("reg-interval-slider", "value"),
    prevent_initial_call=True,
)
def reg_interval_slider_to_input(val):
    if val is None:
        return str(DEFAULT_HALF_LIFE)
    return str(int(val)) if val == int(val) else str(val)


app.clientside_callback(
    "function(v) { var f = parseFloat(v); return (f >= 0) ? f : window.dash_clientside.no_update; }",
    Output("reg-interval-slider", "value"),
    Input("reg-interval-input", "value"),
)


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
        var rangeColor = theme === 'dark' ? '#4cc9f0' : '#0d6efd';
        var railColor  = theme === 'dark' ? '#4a5568' : '#dee2e6';
        function applySliderColors() {
            document.querySelectorAll('.dash-slider-track').forEach(function(el) {
                el.style.setProperty('background', railColor, 'important');
            });
            document.querySelectorAll('.dash-slider-range').forEach(function(el) {
                el.style.setProperty('background', rangeColor, 'important');
            });
            document.querySelectorAll('.dash-slider-thumb').forEach(function(el) {
                el.style.setProperty('background', rangeColor, 'important');
                el.style.setProperty('border-color', rangeColor, 'important');
            });
        }
        applySliderColors();
        setTimeout(applySliderColors, 100);
        return '';
    }
    """,
    Output("body-theme-setter", "children"),
    Input("theme-store", "data"),
)


@app.callback(
    Output("show-max-store", "data"),
    Input("max-btn", "n_clicks"),
    State("show-max-store", "data"),
    prevent_initial_call=True,
)
def toggle_max(_, current):
    return not current


@app.callback(
    Output("max-btn", "style"),
    Input("show-max-store", "data"),
    Input("theme-store", "data"),
)
def update_max_btn_style(active, theme):
    base = {"padding": "6px 14px", "cursor": "pointer", "borderRadius": "6px"}
    if active:
        return {**base, "backgroundColor": "#a855f7", "color": "#ffffff",
                "border": "1px solid #9333ea", "fontWeight": "600"}
    if theme == "dark":
        return {**base, "backgroundColor": "#2d3561", "color": "#e0e0e0",
                "border": "1px solid #4a5568"}
    return {**base, "backgroundColor": "#e9ecef", "color": "#212529",
            "border": "1px solid #adb5bd"}


@app.callback(
    Output("clean-btn", "style"),
    Input("xrange-store", "data"),
    Input("theme-store", "data"),
)
def update_clean_btn_style(xrange, theme):
    base = {"padding": "6px 14px", "cursor": "pointer", "borderRadius": "6px"}
    if xrange is not None:
        return {**base, "backgroundColor": "#0d6efd", "color": "#ffffff",
                "border": "1px solid #0a58ca", "fontWeight": "600"}
    if theme == "dark":
        return {**base, "backgroundColor": "#2d3561", "color": "#e0e0e0",
                "border": "1px solid #4a5568"}
    return {**base, "backgroundColor": "#e9ecef", "color": "#212529",
            "border": "1px solid #adb5bd"}


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
     Output("ka-input", "style"), Output("reg-interval-input", "style")]
    + [Output(f"dose-{i}", "style") for i in range(7)],
    Input("theme-store", "data"),
)
def update_input_styles(theme):
    colors = DARK_THEME if theme == "dark" else LIGHT_THEME
    hl_style = {
        **HL_INPUT_STYLE,
        "border": f"1px solid {colors['grid']}",
        "backgroundColor": colors["paper"],
        "color": colors["text"],
    }
    return [hl_style] * 4 + [hl_style] * 7


def _compute_cutoff(half_life, ka, dose_values):
    hl = half_life or DEFAULT_HALF_LIFE
    ka_val = parse_dose(ka) or DEFAULT_KA
    ke = np.log(2) / hl
    dose_times_abs = [0.0]
    last_t = 0.0
    for dv in dose_values:
        parsed = parse_dose(dv)
        if parsed is not None:
            last_t += parsed
            dose_times_abs.append(last_t)
    t_search = max(dose_times_abs) + 10 * hl
    t, conc = compute_concentration(dose_times_abs, ka_val, ke, t_search)
    peak_idx = int(np.argmax(conc))
    below = np.where(conc[peak_idx:] <= 0.1)[0]
    return float(t[peak_idx + below[0]]) if len(below) > 0 else float(t_search)


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
    triggered = ctx.triggered_id

    if triggered == "clean-btn":
        if current_xrange is not None:
            return None
        return _compute_cutoff(half_life, ka, dose_values)

    # param change while clean active → recompute
    if current_xrange is not None:
        return _compute_cutoff(half_life, ka, dose_values)

    return no_update


@app.callback(
    Output("pk-graph", "figure"),
    Input("halflife-input", "value"),
    Input("delta-hl-input", "value"),
    Input("ka-input", "value"),
    Input("theme-store", "data"),
    Input("xrange-store", "data"),
    Input("show-max-store", "data"),
    *[Input(f"dose-{i}", "value") for i in range(7)],
)
def update_graph(half_life, delta_hl, ka, theme, xrange_override, show_max, *dose_values):
    if not half_life or half_life <= 0:
        half_life = DEFAULT_HALF_LIFE
    ka = parse_dose(ka) or DEFAULT_KA

    dose_times_abs = [0.0]
    last_t = 0.0
    for dv in dose_values:
        parsed = parse_dose(dv)
        if parsed is not None:
            last_t += parsed
            dose_times_abs.append(last_t)

    delta_parsed = parse_dose(delta_hl)
    delta = delta_parsed if delta_parsed and delta_parsed > 0 else 0
    return build_figure(dose_times_abs, half_life, ka, theme,
                        xrange_override=xrange_override, delta_hl=delta, show_max=show_max)


@app.callback(
    [Output("halflife-input", "value"), Output("halflife-slider", "value"),
     Output("ka-input", "value")],
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_params(_):
    return [DEFAULT_HALF_LIFE, DEFAULT_HALF_LIFE, str(DEFAULT_KA)]


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
        cur = parse_dose(values[idx]) or 0
        new_val = cur + 1 if triggered_id["type"] == "dose-plus" else max(0, cur - 1)
        values[idx] = str(int(new_val)) if new_val == int(new_val) else str(new_val)
        return values
    return [no_update] * 7


# --- Panel 2 callbacks ---

@app.callback(
    Output("reg-interval-slider", "max"),
    Output("reg-interval-slider", "marks"),
    Input("halflife-input", "value"),
    Input("theme-store", "data"),
)
def update_reg_interval_props(half_life, theme):
    hl = half_life if half_life and half_life > 0 else DEFAULT_HALF_LIFE
    new_max = 2 * hl
    color = DARK_THEME["text"] if theme == "dark" else LIGHT_THEME["text"]

    def fmt(v):
        return f"{v:.0f}h" if v == int(v) else f"{v:.1f}h"

    marks = {
        0: {"label": "0", "style": {"color": color}},
        hl: {"label": fmt(hl), "style": {"color": color}},
        new_max: {"label": fmt(new_max), "style": {"color": color}},
    }
    return new_max, marks


@app.callback(
    Output("reg-doses-slider", "marks"),
    Input("theme-store", "data"),
)
def update_reg_doses_marks(theme):
    color = DARK_THEME["text"] if theme == "dark" else LIGHT_THEME["text"]
    return {v: {"label": str(v), "style": {"color": color}} for v in [1, 2, 3, 5, 7, 10]}


@app.callback(
    Output("reg-doses-slider", "value"),
    Output("reg-interval-slider", "value"),
    Output("reg-interval-input", "value"),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_reg_params(_):
    return DEFAULT_REG_DOSES, DEFAULT_HALF_LIFE, str(DEFAULT_HALF_LIFE)


def _compute_reg_cutoff(half_life, ka, n_doses, interval_str):
    hl = half_life if half_life and half_life > 0 else DEFAULT_HALF_LIFE
    ka_val = parse_dose(ka) or DEFAULT_KA
    ke = np.log(2) / hl
    n = int(n_doses or DEFAULT_REG_DOSES)
    iv = parse_dose(interval_str)
    if iv is None:
        iv = hl
    iv = min(iv, 2 * hl)
    dose_times_abs = [0.0] * n if iv == 0 else [i * iv for i in range(n)]
    t_search = max(dose_times_abs) + 10 * hl
    t, conc = compute_concentration(dose_times_abs, ka_val, ke, t_search)
    peak_idx = int(np.argmax(conc))
    below = np.where(conc[peak_idx:] <= 0.1)[0]
    return float(t[peak_idx + below[0]]) if len(below) > 0 else float(t_search)


@app.callback(
    Output("xrange-store-reg", "data"),
    Input("clean-btn", "n_clicks"),
    Input("halflife-input", "value"),
    Input("ka-input", "value"),
    Input("reg-doses-slider", "value"),
    Input("reg-interval-input", "value"),
    State("xrange-store-reg", "data"),
    prevent_initial_call=True,
)
def update_reg_xrange(n_clicks, half_life, ka, n_doses, interval_str, current_xrange):
    triggered = ctx.triggered_id

    if triggered == "clean-btn":
        if current_xrange is not None:
            return None
        return _compute_reg_cutoff(half_life, ka, n_doses, interval_str)

    # halflife/ka change → deactivate clean
    if triggered in ("halflife-input", "ka-input"):
        return None

    # reg-specific params change while clean active → recompute cutoff
    if triggered in ("reg-doses-slider", "reg-interval-input"):
        if current_xrange is None:
            return no_update
        return _compute_reg_cutoff(half_life, ka, n_doses, interval_str)

    return no_update


@app.callback(
    Output("pk-graph-reg", "figure"),
    Input("halflife-input", "value"),
    Input("delta-hl-input", "value"),
    Input("ka-input", "value"),
    Input("theme-store", "data"),
    Input("xrange-store-reg", "data"),
    Input("show-max-store", "data"),
    Input("reg-doses-slider", "value"),
    Input("reg-interval-input", "value"),
)
def update_reg_graph(half_life, delta_hl, ka, theme, xrange_override, show_max, n_doses, interval_str):
    hl = half_life if half_life and half_life > 0 else DEFAULT_HALF_LIFE
    ka = parse_dose(ka) or DEFAULT_KA
    n = int(n_doses or DEFAULT_REG_DOSES)
    iv = parse_dose(interval_str)
    if iv is None:
        iv = hl
    iv = min(iv, 2 * hl)

    if iv == 0:
        dose_times_abs = [0.0] * n
    else:
        dose_times_abs = [i * iv for i in range(n)]

    delta_parsed = parse_dose(delta_hl)
    delta = delta_parsed if delta_parsed and delta_parsed > 0 else 0
    return build_figure(dose_times_abs, hl, ka, theme,
                        xrange_override=xrange_override, delta_hl=delta, show_max=show_max)


if __name__ == "__main__":
    app.run(debug=False, port=8050)
