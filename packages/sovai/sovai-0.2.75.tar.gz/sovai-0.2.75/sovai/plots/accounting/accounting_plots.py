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

import pandas as pd
import plotly.express as px

import random

from sovai.utils.port_manager import get_unique_port


def get_balance_sheet_tree_plot_for_ticker(df_accounting=None, ticker="MSFT"):
    # Assuming df_accounting is your DataFrame
    if df_accounting is None:
        df_accounting = data("accounting/weekly", tickers=ticker)

    selected_data = df_accounting.iloc[-1]

    selected_data["other_current_assets"] = max(
        0,
        selected_data["current_assets"]
        - selected_data["cash_equiv_usd"]
        - selected_data["accounts_receivable"]
        - selected_data["inventory_amount"]
        - selected_data["tax_assets"]
        - selected_data["current_investments"],
    )

    selected_data["other_non_current_assets"] = max(
        0,
        selected_data["non_current_assets"]
        - selected_data["property_plant_equipment_net"]
        - selected_data["non_current_investments"]
        - selected_data["intangible_assets"],
    )

    selected_data["other_non_current_liabilities"] = max(
        0, selected_data["non_current_liabilities"] - selected_data["non_current_debt"]
    )

    selected_data["other_current_liabilities"] = max(
        0,
        selected_data["current_liabilities"]
        - selected_data["current_debt"]
        - selected_data["deferred_revenue"]
        - selected_data["tax_liabilities"]
        - selected_data["accounts_payable"]
        - selected_data["bank_deposits"],
    )

    # Prepare the data for Plotly Express with hierarchical relationships
    data_for_plot = [
        # Assets
        {
            "level_1": "Total Assets",
            "level_2": "Current Assets",
            "level_3": "Cash and Equivalents",
            "value": selected_data["cash_equiv_usd"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Current Assets",
            "level_3": "Accounts Receivable",
            "value": selected_data["accounts_receivable"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Current Assets",
            "level_3": "Inventory",
            "value": selected_data["inventory_amount"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Current Assets",
            "level_3": "Tax Asset",
            "value": selected_data["tax_assets"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Current Assets",
            "level_3": "Current Investment",
            "value": selected_data["current_investments"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Current Assets",
            "level_3": "Other Current Assets",
            "value": selected_data["other_current_assets"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Non-Current Assets",
            "level_3": "Property, Plant & Equipment",
            "value": selected_data["property_plant_equipment_net"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Non-Current Assets",
            "level_3": "Non-Current Investments",
            "value": selected_data["non_current_investments"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Non-Current Assets",
            "level_3": "Intangible Assets",
            "value": selected_data["intangible_assets"],
        },
        {
            "level_1": "Total Assets",
            "level_2": "Non-Current Assets",
            "level_3": "Other Non-Current Assets",
            "value": selected_data["other_non_current_assets"],
        },
        # Liabilities & Equity
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Total Equity",
            "level_3": "Total Equity",
            "value": selected_data["equity_usd"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Non-Current Liabilities",
            "level_3": "Non-Current Portion of Total Debt",
            "value": selected_data["non_current_debt"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Non-Current Liabilities",
            "level_3": "Other Non-Current Liabilities",
            "value": selected_data["other_non_current_liabilities"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Current Liabilities",
            "level_3": "Current Debt",
            "value": selected_data["current_debt"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Current Liabilities",
            "level_3": "Deferred Revenue",
            "value": selected_data["deferred_revenue"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Current Liabilities",
            "level_3": "Tax Liabilities",
            "value": selected_data["tax_liabilities"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Current Liabilities",
            "level_3": "Accounts Payable",
            "value": selected_data["accounts_payable"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Current Liabilities",
            "level_3": "Bank Deposits",
            "value": selected_data["bank_deposits"],
        },
        {
            "level_1": "Total Liabilities & Equity",
            "level_2": "Current Liabilities",
            "level_3": "Other Current Liabilities",
            "value": selected_data["other_current_liabilities"],
        },
    ]

    df_for_plot = pd.DataFrame(data_for_plot)

    # Creating the treemap
    fig = px.treemap(
        df_for_plot,
        path=["level_1", "level_2", "level_3"],
        values="value",
        color="level_3",
    )

    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}M",
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f} Million",
    )

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    fig.update_layout(title="Balance Sheet Treemap for Selected Date")

    return fig.show()


def plot_cash_flows(df_accounting):
    import dash
    from dash import dcc, html, Input, Output, State
    import plotly.graph_objects as go
    import pandas as pd

    # Initialize the Dash app with a dark theme
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            "https://codepen.io/chriddyp/pen/bWLwgP.css",
            "https://gist.githubusercontent.com/firmai/5527685f1844845f2cb7bd72b59cac76/raw/f1b7015483fb0c8ea7cb5b1fc6ed0e6cf1a5e6da/dropdown.css",
        ],
    )

    # Custom styles for a dark theme
    dark_theme_style = {
        "backgroundColor": "#1e1e1e",
        "color": "#ffffff",
        "padding": "10px",
        "borderRadius": "5px",
        "textAlign": "center",  # Center text in buttons
        "lineHeight": "2",  # Center vertically
    }

    # Custom style for reducing padding and margins
    compact_layout_style = {"padding": "5px", "margin": "5px"}

    # Custom CSS for dark theme dropdown
    dropdown_dark_theme_css = {
        "color": "#fff",
        "backgroundColor": "#333",
        "borderColor": "#555",
    }

    # App layout with updated styling and checkboxes for cash flow categories
    app.layout = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[
                            {"label": ticker, "value": ticker}
                            for ticker in df_accounting.index.get_level_values(
                                "ticker"
                            ).unique()
                        ],
                        value=["AMZN"],  # Default value
                        multi=True,
                        style={"width": "100%", "marginBottom": "10px"},
                    )
                ],
                style={"width": "100%", "marginBottom": "10px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Button(
                                "Show All Cash Flows",
                                id="show-all-btn",
                                n_clicks=0,
                                style={**dark_theme_style, "marginBottom": "10px"},
                            ),
                            dcc.Checklist(
                                id="cash-flow-categories",
                                options=[
                                    {
                                        "label": "Net Cash Flow Operating",
                                        "value": "net_cash_flow_operating",
                                    },
                                    {
                                        "label": "Net Cash Flow Investing",
                                        "value": "net_cash_flow_investing",
                                    },
                                    {
                                        "label": "Net Cash Flow Financing",
                                        "value": "net_cash_flow_financing",
                                    },
                                ],
                                value=[
                                    "net_cash_flow_operating",
                                    "net_cash_flow_investing",
                                    "net_cash_flow_financing",
                                ],
                                style={
                                    "color": "#fff",
                                    "display": "flex",
                                    "flexDirection": "column",
                                },
                            ),
                        ],
                        style={
                            "width": "15%",
                            "display": "inline-block",
                            "verticalAlign": "top",
                            "marginRight": "10px",
                        },
                    ),
                    dcc.Graph(
                        id="cash-flow-graph",
                        style={
                            "width": "84%",
                            "display": "inline-block",
                            "backgroundColor": "#1e1e1e",
                            "margin": "0",
                        },
                    ),
                ],
                style={**compact_layout_style, "display": "flex"},
            ),
        ],
        style={"backgroundColor": "#1e1e1e", "padding": "5px"},
    )

    # Callback for updating the graph with checkboxes for cash flow categories
    @app.callback(
        Output("cash-flow-graph", "figure"),
        [
            Input("ticker-dropdown", "value"),
            Input("show-all-btn", "n_clicks"),
            Input("cash-flow-categories", "value"),
        ],
        State("cash-flow-graph", "figure"),
    )
    def update_graph(
        selected_tickers, show_all_clicks, selected_categories, existing_figure
    ):
        fig = go.Figure()

        for ticker in selected_tickers:
            filtered_df = (
                df_accounting.xs(ticker, level="ticker")[
                    [category for category in selected_categories]
                ]
                / 13
            )

            # Adding total net cash flow and highlighting it for each ticker
            fig.add_trace(
                go.Waterfall(
                    name=f"{ticker} Total",
                    measure=["relative"] * len(filtered_df),
                    x=filtered_df.index,
                    y=filtered_df.sum(axis=1),
                    textposition="outside",
                    totals=dict(marker=dict(color="red")),
                )
            )

            # Adding traces for selected cash flow categories for each ticker
            for category in selected_categories:
                fig.add_trace(
                    go.Waterfall(
                        name=f"{ticker} {category}",
                        measure=["relative"] * len(filtered_df),
                        x=filtered_df.index,
                        y=filtered_df[category],
                        textposition="outside",
                        visible="legendonly",
                    )
                )

        # Updating layout for readability
        fig.update_layout(
            title=f'{" & ".join(selected_tickers)} Cumulative Cash Flow',
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            waterfallgroupgap=0.5,
            showlegend=True,
            margin=dict(
                l=0, r=20, t=40, b=20
            ),  # Adjust the margins (left, right, top, bottom)
            height=500,  # Set a fixed height for the graph
        )

        # Determine which button was last clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            button_id = "No clicks yet"
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        fig.update_layout(
            plot_bgcolor="#1e1e1e", paper_bgcolor="#1e1e1e", font=dict(color="white")
        )

        return fig

    # Example usage
    app_name = "cummulative_cash"

    return app.run(
        debug=False, port=get_unique_port(app_name)
    )  # Use a different port for each app


def plot_assets(df_accounting):
    import dash
    import dash_bootstrap_components as dbc
    from dash import dcc, html, Input, Output
    import plotly.graph_objects as go
    import pandas as pd

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    # Resample the data correctly
    df_accounting_res = df_accounting.groupby('ticker').resample('M', level='date').last().reset_index()

    dropdown_dark_theme_css = {
        "color": "#000",
        "borderColor": "#555",
    }

    tickersa = df_accounting_res['ticker'].unique()

    app.layout = html.Div([
        html.Div([
            dcc.Dropdown(
                id="ticker-dropdown",
                options=[{"label": ticker, "value": ticker} for ticker in tickersa],
                value=tickersa[0],
                multi=True,
                style={"width": "40%", "display": "inline-block", "marginRight": "0%", **dropdown_dark_theme_css},
            ),
            dcc.Dropdown(
                id="asset-dropdown",
                options=[{"label": asset, "value": asset} for asset in [
                    "non_current_assets", "property_plant_equipment_net", "non_current_investments",
                    "intangible_assets", "current_assets", "tax_assets", "cash_equiv_usd", "inventory_amount"
                ]],
                value=["current_assets", "non_current_assets"],
                multi=True,
                style={"width": "45%", "display": "inline-block", "marginRight": "0%", **dropdown_dark_theme_css},
            ),
            dcc.RadioItems(
                id="plot-type",
                options=[
                    {"label": "Stacked Bar Plot", "value": "bar"},
                    {"label": "Line Plot", "value": "line"},
                ],
                value="bar",
                style={"width": "10%", "display": "inline-block"},
            ),
        ]),
        html.Div(id="graphs-container"),
    ])

    @app.callback(
        Output("graphs-container", "children"),
        [Input("ticker-dropdown", "value"),
         Input("asset-dropdown", "value"),
         Input("plot-type", "value")]
    )
    def update_graph(selected_tickers, selected_assets, plot_type):
        if not isinstance(selected_tickers, list):
            selected_tickers = [selected_tickers]
        
        graphs = []
        for ticker in selected_tickers:
            ticker_data = df_accounting_res[df_accounting_res['ticker'] == ticker]
            fig = go.Figure()
            if plot_type == "bar":
                for asset_type in selected_assets:
                    fig.add_trace(go.Bar(x=ticker_data['date'], y=ticker_data[asset_type], name=asset_type))
                fig.update_layout(barmode="stack")
            elif plot_type == "line":
                for asset_type in selected_assets:
                    fig.add_trace(go.Scatter(x=ticker_data['date'], y=ticker_data[asset_type], 
                                             mode="lines+markers", name=asset_type,
                                             line=dict(shape="spline", width=2),
                                             marker=dict(size=5)))
            fig.update_layout(
                title=f"{ticker} Asset Trends Over Time",
                xaxis_title="Date",
                yaxis_title="Asset Value (USD)",
                yaxis_type="linear",
                legend_title="Asset Type",
                paper_bgcolor="#1e1e1e",
                plot_bgcolor="#1e1e1e",
                font=dict(color="white"),
            )
            graphs.append(dcc.Graph(figure=fig))
            graphs.append(html.Div(style={"borderBottom": "2px solid #ddd", "margin": "20px 0"}))
        return graphs

    app_name = "assets"
    return app.run(debug=True, port=get_unique_port(app_name))