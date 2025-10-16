import pandas as pd
import numpy as np


# from extensions.pfa_feature_selector import PFA ## # ## ### 

# from sovai.extensions.pfa_feature_selector import run_pfa_simulations
pd.options.display.float_format = "{:.3f}".format


# from sovai.extensions.shapley_importance import run_simulations_frame


import warnings

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Pandas doesn't allow columns to be created via a new attribute name",
)

# df_accounting.anomalies("scores", "AAPL")
# df_accounting.anomalies("local", "AAPL")
# df_accounting.anomalies("global", "AAPL")
# df_accounting.anomalies("cluster", "AAPL")
# df_accounting.anomalies("reconstruction", "AAPL")


from dateutil import parser
import pandas as pd

import pandas as pd
from typing import Union, List
# from sovai.extensions.ask_df_llm import Ask

import pandas as pd
from functools import lru_cache
import re
from typing import Union, Tuple

class CustomDataFrame(pd.DataFrame):
    @property
    def _constructor(self):
        # Ensures that pandas operations return CustomDataFrame objects
        return CustomDataFrame

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If the original DataFrame had attrs, copy them
        if len(args) > 0 and isinstance(args[0], pd.DataFrame):
            self.attrs = args[0].attrs.copy()

    def filter(self, conditions: Union[str, List[str]], verbose: bool = False) -> 'CustomDataFrame':
        """
        Filter the DataFrame based on given conditions.
        :param conditions: A string or list of strings describing the filtering conditions.
        :param verbose: If True, print detailed information about the filtering process.
        :return: A filtered CustomDataFrame.
        """

        from sovai.extensions.filter_df import Filter

        filtered_df = Filter.filter(conditions, df_multi=self, verbose=verbose)
        return CustomDataFrame(filtered_df)
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _load_combined_df():
        df = pd.read_parquet("https://storage.googleapis.com/sovai-public/concats/filters/latest.parquet")
        # print("Columns in combined DataFrame:", df.columns)  # Debug print
        # print("Index name:", df.index.name)  # Debug print for index name
        return df
    
    def merge_data(self, column: str) -> 'CustomDataFrame':
        """
        Merge the current DataFrame with the combined DataFrame based on ticker and a specified column.
        
        :param column: The column from the combined DataFrame to merge.
        :return: A new CustomDataFrame with the merged data.
        """
        # Load the combined DataFrame
        df_combined = self._load_combined_df()
        
        # Ensure the specified column exists in the combined DataFrame
        if column not in df_combined.columns:
            raise ValueError(f"Column '{column}' not found in the combined DataFrame.")
        
        # Identify the ticker information in the current DataFrame
        ticker_info = self._identify_ticker_info()
        
        # Prepare the current DataFrame for merging
        df_to_merge = self.copy()
        if ticker_info[0] != 'column':
            df_to_merge = df_to_merge.reset_index()
        
        # Standardize ticker format in the current DataFrame
        
        # Prepare the combined DataFrame for merging
        df_combined_merged = df_combined.reset_index()
        
        # Perform the merge
        merged_df = pd.merge(df_to_merge, df_combined_merged[['ticker', column]], 
                             left_on=ticker_info[1], right_on='ticker', 
                             how='left')
        
        # Drop the redundant 'ticker' column from the merge if it's not the original ticker column
        if 'ticker' in merged_df.columns and 'ticker' != ticker_info[1]:
            merged_df = merged_df.drop('ticker', axis=1)
        
        # Restore the original index structure
        if ticker_info[0] == 'index':
            merged_df = merged_df.set_index(ticker_info[1])
        elif ticker_info[0] == 'multi_index':
            index_cols = [col for col in df_to_merge.columns if col not in self.columns]
            merged_df = merged_df.set_index(index_cols)
        
        return CustomDataFrame(merged_df)
    
    def _identify_ticker_info(self) -> Tuple[str, str]:
        """
        Identify the location and name of ticker information in the DataFrame.
        
        :return: A tuple of (location, column_name).
                 Location can be 'index', 'multi_index', or 'column'.
        """
        # Check if ticker is in the index
        if self.index.name and 'ticker' in self.index.name.lower():
            return ('index', self.index.name)
        elif isinstance(self.index, pd.MultiIndex):
            for name in self.index.names:
                if name and 'ticker' in name.lower():
                    return ('multi_index', name)
        
        # If ticker is not in the index, check the columns
        for col in self.columns:
            if 'ticker' in col.lower():
                return ('column', col)
        
        raise ValueError("Couldn't identify ticker information in the DataFrame.")
    
    
    def get_latest(self, column=None):
        # Your get_latest implementation
        if isinstance(self.index, pd.MultiIndex) and "date" in self.index.names:
            latest_date = self.index.get_level_values("date").max()
            latest_data = self.loc[self.index.get_level_values("date") == latest_date]
        elif "date" == self.index.name:
            latest_date = self.index.max()
            latest_data = self.loc[self.index == latest_date]
        elif "date" in self.columns:
            latest_date = self["date"].max()
            latest_data = self.loc[self["date"] == latest_date]
        else:
            raise ValueError(
                "The DataFrame does not contain a 'date' in its index or columns."
            )

        if column:
            return CustomDataFrame(latest_data.sort_values(column, ascending=False))
        elif "prediction" in latest_data.columns:
            return CustomDataFrame(
                latest_data.sort_values("prediction", ascending=False)
            )

        else:
            return CustomDataFrame(latest_data)

    def plot_line(self, column=None, tickers=None, n=50):
        import plotly.express as px
        # Your plot_line implementation
        if isinstance(self.index, pd.MultiIndex):
            df = self.reset_index()
        else:
            df = self

        if "date" in df.columns:
            x_axis = "date"
        elif isinstance(df.index, pd.DatetimeIndex):
            x_axis = df.index
            df = df.reset_index()
        else:
            raise ValueError("No 'date' column or index found in DataFrame.")

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

        if "ticker" in df.columns and tickers:
            if isinstance(tickers, list):
                df_to_plot = df[df["ticker"].isin(tickers)]
            else:
                df_to_plot = df[df["ticker"] == tickers]
        elif "ticker" in df.columns:
            available_tickers = df["ticker"].unique()
            tickers_to_plot = np.random.choice(
                available_tickers, size=min(n, len(available_tickers)), replace=False
            )
            df_to_plot = df[df["ticker"].isin(tickers_to_plot)]
            print("Plotting for random tickers. Specify tickers to plot specific data.")
        else:
            df_to_plot = df

        fig = px.line(
            df_to_plot,
            x=x_axis,
            y=column,
            color="ticker" if "ticker" in df.columns else None,
            title=f"Line Plot of {column}",
        )
        return fig.show()

    def percentile(self, on="date"):
        # Your percentile implementation
        if on not in ["date", "ticker", "all"]:
            raise ValueError("Parameter 'on' must be 'date', 'ticker', or 'all'.")

        if on in ["date", "ticker"]:
            if on in self.columns or on in self.index.names:
                df_percentile = self.groupby(on).transform(lambda x: x.rank(pct=True))
            else:
                raise ValueError(
                    f"'{on}' not found in DataFrame columns or index names."
                )
        elif on == "all":
            df_percentile = self.rank(pct=True)

        df_percentile = df_percentile.replace([np.inf, -np.inf], np.nan)
        df_percentile = df_percentile.fillna(0.5)
        return CustomDataFrame(df_percentile)

    def distance(
        self,
        orient="cross-sectional",
        on="ticker",
        distance="cosine",
        metric="pearson",
        calculations=["mean"],
    ):
        
        from sovai.extensions.pairwise import distance_calc

        result = distance_calc(
            self,
            orient=orient,
            on=on,
            distance=distance,
            metric=metric,
            calculations=calculations,
        )
        return CustomDataFrame(result)
    
    def relative_distance(
        self,
        orient="cross-sectional",
        on="ticker",
        distance="cosine",
        metric="pearson",
        calculations=["mean"],
    ):
        
        from sovai.extensions.pairwise import distance_calc, relative_distance_calc

        result = relative_distance_calc(
            self,
            orient=orient,
            on=on,
            distance=distance,
            metric=metric,
            calculations=calculations,
        )
        return CustomDataFrame(result)

    def cluster(self, orient="cluster", features=None):

        from sovai.extensions.clustering import (
            cluster,
            cluster_summary,
            feature_cent,
            vizualisation_cluster,
            vizualisation_scatter,
            vizualisation_animation,
        )
        if orient == "cluster":
            result = cluster(self, features)
        elif orient == "summary":
            result = cluster_summary(self)
        elif orient == "feature":
            result = feature_cent(self)
        elif orient == "line_plot":
            result = vizualisation_cluster(self)
            return result
        elif orient == "scatter_plot":
            result = vizualisation_scatter(self)
            return result
        elif orient == "animation_plot":
            result = vizualisation_animation(self)
            return result

        return CustomDataFrame(result)


    import numpy as np
    import pandas as pd


    def cointegration(self, on="ticker", shift=12):

        """
        Calculate an approximate cointegration proxy using shifted cosine similarity.

        :param df: Pandas DataFrame with MultiIndex.
        :param level: The level of the MultiIndex to group by (default 'ticker').
        :param shift: The number of periods to shift for lagged comparison (default 1 month).
        :return: DataFrame of shifted cosine similarities.
        """

        from numpy.linalg import norm

        # Shift the DataFrame by the specified lag
        shifted_df = self.groupby(level=on).shift(-shift)

        # Calculate means of the original and shifted DataFrames
        mean_df = self.groupby(level=on).mean()
        shifted_mean_df = shifted_df.groupby(level=on).mean()

        # Calculate dot products between the original and shifted means
        dot_product = mean_df.values @ shifted_mean_df.values.T
        l2_norm_orig = norm(mean_df.values, axis=1)
        l2_norm_shifted = norm(shifted_mean_df.values, axis=1)

        # Handle cases where the norm is zero (to avoid division by zero)
        l2_norm_orig[l2_norm_orig == 0] = np.nan
        l2_norm_shifted[l2_norm_shifted == 0] = np.nan

        # Calculate cosine similarity
        cosine_similarity = dot_product / np.outer(l2_norm_orig, l2_norm_shifted)

        # cosine_similarity = np.nan_to_num(cosine_similarity, nan=0.5)
        # cosine_similarity = normalize_min_max(cosine_similarity)

        # Convert the similarity array to a DataFrame
        cosine_similarity = pd.DataFrame(
            cosine_similarity * 100, index=mean_df.index, columns=mean_df.index
        )

        return CustomDataFrame(cosine_similarity)


    @staticmethod
    def normalize_min_max(matrix):
        """Apply Min-Max normalization."""
        min_val = np.min(matrix)
        max_val = np.max(matrix)
        return (matrix - min_val) / (max_val - min_val)

    def select_features(
        self, method="random_projection", n_components=None, variability=0.90
    ):
        """
        Selects features based on importance scores from various methods.
        :param method: The method to use for calculating feature importance ('random_projection', 'fourier', 'ica', 'svd', 'sparse_projection').
        :param n_components: Number of components to keep. If specified, this takes precedence over variability.
        :param variability: The explained variance threshold (default 0.90).
        :return: CustomDataFrame with selected features.
        """
        # Get feature importance
        importance_df = self.importance(method)

        if n_components is not None:
            if not isinstance(n_components, int) or n_components <= 0:
                raise ValueError("Number of components must be a positive integer")
            selected_features = importance_df["feature"].head(n_components).tolist()
        else:
            if not 0 < variability <= 1:
                raise ValueError("Variability must be between 0 and 1")

            # Calculate cumulative sum of importance percentages
            total_importance = importance_df["importance"].sum()
            importance_df["cumulative_importance"] = (
                importance_df["importance"].cumsum() / total_importance
            )

            # Select features that explain up to the variability threshold
            selected_features = importance_df[
                importance_df["cumulative_importance"] <= variability
            ]["feature"].tolist()

            # If no features are selected (e.g., if first feature already exceeds variability), select at least one
            if not selected_features:
                selected_features = [importance_df["feature"].iloc[0]]

        # Select the corresponding columns from the original DataFrame
        selected_features_df = self[selected_features]

        return CustomDataFrame(selected_features_df)

    # def feature_importance(self):
    #     """
    #     Computes feature importance using SHAP values based on multiple simulations.

    #     :param num_simulations: The number of simulations to run (default 4).
    #     :param clustering_method: The clustering method to use ('OPTICS' or 'KMeans').
    #     :return: A DataFrame with average SHAP values per feature.
    #     """
    #     # Running the simulations and getting average SHAP values
    #     avg_shap_values = run_simulations(self, num_simulations=4, clustering_method='KMEANS')

    #     return CustomDataFrame(avg_shap_values)

    def orthogonalize_features(self, method="gram_schmidt"):
        from sovai.extensions.feature_neutralizer import orthogonalize_features_function
        
        return CustomDataFrame(orthogonalize_features_function(self, method))

    def importance_reorder(self):
        return CustomDataFrame(self[self.abs().mean().sort_values(ascending=False).index])


    def neutralize_features(self, method="pca"):
        from sovai.extensions.feature_neutralizer import neutralize_features_function
        return CustomDataFrame(neutralize_features_function(self, method))

    def ticker(self, ticker="AAPL"):
        """
        Orthogonalizes the features of the DataFrame using the Gram-Schmidt process.
        :return: CustomDataFrame with orthogonalized features.
        """
        ticker_df = self.query(f"ticker == '{ticker}'")

        return CustomDataFrame(ticker_df)

    def date(self, *date_inputs):
        """
        Selects data for a specific date or date range from the DataFrame.

        :param date_inputs: str or tuple of str or multiple str, the date(s) in any format
        :return: CustomDataFrame with selected data
        """
        if len(date_inputs) == 1:
            date_input = date_inputs[0]
            if isinstance(date_input, str):
                # Single date input
                try:
                    # Attempt to parse the date using dateutil
                    parsed_date = parser.parse(date_input)

                    # Normalize the date format
                    normalized_date = pd.Timestamp(parsed_date).strftime("%Y-%m-%d")

                    # Check if the DataFrame has a MultiIndex or single index
                    if isinstance(self.index, pd.MultiIndex):
                        # Select data for the specified date (MultiIndex)
                        date_df = self.loc[(slice(None), normalized_date), :]
                    else:
                        # Select data for the specified date (single index)
                        date_df = self.loc[normalized_date, :]

                    if date_df.empty:
                        print(f"No data found for date '{date_input}'.")
                        return None

                except ValueError:
                    print(
                        f"Invalid date format: '{date_input}'. Please provide a valid date."
                    )
                    return None

            elif isinstance(date_input, tuple) and len(date_input) == 2:
                # Date range input
                try:
                    # Attempt to parse the start and end dates using dateutil
                    parsed_start_date = parser.parse(date_input[0])
                    parsed_end_date = parser.parse(date_input[1])

                    # Normalize the date formats
                    normalized_start_date = pd.Timestamp(parsed_start_date).strftime(
                        "%Y-%m-%d"
                    )
                    normalized_end_date = pd.Timestamp(parsed_end_date).strftime(
                        "%Y-%m-%d"
                    )

                    # Check if the DataFrame has a MultiIndex or single index
                    if isinstance(self.index, pd.MultiIndex):
                        # Select data within the specified date range (MultiIndex)
                        date_df = self.loc[
                            (
                                slice(None),
                                slice(normalized_start_date, normalized_end_date),
                            ),
                            :,
                        ]
                    else:
                        # Select data within the specified date range (single index)
                        date_df = self.loc[normalized_start_date:normalized_end_date, :]

                    if date_df.empty:
                        print(
                            f"No data found for date range '{date_input[0]}' to '{date_input[1]}'."
                        )
                        return None

                except ValueError:
                    print(
                        f"Invalid date format in range: '{date_input}'. Please provide valid dates."
                    )
                    return None

            else:
                print(
                    "Invalid input format. Please provide a single date or a tuple of two dates."
                )
                return None

        elif len(date_inputs) == 2:
            # Two single-standing date inputs
            try:
                # Attempt to parse the start and end dates using dateutil
                parsed_start_date = parser.parse(date_inputs[0])
                parsed_end_date = parser.parse(date_inputs[1])

                # Normalize the date formats
                normalized_start_date = pd.Timestamp(parsed_start_date).strftime(
                    "%Y-%m-%d"
                )
                normalized_end_date = pd.Timestamp(parsed_end_date).strftime("%Y-%m-%d")

                # Check if the DataFrame has a MultiIndex or single index
                if isinstance(self.index, pd.MultiIndex):
                    # Select data within the specified date range (MultiIndex)
                    date_df = self.loc[
                        (
                            slice(None),
                            slice(normalized_start_date, normalized_end_date),
                        ),
                        :,
                    ]
                else:
                    # Select data within the specified date range (single index)
                    date_df = self.loc[normalized_start_date:normalized_end_date, :]

                if date_df.empty:
                    print(
                        f"No data found for date range '{date_inputs[0]}' to '{date_inputs[1]}'."
                    )
                    return None

            except ValueError:
                print(
                    f"Invalid date format in range: '{date_inputs}'. Please provide valid dates."
                )
                return None

        else:
            print(
                "Invalid input format. Please provide a single date, a tuple of two dates, or two single-standing dates."
            )
            return None

        return CustomDataFrame(date_df)

    def select_stocks(self, market_cap="mega"):
        """
        Select stocks based on market capitalization category.
        
        Args:
            market_cap (str): Market capitalization category (e.g., "mega", "large", "mid", "small")
            
        Returns:
            CustomDataFrame: Filtered dataframe containing only stocks of the specified market cap
        """
        import pandas as pd
        import importlib.resources as pkg_resources
        from io import BytesIO
        
        # Access the parquet file from the package resources
        try:
            with pkg_resources.open_binary('sovai.assets', 'tickers.parq') as f:
                tickers_meta = pd.read_parquet(BytesIO(f.read()))
                
            # Get the list of tickers matching the specified market cap
            tickers = tickers_meta[
                tickers_meta["scalemarketcap"] == market_cap
            ].ticker.to_list()
            
            # Filter the data based on the selected tickers
            filtered_df = self[self.index.get_level_values("ticker").isin(tickers)]
            return CustomDataFrame(filtered_df)
            
        except Exception as e:
            # Handle potential errors gracefully
            print(f"Error loading tickers data: {e}")
            # Return empty dataframe or original depending on your preference
            return CustomDataFrame(self.iloc[0:0])  # Empty dataframe with same structure
    

    def calculate_returns(self, method="simple", log=False):
        df_mega = self[self.index.get_level_values("ticker").notna()]
        df_mega = df_mega["closeadj"].unstack(level="ticker")
        df_mega = df_mega.pct_change(fill_method=None).dropna(axis=0, how="all")
        return CustomDataFrame(df_mega)

    def date_range(self, *date_inputs):
        """
        Selects data for a specific date range from the DataFrame.

        :param date_inputs: str or multiple str, the date(s) in any format
        :return: CustomDataFrame with selected data
        """
        try:
            if len(date_inputs) == 1:
                # Single date input (start date)
                start_date = parser.parse(date_inputs[0])
                end_date = None
            elif len(date_inputs) == 2:
                # Two date inputs (date range)
                start_date = parser.parse(date_inputs[0])
                end_date = parser.parse(date_inputs[1])
            else:
                raise ValueError(
                    "Invalid input. Provide either one date (start date) or two dates (date range)."
                )

            # Normalize the date formats
            normalized_start_date = pd.Timestamp(start_date).strftime("%Y-%m-%d")
            normalized_end_date = (
                pd.Timestamp(end_date).strftime("%Y-%m-%d") if end_date else None
            )

            # Check if the DataFrame has a MultiIndex or single index
            if isinstance(self.index, pd.MultiIndex):
                if end_date:
                    # Select data within the specified date range (MultiIndex)
                    date_df = self.loc[
                        (
                            slice(None),
                            slice(normalized_start_date, normalized_end_date),
                        ),
                        :,
                    ]
                else:
                    # Select data from the start date onwards (MultiIndex)
                    date_df = self.loc[
                        (slice(None), slice(normalized_start_date, None)), :
                    ]
            else:
                if end_date:
                    # Select data within the specified date range (single index)
                    date_df = self.loc[normalized_start_date:normalized_end_date, :]
                else:
                    # Select data from the start date onwards (single index)
                    date_df = self.loc[normalized_start_date:, :]

            if date_df.empty:
                if end_date:
                    print(
                        f"No data found for date range '{normalized_start_date}' to '{normalized_end_date}'."
                    )
                else:
                    print(f"No data found from date '{normalized_start_date}' onwards.")
                return None

            return CustomDataFrame(date_df)

        except ValueError as e:
            print(f"Error: {str(e)}. Please provide valid date(s).")
            return None

    def add_price(self):

        from sovai import data

        df_closeadj = data("market/closeadj", full_history=True).rename({"closeadj": "price"}, axis=1)

        df_merge = self.merge(
            df_closeadj, left_index=True, right_index=True, how="left"
        )

        df_merge.isnull().sum()

        df_merge["price"] = df_merge.groupby(level="ticker")["price"].ffill()

        return CustomDataFrame(df_merge)

    def fractional_difference(self, d=0.845, m=100, groupby_column="ticker"):
        from sovai.extensions.fractional_differencing import fractional_diff

        """
        Apply fractional differencing to each group for all columns, or to the entire DataFrame if groupby_column is not present.
        :param d: Differencing parameter.
        :param m: Truncation order.
        :param groupby_column: The column to group by. If not present, apply to entire DataFrame.
        :return: CustomDataFrame with fractional differencing applied.
        """
        # Check if groupby_column is in the DataFrame's columns or index
        if groupby_column in self.columns or groupby_column in self.index.names:
            # Apply fractional differencing grouped by the specified column
            def apply_frac_diff(group):
                for col in group.columns:
                    if col != groupby_column:  # Exclude the grouping column
                        group[col] = fractional_diff(group[col], d, m)
                return group

            # result_df = self.groupby(groupby_column).apply(apply_frac_diff)
            result_df = self.groupby(groupby_column, group_keys=False).apply(
                apply_frac_diff
            )
        else:
            # Apply fractional differencing to the entire DataFrame
            result_df = pd.DataFrame(index=self.index)
            for column in self.columns:
                result_df[column] = fractional_diff(self[column], d, m)

        return CustomDataFrame(result_df)

    def anomalies(self, method="scores", ticker=None):

        from sovai.extensions.anomalies import (
            anomaly_scores,
            anomaly_global,
            anomaly_local,
            anomaly_cluster,
            anomaly_reconstruction,
        )

        if method == "scores":
            return CustomDataFrame(anomaly_scores(self, ticker=ticker))
        elif method == "global":
            return CustomDataFrame(anomaly_global(self, ticker=ticker))
        elif method == "local":
            return CustomDataFrame(anomaly_local(self, ticker=ticker))
        elif method == "cluster":
            return CustomDataFrame(anomaly_cluster(self, ticker=ticker))
        elif method == "reconstruction":
            return CustomDataFrame(anomaly_reconstruction(self, ticker=ticker))
        else:
            raise ValueError(
                "Invalid method. Choose from 'scores', 'global', 'local', 'cluster', or 'reconstruction'."
            )

    def importance(self, method="random_projection"):

        from sovai.extensions.shapley_global_importance import run_simulations_global_importance

        from sovai.extensions.feature_importance import (
            random_projection_importance,
            fast_nonlinear_diverse_selector,
            fast_ica_selector,
            truncated_svd_selector,
            sparse_random_projection_selector,
        )


        if method == "random_projection":
            return random_projection_importance(self)
        elif method == "fourier":
            return fast_nonlinear_diverse_selector(self)
        elif method == "ica":
            return fast_ica_selector(self)
        elif method == "svd":
            return truncated_svd_selector(self)
        elif method == "sparse_projection":
            return sparse_random_projection_selector(self)
        elif method == "shapley":
            return run_simulations_global_importance(
                self, num_simulations=4, clustering_method="KMEANS"
            )

        else:
            raise ValueError(
                "Invalid method. Choose from 'scores', 'global', 'local', 'cluster', or 'reconstruction'."
            )

    def nowcast_data(self, feature=None):

        from sovai.extensions.nowcasting import nowcast_data_source


        return CustomDataFrame(nowcast_data_source(self, selected_feature=feature))


    def nowcast_plot(self, feature=None):

        from sovai.extensions.nowcasting import nowcast_plot_source

        return nowcast_plot_source(self, feature=feature)


    def change_point(self, method="data", ticker=None, feature=None):

        from sovai.extensions.change_point_generator import (
        perform_cusum_analysis,
        run_cusum_dashboard,
            )

        if ticker is None or feature is None:
            print("Ticker and/or feature not provided. We will choose on your behalf.")
            if ticker is None:
                ticker = self.index.get_level_values("ticker").unique()[0]
                print(f"Selected ticker: {ticker}")
            if feature is None:
                feature = self.columns[0]
                print(f"Selected feature: {feature}")

        if method == "data":
            return CustomDataFrame(
                perform_cusum_analysis(self, ticker=ticker, feature=feature)
            )
        elif method == "plot":
            return run_cusum_dashboard(self, ticker=ticker, feature=feature)
        else:
            raise ValueError("Invalid method. Choose from 'data', 'plot'")

    def regime_change(self, method="data", ticker=None, feature=None):
        if ticker is None or feature is None:
            print("Ticker and/or feature not provided. We will choose on your behalf.")
            if ticker is None:
                ticker = self.index.get_level_values("ticker").unique()[0]
                print(f"Selected ticker: {ticker}")
            if feature is None:
                feature = self.columns[0]
                print(f"Selected feature: {feature}")

        if method == "data":
        
            from sovai.extensions.regime_change import perform_regime_change_analysis

            analysis_df = perform_regime_change_analysis(self, ticker, feature)
            result = CustomDataFrame(analysis_df)
            return result
        elif method == "plot":

            from sovai.extensions.regime_change import run_regime_change_dashboard
            return run_regime_change_dashboard(self, ticker=ticker, feature=feature)
        else:
            raise ValueError("Invalid method. Choose from 'data', 'plot'")

    def pca_regime_change(self, method="data", ticker=None):


        from sovai.extensions.regime_change_pca import (
            perform_pca_regime_change_analysis,
            run_pca_regime_change_dashboard,
        )
        if ticker is None:
            print("Ticker not provided. We will choose on your behalf.")
            ticker = self.index.get_level_values("ticker").unique()[0]
            print(f"Selected ticker: {ticker}")

        if method == "data":
            return CustomDataFrame(perform_pca_regime_change_analysis(self, ticker))
        elif method == "plot":
            return run_pca_regime_change_dashboard(self, ticker=ticker)
        else:
            raise ValueError("Invalid method. Choose from 'data', 'plot'")

    def time_decomposition(self, method="data", ticker=None, feature=None):


        from sovai.extensions.time_decomposition import (
            perform_comprehensive_analysis,
            run_comprehensive_analysis_dashboard,
        )

        if ticker is None or feature is None:
            print("Ticker and/or feature not provided. We will choose on your behalf.")
            if ticker is None:
                ticker = self.index.get_level_values("ticker").unique()[0]
                print(f"Selected ticker: {ticker}")
            if feature is None:
                feature = self.columns[0]
                print(f"Selected feature: {feature}")

        if method == "data":
            return CustomDataFrame(
                perform_comprehensive_analysis(self, ticker, feature)
            )
        elif method == "plot":
            return run_comprehensive_analysis_dashboard(
                self, ticker=ticker, feature=feature
            )
        else:
            raise ValueError("Invalid method. Choose from 'data', 'plot'")

    def extract_features(
        self,
        entity_col="ticker",
        date_col="date",
        lookback=None,
        features=None,
        every="all",
        verbose=False,
    ):
        """
        Extracts features from the CustomDataFrame and returns a new CustomDataFrame with the extracted features.
        """
        from sovai.extensions.feature_extraction import feature_extractor

        result_pd = feature_extractor(
            self, entity_col, date_col, lookback, features, every, verbose
        )
        return CustomDataFrame(result_pd)

    def reduce_dimensions(
        self, method="pca", explained_variance=0.95, verbose=False, n_components=None
    ):
        """
        Perform dimensionality reduction on the CustomDataFrame.

        Parameters:
        method (str): Dimensionality reduction method.
                      Options: 'pca', 'truncated_svd', 'factor_analysis', 'gaussian_random_projection', 'umap'
        explained_variance (float): Amount of variance to be explained (0 to 1)
        verbose (bool): If True, print additional information

        Returns:
        CustomDataFrame: Reduced data in panel format
        """



        from sovai.extensions.dimensionality_reduction import dimensionality_reduction



        def print_status(message):
            if verbose:
                print(message)

        print_status(f"Starting dimensionality reduction using {method}")

        # Apply dimensionality reduction

        
        result_df = dimensionality_reduction(
            self, method, explained_variance, n_components
        )
        return CustomDataFrame(result_df)

    def pca(
        self, explained_variance=0.95, verbose=False, n_components=None
    ):
        return self.reduce_dimensions(method="pca", explained_variance=explained_variance, 
            verbose=verbose, n_components=n_components
        )

    def weight_optimization(self):
        """
        Perform dimensionality reduction on the CustomDataFrame.
        Parameters:
        method (str): Dimensionality reduction method.
        Options: 'pca', 'truncated_svd', 'factor_analysis', 'gaussian_random_projection', 'umap'
        explained_variance (float): Amount of variance to be explained (0 to 1)
        verbose (bool): If True, print additional information
        Returns:
        CustomDataFrame: Reduced data in panel format
        """
        import pandas as pd
        import numpy as np


        from sovai.extensions.weight_optimization import WeightOptimization

        # Check if self is a pandas DataFrame
        if not isinstance(self, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        # Check if 'date' is in the index or columns, and set it as index if it's in columns
        if "date" in self.columns:
            self = self.set_index("date")
        elif not isinstance(self.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have a 'date' index or column.")

        # Check if the dataframe is in wide format
        if len(self.columns) < 2:
            raise ValueError(
                "DataFrame must be in wide format with multiple ticker columns."
            )

        # Check if the data looks like returns
        sample_data = self.values.flatten()
        if not np.all((sample_data >= -1) & (sample_data <= 1)):
            raise ValueError(
                "Data does not appear to be returns. Values should be between -1 and 1."
            )

        # If all checks pass, proceed with creating the WeightOptimization object
        try:
            portfolio = WeightOptimization(self)
            return portfolio
        except Exception as e:
            print(f"Error creating WeightOptimization object: {str(e)}")
            print("\nThe data should be in a wide format, like this:")
            print("\n            AIG     VZ      BHP     ...")
            print("2024-07-19 -0.047  -0.011  -0.008  ...")
            print("2024-07-22  0.022  -0.061   0.002  ...")
            return None

    def signal_evaluator(self, verbose=False):
        """
        Perform weight optimization on the input multi-index DataFrame.

        Returns:
        SignalEvaluator: A SignalEvaluator object with optimized weights
        """
        import pandas as pd
        import numpy as np

        from sovai.extensions.signal_evaluation import SignalEvaluator

        # Check if self.df_factor is a pandas DataFrame
        if not isinstance(self, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        # Check if the DataFrame has a multi-index
        if not isinstance(self.index, pd.MultiIndex):
            raise ValueError("Input DataFrame must have a multi-index.")

        # Check if  'ticker', and 'date' are in the index levels
        required_levels = ["ticker", "date"]
        if not all(level in self.index.names for level in required_levels):
            raise ValueError(
                f"DataFrame must have index levels: {', '.join(required_levels)}"
            )

        # If all checks pass, proceed with creating the SignalEvaluator object
        try:
            optimized_evaluator = SignalEvaluator(self, verbose)
            print("SignalEvaluator object created successfully with optimized weights.")
            return optimized_evaluator
        except Exception as e:
            print(f"Error creating SignalEvaluator object: {str(e)}")
            print("\nThe input data should be in a multi-index format, like this:")
            print("\nbusiness_risk ticker   date")
            print("A            AAPL     1999-11-26    26.000")
            print("                      1999-12-03    26.000")
            print("             IBM      1999-11-26    55.000")
            print("                      1999-12-03    56.000")
            print("B            GOOGL    1999-11-26    85.000")
            print("                      1999-12-03    87.000")
            return None

    def feature_importance(self, num_simulations=4, clustering_method="KMEANS"):
        """
        Computes feature importance using SHAP values based on multiple simulations.

        :param num_simulations: The number of simulations to run (default 4).
        :param clustering_method: The clustering method to use ('OPTICS' or 'KMeans').
        :return: A DataFrame with average SHAP values per feature.
        """
        from sovai.extensions.shapley_global_importance import  run_simulations_frame_global

        # Running the simulations and getting average SHAP values
        avg_shap_values = run_simulations_frame_global(
            self, num_simulations=num_simulations, clustering_method=clustering_method
        )

        return CustomDataFrame(avg_shap_values)
    
    def technical_indicators(self):

        from sovai.extensions.technical_indicators import techn_indicators

        """
        Computes feature importance using SHAP values based on multiple simulations.

        :param num_simulations: The number of simulations to run (default 4).
        :param clustering_method: The clustering method to use ('OPTICS' or 'KMeans').
        :return: A DataFrame with average SHAP values per feature.
        """

        return CustomDataFrame(techn_indicators(self))


# # Example usage
# selected_ticker = 'AAPL'
# selected_feature = 'total_revenue'

# df_signal = df_accounting.query(f"ticker == '{selected_ticker}'").reset_index().set_index("date")[selected_feature]

# analysis_df  = perform_cusum_analysis(df_signal, selected_ticker, selected_feature)


### Works but not faster. Numpy operations still faster than polars.

import polars as pl
import pandas as pd
import numpy as np


def distance_pl(pandas_df, on="ticker"):

    from numpy.linalg import norm

    pl_df = pl.from_pandas(
        pandas_df.reset_index()
        if isinstance(pandas_df.index, pd.MultiIndex)
        else pandas_df
    )

    exclude_cols = [on, "date"]
    numeric_cols = [col for col in pl_df.columns if col not in exclude_cols]

    # Check for missing values
    has_missing = pl_df.select(pl.any_horizontal(pl.all().is_null().any())).item()
    if has_missing:
        missing_count = pl_df.select(numeric_cols).null_count().sum()
        print(
            f"Warning: dataframe has {missing_count.shape} missing values. Imputed with median."
        )
        pl_df = pl_df.with_columns(
            [pl.col(col).fill_null(pl.col(col).median()) for col in numeric_cols]
        )

    agg_df = pl_df.group_by(on).agg([pl.mean(col) for col in numeric_cols]).sort(on)
    numeric_values = agg_df.select(numeric_cols).to_numpy()

    dot_product = numeric_values @ numeric_values.T
    l2_norm = norm(numeric_values, axis=1)
    cosine_similarity = dot_product / np.outer(l2_norm, l2_norm)
    cosine_distance = 1 - cosine_similarity

    min_val, max_val = np.min(cosine_distance), np.max(cosine_distance)
    cosine_distance_normalized = (cosine_distance - min_val) / (max_val - min_val)

    sorted_tickers = agg_df[on].sort().to_list()
    result = pl.DataFrame(cosine_distance_normalized, schema=sorted_tickers)
    result = result.with_columns(pl.Series(name=on, values=sorted_tickers))

    # Convert the result back to a pandas DataFrame
    pandas_result = result.to_pandas()
    pandas_result.set_index(on, inplace=True)

    return pandas_result
