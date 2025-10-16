import pandas as pd
import plotly.express as px
import ipywidgets as widgets
from ipywidgets import interact
from sovai import data


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import random
from scipy.optimize import minimize
from scipy import stats
from sovai.utils.port_manager import get_unique_port


import pandas as pd
import numpy as np

import random


import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np



# Global dictionary to keep track of apps and their ports
app_ports = {}



def create_plot_news_sent_price(ticker, variable, df_price, df_news):
    # Resample df_price to calculate weekly returns for the selected ticker
    df_price_weekly = (
        df_price.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")
        .resample("W-FRI")["closeadj"]
        .last()
        .pct_change()
    )

    # Resample df_news to align with weekly frequency for the selected ticker
    df_news_weekly = (
        df_news.query(f"ticker == '{ticker}'")
        .reset_index()
        .set_index("date")
        .resample("W-FRI")[["relevance", "sentiment", "polarity", "tone"]]
        .last()
    )

    # Merge df_price_weekly with df_news_weekly
    df_merged = pd.merge(
        df_news_weekly,
        df_price_weekly.rename("returns"),
        left_index=True,
        right_index=True,
        how="left",
    )

    fig = px.line(
        df_merged.reset_index(),
        x="date",
        y=[variable, "returns"],
        labels={"variable": "Variable", "value": "Value", "date": "Date"},
        title=f"{variable.capitalize()} and Weekly Returns for {ticker}",
    )

    # Set the y-axis for the selected variable on the left
    fig.update_traces(yaxis="y1", selector=dict(name=variable))

    # Set the y-axis for returns on the right
    fig.update_traces(yaxis="y2", selector=dict(name="returns"))

    # Configure the y-axes
    fig.update_layout(
        yaxis=dict(
            title=variable.capitalize(),
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue"),
        ),
        yaxis2=dict(
            title="Weekly Returns",
            titlefont=dict(color="red"),
            tickfont=dict(color="red"),
            overlaying="y",
            side="right",
        ),
        legend=dict(
            title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )

    return fig


def plot_above_sentiment_returns(df_news=None, tickers=None):
    if df_news is None:
        if tickers is None:
            print("Downloading default tickers, use tickers=[...] to select your own")
            df_news = data(
                "news/daily",
                tickers=["MSFT", "TSLA", "AAPL", "META"],
                start_date="2017-03-30",
            )
        else:
            df_news = data("news/daily", tickers=tickers, start_date="2017-03-30")
    else:
        df_news = df_news.copy()

    unique_tickers = df_news.index.get_level_values("ticker").unique().tolist()
    df_price = data("market/prices", tickers=unique_tickers, start_date="2017-03-30")

    # Get the unique set of tickers from both DataFrames
    tickers = sorted(
        set(df_price.index.get_level_values("ticker")).intersection(
            df_news.index.get_level_values("ticker")
        )
    )

    # Create dropdown widgets
    ticker_dropdown = widgets.Dropdown(
        options=tickers, value=tickers[0], description="Ticker:"
    )

    variable_dropdown = widgets.Dropdown(
        options=["relevance", "sentiment", "polarity", "tone"],
        value="tone",
        description="Variable:",
    )

    # Use the interact function to update the plot based on the dropdown selections
    @interact(ticker=ticker_dropdown, variable=variable_dropdown)
    def update_plot(ticker, variable):
        fig = create_plot_news_sent_price(ticker, variable, df_price, df_news)
        fig.show()


# from statsmodels.tsa.stattools import adfuller, coint
# from statsmodels.tsa.vector_ar.vecm import VECM

def fetch_and_prepare_data(ticker, variables):
    # Fetch news data
    df_news = data("news/daily", tickers=[ticker])
    df_news.index = df_news.index.set_levels(
        pd.to_datetime(df_news.index.levels[1]).date,
        level=1
    )
    
    # Fetch price data
    df_price = data("market/prices", tickers=[ticker])
    df_price.index = df_price.index.set_levels(
        pd.to_datetime(df_price.index.levels[1]).date,
        level=1
    )
    
    # Merge news and price data
    df_merged = pd.merge(df_news[variables], 
                         df_price[['closeadj']], 
                         left_index=True, right_index=True, how='left')
    df_merged = df_merged.ffill().dropna().reset_index(level='date')
    
    return df_merged


def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    excess_returns = returns - risk_free_rate/252  # Assuming daily data
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_max_drawdown(returns):
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.cummax()
    drawdown = (cum_returns - running_max) / running_max
    return drawdown.min()

def calculate_strategy_performance(df, column, long_ma, short_ma, threshold, future_days, transaction_cost=0.001):
    df_plot = df.copy()
    df_plot[f'{column}_ma_long'] = df_plot[column].rolling(window=long_ma).mean()
    df_plot[f'{column}_ma_short'] = df_plot[column].rolling(window=short_ma).mean()
    df_plot['crossover'] = np.where(
        (df_plot[f'{column}_ma_short'] > df_plot[f'{column}_ma_long'] * (1 + threshold)) & 
        (df_plot[f'{column}_ma_short'].shift(1) <= df_plot[f'{column}_ma_long'].shift(1) * (1 + threshold)),
        'golden',
        np.where(
            (df_plot[f'{column}_ma_short'] < df_plot[f'{column}_ma_long'] * (1 - threshold)) & 
            (df_plot[f'{column}_ma_short'].shift(1) >= df_plot[f'{column}_ma_long'].shift(1) * (1 - threshold)),
            'death',
            'none'
        )
    )
    df_plot['future_return'] = df_plot['closeadj'].pct_change(periods=future_days).shift(-future_days)
    df_plot['strategy_return'] = np.where(df_plot['crossover'] == 'golden', df_plot['future_return'] - transaction_cost,
                                          np.where(df_plot['crossover'] == 'death', -df_plot['future_return'] - transaction_cost, 0))
    
    strategy_returns = df_plot['strategy_return'].dropna()
    buy_hold_returns = df_plot['closeadj'].pct_change().dropna()
    
    strategy_sharpe = calculate_sharpe_ratio(strategy_returns)
    buy_hold_sharpe = calculate_sharpe_ratio(buy_hold_returns)
    
    strategy_drawdown = calculate_max_drawdown(strategy_returns)
    buy_hold_drawdown = calculate_max_drawdown(buy_hold_returns)
    
    t_stat, p_value = stats.ttest_ind(strategy_returns, buy_hold_returns)
    
    return {
        'strategy_returns': strategy_returns,
        'buy_hold_returns': buy_hold_returns,
        'strategy_sharpe': strategy_sharpe,
        'buy_hold_sharpe': buy_hold_sharpe,
        'strategy_drawdown': strategy_drawdown,
        'buy_hold_drawdown': buy_hold_drawdown,
        't_stat': t_stat,
        'p_value': p_value
    }

def calculate_accuracy(df, column, long_ma, short_ma, threshold, future_days):
    df_plot = df.copy()
    df_plot[f'{column}_ma_long'] = df_plot[column].rolling(window=long_ma).mean()
    df_plot[f'{column}_ma_short'] = df_plot[column].rolling(window=short_ma).mean()
    df_plot['crossover'] = np.where(
        (df_plot[f'{column}_ma_short'] > df_plot[f'{column}_ma_long'] * (1 + threshold)) & 
        (df_plot[f'{column}_ma_short'].shift(1) <= df_plot[f'{column}_ma_long'].shift(1) * (1 + threshold)),
        'golden',
        np.where(
            (df_plot[f'{column}_ma_short'] < df_plot[f'{column}_ma_long'] * (1 - threshold)) & 
            (df_plot[f'{column}_ma_short'].shift(1) >= df_plot[f'{column}_ma_long'].shift(1) * (1 - threshold)),
            'death',
            'none'
        )
    )
    df_plot['future_return'] = df_plot['closeadj'].pct_change(periods=future_days).shift(-future_days)
    df_plot['correct_prediction'] = np.where(
        (df_plot['crossover'] == 'golden') & (df_plot['future_return'] > 0) |
        (df_plot['crossover'] == 'death') & (df_plot['future_return'] < 0),
        1, 0
    )
    df_signals = df_plot[df_plot['crossover'] != 'none'].dropna(subset=['future_return'])
    total_signals = df_signals.shape[0]
    correct_predictions = df_signals['correct_prediction'].sum()
    return correct_predictions / total_signals if total_signals > 0 else 0

def optimize_parameters(df, column):
    def objective(params):
        long_ma, short_ma, threshold, future_days = params
        # Round parameters to nearest allowed values
        long_ma = round(long_ma / 10) * 10
        short_ma = round(short_ma / 10) * 10
        threshold = round(threshold * 10) / 10
        future_days = round(future_days / 10) * 10
        return -calculate_accuracy(df, column, int(long_ma), int(short_ma), threshold, int(future_days))

    best_accuracy = 0
    best_params = None

    # Random search
    for _ in range(50):
        long_ma = random.choice(range(60, 301, 10))  # 60 to 300, step 10
        short_ma = random.choice(range(10, 61, 10))  # 10 to 60, step 10
        threshold = random.choice([0, 0.1, 0.2, 0.3, 0.4, 0.5])  # 0% to 50%, step 10%
        future_days = random.choice(range(10, 61, 10))  # 10 to 60, step 10

        accuracy = calculate_accuracy(df, column, long_ma, short_ma, threshold, future_days)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_params = (long_ma, short_ma, threshold, future_days)

    # Custom bounds for scipy.optimize.minimize
    bounds = [(60, 300), (10, 60), (0, 0.5), (10, 60)]

    # Custom constraint to ensure parameters are multiples of 10 (except threshold)
    def custom_constraint(params):
        return [params[0] % 10, params[1] % 10, params[3] % 10]

    constraint = {'type': 'eq', 'fun': custom_constraint}

    # Local optimization
    result = minimize(objective, best_params, method='SLSQP', bounds=bounds, constraints=[constraint])
    optimized_params = result.x

    # Round the optimized parameters to the nearest allowed values
    optimized_long_ma = round(optimized_params[0] / 10) * 10
    optimized_short_ma = round(optimized_params[1] / 10) * 10
    optimized_threshold = round(optimized_params[2] * 10) / 10
    optimized_future_days = round(optimized_params[3] / 10) * 10

    optimized_accuracy = -result.fun

    if optimized_accuracy > best_accuracy:
        return (int(optimized_long_ma), int(optimized_short_ma), optimized_threshold, int(optimized_future_days))
    else:
        return best_params
        
def create_plot(df, ticker, column, long_ma, short_ma, threshold, future_days):
    
    # Create a copy of the dataframe to avoid modifying the original
    df_plot = df.copy()

    # Calculate moving averages of the selected column
    df_plot[f'{column}_ma_long'] = df_plot[column].rolling(window=long_ma).mean()
    df_plot[f'{column}_ma_short'] = df_plot[column].rolling(window=short_ma).mean()

    # Calculate logarithm of stock price
    df_plot['log_price'] = np.log(df_plot['closeadj'])

    # Identify crossover points with threshold
    df_plot['crossover'] = np.where(
        (df_plot[f'{column}_ma_short'] > df_plot[f'{column}_ma_long'] * (1 + threshold)) & 
        (df_plot[f'{column}_ma_short'].shift(1) <= df_plot[f'{column}_ma_long'].shift(1) * (1 + threshold)),
        'golden',
        np.where(
            (df_plot[f'{column}_ma_short'] < df_plot[f'{column}_ma_long'] * (1 - threshold)) & 
            (df_plot[f'{column}_ma_short'].shift(1) >= df_plot[f'{column}_ma_long'].shift(1) * (1 - threshold)),
            'death',
            'none'
        )
    )

    # Calculate future returns
    df_plot['future_return'] = df_plot['closeadj'].pct_change(periods=future_days).shift(-future_days)

    # Calculate accuracy
    df_plot['correct_prediction'] = np.where(
        (df_plot['crossover'] == 'golden') & (df_plot['future_return'] > 0) |
        (df_plot['crossover'] == 'death') & (df_plot['future_return'] < 0),
        1, 0
    )

    # Filter out rows with NaN future returns (due to shifting)
    df_signals = df_plot[df_plot['crossover'] != 'none'].dropna(subset=['future_return'])

    total_signals = df_signals.shape[0]
    correct_predictions = df_signals['correct_prediction'].sum()
    accuracy = correct_predictions / total_signals if total_signals > 0 else 0

    # Create the plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add log of stock price
    fig.add_trace(
        go.Scatter(x=df_plot['date'], y=df_plot['log_price'], name="Log Stock Price"),
        secondary_y=False,
    )

    # Add long-term moving average
    fig.add_trace(
        go.Scatter(x=df_plot['date'], y=df_plot[f'{column}_ma_long'], name=f"{column.capitalize()} MA{long_ma}", line=dict(color='blue')),
        secondary_y=True,
    )

    # Add short-term moving average
    fig.add_trace(
        go.Scatter(x=df_plot['date'], y=df_plot[f'{column}_ma_short'], name=f"{column.capitalize()} MA{short_ma}", line=dict(color='orange')),
        secondary_y=True,
    )

    # Add markers for trading opportunities with future returns
    for idx, row in df_signals.iterrows():
        color = 'green' if row['future_return'] > 0 else 'red'
        symbol = 'triangle-up' if row['crossover'] == 'golden' else 'triangle-down'
        
        # Calculate the y-position for the return annotation
        y_pos = max(row[f'{column}_ma_short'], row[f'{column}_ma_long']) + 0.02
        
        fig.add_trace(
            go.Scatter(
                x=[row['date']], 
                y=[y_pos],
                mode='markers+text',
                marker=dict(symbol=symbol, size=10, color=color),
                text=[f"{row['future_return']:.2%}"],
                textposition="top center",
                name='Signal',
                showlegend=False,
                hoverinfo='text',
                hovertext=f"Date: {row['date']}<br>Signal: {'Enter' if row['crossover'] == 'golden' else 'Exit'}<br>Future Return: {row['future_return']:.2%}"
            ),
            secondary_y=True
        )
        
        # Add a line to connect the crossover point to the future price
        future_date = row['date'] + pd.Timedelta(days=future_days)
        future_log_price = df_plot.loc[df_plot['date'] == future_date, 'log_price'].values[0] if future_date in df_plot['date'].values else None
        
        if future_log_price is not None:
            fig.add_trace(
                go.Scatter(
                    x=[row['date'], future_date],
                    y=[row['log_price'], future_log_price],
                    mode='lines',
                    line=dict(color=color, width=1, dash='dot'),
                    showlegend=False
                ),
                secondary_y=False
            )

    # Update layout
    fig.update_layout(
        title=f"Trading Opportunities for {ticker} based on {column.capitalize()} MA Crossovers",
        xaxis_title="Date",
        yaxis_title="Log Stock Price",
        yaxis2_title=f"{column.capitalize()} MA",
        legend_title="Legend",
        hovermode="closest",
        template="plotly_dark",
        height=800,
        paper_bgcolor='rgba(0,0,0,1)',
        plot_bgcolor='rgba(0,0,0,1)',
        font=dict(color='white'),
    )

    # Add accuracy annotation
    fig.add_annotation(
        xref="paper", yref="paper",
        x=1.10, y=0.8,
        text=f"Accuracy: {accuracy:.2%}<br>Total Signals: {total_signals}",
        showarrow=False,
        font=dict(size=14, color="white"),
        align="right",
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="white",
        borderwidth=2,
    )

    performance = calculate_strategy_performance(df, column, long_ma, short_ma, threshold, future_days)
    
    # Add performance metrics to the plot
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.80, y=0.95,  # Adjusted y-coordinate to be below the legend
        text=f"Strategy Max Drawdown: {performance['strategy_drawdown']:.2%}<br>"
             f"Buy & Hold Max Drawdown: {performance['buy_hold_drawdown']:.2%}<br>"
             f"T-Statistic: {performance['t_stat']:.2f}<br>"
             f"P-Value: {performance['p_value']:.4f}",
        showarrow=False,
        font=dict(size=12, color="white"),
        align="left",
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="white",
        borderwidth=2,
    )


    # Create the strategy explanation using Dash components
    strategy_explanation = html.Div([
        html.H3("Trading Strategy Explanation"),
        html.P(f"This strategy uses a moving average crossover system based on the {column} of news sentiment for {ticker}."),
        html.Ul([
            html.Li(f"Long-term MA: {long_ma} days"),
            html.Li(f"Short-term MA: {short_ma} days"),
            html.Li(f"Threshold: {threshold:.2f}"),
            html.Li(f"Future Days: {future_days}")
        ]),
        html.P([
            html.Strong("Buy Signal (Golden Cross):"), 
            f" When the {short_ma}-day MA crosses above the {long_ma}-day MA by more than {threshold:.0%}, it generates a buy signal. This indicates a potential uptrend in sentiment that might precede a price increase."
        ]),
        html.P([
            html.Strong("Sell Signal (Death Cross):"), 
            f" When the {short_ma}-day MA crosses below the {long_ma}-day MA by more than {threshold:.0%}, it generates a sell signal. This indicates a potential downtrend in sentiment that might precede a price decrease."
        ]),
        html.P(f"The strategy then looks {future_days} days into the future to evaluate its performance. Green triangles indicate profitable trades, while red triangles indicate unprofitable ones."),
        html.P(html.Em("Note: This is a hypothetical strategy for educational purposes. Always conduct thorough research before making investment decisions."))
    ], style={'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.5)', 'padding': '15px', 'border': '2px solid white'})

    return fig, strategy_explanation

def plot_news_daily(ticker='NVDA'):
    # Fetch and prepare data

    print(ticker)
    df = fetch_and_prepare_data(ticker, ['tone', 'sentiment'])

    # Initialize the Dash app
    app = dash.Dash(__name__)

    # Define the layout with dark mode styles
    app.layout = html.Div([
        html.Div([
            html.Div([
                html.Label("Column:", style={'color': 'white'}),
                dcc.Dropdown(
                    id='column-dropdown',
                    options=[{'label': col, 'value': col} for col in df.columns if col not in ['date', 'closeadj']],
                    value='sentiment',
                    style={'color': 'black'}
                ),
            ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
            html.Div([
                html.Label("Long MA:", style={'color': 'white'}),
                dcc.Slider(id='long-ma-slider', min=60, max=300, step=30, value=120, marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(60, 301, 60)}),
            ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
            html.Div([
                html.Label("Short MA:", style={'color': 'white'}),
                dcc.Slider(id='short-ma-slider', min=5, max=60, step=5, value=30, marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(5, 61, 10)}),
            ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
            html.Div([
                html.Label("Threshold:", style={'color': 'white'}),
                dcc.Slider(id='threshold-slider', min=0, max=0.5, step=0.05, value=0.1, marks={i/10: {'label': str(i/10), 'style': {'color': 'white'}} for i in range(0, 6)}),
            ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
        ]),
        html.Div([
            html.Div([
                html.Label("Future Days:", style={'color': 'white'}),
                dcc.Slider(id='future-days-slider', min=5, max=60, step=5, value=30, marks={i: {'label': str(i), 'style': {'color': 'white'}} for i in range(5, 61, 10)}),
            ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
        ]),
        html.Div([
            html.Button('Update Plot', id='update-button', n_clicks=0, style={'fontSize': '18px', 'marginTop': '20px', 'backgroundColor': '#4CAF50', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'cursor': 'pointer'}),
            html.Button('Optimize Parameters', id='optimize-button', n_clicks=0, style={'fontSize': '18px', 'marginTop': '20px', 'marginLeft': '20px', 'backgroundColor': '#008CBA', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'cursor': 'pointer'}),
        ], style={'textAlign': 'center'}),
        dcc.Graph(id='trading-opportunities-plot'),
        html.Div(id='strategy-explanation', style={'marginTop': '20px'})
    ], style={'backgroundColor': 'black', 'padding': '20px'})

    # Define the callback to update the plot
    @app.callback(
        [Output('trading-opportunities-plot', 'figure'),
         Output('strategy-explanation', 'children'),
         Output('long-ma-slider', 'value'),
         Output('short-ma-slider', 'value'),
         Output('threshold-slider', 'value'),
         Output('future-days-slider', 'value')],
        [Input('update-button', 'n_clicks'),
         Input('optimize-button', 'n_clicks')],
        [State('column-dropdown', 'value'),
         State('long-ma-slider', 'value'),
         State('short-ma-slider', 'value'),
         State('threshold-slider', 'value'),
         State('future-days-slider', 'value')]
    )
    def update_plot(update_clicks, optimize_clicks, column, long_ma, short_ma, threshold, future_days):
        ctx = dash.callback_context
        if not ctx.triggered:
            optimal_long_ma, optimal_short_ma, optimal_threshold, optimal_future_days = optimize_parameters(df, column)
            fig, explanation = create_plot(df, ticker, column, optimal_long_ma, optimal_short_ma, optimal_threshold, optimal_future_days)
            return fig, explanation, optimal_long_ma, optimal_short_ma, optimal_threshold, optimal_future_days
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'optimize-button':
            optimal_long_ma, optimal_short_ma, optimal_threshold, optimal_future_days = optimize_parameters(df, column)
            fig, explanation = create_plot(df, ticker, column, optimal_long_ma, optimal_short_ma, optimal_threshold, optimal_future_days)
            return fig, explanation, optimal_long_ma, optimal_short_ma, optimal_threshold, optimal_future_days
        else:
            fig, explanation = create_plot(df, ticker, column, long_ma, short_ma, threshold, future_days)
            return fig, explanation, long_ma, short_ma, threshold, future_days

    # Run the app
    app.run(debug=False, port=get_unique_port("news_daily_sentiment"), jupyter_mode="inline", jupyter_height=1100)

# Usage example:
# plot_news_daily(ticker='AAPL')



def dash_news_ts_analysis(df_sentiment, df_polarity, df_topic):
    # Dynamically get all topics from df_sentiment
    all_topics = [col for col in df_sentiment.columns if col not in ['date', 'calculation']]

    # Default topics (10 most relevant from an investor's perspective)
    default_topics = [
        'economic_growth', 'inflation', 'interest_rates', 'financial_markets_investing',
        'monetary_policy', 'fiscal_policy', 'market_sentiment', 'geopolitical_events',
        'technology_innovation', 'commodities_markets'
    ]

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    app.layout = html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Data Selection", className="card-title"),
                            dcc.Dropdown(
                                id='dataframe-dropdown',
                                options=[
                                    {'label': 'Sentiment Analysis', 'value': 'sentiment'},
                                    {'label': 'Topic Polarity', 'value': 'polarity'},
                                    {'label': 'Topic Probability', 'value': 'topic'}
                                ],
                                value='sentiment',
                                clearable=False,
                                className="mb-3",
                                style={'color': 'black'}
                            ),
                            dcc.Dropdown(
                                id='calculation-dropdown',
                                clearable=False,
                                className="mb-3",
                                style={'color': 'black'}
                            ),
                            dcc.Dropdown(
                                id='topic-dropdown',
                                options=[{'label': topic.replace('_', ' ').title(), 'value': topic} for topic in all_topics],
                                value=default_topics,
                                multi=True,
                                className="mb-3",
                                style={'color': 'black'}
                            ),
                            html.Div([
                                html.Label("Rolling Window Size (days)", className="mr-2"),
                                dcc.Slider(
                                    id='rolling-window-slider',
                                    min=1,
                                    max=30,
                                    step=1,
                                    value=15,
                                    marks={i: str(i) for i in range(0, 31, 5)},
                                    className="mb-3"
                                )
                            ]),
                            dbc.Switch(
                                id='relative-switch',
                                label='Relative Calculation',
                                value=False,
                                className="mb-3"
                            ),
                            dbc.Tooltip(
                                "Tracks numerical values relative to the average across other values at that time",
                                target="relative-switch",
                            ),
                        ])
                    ], style={'height': '600px'})
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Time Series Analysis", className="card-title"),
                            dcc.Graph(id='time-series-graph', style={'height': '550px'})
                        ])
                    ], style={'height': '600px'})
                ], md=9)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Key Statistics", className="card-title"),
                            html.Div(id='summary-stats')
                        ])
                    ], style={'height': '500px'})
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Correlation Heatmap", className="card-title"),
                            dcc.Graph(id='correlation-heatmap', style={'height': '550px'})
                        ])
                    ], style={'height': '500px'})
                ], md=6)
            ])
        ], fluid=True)
    ], style={'width': '100%', 'height': '1200px', 'margin': '0', 'padding': '0'})

    @app.callback(
        Output('calculation-dropdown', 'options'),
        Output('calculation-dropdown', 'value'),
        Input('dataframe-dropdown', 'value')
    )
    def update_calculation_dropdown(selected_df):
        if selected_df == 'sentiment':
            df = df_sentiment
        elif selected_df == 'polarity':
            df = df_polarity
        else:
            df = df_topic
        
        calculations = df['calculation'].unique()
        options = [{'label': calc.replace('_', ' ').title(), 'value': calc} for calc in calculations]
        return options, calculations[0]

    @app.callback(
        Output('time-series-graph', 'figure'),
        Output('summary-stats', 'children'),
        Output('correlation-heatmap', 'figure'),
        Input('dataframe-dropdown', 'value'),
        Input('calculation-dropdown', 'value'),
        Input('topic-dropdown', 'value'),
        Input('relative-switch', 'value'),
        Input('rolling-window-slider', 'value')
    )
    def update_dashboard(selected_df, selected_calc, selected_topics, relative_calc, rolling_window):
        if selected_df == 'sentiment':
            df = df_sentiment.copy()
        elif selected_df == 'polarity':
            df = df_polarity.copy()
        else:
            df = df_topic.copy()
        
        df_filtered = df[df['calculation'] == selected_calc]
        df_filtered.set_index('date', inplace=True)
        df_filtered = df_filtered[selected_topics]
        
        if relative_calc:
            df_filtered = df_filtered.sub(df_filtered.mean(axis=1), axis=0)
        
        df_filtered = df_filtered.rolling(window=f'{rolling_window}D').mean()
        # Standardize around zero
        df_filtered = (df_filtered - df_filtered.mean()) / df_filtered.std()
        
        # Time Series Graph
        traces = []
        for column in df_filtered.columns:
            traces.append(go.Scatter(
                x=df_filtered.index,
                y=df_filtered[column],
                mode='lines',
                name=column.replace('_', ' ').title()
            ))
        
        time_series_fig = {
            'data': traces,
            'layout': go.Layout(
                xaxis={'title': 'Date'},
                yaxis={'title': 'Standardized Value'},
                template="plotly_dark",
                legend={'orientation': 'h', 'y': -0.2},
                margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
            )
        }
        
        # Key Statistics
        stats = []
        for column in df_filtered.columns:
            last_30d_change = ((df_filtered[column].iloc[-1] / df_filtered[column].iloc[-30]) - 1) * 100
            yoy_change = ((df_filtered[column].iloc[-1] / df_filtered[column].iloc[-365]) - 1) * 100 if len(df_filtered) >= 365 else np.nan
            max_date = df_filtered[column].idxmax()
            min_date = df_filtered[column].idxmin()
            current_value = df_filtered[column].iloc[-1]
            
            stats.append({
                'Topic': column.replace('_', ' ').title(),
                'Current Value': f"{current_value:.2f}",
                'Last 30 Days Change': f"{last_30d_change:.2f}%",
                'YoY Change': f"{yoy_change:.2f}%" if not np.isnan(yoy_change) else "N/A",
                'Highest Date': max_date.strftime('%Y-%m-%d'),
                'Lowest Date': min_date.strftime('%Y-%m-%d')
            })
        
        stats_df = pd.DataFrame(stats)
        stats_table = dbc.Table.from_dataframe(stats_df, striped=True, bordered=True, hover=True, responsive=True, className="mt-3")
        
        # Correlation Heatmap
        corr_matrix = df_filtered.corr()
        heatmap_fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmin=-1, zmax=1,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10},
        ))
        heatmap_fig.update_layout(
            xaxis={'showticklabels': False},
            yaxis={'showticklabels': False},
            template="plotly_dark",
            margin={'l': 40, 'r': 40, 't': 40, 'b': 40},
            coloraxis_showscale=False  # Remove color legend
        )
        heatmap_fig.update_traces(xgap=3, ygap=3)  # Increase gap between heatmap squares
        
        return time_series_fig, stats_table, heatmap_fig

    return app

def run_dash_news_ts():

    df_sentiment = data("news/sentiment_score", full_history=True).reset_index()
    df_polarity = data("news/polarity_score", full_history=True).reset_index()
    df_topic = data("news/topic_probability", full_history=True).reset_index()

    app = dash_news_ts_analysis(df_sentiment, df_polarity, df_topic)
    app.run(debug=False, port=get_unique_port("news_topic_valuest"), jupyter_mode="inline", jupyter_height=1300)
    