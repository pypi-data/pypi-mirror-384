import pandas as pd
import numpy as np
import plotly.express as px
from numpy.linalg import norm


# First, we'll define a function that does what we want
# Define the function that performs the operation you want.
# To make the get_latest function adaptable to different DataFrame structures, we need to implement
# some checks to handle whether the 'date' is in a MultiIndex, a single Index, or a column.
# Here's a more flexible version of the function:


def percentile(df, on="date"):
    """
    Calculates the percentile rank for each value. The calculation can be grouped by 'on',
    which can be 'date', 'ticker', or 'all' (for no grouping).

    :param df: pandas DataFrame.
    :param on: Specifies the grouping for percentile calculation; 'date', 'ticker', or 'all'.
    :return: DataFrame with percentile ranks.
    """
    if on not in ["date", "ticker", "all"]:
        raise ValueError("Parameter 'on' must be 'date', 'ticker', or 'all'.")

    if on in ["date", "ticker"]:
        if on in df.columns or on in df.index.names:
            df_percentile = df.groupby(on).transform(lambda x: x.rank(pct=True))
        else:
            raise ValueError(f"'{on}' not found in DataFrame columns or index names.")
    elif on == "all":
        df_percentile = df.rank(pct=True)

    df_percentile = df_percentile.replace([np.inf, -np.inf], np.nan)
    df_percentile = df_percentile.fillna(0.5)

    return df_percentile


def get_latest(df):
    # Check if 'date' is a level in a MultiIndex
    if isinstance(df.index, pd.MultiIndex) and "date" in df.index.names:
        latest_date = df.index.get_level_values("date").max()
        latest_data = df.loc[df.index.get_level_values("date") == latest_date]

    # Check if 'date' is the name of the Index
    elif "date" == df.index.name:
        latest_date = df.index.max()
        latest_data = df.loc[df.index == latest_date]

    # Check if 'date' is a column in the DataFrame
    elif "date" in df.columns:
        latest_date = df["date"].max()
        latest_data = df.loc[df["date"] == latest_date]

    # If 'date' is not found, return None or raise an error
    else:
        raise ValueError(
            "The DataFrame does not contain a 'date' in its index or columns."
        )

    # Assuming 'prediction' is a column in the DataFrame
    # If the DataFrame structure is different, additional checks may be required
    if "prediction" in latest_data.columns:
        return latest_data.sort_values("prediction", ascending=False)
    else:
        return latest_data


# Now, you can use the function with any DataFrame structure that contains 'date' and 'prediction'
# latest_data


def plot_line(df, column=None, tickers=None):
    """
    Plots a line chart for a specified column from the DataFrame using Plotly.
    Handles DataFrame with 'date' as a column, index, or part of a MultiIndex.

    :param df: The DataFrame containing the data to plot.
    :param column: The name of the column to plot. If None, tries to find a suitable column.
    :param tickers: A list of ticker symbols to filter on. If None, plots for multiple or all tickers.
    :return: A Plotly graph object.
    """

    # Check if DataFrame has a MultiIndex
    if isinstance(df.index, pd.MultiIndex):
        # Reset the index for plotting
        df = df.reset_index()

    # Identify the date column or index
    if "date" in df.columns:
        x_axis = "date"
    elif isinstance(df.index, pd.DatetimeIndex):
        x_axis = df.index
        df = df.reset_index()
    else:
        raise ValueError("No 'date' column or index found in DataFrame.")

    # If a specific column is not provided, try to find a suitable one
    if column is None:
        preferred_columns = ["probability", "prediction"]
        for col in preferred_columns + list(
            df.select_dtypes(include=["float", "float32", "float64"]).columns
        ):
            if col in df.columns and df[col].nunique() > 10:
                column = col
                break
        else:
            raise ValueError(
                "Please specify a column to plot, unable to find a suitable default."
            )

    # Handle ticker filtering
    if "ticker" in df.columns and tickers:
        if isinstance(tickers, list):
            df_to_plot = df[df["ticker"].isin(tickers)]
        else:
            df_to_plot = df[df["ticker"] == tickers]
    elif "ticker" in df.columns:
        # Select 10 random tickers if there are more than 10, else plot all
        available_tickers = df["ticker"].unique()
        tickers_to_plot = np.random.choice(
            available_tickers, size=min(10, len(available_tickers)), replace=False
        )
        df_to_plot = df[df["ticker"].isin(tickers_to_plot)]
        print("Plotting for random tickers. Specify tickers to plot specific data.")
    else:
        df_to_plot = df

    # Create the plot
    fig = px.line(
        df_to_plot,
        x=x_axis,
        y=column,
        color="ticker" if "ticker" in df.columns else None,
        title=f"Line Plot of {column}",
    )
    return fig


# Example usage:
# fig = plot_line(df_breakout, tickers=['TSLA', 'AAPL'])
# fig.show()


def normalize_min_max(matrix):
    """Apply Min-Max normalization."""
    min_val = np.min(matrix)
    max_val = np.max(matrix)
    return (matrix - min_val) / (max_val - min_val)


def distance(df, on="ticker"):
    """
    Calculate the Cosine distance for a MultiIndex DataFrame with Min-Max normalization.

    :param df: Pandas DataFrame with MultiIndex
    :param level: The level of the MultiIndex to group by (default 'ticker')
    :return: DataFrame of normalized Cosine distances
    """
    # Aggregate data by the specified level
    agg_df = df.groupby(level=on).mean()

    # Cosine Similarity and Distance
    dot_product = agg_df.values @ agg_df.values.T
    l2_norm = norm(agg_df.values, axis=1)
    cosine_similarity = dot_product / np.outer(l2_norm, l2_norm)
    cosine_distance = 1 - cosine_similarity

    # Normalize the distance matrix
    cosine_distance = normalize_min_max(cosine_distance)

    # Convert the normalized distance array to a DataFrame
    cosine_distance = pd.DataFrame(
        cosine_distance, index=agg_df.index, columns=agg_df.index
    )

    return cosine_distance


# Prepare the DataFrame by adding the function as an attribute.
def prepare_dataframe(df):
    # Convert the function to a method of the instance `df`.
    df.get_latest = get_latest.__get__(df)
    df.plot_line = plot_line.__get__(df)
    df.percentile = percentile.__get__(df)
    df.distance = distance.__get__(df)
    return df


import pandas as pd
import numpy as np


class CustomDataFrame(pd.DataFrame):
    @property
    def _constructor(self):
        # Ensures that pandas operations return CustomDataFrame objects
        return CustomDataFrame

    def get_latest(self):
        # Define or call your 'get_latest' method here
        pass

    def plot_line(self):
        # Define or call your 'plot_line' method here
        pass

    def percentile(self, on="date"):
        # Your percentile calculation code here
        # Remember to return a CustomDataFrame
        pass

    def distance(self, on="ticker"):
        # Your distance calculation code here
        # Remember to return a CustomDataFrame
        pass


# Example usage
df = CustomDataFrame(your_data)
result = df.percentile().distance()
