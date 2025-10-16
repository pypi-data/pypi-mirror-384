import pandas as pd
import numpy as np

## first a tiny change #
def is_percentile_data(df):
    # Select a sample of data for quick checking
    sample = df.select_dtypes(include=[np.number]).sample(min(1000, len(df)))

    # Check if all values are between 0 and 1
    is_between_0_and_1 = ((sample >= 0) & (sample <= 1)).all().all()

    # Check if all columns are float type
    is_float = (df.dtypes == float).all()

    return is_between_0_and_1 and is_float


def prepare_and_select_neighbors(df_accounting, ticker_select, neighbours):
    # Check if df_accounting has a MultiIndex with 'ticker' and 'date'
    if not (
        isinstance(df_accounting.index, pd.MultiIndex)
        and set(df_accounting.index.names) == {"ticker", "date"}
    ):
        print(
            "Error: The DataFrame should have a MultiIndex with levels 'ticker' and 'date'."
        )
        print("Please restructure your data using:")
        print("df_accounting = df_accounting.set_index(['ticker', 'date'])")
        print(
            "The anomaly detection method we're using works only on panel data structured this way."
        )
        return None

    # Check if data is already in percentiles
    if not is_percentile_data(df_accounting):
        print("Data is not in percentile form. Applying percentile transformation.")
        try:
            df_accounting = df_accounting.percentile("date")
        except AttributeError:
            print(
                "Error: The 'percentile()' method is not available. Make sure you're using the correct DataFrame method."
            )
            return None

    # If the index is correct and data is in percentiles, proceed with neighbor selection
    if ticker_select:
        try:
            neighs = (
                df_accounting.distance()
                .sort_values([ticker_select])
                .head(neighbours)
                .index.to_list()
            )
        except AttributeError:
            print(
                "Error: The 'distance()' method is not available. Make sure you're using the correct DataFrame method."
            )
            return None

        # Select the rows from df_accounting where the ticker is in the neighs list
        df_calc = df_accounting.loc[
            df_accounting.index.get_level_values("ticker").isin(neighs)
        ]
        df_calc = df_calc[~df_calc.index.duplicated(keep="first")]  # ← NEW LINE
        return df_calc

    else:
        return df_accounting


from sklearn.neighbors import NearestNeighbors, LocalOutlierFactor
import numpy as np
import pandas as pd


def find_optimal_k(data, max_k):
    neigh = NearestNeighbors(n_neighbors=max_k)
    neigh.fit(data)
    distances, _ = neigh.kneighbors(data)
    distances = np.sort(distances, axis=0)
    distances = distances[:, 1:]  # exclude the first column as it's distance to self

    avg_distances = np.mean(distances, axis=0)
    diffs = np.diff(avg_distances)
    optimal_k = np.argmin(diffs) + 1  # Add 1 because we're looking at differences

    return min(optimal_k + 1, max_k)  # Add 1 to optimal_k for a bit of buffer


def calculate_global_anomaly_scores(df, feature_columns):
    # Reset the index to convert ticker and date to regular columns
    df_reset = df.reset_index()

    # Find optimal k
    n_samples = len(df_reset)
    max_k = min(50, n_samples - 1)  # adjust max_k based on your data size
    optimal_k = find_optimal_k(df_reset[feature_columns], max_k)
    print(f"Optimal k for global anomaly detection: {optimal_k}")

    # Create an instance of NearestNeighbors with optimal k
    nn = NearestNeighbors(n_neighbors=optimal_k)

    # Fit NearestNeighbors to the feature data
    nn.fit(df_reset[feature_columns])

    # Get the distances to the k-th nearest neighbor
    distances, _ = nn.kneighbors(df_reset[feature_columns])
    outlier_scores = distances[
        :, -1
    ]  # Use the distance to the k-th neighbor as the outlier score

    # Normalize the scores to be between 0 and 1
    min_score = np.min(outlier_scores)
    max_score = np.max(outlier_scores)
    normalized_scores = (outlier_scores - min_score) / (max_score - min_score)

    return normalized_scores


from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import numpy as np


def robust_minmax_scale(scores):
    q1, q3 = np.percentile(scores, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    scaled_scores = np.clip(scores, lower_bound, upper_bound)
    scaled_scores = (scaled_scores - lower_bound) / (upper_bound - lower_bound)
    return scaled_scores


def calculate_local_anomaly_scores(df, feature_columns):
    # Reset the index to convert ticker and date to regular columns
    df_reset = df.reset_index()

    # Create instances of LOF and Isolation Forest
    lof = LocalOutlierFactor(contamination="auto", novelty=False)
    iso_forest = IsolationForest(contamination="auto", random_state=42)

    # Fit the models
    lof.fit(df_reset[feature_columns])
    iso_forest.fit(df_reset[feature_columns])

    # Get LOF scores
    lof_scores = -lof.negative_outlier_factor_

    # Get Isolation Forest scores
    # Use decision_function instead of predict to get continuous scores
    iso_scores = -iso_forest.decision_function(df_reset[feature_columns])

    print("LOF scores shape:", lof_scores.shape)
    print("Isolation Forest scores shape:", iso_scores.shape)

    # Combine the scores

    # Apply robust min-max scaling to both scores
    lof_scores_scaled = robust_minmax_scale(lof_scores)
    iso_scores_scaled = robust_minmax_scale(iso_scores)

    outlier_scores = (lof_scores_scaled + iso_scores_scaled) / 2

    outlier_scores = robust_minmax_scale(outlier_scores)

    return outlier_scores


from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler
import numpy as np


def calculate_clustered_anomaly_scores(df, feature_columns, n_components=0.80):
    # Reset the index to convert ticker and date to regular columns
    df_reset = df.reset_index()

    # Robustly scale the features
    scaler = RobustScaler()
    scaled_data = scaler.fit_transform(df_reset[feature_columns])

    # Apply PCA
    pca = PCA(n_components=n_components, svd_solver="full")
    pca_result = pca.fit_transform(scaled_data)

    # Calculate Mahalanobis distances
    covariance_matrix = np.cov(pca_result, rowvar=False)
    inv_covariance_matrix = np.linalg.inv(covariance_matrix)
    mean = np.mean(pca_result, axis=0)
    mahalanobis_distances = np.sqrt(
        ((pca_result - mean) @ inv_covariance_matrix * (pca_result - mean)).sum(axis=1)
    )

    # Convert to anomaly scores
    from scipy.stats import chi2

    anomaly_scores = chi2.cdf(mahalanobis_distances, df=pca_result.shape[1])

    # Robust normalization
    normalized_scores = robust_minmax_scale(anomaly_scores)

    return normalized_scores


def anomaly_scores(df_accounting, ticker=None, neighbours=50):

    df_calc = prepare_and_select_neighbors(df_accounting, ticker, neighbours)

    # Assuming df_accounting is your original DataFrame
    feature_columns = df_calc.columns

    # Calculate global anomaly scores
    global_anomaly_scores = calculate_global_anomaly_scores(df_calc, feature_columns)

    # Calculate local anomaly scores
    local_anomaly_scores = calculate_local_anomaly_scores(df_calc, feature_columns)

    # Calculate clustered anomaly scores
    clustered_anomaly_scores = calculate_clustered_anomaly_scores(
        df_calc, feature_columns
    )

    # Add the anomaly scores to the DataFrame
    df_anomaly = df_calc[[]].copy()
    df_anomaly["global_anomaly_score"] = global_anomaly_scores
    df_anomaly["local_anomaly_score"] = local_anomaly_scores
    # Add the clustered anomaly scores to the DataFrame
    df_anomaly["clustered_anomaly_score"] = clustered_anomaly_scores

    return df_anomaly


import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler
from joblib import Parallel, delayed
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from scipy.special import expit


def calculate_feature_anomaly_scores(
    feature_data, n_neighbors=5, sample_size=10000, sensitivity=5
):
    # Remove NaN and infinite values
    feature_data = feature_data[np.isfinite(feature_data)]

    # If not enough data points or all values are the same, return zeros
    if len(feature_data) < n_neighbors + 1 or feature_data.nunique() == 1:
        return np.zeros(len(feature_data))

    # Reshape and scale the data
    feature_data = feature_data.values.reshape(-1, 1)
    scaler = MinMaxScaler()
    feature_data_scaled = scaler.fit_transform(feature_data)

    # Sample data for fitting if it's too large
    if len(feature_data) > sample_size:
        sample_indices = np.random.choice(len(feature_data), sample_size, replace=False)
        sample_data = feature_data_scaled[sample_indices]
    else:
        sample_data = feature_data_scaled

    # Fit NearestNeighbors on the sample
    nn = NearestNeighbors(n_neighbors=n_neighbors + 1, algorithm="ball_tree", n_jobs=-1)
    nn.fit(sample_data)

    # Calculate distances for all points
    distances, _ = nn.kneighbors(feature_data_scaled)

    # Calculate anomaly scores
    k_distance = distances[:, -1]
    mean_distance = np.mean(distances[:, 1:], axis=1)

    # Avoid division by zero and handle potential infinities
    epsilon = np.finfo(float).eps
    ratio = np.divide(
        k_distance,
        mean_distance,
        out=np.ones_like(k_distance),
        where=mean_distance > epsilon,
    )

    # Apply log transformation to handle extreme values
    log_ratio = np.log1p(ratio)

    # Apply sigmoid transformation to get scores in [0, 1] range
    anomaly_scores = expit(sensitivity * (log_ratio - np.median(log_ratio)))

    return anomaly_scores


def process_feature(df, feature):
    try:
        return calculate_feature_anomaly_scores(df[feature])
    except Exception as e:
        print(f"Error processing feature {feature}: {str(e)}")
        return np.zeros(len(df))


def anomaly_global(df_accounting, ticker=None, neighbours=50):

    df_calc = prepare_and_select_neighbors(df_accounting, ticker, neighbours)

    # Assuming df_accounting is your original DataFrame
    feature_columns = df_calc.columns

    # Calculate feature anomaly scores in parallel
    results = Parallel(n_jobs=-1)(
        delayed(process_feature)(df_calc, feature) for feature in feature_columns
    )

    # Create DataFrame with anomaly scores
    df_anomaly = pd.DataFrame(dict(zip(feature_columns, results)), index=df_calc.index)

    df_anomaly["anomaly_score"] = df_anomaly.mean(axis=1)

    return df_anomaly


# df_global.query("ticker == 'ACGL'").reset_index().set_index("date")["anomaly_score"].plot()

# df_anomaly.query("ticker == 'PVN'").reset_index().set_index("date")["overall_anomaly_score"].plot()


from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
import numpy as np


def robust_minmax_scale(scores):
    q1, q3 = np.percentile(scores, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    scaled_scores = np.clip(scores, lower_bound, upper_bound)
    scaled_scores = (scaled_scores - lower_bound) / (upper_bound - lower_bound)
    return scaled_scores


def calculate_feature_anomaly_scores_ensemble(
    feature_data, n_neighbors=20, contamination=0.1, random_state=42
):
    # Remove NaN and infinite values
    feature_data = feature_data[np.isfinite(feature_data)]

    # If not enough data points or all values are the same, return zeros
    if len(feature_data) < n_neighbors + 1 or feature_data.nunique() == 1:
        return np.zeros(len(feature_data))

    # Reshape the data
    feature_data = feature_data.values.reshape(-1, 1)

    # Apply robust scaling
    scaler = RobustScaler()
    feature_data_scaled = scaler.fit_transform(feature_data)

    # Create instances of the two algorithms
    lof = LocalOutlierFactor(
        n_neighbors=n_neighbors, contamination="auto", n_jobs=-1, novelty=False
    )
    iso_forest = IsolationForest(
        contamination="auto", random_state=random_state, n_jobs=-1
    )

    # Fit and predict with LOF
    lof.fit(feature_data_scaled)
    lof_scores = -lof.negative_outlier_factor_

    # Fit and predict with Isolation Forest
    iso_forest.fit(feature_data_scaled)
    iso_scores = -iso_forest.decision_function(feature_data_scaled)

    # Apply robust min-max scaling to both scores
    lof_scores_scaled = robust_minmax_scale(lof_scores)
    iso_scores_scaled = robust_minmax_scale(iso_scores)

    # Combine scaled scores
    anomaly_scores = (lof_scores_scaled + iso_scores_scaled) / 2

    anomaly_scores = robust_minmax_scale(anomaly_scores)

    # print("LOF scores shape:", lof_scores.shape)
    # print("Isolation Forest scores shape:", iso_scores.shape)
    # print("Combined scores shape:", anomaly_scores.shape)

    # Optional: Apply logarithmic scaling to enhance sensitivity
    # anomaly_scores = np.log1p(anomaly_scores)

    return anomaly_scores


def process_feature_lof(df, feature):
    try:
        return calculate_feature_anomaly_scores_ensemble(df[feature])
    except Exception as e:
        print(f"Error processing feature {feature}: {str(e)}")
        return np.zeros(len(df))


def anomaly_local(df_accounting, ticker=None, neighbours=50):

    df_calc = prepare_and_select_neighbors(df_accounting, ticker, neighbours)

    # Assuming df_accounting is your original DataFrame
    feature_columns = df_calc.columns

    # Calculate feature anomaly scores in parallel
    results = Parallel(n_jobs=-1)(
        delayed(process_feature_lof)(df_calc, feature) for feature in feature_columns
    )

    # Create DataFrame with anomaly scores
    df_anomaly_lof = pd.DataFrame(
        dict(zip(feature_columns, results)), index=df_calc.index
    )

    # Calculate overall anomaly score
    df_anomaly_lof["anomaly_score"] = df_anomaly_lof[feature_columns].mean(axis=1)

    return df_anomaly_lof


import numpy as np
import pandas as pd
import tensorly as tl
from tensorly import tucker_to_tensor, unfold
from tensorly.decomposition import tucker
from sklearn.preprocessing import MinMaxScaler

tl.set_backend('numpy')

## If you want to speed things up use this.
# from tensorly.decomposition import tensor_train

# Assuming your data is stored in a DataFrame called 'df_accounting' with a multi-index of 'ticker' and 'date'


def estimate_rank(tensor_data, explained_var_threshold=0.95):
    """Estimate rank for each mode based on explained variance."""
    ranks = []
    for mode in range(tensor_data.ndim):
        U, S, _ = np.linalg.svd(unfold(tensor_data, mode), full_matrices=False)
        explained_var = np.cumsum(S**2) / np.sum(S**2)
        rank = np.argmax(explained_var >= explained_var_threshold) + 1
        ranks.append(min(rank, tensor_data.shape[mode]))
    return ranks


def create_reconstruction(df_calc):

    # Get the unique tickers and dates
    tickers = df_calc.index.get_level_values("ticker").unique()
    dates = df_calc.index.get_level_values("date").sort_values().unique()

    # Create a MultiIndex with all combinations of tickers and dates
    multi_index = pd.MultiIndex.from_product([tickers, dates], names=["ticker", "date"])

    # Reindex the DataFrame with the new MultiIndex and fill missing values with 0.5
    df_filled = df_calc.reindex(multi_index, fill_value=0.5)

    # Create a boolean mask based on the multi_index
    mask = pd.Series(multi_index.isin(df_calc.index), index=multi_index)

    # Reshape the filled data into a tensor
    tensor_data = np.array(df_filled).reshape(
        len(tickers), len(dates), len(df_filled.columns)
    )

    # def select_ranks(tensor_data, threshold=0.95):
    #     ranks = []
    #     for mode in range(tensor_data.ndim):
    #         unfolded = unfold(tensor_data, mode)
    #         _, s, _ = np.linalg.svd(unfolded, full_matrices=False)
    #         explained_variance = np.cumsum(s**2) / np.sum(s**2)
    #         rank = np.searchsorted(explained_variance, threshold) + 1
    #         ranks.append(rank)
    #     return ranks

    # # Automatically select the ranks based on explained variance
    # ranks = select_ranks(tensor_data, threshold=0.95)

    # Apply Tucker decomposition
    rank = estimate_rank(tensor_data, 0.95)
    print(f"Estimated rank: {rank}")

    core, factors = tucker(tensor_data, rank=rank)  # Adjust the rank as needed

    # Calculate reconstruction error

    # Extract the factors
    ticker_factor, date_factor, feature_factor = factors

    reconstructed_tensor = tucker_to_tensor((core, factors))

    # Convert the reconstructed tensor to a DataFrame with multi-index
    reconstructed_df = pd.DataFrame(
        reconstructed_tensor.reshape(-1, len(df_filled.columns)),
        index=multi_index,
        columns=df_filled.columns,
    )

    reconstruction_error_df = df_filled - reconstructed_df

    reconstruction_error_df = reconstruction_error_df[mask]

    return reconstruction_error_df


def normalize_tensor(reconstruction_error_df):
    abs_reconstruction_error_df = reconstruction_error_df.abs()

    # Initialize a MinMaxScaler
    scaler = MinMaxScaler()

    # Normalize each column to 0-1 range
    normalized_error_df = pd.DataFrame(
        scaler.fit_transform(abs_reconstruction_error_df),
        columns=abs_reconstruction_error_df.columns,
        index=abs_reconstruction_error_df.index,
    )

    # This normalized_error_df now contains outlier scores for each feature
    # Higher values (closer to 1) indicate more unusual or outlier-like behavior

    # Calculate an overall outlier score by taking the mean across all features
    overall_outlier_score = normalized_error_df.mean(axis=1)

    # Add the overall outlier score to the dataframe
    normalized_error_df["outlier_score"] = overall_outlier_score

    return normalized_error_df


def anomaly_cluster(df_accounting, ticker=None, neighbours=50):

    df_calc = prepare_and_select_neighbors(df_accounting, ticker, neighbours)

    df_calc = create_reconstruction(df_calc)

    df_calc = normalize_tensor(df_calc)

    return df_calc


def anomaly_reconstruction(df_accounting, ticker=None, neighbours=50):

    df_calc = prepare_and_select_neighbors(df_accounting, ticker, neighbours)

    cols = df_calc.columns
    index = df_calc.index

    df_calc = create_reconstruction(df_calc)

    # Normalize each column to 0-1 range
    df_calc = pd.DataFrame(df_calc, columns=cols, index=index)

    return df_calc


# ticker_select = "ACGL"

# df_anomaly = anomaly_scores(df_accounting, ticker_select)
# df_global = anomaly_global(df_accounting, ticker_select)
# df_local = anomaly_local(df_accounting, ticker_select)
# df_cluster = anomaly_local(df_accounting, ticker_select)
# df_recons = anomaly_reconstruction(df_accounting, ticker_select)


# df_accounting.anomalies("scores", "AAPL")
# df_accounting.anomalies("local", "AAPL")
# df_accounting.anomalies("global", "AAPL")
# df_accounting.anomalies("cluster", "AAPL")
# df_accounting.anomalies("reconstruction", "AAPL")
