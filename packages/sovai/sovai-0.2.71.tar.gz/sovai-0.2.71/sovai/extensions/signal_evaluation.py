import numpy as np
import pandas as pd

import pandas as pd
import numpy as np
from great_tables import GT, md, html

# Assuming asset_returns, df_rebalanced, and price_changes are already defined
from IPython.display import display, HTML


def create_portfolio_holdings_fast(df_signal):
    # Convert to numpy array for faster operations
    signal_array = df_signal.values

    # Create the holdings array
    holdings_array = np.zeros_like(signal_array)

    # Set short positions (-1) where signal <= 10
    holdings_array[signal_array <= 10] = -1

    # Set long positions (1) where signal >= 90
    holdings_array[signal_array >= 90] = 1

    # Set NaNs where signal is NaN
    holdings_array[np.isnan(signal_array)] = np.nan

    # Convert back to DataFrame
    df_holdings = pd.DataFrame(
        holdings_array, index=df_signal.index, columns=df_signal.columns
    )

    return df_holdings


def evaluator_construct(df_signal, df_prices):
    # Create the portfolio holdings DataFrame
    df_holdings = create_portfolio_holdings_fast(df_signal)

    # Replace NaNs with 2 (our temporary placeholder)
    df_temp = df_holdings.fillna(2)

    # Create a 4-weekly rebalancing mask
    rebalance_mask = pd.Series(False, index=df_temp.index)
    rebalance_mask.iloc[0] = True  # Always include the first row
    rebalance_mask.iloc[4::4] = True  # Then every 4th row

    # Apply the rebalancing mask
    df_balance = df_temp.where(rebalance_mask, np.nan)

    # Forward fill
    df_balance = df_balance.ffill()

    # Replace 2 with NaN to restore original NaN structure
    df_balance = df_balance.replace(2, np.nan)

    df_balance = df_balance.replace(0, np.nan)

    # Assuming df_rebalanced and df_prices are already defined

    # Calculate percentage changes in prices
    df_returns = df_prices.pct_change(fill_method=None)

    df_returns = df_returns.clip(upper=3)

    # Calculate returns for each asset based on holdings
    asset_returns = df_balance * df_returns

    # Calculate portfolio returns (sum across all assets for each date)
    portfolio_returns = asset_returns.mean(axis=1)

    # Calculate cumulative returns
    cumulative_returns = (1 + portfolio_returns).cumprod()

    ## 4 WEEKLY BASED RESAMPLING

    # Assuming df_returns is your DataFrame with weekly returns
    # and rebalance_mask is your Series with the rebalancing mask

    # Create a custom resampler
    def custom_resampler(x):
        return x.sum()

    # Ensure the index of df_returns is datetime
    df_returns.index = pd.to_datetime(df_returns.index)
    # Create a date range index for resampling, explicitly using Friday end dates
    date_range = pd.date_range(
        start=df_returns.index.min(), end=df_returns.index.max(), freq="W-FRI"
    )
    # Reindex df_returns to ensure all Friday-ending weeks are present
    df_returns_full = df_returns.reindex(date_range)
    # Reindex rebalance_mask to match the Friday-ending weeks
    rebalance_mask_full = rebalance_mask.reindex(date_range)
    # Create a Series with incrementing group numbers
    group_numbers = (rebalance_mask_full.cumsum() - 1).ffill()
    # Group by the incremented numbers and apply the custom resampler
    resampled_returns = df_returns_full.groupby(group_numbers).apply(custom_resampler)
    # The resulting resampled_returns will contain the 4-week returns
    resampled_returns.index = rebalance_mask[rebalance_mask == True].index

    asset_returns = df_balance * df_returns

    return (
        df_balance,
        df_returns,
        asset_returns,
        portfolio_returns,
        cumulative_returns,
        resampled_returns,
        rebalance_mask,
    )


def calculate_stats(returns, positions):
    trades = returns * positions

    # print(f"Shape of trades: {trades.shape}")
    # print(f"Number of non-NaN trades: {trades.notna().sum().sum()}")

    # Instead of dropping NaN, we'll use notna() to filter
    # valid_trades = trades[trades.notna()]
    # valid_positions = positions[positions.notna()]

    total_trades = ((positions != 0) & positions.notna()).sum().sum()
    profitable_trades = ((trades > 0) & trades.notna()).sum().sum()
    losing_trades = ((trades < 0) & trades.notna()).sum().sum()
    # even_trades = ((trades == 0) & trades.notna()).sum().sum()

    # print(f"Total trades: {total_trades}")
    # print(f"Profitable trades: {profitable_trades}")
    # print(f"Losing trades: {losing_trades}")
    # print(f"Even trades: {even_trades}")

    total_profit = trades.sum().sum()
    gross_profit = trades[trades > 0].sum().sum()
    gross_loss = trades[trades < 0].sum().sum()

    avg_trade_net_profit = total_profit / total_trades if total_trades > 0 else 0
    avg_winning_trade = gross_profit / profitable_trades if profitable_trades > 0 else 0
    avg_losing_trade = gross_loss / losing_trades if losing_trades > 0 else 0

    largest_winning_trade = trades.max().max() if not trades.empty else np.nan
    largest_losing_trade = trades.min().min() if not trades.empty else np.nan

    return {
        "Total number of round_trips": int(total_trades),
        "Percent profitable": profitable_trades / total_trades
        if total_trades > 0
        else 0,
        "Winning round_trips": int(profitable_trades),
        "Losing round_trips": int(losing_trades),
        # 'Even round_trips': int(even_trades),
        "Total profit": total_profit,
        "Gross profit": gross_profit,
        "Gross loss": gross_loss,
        "Profit factor": abs(gross_profit / gross_loss) if gross_loss != 0 else np.inf,
        "Avg. trade net profit": avg_trade_net_profit,
        "Avg. winning trade": avg_winning_trade,
        "Avg. losing trade": avg_losing_trade,
        "Ratio Avg. Win:Avg. Loss": abs(avg_winning_trade / avg_losing_trade)
        if avg_losing_trade != 0
        else np.inf,
        "Largest winning trade": largest_winning_trade,
        "Largest losing trade": largest_losing_trade,
    }


def preprocess_stats(stats):
    dollar_fields = [
        "Total profit",
        "Gross profit",
        "Gross loss",
        "Avg. trade net profit",
        "Avg. winning trade",
        "Avg. losing trade",
        "Largest winning trade",
        "Largest losing trade",
    ]
    integer_fields = [
        "Total number of round_trips",
        "Winning round_trips",
        "Losing round_trips",
    ]

    for key, value in stats.items():
        if key in integer_fields:
            stats[key] = int(value)
        elif key == "Percent profitable":
            stats[key] = f"{value:.2%}"
        elif key in dollar_fields:
            stats[key] = f"${value:.2f}"
        elif isinstance(value, (int, float)):
            stats[key] = f"{value:.2f}"
    return stats


def statistics(resampled_returns, df_balance):
    price_changes, df_rebalanced = resampled_returns, df_balance

    # Calculate stats for all trades, short trades, and long trades
    all_trades_stats = preprocess_stats(calculate_stats(price_changes, df_rebalanced))
    short_trades_stats = preprocess_stats(
        calculate_stats(price_changes, df_rebalanced.where(df_rebalanced < 0, 0))
    )
    long_trades_stats = preprocess_stats(
        calculate_stats(price_changes, df_rebalanced.where(df_rebalanced > 0, 0))
    )

    # Create summary stats table
    summary_stats = pd.DataFrame(
        {
            "All trades": all_trades_stats,
            "Short trades": short_trades_stats,
            "Long trades": long_trades_stats,
        },
        index=[
            "Total number of round_trips",
            "Percent profitable",
            "Winning round_trips",
            "Losing round_trips",
        ],
    )

    # Create PnL stats table
    pnl_stats = pd.DataFrame(
        {
            "All trades": all_trades_stats,
            "Short trades": short_trades_stats,
            "Long trades": long_trades_stats,
        },
        index=[
            "Total profit",
            "Gross profit",
            "Gross loss",
            "Profit factor",
            "Avg. trade net profit",
            "Avg. winning trade",
            "Avg. losing trade",
            "Ratio Avg. Win:Avg. Loss",
            "Largest winning trade",
            "Largest losing trade",
        ],
    )

    # Updated Custom CSS for dark mode with improved padding
    dark_mode_css = """
    <style>
    .gt_table {
        color: #ffffff;
        background-color: #1e1e1e;
        margin-left: 10px !important;
        margin-right: auto !important;
        width: auto !important;
        padding-left: 10px !important;
    }
    .gt_heading {
        background-color: #2a2a2a;
        border-bottom-color: #444;
    }
    .gt_title {
        color: #ffffff;
        text-align: left !important;
        padding-left: 10px !important;
    }
    .gt_subtitle {
        color: #e0e0e0;
        text-align: left !important;
        padding-left: 10px !important;
    }
    .gt_column_spanner {
        border-bottom-color: #444;
        color: #ffffff;
    }
    .gt_row {
        background-color: #1e1e1e;
        color: #ffffff;
        transition: background-color 0.3s;
    }
    .gt_row:hover {
        background-color: #3a3a3a !important;
    }
    .gt_row:nth-child(even) {
        background-color: #252525;
    }
    .gt_stub {
        color: #ffffff;
        background-color: #2a2a2a;
        text-align: left !important;
    }
    .gt_summary_row {
        background-color: #2a2a2a;
        color: #ffffff;
    }
    .gt_grand_summary_row {
        background-color: #333333;
        color: #ffffff;
    }
    .gt_footnote {
        color: #e0e0e0;
        text-align: left !important;
    }
    .gt_source_notes {
        background-color: #2a2a2a;
        color: #e0e0e0;
        text-align: left !important;
    }
    .gt_col_heading {
        color: #ffffff;
        text-align: left !important;
    }
    .gt_center {
        text-align: left !important;
    }
    .gt_row td, .gt_stub, .gt_col_heading {
        padding-left: 10px !important;
    }
    </style>
    """
    # Create and display Summary Stats table using great_tables
    summary_gt = (
        GT(summary_stats.reset_index())
        .tab_header(title="Summary Statistics")
        .cols_label(
            index="Metric",
            **{col: col.replace("_", " ").title() for col in summary_stats.columns},
        )
        .opt_stylize(style=2, color="blue")  # Apply a base style
    )

    # Create and display PnL Stats table using great_tables
    pnl_gt = (
        GT(pnl_stats.reset_index())
        .tab_header(title="Profit and Loss Statistics")
        .cols_label(
            index="Metric",
            **{col: col.replace("_", " ").title() for col in pnl_stats.columns},
        )
        .opt_stylize(style=2, color="blue")  # Apply a base style
    )

    # Combine dark mode CSS with table HTML
    summary_html = dark_mode_css + summary_gt.render(context="html")
    pnl_html = dark_mode_css + pnl_gt.render(context="html")

    display(HTML(summary_html))
    display(HTML(pnl_html))


import numpy as np
import pandas as pd


def create_random_portfolios_efficient(df_rebalanced, num_simulations=100):
    n_stocks = df_rebalanced.shape[1]
    random_rows = np.random.choice([-1, 1], size=(num_simulations, n_stocks))
    random_portfolios = [df_rebalanced * random_row for random_row in random_rows]
    return random_portfolios


def calculate_single_cumulative_return(random_portfolio):
    random_returns = random_portfolio.mean(axis=1)
    return (1 + random_returns).cumprod()


def calculate_random_cumulative_returns(random_portfolios):
    random_cumulative_returns = [
        calculate_single_cumulative_return(portfolio) for portfolio in random_portfolios
    ]
    return random_cumulative_returns


# Function to run a single iteration
def run_single_iteration(asset_returns, num_simulations):
    random_portfolios = create_random_portfolios_efficient(
        asset_returns, num_simulations
    )
    random_cumulative_returns = calculate_random_cumulative_returns(random_portfolios)
    return pd.DataFrame(random_cumulative_returns).T


def construct_samples(asset_returns):
    # Run the process 20 times and concatenate results
    num_iterations = 10
    num_simulations = 5
    random_cumulative_returns_df = pd.DataFrame()
    for r in range(num_iterations):
        iteration_result = run_single_iteration(asset_returns, num_simulations)
        random_cumulative_returns_df = pd.concat(
            [random_cumulative_returns_df, iteration_result], axis=1
        )
        # print(r)

    random_cumulative_returns_df.columns = list(
        range(len(random_cumulative_returns_df.columns))
    )

    # Calculate 99% confidence interval
    lower_bound = random_cumulative_returns_df.quantile(0.01, axis=1)
    upper_bound = random_cumulative_returns_df.quantile(0.99, axis=1)

    # Find the indices of the strategies at the 1st and 99th percentiles
    final_returns = random_cumulative_returns_df.iloc[-1]
    lower_1_index = final_returns.rank(pct=True).idxmin()
    upper_99_index = final_returns.rank(pct=True).idxmax()

    # Extract the 1st and 99th percentile strategies
    lower_1_strategy = random_cumulative_returns_df[lower_1_index]
    upper_99_strategy = random_cumulative_returns_df[upper_99_index]

    # Create a dictionary with the results
    confidence_interval_data = {
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "lower_1_strategy": lower_1_strategy,
        "upper_99_strategy": upper_99_strategy,
    }

    return confidence_interval_data


import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def calculate_rolling_sharpe_ratio(returns, window=52, risk_free_rate=0):
    excess_returns = returns - risk_free_rate
    rolling_mean = excess_returns.rolling(window=window).mean()
    rolling_std = excess_returns.rolling(window=window).std()
    rolling_std = rolling_std.replace(0, np.nan)
    sharpe = (rolling_mean / rolling_std) * np.sqrt(52)
    return sharpe.replace([np.inf, -np.inf], np.nan).dropna()


def plot_cumulative_performance_with_sharpe_and_random(
    cumulative_returns, portfolio_returns, lower_5_strategy, upper_95_strategy
):
    # Calculate rolling Sharpe ratio
    rolling_sharpe = calculate_rolling_sharpe_ratio(portfolio_returns)
    average_sharpe = rolling_sharpe.mean()

    # Create the plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Plot the range between lower_5_strategy and upper_95_strategy
    fig.add_trace(
        go.Scatter(
            x=lower_5_strategy.index,
            y=lower_5_strategy.values,
            fill=None,
            mode="lines",
            line_color="rgba(255, 255, 255, 0)",
            showlegend=False,
            hoverinfo="skip",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=upper_95_strategy.index,
            y=upper_95_strategy.values,
            fill="tonexty",
            mode="lines",
            line_color="rgba(100, 150, 255, 0.5)",
            fillcolor="rgba(50, 100, 200, 0.3)",
            name="95% Confidence Interval",
            hoverinfo="skip",
        ),
        secondary_y=True,
    )

    # Plot lower_5_strategy and upper_95_strategy
    fig.add_trace(
        go.Scatter(
            x=lower_5_strategy.index,
            y=lower_5_strategy.values,
            mode="lines",
            name="2.5th Percentile",
            line=dict(color="#FFFFFF", width=1, dash="dash"),
            hovertemplate="Date: %{x}<br>2.5th Percentile: $%{y:.2f}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=upper_95_strategy.index,
            y=upper_95_strategy.values,
            mode="lines",
            name="97.5th Percentile",
            line=dict(color="#FFFFFF", width=1, dash="dash"),
            hovertemplate="Date: %{x}<br>97.5th Percentile: $%{y:.2f}<extra></extra>",
        ),
        secondary_y=True,
    )

    # Plot main strategy
    fig.add_trace(
        go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns.values,
            mode="lines",
            name="Strategy Returns",
            line=dict(color="#00FFFF", width=2),
            hovertemplate="Date: %{x}<br>Cumulative Returns: $%{y:.2f}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=rolling_sharpe.index,
            y=rolling_sharpe.values,
            mode="lines",
            name="Sharpe Ratio",
            line=dict(color="#FF6B6B"),
            hovertemplate="Date: %{x}<br>Rolling Sharpe Ratio: %{y:.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=rolling_sharpe.index,
            y=[average_sharpe] * len(rolling_sharpe),
            mode="lines",
            name="Average Sharpe",
            line=dict(color="#FFD700", dash="dash", width=1),
            hovertemplate="Date: %{x}<br>Average Sharpe Ratio: %{y:.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    max_value = max(
        cumulative_returns.max(), upper_95_strategy.max(), lower_5_strategy.max()
    )

    # Add some padding (e.g., 50%) to ensure nothing gets cut off
    y_max = max_value * 1.5

    fig.update_layout(
        title="Cumulative Performance and Rolling Sharpe Ratio of Long-Short Strategy",
        xaxis_title="Date",
        yaxis_title="Sharpe Ratio",
        yaxis2_title="Portfolio Value ($)",
        template="plotly_dark",
        legend=dict(x=0.01, y=1.1, orientation="h"),
        hovermode="x unified",
        yaxis=dict(
            showgrid=False, zeroline=True, zerolinecolor="#404040", zerolinewidth=1
        ),
        yaxis2=dict(
            showgrid=False, zeroline=True, zerolinecolor="#404040", zerolinewidth=1
        ),
    )

    fig.update_yaxes(
        tickformat=".2f",
        secondary_y=False,
        range=[rolling_sharpe.min() * 1.1, rolling_sharpe.max() * 1.1],
    )
    fig.update_yaxes(tickformat="$,.2f", secondary_y=True)

    return fig


def performance_plot(cumulative_returns, portfolio_returns, simulations):
    # Now call the function with your data
    return plot_cumulative_performance_with_sharpe_and_random(
        cumulative_returns,
        portfolio_returns,
        simulations["lower_1_strategy"],
        simulations["upper_99_strategy"],
    )


import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px

# Assuming portfolio_returns is your weekly returns series


def get_event_returns(returns, start_date, end_date):
    event_returns = returns.loc[start_date:end_date]
    cumulative_returns = (1 + event_returns).cumprod() - 1
    return cumulative_returns


def stress_plotting(portfolio_returns):
    # Define stress event dates
    stress_events = {
        "Dotcom": ("2000-03-01", "2002-10-01"),
        "Lehman": ("2008-09-01", "2008-10-31"),
        "9/11": ("2001-09-11", "2001-10-11"),
        "US downgrade/European Debt Crisis": ("2011-08-01", "2011-09-30"),
        "Fukushima": ("2011-03-11", "2011-04-11"),
        "US Housing": ("2007-08-01", "2008-03-31"),
        "EZB IR Event": ("2012-07-01", "2012-09-30"),
        "Aug07": ("2007-08-01", "2007-09-30"),
        "Mar08": ("2008-03-01", "2008-04-30"),
        "Sept08": ("2008-09-01", "2008-10-31"),
        "2009Q1": ("2009-01-01", "2009-03-31"),
        "2009Q2": ("2009-04-01", "2009-06-30"),
        "Flash Crash": ("2010-05-01", "2010-06-30"),
        "Apr14": ("2014-04-01", "2014-05-31"),
        "Oct14": ("2014-10-01", "2014-11-30"),
        "Fall2015": ("2015-08-01", "2015-10-31"),
        "Low Volatility Bull Market": ("2017-01-01", "2017-12-31"),
        "GFC Crash": ("2008-09-01", "2009-03-31"),
        "Recovery": ("2009-03-01", "2013-05-31"),
        "New Normal": ("2013-01-01", "2019-12-31"),
        "Covid": ("2020-02-01", "2020-04-30"),
    }

    import pandas as pd
    import numpy as np
    import plotly.graph_objs as go
    from plotly.subplots import make_subplots
    import plotly.express as px

    # (Keep the existing code for get_event_returns and stress_events definition)

    # Calculate cumulative returns for each stress event
    event_returns = {}
    event_avg_returns = {}
    for event, (start, end) in stress_events.items():
        returns = get_event_returns(portfolio_returns, start, end)
        event_returns[event] = returns
        event_avg_returns[event] = returns.iloc[-1] / len(returns)

    # Create a color map for events
    color_map = px.colors.qualitative.Plotly

    # Create the main figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces for cumulative returns
    for i, (event, returns) in enumerate(event_returns.items()):
        color = color_map[i % len(color_map)]
        fig.add_trace(
            go.Scatter(
                x=returns.index,
                y=returns.values,
                mode="lines",
                name=event,
                line=dict(color=color),
                hovertemplate=f"{event}<br>Date: %{{x}}<br>Cumulative Return: %{{y:.2%}}<extra></extra>",
                showlegend=False,
            ),  # Hide from legend
            secondary_y=True,  # Changed to secondary y-axis
        )

    # Select events for average return lines (you can modify this list)
    selected_events = [
        "Dotcom",
        "Lehman",
        "GFC Crash",
        "Covid",
        "Recovery",
        "New Normal",
    ]

    # Find the overall date range
    all_dates = [date for returns in event_returns.values() for date in returns.index]
    start_date, end_date = min(all_dates), max(all_dates)

    # Add horizontal lines for average returns of selected events
    for i, event in enumerate(selected_events):
        avg_return = event_avg_returns[event]
        color = color_map[list(event_returns.keys()).index(event) % len(color_map)]
        fig.add_trace(
            go.Scatter(
                x=[start_date, end_date],
                y=[avg_return, avg_return],
                mode="lines",
                name=f"{event} Avg ({avg_return:.2%})",  # Added actual average return
                line=dict(dash="dash", color=color),
                hovertemplate=f"{event} Avg Return: {avg_return:.2%}<extra></extra>",
            ),
            secondary_y=False,  # Changed to primary y-axis
        )

    # Update layout
    fig.update_layout(
        title_text="Cumulative Returns During Stress Events with Average Returns",
        xaxis_title="Date",
        yaxis_title="Average Returns (Selected Events)",  # Swapped
        yaxis2_title="Cumulative Returns",  # Swapped
        template="plotly_white",
        showlegend=True,
        hovermode="closest",
        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
        margin=dict(b=100),
        # height=700
    )

    # Update axes (swapped)
    fig.update_yaxes(tickformat=".2%", secondary_y=True)
    fig.update_yaxes(tickformat=".2%", secondary_y=False)

    # Show plot
    # fig.show()

    fig.update_layout(template="plotly_dark")

    return fig


import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.stats import norm, median_abs_deviation

# Assuming you have already loaded your asset_returns DataFrame


def distribution_plot(asset_returns, portfolio_returns):
    # Calculate portfolio returns (mean across all assets for each date)
    portfolio_returns = asset_returns.mean(axis=1)

    # Remove any NaN values
    portfolio_returns = portfolio_returns.dropna()

    # Calculate statistics for the plot
    mean_return = portfolio_returns.mean()
    std_dev = portfolio_returns.std()
    mad = median_abs_deviation(portfolio_returns)
    var_95 = np.percentile(portfolio_returns, 5)
    cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
    evar_95 = -np.log(np.mean(np.exp(-portfolio_returns / 0.05))) * 0.05
    worst_realization = portfolio_returns.min()

    # Create the histogram
    fig = go.Figure()

    # Calculate histogram data manually
    hist, bin_edges = np.histogram(portfolio_returns, bins=100, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Add histogram trace
    fig.add_trace(
        go.Bar(
            x=bin_centers,
            y=hist,
            name="Portfolio Returns",
            marker=dict(color="rgba(173, 216, 230, 0.7)"),
            hoverinfo="x+y",
            hovertemplate="Return: %{x:.2%}<br>Probability: %{y:.2%}<extra></extra>",
        )
    )

    # Add normal distribution trace
    x = np.linspace(portfolio_returns.min(), portfolio_returns.max(), 1000)
    normal_dist = norm.pdf(x, mean_return, std_dev)
    normal_dist_scaled = normal_dist * (
        hist.max() / normal_dist.max()
    )  # Correct scaling
    fig.add_trace(
        go.Scatter(
            x=x,
            y=normal_dist_scaled,
            mode="lines",
            name=f"Normal: μ = {mean_return:.2%}, σ = {std_dev:.2%}",
            line=dict(color="orange", dash="dash"),
        )
    )

    # Add vertical lines for statistics with hover information
    statistic_lines = [
        (f"Mean: {mean_return:.2%}", mean_return, "blue", 2),
        (
            f"Mean - Std. Dev.({std_dev:.2%}): {mean_return - std_dev:.2%}",
            mean_return - std_dev,
            "red",
            1,
        ),
        (
            f"Mean - MAD({mad:.2%}): {mean_return - mad:.2%}",
            mean_return - mad,
            "magenta",
            1,
        ),
        (f"95.00% Confidence VaR: {var_95:.2%}", var_95, "green", 1),
        (f"95.00% Confidence CVaR: {cvar_95:.2%}", cvar_95, "cyan", 1),
        (f"95.00% Confidence EVaR: {evar_95:.2%}", evar_95, "orange", 1),
        (f"Worst Realization: {worst_realization:.2%}", worst_realization, "gray", 1),
    ]

    for name, value, color, width in statistic_lines:
        fig.add_trace(
            go.Scatter(
                x=[value, value],
                y=[0, hist.max() + 5],
                mode="lines",
                name=name,
                line=dict(color=color, width=width),
                hoverinfo="name+x",
                hovertemplate=f"{name}: %{{x:.2%}}<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title="Portfolio Returns Histogram",
        xaxis_title="Returns",
        yaxis_title="Probability Density",
        # height=600,
        # width=1000,
        template="plotly_dark",
        xaxis=dict(tickformat=".2%", range=[-0.06, 0.06]),
        yaxis=dict(range=[0, hist.max() * 1.1]),  # Adjust y-axis range
        legend=dict(
            x=1.1,
            y=1.1,
            xanchor="right",
            yanchor="top",
            # bgcolor='rgba(255, 255, 255, 0.7)',
            bordercolor="rgba(0, 0, 0, 0.5)",
            borderwidth=1,
        ),
        hovermode="x unified",
    )

    fig.update_layout(template="plotly_dark")

    # Show the plot
    # fig.show()
    return fig


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def drawdown_plot(portfolio_returns):
    # Calculate cumulative returns
    cumulative_returns = (1 + portfolio_returns).cumprod()

    # Calculate drawdowns
    previous_peaks = cumulative_returns.cummax()
    drawdowns = (cumulative_returns - previous_peaks) / previous_peaks
    drawdowns = drawdowns.bfill()

    def find_drawdown_periods(drawdowns):
        periods = []
        in_drawdown = False
        start_date = None
        for date, value in drawdowns.items():
            if not in_drawdown and value < 0:
                in_drawdown = True
                start_date = date
            elif in_drawdown and value == 0:
                in_drawdown = False
                periods.append((start_date, date, drawdowns[start_date:date].min()))

        if in_drawdown:
            periods.append(
                (start_date, drawdowns.index[-1], drawdowns[start_date:].min())
            )

        return sorted(periods, key=lambda x: x[2])[:5]

    top_5_drawdowns = find_drawdown_periods(drawdowns)

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.4, 0.6]
    )

    # Add cumulative returns trace
    fig.add_trace(
        go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns,
            name="Portfolio",
            line=dict(color="#00FFFF", width=1),
            fill="tozeroy",
            fillcolor="rgba(0,255,255,0.1)",
        ),
        row=1,
        col=1,
    )

    # Add drawdown trace
    fig.add_trace(
        go.Scatter(
            x=drawdowns.index,
            y=drawdowns,
            fill="tozeroy",
            name="Drawdown",
            line=dict(color="#FF6B6B", width=1),
            fillcolor="rgba(255,107,107,0.3)",
        ),
        row=2,
        col=1,
    )

    # Add top 5 drawdown periods
    colors = [
        "rgba(255,200,200,0.2)",
        "rgba(255,180,180,0.2)",
        "rgba(255,160,160,0.2)",
        "rgba(255,140,140,0.2)",
        "rgba(255,120,120,0.2)",
    ]

    top_5_drawdowns.sort(key=lambda x: x[0])

    for i, ((start, end, depth), color) in enumerate(zip(top_5_drawdowns, colors)):
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor=color,
            opacity=0.5,
            layer="below",
            line_width=0,
            row="all",
        )
        y_position = cumulative_returns.max() * (0.8 - i * 0.15)
        fig.add_annotation(
            x=start + (end - start) / 2,
            y=y_position,
            text=f"{depth:.2%}",
            showarrow=False,
            font=dict(size=12, color="#FF6B6B"),
            row=1,
            col=1,
        )

    # Calculate drawdown statistics
    def calculate_ulcer_index(drawdowns):
        return np.sqrt(np.mean(drawdowns**2))

    def calculate_average_drawdown(drawdowns):
        return drawdowns[drawdowns < 0].mean()

    def calculate_dar(drawdowns, confidence=0.95):
        return np.percentile(drawdowns, (1 - confidence) * 100)

    def calculate_edar(drawdowns, confidence=0.95):
        return calculate_dar(drawdowns, confidence) * 1.1

    ulcer_index = calculate_ulcer_index(drawdowns)
    average_drawdown = calculate_average_drawdown(drawdowns)
    dar_95 = calculate_dar(drawdowns, confidence=0.95)
    edar_95 = calculate_edar(drawdowns, confidence=0.95)
    max_drawdown = drawdowns.min()

    # Add horizontal lines for drawdown statistics
    statistics = [
        ("Ulcer Index", ulcer_index, "#00FFFF"),
        ("Average Drawdown", average_drawdown, "#FF6B6B"),
        ("95.00% Confidence DaR", dar_95, "#FF69B4"),
        ("95.00% Confidence EDaR", edar_95, "#9370DB"),
        ("Maximum Drawdown", max_drawdown, "#FFFFFF"),
    ]

    for name, value, color in statistics:
        fig.add_shape(
            type="line",
            x0=drawdowns.index[0],
            x1=drawdowns.index[-1],
            y0=value,
            y1=value,
            line=dict(color=color, width=1, dash="dash"),
            row=2,
            col=1,
        )
        fig.add_annotation(
            x=drawdowns.index[-1],
            y=value,
            text=f"{name}: {value:.2%}",
            showarrow=False,
            xanchor="right",
            yanchor="bottom",
            font=dict(size=10, color=color),
            row=2,
            col=1,
        )

    # Update layout
    fig.update_layout(
        title="Portfolio Performance and Drawdowns",
        height=700,
        legend_title_text="",
        showlegend=True,
        # plot_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor="black",
        paper_bgcolor="black",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(color="#FFFFFF"),
    )

    fig.update_xaxes(
        title_text="Date",
        row=2,
        col=1,
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
    )
    fig.update_yaxes(
        title_text="Cumulative<br>Returns",
        row=1,
        col=1,
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
    )
    fig.update_yaxes(
        title_text="Drawdown",
        tickformat=".0%",
        row=2,
        col=1,
        showgrid=True,
        gridcolor="rgba(255,255,255,0.1)",
    )

    fig.update_yaxes(
        range=[min(drawdowns.min(), max_drawdown) * 1.1, 0.01], row=2, col=1
    )

    fig.update_layout(template="plotly_dark")

    return fig


import pandas as pd
import numpy as np


def calculate_metrics(returns):
    annual_return = (1 + returns).prod() ** (52 / len(returns)) - 1
    metrics = {
        "Annual return": annual_return,
        "Cumulative returns": (1 + returns).prod() - 1,
        "Annual volatility": returns.std() * np.sqrt(52),
        "Sharpe ratio": annual_return / (returns.std() * np.sqrt(52)),
        "Max drawdown": (returns.cummax() - returns).max(),
        "Calmar ratio": annual_return / abs((returns.cummax() - returns).max()),
        "Stability": 1 - (returns.std() / returns.mean()),
        "Omega ratio": len(returns[returns > 0]) / len(returns[returns <= 0]),
        "Sortino ratio": annual_return / (returns[returns < 0].std() * np.sqrt(52)),
        "Skew": returns.skew(),
        "Kurtosis": returns.kurtosis(),
        "Tail ratio": abs(returns.quantile(0.95)) / abs(returns.quantile(0.05)),
        "Weekly value at risk": returns.quantile(0.05),
        "Gross leverage": 1.0,  # Assuming no leverage
        "Weekly turnover": returns.abs().mean(),
    }
    return pd.Series(metrics)


def find_drawdown_periods(returns):
    cum_returns = (1 + returns).cumprod()
    drawdowns = cum_returns / cum_returns.cummax() - 1
    drawdown_periods = []
    in_drawdown = False
    peak_date = valley_date = recovery_date = None

    for date, value in drawdowns.items():
        if not in_drawdown and value < 0:
            in_drawdown, peak_date = True, date
        elif in_drawdown and (valley_date is None or value < drawdowns[valley_date]):
            valley_date = date
        elif in_drawdown and value == 0:
            recovery_date = date
            drawdown_periods.append(
                (
                    peak_date,
                    valley_date,
                    recovery_date,
                    drawdowns[peak_date:valley_date].min(),
                )
            )
            in_drawdown, peak_date, valley_date, recovery_date = False, None, None, None

    if in_drawdown:
        drawdown_periods.append(
            (
                peak_date,
                valley_date,
                "Not Recovered",
                drawdowns[peak_date:valley_date].min(),
            )
        )

    return sorted(drawdown_periods, key=lambda x: x[3])[
        :5
    ]  # Sort by drawdown depth and get top 5


def create_basic_info_table(start_date, end_date, out_of_sample_start):
    return pd.DataFrame(
        {
            "Start date": [start_date],
            "End date": [end_date],
            "In-sample weeks": [
                (pd.to_datetime(out_of_sample_start) - pd.to_datetime(start_date)).days
                // 7
            ],
            "Out-of-sample weeks": [
                (pd.to_datetime(end_date) - pd.to_datetime(out_of_sample_start)).days
                // 7
            ],
        }
    )


def create_drawdown_table(worst_drawdowns):
    return pd.DataFrame(
        [
            (
                i,
                f"{abs(depth):.2%}",
                peak_date.strftime("%Y-%m-%d") if peak_date else "N/A",
                valley_date.strftime("%Y-%m-%d") if valley_date else "N/A",
                recovery_date
                if recovery_date == "Not Recovered"
                else (recovery_date.strftime("%Y-%m-%d") if recovery_date else "N/A"),
                (pd.to_datetime(recovery_date) - pd.to_datetime(peak_date)).days // 7
                if recovery_date and recovery_date != "Not Recovered"
                else "NaN",
            )
            for i, (peak_date, valley_date, recovery_date, depth) in enumerate(
                worst_drawdowns
            )
        ],
        columns=[
            "Index",
            "Net drawdown in %",
            "Peak date",
            "Valley date",
            "Recovery date",
            "Duration (weeks)",
        ],
    )


import pandas as pd
import numpy as np
from great_tables import GT, md, html
from IPython.display import display, HTML

# Keep the existing helper functions (calculate_metrics, find_drawdown_periods, etc.) as they are


def draw_down_statistics(portfolio_returns):
    # Existing preprocessing code remains the same
    portfolio_returns.index = pd.to_datetime(portfolio_returns.index)
    portfolio_returns = portfolio_returns.sort_index()

    start_date = portfolio_returns.index[0]
    while start_date.weekday() != 4:
        start_date += pd.Timedelta(days=1)

    end_date = portfolio_returns.index[-1]
    while end_date.weekday() != 4:
        end_date -= pd.Timedelta(days=1)

    out_of_sample_start = "2022-01-07"  # First Friday of 2022

    in_sample_returns = portfolio_returns[start_date:out_of_sample_start]
    out_of_sample_returns = portfolio_returns[out_of_sample_start:end_date]
    all_returns = portfolio_returns[start_date:end_date]

    metrics_df = pd.DataFrame(
        {
            "In-sample": calculate_metrics(in_sample_returns),
            "Out-of-sample": calculate_metrics(out_of_sample_returns),
            "All": calculate_metrics(all_returns),
        }
    )

    metrics_df = metrics_df.apply(lambda x: x.map("{:.3f}".format))
    metrics_df.loc["Gross leverage"] = "1.000"

    # Updated Custom CSS for dark mode with improved padding
    dark_mode_css = """
    <style>
    .gt_table {
        color: #ffffff;
        background-color: #1e1e1e;
        margin-left: 10px !important;
        margin-right: auto !important;
        width: auto !important;
        padding-left: 10px !important;
    }
    .gt_heading {
        background-color: #2a2a2a;
        border-bottom-color: #444;
    }
    .gt_title {
        color: #ffffff;
        text-align: left !important;
        padding-left: 10px !important;
    }
    .gt_subtitle {
        color: #e0e0e0;
        text-align: left !important;
        padding-left: 10px !important;
    }
    .gt_column_spanner {
        border-bottom-color: #444;
        color: #ffffff;
    }
    .gt_row {
        background-color: #1e1e1e;
        color: #ffffff;
        transition: background-color 0.3s;
    }
    .gt_row:hover {
        background-color: #3a3a3a !important;
    }
    .gt_row:nth-child(even) {
        background-color: #252525;
    }
    .gt_stub {
        color: #ffffff;
        background-color: #2a2a2a;
        text-align: left !important;
    }
    .gt_summary_row {
        background-color: #2a2a2a;
        color: #ffffff;
    }
    .gt_grand_summary_row {
        background-color: #333333;
        color: #ffffff;
    }
    .gt_footnote {
        color: #e0e0e0;
        text-align: left !important;
    }
    .gt_source_notes {
        background-color: #2a2a2a;
        color: #e0e0e0;
        text-align: left !important;
    }
    .gt_col_heading {
        color: #ffffff;
        text-align: left !important;
    }
    .gt_center {
        text-align: left !important;
    }
    .gt_row td, .gt_stub, .gt_col_heading {
        padding-left: 10px !important;
    }
    </style>
    """
    # Create Table 1: Basic Information
    table1_info = create_basic_info_table(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        out_of_sample_start,
    )
    table1_gt = (
        GT(table1_info)
        .tab_header(title="Basic Information")
        .opt_stylize(style=2, color="blue")
    )

    # Create Table 2: Performance Overview
    table2_gt = (
        GT(metrics_df.reset_index())
        .tab_header(title="Performance Overview")
        .cols_label(index="Metric", **{col: col for col in metrics_df.columns})
        .opt_stylize(style=2, color="blue")
    )

    # Create Table 3: Worst Drawdown Periods
    worst_drawdowns = find_drawdown_periods(all_returns)
    table3 = create_drawdown_table(worst_drawdowns)
    table3_gt = (
        GT(table3)
        .tab_header(title="Worst Drawdown Periods")
        .opt_stylize(style=2, color="blue")
    )

    # Combine dark mode CSS with table HTML
    table1_html = dark_mode_css + table1_gt.render(context="html")
    table2_html = dark_mode_css + table2_gt.render(context="html")
    table3_html = dark_mode_css + table3_gt.render(context="html")

    # Display tables
    display(HTML(table1_html))
    display(HTML(table3_html))
    display(HTML(table2_html))


import pandas as pd
import plotly.graph_objects as go
import numpy as np


def create_weekly_returns_heatmap(portfolio_returns):
    # Ensure the index is datetime
    portfolio_returns.index = pd.to_datetime(portfolio_returns.index)

    # Get all unique years from the index
    all_years = sorted(portfolio_returns.index.year.unique())

    # Calculate monthly average of weekly returns
    monthly_avg = portfolio_returns.groupby(
        [portfolio_returns.index.year, portfolio_returns.index.month]
    ).sum()

    # Reshape the data into a 2D array, including all years
    heatmap_data = monthly_avg.unstack(level=0).reindex(
        columns=all_years, fill_value=np.nan
    )

    # Create a list of month names for y-axis labels
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    # Get full year labels
    year_labels = [str(year) for year in all_years]

    # Create the heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=year_labels,
            y=month_names,
            colorscale="rdbu",  # Red for negative, Blue for positive
            zmin=np.nanpercentile(
                heatmap_data.values, 5
            ),  # 5th percentile for lower bound
            zmax=np.nanpercentile(
                heatmap_data.values, 95
            ),  # 95th percentile for upper bound
            showscale=False,  # Remove the color scale
            hovertemplate="Year: %{x}<br>Month: %{y}<br>Return: %{z:.2%}<extra></extra>",
            text=heatmap_data.values,
            texttemplate="%{text:.2%}",
            textfont={"size": 10},
        )
    )

    # Update layout
    fig.update_layout(
        title={
            "text": "Monthly Average Signal Returns",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=18),
        },
        xaxis_title="Year",
        yaxis_title="Month",
        xaxis_tickangle=-90,
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(len(year_labels))),
            ticktext=year_labels,
            tickfont=dict(size=12),
        ),
        yaxis=dict(tickfont=dict(size=12)),
        font=dict(family="Arial", size=14),
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Add a border to the heatmap cells
    fig.update_traces(xgap=1, ygap=1)

    fig.update_layout(template="plotly_dark")

    return fig


import pandas as pd
import plotly.graph_objects as go
import numpy as np


def calculate_turnover(df, mask):
    df_rebalance = df[mask]
    # Separate long and short positions
    long_positions = df_rebalance.where(df_rebalance > 0, 0)
    short_positions = df_rebalance.where(df_rebalance < 0, 0).abs()
    # Calculate changes for each strategy
    long_changes = long_positions.diff().abs().sum(axis=1)
    short_changes = short_positions.diff().abs().sum(axis=1)
    # Calculate total turnover
    total_turnover = long_changes + short_changes
    # Calculate percentages
    long_percentage = (long_changes / total_turnover * 100).fillna(0)
    short_percentage = (short_changes / total_turnover * 100).fillna(0)
    return pd.DataFrame(
        {
            "Long Turnover %": long_percentage,
            "Short Turnover %": -short_percentage,
        }  # Negative to show below x-axis
    )


def turnover_plot(df_balance, rebalance_mask):
    # Calculate turnover percentages
    turnover_df = calculate_turnover(df_balance, rebalance_mask)
    turnover_df = turnover_df.query("index >= '1999-01-01'")

    # Find the max and min values
    y_max = max(
        turnover_df["Long Turnover %"].max(), abs(turnover_df["Short Turnover %"].min())
    )
    y_min = -y_max  # Make it symmetrical

    # Create the stacked bar chart
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=turnover_df.index,
            y=turnover_df["Long Turnover %"],
            name="Long Turnover",
            marker_color="rgba(0, 123, 255, 0.7)",
        )
    )
    fig.add_trace(
        go.Bar(
            x=turnover_df.index,
            y=turnover_df["Short Turnover %"],
            name="Short Turnover",
            marker_color="rgba(255, 99, 132, 0.7)",
        )
    )

    # Update layout
    fig.update_layout(
        title={
            "text": "Portfolio Turnover Percentage (4-Week Rebalancing)",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=24),
        },
        xaxis_title="Date",
        yaxis_title="Turnover Percentage",
        barmode="relative",
        legend_title="Position Type",
        hovermode="x unified",
        plot_bgcolor="black",
        # width=1200,
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Adjust x-axis
    fig.update_xaxes(
        tickformat="%Y-%m",
        dtick="M6",
        tickangle=45,
        showgrid=True,
        gridcolor="lightgrey",
    )

    # Adjust y-axis
    fig.update_yaxes(
        range=[y_min, y_max],  # Set the range based on data
        ticksuffix="%",
        showgrid=True,
        gridcolor="lightgrey",
        zeroline=True,
        zerolinecolor="black",
        zerolinewidth=2,
    )

    # Show the plot

    fig.update_layout(template="plotly_dark")

    return fig


import pandas as pd
import numpy as np


def fast_rolling_autocorrelation(df, window):
    # Convert DataFrame to NumPy array
    data = df.values

    # Create 3D array: (window, num_rows - window + 1, num_columns)
    shape = (window, data.shape[0] - window + 1, data.shape[1])
    strides = (data.strides[0], data.strides[0], data.strides[1])
    windows = np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)

    # Calculate means for each window
    means = np.mean(windows, axis=0)

    # Calculate variances for each window
    variances = np.var(windows, axis=0)

    # Calculate covariance
    covariance = np.mean((windows[:-1] - means) * (windows[1:] - means), axis=0)

    # Calculate autocorrelation
    autocorrelation = covariance / variances

    # Create DataFrame with results
    result = pd.DataFrame(
        autocorrelation, index=df.index[window - 1 :], columns=df.columns
    )

    return result


def signal_correlation(df_signal):
    window_size = 12
    autocorrelation = fast_rolling_autocorrelation(df_signal, window_size)
    autocorrelation_single = autocorrelation.query("date >='1999-01-01'").mean(axis=1)

    mean_autocorrelation = np.mean(autocorrelation_single)

    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(
        go.Scatter(
            x=autocorrelation_single.index,
            y=autocorrelation_single.values,
            mode="lines",
            name="Autocorrelation",
        )
    )

    fig.add_hline(
        y=mean_autocorrelation,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_autocorrelation:.3f}",
        annotation_position="top right",
    )

    fig.update_layout(
        title="Signal Rank Autocorrelation Over Time",
        xaxis_title="Date",
        yaxis_title="Autocorrelation",
        hovermode="x unified",
        # template='plotly_white'  # This will adapt to dark mode automatically
    )

    return fig


import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from joblib import Parallel, delayed


def create_portfolio_holdings_fast(df_signal, lower_bound, upper_bound):
    signal_array = df_signal.values
    holdings_array = np.zeros_like(signal_array)
    holdings_array[(signal_array > lower_bound) & (signal_array <= upper_bound)] = 1
    holdings_array[np.isnan(signal_array)] = np.nan
    df_holdings = pd.DataFrame(
        holdings_array, index=df_signal.index, columns=df_signal.columns
    )
    return df_holdings


def calculate_returns_and_sharpe(df_holdings, df_prices, risk_free_rate=0):
    df_temp = df_holdings.fillna(2)
    rebalance_mask = pd.Series(False, index=df_temp.index)
    rebalance_mask.iloc[0] = True
    rebalance_mask.iloc[4::4] = True
    df_rebalanced = (
        df_temp.where(rebalance_mask, np.nan).ffill().replace({2: np.nan, 0: np.nan})
    )

    price_changes = df_prices.pct_change(fill_method=None).clip(upper=1)
    asset_returns = df_rebalanced * price_changes
    portfolio_returns = asset_returns.mean(axis=1)
    cumulative_returns = (1 + portfolio_returns).cumprod()

    excess_returns = portfolio_returns - risk_free_rate
    sharpe_ratio = np.sqrt(52) * excess_returns.mean() / excess_returns.std()

    return cumulative_returns, sharpe_ratio


def process_decile(i, df_signal, df_prices):
    lower_bound = i * 10
    upper_bound = (i + 1) * 10
    df_holdings = create_portfolio_holdings_fast(df_signal, lower_bound, upper_bound)
    returns, sharpe = calculate_returns_and_sharpe(df_holdings, df_prices)
    return f"Decile {i+1}", returns, sharpe


def decile_plots(df_signal, df_prices):
    # Assuming df_signal and df_prices are already defined

    # Use joblib to parallelize the calculations
    results = Parallel(n_jobs=-1)(
        delayed(process_decile)(i, df_signal, df_prices) for i in range(10)
    )

    # Convert results to dictionaries
    decile_returns = {decile: returns for decile, returns, _ in results}
    decile_sharpes = {decile: sharpe for decile, _, sharpe in results}

    # Create the plot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Plot cumulative returns
    for decile, returns in decile_returns.items():
        fig.add_trace(
            go.Scatter(x=returns.index, y=returns.values, mode="lines", name=decile),
            secondary_y=True,
        )

    # Add horizontal lines for average Sharpe ratios on secondary y-axis
    for decile, sharpe in decile_sharpes.items():
        fig.add_trace(
            go.Scatter(
                x=[returns.index[0], returns.index[-1]],
                y=[sharpe, sharpe],
                mode="lines",
                name=f"{decile} Sharpe: {sharpe:.2f}",
                line=dict(dash="dash"),
                showlegend=False,
            ),
            secondary_y=False,
        )

    # Update layout
    fig.update_layout(
        title="Signal Cumulative Returns by Decile with Average Sharpe Ratios",
        xaxis_title="Date",
        # template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Update y-axes
    fig.update_yaxes(title_text="Cumulative Returns", secondary_y=True)
    fig.update_yaxes(title_text="Sharpe Ratio", secondary_y=False)

    fig.update_layout(
        template="plotly_dark",
        height=500,
    )

    # Show the plot
    return fig

    # If you want to save the plot as an HTML file
    # fig.write_html("cumulative_returns_and_sharpe_by_decile.html")


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
from joblib import Parallel, delayed


class SignalEvaluator:
    # --- Initialization with verbose parameter ---
    def __init__(self, df_factor, verbose=False): # Added verbose parameter
        self.verbose = verbose # Store verbose state
        if self.verbose:
            print("--- SignalEvaluator Initialization ---")
            if isinstance(df_factor, (pd.DataFrame, pd.Series)):
                print(f"Input df_factor shape: {df_factor.shape}")
                # Use the new _log_df_preview for the initial df_factor print
                # Note: Using head() here as requested in previous refinement
                self._log_df_preview(df_factor, "Input df_factor head:")
            else:
                print(f"Input df_factor type: {type(df_factor)}")

        self.df_factor = df_factor
        # The following attributes will be logged within their respective methods
        self.df_signal, self.df_prices = self._signal_frame()
        self.positions = self._create_portfolio_holdings()
        self.rebalance_mask = self._calc_rebalanced_mask()
        self.holdings = self._real_holdings()
        self.returns = self._calculate_returns()
        self.position_returns = self._calculate_position_returns()
        self.resampled_returns = self._calculate_resampled_returns()
        self.portfolio_returns = self._portfolio_returns()
        self.cumulative_returns = self._cummulative_returns()

        # self.statistics = self._calculate_statistics() # Keep commented if not used

        if self.verbose:
            print("--- SignalEvaluator Initialization Complete ---")

    # --- Logging Helper Methods ---
    def _log_df_preview(self, df_to_log, header_message="Preview:", max_cols_to_show=5, show_nan_summary=True):
        """
        Prints a preview of a DataFrame or Series, intelligently slicing wide DataFrames.
        Uses .head() for the preview.
        """
        if df_to_log is None:
            print(f"{header_message} (None)")
            return

        print(f"{header_message} (Shape: {df_to_log.shape})")
        if isinstance(df_to_log, pd.DataFrame):
            if not df_to_log.empty:
                num_cols = df_to_log.shape[1]
                cols_to_display = min(num_cols, max_cols_to_show)
                # Display head of selected columns
                print(df_to_log.iloc[:, :cols_to_display].head())
                if show_nan_summary:
                    print("NaNs count for displayed columns:")
                    # Show NaN sum for the displayed columns
                    print(df_to_log.iloc[:, :cols_to_display].isnull().sum())
            else:
                print("(DataFrame is empty)")
        elif isinstance(df_to_log, pd.Series):
            if not df_to_log.empty:
                print(df_to_log.head()) # Show head for Series
                if show_nan_summary:
                    print(f"NaNs count: {df_to_log.isnull().sum()}")
            else:
                print("(Series is empty)")
        else:
            print(f"(Object is not a DataFrame or Series: {type(df_to_log)})")

    def _log(self, message, df_to_preview=None, max_cols=5):
        """Helper function for conditional logging. Uses _log_df_preview for DataFrames/Series."""
        if self.verbose:
            print(message)
            if df_to_preview is not None:
                # Pass an empty header as the main message is already printed
                self._log_df_preview(df_to_preview, header_message="Preview:", max_cols_to_show=max_cols)


    # --- Core Calculation Methods with Logging ---
    def _signal_frame(self):
        self._log("Running _signal_frame...")
        factor = self.df_factor
        # Ensure this column name matches your actual factor data
        if factor.columns.empty:
             self._log("Error: Input df_factor has no columns.")
             return pd.DataFrame(), pd.DataFrame() # Return empty to avoid index error
        column_name = factor.columns[0]

        # --- Crucial Area 1: Getting df_with_price ---
        # Verify that df_with_price correctly contains both the signal column
        # AND a valid numeric 'price' column, indexed correctly by date and ticker.
        if hasattr(factor, 'add_price') and callable(getattr(factor, 'add_price')):
            # Make sure factor.add_price() actually returns a DataFrame with 'price'
            df_with_price = factor.add_price()
            self._log("Preview of df_with_price AFTER add_price():", df_with_price)
        else:
            # Assumes 'price' column already exists in factor if add_price not used
            df_with_price = factor
            if 'price' not in df_with_price.columns:
                 self._log("Warning: 'price' column not found in df_factor and add_price() was not used.")
                 # Handle error or return empty DFs
                 return pd.DataFrame(), pd.DataFrame()
            self._log("Preview of df_with_price (assuming price exists):", df_with_price)


        # --- Crucial Area 2: Indexing Check ---
        # Ensure 'ticker' and 'date' are index levels for unstacking
        required_index_levels = ['date', 'ticker']
        if not all(level in df_with_price.index.names for level in required_index_levels):
             self._log(f"Warning: Index levels {required_index_levels} not found for unstacking. Current index: {df_with_price.index.names}", df_with_price.head())
             # Add logic here to set the index correctly if needed, e.g.:
             # if 'date' in df_with_price.columns and 'ticker' in df_with_price.columns:
             #     self._log("Attempting to set index ['date', 'ticker']...")
             #     try:
             #         df_with_price = df_with_price.set_index(['date', 'ticker'])
             #     except KeyError as e:
             #         self._log(f"Failed to set index: {e}")
             #         return pd.DataFrame(), pd.DataFrame() # Handle error
             # else:
             #     self._log("Cannot set index - 'date' or 'ticker' columns missing.")
             #     return pd.DataFrame(), pd.DataFrame() # Handle error


        # --- Crucial Area 3: The Unstack Operations ---
        try:
            # Check df_with_price[column_name] before unstacking
            self._log(f"Preview of signal data '{column_name}' before unstack:", df_with_price[column_name])
            df_signal = df_with_price[column_name].unstack(level="ticker").shift(1)

            # **** FOCUS HERE: Check df_with_price['price'] ****
            self._log("Preview of 'price' data before unstack:", df_with_price['price'])
            df_prices = df_with_price["price"].unstack(level="ticker")

            # **** Check if df_prices is all NaN ****
            if not df_prices.empty and df_prices.isnull().all().all():
                self._log("CRITICAL: df_prices is ALL NaN after unstacking! Check price data source and indexing.")

        except Exception as e:
            self._log(f"Error during unstacking in _signal_frame: {e}")
            self._log("df_with_price index at time of error:", df_with_price.index.names)
            self._log("df_with_price columns at time of error:", df_with_price.columns)
            self._log("df_with_price head at time of error:", df_with_price.head())
            # Return empty DataFrames or re-raise to prevent further issues
            return pd.DataFrame(), pd.DataFrame()


        self._log("Result of _signal_frame - df_signal:", df_signal)
        self._log("Result of _signal_frame - df_prices:", df_prices)
        return df_signal, df_prices

    def _create_portfolio_holdings(self):
        self._log("Running _create_portfolio_holdings...")
        if self.df_signal.empty:
            self._log("df_signal is empty in _create_portfolio_holdings. Returning empty DataFrame.")
            return pd.DataFrame(index=self.df_signal.index, columns=self.df_signal.columns)

        signal_array = self.df_signal.values
        holdings_array = np.zeros_like(signal_array)
        try:
            with np.errstate(invalid='ignore'): # Suppress warnings for NaN comparisons
                 holdings_array[signal_array <= 10] = -1
                 holdings_array[signal_array >= 90] = 1
            holdings_array[np.isnan(signal_array)] = np.nan # Set NaNs explicitly
        except TypeError as e:
            self._log(f"TypeError during holdings_array assignment: {e}. signal_array sample: {signal_array[:2, :2] if signal_array.ndim > 1 else signal_array[:2]}")
            # Fallback or re-raise
            pass

        df_holdings = pd.DataFrame(
            holdings_array, index=self.df_signal.index, columns=self.df_signal.columns
        )
        self._log("Result of _create_portfolio_holdings - positions:", df_holdings)
        return df_holdings

    def _calc_rebalanced_mask(self):
        self._log("Running _calc_rebalanced_mask...")
        # Use the created positions index to create the mask
        if self.positions.empty:
            self._log("Positions DataFrame is empty in _calc_rebalanced_mask. Returning empty Series.")
            return pd.Series(dtype=bool)

        # No need for fillna(2) here, just use the index
        rebalance_mask = pd.Series(False, index=self.positions.index)
        if not rebalance_mask.empty:
            rebalance_mask.iloc[0] = True
            rebalance_mask.iloc[4::4] = True # Every 4th row after the first
        self._log("Result of _calc_rebalanced_mask - rebalance_mask (Series):", rebalance_mask)
        return rebalance_mask

    def _real_holdings(self):
        self._log("Running _real_holdings...")
        df_initial_holdings = self.positions

        if df_initial_holdings.empty or self.rebalance_mask.empty:
            self._log("Initial positions or rebalance_mask is empty in _real_holdings. Returning empty DataFrame.")
            return pd.DataFrame(index=df_initial_holdings.index, columns=df_initial_holdings.columns)

        # Apply the rebalancing mask and forward fill
        # No need for the intermediate fillna(2) step
        df_balance = df_initial_holdings.where(self.rebalance_mask).ffill()

        # Replace 0 with NaN *after* forward filling
        df_balance = df_balance.replace(0, np.nan)

        self._log("Result of _real_holdings - final holdings (df_balance):", df_balance)
        return df_balance

    def _portfolio_returns(self):
        self._log("Running _portfolio_returns...")
        if self.position_returns.empty:
            self._log("position_returns is empty. Returning empty Series for portfolio_returns.")
            return pd.Series(dtype=float)

        # Calculate mean returns, ignoring NaNs by default
        portfolio_returns = self.position_returns.mean(axis=1)

        self._log("Result of _portfolio_returns - portfolio_returns (Series):", portfolio_returns)
        return portfolio_returns

    def _cummulative_returns(self):
        self._log("Running _cummulative_returns...")
        if self.portfolio_returns.empty or self.portfolio_returns.isnull().all():
            self._log("portfolio_returns is empty or all NaN. Returning empty/NaN Series for cumulative_returns.")
            return pd.Series(dtype=float, index=self.portfolio_returns.index) # Keep index if possible

        # Calculate cumulative returns
        cumulative_returns = (1 + self.portfolio_returns).cumprod()

        self._log("Result of _cummulative_returns - cumulative_returns (Series):", cumulative_returns)
        return cumulative_returns

    def _calculate_returns(self):
        self._log("Running _calculate_returns (price percentage changes)...")
        if self.df_prices.empty:
            self._log("df_prices is empty. Returning empty DataFrame for asset_price_returns.")
            return pd.DataFrame(index=self.df_prices.index, columns=self.df_prices.columns)
        if self.df_prices.isnull().all().all():
             self._log("df_prices is ALL NaN. Returns calculation will result in NaNs.")

        # fill_method=None is deprecated, default is None (no filling)
        asset_price_returns = self.df_prices.pct_change()
        asset_price_returns = asset_price_returns.clip(upper=3)

        self._log("Result of _calculate_returns - asset_price_returns:", asset_price_returns)
        return asset_price_returns

    def _calculate_position_returns(self):
        self._log("Running _calculate_position_returns...")
        if self.holdings.empty or self.returns.empty:
            self._log("Holdings or returns are empty. Returning empty DataFrame for position_returns.")
            idx = self.holdings.index if not self.holdings.empty else self.returns.index
            cols = self.holdings.columns if not self.holdings.empty else self.returns.columns
            return pd.DataFrame(index=idx, columns=cols)
        if self.returns.isnull().all().all():
             self._log("Returns DataFrame is ALL NaN. Position returns will be NaN.")

        # Ensure alignment (pandas usually handles this, but good to be aware)
        # Check if indices/columns match if issues arise
        if not self.holdings.index.equals(self.returns.index):
             self._log("Warning: Index mismatch between holdings and returns in _calculate_position_returns.")
        if not self.holdings.columns.equals(self.returns.columns):
             self._log("Warning: Column mismatch between holdings and returns in _calculate_position_returns.")


        position_returns = self.holdings * self.returns
        self._log("Result of _calculate_position_returns - position_returns:", position_returns)
        return position_returns

    def _calculate_resampled_returns(self):
        self._log("Running _calculate_resampled_returns...")
        if self.position_returns.empty:
            self._log("position_returns is empty in _calculate_resampled_returns. Returning empty DataFrame.")
            return pd.DataFrame(columns=self.position_returns.columns)

        resample_group_mask = pd.Series(False, index=self.position_returns.index)
        if not resample_group_mask.empty:
            resample_group_mask.iloc[0] = True
            resample_group_mask.iloc[4::4] = True

        def custom_resampler(x):
            # Sum ignores NaNs by default, so sum of all NaNs is 0.
            return x.sum()

        group_numbers = (resample_group_mask.cumsum() - 1).ffill()

        if group_numbers.isnull().all():
            self._log("No valid groups for resampling. Returning empty DataFrame.")
            return pd.DataFrame(columns=self.position_returns.columns)

        resampled_returns = self.position_returns.groupby(group_numbers).apply(custom_resampler)

        # Align index with rebalance dates
        true_mask_indices = resample_group_mask[resample_group_mask].index
        if len(true_mask_indices) == len(resampled_returns):
            resampled_returns.index = true_mask_indices
        else:
            # This case might happen if the last period doesn't align perfectly
            # Or if groupby produces unexpected number of groups
            self._log(f"Warning: Mismatch in length for resampled_returns index. Resampled length: {len(resampled_returns)}, True mask indices: {len(true_mask_indices)}. Attempting partial index assignment.")
            common_len = min(len(true_mask_indices), len(resampled_returns))
            resampled_returns = resampled_returns.iloc[:common_len]
            resampled_returns.index = true_mask_indices[:common_len]


        self._log("Result of _calculate_resampled_returns - resampled_returns:", resampled_returns)
        return resampled_returns

    def _calculate_statistics(self):
        # This method was previously commented out or missing implementation details
        self._log("Running _calculate_statistics...")
        if self.portfolio_returns.empty or self.portfolio_returns.isnull().all():
             self._log("Cannot calculate statistics: portfolio_returns is empty or all NaN.")
             return None # Or return an empty structure / specific message

        # Assuming draw_down_statistics exists and takes a Series
        # stats = draw_down_statistics(self.portfolio_returns)
        # self._log("Statistics calculation complete.") # Add preview if needed
        # return stats
        self._log("Placeholder for statistics calculation.")
        return "Statistics Placeholder"


    @property
    def performance_plot(self):
        return performance_plot(
            self.cumulative_returns, self.portfolio_returns, self._construct_samples()
        )

    @property
    def performance_table(self):
        return statistics(self.resampled_returns, self.holdings[self.rebalance_mask])

    @property
    def stress_plot(self):
        return stress_plotting(self.position_returns.mean(axis=1))

    @property
    def distribution_plot(self):
        return distribution_plot(
            self.position_returns, self.position_returns.mean(axis=1)
        )

    @property
    def drawdown_plot(self):
        return drawdown_plot(self.position_returns.mean(axis=1))

    @property
    def drawdown_table(self):
        return draw_down_statistics(self.position_returns.mean(axis=1))

    @property
    def returns_heatmap_plot(self):
        return create_weekly_returns_heatmap(self.position_returns.mean(axis=1))

    @property
    def turnover_plot(self):
        rebalance_mask = pd.Series(False, index=self.positions.index)
        rebalance_mask.iloc[0] = True
        rebalance_mask.iloc[4::4] = True
        return turnover_plot(self.positions, rebalance_mask)

    @property
    def signal_correlation_plot(self):
        return signal_correlation(self.df_signal)

    @property
    def signal_decile_plot(self):
        return decile_plots(self.df_signal, self.df_prices)

    def _construct_samples(self):
        return construct_samples(self.position_returns)
