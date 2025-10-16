import numpy as np
import pandas as pd
import ruptures as rpt
import matplotlib.colors as mcolors
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import random
import pandas as pd
import ruptures as rpt
import matplotlib.colors as mcolors

random.seed(42)
np.random.seed(42)

from sovai.utils.port_manager import get_unique_port


def perform_regime_change_analysis(df_accounting, ticker, feature):
    df_signal = (
        df_accounting.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")[feature]
    )
    signal_array = df_signal.values

    # Detection using ruptures
    algo = rpt.Pelt(model="rbf").fit(signal_array)
    breakpoints = algo.predict(pen=10)

    # Ensure breakpoints are within the range of df_signal's index
    dates = df_signal.index.tolist()
    max_index = len(dates) - 1  # Maximum valid index
    valid_breakpoints = [0] + [bp for bp in breakpoints if bp <= max_index]
    if valid_breakpoints[-1] != max_index:
        valid_breakpoints.append(max_index)

    # Define color maps for regimes
    cmap_up = mcolors.LinearSegmentedColormap.from_list("", ["lightgreen", "green"])
    cmap_down = mcolors.LinearSegmentedColormap.from_list("", ["lightcoral", "red"])
    cmap_sideways = mcolors.LinearSegmentedColormap.from_list(
        "", ["lightyellow", "yellow"]
    )

    def get_shaded_color(change_percentage, duration, cmap):
        avg_daily_change = change_percentage / duration
        norm_value = np.clip(avg_daily_change * duration, 0, 1)
        return mcolors.to_hex(cmap(norm_value))

    sideways_threshold = 0.01

    # Create analysis DataFrame
    analysis_data = []
    for i in range(1, len(valid_breakpoints)):
        start_idx = valid_breakpoints[i - 1]
        end_idx = valid_breakpoints[i]
        segment = df_signal.iloc[start_idx:end_idx]

        start_value = segment.iloc[0]
        end_value = segment.iloc[-1]
        change_percentage = (end_value - start_value) / start_value
        duration = (segment.index[-1] - segment.index[0]).days

        if abs(change_percentage) < sideways_threshold:
            trend = "Sideways"
            color = get_shaded_color(abs(change_percentage), duration, cmap_sideways)
        elif change_percentage > 0:
            trend = "Increasing"
            color = get_shaded_color(change_percentage, duration, cmap_up)
        else:
            trend = "Decreasing"
            color = get_shaded_color(abs(change_percentage), duration, cmap_down)

        analysis_data.append(
            {
                "Start_Date": segment.index[0],
                "End_Date": segment.index[-1],
                "Duration_Days": duration,
                "Start_Value": start_value,
                "End_Value": end_value,
                "Percent_Change": change_percentage * 100,
                "Trend": trend,
                "Color": color,
            }
        )

    analysis_df = pd.DataFrame(analysis_data)

    # Overall statistics
    overall_stats = pd.DataFrame(
        {
            "Statistic": [
                "Ticker",
                "Feature",
                "Total_Regimes",
                "Average_Duration_Days",
                "Average_Percent_Change",
                "Increasing_Trends",
                "Decreasing_Trends",
                "Sideways_Trends",
            ],
            "Value": [
                ticker,
                feature,
                len(analysis_df),
                analysis_df["Duration_Days"].mean(),
                analysis_df["Percent_Change"].mean(),
                sum(analysis_df["Trend"] == "Increasing"),
                sum(analysis_df["Trend"] == "Decreasing"),
                sum(analysis_df["Trend"] == "Sideways"),
            ],
        }
    )
    analysis_df.attrs["stats"] = overall_stats

    return analysis_df


def plot_regime_change(df_accounting, ticker, feature):
    df_signal = (
        df_accounting.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")[feature]
    )
    analysis_df = perform_regime_change_analysis(df_accounting, ticker, feature)

    fig = go.Figure()

    # Plot the regimes
    for i, regime in analysis_df.iterrows():
        mask = (df_signal.index >= regime["Start_Date"]) & (
            df_signal.index <= regime["End_Date"]
        )
        regime_data = df_signal[mask]

        fig.add_trace(
            go.Scatter(
                x=regime_data.index,
                y=regime_data,
                mode="lines",
                line=dict(color=regime["Color"], width=2),
                name=f"{regime['Trend']} ({regime['Start_Date'].date()} to {regime['End_Date'].date()})",
                showlegend=False,
                fill="tozeroy",
            )
        )

        # Add vertical line for regime change
        if i < len(analysis_df) - 1:
            fig.add_shape(
                type="line",
                x0=regime["End_Date"],
                y0=0,
                x1=regime["End_Date"],
                y1=1,
                line=dict(color="red", width=2, dash="dash"),
                xref="x",
                yref="paper",
            )
            fig.add_annotation(
                x=regime["End_Date"],
                y=1.05,
                text=f'{regime["Duration_Days"]} days',
                showarrow=False,
                yref="paper",
                align="center",
                font=dict(color="white"),
                textangle=90,
            )

    # Calculate duration of the current regime
    current_regime_duration = analysis_df.iloc[-1]["Duration_Days"]
    current_regime_date = analysis_df.iloc[-1]["End_Date"]
    fig.add_annotation(
        x=current_regime_date + pd.Timedelta(days=100),
        y=1.05,
        text=f"Current Regime: {current_regime_duration} days",
        showarrow=False,
        yref="paper",
        align="center",
        font=dict(color="white"),
        textangle=90,
    )

    # Update layout
    fig.update_layout(
        title=f"{feature} with Regime Changes for {ticker}",
        xaxis_title="Date",
        yaxis_title=feature,
        showlegend=False,
        plot_bgcolor="rgba(0, 0, 0, 0.95)",
        paper_bgcolor="rgba(0, 0, 0, 0.95)",
        font=dict(color="white", size=12),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    return fig


def run_regime_change_dashboard(df_accounting, ticker=None, feature=None):
    if ticker is None:
        ticker = df_accounting.index.get_level_values("ticker").unique()[0]
    if feature is None:
        feature = df_accounting.columns[0]

    app = dash.Dash(__name__)

    dark_mode_colors = {
        "background": "#1E1E1E",
        "text": "#FFFFFF",
        "plot_bg": "#2B2B2B",
        "plot_gridlines": "#3A3A3A",
    }

    app.layout = html.Div(
        [
            html.H3(
                "Financial Metric Regime Change Detection",
                style={
                    "textAlign": "center",
                    "marginBottom": "20px",
                    "paddingTop": "10px",
                    "color": dark_mode_colors["text"],
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Select Ticker:",
                                style={"color": dark_mode_colors["text"]},
                            ),
                            dcc.Dropdown(
                                id="ticker-dropdown",
                                options=[
                                    {"label": t, "value": t}
                                    for t in df_accounting.index.get_level_values(
                                        "ticker"
                                    ).unique()
                                ],
                                value=ticker,
                            ),
                        ],
                        style={"width": "48%", "display": "inline-block"},
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Select Feature:",
                                style={"color": dark_mode_colors["text"]},
                            ),
                            dcc.Dropdown(
                                id="feature-dropdown",
                                options=[
                                    {"label": col, "value": col}
                                    for col in df_accounting.columns
                                ],
                                value=feature,
                            ),
                        ],
                        style={
                            "width": "48%",
                            "float": "right",
                            "display": "inline-block",
                        },
                    ),
                ],
                style={"padding": "20px 0px"},
            ),
            dcc.Graph(id="regime-change-plot", style={"height": "80vh"}),
        ],
        style={
            "padding": "0 20px",
            "margin": "0 auto",
            "backgroundColor": dark_mode_colors["background"],
        },
    )

    @app.callback(
        Output("regime-change-plot", "figure"),
        [Input("ticker-dropdown", "value"), Input("feature-dropdown", "value")],
    )
    def update_graph(selected_ticker, selected_feature):
        fig = plot_regime_change(df_accounting, selected_ticker, selected_feature)
        fig.update_layout(
            plot_bgcolor=dark_mode_colors["plot_bg"],
            paper_bgcolor=dark_mode_colors["plot_bg"],
            font_color=dark_mode_colors["text"],
        )
        fig.update_xaxes(gridcolor=dark_mode_colors["plot_gridlines"])
        fig.update_yaxes(gridcolor=dark_mode_colors["plot_gridlines"])
        return fig

    app_name = "regime-change-app"
    return app.run(debug=False, port=get_unique_port(app_name))
