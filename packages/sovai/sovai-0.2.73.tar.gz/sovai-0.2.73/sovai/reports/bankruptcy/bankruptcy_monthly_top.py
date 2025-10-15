import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML


def show_bankruptcy_monthly_top(df=None, sort=None, names=None):

    tickers_meta = pd.read_parquet("data/tickers.parq")

    print(sort)

    if "date" in df.columns:
        df_filtered = df[df["date"] == df["date"].max()]
    # If 'date' is not a column, check if it's in the index
    elif "date" in df.index.names:
        df = df.reset_index()
        df_filtered = df[df["date"] == df["date"].max()]
    else:
        # Raise an error if 'date' is neither a column nor in the index
        raise ValueError(
            "The DataFrame is not compatible: 'date' is neither a column nor in the index."
        )

    df = pd.merge(df, tickers_meta, on="ticker", how="left")

    df = df.drop_duplicates(subset=["ticker"])

    def make_clickable(ticker):
        url = f"https://finance.yahoo.com/quote/{ticker}"
        return f'<a href="{url}" target="_blank">{ticker}</a>'

    def gradient_color(value):
        """
        Converts a probability value into a color that forms part of a gradient.
        Assumes that value is a string formatted as a percentage (e.g., '15.23%').
        The gradient is applied only to numeric values, with higher probabilities
        getting a color closer to green, and lower probabilities closer to red.
        """
        try:
            prob = (
                float(value.strip("%")) / 100
            )  # Normalize the probability to a range between 0 and 1
            red = 255
            green = int(255 * prob)  # More probable values get greener
            blue = int(255 * (1 - prob))  # Less probable values get bluer
            color = f"rgb({red}, {green}, {blue})"  # Gradient from red to blue
        except:
            color = "inherit"  # Use the default text color if conversion fails

        return f"color: {color};"

    # Function to display the DataFrame based on the selected options
    def display_dataframe(category, top_n, prob_type, ascending):
        with output:
            clear_output(wait=True)

            # Group by category and get the top N for each group
            grouped = df.groupby(category)

            top_n_df = pd.DataFrame()

            for name, group in grouped:
                top_group = (
                    group.nlargest(top_n, prob_type)
                    if not ascending
                    else group.nsmallest(top_n, prob_type)
                )
                top_group["rank"] = range(1, len(top_group) + 1)
                top_n_df = pd.concat([top_n_df, top_group])

            # Format the probability column to show percentage with two decimals
            top_n_df[prob_type] = top_n_df[prob_type].map("{:.2f}".format)

            top_n_df["ticker"] = top_n_df["ticker"].apply(make_clickable)

            # Create a pivot table with the rank as index
            top_n_pivot = (
                top_n_df.pivot(
                    index="rank", columns=category, values=[prob_type, "ticker"]
                )
                .swaplevel(axis=1)
                .sort_index(axis=1, level=0)
            )

            # Apply coloring based on the value of the probability
            styled_pivot = top_n_pivot.style.applymap(gradient_color)

            # Display the DataFrame with styles
            display(styled_pivot)

    # Widgets for user input
    category_dropdown = widgets.Dropdown(
        options=["sector", "scalemarketcap", "scalerevenue", "category"],
        value="sector",
        description="Category:",
    )
    top_n_slider = widgets.IntSlider(
        value=10, min=1, max=20, step=1, description="Top N:"
    )
    probability_type_dropdown = widgets.Dropdown(
        options=[col for col in df.columns], value=sort, description=f"{names} Type:"
    )
    sort_order_toggle = widgets.ToggleButtons(
        options={"Descending": False, "Ascending": True}, value=False
    )
    output = widgets.Output()

    # Function to update the DataFrame display when widget values change
    def on_value_change(change):
        display_dataframe(
            category_dropdown.value,
            top_n_slider.value,
            probability_type_dropdown.value,
            sort_order_toggle.value,
        )

    # Observe widgets for changes
    category_dropdown.observe(on_value_change, names="value")
    top_n_slider.observe(on_value_change, names="value")
    probability_type_dropdown.observe(on_value_change, names="value")
    sort_order_toggle.observe(on_value_change, names="value")

    # Layout the widgets
    widgets_layout = widgets.HBox(
        [category_dropdown, probability_type_dropdown, top_n_slider, sort_order_toggle]
    )

    # Initialize the display
    display(widgets_layout, output)
    on_value_change(None)  # Trigger the display of the dataframe


def create_difference_df(df_bankrupt):
    df_bankrupt_change = df_bankrupt.copy()
    float_columns = df_bankrupt_change.select_dtypes(include="float").columns
    df_bankrupt_change[float_columns] = df_bankrupt_change.groupby("ticker")[
        float_columns
    ].diff()
    return df_bankrupt_change


def show_bankruptcy_monthly_change(df=None, sort=None, names=None):
    return show_bankruptcy_monthly_top(create_difference_df(df), sort, names)


def report_accounting_diff_average(df_importance_pct_mapped):
    # Function to prepare the data by subtracting the 'average' from all other columns
    def data_plot_function_diff(df_importance_pct_mapped):
        max_date = df_importance_pct_mapped.index.get_level_values("date").max()
        max_date_rows = df_importance_pct_mapped.loc[
            df_importance_pct_mapped.index.get_level_values("date") == max_date
        ].copy()
        max_date_rows["average"] = max_date_rows.mean(axis=1)

        columns_to_process = df_importance_pct_mapped.columns.difference(
            ["average"]
        ).tolist()
        for column in columns_to_process:
            max_date_rows[column] -= max_date_rows["average"]

        return max_date_rows

    # Assuming max_date_rows is the DataFrame you want to work with

    def create_widgets(max_date_rows):
        # Create widgets for user input
        metric_dropdown = widgets.Dropdown(
            options=max_date_rows.columns.tolist(), description="Metric:"
        )
        top_n_slider = widgets.IntSlider(
            value=5, min=1, max=200, step=1, description="Top N:"
        )
        ascending_toggle = widgets.ToggleButtons(
            options={"Ascending": True, "Descending": False}, value=False
        )
        output = widgets.Output()
        description_output = widgets.Output()
        return (
            metric_dropdown,
            top_n_slider,
            ascending_toggle,
            output,
            description_output,
        )

    def setup_interaction(
        metric_dropdown,
        top_n_slider,
        ascending_toggle,
        output,
        description_output,
        max_date_rows,
    ):
        # Function to display the DataFrame based on the selected options
        def display_dataframe(metric, top_n, ascending):
            with output:
                clear_output(wait=True)
                top_n_rows = (
                    max_date_rows.nsmallest(top_n, metric)
                    if ascending
                    else max_date_rows.nlargest(top_n, metric)
                )
                display(top_n_rows)

            with description_output:
                clear_output(wait=True)
                order_text = "lower" if ascending else "higher"
                risk_text = "lower" if ascending else "higher"
                description_text = (
                    f"<b>{'Ascending' if ascending else 'Descending'} Order:</b> Tickers at the top have {order_text} "
                    f"'{metric}' values, indicating a {risk_text} risk of bankruptcy according to this metric."
                )
                display(HTML(description_text))

        # Function to update the DataFrame display when widget values change
        def on_value_change(change):
            display_dataframe(
                metric_dropdown.value, top_n_slider.value, ascending_toggle.value
            )

        # Observe widgets for changes
        metric_dropdown.observe(on_value_change, names="value")
        top_n_slider.observe(on_value_change, names="value")
        ascending_toggle.observe(on_value_change, names="value")

        # Layout the widgets and the output
        widgets_layout = widgets.HBox([metric_dropdown, top_n_slider, ascending_toggle])

        # Initialize the display
        display(widgets_layout, output, description_output)
        # Trigger the initial display of the dataframe
        display_dataframe(
            metric_dropdown.value, top_n_slider.value, ascending_toggle.value
        )

    def show_difference_bankruptcy(df_importance_pct_mapped=None):
        # Run the interactive display
        max_date_rows = data_plot_function_diff(df_importance_pct_mapped)
        (
            metric_dropdown,
            top_n_slider,
            ascending_toggle,
            output,
            description_output,
        ) = create_widgets(max_date_rows)
        setup_interaction(
            metric_dropdown,
            top_n_slider,
            ascending_toggle,
            output,
            description_output,
            max_date_rows,
        )

    show_difference_bankruptcy(df_importance_pct_mapped)
