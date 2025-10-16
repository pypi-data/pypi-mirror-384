from sovai import data
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from scipy.signal import savgol_filter
import numpy as np
import random

from sovai.utils.port_manager import get_unique_port


def plotting_corp_risk_line(df):
    # Create the Dash app
    app = dash.Dash(
        __name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    )

    # Set the app layout
    app.layout = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[
                            {"label": i, "value": i}
                            for i in df.index.get_level_values("ticker").unique()
                        ],
                        value="TSLA",
                    )
                ],
                style={"width": "20%", "display": "inline-block"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6("Lookback", style={"margin-bottom": "0px"}),
                                    html.P(
                                        "Window length for Savitzky-Golay filter",
                                        style={"fontSize": "12px", "margin-top": "0px"},
                                    ),
                                ],
                                style={"text-align": "center"},
                            ),
                            dcc.Slider(
                                id="lookback-slider",
                                min=5,
                                max=31,
                                value=5,
                                marks={
                                    str(year): str(year) for year in range(5, 32, 2)
                                },
                                step=None,
                            ),
                        ],
                        style={
                            "width": "45%",
                            "display": "inline-block",
                            "vertical-align": "middle",
                        },
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6("Order", style={"margin-bottom": "0px"}),
                                    html.P(
                                        "Polynomial order for Savitzky-Golay filter",
                                        style={"fontSize": "12px", "margin-top": "0px"},
                                    ),
                                ],
                                style={"text-align": "center"},
                            ),
                            dcc.Slider(
                                id="order-slider",
                                min=2,
                                max=5,
                                value=3,
                                marks={str(order): str(order) for order in range(2, 6)},
                                step=None,
                            ),
                        ],
                        style={
                            "width": "45%",
                            "display": "inline-block",
                            "padding-left": "20px",
                            "vertical-align": "middle",
                        },
                    ),
                ],
                style={
                    "width": "70%",
                    "display": "inline-block",
                    "padding-left": "50px",
                },
            ),
            dcc.Graph(id="risks-graph"),
        ],
        style={"backgroundColor": "#111111", "color": "#7FDBFF", "padding": "20px"},
    )

    # Update the graph based on the selected ticker, lookback, and order
    @app.callback(
        Output("risks-graph", "figure"),
        Input("ticker-dropdown", "value"),
        Input("lookback-slider", "value"),
        Input("order-slider", "value"),
    )
    def update_graph(selected_ticker, lookback, order):
        filtered_df = (
            df.query("ticker == @selected_ticker").reset_index().set_index("date")
        )

        # Apply Savitzky-Golay filter based on the lookback and order
        filtered_df["accounting_ind_adjs_filtered"] = savgol_filter(
            filtered_df["accounting_ind_adjs"], lookback, order
        )
        filtered_df["misstatement_ind_adjs_filtered"] = savgol_filter(
            filtered_df["misstatement_ind_adjs"], lookback, order
        )
        filtered_df["events_ind_adjs_filtered"] = savgol_filter(
            filtered_df["events_ind_adjs"], lookback, order
        )
        filtered_df["risk_ind_adjs_filtered"] = savgol_filter(
            filtered_df["risk_ind_adjs"], lookback, order
        )

        # Resample df_price to calculate log price for the selected ticker
        df_price = (
            data("market/prices", tickers=selected_ticker)
            .reset_index()
            .set_index("date")
            .resample("W-FRI")["closeadj"]
            .last()
        )
        df_price_log = np.log(df_price)

        # Merge filtered_df with df_price_log
        df_merged = pd.merge(
            filtered_df,
            df_price_log.rename("log_price").to_frame(),
            left_index=True,
            right_index=True,
            how="left",
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_merged.index,
                y=df_merged["risk_ind_adjs_filtered"],
                name="Overall Risk",
                line=dict(width=4),
                yaxis="y1",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_merged.index,
                y=df_merged["accounting_ind_adjs_filtered"],
                name="Accounting Risk",
                opacity=0.5,
                yaxis="y1",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_merged.index,
                y=df_merged["misstatement_ind_adjs_filtered"],
                name="Misstatement Risk",
                opacity=0.5,
                yaxis="y1",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_merged.index,
                y=df_merged["events_ind_adjs_filtered"],
                name="Events Risk",
                opacity=0.5,
                yaxis="y1",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_merged.index,
                y=df_merged["log_price"],
                name="Log Price",
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Risks and Log Price",
            xaxis_title="Date",
            yaxis=dict(
                title="Risk Scores",
                titlefont=dict(color="#7FDBFF"),
                tickfont=dict(color="#7FDBFF"),
            ),
            yaxis2=dict(
                title="Log Price",
                titlefont=dict(color="red"),
                tickfont=dict(color="red"),
                overlaying="y",
                side="right",
            ),
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font=dict(color="#7FDBFF"),
            hovermode="x unified",
            legend=dict(
                traceorder="normal",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=0.9,  # Adjust this value to move the legend to the right
            ),
        )

        return fig

    app_name = "corporate_risk"
    return app.run(debug=False, port=get_unique_port(app_name))
