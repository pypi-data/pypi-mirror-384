import numpy as np
import pandas as pd
from typing import Tuple, List, Optional # Modified to include List and Optional for new functions
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import random
import socket # Added for port management
import time # Added for port management
import errno # Added for port management

# from port_manager_utility import get_unique_port, kill_process_on_port, release_port, get_port_manager_instance
# from utils.port_manager import get_unique_port, kill_process_on_port
from sovai.utils.port_manager import get_unique_port, kill_process_on_port

random.seed(42)
np.random.seed(42)

# Global dictionary to keep track of apps and their ports launched by this script
app_ports = {}

class ImprovedCusumDetector: # Exactly as in the first script
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
                elif ( # This condition for sideways might lead to ZeroDivisionError if signal[last_cp] is 0. Preserved as per original.
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

def plot_cusum_results( # Exactly as in the first script
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
        # Original script might have index out of bounds if changepoints[mask] is empty or values are too large. Preserved.
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
        # Original script might have index out of bounds if cp is too large. Preserved.
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


def run_cusum_dashboard(df_accounting, ticker=None, feature=None): # Modified for new port logic
    if ticker is None:
        ticker_options = df_accounting.index.get_level_values("ticker").unique()
        if not ticker_options.empty:
            ticker = ticker_options[0]
        else:
            print("Error: No tickers found in DataFrame for dashboard.")
            return
    if feature is None:
        if not df_accounting.columns.empty:
            feature = df_accounting.columns[0]
        else:
            print("Error: No features found in DataFrame for dashboard.")
            return

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
    def update_graph(selected_ticker, selected_feature): # Exactly as in the first script's dashboard
        df_signal = (
            df_accounting.query(f"ticker == '{selected_ticker}'")
            .reset_index()
            .set_index("date")[selected_feature]
        )
        signal_array = df_signal.values
        # Add a check for empty signal_array to prevent errors downstream
        if len(signal_array) == 0:
            fig = go.Figure()
            fig.update_layout(
                title_text=f"No data available for {selected_ticker} - {selected_feature}",
                plot_bgcolor=dark_mode_colors["plot_bg"],
                paper_bgcolor=dark_mode_colors["plot_bg"],
                font_color=dark_mode_colors["text"],
            )
            return fig
            
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

    app_name = f"cumsum-app-{ticker}-{feature}".replace(" ","_") # Using more specific app name
    
    # --- Robust Server Launch (from the second script) ---
    max_retries = 3
    for attempt in range(max_retries):
        port = get_unique_port(app_name)
        try:
            print(f"Attempting to launch Dash app '{app_name}' on port {port} (Attempt {attempt + 1}/{max_retries})")
            # Using host='0.0.0.0' to make it accessible on the network
            app.run(debug=False, port=port, host='0.0.0.0') 
            print(f"Dash app '{app_name}' running on http://127.0.0.1:{port}/ or http://<your-ip>:{port}/")
            break # Success
        except socket.error as e:
            if e.errno == errno.EADDRINUSE: # Address already in use
                print(f"Port {port} is in use. Attempting to kill blocking process(es).")
                if kill_process_on_port(port):
                    print(f"Successfully killed process(es) on port {port}. Retrying Dash launch...")
                    time.sleep(2) # Give OS a moment to free the port
                else:
                    print(f"Could not kill process(es) on port {port} or no process found. Trying a different port.")
                    # Invalidate this port for this app_name so get_unique_port tries a new one
                    if app_name in app_ports and app_ports[app_name] == port:
                        del app_ports[app_name] 
                
                if attempt == max_retries - 1:
                    print(f"Failed to launch Dash app '{app_name}' after {max_retries} attempts. Port {port} remains occupied.")
                    # Not returning here, as the original run_server call was the return
                    # This will effectively mean the function finishes if all retries fail.
                    # To match original behavior of returning the server object, this structure would need adjustment
                    # However, run_server is blocking, so returning it means the rest of the script doesn't run until server stops.
                    # This current structure runs the server and blocks, or prints failure and continues if it can't.
                    # The original `return app.run(...)` would also block.
                    # If it fails to launch due to port, original would raise error immediately.
                    # This structure tries to recover or fails after retries.
                    # To make it fully equivalent on failure, we should re-raise here.
                    raise RuntimeError(f"Failed to launch Dash app '{app_name}' after {max_retries} attempts. Port {port} remains occupied.")
            else:
                print(f"An unexpected socket error occurred: {e}")
                raise # Re-raise other socket errors
        except Exception as e:
            print(f"An unexpected error occurred during app launch: {e}")
            raise
    else: # Executed if the loop completes without break (i.e., all retries failed before exception)
         print(f"CRITICAL: Dash app '{app_name}' could not be started after {max_retries} attempts due to port issues without raising an exception in the loop (should not happen).")
         # This else block for the for loop is unlikely to be hit if EADDRINUSE always occurs and leads to a raise on final attempt.
         # If get_unique_port exhausted options and raised an error, that would be caught by the generic Exception.


def perform_cusum_analysis(df_accounting, ticker=None, feature=None): # Exactly as in the first script
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

    # Added basic check for empty signal to prevent error in detect_changepoints
    if len(signal_array) == 0:
        print(f"Warning: No data for {ticker} - {feature} in perform_cusum_analysis. Returning empty results.")
        empty_analysis_df = pd.DataFrame(columns=["Date", "Trend", "Signal_Value", "CUSUM_Score", "Duration", "Duration_Days", "Percent_Change"])
        empty_stats_df = pd.DataFrame({
            "Statistic": [
                "Ticker", "Feature", "Total_Change_Points", "Average_Duration_Days", 
                "Average_Percent_Change", "Increasing_Trends", "Decreasing_Trends", 
                "Sideways_Trends", "Max_CUSUM_Score", "Min_CUSUM_Score", "Window_Size"],
            "Value": [ticker, feature, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        })
        empty_analysis_df.attrs["stats"] = empty_stats_df
        return empty_analysis_df


    changepoints, trends, scores, window_size = detector.detect_changepoints(
        signal_array
    )
    
    # Handle case with no changepoints to avoid errors
    if len(changepoints) == 0:
        analysis_df = pd.DataFrame(columns=["Date", "Trend", "Signal_Value", "CUSUM_Score"])
    else:
        # Original script might have index out of bounds or issues if changepoints are empty or too large. Preserved.
        # CUSUM_Score indexing `changepoints - 1` could be problematic if changepoints contains 0.
        # `_calculate_two_sided_cusum` starts `i` from 1, so changepoints should be >= 1.
        # However, if warm_up_period is very large, changepoints could be empty.
        analysis_df = pd.DataFrame(
            {
                "Date": df_signal.index[changepoints],
                "Trend": trends,
                "Signal_Value": signal_array[changepoints],
                "CUSUM_Score": scores[changepoints - 1],
            }
        )

    # Calculate duration between change points
    if not analysis_df.empty:
        analysis_df["Duration"] = (
            analysis_df["Date"].diff().shift(-1).fillna(pd.Timedelta(days=0))
        )
        analysis_df["Duration_Days"] = analysis_df["Duration"].dt.days

        # Calculate percentage change between change points
        analysis_df["Percent_Change"] = (
            analysis_df["Signal_Value"].pct_change().shift(-1) * 100
        ).fillna(0)
    else: # Ensure columns exist if analysis_df is empty
        analysis_df["Duration"] = pd.Series(dtype='timedelta64[ns]')
        analysis_df["Duration_Days"] = pd.Series(dtype='int')
        analysis_df["Percent_Change"] = pd.Series(dtype='float')


    # Overall statistics
    # Original `scores[scores > 0].min()` could fail if scores[scores > 0] is empty.
    min_cusum_score_val = 0
    if any(scores > 0):
        min_positive_scores = scores[scores > 0]
        if len(min_positive_scores) > 0:
            min_cusum_score_val = min_positive_scores.min()
            
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
                "Min_CUSUM_Score", # Original name was Min_CUSUM_Score
                "Window_Size",
            ],
            "Value": [
                ticker,
                feature,
                len(changepoints),
                analysis_df["Duration_Days"].mean() if not analysis_df.empty else 0,
                analysis_df["Percent_Change"].mean() if not analysis_df.empty else 0,
                sum(trends == "Increasing") if len(trends) > 0 else 0,
                sum(trends == "Decreasing") if len(trends) > 0 else 0,
                sum(trends == "Sideways") if len(trends) > 0 else 0,
                scores.max() if len(scores) > 0 else 0,
                min_cusum_score_val,
                window_size,
            ],
        }
    )
    # Fill NaN for mean values if analysis_df was empty or had single row for stats
    overall_stats['Value'] = overall_stats['Value'].fillna(0)

    analysis_df.attrs["stats"] = overall_stats

    return analysis_df


if __name__ == "__main__":
    # Create a dummy df_accounting for demonstration as in the second script
    # This helps in testing the updated script functionality.
    dates = pd.to_datetime(pd.date_range(start="2020-01-01", periods=300, freq="B"))
    data_aapl = np.random.lognormal(mean=0.001, sigma=0.02, size=300).cumprod() * 100
    data_msft = np.random.lognormal(mean=0.0005, sigma=0.025, size=300).cumprod() * 150
    
    data_aapl[100:150] *= 1.3 
    data_aapl[200:250] *= 0.7 
    
    data_msft[50:80] *= 0.8   
    data_msft[150:200] *= 1.5 
    data_msft[250:] += 20 

    df_aapl = pd.DataFrame({"Close": data_aapl, "Volume": np.random.randint(1000, 5000, 300)}, index=dates)
    df_aapl["ticker"] = "AAPL"
    
    df_msft = pd.DataFrame({"Close": data_msft, "Volume": np.random.randint(2000, 7000, 300)}, index=dates)
    df_msft["ticker"] = "MSFT"

    # Ensure df_accounting structure matches what functions expect (MultiIndex with 'ticker', 'date')
    df_accounting_demo = pd.concat([
        df_aapl.reset_index().rename(columns={'index': 'date'}).set_index(['ticker', 'date']),
        df_msft.reset_index().rename(columns={'index': 'date'}).set_index(['ticker', 'date'])
    ])

    print("---- Running CUSUM Analysis for AAPL Close ----")
    analysis_results_aapl = perform_cusum_analysis(df_accounting_demo, ticker="AAPL", feature="Close")
    if not analysis_results_aapl.empty: # Check if DataFrame is not empty
        print(analysis_results_aapl)
        print("\nOverall Stats (AAPL Close):")
        print(analysis_results_aapl.attrs["stats"])
    else:
        print("No analysis results for AAPL Close.")


    print("\n---- Running CUSUM Analysis for MSFT Volume ----")
    analysis_results_msft_vol = perform_cusum_analysis(df_accounting_demo, ticker="MSFT", feature="Volume")
    if not analysis_results_msft_vol.empty: # Check if DataFrame is not empty
        print(analysis_results_msft_vol)
        print("\nOverall Stats (MSFT Volume):")
        print(analysis_results_msft_vol.attrs["stats"])
    else:
        print("No analysis results for MSFT Volume.")
    
    print("\n---- Launching Dashboard ----")
    print("Note: If a port is busy, the script will attempt to kill the process.")
    print("Ensure you are comfortable with this, especially if not in a dev environment.")
    
    try:
        # df_accounting_demo needs to be passed to the dashboard
        run_cusum_dashboard(df_accounting_demo, ticker="AAPL", feature="Close")
    except Exception as e:
        print(f"Dashboard launch failed: {e}")