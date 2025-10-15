import numpy as np
import pandas as pd
import plotly.graph_objects as go
import ruptures as rpt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import random

random.seed(42)
np.random.seed(42)

from sovai.utils.port_manager import get_unique_port


def perform_pca_regime_change_analysis(df_accounting, ticker):
    df_signal = (
        df_accounting.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")
        .drop(columns=["ticker"])
    )

    # Calculate window size as 4% of total data
    window_size = max(int(len(df_signal) * 0.04), 2)

    # Scale the data
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df_signal)

    # Apply rolling PCA
    pca_values = []
    for i in range(len(df_scaled) - window_size + 1):
        window_data = df_scaled[i : i + window_size]
        pca = PCA(n_components=1)
        pca_transformed = pca.fit_transform(window_data)
        pca_values.append(pca_transformed[-1])

    # Create a Series for the PCA values
    pca_series = pd.Series(
        np.concatenate(pca_values), index=df_signal.index[window_size - 1 :]
    )

    # Detection using ruptures
    algo = rpt.Pelt(model="rbf").fit(pca_series.values)
    breakpoints = algo.predict(pen=10)

    # Ensure breakpoints are within the range of pca_series's index
    dates = pca_series.index.tolist()
    max_index = len(dates) - 1
    valid_breakpoints = [0] + [bp for bp in breakpoints if bp <= max_index]
    if valid_breakpoints[-1] != max_index:
        valid_breakpoints.append(max_index)

    # Create analysis DataFrame
    analysis_data = []
    color_1, color_2 = "blue", "orange"
    current_color = color_1

    for i in range(1, len(valid_breakpoints)):
        start_idx = valid_breakpoints[i - 1]
        end_idx = valid_breakpoints[i]
        segment = pca_series.iloc[start_idx:end_idx]

        current_color = color_1 if current_color == color_2 else color_2

        analysis_data.append(
            {
                "Start_Date": segment.index[0],
                "End_Date": segment.index[-1],
                "Duration_Days": (segment.index[-1] - segment.index[0]).days,
                "Color": current_color,
                "PCA_Start": segment.iloc[0],
                "PCA_End": segment.iloc[-1],
                "PCA_Change": segment.iloc[-1] - segment.iloc[0],
            }
        )

    analysis_df = pd.DataFrame(analysis_data)

    # Overall statistics
    overall_stats = pd.DataFrame(
        {
            "Statistic": [
                "Ticker",
                "Total_Regimes",
                "Average_Duration_Days",
                "Average_PCA_Change",
                "Window_Size",
            ],
            "Value": [
                ticker,
                len(analysis_df),
                analysis_df["Duration_Days"].mean(),
                analysis_df["PCA_Change"].mean(),
                window_size,
            ],
        }
    )

    analysis_df.attrs["stats"] = overall_stats
    analysis_df.attrs["pca_series"] = pca_series

    return analysis_df


def plot_pca_regime_change(df_accounting, ticker):
    analysis_df = perform_pca_regime_change_analysis(df_accounting, ticker)
    pca_series = analysis_df.attrs["pca_series"]
    overall_stats = analysis_df.attrs["stats"]

    fig = go.Figure()

    # Plot the entire time series
    fig.add_trace(
        go.Scatter(
            x=pca_series.index,
            y=pca_series,
            mode="lines",
            name="PCA Transformed Series",
            line=dict(color="gray"),
        )
    )

    # Add colored segments for each regime
    for _, regime in analysis_df.iterrows():
        segment = pca_series.loc[regime["Start_Date"] : regime["End_Date"]]
        fig.add_trace(
            go.Scatter(
                x=segment.index,
                y=segment,
                mode="lines",
                name=f"Segment {_}",
                line=dict(color=regime["Color"]),
                fill="tozeroy",
            )
        )

        # Add vertical line for regime change
        if _ < len(analysis_df) - 1:
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
        title=f'Rolling PCA Transformed Dataset with Regime Changes for {ticker} (Window Size: {overall_stats.loc[overall_stats["Statistic"] == "Window_Size", "Value"].values[0]})',
        xaxis_title="Date",
        yaxis_title="PCA Transformed Dataset",
        showlegend=False,
        plot_bgcolor="rgba(0, 0, 0, 0.95)",
        paper_bgcolor="rgba(0, 0, 0, 0.95)",
        font=dict(color="white", size=12),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    return fig


def run_pca_regime_change_dashboard(df_accounting, ticker=None):
    if ticker is None:
        ticker = df_accounting.index.get_level_values("ticker").unique()[0]

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
                "Rolling PCA Regime (All Features)",
                style={
                    "textAlign": "center",
                    "marginBottom": "20px",
                    "paddingTop": "10px",
                    "color": dark_mode_colors["text"],
                },
            ),
            html.Div(
                [
                    html.Label(
                        "Select Ticker:", style={"color": dark_mode_colors["text"]}
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
                style={"width": "30%", "margin": "0 auto", "padding": "20px 0px"},
            ),
            dcc.Graph(id="pca-regime-plot", style={"height": "80vh"}),
        ],
        style={
            "padding": "0 20px",
            "margin": "0 auto",
            "backgroundColor": dark_mode_colors["background"],
        },
    )

    @app.callback(
        Output("pca-regime-plot", "figure"), [Input("ticker-dropdown", "value")]
    )
    def update_graph(selected_ticker):
        fig = plot_pca_regime_change(df_accounting, selected_ticker)
        fig.update_layout(
            plot_bgcolor=dark_mode_colors["plot_bg"],
            paper_bgcolor=dark_mode_colors["plot_bg"],
            font_color=dark_mode_colors["text"],
        )
        fig.update_xaxes(gridcolor=dark_mode_colors["plot_gridlines"])
        fig.update_yaxes(gridcolor=dark_mode_colors["plot_gridlines"])
        return fig

    app_name = "pca-regime-change-app"
    return app.run(debug=False, port=get_unique_port(app_name))


# Example usage
# df_accounting = CustomDataFrame(your_data_here)  # Replace with your actual data
# pca_rc_result = df_accounting.pca_regime_change(method="data", ticker="AAPL")
# print(pca_rc_result)
# print(pca_rc_result.attrs['stats'])
# df_accounting.pca_regime_change(method="plot", ticker="AAPL")
