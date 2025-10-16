import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import random

random.seed(42)
np.random.seed(42)

from sovai.utils.port_manager import get_unique_port


def categorize_trend(
    segment, window_size=12, increase_threshold=0.05, decrease_threshold=-0.05
):
    if len(segment) < window_size:
        return "Insufficient Data"
    recent_segment = segment[-window_size:]
    slope, _, _, _, _ = stats.linregress(range(len(recent_segment)), recent_segment)
    if slope > increase_threshold:
        return "Increasing"
    elif slope < decrease_threshold:
        return "Decreasing"
    else:
        return "Sideways"


def perform_comprehensive_analysis(df_accounting, ticker, feature):
    from statsforecast.models import MSTL
    
    df_signal = (
        df_accounting.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")[feature]
    )

    # Decomposition
    seasonal_periods = [13, 52]
    model = MSTL(season_length=seasonal_periods).fit(df_signal)
    decomposition = model.model_

    # Reactive Trend Analysis
    n = len(df_signal)
    warm_up_period_ratio = 0.1
    warm_up_period = int(n * warm_up_period_ratio)
    window_size_ratio = 0.05
    window_size = max(int(n * window_size_ratio), 12)
    std_dev = np.std(df_signal)
    increase_threshold_ratio = 0.005
    decrease_threshold_ratio = -0.005
    increase_threshold = std_dev * increase_threshold_ratio
    decrease_threshold = std_dev * decrease_threshold_ratio
    trends = ["Insufficient Data"] * warm_up_period
    for i in range(warm_up_period, len(df_signal)):
        segment = df_signal.iloc[: i + 1]
        trend = categorize_trend(
            segment, window_size, increase_threshold, decrease_threshold
        )
        trends.append(trend)

    # Create comprehensive DataFrame
    comprehensive_df = pd.DataFrame(
        {
            "Observed": df_signal,
            "Trend": decomposition["trend"],
            "Remainder": decomposition["remainder"],
            "Reactive_Trend": trends,
        }
    )

    # Add seasonal components dynamically
    for col in decomposition.columns:
        if "season" in col.lower():
            comprehensive_df[f"Seasonal_{col}"] = decomposition[col]

    # Calculate overall statistics
    overall_slope, _, _, _, _ = stats.linregress(range(len(df_signal)), df_signal)
    trend_counts = pd.Series(trends).value_counts()

    # Create a dictionary for overall statistics
    overall_stats = pd.DataFrame(
        {
            "Statistic": [
                "Ticker",
                "Feature",
                "Total_Observations",
                "Overall_Average",
                "Overall_Trend_Slope",
                "Increasing_Trends_Count",
                "Decreasing_Trends_Count",
                "Sideways_Trends_Count",
                "Remainder_Standard_Deviation",
            ],
            "Value": [
                ticker,
                feature,
                len(df_signal),
                df_signal.mean(),
                overall_slope,
                trend_counts.get("Increasing", 0),
                trend_counts.get("Decreasing", 0),
                trend_counts.get("Sideways", 0),
                decomposition["remainder"].std(),
            ],
        }
    )

    # Add seasonal amplitudes using pd.concat
    new_rows = []
    for col in decomposition.columns:
        if "season" in col.lower():
            amplitude = decomposition[col].max() - decomposition[col].min()
            new_rows.append(
                pd.DataFrame([{"Statistic": f"Seasonal_{col}_Amplitude", "Value": amplitude}])
            )

    if new_rows: # Check if there are any seasonal components to add
        overall_stats = pd.concat([overall_stats] + new_rows, ignore_index=True)

    comprehensive_df.attrs["stats"] = overall_stats
    return comprehensive_df


def plot_comprehensive_analysis(comprehensive_df, ticker, feature):
    fig = make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=(
            "Observed",
            "Trend",
            "Seasonal (13)",
            "Seasonal (52)",
            "Reactive Trend Analysis",
        ),
    )

    # Add decomposition plots
    fig.add_trace(
        go.Scatter(
            x=comprehensive_df.index,
            y=comprehensive_df["Observed"],
            mode="lines",
            name="Observed",
            line=dict(color="white"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=comprehensive_df.index,
            y=comprehensive_df["Trend"],
            mode="lines",
            name="Trend",
            line=dict(color="cyan"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=comprehensive_df.index,
            y=comprehensive_df["Seasonal_seasonal13"],
            mode="lines",
            name="Seasonal (13)",
            line=dict(color="magenta"),
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=comprehensive_df.index,
            y=comprehensive_df["Seasonal_seasonal52"],
            mode="lines",
            name="Seasonal (52)",
            line=dict(color="yellow"),
        ),
        row=4,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=comprehensive_df.index,
            y=comprehensive_df["Remainder"],
            mode="lines",
            name="Remainder",
            line=dict(color="blue"),
        ),
        row=5,
        col=1,
    )

    # Add reactive trend analysis
    color_map = {
        "Increasing": "green",
        "Decreasing": "red",
        "Sideways": "yellow",
        "Insufficient Data": "gray",
    }
    current_trend = comprehensive_df["Reactive_Trend"].iloc[0]
    start_index = 0
    for i in range(1, len(comprehensive_df)):
        if (
            comprehensive_df["Reactive_Trend"].iloc[i] != current_trend
            or i == len(comprehensive_df) - 1
        ):
            segment = comprehensive_df["Observed"].iloc[start_index:i]
            fig.add_trace(
                go.Scatter(
                    x=segment.index,
                    y=segment,#
                    mode="lines",
                    name=current_trend,
                    line=dict(color=color_map[current_trend]),
                    fill="tozeroy",
                ),
                row=5,
                col=1,
            )
            current_trend = comprehensive_df["Reactive_Trend"].iloc[i]
            start_index = i

    # Update layout
    fig.update_layout(
        height=1000,
        title_text=f"{feature} Analysis for {ticker}",
        showlegend=False,
        plot_bgcolor="rgba(0, 0, 0, 1)",
        paper_bgcolor="rgba(0, 0, 0, 1)",
        font=dict(color="white"),
    )

    # Update y-axes titles
    fig.update_yaxes(title_text="Observed", row=1, col=1)
    fig.update_yaxes(title_text="Trend", row=2, col=1)
    fig.update_yaxes(title_text="Seasonal (13)", row=3, col=1)
    fig.update_yaxes(title_text="Seasonal (52)", row=4, col=1)
    fig.update_yaxes(title_text="Remainder", row=5, col=1)

    # Update x-axis title
    fig.update_xaxes(title_text="Date", row=5, col=1)

    return fig


def run_comprehensive_analysis_dashboard(df_accounting, ticker=None, feature=None):
    if ticker is None:
        ticker = df_accounting.index.get_level_values("ticker").unique()[0]
    if feature is None:
        feature = df_accounting.columns[0]

    app = dash.Dash(__name__)
    app.layout = html.Div(
        [
            html.H3(
                "Financial Metric Analysis",
                style={
                    "textAlign": "center",
                    "marginBottom": "20px",
                    "color": "white",
                    "marginTop": "20px",
                    "padding": "10px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Select Ticker:", style={"color": "white"}),
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
                            html.Label("Select Feature:", style={"color": "white"}),
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
            dcc.Graph(id="combined-plot", style={"height": "1000px"}),
        ],
        style={"padding": "0 20px", "margin": "0 auto"},
    )

    @app.callback(
        Output("combined-plot", "figure"),
        [Input("ticker-dropdown", "value"), Input("feature-dropdown", "value")],
    )
    def update_graph(selected_ticker, selected_feature):
        comprehensive_df = perform_comprehensive_analysis(
            df_accounting, selected_ticker, selected_feature
        )
        return plot_comprehensive_analysis(
            comprehensive_df, selected_ticker, selected_feature
        )

    app_name = "comprehensive-analysis-app"
    return app.run(debug=False, port=get_unique_port(app_name))


# Example usage
# df_accounting = your_data_here  # Replace with your actual data
# run_comprehensive_analysis_dashboard(df_accounting, ticker="AAPL", feature="total_revenue")
