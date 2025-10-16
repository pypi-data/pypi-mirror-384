import pandas as pd
from MFLES.Forecaster import fit_from_df

import plotly.express as px

from MFLES.Forecaster import fit_from_df
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import plotly.figure_factory as ff

import os
import sys
import contextlib

# from halo import Halo


class nowcast:
    def __init__(self, df_signal):
        self.df_signal = df_signal.reset_index()
        self.starting_feature = self.determine_starting_feature()

    def calculate_scaling_factor(self, percentage_diff):
        # Define the function as before
        base_multiplier = 2
        scaling_factor = 0.01
        return base_multiplier + scaling_factor * percentage_diff

    def determine_starting_feature(self):
        # Filter numeric columns
        numeric_cols = self.df_signal.select_dtypes(include="number").columns

        # Calculate coefficient of variation (CV) for each numeric column
        cv = {
            col: self.df_signal[col].std() / self.df_signal[col].mean()
            for col in numeric_cols
            if self.df_signal[col].mean() != 0
        }

        # Find the column with the highest CV
        return max(cv, key=cv.get, default=None)

    def scale_predictions(self, group, selected_feature):
        # Extract the ticker from the group
        ticker = group["ticker"].iloc[0]

        # Use self.df_signal to get the last actual value and last date for this ticker
        df_signal_group = self.df_signal[self.df_signal["ticker"] == ticker]
        last_date = df_signal_group["date"].iloc[-1]
        last_actual_value = df_signal_group[selected_feature].iloc[-1]

        # Check if there are predicted values after the last date
        if any(group["date"] > last_date):
            last_predicted_value = group.loc[group["date"] > last_date, "mfles"].iloc[
                -1
            ]
            percentage_difference = (
                abs((last_predicted_value - last_actual_value) / last_actual_value)
                * 100
            )
            scaling_factor = self.calculate_scaling_factor(percentage_difference)

            # Apply scaling to predictions after the last actual value date
            group.loc[group["date"] > last_date, "mfles"] = group.loc[
                group["date"] > last_date, "mfles"
            ].apply(
                lambda x: ((scaling_factor - 1) * last_actual_value + x)
                / scaling_factor
            )

        return group

    @contextlib.contextmanager
    def suppress_output(self):
        # Redirect standard output and error to null
        with open(os.devnull, "w") as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    def get_data(self, selected_tickers=None, selected_feature=None):
        # Use entire DataFrame if no specific tickers are selected
        if selected_tickers is not None:
            filtered_df = self.df_signal[
                self.df_signal["ticker"].isin(selected_tickers)
            ]
        else:
            filtered_df = self.df_signal

        # Default to a single feature if none are selected
        if selected_feature is None:
            selected_feature = self.df_signal.columns.difference(["date", "ticker"])[0]

        # Run time consuming work here
        # You can also change properties for spinner as and when you want

        # spinner = Halo(text="", spinner={"interval": 1000, "frames": ["ˢᵒᵛ"]})
        # spinner.start()
        with self.suppress_output():
            # Fit the forecaster for the selected feature
            output = fit_from_df(
                filtered_df,
                forecast_horizon=210,
                freq="W",
                seasonal_period=[13, 26, 52, 104, 210, 420, 840],
                id_column="ticker",
                time_column="date",
                value_column=selected_feature,
                floor=0,
            ).reset_index(drop=True)

            # Apply scaling to the predictions
            scaled_output = output.groupby("ticker", group_keys=False).apply(
                lambda group: self.scale_predictions(group, selected_feature)
            )
        spinner.stop()

        scaled_output["mfles"] = scaled_output["mfles"].clip(lower=0)

        return scaled_output.rename(columns={"mfles": "nowcast"})

    def plot(self, selected_tickers=None, selected_feature=None):

        if selected_tickers is not None:
            filtered_df = self.df_signal[
                self.df_signal["ticker"].isin(selected_tickers)
            ]
        else:
            filtered_df = self.df_signal

        def get_top_16_firms(df):
            last_date = df["date"].max()
            top_firms = (
                df[df["date"] == last_date]
                .sort_values(by=self.starting_feature, ascending=False)
                .head(12)["ticker"]
                .unique()
            )
            return top_firms

        # Get the initial list of top 16 tickers
        initial_top_tickers = get_top_16_firms(filtered_df)

        # Function to create correlation heatmap
        import scipy.cluster.hierarchy as sch

        def corr_map(df_wide):

            # Calculate the correlation matrix
            dfc = df_wide.corr()

            # Perform hierarchical clustering
            linkage = sch.linkage(sch.distance.pdist(dfc), method="average")

            # Get the order of the dendrogram leaves
            dendro = sch.dendrogram(linkage, no_plot=True)
            order = dendro["leaves"]

            # Reorder the correlation matrix
            dfc = dfc.iloc[order, order]

            # dfc = dfc.iloc[::-1]  # Reverse the order of rows

            # dfc = dfc.iloc[::-1, ::-1]

            z = dfc.values
            z_text = [[str(round(y, 2)) for y in x] for x in z]

            # Create the heatmap
            fig = ff.create_annotated_heatmap(
                z,
                x=dfc.columns.tolist(),
                y=dfc.columns.tolist(),
                annotation_text=z_text,
                colorscale="Blues",
                xgap=10,
                ygap=6,
            )

            # Set the height of the figure
            fig.update_layout(height=750)

            return fig

        # Initialize Dash app
        app = dash.Dash(__name__)

        app.layout = html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="feature-dropdown",
                            options=[
                                {"label": col, "value": col}
                                for col in filtered_df.columns
                                if col not in ["date", "ticker"]
                            ],
                            value=self.starting_feature,
                            style={"flex": "1", "margin": "5px"},
                        ),
                        dcc.Dropdown(
                            id="ticker-dropdown",
                            options=[
                                {"label": ticker, "value": ticker}
                                for ticker in filtered_df["ticker"].unique()
                            ],
                            value=initial_top_tickers,
                            multi=True,
                            style={"flex": "3", "margin": "5px"},
                        ),
                        dcc.Checklist(
                            id="toggle-predictions",
                            options=[
                                {"label": "Show Only Predictions", "value": "only_pred"}
                            ],
                            value=[],
                            style={
                                "flex": "1",
                                "margin": "5px",
                                "margin-top": "15px",
                                "margin-left": "15px",
                            },
                        ),
                        dcc.Checklist(
                            id="correlation-heatmap-toggle",
                            options=[
                                {
                                    "label": "Show Correlation Heatmap",
                                    "value": "show_corr",
                                }
                            ],
                            value=[],
                            style={"flex": "1", "margin": "5px", "margin-top": "15px"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "margin": "0px",
                        "boxSizing": "border-box",
                    },
                ),
                dcc.Loading(
                    id="loading-1",
                    type="default",
                    children=html.Div(dcc.Graph(id="feature-graph")),
                ),
                dcc.Store(id="stored-predictions"),
            ],
            style={"padding": "0px", "margin": "0px", "boxSizing": "border-box"},
        )

        # Callback to update graph based on selected feature
        @app.callback(
            Output("stored-predictions", "data"),
            [
                Input("feature-dropdown", "value"),
                Input("ticker-dropdown", "value"),
            ],  # Add Input for ticker dropdown
        )
        def store_predictions(selected_feature, selected_tickers):
            # Filter df_signal based on selected tickers
            output = self.get_data(selected_tickers, selected_feature)

            return output.to_json(date_format="iso", orient="split")

        @app.callback(
            Output("feature-graph", "figure"),
            [
                Input("stored-predictions", "data"),
                Input("toggle-predictions", "value"),
                Input("correlation-heatmap-toggle", "value"),
            ],
            State("feature-dropdown", "value"),
        )
        def update_graph(
            stored_data, toggle_state, corr_toggle_state, selected_feature
        ):
            output = (
                pd.read_json(stored_data, orient="split")
                if stored_data
                else pd.DataFrame()
            )
            today = datetime.now()

            print(corr_toggle_state)

            # If the correlation heatmap is to be shown
            if "show_corr" in corr_toggle_state and not output.empty:
                # If only predictions are to be shown, filter the data accordingly
                if "only_pred" not in toggle_state:
                    output = output[output["date"] >= today]

                df_wide = output.pivot(
                    index="date", columns="ticker", values="nowcast"
                ).dropna(axis=1)
                print(df_wide.head())
                return corr_map(df_wide)

            # For the non-heatmap part, if only predictions are to be shown, filter the data
            if "only_pred" in toggle_state:
                output = output[output["date"] >= today]

            # Check if any data is left after filtering
            if output.empty:
                return go.Figure()  # Return an empty figure if no data is available

            tickers = output["ticker"].unique()
            num_tickers = len(tickers)
            cols = min(
                4, num_tickers
            )  # Use a maximum of 4 columns or fewer if less tickers
            rows = -(-num_tickers // cols)  # Calculate the number of rows needed

            fig = make_subplots(rows=rows, cols=cols, subplot_titles=tickers)
            color_palette = px.colors.qualitative.Plotly

            for idx, ticker in enumerate(tickers):
                color = color_palette[idx % len(color_palette)]
                ticker_data = output[output["ticker"] == ticker]
                actual_data = ticker_data[ticker_data["date"] < today]
                prediction_data = ticker_data[ticker_data["date"] >= today]

                row_idx = (idx // cols) + 1
                col_idx = (idx % cols) + 1

                if "only_pred" not in toggle_state:
                    fig.add_trace(
                        go.Scatter(
                            x=actual_data["date"],
                            y=actual_data["nowcast"],
                            mode="lines",
                            name=f"{ticker} - Actual",
                            line=dict(color=color),
                        ),
                        row=row_idx,
                        col=col_idx,
                    )

                if not prediction_data.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=prediction_data["date"],
                            y=prediction_data["nowcast"],
                            mode="lines",
                            name=f"{ticker} - Predicted",
                            line=dict(color=color, dash="dot"),
                        ),
                        row=row_idx,
                        col=col_idx,
                    )

            title = (
                " ".join(word.capitalize() for word in selected_feature.split("_"))
                + " Nowcasted for Each Ticker"
            )
            fig.update_layout(
                height=300 * rows,
                title_text=title,
                template="plotly_dark",
                showlegend=False,
            )

            return fig

        app.run(debug=True)
