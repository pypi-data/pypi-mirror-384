import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sovai import data
import random

from sovai.utils.port_manager import get_unique_port


def create_earnings_surprise_plot():
    df_earn = data("earnings/surprise")


    def calculate_slope(data):
        x = np.arange(len(data))
        slope, _ = np.polyfit(x, data, 1)
        return slope

    def create_figure(df_company, df_price, ticker):
        df_company['rolling_slope'] = df_company['surprise_probability'].rolling(window=13).apply(calculate_slope)
        min_slope = df_company['rolling_slope'].min()
        max_slope = df_company['rolling_slope'].max()
        df_company['scaled_slope'] = np.interp(df_company['rolling_slope'], (min_slope, max_slope), (-0.5, 0.5))

        fig = go.Figure()

        # Earnings data
        fig.add_trace(go.Scatter(x=df_company.index, y=df_company['surprise_probability'], name='Predicted Surprise Probability', line=dict(color='#00FFFF', width=2)))
        fig.add_trace(go.Scatter(x=df_company.index, y=df_company['eps_surprise'], name='Real EPS Surprise', line=dict(color='#FF69B4', width=2)))
        fig.add_trace(go.Scatter(x=df_company.index, y=df_company['scaled_slope'], name='Surprise Probability Rolling Slope (13-period, Scaled)', line=dict(color='#d62728', width=1)))

        # Stock price data
        fig.add_trace(go.Scatter(x=df_price['date'], y=df_price['closeadj'], name='Stock Price', yaxis='y2', line=dict(color='#90EE90', width=2)))

        earnings_range = max(
            abs(df_company['surprise_probability'].min()),
            abs(df_company['surprise_probability'].max()),
            abs(df_company['eps_surprise'].min()),
            abs(df_company['eps_surprise'].max())
        )

        fig.update_layout(
            title=dict(text=f'{ticker}: Earnings Surprise and Stock Price', font=dict(size=20, color='white')),
            xaxis=dict(
                title='Date', 
                gridcolor='#2c2c2c', 
                showgrid=True, 
                linecolor='white', 
                tickfont=dict(color='white'),
                range=[df_company.index.min(), df_company.index.max()]  # Set x-axis range based on earnings data
            ),
            yaxis=dict(
                title='Earnings Metrics',
                range=[-earnings_range, earnings_range],
                gridcolor='#2c2c2c',
                showgrid=True,
                linecolor='white',
                tickfont=dict(color='white')
            ),
            yaxis2=dict(
                title='Stock Price',
                overlaying='y',
                side='right',
                gridcolor='#2c2c2c',
                showgrid=False,
                linecolor='white',
                tickfont=dict(color='white')
            ),
            plot_bgcolor='#1c1c1c',
            paper_bgcolor='#1c1c1c',
            legend=dict(
                x=0.5,
                y=-0.2,
                orientation='h',
                xanchor='center',
                font=dict(color='white'),
                bgcolor='#1c1c1c',
                bordercolor='white',
                borderwidth=1
            ),
            hovermode='x unified',
            hoverlabel=dict(font=dict(color='white'), bgcolor='#1c1c1c')
        )

        return fig
    
    app = dash.Dash(__name__)
    app.layout = html.Div([
        dcc.Dropdown(
            id='ticker-dropdown',
            options=[{'label': ticker, 'value': ticker} for ticker in df_earn.index.get_level_values('ticker').unique()],
            value='ADBE',  # Default value
            style={'width': '50%', 'margin': '10px auto'}
        ),
        dcc.Graph(id='stock-graph')
    ])

    @app.callback(
        Output('stock-graph', 'figure'),
        Input('ticker-dropdown', 'value')
    )
    def update_graph(selected_ticker):
        df_earn_full = data("earnings/surprise", tickers=[selected_ticker], full_history=True)
        df_company = df_earn_full.reset_index().set_index("date").query("ticker == @selected_ticker")
        price_df = data("market/prices", tickers=[selected_ticker]).reset_index()
        return create_figure(df_company, price_df, selected_ticker)


    app_name = "earning_surprise_plot"
    return app.run(
        debug=False, port=get_unique_port(app_name)
    )  # Apply exponential moving average to smooth the data


import plotly.express as px
import pandas as pd
import numpy as np

def earnings_tree():
    df_earn = data("earnings/surprise")
    df_earn = df_earn.merge_data("market_cap")
    # Ensure 'ticker' is a column, not an index
    if 'ticker' not in df_earn.columns:
        df_earn = df_earn.reset_index()
    
    df_earn['market_cap'] = df_earn['market_cap'].replace(0, 1e-6)
    # Calculate market cap deciles and handle NaN values
    df_earn['market_cap_decile'] = pd.qcut(df_earn['market_cap'].rank(method='first'), q=10, labels=range(1, 11))
    df_earn['market_cap_decile'] = df_earn['market_cap_decile'].astype(str).replace('nan', 'Unknown')
    
    # Update decile labels
    df_earn['market_cap_decile'] = df_earn['market_cap_decile'].apply(lambda x: f"{x} Cap Decile" if x != 'Unknown' else x)
    
    
    # Create the main treemap
    fig = px.treemap(
        df_earn,
        path=[px.Constant("All"), 'market_cap_decile', "ticker"],
        values="market_cap",
        color="surprise_probability",
        color_continuous_scale="RdYlBu",
        color_continuous_midpoint=0,
        hover_data=["surprise_probability", "market_cap", "date"],
        title="Earnings Surprise Probability and Market Cap Treemap",
    )
    
    # Update layout for better appearance
    fig.update_layout(
        font=dict(family="Arial", size=14),
        title=dict(font=dict(size=20, color="lightgrey")),
        coloraxis_colorbar=dict(
            title="Surprise Probability",
            tickformat=".2%",
            len=0.75,
            thickness=20,
            title_font=dict(size=16),
            tickfont=dict(size=14),
        ),
        height=900,
        # width=1200,
        # plot_bgcolor='rgba(240,240,240,0.8)',
        # paper_bgcolor='rgba(240,240,240,0.8)',
        margin=dict(t=50, l=25, r=25, b=25),
    )
    
    # Update traces for better text visibility and style
    fig.update_traces(
        textposition="middle center",
        textfont=dict(family="Arial", size=12, color="black"),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Date: %{customdata[2]}<br>"
            "Surprise Probability: %{customdata[0]:.2%}<br>"
            "Market Cap: $%{customdata[1]:,.0f}M"
            "<extra></extra>"
        ),
        marker=dict(
            cornerradius=5,
            line=dict(width=1, color="white"),
        ),
    )
    
    # Show the plot
    fig

    return fig