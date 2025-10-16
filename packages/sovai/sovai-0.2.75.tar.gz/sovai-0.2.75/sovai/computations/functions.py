import numpy as np
import pandas as pd
from numpy.linalg import norm
from sovai import data

pd.options.display.float_format = "{:.3f}".format

## somethigns mall has to change

def normalize_min_max(matrix):
    """Apply Min-Max normalization."""
    min_val = np.min(matrix)
    max_val = np.max(matrix)
    return (matrix - min_val) / (max_val - min_val)


def percentile_calculation(df_importance, on="date"):
    df_importance = df_importance.groupby(level=on).transform(
        lambda x: x.rank(pct=True)
    )
    df_importance = df_importance.replace([np.inf, -np.inf], np.nan)
    df_importance = df_importance.fillna(0.5)
    return df_importance


def calculate_cosine_distance(df, on="ticker"):
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

    return cosine_distance * 100


def calculate_bar_S_matrix(cosine_similarity_df):
    """
    Highly optimized, fully vectorized calculation of the bar S matrix based on cosine similarities with Min-Max normalization.

    :param cosine_similarity_df: DataFrame representing the cosine similarity matrix.
    :return: DataFrame representing the normalized bar S matrix.
    """
    shape = cosine_similarity_df.shape
    if shape[0] != shape[1]:
        cosine_similarity_df = calculate_cosine_distance(cosine_similarity_df)

    cosine_similarity = cosine_similarity_df.values
    n = cosine_similarity.shape[0]

    # Vectorized calculation of squared differences
    sum_sq = np.sum(cosine_similarity**2, axis=1, keepdims=True)
    bar_S_matrix = np.sqrt(
        np.abs(sum_sq + sum_sq.T - 2 * np.dot(cosine_similarity, cosine_similarity.T))
    )

    # Normalize the bar S matrix
    bar_S_matrix = normalize_min_max(bar_S_matrix)

    # Convert back to DataFrame with appropriate indices and columns
    bar_S_matrix = pd.DataFrame(
        bar_S_matrix * 100,
        index=cosine_similarity_df.index,
        columns=cosine_similarity_df.columns,
    )

    return bar_S_matrix


import numpy as np
import pandas as pd
from numpy.linalg import norm


def calculate_shifted_cosine_similarity(df, on="ticker", shift=12):
    """
    Calculate an approximate cointegration proxy using shifted cosine similarity.

    :param df: Pandas DataFrame with MultiIndex.
    :param level: The level of the MultiIndex to group by (default 'ticker').
    :param shift: The number of periods to shift for lagged comparison (default 1 month).
    :return: DataFrame of shifted cosine similarities.
    """
    # Shift the DataFrame by the specified lag
    shifted_df = df.groupby(level=on).shift(-shift)

    # Calculate means of the original and shifted DataFrames
    mean_df = df.groupby(level=on).mean()
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

    return cosine_similarity


import numpy as np
import pandas as pd


def pca_from_scratch(df, n_components=4):
    # Drop columns with constant values (std=0) to avoid division by zero during standardization
    # df = df.loc[:, df.std() > 0]

    # Standardize the data
    # Fill NaN values with the mean of each column
    standardized_data = (df - df.mean()) / df.std()

    standardized_data = standardized_data.fillna(0)

    # Compute the covariance matrix
    covariance_matrix = np.cov(standardized_data.values, rowvar=False)

    # Compute the eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # Sort the eigenvalues and eigenvectors in descending order
    sorted_idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sorted_idx]
    eigenvectors = eigenvectors[:, sorted_idx]

    # Select the top n_components eigenvectors (principal components)
    principal_components = eigenvectors[:, :n_components]

    # Project the standardized data onto the principal components

    # print(principal_components[:2])
    # print(standardized_data[:2])

    pca_result = standardized_data.values.dot(principal_components)

    # Convert the PCA results to a DataFrame
    df_pca = pd.DataFrame(
        pca_result, columns=[f"PC{i+1}" for i in range(n_components)], index=df.index
    )

    # Convert the PCA results into percentiles
    # df_percentiles = df_pca.rank(pct=True)

    return df_pca


def preprocess_pca(df_importance_pca):
    df_balanced_sampled = df_importance_pca.reset_index()
    df_balanced_sampled["date"] = pd.to_datetime(
        df_balanced_sampled["date"], errors="coerce"
    )
    df_balanced_sampled.dropna(
        subset=["date"], inplace=True
    )  # Ensure there are no NaT types
    max_date = df_balanced_sampled["date"].max()
    min_date = df_balanced_sampled["date"].min()
    max_lag = (max_date.to_period("M") - min_date.to_period("M")).n
    return df_balanced_sampled, max_date, max_lag


def process_pca_plot(df_importance_pca):
    df_importance_pca.columns = [
        "price_factor_pca",
        "volatility_factor_pca",
        "solvency_factor_pca",
        "liquidity_factor_pca",
    ]
    df_describe = data("bankruptcy/description").set_index(["ticker", "date"])
    # Perform data preprocessing outside the function
    df_describe["target"] = df_describe["target"].astype("int")
    df_importance_pca = pd.merge(
        df_importance_pca, df_describe, left_index=True, right_index=True, how="left"
    )
    df_balanced_sampled, max_date, max_lag = preprocess_pca(df_importance_pca)

    return df_balanced_sampled, max_date, max_lag


def process_bankrupt_plot(df_bankrupt):
    df_describe = data("bankruptcy/description").set_index(["ticker", "date"])
    # Perform data preprocessing outside the function
    df_describe["target"] = df_describe["target"].astype("int")
    df_bankrupt = pd.merge(
        df_bankrupt, df_describe, left_index=True, right_index=True, how="left"
    )

    # Assuming df_bankrupt is your DataFrame as shown in the image

    # Reset index to make 'ticker' and 'date' normal columns
    df_bankrupt.reset_index(inplace=True)

    # df_bankrupt['target'] = df_bankrupt.groupby('ticker')['target'].transform(lambda x: x.shift(23).fillna(0))

    # Filter to include only bankrupt tickers
    bankrupt_tickers = df_bankrupt[df_bankrupt["target"] == 1]

    # Find the most recent bankruptcy date for each ticker
    recent_bankruptcy = bankrupt_tickers.groupby("ticker")["date"].max().reset_index()

    # Sort the tickers by most recent bankruptcy date
    sorted_tickers = recent_bankruptcy.sort_values("date", ascending=False)[
        "ticker"
    ].tolist()

    df_bankrupt["highlight"] = (
        df_bankrupt.groupby("ticker")["target"]
        .transform(lambda x: x.shift(23).fillna(0))
        .map({0: "Healthy", 1: "Bankrupt"})
    )

    return df_bankrupt, sorted_tickers


def map_bankrupt_features(df_importance_pct=None):
    df_mapping = pd.read_parquet("../assets/features_mapping.parq")

    df_mapping.head()

    # Ensure that model_indicators are in the columns of df_importance_pct
    df_mapping_filtered = df_mapping[
        df_mapping["model_indicators"].isin(df_importance_pct.columns)
    ]

    # Create a dictionary that maps 'model_indicators' to 'characteristic'
    mapping_dict = df_mapping_filtered.set_index("model_indicators")[
        "characteristic"
    ].to_dict()

    # Map the columns of df_importance_pct to their characteristics
    mapped_columns = df_importance_pct.columns.map(mapping_dict)

    # Group by the characteristics and calculate the mean
    # Note: This assumes that the index of df_importance_pct does not contain duplicates that would be aggregated unintentionally.
    # df_importance_pct_mapped = df_importance_pct.groupby(mapped_columns, axis=1).mean() # maybe you don't want abs.
    df_importance_pct_mapped = df_importance_pct.groupby(mapped_columns, axis=1).mean()
    return df_importance_pct_mapped


def more_risk_aggregates(df_risks):
    # Calculate the 30-day percentage change for the entire DataFrame
    # rolling_30day_pct_change = df_risks.pct_change(periods=30)
    rolling_30day_pct_change = df_risks.copy()

    # Define a function to calculate new columns based on the percentage change
    def new_calcs_function(df):
        df["VOLATILITY_RISK"] = df[["ENSEMBLE", "VIX"]].mean(axis=1)
        df["RECESSION_PROBABILITY"] = df[
            ["RECESSION_6", "RECESSION_12", "RECESSION_24"]
        ].mean(axis=1)
        df["GEOPOLITICAL_RISK"] = df[
            [
                "UK_POLICY_UNC_D",
                "CHINA_POLICY_UNC_M",
                "GLOBAL_POLICY_UNC_M",
                "GEO_UNC_D",
                "GEO_UNC_M",
                "GEO_EQUAL_M",
                "THINKTANK_UNC_M",
            ]
        ].mean(axis=1)
        df["DOMESTIC_POLITICAL_RISK"] = df[
            [
                "WEB_SEARCH_UNC_M",
                "US_SOVEREIGN_UNC_M",
                "US_MARKET_UNC_D",
                "US_POLICY_VOL_M",
                "US_POLICY_UNC_D",
            ]
        ].mean(axis=1)
        df["BOND_RISK"] = df[
            ["CREDIT_SPREAD", "TERM_SPREAD", "CORP_BOND_DISTRESS"]
        ].mean(axis=1)
        df["ECONOMIC_SENTIMENT"] = df[
            [
                "NEW_TRUCKS",
                "NEW_HOMES",
                "CAPE",
                "CFSEC_NEG",
                "CFNAI_FNEG",
                "ADS_BUSINESS_NEG",
            ]
        ].mean(axis=1)
        df["INVESTOR_SENTIMENT"] = df[["NAIIM_NEG", "AAII_NEG", "ZEW_SENT_NEG"]].mean(
            axis=1
        )
        df["CONSUMER_SENTIMENT"] = df[
            [
                "MICS_ICS_NEG",
                "MICS_ICC_NEG",
                "MICS_ICE_NEG",
                "MISERY_INDEX",
                "HOUSING_AFFORD_NEG",
            ]
        ].mean(axis=1)
        df["MANUFACTURING_SENTIMENT"] = df[
            ["MAN_PHIL_NEG", "MAN_TEX_NEG", "MAN_NY_NEG"]
        ].mean(axis=1)
        df["SERVICES_SENTIMENT"] = df[
            ["NONMAN_OUTLOOK_NEG", "RETAIL_INDEX_NEG", "SERVICES_INDEX_NEG"]
        ].mean(axis=1)
        return df

    # Apply the calculation function to the rolling percentage change DataFrame
    rolling_30day_pct_change = new_calcs_function(rolling_30day_pct_change)

    # Specify the columns to write
    write_text = [
        "TURING_RISK",
        "MARKET_RISK",
        "BUSINESS_RISK",
        "POLITICAL_RISK",
        "VOLATILITY_RISK",
        "RECESSION_PROBABILITY",
        "GEOPOLITICAL_RISK",
        "DOMESTIC_POLITICAL_RISK",
        "BOND_RISK",
        "ECONOMIC_SENTIMENT",
        "INVESTOR_SENTIMENT",
        "CONSUMER_SENTIMENT",
        "MANUFACTURING_SENTIMENT",
        "SERVICES_SENTIMENT",
    ]

    # Create a new DataFrame with the specified columns
    rolling_30day_pct_change_new = rolling_30day_pct_change[write_text].copy()

    return rolling_30day_pct_change_new
