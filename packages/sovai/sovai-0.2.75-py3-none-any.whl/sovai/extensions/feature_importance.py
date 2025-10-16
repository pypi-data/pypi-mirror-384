import numpy as np
import pandas as pd
from sklearn.random_projection import GaussianRandomProjection
from scipy import stats

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.kernel_approximation import RBFSampler
from scipy import stats


import numpy as np
import pandas as pd
from sklearn.decomposition import FastICA
from scipy import stats

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from scipy import stats
import numpy as np
import pandas as pd
from sklearn.random_projection import SparseRandomProjection
from scipy import stats


def random_projection_importance(df_filled, n_components=100):
    # Identify columns with sufficient non-NaN values
    # min_non_nan = len(df_returns) * 0.5  # Adjust this threshold as needed
    # valid_columns = df_returns.columns[df_returns.notna().sum() > min_non_nan]

    # # Select only valid columns
    # df_valid = df_returns[valid_columns]

    # Fill NaN with 0 for projection (you might want to use a different imputation method)
    df_filled = df_filled.fillna(0)

    # Perform random projection
    n_components = min(n_components, len(df_filled.columns))
    rp = GaussianRandomProjection(n_components=n_components, random_state=42)
    rp.fit(df_filled)

    # Calculate the importance of each original feature
    feature_importance = np.sum(rp.components_**2, axis=0)

    # Convert importance to percentiles
    importance_percentiles = stats.percentileofscore(
        feature_importance, feature_importance
    )

    # Create a DataFrame with feature importances and percentiles
    importance_df = pd.DataFrame(
        {
            "feature": df_filled.columns,
            "importance": feature_importance,
            "importance_percentile": importance_percentiles,
        }
    )

    # Sort the DataFrame by importance percentile in descending order
    importance_df_sorted = importance_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return importance_df_sorted


def fast_nonlinear_diverse_selector(df_valid, n_components=100, gamma=1.0):
    df_valid = df_valid.fillna(0)

    # Apply Random Fourier Features
    rff = RBFSampler(n_components=n_components, gamma=gamma, random_state=42)
    data_rff = rff.fit_transform(df_valid.T)  # Transform features, not samples

    # Calculate feature importance as the norm of each feature in RFF space
    feature_importance = np.linalg.norm(data_rff, axis=1)

    # Convert importance to percentiles
    importance_percentiles = stats.percentileofscore(
        feature_importance, feature_importance
    )

    # Create a DataFrame with feature importances and percentiles
    importance_df = pd.DataFrame(
        {
            "feature": df_valid.columns,
            "importance": feature_importance,
            "importance_percentile": importance_percentiles,
        }
    )

    # Sort the DataFrame by importance percentile in descending order
    importance_df_sorted = importance_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return importance_df_sorted


def fast_ica_selector(df_filled, n_components=20):
    df_filled = df_filled.fillna(0)

    # Perform ICA
    n_components = min(n_components, len(df_filled.columns))
    ica = FastICA(n_components=n_components, random_state=42)
    S = ica.fit_transform(df_filled)

    # Calculate feature importance
    feature_importance = np.linalg.norm(ica.components_, axis=0)

    # Scale the importance values
    feature_importance = feature_importance * 1e11  # Multiply by a million

    # Calculate percentiles
    importance_percentiles = stats.percentileofscore(
        feature_importance, feature_importance
    )

    # Create DataFrame with results
    result_df = pd.DataFrame(
        {
            "feature": df_filled.columns,
            "importance": feature_importance,
            "importance_percentile": importance_percentiles,
        }
    )

    # Sort by importance percentile in descending order
    result_df = result_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return result_df


def truncated_svd_selector(df_filled, n_components=20):
    # Identify columns with sufficient non-NaN values
    # min_non_nan = len(df_returns) * 0.1
    # valid_columns = df_returns.columns[df_returns.notna().sum() > min_non_nan]

    # # Select only valid columns
    # df_valid = df_returns[valid_columns]

    # # Fill NaN with 0 for SVD (you might want to use a different imputation method)
    df_filled = df_filled.fillna(0)

    # Perform Truncated SVD
    n_components = min(n_components, len(df_filled.columns) - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    svd.fit(df_filled)

    # Calculate feature importance
    feature_importance = np.sum(svd.components_**2, axis=0)

    # Calculate percentiles
    importance_percentiles = stats.percentileofscore(
        feature_importance, feature_importance
    )

    # Create DataFrame with results
    result_df = pd.DataFrame(
        {
            "feature": df_filled.columns,
            "importance": feature_importance,
            "importance_percentile": importance_percentiles,
        }
    )

    # Sort by importance percentile in descending order
    result_df = result_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return result_df


def sparse_random_projection_selector(df_returns, n_components=30):
    # Identify columns with sufficient non-NaN values
    # min_non_nan = len(df_returns) * 0.1
    # valid_columns = df_returns.columns[df_returns.notna().sum() > min_non_nan]

    # # Select only valid columns
    # df_valid = df_returns[valid_columns]

    # Fill NaN with 0 for projection (you might want to use a different imputation method)
    df_valid = df_returns.fillna(0)

    # Perform Sparse Random Projection
    n_components = min(n_components, len(df_valid.columns))
    srp = SparseRandomProjection(n_components=n_components, random_state=42)
    srp.fit(df_valid)

    # Calculate feature importance
    feature_importance = np.sum(srp.components_.power(2).toarray(), axis=0)

    # Calculate percentiles
    importance_percentiles = stats.percentileofscore(
        feature_importance, feature_importance
    )

    # Create DataFrame with results
    result_df = pd.DataFrame(
        {
            "feature": df_valid.columns,
            "importance": feature_importance,
            "importance_percentile": importance_percentiles,
        }
    )

    # Sort by importance percentile in descending order
    result_df = result_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return result_df


## Other ones for future

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy.stats import special_ortho_group


def pca_varimax_selection(df_returns, k=30, n_components=50):
    # Identify columns with sufficient non-NaN values
    min_non_nan = len(df_returns) * 0.1
    valid_columns = df_returns.columns[df_returns.notna().sum() > min_non_nan]
    df_valid = df_returns[valid_columns]

    # Impute NaN values with column means
    df_imputed = df_valid.fillna(0)

    # Perform PCA
    pca = PCA(n_components=n_components)
    pca_result = pca.fit_transform(df_imputed)

    # Varimax rotation
    rotation_matrix = special_ortho_group.rvs(n_components)
    rotated_components = np.dot(pca.components_.T, rotation_matrix)

    # Find columns with highest loadings
    loadings = np.abs(rotated_components)
    aggregated_loadings = np.sum(loadings, axis=1)
    selected_indices = np.argsort(-aggregated_loadings)[:k]
    selected_columns = df_valid.columns[selected_indices]

    return selected_columns


# # Usage
# selected_cols = pca_varimax_selection(df_returns, k=30, n_components=50)
# print(selected_cols)


import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import special_ortho_group


def pca_varimax_rolling_stats(df_returns, k=30, window=30, n_components=50):
    # Identify columns with sufficient non-NaN values
    min_non_nan = len(df_returns) * 0.1
    valid_columns = df_returns.columns[df_returns.notna().sum() > min_non_nan]
    df_valid = df_returns[valid_columns]

    # Calculate rolling statistics
    rolling_mean = df_valid.rolling(window=window, min_periods=1).mean()
    rolling_std = df_valid.rolling(window=window, min_periods=1).std()
    rolling_skew = df_valid.rolling(window=window, min_periods=1).skew()
    rolling_kurt = df_valid.rolling(window=window, min_periods=1).kurt()

    # Combine all statistics into a single DataFrame
    combined_stats = pd.concat(
        [rolling_mean, rolling_std, rolling_skew, rolling_kurt],
        axis=1,
        keys=["mean", "std", "skew", "kurt"],
    )

    # Flatten the multi-level columns
    combined_stats.columns = [
        "_".join(col).strip() for col in combined_stats.columns.values
    ]

    # Replace NaN with 0
    combined_stats = combined_stats.fillna(0)

    # Scale the combined statistics
    scaler = StandardScaler()
    scaled_stats = scaler.fit_transform(combined_stats)

    # Perform PCA
    n_components = min(n_components, scaled_stats.shape[1])
    pca = PCA(n_components=n_components)
    pca_result = pca.fit_transform(scaled_stats)

    # Varimax rotation
    rotation_matrix = special_ortho_group.rvs(n_components)
    rotated_components = np.dot(pca.components_.T, rotation_matrix)

    # Find columns with highest loadings
    loadings = np.abs(rotated_components)

    # Reshape loadings to group by original columns (4 stats per column)
    reshaped_loadings = loadings.reshape(-1, 4, loadings.shape[1])

    # Aggregate loadings for each original column
    aggregated_loadings = np.sum(reshaped_loadings, axis=(1, 2))

    # Create a Series with the loadings for each valid column
    loading_series = pd.Series(aggregated_loadings, index=valid_columns)

    # Select k columns with the largest loadings
    selected_columns = loading_series.nlargest(k).index

    return selected_columns


# # Usage
# selected_cols = pca_varimax_rolling_stats(df_returns, k=30, window=30, n_components=50)
# print(selected_cols)

## pretty cool too

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans


def diverse_stock_selector(df_returns, n_components=30, n_clusters=20):
    # Fill NaN values with 0
    df_valid = df_returns.fillna(0)

    # Calculate correlations with the mean returns (proxy for index)
    correlations = df_valid.corrwith(df_valid.mean(axis=1))

    # Perform PCA
    pca = PCA(n_components=min(n_components, len(df_valid.columns)))
    pca.fit(df_valid)

    # Get PCA importance scores
    pca_importance = np.sum(pca.components_**2, axis=0)

    # Cluster stocks using MiniBatchKMeans
    mbk = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    clusters = mbk.fit_predict(df_valid.T)

    # Calculate feature importance
    feature_importance = pca_importance / correlations.abs().values

    # Create DataFrame with results
    result_df = pd.DataFrame(
        {
            "feature": df_valid.columns,
            "importance": feature_importance,
            "cluster": clusters,
        }
    )

    # Calculate percentile rank using pandas
    result_df["importance_percentile"] = result_df["importance"].rank(pct=True) * 100

    # Sort by importance percentile in descending order
    result_df = result_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return result_df


# Usage
# importance_df = diverse_stock_selector(df_returns)

# unique_feats = importance_df.drop_duplicates("cluster", keep='first')
