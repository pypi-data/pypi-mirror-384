import pandas as pd
from datetime import timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import time
import numpy as np
from sovai import data
import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
import sys
import os
import pandas as pd
import plotly.express as px
from sovai.utils.port_manager import get_unique_port


import pandas as pd
from scipy.signal import savgol_filter
from functools import cache
import pandas as pd
import plotly.express as px
from scipy.signal import savgol_filter
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State


# Assume 'df' is your original DataFrame


def analyze_institutional_flows(df_accf, df_institute, pred_or_pressure):
    """
    Analyze institutional flows weighted by individual stock factor values.

    Parameters:
    - df_accf: DataFrame containing accounting factors data
    - df_institute: DataFrame containing institutional trading data

    Returns:
    - result: DataFrame with the weighted factor values
    """
    # Select relevant columns from the institutional trading data and calculate the mean
    if pred_or_pressure == "pressure":
        df_inst = df_institute[
            [
                "growth_shrholders",
                "growth_percentoftotal",
                "quarter_flows",
                "net_flows_sum",
                "net_flows_mean",
                "overweight",
            ]
        ].mean(axis=1)
    else:
        df_prediction = data("institutional/flow_prediction", full_history=True)
        df_inst = df_prediction["flow_prediction"]

    # Resample the accounting factors data to quarterly frequency and select the last value within each quarter
    df_accf = df_accf.groupby("ticker").resample("Q", level="date").last()

    # Multiply the institutional flows with the factor values of individual stocks
    result = df_accf.mul(df_inst, axis=0)

    # Calculate the rank percentile of the weighted factor values along the ticker axis
    result = result.rank(axis=1, pct=True)

    # Reset the index, drop the 'ticker' column, group by 'date', and calculate the median value
    result = result.reset_index().drop(columns=["ticker"]).groupby("date").median()

    # Drop any rows with missing values, calculate rank percentile along both axes
    result = (
        result.dropna(axis=0, how="any")
        .rank(axis=1, pct=True)
        .rank(axis=0, pct=True)
        .rank(axis=1, pct=True)
    )

    # Plot the resulting DataFrame as a bar chart

    return result


def process_for_express(df):
    # Melt the DataFrame to convert it to long format
    df_melted = pd.melt(
        df, id_vars=["date"], var_name="factors", value_name="percentile_rank"
    )

    # Calculate the smoothed rank using the Savitzky-Golay filter
    window_length = 5
    polyorder = 2
    df_melted["smoothed_rank"] = df_melted.groupby("factors")[
        "percentile_rank"
    ].transform(lambda x: savgol_filter(x, window_length, polyorder))

    # Reset the index
    df_melted.reset_index(drop=True, inplace=True)
    return df_melted


@cache
def factors_for_plot(pred_or_pressure="pressure"):
    df_institute = data("institutional/trading", full_history=True)
    df_accf = data("factors/accounting", full_history=True)
    df = analyze_institutional_flows(
        df_accf, df_institute, pred_or_pressure
    ).reset_index()
    df = process_for_express(df)
    return df


def institutional_flows_plot():
    tickers_meta = pd.read_parquet("data/tickers.parq")[
        [
            "ticker",
            "sector",
            "industry",
            "class",
            "active",
            "foreign",
            "scalemarketcap",
            "scalerevenue",
            "category",
        ]
    ].dropna(subset=["ticker"])

    df_institute = data("institutional/trading", full_history=True)
    df_institute = pd.merge(
        df_institute[
            [
                "growth_shrholders",
                "growth_percentoftotal",
                "quarter_flows",
                "net_flows_sum",
                "net_flows_mean",
                "overweight",
            ]
        ].reset_index(),
        tickers_meta,
        on="ticker",
        how="left",
    ).set_index(["ticker", "date"])

    df_prediction = data("institutional/flow_prediction", full_history=True)
    df_prediction = pd.merge(
        df_prediction.reset_index(), tickers_meta, on="ticker", how="left"
    ).set_index(["ticker", "date"])

    # Create the Dash app
    app = Dash(__name__)

    values = [
        "sector",
        "class",
        "active",
        "foreign",
        "scalemarketcap",
        "scalerevenue",
        "factors",
    ]
    labels = [
        "sector",
        "class",
        "active",
        "foreign",
        "scalemarketcap",
        "scalerevenue",
        "factors (2 mins first run!)",
    ]

    # Define the layout
    app.layout = html.Div(
        [
            # html.H3('Sector Data Over Time', style={'color': 'white'}),
            html.Div(
                [
                    dcc.Dropdown(
                        id="characteristic-dropdown",
                        options=[
                            {"label": label, "value": col}
                            for label, col in zip(labels, values)
                        ],
                        value="sector",
                        style={"width": "220px", "marginRight": "40px"},
                    ),
                    dcc.RadioItems(
                        id="plot-type-stacked",
                        options=[
                            {"label": "Line Plot", "value": "line"},
                            {"label": "Stacked Bar Plot", "value": "bar"},
                        ],
                        value="line",
                        labelStyle={
                            "display": "inline-block",
                            "marginRight": "10px",
                            "color": "white",
                        },
                        style={"marginRight": "30px"},
                    ),
                    dcc.RadioItems(
                        id="plot-type-pred",
                        options=[
                            {"label": "Prediction Flow", "value": "prediction"},
                            {"label": "Pressure Flow", "value": "pressure"},
                        ],
                        value="prediction",
                        labelStyle={
                            "display": "inline-block",
                            "marginRight": "10px",
                            "color": "white",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "0px",
                },
            ),
            html.Div(
                [
                    dcc.Loading(
                        id="loading-1",
                        type="default",  # Choose from 'graph', 'cube', 'circle', 'dot', or 'default'
                        fullscreen=False,  # Loading spinner appears only on the graph
                        children=[
                            dcc.Graph(id="plot"),
                        ],
                        style={
                            "backgroundColor": "black"
                        },  # Set background color to black
                    )
                ],
                style={"marginTop": "20px"},
            ),
            # dcc.Graph(id='plot'),
            dcc.Store(id="factors-first-time", data=True, storage_type="local"),
            dcc.ConfirmDialog(
                id="confirm-dialog",
                message="Processing the factor data will download 1GB of data and take approximately 60 seconds. Do you want to proceed?",
            ),
        ],
        style={"backgroundColor": "#212121", "padding": "20px", "borderRadius": "15px"},
    )

    # Callback to update the plot based on user selections

    def pred_pressure_search(pred_or_pressure, characteristic):
        if pred_or_pressure == "pressure":
            df = (
                df_institute.reset_index()
                .drop(columns=["ticker"])
                .groupby([characteristic, "date"])
                .mean(numeric_only=True)
                .mean(axis=1)
                .reset_index()
            )
            df["percentile_rank"] = df.groupby("date")[0].rank(pct=True)

        else:
            df = (
                df_prediction.reset_index()
                .drop(columns=["ticker"])
                .groupby([characteristic, "date"])
                .mean(numeric_only=True)
                .mean(axis=1)
                .reset_index()
            )
            df["percentile_rank"] = df.groupby("date")[0].rank(pct=True)
        return df

    @app.callback(
        [Output("confirm-dialog", "displayed"), Output("factors-first-time", "data")],
        [Input("characteristic-dropdown", "value")],
        [State("factors-first-time", "data")],
    )
    def show_confirm_dialog(characteristic, factors_first_time):
        if characteristic == "factors" and factors_first_time:
            return True, False
        return False, factors_first_time

    @app.callback(
        Output("plot", "figure"),
        [
            Input("characteristic-dropdown", "value"),
            Input("plot-type-stacked", "value"),
            Input("plot-type-pred", "value"),
        ],
    )
    def update_plot(characteristic, plot_type, pred_or_pressure):
        if characteristic == "factors":
            df = factors_for_plot(pred_or_pressure)

        else:

            df = pred_pressure_search(pred_or_pressure, characteristic)
            # Apply Savitzky-Golay filter for smoothing
            window_length = 5
            polyorder = 2
            df["smoothed_rank"] = df.groupby(characteristic)[
                "percentile_rank"
            ].transform(lambda x: savgol_filter(x, window_length, polyorder))

        if plot_type == "line":
            fig = px.line(
                df,
                x="date",
                y="smoothed_rank",
                color=characteristic,
                title=f"{characteristic.capitalize()} Data Over Time (Smoothed)",
                labels={
                    "date": "Date",
                    "smoothed_rank": "Smoothed Value",
                    characteristic: characteristic.capitalize(),
                },
                hover_name=characteristic,
            )
        else:
            fig = px.bar(
                df,
                x="date",
                y="smoothed_rank",
                color=characteristic,
                title=f"{characteristic.capitalize()} Data Over Time (Smoothed)",
                labels={
                    "date": "Date",
                    "smoothed_rank": "Smoothed Value",
                    characteristic: characteristic.capitalize(),
                },
                hover_name=characteristic,
            )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Smoothed Value",
            legend_title=characteristic.capitalize(),
            font=dict(size=12, color="white"),
            title_font=dict(size=16, color="white"),
            hoverlabel=dict(font_size=14),
            height=500,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.4, xanchor="right", x=1
            ),
            plot_bgcolor="#212121",
            paper_bgcolor="#212121",
        )

        fig.update_traces(
            opacity=0.8, hovertemplate="Date: %{x}<br>Smoothed Value: %{y:.2f}<br>"
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#3c4f6d", color="white")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#3c4f6d", color="white")

        return fig

    # @app.long_callback(
    #     Output('factors-first-time', 'data'),
    #     Input('characteristic-dropdown', 'value'),
    #     prevent_initial_call=True
    # )
    # def run_long_task(start):
    #     factors_for_plot("pressure")

    return app.run(
        debug=False, port=get_unique_port( "institutional_flows")
    )  # Apply exponential moving average to smooth the data


import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def institutional_flow_predictions_plot():
    app = dash.Dash(__name__)

    # Load the tickers metadata
    df_prediction = data("institutional/flow_prediction", full_history=True)

    tickers_meta = pd.read_parquet("data/tickers.parq")[
        ["ticker", "sector", "industry", "scalemarketcap", "scalerevenue", "category"]
    ].dropna(subset=["ticker"])
    tickers_meta = tickers_meta[~tickers_meta["category"].isin(["ETF"])]
    # Assuming df_prediction is your DataFrame with predictions and tickers_meta is the DataFrame with tickers
    # Convert the tickers in tickers_meta to a set
    tickers_set = set(tickers_meta["ticker"])

    # Get the set of tickers from the index of df_prediction
    prediction_tickers_set = set(df_prediction.reset_index()["ticker"])

    # Find the overlap of tickers present in both sets
    overlap_tickers = tickers_set.intersection(prediction_tickers_set)

    # Create options for the dropdown from the overlap tickers
    options = [{"label": ticker, "value": ticker} for ticker in overlap_tickers]

    app.layout = html.Div(
        [
            # html.H3('Flow Dashboard', className='text-center text-white'),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="ticker-dropdown",
                                options=options,
                                value="AAPL",
                                style={
                                    "backgroundColor": "#f8f9fa",  # Light gray background
                                    "color": "#495057",  # Darker text color for better contrast
                                    "width": "100%",  # Full width of the container
                                    "borderRadius": "15px",  # Rounded borders
                                },
                            )
                        ],
                        style={
                            "display": "inline-block",
                            "verticalAlign": "top",
                            "width": "48%",
                            "marginTop": "20",
                        },
                    ),
                    html.Div(
                        [
                            dcc.Slider(
                                id="smoothing-factor-slider",
                                min=0.1,
                                max=1.0,
                                step=0.1,
                                value=0.5,
                                marks={i / 10: str(i / 10) for i in range(1, 11)},
                                className="bg-dark",
                            )
                        ],
                        style={
                            "display": "inline-block",
                            "verticalAlign": "top",
                            "width": "48%",
                            "marginLeft": "4%",
                        },
                    ),
                ],
                style={"textAlign": "center", "marginTop": "20px"},
            ),
            html.Div(
                [
                    dcc.Loading(
                        id="loading-1",
                        type="default",  # Choose from 'graph', 'cube', 'circle', 'dot', or 'default'
                        fullscreen=False,  # Loading spinner appears only on the graph
                        children=[
                            dcc.Graph(
                                id="stock-graph",
                                style={"backgroundColor": "#1a1a1a", "width": "100%"},
                            )
                        ],
                        style={
                            "backgroundColor": "black"
                        },  # Set background color to black
                    )
                ],
                style={"marginTop": "20px"},
            ),
        ],
        className="container",
        style={
            "backgroundColor": "#212121",
            "color": "white",
            "borderRadius": "7px",
            "padding": "10px",
        },
    )

    @app.callback(
        Output("stock-graph", "figure"),
        [Input("ticker-dropdown", "value"), Input("smoothing-factor-slider", "value")],
        [State("stock-graph", "figure")],  # Add the current state of the graph
    )
    def update_graph(selected_ticker, smoothing_factor, current_figure):
        try:
            filtered_df = df_prediction.loc[[selected_ticker]]

            # Apply exponential moving average to smooth the data
            filtered_df = filtered_df.reset_index()
            filtered_df["flow_prediction_smooth"] = (
                filtered_df["flow_prediction"].ewm(alpha=smoothing_factor).mean()
            )

            fig = px.line(
                filtered_df,
                x="date",
                y="flow_prediction_smooth",
                color="ticker",
                title="Institutional Flow Prediction",
                labels={
                    "flow_prediction_smooth": "Flow Prediction",
                    "ticker": "Flow Prediction:",
                },
            )
            # Add price series to the secondary y-axis
            price_df = data("market/prices", tickers=[selected_ticker]).reset_index()
            fig.add_trace(
                go.Scatter(
                    x=price_df["date"],
                    y=price_df["closeadj"],
                    name=f"{selected_ticker} Stock Price",
                    yaxis="y2",
                )
            )

            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Predicted Flows",
                yaxis2=dict(title="Price", overlaying="y", side="right"),
                margin=dict(l=50, r=50, t=50, b=50),
                legend=dict(x=0.35, y=1.15, orientation="h"),
                # name = "Flow Prediction",
                plot_bgcolor="#212121",
                paper_bgcolor="#212121",
                font=dict(color="white"),
            )

            # Update the x-axis range
            fig.update_xaxes(
                range=[filtered_df["date"].min(), filtered_df["date"].max()]
            )

            return fig
        except Exception as e:
            print(f"An error occurred: {e}")
            # Return the previous state of the graph in case of an error
            return current_figure

    stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")

    return app.run(
        debug=False, port=get_unique_port("institutional_predictions")
    )  # Apply exponential moving average to smooth the data
