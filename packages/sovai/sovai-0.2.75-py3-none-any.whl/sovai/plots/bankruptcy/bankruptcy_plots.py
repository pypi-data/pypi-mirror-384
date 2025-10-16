import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
from plotly.subplots import make_subplots


def create_plot(df, tickers, probability_column, moving_average, dark_mode):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = px.colors.qualitative.Plotly[: len(tickers)]

    for i, ticker in enumerate(tickers):
        ticker_df = df[df["ticker"] == ticker]
        fig.add_trace(
            go.Scatter(
                x=ticker_df["date"],
                y=ticker_df[probability_column],
                name=f"{ticker} {probability_column.capitalize()}",
                line=dict(color=colors[i]),
            ),
            secondary_y=(i == 1 and len(tickers) == 2),
        )

    if moving_average:
        for i, ticker in enumerate(tickers):
            ma_df = df[df["ticker"] == ticker]
            fig.add_trace(
                go.Scatter(
                    x=ma_df["date"],
                    y=ma_df[f"{probability_column}_ma"],
                    name=f"{ticker} {moving_average}-Month MA",
                    line=dict(color=colors[i], dash="dash", width=1),
                    opacity=0.6,
                ),
                secondary_y=(i == 1 and len(tickers) == 2),
            )

    fig.update_layout(
        title=f"{probability_column.capitalize()} Over Time for Selected Tickers"
    )
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(
        title_text=f"{tickers[0]} {probability_column.capitalize()}", secondary_y=False
    )

    if len(tickers) == 2:
        fig.update_yaxes(
            title_text=f"{tickers[1]} {probability_column.capitalize()}",
            secondary_y=True,
        )

    if dark_mode:
        fig.update_layout(template="plotly_dark")

    return fig


def plot_ticker_probabilities(
    df,
    tickers,
    probability_column="probability",
    moving_average=None,
    same_plot=True,
    lookback_period=None,
    dark_mode=False,
):
    """
    Plots a specified probability column and optionally its moving average over time for specified tickers
    on the same or separate plots using Plotly Express. Allows for an optional lookback period selection and dark mode.
    
    :param df: Pandas DataFrame containing the data with MultiIndex (ticker, date).
    :param tickers: List of tickers to plot.
    :param probability_column: The probability column to plot, defaults to 'probability'.
    :param moving_average: The window size for the moving average, None for no moving average.
    :param same_plot: Boolean to indicate if all tickers should be plotted on the same plot.
    :param lookback_period: Number of days in the past to include in the plot, None for all history.
    :param dark_mode: Boolean to enable dark mode for the plot.
    """
    # Reset index to work with ticker and date as columns
    df_reset = df.reset_index()
    
    # Filter DataFrame for the selected tickers
    filtered_df = df_reset[df_reset["ticker"].isin(tickers)]
    
    # Ensure 'date' is a datetime column for proper plotting
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])
    
    # Sort by date to ensure correct calculations
    filtered_df = filtered_df.sort_values(by=["ticker", "date"])
    
    # Calculating moving average for each ticker
    if moving_average is not None:
        filtered_df[f"{probability_column}_ma"] = filtered_df.groupby("ticker")[
            probability_column
        ].transform(lambda x: x.rolling(window=moving_average, min_periods=1).mean())
    
    # Filter the DataFrame based on the lookback period if specified
    if lookback_period is not None:
        max_date = filtered_df["date"].max()
        min_date = max_date - pd.Timedelta(days=lookback_period)
        filtered_df = filtered_df[filtered_df["date"] >= min_date]
    
    # Plotting logic based on 'same_plot' parameter
    if same_plot:
        # Plot on the same graph
        fig = create_plot(
            filtered_df, tickers, probability_column, moving_average, dark_mode
        )
        fig.show(renderer="colab")
    else:
        # Plot on separate graphs
        for ticker in tickers:
            ticker_df = filtered_df[filtered_df["ticker"] == ticker]
            fig = create_plot(
                ticker_df, [ticker], probability_column, moving_average, dark_mode
            )
            fig.show(renderer="colab")


def plot_bankruptcy_monthly_line(df, tickers=None):
    # Set default tickers if None is provided
    if tickers is None:
        tickers = ["TSLA", "LULU"]
    
    # Convert the tickers list to a string (limit to 5 tickers)
    tickers_str = ", ".join(tickers[:5])
    
    ticker_input = widgets.Text(value=tickers_str, description="Tickers:")
    probability_column_selector = widgets.Dropdown(
        options=df.columns, value="probability", description="Probability"
    )
    moving_average_selector = widgets.IntSlider(
        value=12, min=0, max=24, step=1, description="MA Months"
    )
    lookback_period_selector = widgets.IntSlider(
        value=0, min=0, max=1000, step=10, description="Lookback"
    )
    same_plot_selector = widgets.Checkbox(value=False, description="Same Plot")
    dark_mode_selector = widgets.Checkbox(value=True, description="Dark Mode")

    # Create an output widget to display the plot
    output = widgets.Output()

    # Create a function to update the plot
    def update_plot(change):
        with output:
            output.clear_output(wait=True)
            try:
                tickers = [ticker.strip() for ticker in ticker_input.value.split(",")]
                plot_ticker_probabilities(
                    df,
                    tickers=tickers,
                    probability_column=probability_column_selector.value,
                    moving_average=None
                    if moving_average_selector.value == 0
                    else moving_average_selector.value,
                    same_plot=same_plot_selector.value,
                    lookback_period=None
                    if lookback_period_selector.value == 0
                    else lookback_period_selector.value,
                    dark_mode=dark_mode_selector.value,
                )
            except Exception as e:
                print(f"An error occurred: {e}")

    # Attach the update_plot function as an observer to each widget
    ticker_input.observe(update_plot, names="value")
    probability_column_selector.observe(update_plot, names="value")
    moving_average_selector.observe(update_plot, names="value")
    lookback_period_selector.observe(update_plot, names="value")
    same_plot_selector.observe(update_plot, names="value")
    dark_mode_selector.observe(update_plot, names="value")

    # Function to toggle the visibility of the widget controls
    def toggle_controls(b):
        controls_container.layout.display = (
            "none" if controls_container.layout.display == "flex" else "flex"
        )

    toggle_button = widgets.Button(description="Show/Hide Controls")
    toggle_button.on_click(toggle_controls)

    row1 = widgets.HBox(
        [ticker_input, probability_column_selector, dark_mode_selector, toggle_button]
    )
    row2 = widgets.HBox(
        [moving_average_selector, lookback_period_selector, same_plot_selector]
    )

    # Group widgets into a container
    controls_container = widgets.VBox([row1, row2])

    # Display the widgets and the output widget
    display(controls_container, output)

    # Initially, display the current plot
    update_plot(None)  # Pass None because the event parameter is not used



def plot_pca_clusters(df, target="target", max_lag=12, max_date=None):
    """
    Plot a scatter plot of PCA clusters using Plotly with a lag slider to adjust the date.

    :param df: DataFrame containing PCA components and target.
    :param target: Name of the target column that indicates health status.
    :param max_lag: The maximum number of months to lag.
    :param max_date: The maximum date available in the dataset.
    """
    if max_date is None:
        max_date = datetime.today()  # Set max_date to today's date if not provided

    # Define the PCA components dropdown
    pca_components = [
        "price_factor_pca",
        "volatility_factor_pca",
        "solvency_factor_pca",
        "liquidity_factor_pca",
    ]
    pca_x_dropdown = widgets.Dropdown(
        options=pca_components, value=pca_components[0], description="X-axis:"
    )
    pca_y_dropdown = widgets.Dropdown(
        options=pca_components, value=pca_components[1], description="Y-axis:"
    )

    # Define the lag slider
    lag_slider = widgets.IntSlider(
        value=-12,
        min=-max_lag,
        max=0,
        step=1,
        description="Lag:",
        continuous_update=False,
    )
    date_label = widgets.Label(
        layout=widgets.Layout(margin="0 0 0 40px")
    )  # 20px left margin

    # space_label = widgets.Label()

    # Prepare the output area for the plot
    output = widgets.Output()

    # Define the function to update the plot
    def update_plot(*args):
        with output:
            clear_output(wait=True)
            # Calculate the period for the lag
            lag_months = lag_slider.value
            selected_month = max_date + pd.DateOffset(months=lag_months)
            selected_month_start = pd.Timestamp(
                selected_month.year, selected_month.month, 1
            )
            selected_month_end = pd.Timestamp(
                selected_month.year, selected_month.month, 1
            ) + pd.offsets.MonthEnd(0)

            date_label.value = f"Date: {selected_month.strftime('%Y-%m')}"  # Adjust the number of nbsp as needed

            # Data for the specific month
            filtered_df = df[
                (df["date"] >= selected_month_start)
                & (df["date"] <= selected_month_end)
            ].copy()
            # print(filtered_df.tail())

            # Highlight the targets
            filtered_df["highlight"] = (
                filtered_df[target].map({0: "Healthy", 1: "Bankrupt"}).copy()
            )

            # Plot

            # Define colors for dark mode visibility
            # color_discrete_map = {0: 'rgba(57, 255, 20, 0.8)', 1: 'rgba(255, 85, 85, 0.8)'}  # Neon green and neon red

            fig = px.scatter(
                filtered_df,
                x=pca_x_dropdown.value,
                y=pca_y_dropdown.value,
                color="highlight",
                labels={"highlight": "Financial Health"},
                hover_data=["ticker", "date"],
            )
            # fig.update_traces(marker=dict(size=10, symbol='circle', opacity=0.8))
            fig.update_layout(template="plotly_dark", showlegend=True)
            fig.show(renderer="colab")

    # Setup widget interaction
    pca_x_dropdown.observe(update_plot, names="value")
    pca_y_dropdown.observe(update_plot, names="value")
    lag_slider.observe(update_plot, names="value")

    # Display widgets
    widgets_container = widgets.HBox(
        [pca_x_dropdown, pca_y_dropdown, lag_slider, date_label]
    )
    display(widgets_container, output)

    # Initial plot
    update_plot()


# Create a scatter plot for each ticker
def plot_ticker(df_bankrupt, ticker, probability_column):

    df_ticker = df_bankrupt[df_bankrupt["ticker"] == ticker].copy()

    df_ticker["highlight"] = (
        df_ticker["target"].shift(23).fillna(0).map({0: "Healthy", 1: "Bankrupt"})
    )

    # df_ticker['highlight'] = df_bankrupt['target'].transform(lambda x: x.shift(23).fillna(0)).map({0: 'Healthy', 1: 'Bankrupt'}).copy()

    fig = px.scatter(
        df_ticker,
        x="date",
        y="probability",
        color="highlight",
        labels={"probability": "Probability of Bankruptcy", "target": "Bankruptcy"},
        title=f"Bankruptcy Probability Over Time for {ticker}",
    )

    fig = px.scatter(
        df_ticker,
        x="date",
        y=probability_column,
        color="highlight",
        labels={
            probability_column: "Probability of Bankruptcy",
            "target": "Bankruptcy",
        },
        title=f"Bankruptcy Probability Over Time for {ticker} using {probability_column}",
    )

    # Sort bankrupt points by date in ascending order to get the oldest bankruptcy first
    bankrupt_points = df_ticker[df_ticker["target"] == 1].sort_values(
        by="date", ascending=True
    )

    # Loop through bankrupt points to add vertical lines with varying opacity
    for idx, (i, point) in enumerate(bankrupt_points.iterrows()):
        # Calculate opacity: start with 1.0 and progressively decrease to 0.2 for the oldest
        # Calculate opacity: start with 0.2 and progressively increase towards 1.0 for older events
        opacity = (
            0.2 + 0.8 * (idx / (len(bankrupt_points) - 1))
            if len(bankrupt_points) > 1
            else 0.2
        )

        fig.add_vline(
            x=point["date"],
            line_width=2,
            line_dash="dash",
            line_color=f"rgba(255,0,0,{opacity})",
        )

    # Update layout for dark mode
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        title_font_color="white",
        transition_duration=500,
    )
    return fig


def plot_ticker_widget(df_bankrupt, sorted_tickers):
    # Dropdown for selecting bankrupt tickers
    # bankrupt_tickers = df_bankrupt[df_bankrupt['target'] == 1]['ticker'].unique()
    ticker_dropdown = widgets.Dropdown(
        options=sorted_tickers,
        description="Bankrupt:",
        disabled=False,
    )

    # Search box for searching all tickers
    ticker_search = widgets.Text(
        value="",
        placeholder="Search all tickers",
        description="Search:",
        disabled=False,
    )

    probability_columns = [
        "probability",
        "probability_light",
        "probability_convolution",
        "probability_rocket",
        "probability_encoder",
        "probability_fundamental",
    ]

    probability_dropdown = widgets.Dropdown(
        options=probability_columns,
        value="probability",
        description="Probability:",
        disabled=False,
    )

    # Output widget to display plot
    output = widgets.Output()

    last_selected_ticker = sorted_tickers[0] if sorted_tickers else None

    def widget_eventhandler(change):
        nonlocal last_selected_ticker
        with output:
            clear_output(wait=True)
            ticker = last_selected_ticker  # Use the last selected ticker by default

            # Update last selected ticker if change is from ticker_search or ticker_dropdown
            if change is not None and change["owner"] in [
                ticker_search,
                ticker_dropdown,
            ]:
                last_selected_ticker = change["new"]
                ticker = last_selected_ticker

            probability_column = probability_dropdown.value
            fig = plot_ticker(df_bankrupt, ticker, probability_column)
            fig.show(renderer="colab")

    ticker_dropdown.observe(widget_eventhandler, names="value")
    probability_dropdown.observe(widget_eventhandler, names="value")
    ticker_search.observe(widget_eventhandler, names="value")

    widgets_container = widgets.HBox(
        [ticker_dropdown, ticker_search, probability_dropdown]
    )
    display(widgets_container, output)

    widget_eventhandler(None)
