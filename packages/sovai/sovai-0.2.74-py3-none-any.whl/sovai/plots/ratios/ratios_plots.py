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
from sovai.utils import get_tickers

import pandas as pd
import plotly.express as px

import random

from sklearn.cluster import MiniBatchKMeans

from sovai.utils.port_manager import get_unique_port

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State


import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.colors as colors
import pandas as pd
import hashlib
import json
import openai
from dash import no_update
import random
import numpy as np
from sklearn.cluster import KMeans

import pandas as pd
import numpy as np
from sovai import data


def neutralize_and_differentiate(
    df_latest, lagged_zero="0_week", lagged_one="1_quarter", characteristic="sector"
):
    # print(df_latest.head())
    df_filtered_zero = df_latest[df_latest["lagged"] == lagged_zero]
    df_filtered_one = df_latest[df_latest["lagged"] == lagged_one]

    # Get the numeric columns
    numeric_columns = df_filtered_zero.select_dtypes(include=[np.number]).columns

    # Calculate the mean values for the specified characteristic using only numeric columns
    characteristic_means = df_filtered_zero.groupby(characteristic)[
        numeric_columns
    ].mean()

    # Create new DataFrames for characteristic neutralization
    df_characteristic_neutralized_zero = df_filtered_zero.copy()
    df_characteristic_neutralized_one = df_filtered_one.copy()

    # Neutralize the numeric columns based on characteristic means for lagged_zero
    for col in numeric_columns:
        df_characteristic_neutralized_zero[col] = df_filtered_zero[
            col
        ] - df_filtered_zero[characteristic].map(characteristic_means[col])

    # Neutralize the numeric columns based on characteristic means for lagged_one
    for col in numeric_columns:
        df_characteristic_neutralized_one[col] = df_filtered_one[col] - df_filtered_one[
            characteristic
        ].map(characteristic_means[col])

    # Drop the 'date' level from the MultiIndex of both DataFrames
    df_characteristic_neutralized_zero = df_characteristic_neutralized_zero.reset_index(
        level="date", drop=True
    )
    df_characteristic_neutralized_one = df_characteristic_neutralized_one.reset_index(
        level="date", drop=True
    )

    # Calculate the difference between lagged_zero and lagged_one for numeric columns only
    df_difference = (
        df_characteristic_neutralized_zero[numeric_columns]
        - df_characteristic_neutralized_one[numeric_columns]
    )

    # Merge the non-numeric columns from df_characteristic_neutralized_zero into df_difference
    non_numeric_columns = df_characteristic_neutralized_zero.columns.difference(
        numeric_columns
    )
    df_difference = pd.concat(
        [df_difference, df_characteristic_neutralized_zero[non_numeric_columns]], axis=1
    )

    return df_characteristic_neutralized_zero.select_dtypes(
        include=[np.number]
    ), df_difference.select_dtypes(include=[np.number])


def neutralize_by_benchmark(
    df_latest, lagged_zero="0_week", lagged_one="1_quarter", n_clusters=170
):
    df_latest_zero = df_latest[df_latest["lagged"] == lagged_zero]
    df_latest_one = df_latest[df_latest["lagged"] == lagged_one]

    # Reset the index to remove the 'date' level
    df_latest_zero = df_latest_zero.reset_index(level="date", drop=True)
    df_latest_one = df_latest_one.reset_index(level="date", drop=True)

    # Get the common tickers that exist in both lagged periods
    common_tickers = df_latest_zero.index.intersection(df_latest_one.index)

    df_latest_zero = df_latest_zero.loc[common_tickers]
    df_latest_one = df_latest_one.loc[common_tickers]

    # Get the numeric columns
    numeric_columns = df_latest_zero.select_dtypes(include=[np.number]).columns

    # Create copies of df_latest_zero and df_latest_one for neutralization
    df_neutralized_zero = df_latest_zero.copy()
    df_neutralized_one = df_latest_one.copy()

    # Perform clustering based on the numeric columns of df_latest_zero
    # kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    # clusters = kmeans.fit_predict(df_latest_zero[numeric_columns])

    batch_size = 100
    mbk = MiniBatchKMeans(
        n_clusters=n_clusters,
        batch_size=batch_size,
        init_size=3 * batch_size,
        random_state=42,
    )
    clusters = mbk.fit_predict(df_latest_zero[numeric_columns].values)

    # Create a DataFrame to store the cluster assignments
    df_clusters = pd.DataFrame({"ticker": df_latest_zero.index, "cluster": clusters})

    # Create new DataFrames to store the neutralized values
    df_neutralized_values_zero = pd.DataFrame(
        index=df_neutralized_zero.index, columns=numeric_columns
    )
    df_neutralized_values_one = pd.DataFrame(
        index=df_neutralized_one.index, columns=numeric_columns
    )
    # print("already here")
    # Neutralize the numeric columns based on the cluster assignments
    for cluster in range(n_clusters):
        # Get the tickers in the current cluster
        cluster_tickers = df_clusters[df_clusters["cluster"] == cluster][
            "ticker"
        ].tolist()

        # Get the numeric values for the tickers in the current cluster
        cluster_values_zero = df_neutralized_zero.loc[cluster_tickers, numeric_columns]
        cluster_values_one = df_neutralized_one.loc[cluster_tickers, numeric_columns]

        # Calculate the cluster average values
        cluster_mean_zero = cluster_values_zero.mean()
        cluster_mean_one = cluster_values_one.mean()

        # Neutralize the numeric values for the tickers in the current cluster
        df_neutralized_values_zero.loc[cluster_tickers] = (
            cluster_values_zero - cluster_mean_zero
        )
        df_neutralized_values_one.loc[cluster_tickers] = (
            cluster_values_one - cluster_mean_one
        )

    # Update the neutralized DataFrames with the neutralized values
    df_neutralized_zero.loc[:, numeric_columns] = df_neutralized_values_zero
    df_neutralized_one.loc[:, numeric_columns] = df_neutralized_values_one

    # Calculate the difference between lagged_zero and lagged_one for numeric columns only
    df_difference = (
        df_neutralized_zero[numeric_columns] - df_neutralized_one[numeric_columns]
    )

    # Merge the non-numeric columns from df_neutralized_zero into df_difference
    non_numeric_columns = df_neutralized_zero.columns.difference(numeric_columns)
    df_difference = pd.concat(
        [df_difference, df_neutralized_zero[non_numeric_columns]], axis=1
    )

    return df_neutralized_zero[numeric_columns].astype(float), df_difference[
        numeric_columns
    ].astype(float)


def plot_ratios_benchmark():

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
    df_ratios = data("ratios/relative", frequency="summary")
    df_latest = pd.merge(
        df_ratios.reset_index(), tickers_meta, on="ticker", how="left"
    ).set_index(["ticker", "date"])

    # Initialize your Dash app
    app = dash.Dash(__name__)

    # Load the dataframes

    # Create the Dash app

    # Initialize the cache dictionary
    _query_cache = {}

    app = dash.Dash(__name__)
    app.title = "Financial Metric Dashboard"  # Adds a title to the browser tab
    app.layout = html.Div(
        style={"backgroundColor": "#1e1e1e"},
        children=[
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Ticker", style={"color": "#FFFFFF"}),
                            dcc.Dropdown(
                                id="ticker-dropdown",
                                options=[
                                    {"label": ticker, "value": ticker}
                                    for ticker in df_latest.index.get_level_values(
                                        0
                                    ).unique()
                                ],
                                value=df_latest.index.get_level_values(0).unique()[0],
                            ),
                        ],
                        style={
                            "width": "18%",
                            "display": "inline-block",
                            "padding": "10px",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("Characteristic", style={"color": "#FFFFFF"}),
                            dcc.Dropdown(
                                id="characteristic-dropdown",
                                options=[
                                    {"label": "Sector", "value": "sector"},
                                    {"label": "Industry", "value": "industry"},
                                    {"label": "AI Benchmark", "value": "ai_benchmark"},
                                ],
                                value="sector",
                            ),
                        ],
                        style={
                            "width": "18%",
                            "display": "inline-block",
                            "padding": "10px",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("Lagged One", style={"color": "#FFFFFF"}),
                            dcc.Dropdown(
                                id="lagged-one-dropdown",
                                options=[
                                    {"label": "1 Quarter", "value": "1_quarter"},
                                    {"label": "1 Year", "value": "1_year"},
                                    {"label": "5 Years", "value": "5_year"},
                                ],
                                value="1_year",
                            ),
                        ],
                        style={
                            "width": "18%",
                            "display": "inline-block",
                            "padding": "10px",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("Current/Change", style={"color": "#FFFFFF"}),
                            dcc.RadioItems(
                                id="current-change-switch",
                                options=[
                                    {"label": "Current", "value": "current"},
                                    {"label": "Change", "value": "change"},
                                ],
                                value="current",
                                style={"color": "#FFFFFF"},
                            ),
                        ],
                        style={
                            "width": "18%",
                            "display": "inline-block",
                            "padding": "10px",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H3(
                                        "Benchmark Analysis of Ratios",
                                        style={
                                            "color": "#FFFFFF",
                                            "marginBottom": "3px",
                                        },
                                    )
                                ],
                                style={"textAlign": "left", "padding": "5px 0 0 10px"},
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Analyze with AI", id="analyze-btn", n_clicks=0
                                    ),
                                    html.Button(
                                        "Remove Commentary",
                                        id="remove-btn",
                                        n_clicks=0,
                                        style={"marginLeft": "10px"},
                                    ),
                                ],
                                style={
                                    "textAlign": "left",
                                    "padding": "0 0 0 10px",
                                    "display": "flex",
                                    "alignItems": "center",
                                },
                            ),
                        ],
                        style={
                            "width": "20%",
                            "display": "inline-block",
                            "verticalAlign": "middle",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "justifyContent": "space-between",
                },
            ),
            html.Div(
                id="analyst-commentary", style={"color": "#FFFFFF", "padding": "10px"}
            ),
            dcc.Loading(
                id="loading-spinner",
                type="default",
                children=[
                    dcc.Graph(
                        id="data-plot",
                        style={"backgroundColor": "#1e1e1e", "color": "#FFFFFF"},
                    )
                ],
            ),
        ],
    )

    # Cache the dataframes based on selected characteristics and lagged one
    @app.callback(
        Output("data-plot", "figure"),
        Output("loading-spinner", "loading_state"),
        [
            Input("characteristic-dropdown", "value"),
            Input("lagged-one-dropdown", "value"),
            Input("current-change-switch", "value"),
            Input("ticker-dropdown", "value"),
        ],
    )
    def update_plot(
        characteristic, lagged_one, current_change, ticker, purge_cache=False
    ):
        # Create a cache key based on the selected characteristic and lagged_one values
        # print(characteristic, lagged_one, current_change)
        cache_key = hashlib.sha256(
            json.dumps(
                [lagged_one, characteristic, current_change], sort_keys=True
            ).encode()
        ).hexdigest()

        # Check if the data is already in the cache
        if not purge_cache and cache_key in _query_cache:
            # print("Returning cached data")
            df_neutralized, df_neutralized_difference = _query_cache[cache_key]
        else:
            # Generate the dataframes based on the selected characteristics and lagged one
            if characteristic == "ai_benchmark":
                df_neutralized, df_neutralized_difference = neutralize_by_benchmark(
                    df_latest.copy(), lagged_zero="0_week", lagged_one=lagged_one
                )
            else:
                (
                    df_neutralized,
                    df_neutralized_difference,
                ) = neutralize_and_differentiate(
                    df_latest.copy(),
                    lagged_zero="0_week",
                    lagged_one=lagged_one,
                    characteristic=characteristic,
                )
            # Cache the generated dataframes
            _query_cache[cache_key] = (df_neutralized, df_neutralized_difference)

        # Select the appropriate dataframe based on the current/change switch
        if current_change == "current":
            df = df_neutralized
        else:
            df = df_neutralized_difference

        ticker_data = df.loc[ticker].dropna().to_frame().T

        # Sort the data from largest to smallest
        sorted_data = ticker_data.iloc[0].sort_values(ascending=False)

        # Create color scales for positive and negative values
        positive_color_scale = colors.sequential.Plasma
        negative_color_scale = colors.sequential.Viridis

        # Create a list to store the colors for each bar
        bar_colors = []

        # Assign colors based on positive or negative values
        for value in sorted_data:
            if value >= 0:
                normalized_value = (
                    value / sorted_data.max() if sorted_data.max() > 0 else 0
                )
                color = colors.sample_colorscale(
                    positive_color_scale, normalized_value
                )[0]
            else:
                normalized_value = (
                    value / sorted_data.min() if sorted_data.min() < 0 else 0
                )
                color = colors.sample_colorscale(
                    negative_color_scale, normalized_value
                )[0]
            bar_colors.append(color)

        # Create the bar chart
        # print(sorted_data.head())
        fig = go.Figure(
            data=[
                go.Bar(
                    x=sorted_data.values,
                    y=sorted_data.index,
                    orientation="h",
                    marker=dict(color=bar_colors, line=dict(color="black", width=1)),
                    hovertemplate="Metric: %{y}<br>Value: %{x:.3f}<extra></extra>",
                )
            ]
        )

        # Set the chart title and axis labels
        fig.update_layout(
            title=dict(
                text=f"Ticker: {ticker} | Company Versus {characteristic.capitalize()} Mean",
                font=dict(size=24),
            ),
            xaxis_title=dict(text="Value", font=dict(size=18)),
            yaxis_title=dict(text="Metric", font=dict(size=18)),
            template="plotly_dark",
            hoverlabel=dict(font_size=16),
        )

        # Adjust the chart size and margins
        fig.update_layout(height=600, margin=dict(l=200, r=50, t=100, b=50))

        # Customize the axis tick labels
        fig.update_xaxes(tickfont=dict(size=14))
        fig.update_yaxes(tickfont=dict(size=14))

        return fig, {"is_loading": True}

    # Generate analyst commentary
    @app.callback(
        Output("analyst-commentary", "children"),
        Input("analyze-btn", "n_clicks"),
        Input("remove-btn", "n_clicks"),
        State("data-plot", "figure"),
        State("characteristic-dropdown", "value"),
        State("lagged-one-dropdown", "value"),
        State("current-change-switch", "value"),
        prevent_initial_call=True,
    )
    def generate_commentary(
        analyze_clicks, remove_clicks, fig, characteristic, lagged_one, current_change
    ):
        # Remove the commentary if the remove button is clicked
        if dash.callback_context.triggered_id == "remove-btn":
            return None

        # Generate the commentary if the analyze button is clicked
        if dash.callback_context.triggered_id == "analyze-btn":
            # Get the sorted data from the plot
            sorted_data = fig["data"][0]["y"]
            sorted_values = fig["data"][0]["x"]

            # Create a dictionary of the sorted data
            data_dict = {
                metric: value for metric, value in zip(sorted_data, sorted_values)
            }

            # Generate the analyst commentary
            commentary = generate_analyst_commentary(
                data_dict, characteristic, lagged_one, current_change
            )

            return html.Div([html.H3("Analyst Commentary"), dcc.Markdown(commentary)])

        return no_update

    def generate_analyst_commentary(
        data_dict, characteristic, lagged_one, current_change
    ):
        client = openai.OpenAI(
            api_key="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"
        )

        # Convert the data dictionary to a formatted string
        data_str = "\n".join(
            [f"{metric}: {value}" for metric, value in data_dict.items()]
        )

        characteristic_text = {
            "sector": "the difference between the stock and the sector average percentile",
            "industry": "the difference between the stock and the industry average",
            "ai_benchmark": "the difference between the stock and the AI benchmark",
        }[characteristic]

        current_change_text = {
            "current": f"All values are {characteristic_text} and are between -1 and 1. Positive values means growth with respect to benchamrk, negative means decrease. Some growth could be negative, it depends on the specifics of the metric/ratio.",
            "change": f"All values represent the change in the stock's ratio over and above its {characteristic} change over the {lagged_one} period. Positive values means growth with respect to benchamrk, negative means decrease. Some growth could be negative, it depends on the specifics of the metric/ratio.",
        }[current_change]

        messages = [
            {
                "role": "system",
                "content": "You are an extremely consice but explicit corporate benchmark analyst that displays numbers and values to highlight your point. Positive values means larger numbers than peers. Given some relative measures, provide a concise commentary discussing the company's relative difference in liquidity, capital structure, revenue growth, and profitability. This is not a ratio analysis, but benchamrk analysis. Positive values means growth with respect to benchamrk, negative means decrease. Some growth could be negative, it depends on the specifics of the metric/ratio. Highlight any notable strengths, weaknesses, or areas for improvement. Very importantly highlight the type of financial activity you are seeing there are thousands of descriptions, like growing, deep investment, relying on cash cow etc. Don't give standard feedback be very holistic showing a deep professorial and scholarly understanding of the financial relative benchmark patterns and nuances. The commentary should be written in Markdown format, with each paragraph separated by a blank line and using appropriate headers (e.g., ### for subheadings).",
            },
            {
                "role": "user",
                "content": f"Here is the financial data: \n\n{data_str}\n\n{current_change_text}\n\nProvide your commentary with numbers.",
            },
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        commentary = response.choices[0].message.content.strip()
        return commentary

    # Example usage
    app_name = "ratio_benchmark"
    return app.run(
        debug=False, port=get_unique_port(app_name)
    )  # Use a different port for each app


def plot_ratios_triple(ticker="TSLA"):
    # Assuming you have the df_percentiles dataframe loaded
    app = dash.Dash(
        __name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    )

    # Set dark mode colors
    colors = {"background": "#111111", "text": "#7FDBFF"}

    # Default factors to display
    equity_tickers = get_tickers.equity_tickers("data/tickers.parq")
    default_factors = [
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "operating_cash_flow_ratio",
        "net_working_capital_ratio",
    ]

    app.layout = html.Div(
        style={
            "backgroundColor": colors["background"],
            "color": colors["text"],
            "padding": "10px",
        },
        children=[
            # html.H6('Modern Plotly Dash Application', style={'textAlign': 'center', 'color': colors['text'], 'margin-bottom': '10px'}),
            html.Div(
                [
                    html.Label(
                        "Ticker:",
                        style={
                            "color": colors["text"],
                            "margin-right": "5px",
                            "font-size": "15px",
                        },
                    ),
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[
                            {"label": ticka, "value": ticka} for ticka in equity_tickers
                        ],
                        value=ticker,
                        style={
                            "width": "100px",
                            "display": "inline-block",
                            "font-size": "12px",
                        },
                    ),
                ],
                style={"textAlign": "center", "margin-bottom": "10px"},
            ),
            html.Div(
                [
                    html.Label(
                        "Factors:",
                        style={
                            "color": colors["text"],
                            "margin-right": "5px",
                            "font-size": "15px",
                        },
                    ),
                    dcc.Dropdown(
                        id="factor-dropdown",
                        options=[
                            {"label": factor, "value": factor}
                            for factor in data("ratios/relative", tickers=[ticker])
                            .reset_index()
                            .drop(columns=["ticker"])
                            .set_index("date")
                            .columns
                        ],
                        value=default_factors,
                        multi=True,
                        style={
                            "width": "800px",
                            "display": "inline-block",
                            "font-size": "12px",
                        },
                    ),
                ],
                style={"textAlign": "center", "margin-bottom": "10px"},
            ),
            dcc.Graph(id="plot1", style={"height": "200px"}),
            dcc.Graph(id="plot2", style={"height": "200px"}),
            dcc.Graph(id="plot3", style={"height": "130px"}),
            html.Button(
                "Print to PDF",
                id="print-button",
                n_clicks=0,
                style={"margin-top": "10px"},
            ),
            dcc.Download(id="download-pdf"),
        ],
    )

    @app.callback(
        [
            Output("plot1", "figure"),
            Output("plot2", "figure"),
            Output("plot3", "figure"),
        ],
        [
            Input("ticker-dropdown", "value"),
            Input("factor-dropdown", "value"),
            Input("plot2", "hoverData"),
        ],
    )
    def update_plots(selected_ticker, selected_factors, hover_data2):
        from sovai import data

        # Filter data based on selected ticker and factors
        filtered_data = (
            data("ratios/relative", tickers=[selected_ticker])
            .reset_index()
            .drop(columns=["ticker"])
            .set_index("date")
        )

        last_4_years = filtered_data.index.max() - pd.DateOffset(years=4)

        # Filter data to include only the last 4 years

        filtered_data = filtered_data.loc[filtered_data.index >= last_4_years]

        # Resample data to quarterly frequency
        quarterly_data = filtered_data.resample("Q").mean()

        plot1_fig = go.Figure()

        for factor in selected_factors:
            scaled_data = []
            hover_data = []
            for year, data in quarterly_data.groupby(quarterly_data.index.year):
                num_quarters = len(data)
                scaled_values = data[factor] / num_quarters
                scaled_data.extend(scaled_values)
                year_sum = scaled_values.sum()
                hover_data.extend(
                    [f"Year: {year}<br>{factor}: {year_sum:.2f}"] * num_quarters
                )

            plot1_fig.add_trace(
                go.Bar(
                    x=quarterly_data.index.strftime("%Y-Q%q"),
                    y=scaled_data,
                    name=factor,
                    text=[
                        f"Q{q}" for q in quarterly_data.index.quarter
                    ],  # Add quarter number as text
                    textposition="inside",  # Automatically position the text
                    hovertext=hover_data,
                    hoverinfo="text",
                )
            )

        plot1_fig.add_shape(
            type="line",
            xref="paper",  # Set the x-axis reference to 'paper'
            x0=0,  # Set the start of the line to the left edge of the plot
            y0=0.5,
            x1=1,  # Set the end of the line to the right edge of the plot
            y1=0.5,
            line=dict(color="white", width=1, dash="dash"),
        )

        plot1_fig.update_layout(
            title="Factor by Factor",
            xaxis_title="Quarter",
            yaxis_title="Value",
            hovermode="x unified",
            barmode="group",
            plot_bgcolor=colors["background"],
            paper_bgcolor=colors["background"],
            font=dict(color=colors["text"], size=10),
            margin=dict(l=30, r=30, t=30, b=30),
            # yaxis=dict(range=[0, 1])  # Set the y-axis range from 0 to 1
        )

        plot2_fig = go.Figure()

        # Define a color mapping for each factor

        color_map = {
            factor: px.colors.qualitative.Plotly[i]
            for i, factor in enumerate(selected_factors)
        }
        # color_map = {factor: f'rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})' for factor in selected_factors}

        for idx, quarter in enumerate(quarterly_data.index):
            for factor in selected_factors:
                plot2_fig.add_trace(
                    go.Bar(
                        x=[factor],
                        y=[quarterly_data.loc[quarter, factor]],
                        name=factor,
                        marker=dict(color=color_map[factor]),
                    )
                )

        plot2_fig.add_shape(
            type="line",
            xref="paper",  # Set the x-axis reference to 'paper'
            x0=0,  # Set the start of the line to the left edge of the plot
            y0=0.5,
            x1=1,  # Set the end of the line to the right edge of the plot
            y1=0.5,
            line=dict(color="white", width=1, dash="dash"),
        )

        plot2_fig.update_layout(
            title="Quarter by Quarter",
            xaxis_title="Factor",
            yaxis_title="Value",
            barmode="group",
            plot_bgcolor=colors["background"],
            paper_bgcolor=colors["background"],
            font=dict(color=colors["text"], size=10),
            margin=dict(l=30, r=30, t=30, b=30),
        )
        # Plot 3: Line plot of the hovering factor on the second plot
        # Plot 3: Line plot of the hovering factor on the second plot
        hovered_factor = None
        if hover_data2 is not None:
            hovered_factor = hover_data2["points"][0]["x"]

        if hovered_factor is not None:
            line_color = color_map[
                hovered_factor
            ]  # Get the color of the selected factor
            plot3_fig = go.Figure(
                data=go.Scatter(
                    x=filtered_data.index,
                    y=filtered_data[hovered_factor],
                    name=hovered_factor,
                    mode="lines",
                    line=dict(color=line_color),
                )
            )
        else:
            plot3_fig = go.Figure()

        plot3_fig.add_shape(
            type="line",
            x0=filtered_data.index.min(),
            y0=0.5,
            x1=filtered_data.index.max(),
            y1=0.5,
            line=dict(color="white", width=1, dash="dash"),
        )
        plot3_fig.update_layout(
            title=f"Factor: {hovered_factor}"
            if hovered_factor
            else "No Factor Selected",
            xaxis_title="Date",
            yaxis_title="Value",
            plot_bgcolor=colors["background"],
            paper_bgcolor=colors["background"],
            font=dict(color=colors["text"], size=10),
            margin=dict(l=30, r=30, t=40, b=10),
        )

        return plot1_fig, plot2_fig, plot3_fig

    @app.callback(
        Output("download-pdf", "data"),
        Input("print-button", "n_clicks"),
        [
            State("plot1", "figure"),
            State("plot2", "figure"),
            State("plot3", "figure"),
            State("ticker-dropdown", "value"),
            State("factor-dropdown", "value"),
        ],
        prevent_initial_call=True,
    )
    def func(
        n_clicks, plot1_fig, plot2_fig, plot3_fig, selected_ticker, selected_factors
    ):
        if n_clicks:
            # Create a new figure with three subplots
            pdf_fig = make_subplots(
                rows=3, cols=1, vertical_spacing=0.1, shared_xaxes=False
            )

            # Add the plots to the PDF figure
            pdf_fig.add_traces(
                plot1_fig["data"],
                rows=[1] * len(plot1_fig["data"]),
                cols=[1] * len(plot1_fig["data"]),
            )
            pdf_fig.add_traces(
                plot2_fig["data"],
                rows=[2] * len(plot2_fig["data"]),
                cols=[1] * len(plot2_fig["data"]),
            )
            pdf_fig.add_traces(
                plot3_fig["data"],
                rows=[3] * len(plot3_fig["data"]),
                cols=[1] * len(plot3_fig["data"]),
            )

            # Update the layout of the PDF figure
            pdf_fig.update_layout(
                title=dict(
                    text=f"Dashboard for {selected_ticker}",
                    x=0.5,
                    font=dict(size=24, color=colors["text"]),
                ),
                height=800,
                width=1200,
                showlegend=False,
                paper_bgcolor=colors["background"],
                plot_bgcolor=colors["background"],
                font=dict(color=colors["text"]),
                # showlegend=True,
                legend=dict(x=1, y=1),
                margin=dict(t=100, b=20, l=20, r=20),
                annotations=[
                    dict(
                        x=0.5,
                        y=1.01,
                        xref="paper",
                        yref="paper",
                        text=f"Factors: {', '.join(selected_factors)}",
                        showarrow=False,
                        font=dict(size=14, color=colors["text"]),
                    ),
                    dict(
                        x=0.5,
                        y=0.05,
                        xref="paper",
                        yref="paper",
                        text="Generated by SovAI",
                        showarrow=False,
                        font=dict(size=12, color=colors["text"]),
                    ),
                ],
            )

            # Save the figure as a PDF file
            pdf_path = "dashboard.pdf"
            pdf_fig.write_image(pdf_path)

            return dcc.send_file(pdf_path)

        return None

    app_name = "ratios"
    return app.run(
        debug=False, port=get_unique_port(app_name)
    )  # Use a different port for each app
