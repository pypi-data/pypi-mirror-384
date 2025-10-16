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


class LazyLoader:
    def __init__(self):
        self._medians = None

    @property
    def medians(self):
        if self._medians is None:
            self._medians = data("breakout/median", purge_cache=False)["prediction"][0]
        return self._medians


def get_predict_breakout_plot_for_ticker(msft_df=None):

    msft_df = msft_df.reset_index(drop=False)

    # Find the date 56 days before the maximum date
    cut_off_date = msft_df["date"].max() - pd.Timedelta(days=56)

    # Identify the indices of the last 56 days
    indices = msft_df[msft_df["date"] > cut_off_date].index

    # Set the 'returns' of these days to NaN
    msft_df.loc[indices, "future_returns"] = np.nan

    # Define the desired range
    min_value = 0
    max_value = 100

    # Force the values in the column to be within the range
    msft_df["standard_deviation_outsample"] = (msft_df["standard_deviation"] * 2).clip(
        min_value, max_value
    )
    msft_df["top_range"] = msft_df["top_prediction"] / 2 + msft_df["top_conformal"] / 2
    msft_df["bottom_range"] = (
        msft_df["bottom_prediction"] / 2 + msft_df["bottom_conformal"] / 2
    )

    import plotly.graph_objects as go

    msft_df = msft_df.bfill()

    msft_df["date"] = pd.to_datetime(msft_df["date"])  # convert to datetime
    msft_df["indicator_15"] = 0
    msft_df["indicator_neg_15"] = 0

    last_found_date = None

    for index, row in msft_df.iterrows():
        if row["future_returns"] > 0.15:
            if last_found_date is None or (row["date"] - last_found_date).days > 60:
                msft_df.loc[index, "indicator_15"] = 1
                last_found_date = row["date"]

    last_found_date = None

    for index, row in msft_df.iterrows():
        if row["future_returns"] < -0.15:
            if last_found_date is None or (row["date"] - last_found_date).days > 60:
                msft_df.loc[index, "indicator_neg_15"] = 1
                last_found_date = row["date"]

    # Color definition based on slope
    def color(slope):
        if slope > 0:
            return "green"
        else:
            return "red"

    fig = go.Figure()

    # Adding the standard deviation lines (replace 'std_dev' with the actual column name)

    # Adding the confidence interval (bottom and top predictions)
    fig.add_trace(
        go.Scatter(
            x=msft_df["date"],
            y=msft_df["top_range"],
            showlegend=False,
            mode="lines",
            name="High Prediction",
            line=dict(width=0),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=msft_df["date"],
            y=msft_df["bottom_range"],
            showlegend=False,
            mode="lines",
            name="Low Prediction",
            line=dict(width=0),
            fillcolor="rgba(68, 68, 68, 0.6)",
            fill="tonexty",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=msft_df["date"],
            y=msft_df["prediction"] + msft_df["standard_deviation_outsample"],
            showlegend=False,
            mode="lines",
            name="Upper Std Dev",
            line=dict(width=0),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=msft_df["date"],
            y=msft_df["prediction"] - msft_df["standard_deviation_outsample"],
            showlegend=False,
            mode="lines",
            name="Lower Std Dev",
            line=dict(width=0),
            fillcolor="rgba(0, 0, 255, 0.4)",
            fill="tonexty",
        )
    )

    # # Adding the main line (predictions) with color based on slope
    # for i in range(1, len(msft_df)):
    #     fig.add_trace(go.Scatter(x=msft_df['date'].iloc[i-1:i+1],
    #                             y=msft_df['prediction'].iloc[i-1:i+1],
    #                             showlegend=False,
    #                             mode='lines',
    #                             name='Prediction',
    #                             line=dict(color=color(msft_df['slope'].iloc[i-1]))))

    # Group the dataframe by the sign of the slope and create a cumulative sum over the groups
    msft_df["group"] = (msft_df["slope"] > 0).diff().cumsum()

    # For each group, create a single Scatter trace
    for _, group in msft_df.groupby("group"):
        slope_color = "green" if group["slope"].iloc[0] > 0 else "red"
        fig.add_trace(
            go.Scatter(
                x=group["date"],
                y=group["prediction"],
                showlegend=False,
                mode="lines",
                name="Prediction",
                line=dict(color=slope_color),
            )
        )

    fig.update_layout(
        # title_text="Predictions with Confidence Interval",
        xaxis_title="Date",
        yaxis_title="Prediction",
    )

    # get dates when indicator_15 == 1 and -1
    indicator_pos_dates = msft_df[msft_df["indicator_15"] == 1]["date"]
    indicator_neg_dates = msft_df[msft_df["indicator_neg_15"] == 1]["date"]

    # add the annotations and marker points for positive returns
    for date in indicator_pos_dates:
        random_adjustment = np.random.uniform(0, 0.1)
        fig.add_trace(
            go.Scatter(
                x=[date, date],
                y=[
                    msft_df.loc[msft_df["date"] == date, "prediction"].values[0],
                    msft_df["prediction"].max() + random_adjustment,
                ],
                mode="lines",
                line=go.scatter.Line(color="green"),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[date],
                y=[msft_df["prediction"].max() + random_adjustment],
                mode="markers",
                marker=dict(size=8, color="green"),
                showlegend=False,
                hovertemplate="The price of the stock realized more than 15% increase in the coming 60 days.",
            )
        )

        fig.add_annotation(
            dict(
                x=date,
                y=msft_df["prediction"].max() + random_adjustment + 0.08,
                text="15%",
                showarrow=False,
                textangle=-35,
                font=dict(color="grey"),
            )
        )

    # add the annotations and marker points for negative returns
    for date in indicator_neg_dates:
        random_adjustment = np.random.uniform(0, 0.1)
        fig.add_trace(
            go.Scatter(
                x=[date, date],
                y=[
                    msft_df.loc[msft_df["date"] == date, "prediction"].values[0],
                    msft_df["prediction"].min() - random_adjustment,
                ],
                mode="lines",
                line=go.scatter.Line(color="red"),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[date],
                y=[msft_df["prediction"].min() - random_adjustment],
                mode="markers",
                marker=dict(size=8, color="red"),
                showlegend=False,
                hovertemplate="The price of the stock realized more than 15% decrease in the coming 60 days.",
            )
        )

        fig.add_annotation(
            dict(
                x=date,
                y=msft_df["prediction"].min() - random_adjustment - 0.08,
                text="-15%",
                showarrow=False,
                textangle=35,  # Angle the text by 35 degrees
                font=dict(color="grey"),
            )
        )

    fig.update_layout(
        margin=dict(
            l=20, r=20, t=60, b=20
        ),  # Adjust the margins (left, right, top, bottom)
        # title_text="Predictions with Confidence Interval and 15% Return Indicators",
        xaxis_title="Date",
        yaxis_title="Prediction",
        legend=dict(
            orientation="h",  # Set the orientation to horizontal
            yanchor="bottom",  # Anchor the legend to the bottom
            y=1.12,  # Adjust the y position
            xanchor="center",  # Anchor the legend to the center
            x=0.5,  # Adjust the x position
        ),
    )

    # fig.update_layout(
    #     title_text="Predictions with Confidence Interval and 15% Return Indicators",
    #     xaxis_title="Date",
    #     yaxis_title="Prediction",
    # #   template="plotly_dark",  # Use built-in dark mode
    # )

    fig.add_trace(
        go.Scatter(
            x=[None],  # these scatter plots are not shown
            y=[None],
            mode="lines",
            line=dict(color="grey"),  # color of the line
            showlegend=True,
            name="Prediction Range",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="blue"),  # color of the line
            showlegend=True,
            name="Standard Deviation",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="green"),  # color of the line
            showlegend=True,
            name="Positive Slope",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="red"),  # color of the line
            showlegend=True,
            name="Negative Slope",
        )
    )
    fig.add_shape(
        type="line",
        x0=msft_df["date"].min(),
        x1=msft_df["date"].max(),
        y0=0.5,
        y1=0.5,
        line=dict(dash="dash", color="grey"),
    )  # 'dash' creates a dashed line

    # fig = ut.easy_update(fig, None,xaxis_title="Date")
    min_date = msft_df["date"].min() - timedelta(days=15)
    max_date = msft_df["date"].max()

    # Update the x-axis range
    fig.update_xaxes(range=[min_date, max_date])

    # fig.update_layout(
    #     template="plotly_dark",
    #     plot_bgcolor='rgba(16, 18, 31, 1)',
    #     paper_bgcolor='rgba(16, 18, 31, 1)',
    # )

    # fig.update_yaxes(range=[-0.2, 1])

    return fig


def accuracy_score(y_true, y_pred):
    """Computes the accuracy score.

    Args:
    y_true (list): List of true labels.
    y_pred (list): List of predicted labels.

    Returns:
    float: The accuracy score.
    """
    correct = 0
    for actual, pred in zip(y_true, y_pred):
        if actual == pred:
            correct += 1
    return correct / len(y_true)


# @timer_decorator
def get_rolling_accuracy_plot(df):
    df["accuracy_fill"] = df["accuracy"].where(df["accuracy"] >= 0.5, 0.5)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["accuracy"],
            mode="lines",
            line=dict(color="blue", width=2),
            name="Accuracy",
            showlegend=False,
        )
    )

    # Add a invisible trace at y=0.5
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=[0.5] * len(df),
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
        )
    )

    # Add a filled trace for the rolling accuracy above 0.5
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["accuracy"].where(df["accuracy"] >= 0.5),
            mode="none",
            fill="tonexty",
            fillcolor="rgba(50, 205, 50, 0.3)",
            showlegend=False,
        )
    )

    # Add a trace for the average accuracy with increased line width
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=[df["accuracy"].mean()] * len(df),
            mode="lines",
            name="Average",
            line=dict(dash="dash", color="limegreen", width=2),
        )
    )

    # Add a trace for the "random" line at y=0.5 for the accuracy plot with increased line width
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=[0.5] * len(df),
            mode="lines",
            name="Random Line",
            line=dict(dash="dash", color="red", width=2),
        )
    )

    fig.update_layout(
        title_text="Rolling Accuracy",
        xaxis_title="Date",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.2)",  # set grid color and transparency
            gridwidth=0.5,  # set grid line width
            zerolinecolor="rgba(255, 255, 255, 0.5)",  # set zero line color and transparency
            zerolinewidth=0.5,  # set zero line width
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.2)",  # set grid color and transparency
            gridwidth=0.5,  # set grid line width
            zerolinecolor="rgba(255, 255, 255, 0.5)",  # set zero line color and transparency
            zerolinewidth=0.5,  # set zero line width
        ),
    )

    fig.update_yaxes(title_text="Accuracy")

    # fig = ut.easy_update(fig, None,xaxis_title="Date")

    return fig


# @timer_decorator
def get_rolling_correlation_plot(df):
    df["corr_fill"] = df["rolling_corr"].where(df["rolling_corr"] > 0, 0)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rolling_corr"],
            mode="lines",
            line=dict(color="blue", width=2),
            name="Correlation",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["corr_fill"],
            mode=None,
            name=None,
            line=dict(color="blue", width=2),
            fill="tozeroy",
            fillcolor="rgba(50, 205, 50, 0.3)",
            showlegend=False,
        )
    )

    # Add a trace for the average correlation with increased line width
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=[df["rolling_corr"].mean()] * len(df),
            mode="lines",
            name="Average",
            line=dict(dash="dash", color="limegreen", width=2),
        )
    )

    # Add a trace for the "random" line at y=0 for the correlation plot with increased line width
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=[0] * len(df),
            mode="lines",
            name="Random Line",
            line=dict(dash="dash", color="red", width=2),
        )
    )

    fig.update_layout(
        title_text="Rolling Correlation",
        xaxis_title="Date",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.2)",  # set grid color and transparency
            gridwidth=0.5,  # set grid line width
            zerolinecolor="rgba(255, 255, 255, 0.5)",  # set zero line color and transparency
            zerolinewidth=0.5,  # set zero line width
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.2)",  # set grid color and transparency
            gridwidth=0.5,  # set grid line width
            zerolinecolor="rgba(255, 255, 255, 0.5)",  # set zero line color and transparency
            zerolinewidth=0.5,  # set zero line width
        ),
    )

    fig.update_yaxes(title_text="Correlation")

    # fig = ut.easy_update(fig, None,xaxis_title="Date")

    return fig


def preprocess_data_for_plots(df, window=60):
    loader = LazyLoader()
    medians = loader.medians
    df["return_binary"] = np.where(df["future_returns"] > 0, 1, 0)
    df["target_binary"] = np.where(df["prediction"] > medians, 1, 0)
    df["accuracy"] = [
        accuracy_score(
            df["target_binary"].iloc[i - window : i],
            df["return_binary"].iloc[i - window : i],
        )
        if i >= window
        else np.nan
        for i in range(len(df))
    ]
    df["rolling_corr"] = (
        df["prediction"].rolling(window=window).corr(df["future_returns"])
    )

    return df


import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np

def create_dash_app(df):
    app = dash.Dash(__name__)
    
    df = df.reset_index(drop=False)
    df = preprocess_data_for_plots(df)
    
    # Define dark theme colors
    dark_theme = {
        'background': '#111111',
        'text': '#7FDBFF'
    }
    
    app.layout = html.Div(style={'backgroundColor': dark_theme['background'], 'color': dark_theme['text']}, children=[
        dcc.Dropdown(
            id='plot-type-dropdown',
            options=[
                {'label': 'Rolling Accuracy', 'value': 'Rolling Accuracy'},
                {'label': 'Rolling Correlation', 'value': 'Rolling Correlation'}
            ],
            value='Rolling Accuracy',
            style={
                'backgroundColor': 'white',
                'color': 'black',
                'margin-bottom': '10px'  # Add some space between dropdown and graph
            }
        ),
        dcc.Graph(id='interactive-plot')
    ])
    
    @app.callback(
        Output('interactive-plot', 'figure'),
        Input('plot-type-dropdown', 'value')
    )
    def update_plot(plot_type):
        if plot_type == 'Rolling Accuracy':
            return get_rolling_accuracy_plot(df)
        else:
            return get_rolling_correlation_plot(df)
    
    return app


def interactive_plot_display_breakout_accuracy(df=None):
    # Assuming you have your DataFrame 'df' ready
    app = create_dash_app(df)

    return app.run(debug=False)


# def interactive_plot_display_breakout_accuracy(df=None):
#     df = df.reset_index(drop=False)
#     df = preprocess_data_for_plots(df)

#     dropdown = widgets.Dropdown(
#         options=["Rolling Accuracy", "Rolling Correlation"],
#         value="Rolling Accuracy",
#         description="Plot Type:",
#     )

#     def display_plot(plot_type):
#         if plot_type == "Rolling Accuracy":
#             return get_rolling_accuracy_plot(df)
#         else:
#             return get_rolling_correlation_plot(df)

#     interactive_plot = widgets.interactive_output(display_plot, {'plot_type': dropdown})
    
#     display(widgets.VBox([dropdown, interactive_plot]))
