import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

import numpy as np
import random

random.seed(42)
np.random.seed(42)
from sovai.utils.port_manager import get_unique_port


def pandas_to_array(df_accounting, days=None, features_select=None):

    # Pivot the DataFrame
    df_standardized = df_accounting.reset_index().pivot(index="date", columns="ticker")

    # Handling missing data
    df_standardized.fillna(method="ffill", inplace=True)
    df_standardized.fillna(method="bfill", inplace=True)

    if days:
        df_standardized = df_standardized.tail(days)

    # Standardize the features
    scaler = StandardScaler()
    df_standardized = pd.DataFrame(
        scaler.fit_transform(df_standardized),
        index=df_standardized.index,
        columns=df_standardized.columns,
    )

    if features_select:
        # Select the specified features
        df_standardized = df_standardized[features_select]

        num_dates = len(df_standardized)
        num_tickers = len(df_standardized.columns.levels[1])

        if len(features_select) == 1:
            # If there's only one feature selected
            num_features = 1
            np_array = df_standardized.to_numpy().T.reshape(
                num_tickers, num_dates, num_features
            )
        else:
            # If more than one feature is selected
            num_features = len(features_select)
            np_array = df_standardized.to_numpy().reshape(
                num_dates, num_features, num_tickers
            )
            np_array = np_array.swapaxes(0, 2).swapaxes(1, 2)

        return (
            np_array,
            df_standardized.columns.levels[1],
            features_select,
            df_standardized.index,
        )
    else:
        # If no specific features are selected
        num_dates = len(df_standardized)
        num_features = len(df_standardized.columns.levels[0])
        num_tickers = len(df_standardized.columns.levels[1])

        np_array = df_standardized.to_numpy().reshape(
            num_dates, num_features, num_tickers
        )
        np_array = np_array.swapaxes(0, 2).swapaxes(1, 2)

        return (
            np_array,
            df_standardized.columns.levels[1],
            df_standardized.columns.levels[0],
            df_standardized.index,
        )


import itertools
from functools import cache
import pandas as pd
import hashlib
from sovai.extensions.core_kshape import KShapeClusteringCPU
import numpy as np


def calculate_number_of_clusters(n_tickers):
    if n_tickers <= 10:
        return 3
    elif n_tickers <= 100:
        # Linear increase from 5 to 9 clusters as tickers increase from 10 to 100
        return int(5 + 6 * (n_tickers - 10) / 90)
    else:
        # Sigmoid-like function for a smooth transition from 9 to 12 clusters
        return int(9 + 3 / (1 + np.exp(-0.03 * (n_tickers - 100))))
    # Ensure the number of clusters does not exceed 12
    return min(int(round(clusters)), 12)


import hashlib
import pandas as pd
from functools import cache


def hash_dataframe(df):
    return hashlib.md5(pd.util.hash_pandas_object(df.head(100)).values).hexdigest()


@cache
def segment_series_cached(df_hash, features_select_hash):
    global df_accounting_global, features_select_global
    df_accounting = df_accounting_global
    features_select = features_select_global

    days = df_accounting.index.get_level_values("date").nunique()
    np_array, tickers, features, dates = pandas_to_array(
        df_accounting, days=days, features_select=features_select
    )
    n_tickers = int(len(tickers))
    num_clusters = calculate_number_of_clusters(n_tickers)
    ksc = KShapeClusteringCPU(
        n_clusters=num_clusters, centroid_init="zero", max_iter=1000, n_jobs=1
    )
    ksc.fit(np_array)
    labels = ksc.labels_
    cluster_centroids = ksc.centroids_
    dicta = {"tickers": tickers, "labels": labels}
    dicat_df = pd.DataFrame(dicta)
    idx, centroids, distances, result = ksc.predict(np_array)
    return (
        idx,
        centroids,
        distances,
        result,
        tickers,
        features,
        dates,
        dicat_df,
        num_clusters,
    )


def segment_series(df_accounting, features_select=None):
    global df_accounting_global, features_select_global
    df_accounting_global = df_accounting
    features_select_global = features_select

    df_hash = hash_dataframe(df_accounting)
    features_select_hash = hash(tuple(features_select)) if features_select else None
    return segment_series_cached(df_hash, features_select_hash)


def cluster(df_mega, features_select=None):

    df_mega = df_mega[~df_mega.index.duplicated(keep="first")]  # ← NEW LINE

    days = df_mega.index.get_level_values("date").nunique()

    (
        idx,
        centroids,
        distances,
        result,
        tickers,
        features,
        dates,
        dicat_df,
        num_clusters,
    ) = segment_series(df_mega, features_select)

    # Generate centroid names
    centroids_names = [f"Centroid {i}" for i in range(num_clusters)]

    data = [
        (ticker, centroida, time)
        for ticker in tickers
        for centroida in centroids_names
        for time in dates
    ]

    # Create DataFrame
    output_df = pd.DataFrame(data, columns=["ticker", "centroid", "date"])

    long_list = list(itertools.chain.from_iterable(res[:days] for res in result))

    output_df["distance"] = long_list

    output_df = output_df.set_index(["ticker", "date"])

    output_df = output_df.reset_index().pivot_table(
        index=["ticker", "date"], columns="centroid", values="distance"
    )

    output_df.columns = [col for col in output_df.columns]

    # Resetting the index of wide_df to turn MultiIndex into columns
    output_df = output_df.reset_index()

    # Merging wide_df with dict_df
    output_df = pd.merge(output_df, dicat_df, left_on="ticker", right_on="tickers")

    # Dropping the 'tickers' column
    output_df = output_df.drop(columns="tickers")

    # Re-setting the MultiIndex with 'ticker' and 'date'
    output_df.set_index(["ticker", "date"], inplace=True)

    output_df["labels"] = output_df["labels"].apply(lambda x: f"Centroid {int(x)}")

    # Group by 'ticker' and sum across rows
    summed_series = output_df.groupby("ticker").sum(numeric_only=True).sum(axis=1)

    # Find the indices where the value is 0.00
    zero_indices = summed_series[summed_series == 0.00].index.tolist()

    print(
        f"We will remove {len(zero_indices)} tickers for which sufficient data does not exist, they are probably delisted"
    )

    mask = ~output_df.index.get_level_values("ticker").isin(zero_indices)

    # Apply the mask to filter the DataFrame
    output_df = output_df[mask]
    return output_df


import pandas as pd
from datetime import timedelta


def calculate_mean_last_6_months(df, ticker, latest_date):
    six_months_ago = latest_date - timedelta(days=180)
    df_last_6_months = df.loc[ticker].loc[six_months_ago:latest_date]
    return df_last_6_months.mean(numeric_only=True)


def cluster_summary(df_mega):

    merged_df = cluster(df_mega)

    # Prepare the latest values
    latest_values = (
        merged_df.reset_index()
        .groupby("ticker")
        .last()
        .reset_index()
        .set_index(["ticker", "date"])
    )

    divergence_values = []

    for ticker in latest_values.index.get_level_values("ticker").unique():
        latest_date = merged_df.loc[ticker].index[-1]
        mean_last_6_months = calculate_mean_last_6_months(
            merged_df, ticker, latest_date
        )
        latest_label = latest_values.loc[(ticker, latest_date), "labels"]
        latest_value = merged_df.loc[(ticker, latest_date), latest_label]
        mean_value = mean_last_6_months[latest_label]

        divergence = ((latest_value - mean_value) * 100) if mean_value != 0 else None
        divergence_values.append((ticker, divergence))

    # Convert divergence_values to a DataFrame
    divergence_df = pd.DataFrame(
        divergence_values, columns=["ticker", "Divergence"]
    ).set_index("ticker")
    add_df = (
        latest_values.reset_index().set_index("ticker").join(divergence_df, how="left")
    )

    # Continue with the rest of your calculations...

    centroid_cols = [col for col in merged_df.columns if "Centroid" in col]

    # Calculate standard deviation for each ticker for all Centroid columns
    std_devs_per_ticker = (
        merged_df[centroid_cols].groupby(level="ticker").std(numeric_only=True)
    )

    # Calculate the average standard deviation for each ticker
    avg_std_dev_per_ticker = std_devs_per_ticker.mean(axis=1)

    avg_std_dev_per_ticker

    last_data_points = merged_df.reset_index().groupby("ticker")[centroid_cols].last()

    avg_corr = last_data_points.abs().mean(axis=1)

    centroid_cols = [col for col in merged_df.columns if "Centroid" in col]

    # Calculate rolling means for each ticker
    rolling_means = (
        merged_df[centroid_cols]
        .groupby(level="ticker")
        .rolling(window=26, min_periods=1)
        .mean()
    )

    rolling_means = rolling_means.droplevel(level=0)

    latest_values = merged_df.groupby(level="ticker").tail(1)

    # Calculate the differences between the latest values and the rolling means
    latest_minus_rolling_mean = latest_values[centroid_cols].reset_index(
        level="date", drop=True
    ) - rolling_means.groupby(level="ticker").tail(1)

    latest_minus_rolling_mean

    # Most Growing and Falling Centroid for each ticker
    growing_centroids = latest_minus_rolling_mean.idxmax(axis=1)
    falling_centroids = latest_minus_rolling_mean.idxmin(axis=1)

    # Extract corresponding change values for growing and falling centroids
    growing_change = latest_minus_rolling_mean.max(axis=1) * 100
    falling_change = latest_minus_rolling_mean.min(axis=1) * 100

    # Format the values and centroid names into a single string
    latest_values["Growing Centroid"] = (
        growing_centroids + " (" + growing_change.apply(lambda x: f"{x:+.2f}") + "%)"
    )
    latest_values["Falling Centroid"] = (
        falling_centroids + " (" + falling_change.apply(lambda x: f"{x:+.2f}") + "%)"
    )

    combined_df = pd.DataFrame(
        {
            "Cluster": add_df["labels"],
            "Divergence": add_df["Divergence"],
            "Growing Centroid": latest_values.reset_index().set_index("ticker")[
                "Growing Centroid"
            ],
            "Falling Centroid": latest_values.reset_index().set_index("ticker")[
                "Falling Centroid"
            ],
            "Average Standard Deviation": avg_std_dev_per_ticker,
            "Average Correlation": avg_corr,
        }
    )
    return combined_df


import pandas as pd
import numpy as np


def feature_cent(df_mega, select_features=None):
    (
        idx,
        centroids,
        distances,
        result,
        tickers,
        features,
        dates,
        dicat_df,
        num_clusters,
    ) = segment_series(df_mega, select_features)

    centroids_names = [f"Centroid {i}" for i in range(num_clusters)]

    num_centroids, num_dates, num_features = centroids.shape

    # Reshape the array to match the new MultiIndex order
    reshaped_centroids = centroids.transpose(2, 1, 0).reshape(
        num_features * num_dates, num_centroids
    )

    # Create a MultiIndex with features first, then dates
    multi_index = pd.MultiIndex.from_product(
        [features, dates], names=["feature", "date"]
    )

    # Create the DataFrame with the new MultiIndex
    cent_df = pd.DataFrame(
        reshaped_centroids, index=multi_index, columns=centroids_names
    )
    return cent_df


import dash
from dash import html, dcc, Input, Output, State, callback_context
import plotly.express as px
import pandas as pd
import numpy as np


def vizualisation_cluster(df_mega):
    # Assuming you've already run this:
    # idx, centroids, distances, result, tickers, features, dates, dicat_df, num_clusters = segment_series(df_mega)

    cent_df = feature_cent(df_mega)

    merged_df = cluster(df_mega)

    # Initialize the Dash app
    app = dash.Dash(__name__)

    def create_initial_plot():
        filtered_df = merged_df[merged_df["labels"] == "Centroid 0"]
        fig = px.line(
            filtered_df.reset_index(), x="date", y="Centroid 0", color="ticker"
        )
        return fig

    # Set up the app layout
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Select Clusters:", style={"marginRight": "10px"}
                            ),
                            dcc.Dropdown(
                                id="centroid-dropdown",
                                options=[
                                    {"label": i, "value": i}
                                    for i in sorted(merged_df["labels"].unique())
                                ],
                                value="Centroid 0",
                                placeholder="Sort by Centroid",
                                style={"width": "80%"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "width": "32%",
                            "marginRight": "2%",
                        },
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Select Tickers:", style={"marginRight": "10px"}
                            ),
                            dcc.Dropdown(
                                id="ticker-dropdown",
                                options=[
                                    {"label": i, "value": i}
                                    for i in merged_df.index.get_level_values(
                                        "ticker"
                                    ).unique()
                                ],
                                value=None,
                                placeholder="Sort by Ticker",
                                style={"width": "80%"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "width": "32%",
                            "marginRight": "2%",
                        },
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Select Feature:", style={"marginRight": "10px"}
                            ),
                            dcc.Dropdown(
                                id="feature-dropdown",
                                options=[
                                    {"label": i, "value": i}
                                    for i in cent_df.index.get_level_values(0).unique()
                                ],
                                value=None,  # Changed from initial value to None
                                placeholder="Select Feature",
                                style={"width": "80%"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "width": "32%",
                        },
                    ),
                ],
                style={"display": "flex", "marginBottom": "15px"},
            ),
            dcc.Graph(id="line-plot", figure=create_initial_plot()),
        ]
    )

    @app.callback(
        Output("line-plot", "figure"),
        Output("centroid-dropdown", "value"),
        Output("ticker-dropdown", "value"),
        Output("feature-dropdown", "value"),
        Input("centroid-dropdown", "value"),
        Input("ticker-dropdown", "value"),
        Input("feature-dropdown", "value"),
    )
    def update_graph(selected_centroid, selected_ticker, selected_feature):
        ctx = callback_context
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if input_id == "centroid-dropdown" and selected_centroid:
            filtered_df = merged_df[merged_df["labels"] == selected_centroid]
            fig = px.line(
                filtered_df.reset_index(), x="date", y=selected_centroid, color="ticker"
            )
            return fig, selected_centroid, None, None
        elif input_id == "ticker-dropdown" and selected_ticker:
            filtered_df = merged_df.xs(selected_ticker, level="ticker")
            fig = px.line(
                filtered_df.reset_index(),
                x="date",
                y=filtered_df.columns.drop("labels"),
            )
            return fig, None, selected_ticker, None
        elif input_id == "feature-dropdown" and selected_feature:
            filtered_df = cent_df.xs(selected_feature, level=0)
            fig = px.line(filtered_df, x=filtered_df.index, y=filtered_df.columns)
            return fig, None, None, selected_feature

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    app_name = "clustering-app"
    return app.run(
        debug=False, port=get_unique_port(app_name)
    )  # Apply exponential moving average to smooth the data


import dash
from dash import html, dcc, Input, Output, State
import plotly.express as px
import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Assuming df_mega is your original DataFrame and it has a cluster method


def vizualisation_scatter(df_mega):

    app = dash.Dash(__name__)

    features = [
        {"label": col, "value": col}
        for col in df_mega.columns
        if col
        not in [
            "Centroid 0",
            "Centroid 1",
            "Centroid 2",
            "Centroid 3",
            "Centroid 4",
            "Centroid 5",
            "Centroid 6",
            "Centroid 7",
            "labels",
        ]
    ]

    features.append({"label": "All Features", "value": "All Features"})

    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Select Feature:"),
                            dcc.Dropdown(
                                id="feature-dropdown",
                                options=features,
                                value="All Features",
                            ),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline-block",
                            "marginRight": "3%",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("X-axis Centroid:"),
                            dcc.Dropdown(
                                id="x-centroid-dropdown",
                                options=[
                                    {"label": f"Centroid {i}", "value": f"Centroid {i}"}
                                    for i in range(8)
                                ],
                                value="Centroid 0",
                            ),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline-block",
                            "marginRight": "3%",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("Y-axis Centroid:"),
                            dcc.Dropdown(
                                id="y-centroid-dropdown",
                                options=[
                                    {"label": f"Centroid {i}", "value": f"Centroid {i}"}
                                    for i in range(8)
                                ],
                                value="Centroid 4",
                            ),
                        ],
                        style={"width": "30%", "display": "inline-block"},
                    ),
                ],
                style={"marginBottom": "20px"},
            ),
            html.Div(
                [
                    html.Label("Select Date:"),
                    dcc.Slider(
                        id="date-slider",
                        min=0,
                        max=len(df_mega.index.get_level_values("date").unique()) - 1,
                        value=len(df_mega.index.get_level_values("date").unique()) - 1,
                        marks={
                            i: ""
                            for i in range(
                                len(df_mega.index.get_level_values("date").unique())
                            )
                        },
                        step=None,
                    ),
                ],
                style={"marginBottom": "20px"},
            ),
            dcc.Graph(id="scatter-plot"),
        ]
    )

    @app.callback(
        Output("scatter-plot", "figure"),
        [
            Input("feature-dropdown", "value"),
            Input("x-centroid-dropdown", "value"),
            Input("y-centroid-dropdown", "value"),
            Input("date-slider", "value"),
        ],
    )
    def update_graph(selected_feature, x_centroid, y_centroid, selected_date_index):
        # Suppress print statements
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        if selected_feature == "All Features":
            df_cluster = df_mega.cluster()

            # Restore stdout
            sys.stdout = old_stdout

            # Get the selected date
            selected_date = sorted(df_mega.index.get_level_values("date").unique())[
                selected_date_index
            ]

            # Filter the DataFrame for the selected date
            filtered_df = df_cluster.loc[
                pd.IndexSlice[:, selected_date], :
            ].reset_index()

            # Create the scatter plot
            fig = px.scatter(
                filtered_df,
                x=x_centroid,
                y=y_centroid,
                color="labels",
                hover_data=["ticker"],
                title=f"{selected_feature} - {selected_date}",
            )
            fig.update_traces(
                hovertemplate='<b><span style="font-size: 120%">%{customdata[0]}</span></b><br><br>'
                + f"{x_centroid}: "
                + "%{x}<br>"
                + f"{y_centroid}: "
                + "%{y}<br>"
            )
        else:
            # Recalculate clustering for the selected feature
            df_cluster = df_mega.cluster(features=[selected_feature])

            # Restore stdout
            sys.stdout = old_stdout

            # Get the selected date
            selected_date = sorted(df_mega.index.get_level_values("date").unique())[
                selected_date_index
            ]

            # Filter the DataFrame for the selected date
            filtered_df = df_cluster.loc[
                pd.IndexSlice[:, selected_date], :
            ].reset_index()

            # Merge with original df_mega to get the selected feature
            filtered_df = filtered_df.merge(
                df_mega.loc[
                    pd.IndexSlice[:, selected_date], [selected_feature]
                ].reset_index(),
                on=["ticker", "date"],
            )

            # Create the scatter plot
            fig = px.scatter(
                filtered_df,
                x=x_centroid,
                y=y_centroid,
                color="labels",
                hover_data=["ticker", selected_feature],
                title=f"{selected_feature} - {selected_date}",
            )
            fig.update_traces(
                hovertemplate='<b><span style="font-size: 120%">%{customdata[0]}</span></b><br><br>'
                + f"{x_centroid}: "
                + "%{x}<br>"
                + f"{y_centroid}: "
                + "%{y}<br>"
                + f"{selected_feature}: "
                + "%{customdata[1]:.6f}<br>"
            )

        # Increase marker size
        fig.update_traces(marker=dict(size=10))

        fig.update_layout(transition_duration=500)

        return fig

    app_name = "scatter-app"
    return app.run(
        debug=False, port=get_unique_port(app_name)
    )  # Apply exponential moving average to smooth the data


import dash
from dash import html, dcc, Input, Output, callback_context
import plotly.express as px
import pandas as pd


def vizualisation_animation(df_mega):
    app = dash.Dash(__name__)

    features = [
        {"label": col, "value": col}
        for col in df_mega.columns
        if col
        not in [
            "Centroid 0",
            "Centroid 1",
            "Centroid 2",
            "Centroid 3",
            "Centroid 4",
            "Centroid 5",
            "Centroid 6",
            "Centroid 7",
            "labels",
        ]
    ]
    features.append({"label": "All Features", "value": "All Features"})

    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Select Feature:"),
                            dcc.Dropdown(
                                id="feature-dropdown",
                                options=features,
                                value="All Features",
                            ),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline-block",
                            "marginRight": "3%",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("X-axis Centroid:"),
                            dcc.Dropdown(
                                id="x-centroid-dropdown",
                                options=[
                                    {"label": f"Centroid {i}", "value": f"Centroid {i}"}
                                    for i in range(8)
                                ],
                                value="Centroid 0",
                            ),
                        ],
                        style={
                            "width": "30%",
                            "display": "inline-block",
                            "marginRight": "3%",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("Y-axis Centroid:"),
                            dcc.Dropdown(
                                id="y-centroid-dropdown",
                                options=[
                                    {"label": f"Centroid {i}", "value": f"Centroid {i}"}
                                    for i in range(8)
                                ],
                                value="Centroid 4",
                            ),
                        ],
                        style={"width": "30%", "display": "inline-block"},
                    ),
                ],
                style={"marginBottom": "20px"},
            ),
            dcc.Graph(id="scatter-plot"),
        ]
    )

    @app.callback(
        Output("scatter-plot", "figure"),
        Input("feature-dropdown", "value"),
        Input("x-centroid-dropdown", "value"),
        Input("y-centroid-dropdown", "value"),
    )
    def update_graph(selected_feature, x_centroid, y_centroid):
        if selected_feature == "All Features":
            df_cluster = df_mega.cluster()
        else:
            df_cluster = df_mega.cluster(features=[selected_feature])

        df_cluster_reset = df_cluster.reset_index()
        df_cluster_reset["date"] = pd.to_datetime(df_cluster_reset["date"]).dt.strftime(
            "%Y-%m-%d"
        )

        if selected_feature != "All Features":
            df_mega_reset = df_mega.reset_index()
            df_mega_reset["date"] = pd.to_datetime(df_mega_reset["date"]).dt.strftime(
                "%Y-%m-%d"
            )
            df_cluster_reset = df_cluster_reset.merge(
                df_mega_reset[[selected_feature, "ticker", "date"]],
                on=["ticker", "date"],
            )

        hover_data = ["ticker"]
        if selected_feature != "All Features":
            hover_data.append(selected_feature)

        fig = px.scatter(
            df_cluster_reset,
            x=x_centroid,
            y=y_centroid,
            color="labels",
            hover_data=hover_data,
            animation_frame="date",
            animation_group="ticker",
            title=f"{selected_feature} - Animated over time",
        )

        # Customize hover template
        hovertemplate = (
            '<b><span style="font-size: 120%">%{customdata[0]}</span></b><br><br>'
            + f"{x_centroid}: "
            + "%{x}<br>"
            + f"{y_centroid}: "
            + "%{y}<br>"
        )

        if selected_feature != "All Features":
            hovertemplate += f"{selected_feature}: " + "%{customdata[1]:.6f}<br>"

        fig.update_traces(hovertemplate=hovertemplate, marker=dict(size=10))

        # Customize animation settings
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 100
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 50

        # Dynamic axis scaling
        x_ranges = {}
        y_ranges = {}
        for date in df_cluster_reset["date"].unique():
            date_data = df_cluster_reset[df_cluster_reset["date"] == date]
            x_ranges[date] = [date_data[x_centroid].min(), date_data[x_centroid].max()]
            y_ranges[date] = [date_data[y_centroid].min(), date_data[y_centroid].max()]

        for f in fig.frames:
            if f.name in x_ranges and f.name in y_ranges:
                f.layout.update(
                    xaxis_range=x_ranges[f.name], yaxis_range=y_ranges[f.name]
                )

        return fig

    app_name = "animation-app"
    return app.run(debug=False, port=get_unique_port(app_name))
