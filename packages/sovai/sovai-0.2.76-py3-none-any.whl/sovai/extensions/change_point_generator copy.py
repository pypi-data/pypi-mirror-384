import numpy as np
import pandas as pd
from typing import Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import random

random.seed(42)
np.random.seed(42)

# Your code that uses NumPy's random functions
# Global dictionary to keep track of apps and their ports
app_ports = {}


def get_unique_port(app_name):
    global app_ports
    min_port = 8050  # define the range of ports you want to use
    max_port = 8099

    if app_name in app_ports:
        # Return the previously assigned port for this app
        return app_ports[app_name]
    else:
        # Generate a unique port for the new app
        while True:
            port = random.randint(min_port, max_port)
            if (
                port not in app_ports.values()
            ):  # check if the port is not already in use
                app_ports[app_name] = port
                return port


class ImprovedCusumDetector:
    def __init__(
        self,
        window_size_ratio: float = 0.05,
        threshold_factor: float = 2.5,
        drift_factor: float = 0.05,
        min_distance: int = 30,
        sideways_threshold: float = 0.03,
        warm_up_period_ratio: float = 0.1,
    ):
        self.window_size_ratio = window_size_ratio
        self.threshold_factor = threshold_factor
        self.drift_factor = drift_factor
        self.min_distance = min_distance
        self.sideways_threshold = sideways_threshold
        self.warm_up_period_ratio = warm_up_period_ratio

    def detect_changepoints(
        self, signal: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        n = len(signal)
        window_size = max(int(n * self.window_size_ratio), 8)
        warm_up_period = int(n * self.warm_up_period_ratio)

        ewma = self._calculate_ewma(signal, window_size)
        z_scores = self._calculate_rolling_z_scores(signal, ewma, window_size)
        scores, changepoints, trend_codes = self._calculate_two_sided_cusum(
            signal,
            z_scores,
            self.drift_factor,
            self.threshold_factor,
            self.min_distance,
            self.sideways_threshold,
            warm_up_period,
        )

        trends = np.where(
            trend_codes == 1,
            "Increasing",
            np.where(trend_codes == -1, "Decreasing", "Sideways"),
        )

        return changepoints, trends, scores, window_size

    import numba
    import numpy as np

    @staticmethod
    @numba.njit(cache=True)
    def _calculate_ewma(signal, window_size):
        alpha = 2 / (window_size + 1)
        ewma = np.zeros_like(signal)
        ewma[0] = signal[0]
        for i in range(1, len(signal)):
            ewma[i] = alpha * signal[i] + (1 - alpha) * ewma[i - 1]
        return ewma

    @staticmethod
    @numba.njit(cache=True)
    def _calculate_rolling_z_scores(signal, ewma, window_size):
        rolling_var = np.zeros_like(signal)
        for i in range(window_size, len(signal)):
            rolling_var[i] = np.var(signal[i - window_size + 1 : i + 1])
        rolling_std = np.sqrt(rolling_var)
        z_scores = (signal - ewma) / (rolling_std + 1e-8)
        return z_scores

    @staticmethod
    @numba.njit(cache=True)
    def _calculate_two_sided_cusum(
        signal,
        z,
        drift,
        threshold_factor,
        min_distance,
        sideways_threshold,
        warm_up_period,
    ):
        cs_upper = np.zeros_like(z)
        cs_lower = np.zeros_like(z)
        changepoints = []
        trend_codes = []
        last_cp = -min_distance
        for i in range(1, len(z)):
            if i < warm_up_period:
                continue
            cs_upper[i] = max(0, cs_upper[i - 1] + z[i] - drift)
            cs_lower[i] = min(0, cs_lower[i - 1] + z[i] + drift)
            if i - last_cp >= min_distance:
                if cs_upper[i] > threshold_factor * np.sqrt(i):
                    changepoints.append(i)
                    trend_codes.append(1)
                    cs_upper[i] = 0
                    cs_lower[i] = 0
                    last_cp = i
                elif cs_lower[i] < -threshold_factor * np.sqrt(i):
                    changepoints.append(i)
                    trend_codes.append(-1)
                    cs_upper[i] = 0
                    cs_lower[i] = 0
                    last_cp = i
                elif (
                    i > 0
                    and abs((signal[i] - signal[last_cp]) / signal[last_cp])
                    < sideways_threshold
                ):
                    changepoints.append(i)
                    trend_codes.append(0)
                    cs_upper[i] = 0
                    cs_lower[i] = 0
                    last_cp = i
        return (
            np.maximum(cs_upper, -cs_lower),
            np.array(changepoints),
            np.array(trend_codes),
        )

def plot_cusum_results(
    df_signal, signal_array, changepoints, trends, scores, ticker, feature
):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"{feature} Over Time for {ticker}", "CUSUM Score"),
    )

    fig.add_trace(
        go.Scatter(
            x=df_signal.index,
            y=signal_array,
            mode="lines",
            line=dict(color="gold", width=2),
            name=feature,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df_signal.index,
            y=scores,
            mode="lines",
            line=dict(color="rgba(30, 144, 255, 0.7)", width=1.5),
            name="CUSUM Score",
        ),
        row=2,
        col=1,
    )

    colors = {"Increasing": "lime", "Decreasing": "red", "Sideways": "yellow"}
    symbols = {
        "Increasing": "triangle-up",
        "Decreasing": "triangle-down",
        "Sideways": "circle",
    }

    for trend in set(trends):
        mask = trends == trend
        fig.add_trace(
            go.Scatter(
                x=df_signal.index[changepoints[mask]],
                y=signal_array[changepoints[mask]],
                mode="markers",
                marker=dict(color=colors[trend], size=10, symbol=symbols[trend]),
                name=f"{trend}",
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        title=f"{feature} Change Point Detection for {ticker}",
        plot_bgcolor="rgba(0,0,0,0.95)",
        paper_bgcolor="rgba(0,0,0,0.95)",
        font=dict(color="white", size=12),
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.5)",
        ),
        showlegend=True,
    )

    fig.update_xaxes(title_text="Date", row=2, col=1, gridcolor="rgba(255,255,255,0.2)")
    fig.update_yaxes(
        title_text=feature, type="log", row=1, col=1, gridcolor="rgba(255,255,255,0.2)"
    )
    fig.update_yaxes(
        title_text="CUSUM Score", row=2, col=1, gridcolor="rgba(255,255,255,0.2)"
    )

    for i, (cp, trend) in enumerate(zip(changepoints, trends)):
        fig.add_annotation(
            x=df_signal.index[cp],
            y=signal_array[cp],
            text=f"{trend[0]} {i+1}",
            showarrow=False,
            yshift=10 if trend == "Increasing" else -10,
            font=dict(color=colors[trend]),
            row=1,
            col=1,
        )

    return fig


def run_cusum_dashboard(df_accounting, ticker=None, feature=None):
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
                "Financial Metric Change Point Detection",
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
            dcc.Graph(id="cusum-plot", style={"height": "80vh"}),
        ],
        style={
            "padding": "0 20px",
            "margin": "0 auto",
            "backgroundColor": dark_mode_colors["background"],
        },
    )

    @app.callback(
        Output("cusum-plot", "figure"),
        [Input("ticker-dropdown", "value"), Input("feature-dropdown", "value")],
    )
    def update_graph(selected_ticker, selected_feature):
        df_signal = (
            df_accounting.query(f"ticker == '{selected_ticker}'")
            .reset_index()
            .set_index("date")[selected_feature]
        )
        signal_array = df_signal.values
        detector = ImprovedCusumDetector()
        changepoints, trends, scores, window_size = detector.detect_changepoints(
            signal_array
        )
        fig = plot_cusum_results(
            df_signal,
            signal_array,
            changepoints,
            trends,
            scores,
            selected_ticker,
            selected_feature,
        )
        fig.update_layout(
            plot_bgcolor=dark_mode_colors["plot_bg"],
            paper_bgcolor=dark_mode_colors["plot_bg"],
            font_color=dark_mode_colors["text"],
        )
        fig.update_xaxes(gridcolor=dark_mode_colors["plot_gridlines"])
        fig.update_yaxes(gridcolor=dark_mode_colors["plot_gridlines"])
        return fig

    app_name = "cumsum-app"
    return app.run(debug=False, port=get_unique_port(app_name))


def perform_cusum_analysis(df_accounting, ticker=None, feature=None):
    # Get the first ticker and feature if not provided
    if ticker is None:
        ticker = df_accounting.index.get_level_values("ticker").unique()[0]
    if feature is None:
        feature = df_accounting.columns[0]

    # Extract the signal for the specified ticker and feature
    df_signal = (
        df_accounting.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")[feature]
    )

    detector = ImprovedCusumDetector()
    signal_array = df_signal.values
    changepoints, trends, scores, window_size = detector.detect_changepoints(
        signal_array
    )

    # Create main analysis DataFrame
    analysis_df = pd.DataFrame(
        {
            "Date": df_signal.index[changepoints],
            "Trend": trends,
            "Signal_Value": signal_array[changepoints],
            "CUSUM_Score": scores[
                changepoints - 1
            ],  # Take the score from just before the change point
        }
    )

    # Calculate duration between change points
    analysis_df["Duration"] = (
        analysis_df["Date"].diff().shift(-1).fillna(pd.Timedelta(days=0))
    )
    analysis_df["Duration_Days"] = analysis_df["Duration"].dt.days

    # Calculate percentage change between change points
    analysis_df["Percent_Change"] = (
        analysis_df["Signal_Value"].pct_change().shift(-1) * 100
    ).fillna(0)

    # Overall statistics
    overall_stats = pd.DataFrame(
        {
            "Statistic": [
                "Ticker",
                "Feature",
                "Total_Change_Points",
                "Average_Duration_Days",
                "Average_Percent_Change",
                "Increasing_Trends",
                "Decreasing_Trends",
                "Sideways_Trends",
                "Max_CUSUM_Score",
                "Min_CUSUM_Score",
                "Window_Size",
            ],
            "Value": [
                ticker,
                feature,
                len(changepoints),
                analysis_df["Duration_Days"].mean(),
                analysis_df["Percent_Change"].mean(),
                sum(trends == "Increasing"),
                sum(trends == "Decreasing"),
                sum(trends == "Sideways"),
                scores.max(),
                scores[scores > 0].min() if any(scores > 0) else 0,
                window_size,
            ],
        }
    )

    analysis_df.attrs["stats"] = overall_stats

    return analysis_df
