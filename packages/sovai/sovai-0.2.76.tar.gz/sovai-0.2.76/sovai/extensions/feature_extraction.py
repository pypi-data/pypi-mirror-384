import polars as pl
import numpy as np
import time


def feature_extractor(
    df,
    entity_col="ticker",
    date_col="date",
    lookback=None,
    features=None,
    every="all",
    verbose=False,
):
    def print_status(message):
        if verbose:
            print(message)

    start_time = time.time()

    # Convert pandas DataFrame to polars if necessary
    if not isinstance(df, pl.DataFrame):
        df = pl.from_pandas(df.reset_index())
    print_status(f"Conversion to polars: {time.time() - start_time:.2f} seconds")

    if features:
        value_cols = features
    else:
        # Get the list of columns to process (excluding index columns)
        value_cols = [col for col in df.columns if col not in [entity_col, date_col]]

    # Backfill missing values by ticker
    start_time = time.time()
    df = df.with_columns(
        [pl.col(col).backward_fill().over(entity_col) for col in value_cols]
    )
    print_status(f"Backfill missing values: {time.time() - start_time:.2f} seconds")

    # Fill remaining NaN values with the median of each column
    start_time = time.time()
    for col in value_cols:
        median_value = df.select(pl.col(col).median()).item()
        df = df.with_columns([pl.col(col).fill_null(median_value).alias(col)])
    print_status(f"Fill NaN values with median: {time.time() - start_time:.2f} seconds")

    # Standardize the data
    start_time = time.time()
    df = df.with_columns(
        [
            ((pl.col(col) - pl.col(col).mean()) / pl.col(col).std()).alias(col)
            for col in value_cols
        ]
    )
    print_status(f"Standardize the data: {time.time() - start_time:.2f} seconds")

    # Generate feature calculations for all columns
    def generate_features(col):
        return [
            pl.col(col).ts.binned_entropy(bin_count=10).alias(f"{col}_binned_entropy"),
            pl.col(col)
            .ts.lempel_ziv_complexity(threshold=3)
            .alias(f"{col}_lempel_ziv_complexity"),
            pl.col(col)
            .ts.longest_streak_above_mean()
            .alias(f"{col}_longest_streak_above_mean"),
            pl.col(col).ts.absolute_energy().alias(f"{col}_absolute_energy"),
            pl.col(col).ts.absolute_maximum().alias(f"{col}_absolute_maximum"),
            pl.col(col)
            .ts.absolute_sum_of_changes()
            .alias(f"{col}_absolute_sum_of_changes"),
            pl.col(col).ts.benford_correlation().alias(f"{col}_benford_correlation"),
            pl.col(col).ts.c3(1).alias(f"{col}_c3"),
            pl.col(col).ts.count_above_mean().alias(f"{col}_count_above_mean"),
            pl.col(col).ts.count_below_mean().alias(f"{col}_count_below_mean"),
            pl.col(col)
            .ts.first_location_of_maximum()
            .alias(f"{col}_first_location_of_maximum"),
            pl.col(col)
            .ts.first_location_of_minimum()
            .alias(f"{col}_first_location_of_minimum"),
            pl.col(col)
            .ts.last_location_of_maximum()
            .alias(f"{col}_last_location_of_maximum"),
            pl.col(col)
            .ts.last_location_of_minimum()
            .alias(f"{col}_last_location_of_minimum"),
            pl.col(col)
            .ts.longest_losing_streak()
            .alias(f"{col}_longest_losing_streak"),
            pl.col(col)
            .ts.longest_winning_streak()
            .alias(f"{col}_longest_winning_streak"),
            pl.col(col).ts.max_abs_change().alias(f"{col}_max_abs_change"),
            pl.col(col).ts.mean_abs_change().alias(f"{col}_mean_abs_change"),
            pl.col(col).ts.mean_change().alias(f"{col}_mean_change"),
            pl.col(col)
            .ts.mean_second_derivative_central()
            .alias(f"{col}_mean_second_derivative_central"),
            pl.col(col).ts.number_crossings().alias(f"{col}_number_crossings"),
            pl.col(col).ts.number_peaks(1).alias(f"{col}_number_peaks"),
            pl.col(col)
            .ts.percent_reoccurring_points()
            .alias(f"{col}_percent_reoccurring_points"),
            pl.col(col)
            .ts.percent_reoccurring_values()
            .alias(f"{col}_percent_reoccurring_values"),
            pl.col(col).ts.range_change().alias(f"{col}_range_change"),
            pl.col(col).ts.ratio_beyond_r_sigma().alias(f"{col}_ratio_beyond_r_sigma"),
            pl.col(col).ts.root_mean_square().alias(f"{col}_root_mean_square"),
            pl.col(col)
            .ts.time_reversal_asymmetry_statistic(1)
            .alias(f"{col}_time_reversal_asymmetry_statistic"),
            pl.col(col)
            .ts.variation_coefficient()
            .alias(f"{col}_variation_coefficient"),
        ]

    # Generate all features if not provided
    # if features is None:
    features = [feature for col in value_cols for feature in generate_features(col)]

    # Ensure the date column is of datetime type
    df = df.with_columns(pl.col(date_col).cast(pl.Date))

    # Map 'every' parameter to appropriate string
    every_map = {"week": "1w", "month": "1mo", "year": "1y"}
    every = every_map.get(every, every)

    if every == "all" or every is None:
        # Use regular group_by for non-rolling features
        result = df.group_by(entity_col).agg(features)
    else:
        # Use group_by_dynamic for rolling time series features
        if lookback is None:
            raise ValueError("lookback must be specified when using rolling features")

        result = (
            df.sort([entity_col, date_col])
            .group_by_dynamic(
                index_column=date_col,
                every=every,
                period=f"{lookback}{every[-1]}"
                if isinstance(lookback, int)
                else lookback,
                by=entity_col,
                closed="right",
                label="right",
                offset="-3d",  # Offset by 3 days to end on Friday
                include_boundaries=True,
            )
            .agg(features)
        )

    # Convert back to pandas
    result_pd = result.to_pandas()

    # Set index based on available columns
    if entity_col in result_pd.columns and date_col in result_pd.columns:
        result_pd = result_pd.set_index([entity_col, date_col])
    elif entity_col in result_pd.columns:
        result_pd = result_pd.set_index(entity_col)
    elif date_col in result_pd.columns:
        result_pd = result_pd.set_index(date_col)

    # Remove non-numerical columns
    numerical_columns = result_pd.select_dtypes(include=[np.number]).columns
    result_pd = result_pd[numerical_columns]

    print_status("Feature extraction completed successfully!")
    print_status(f"Number of features calculated: {len(result_pd.columns)}")

    return result_pd
