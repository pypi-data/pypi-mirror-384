import numpy as np
import pandas as pd
from numpy.linalg import norm
from scipy.fft import fft
from scipy.spatial.distance import pdist, squareform
import numpy as np

# Set numpy to ignore warnings on invalid operations
np.seterr(divide="ignore", invalid="ignore")


def normalize_min_max(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def zero_crossing_rate(series):
    # Subtract the mean of each column
    centered = series - np.mean(series, axis=0)
    # Calculate the zero-crossing rate
    return np.mean(np.abs(np.diff(np.sign(centered), axis=0)), axis=0)


def mean_absolute_change(series):
    return np.mean(np.abs(np.diff(series, axis=0)), axis=0)


def spectral_centroid(series):
    spectrum = np.abs(fft(series, axis=0))
    normalized_spectrum = spectrum / np.sum(spectrum, axis=0)
    normalized_frequencies = np.linspace(0, 1, spectrum.shape[0])[:, np.newaxis]
    return np.sum(normalized_frequencies * normalized_spectrum, axis=0)


def turning_points(series):
    diff = np.diff(series, axis=0)
    return np.sum((diff[:-1] * diff[1:]) < 0, axis=0) / series.shape[0]


def autocorr_lag_1(series):
    return np.array(
        [
            np.corrcoef(series[:-1, i], series[1:, i])[0, 1]
            for i in range(series.shape[1])
        ]
    )


def fast_complexity_proxy(series):
    return np.std(series, axis=0)  # or np.ptp(series, axis=0) for peak-to-peak


def hjorth_mobility(series):
    diff1 = np.diff(series, axis=0)

    activity = np.nanvar(series, axis=0)
    mobility = np.sqrt(np.nanvar(diff1, axis=0) / activity)

    return mobility


def hurst_exponent(series, max_lag=7):
    lags = range(2, min(max_lag, len(series) // 2))
    if len(lags) == 0:
        return np.nan
    variances = np.array(
        [np.var(np.subtract(series[lag:], series[:-lag])) for lag in lags]
    )
    if np.any(variances <= 0):
        return np.nan
    try:
        return (np.polyfit(np.log(lags), np.log(variances), 1)[0]) / 2
    except Exception:
        return np.nan


def hurst_multivariate(series):
    return np.apply_along_axis(hurst_exponent, 0, series)


def series_range(series):
    return np.ptp(series, axis=0)


def series_mean(series):
    return np.mean(series, axis=0)


def series_skewness(series):
    return np.mean(
        ((series - np.mean(series, axis=0)) / np.std(series, axis=0)) ** 3, axis=0
    )


def first_diff_mean(series):
    return np.mean(np.diff(series, axis=0), axis=0)


def histogram_mode_5bins(series):
    if series.ndim == 1:
        series = series[:, np.newaxis]

    modes = []
    for col in range(series.shape[1]):
        hist, bin_edges = np.histogram(series[:, col], bins=5)
        mode_index = np.argmax(hist)
        mode_value = (bin_edges[mode_index] + bin_edges[mode_index + 1]) / 2
        modes.append(mode_value)

    return np.array(modes)


def time_reversibility_statistic(series):
    if series.ndim == 1:
        series = series[:, np.newaxis]

    trev_values = []
    for col in range(series.shape[1]):
        diff = np.diff(series[:, col])
        S1 = np.sum(diff**3)
        S2 = np.sum(diff**2)
        trev_values.append(S1 / S2**1.5 if S2 != 0 else np.nan)

    return np.array(trev_values)


def extract_metrics(df, feature_list=None, on="ticker"):
    series = df.values
    all_features = {
        "mean": series_mean,
        "skew": series_skewness,
        "std": fast_complexity_proxy,
        "diffm": first_diff_mean,
        "zcr": zero_crossing_rate,
        "mac": mean_absolute_change,
        "sc": spectral_centroid,
        "tp": turning_points,
        "acl1": autocorr_lag_1,
        "hjorthm": hjorth_mobility,
        "hurst": hurst_multivariate,
        "hist": histogram_mode_5bins,
        "timerev": time_reversibility_statistic,
    }

    # If no feature_list is provided, use all features
    if feature_list is None:
        feature_list = list(all_features.keys())

    features = {}
    for feature_name in feature_list:
        if feature_name in all_features:
            features[feature_name] = all_features[feature_name](series)
        else:
            print(f"Warning: Feature '{feature_name}' not found. Skipping.")

    # Flatten the features dictionary
    flattened_features = {}
    for feature_name, feature_values in features.items():
        for i, value in enumerate(feature_values):
            flattened_features[f"{feature_name}_{i}"] = value

    return pd.DataFrame([flattened_features], index=[df.index.get_level_values(on)[0]])


def cosine_distance(agg_df):
    dot_product = agg_df.values @ agg_df.values.T
    l2_norm = norm(agg_df.values, axis=1)
    cosine_similarity = dot_product / np.outer(l2_norm, l2_norm)
    cosine_distance = 1 - cosine_similarity
    return normalize_min_max(cosine_distance)


def euclidean_distance_matrix(agg_df):
    euclidean_distances = pdist(agg_df.values, metric="euclidean")
    euclidean_distance_matrix = squareform(euclidean_distances)
    return normalize_min_max(euclidean_distance_matrix)


def distance_cross(df_factors, on="ticker", distance="cosine", metric_list=None):
    # Check for missing values more efficiently
    missing_mask = df_factors.isna()
    missing_count = missing_mask.sum().sum()

    if missing_count > 0:
        print(f"Warning: {missing_count} missing values detected. Imputed with median.")
        # Calculate medians only for columns with missing values
        columns_with_missing = missing_mask.any()
        medians = df_factors.loc[:, columns_with_missing].median()
        df_factors = df_factors.fillna(medians)

    # Extract features for each group
    grouped = df_factors.groupby(level=on)
    feature_dfs = []
    for name, group in grouped:
        features = extract_metrics(group, metric_list, on)
        feature_dfs.append(features)

    # Combine all features
    agg_df = pd.concat(feature_dfs)

    agg_df = agg_df.fillna(agg_df.median())

    # Calculate distance based on the selected metric
    if distance == "cosine":
        distance_matrix = cosine_distance(agg_df)
    elif distance == "euclidean":
        distance_matrix = euclidean_distance_matrix(agg_df)
    else:
        raise ValueError("Unsupported metric. Choose from 'cosine' or 'euclidean'.")

    distance_df = pd.DataFrame(
        distance_matrix, index=agg_df.index, columns=agg_df.index
    )
    return distance_df, agg_df


# Usage
# result, agg_df = distance(df_factors.head(1000000), on='ticker')


## I would just vehemently recommend against this method.

import numpy as np
import pandas as pd
import polars as pl
from scipy.signal import hilbert
from scipy.spatial.distance import euclidean
from scipy.stats import pearsonr
# from fastdtw import fastdtw
from scipy.interpolate import interp1d
from numpy.linalg import norm

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict


def fastdtw(x, y, radius=1, dist=lambda a, b: abs(a - b)):
    min_time_size = radius + 2

    if len(x) < min_time_size or len(y) < min_time_size:
        return dtw(x, y, dist=dist)

    x_shrinked = __reduce_by_half(x)
    y_shrinked = __reduce_by_half(y)
    distance, path = fastdtw(x_shrinked, y_shrinked, radius=radius, dist=dist)
    window = __expand_window(path, len(x), len(y), radius)
    return dtw(x, y, window, dist=dist)


def dtw(x, y, window=None, dist=lambda a, b: abs(a - b)):
    len_x, len_y = len(x), len(y)
    if window is None:
        window = [(i, j) for i in range(len_x) for j in range(len_y)]
    window = ((i + 1, j + 1) for i, j in window)
    D = defaultdict(lambda: (float('inf'),))
    D[0, 0] = (0, 0, 0)
    for i, j in window:
        dt = dist(x[i-1], y[j-1])
        D[i, j] = min((D[i-1, j][0]+dt, i-1, j), (D[i, j-1][0]+dt, i, j-1), (D[i-1, j-1][0]+dt, i-1, j-1), key=lambda a: a[0])
    path = []
    i, j = len_x, len_y
    while not (i == j == 0):
        path.append((i-1, j-1))
        i, j = D[i, j][1], D[i, j][2]
    path.reverse()
    return (D[len_x, len_y][0], path)


def __reduce_by_half(x):
    return [(x[i//2] + x[1+i//2]) / 2 for i in range(0, len(x), 2)]


def __expand_window(path, len_x, len_y, radius):
    path_ = set(path)
    for i, j in path:
        for a, b in ((i + a, j + b) for a in range(-radius, radius+1) for b in range(-radius, radius+1)):
            path_.add((a, b))

    window_ = set()
    for i, j in path_:
        for a, b in ((i * 2, j * 2), (i * 2, j * 2 + 1), (i * 2 + 1, j * 2), (i * 2 + 1, j * 2 + 1)):
            window_.add((a, b))

    window = []
    start_j = 0
    for i in range(0, len_x):
        new_start_j = None
        for j in range(start_j, len_y):
            if (i, j) in window_:
                window.append((i, j))
                if new_start_j is None:
                    new_start_j = j
            elif new_start_j is not None:
                break
        start_j = new_start_j

    return window




# Set numpy to ignore warnings on invalid operations
np.seterr(divide="ignore", invalid="ignore")


def normalize_min_max(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def normalize_zscore(data):
    mean = np.mean(data, axis=0)
    std = np.std(data, axis=0)
    return (data - mean) / std


def dtw_distance(x, y):
    distance, _ = fastdtw(x, y, dist=euclidean)
    return distance


def pearson_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    corr_matrix = x.corrwith(y, axis=0)
    avg_corr = np.abs(corr_matrix).mean()
    return 1 - avg_corr


def euclidean_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 1:
        return np.nan
    diff = x.values[:, :, np.newaxis] - y.values[:, np.newaxis, :]
    distances = np.sqrt(np.mean(diff**2, axis=0))
    return np.mean(distances)


def euclidean_interpolated(x, y):
    max_len = max(len(x), len(y))
    x_interp = interp1d(np.linspace(0, 1, len(x)), x, axis=0)(
        np.linspace(0, 1, max_len)
    )
    y_interp = interp1d(np.linspace(0, 1, len(y)), y, axis=0)(
        np.linspace(0, 1, max_len)
    )
    return np.sqrt(np.sum((x_interp - y_interp) ** 2))


def vectorized_pec(data):
    data = np.nan_to_num(data)
    if data.size == 0:
        print("Warning: No valid data after removing NaNs")
        return np.array([[np.nan]])

    # Apply Hilbert transform to each column
    analytic_signal = np.apply_along_axis(hilbert, 0, data)

    # Compute power envelope
    envelope = np.abs(analytic_signal) ** 2

    # Compute correlation matrix
    return np.corrcoef(envelope.T)


def pec_distance(x, y):
    # Convert to DataFrames if not already
    x = pd.DataFrame(x) if not isinstance(x, pd.DataFrame) else x
    y = pd.DataFrame(y) if not isinstance(y, pd.DataFrame) else y

    # Align the DataFrames
    x, y = x.align(y, join="inner", axis=0)

    if len(x) < 1:
        return np.nan

    # Normalize the data using z-score
    x_norm = normalize_zscore(x.values)
    y_norm = normalize_zscore(y.values)

    combined_data = np.hstack((x_norm, y_norm))
    corr_matrix = vectorized_pec(combined_data)

    # Fill NaN values in the correlation matrix
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

    # Calculate the average correlation between x and y features
    n_x_features = x.shape[1]
    avg_corr = np.mean(corr_matrix[:n_x_features, n_x_features:])

    # Handle the case where avg_corr is NaN
    if np.isnan(avg_corr):
        return 1.0  # Maximum distance when correlation can't be computed

    return 1 - avg_corr


from scipy.stats import spearmanr
import warnings


def spearman_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    # Suppress warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            corr_matrix, _ = spearmanr(x, y, axis=0)
            if isinstance(
                corr_matrix, float
            ):  # If only one feature, spearmanr returns a single value
                avg_corr = np.abs(corr_matrix)
            else:
                # Filter out nan values before taking the mean
                valid_corrs = np.abs(corr_matrix[: x.shape[1], x.shape[1] :])
                avg_corr = np.nanmean(valid_corrs)

            # Check if avg_corr is nan (which can happen if all correlations are undefined)
            if np.isnan(avg_corr):
                return 1.0  # Maximum distance when correlation can't be computed
            return 1 - avg_corr
        except ValueError:
            # This can happen if one or both inputs are constant
            return 1.0  # Maximum distance when correlation can't be computed


from scipy.spatial.distance import cdist

import numba


import numpy as np

@numba.njit(cache=True)
def frechet_dist_fast(x, y, p=2):
    n, m = len(x), len(y)
    ca = np.ones((n, m)) * np.inf
    # Compute the distance matrix once
    dist_matrix = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            dist_matrix[i, j] = np.sum(np.abs(x[i] - y[j]) ** p) ** (1 / p)
    ca[0, 0] = dist_matrix[0, 0]
    for i in range(1, n):
        ca[i, 0] = max(ca[i - 1, 0], dist_matrix[i, 0])
    for j in range(1, m):
        ca[0, j] = max(ca[0, j - 1], dist_matrix[0, j])
    for i in range(1, n):
        for j in range(1, m):
            ca[i, j] = max(
                min(ca[i - 1, j], ca[i, j - 1], ca[i - 1, j - 1]), dist_matrix[i, j]
            )
    return ca[n - 1, m - 1]


import numpy as np
import pandas as pd
from scipy.stats import entropy, wasserstein_distance
from scipy.spatial.distance import jaccard


def kl_divergence_fast(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values = x.values + 1e-10  # Add small constant to avoid division by zero
    y_values = y.values + 1e-10
    return np.mean(
        [entropy(x_values[:, i], y_values[:, i]) for i in range(x_values.shape[1])]
    )


def wasserstein_fast(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values, y_values = x.values, y.values
    return np.mean(
        [
            wasserstein_distance(x_values[:, i], y_values[:, i])
            for i in range(x_values.shape[1])
        ]
    )


def jaccard_fast(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values, y_values = x.values, y.values
    x_bool = x_values > np.mean(x_values, axis=0)
    y_bool = y_values > np.mean(y_values, axis=0)
    return np.mean(
        [jaccard(x_bool[:, i], y_bool[:, i]) for i in range(x_bool.shape[1])]
    )


import numpy as np
import pandas as pd
from scipy.spatial.distance import directed_hausdorff


def bray_curtis_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values, y_values = x.values, y.values
    return np.mean(
        [
            np.sum(np.abs(x_values[:, i] - y_values[:, i]))
            / np.sum(x_values[:, i] + y_values[:, i])
            for i in range(x_values.shape[1])
        ]
    )


def hausdorff_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    return directed_hausdorff(x.values, y.values)[0]


def manhattan_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    return np.mean(np.abs(x.values - y.values))


def chi2_distance(x, y, eps=1e-10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values, y_values = x.values + eps, y.values + eps
    return np.mean(
        [
            0.5
            * np.sum(
                (x_values[:, i] - y_values[:, i]) ** 2
                / (x_values[:, i] + y_values[:, i])
            )
            for i in range(x_values.shape[1])
        ]
    )


def hellinger_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values, y_values = x.values, y.values
    return np.mean(
        [
            np.sqrt(
                0.5 * np.sum((np.sqrt(x_values[:, i]) - np.sqrt(y_values[:, i])) ** 2)
            )
            for i in range(x_values.shape[1])
        ]
    )


def canberra_distance(x, y):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan
    x_values, y_values = x.values, y.values
    return np.mean(
        [
            np.sum(
                np.abs(x_values[:, i] - y_values[:, i])
                / (np.abs(x_values[:, i]) + np.abs(y_values[:, i]))
            )
            for i in range(x_values.shape[1])
        ]
    )


import numpy as np
from scipy.stats import entropy


def shannon_entropy_distance(x, y, bins=10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    def calc_entropy(data):
        hist, _ = np.histogram(data, bins=bins)
        return entropy(hist)

    x_entropy = np.apply_along_axis(calc_entropy, 0, x.values)
    y_entropy = np.apply_along_axis(calc_entropy, 0, y.values)

    return np.mean(np.abs(x_entropy - y_entropy))


# Add to distance_metrics
import numpy as np
import pandas as pd
from scipy.stats import entropy
from scipy.spatial.distance import cdist


def shannon_entropy_distance(x, y, bins=10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    def calc_entropy(data):
        hist, _ = np.histogram(data, bins=bins)
        return entropy(hist)

    x_entropy = np.apply_along_axis(calc_entropy, 0, x.values)
    y_entropy = np.apply_along_axis(calc_entropy, 0, y.values)

    return np.mean(np.abs(x_entropy - y_entropy))


def sample_entropy_distance(x, y, m=2, r=0.2):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < m + 1:
        return np.nan

    def sampen(X):
        N = len(X)
        B = 0.0
        A = 0.0

        # Split time series and save all templates of length m and m+1
        xmi = np.array([X[i : i + m] for i in range(N - m)])
        xmj = np.array([X[i : i + m] for i in range(N - m + 1)])

        # Save all matches minus the self-match, compute B
        B = np.sum([np.sum(np.abs(xmii - xmi).max(axis=1) <= r) - 1 for xmii in xmi])

        # Similar for computing A
        xm = np.array([X[i : i + m] for i in range(N - m + 1)])
        A = np.sum([np.sum(np.abs(xmi - xm).max(axis=1) <= r) - 1 for xmi in xm])

        # Return SampEn
        return -np.log(A / B)

    x_sampen = np.apply_along_axis(sampen, 0, x.values)
    y_sampen = np.apply_along_axis(sampen, 0, y.values)

    return np.mean(np.abs(x_sampen - y_sampen))


def approx_entropy_distance(x, y, m=2, r=0.2):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < m + 1:
        return np.nan

    def apen(X):
        def _phi(m):
            x = np.array([X[i : i + m] for i in range(len(X) - m + 1)])
            C = np.sum(np.abs(x[:, None] - x) <= r, axis=2)
            return np.mean(np.log(C / (len(X) - m + 1)))

        return abs(_phi(m + 1) - _phi(m))

    x_apen = np.apply_along_axis(apen, 0, x.values)
    y_apen = np.apply_along_axis(apen, 0, y.values)

    return np.mean(np.abs(x_apen - y_apen))


def jensen_shannon_distance(x, y, bins=10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    def calc_js(p, q):
        m = 0.5 * (p + q)
        return 0.5 * (entropy(p, m) + entropy(q, m))

    def get_hist(data):
        hist, _ = np.histogram(data, bins=bins, density=True)
        return hist + 1e-10  # avoid zero probabilities

    x_hist = np.apply_along_axis(get_hist, 0, x.values)
    y_hist = np.apply_along_axis(get_hist, 0, y.values)

    js_divs = np.array(
        [calc_js(x_hist[:, i], y_hist[:, i]) for i in range(x_hist.shape[1])]
    )

    return np.mean(js_divs)


def renyi_entropy_distance(x, y, alpha=2, bins=10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    def renyi_entropy(data, alpha):
        hist, _ = np.histogram(data, bins=bins, density=True)
        hist = hist + 1e-10  # avoid zero probabilities
        return 1 / (1 - alpha) * np.log(np.sum(hist**alpha))

    x_renyi = np.apply_along_axis(renyi_entropy, 0, x.values, alpha=alpha)
    y_renyi = np.apply_along_axis(renyi_entropy, 0, y.values, alpha=alpha)

    return np.mean(np.abs(x_renyi - y_renyi))


def tsallis_entropy_distance(x, y, q=2, bins=10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    def tsallis_entropy(data, q):
        hist, _ = np.histogram(data, bins=bins, density=True)
        hist = hist + 1e-10  # avoid zero probabilities
        return (1 - np.sum(hist**q)) / (q - 1)

    x_tsallis = np.apply_along_axis(tsallis_entropy, 0, x.values, q=q)
    y_tsallis = np.apply_along_axis(tsallis_entropy, 0, y.values, q=q)

    return np.mean(np.abs(x_tsallis - y_tsallis))


def mutual_information_distance(x, y, bins=10):
    x, y = pd.DataFrame(x), pd.DataFrame(y)
    x, y = x.align(y, join="inner", axis=0)
    if len(x) < 2:
        return np.nan

    def calc_mi(x, y):
        c_xy = np.histogram2d(x, y, bins)[0]
        c_x = np.sum(c_xy, axis=1)
        c_y = np.sum(c_xy, axis=0)
        h_x = entropy(c_x)
        h_y = entropy(c_y)
        h_xy = entropy(c_xy.flatten())
        mi = h_x + h_y - h_xy
        return mi

    mi_values = [calc_mi(x.values[:, i], y.values[:, i]) for i in range(x.shape[1])]
    return 1 / (1 + np.mean(mi_values))


def entropy(c):
    c_normalized = c / float(np.sum(c))
    c_normalized = c_normalized[c_normalized > 0]
    H = -np.sum(c_normalized * np.log2(c_normalized))
    return H


# Dictionary of distance metrics
distance_metrics = {
    "dtw": dtw_distance,
    "pearson": pearson_distance,
    "spearman": spearman_distance,
    "euclidean": euclidean_distance,
    "euclidean_int": euclidean_interpolated,
    "pec": pec_distance,
    "frechet": frechet_dist_fast,
    "kl_divergence": kl_divergence_fast,
    "wasserstein": wasserstein_fast,
    "jaccard": jaccard_fast,
    "bray_curtis": bray_curtis_distance,
    "hausdorff": hausdorff_distance,
    "manhattan": manhattan_distance,
    "chi2": chi2_distance,
    "hellinger": hellinger_distance,
    "canberra": canberra_distance,
    "shannon_entropy": shannon_entropy_distance,
    "sample_entropy": sample_entropy_distance,
    "approx_entropy": approx_entropy_distance,
    "jensen_shannon": jensen_shannon_distance,
    "renyi_entropy": renyi_entropy_distance,
    "tsallis_entropy": tsallis_entropy_distance,
    "mutual_information": mutual_information_distance,
}



def calculate_distance_matrix(df, on="ticker", metric="dtw", feature=None):
    if metric not in distance_metrics:
        raise ValueError(f"Unknown metric: {metric}")

    df = df.reset_index()
    # df = df.sort_values([on, 'date'])

    if feature is not None and feature not in df.columns:
        raise ValueError(f"Feature '{feature}' not found in dataframe")

    numeric_cols = (
        [feature] if feature else df.select_dtypes(include=[np.number]).columns
    )

    has_missing = df[numeric_cols].isnull().any().any()
    if has_missing:
        missing_count = df[numeric_cols].isnull().sum().sum()
        print(
            f"Warning: dataframe has {missing_count} missing values. Imputed with median."
        )
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    tickers = df[on].unique()
    n = len(tickers)

    distance_matrix = np.zeros((n, n))
    metric_func = distance_metrics[metric]

    data_dict = {
        ticker: df[df[on] == ticker][numeric_cols].values for ticker in tickers
    }

    for i, ticker1 in enumerate(tickers):
        data1 = data_dict[ticker1]
        for j in range(i + 1, n):
            ticker2 = tickers[j]
            data2 = data_dict[ticker2]
            distance = metric_func(data1, data2)
            distance_matrix[i, j] = distance_matrix[j, i] = distance

    distance_matrix = normalize_min_max(distance_matrix)
    return pd.DataFrame(distance_matrix, index=tickers, columns=tickers)


import numpy as np
import pandas as pd
import tensorly as tl
from tensorly import unfold
from tensorly.decomposition import tucker, parafac
from sklearn.preprocessing import StandardScaler
from collections import OrderedDict
from scipy.spatial.distance import cosine


tl.set_backend('numpy')


def estimate_rank(tensor_data, explained_var_threshold=0.95):
    """Estimate rank for each mode based on explained variance."""
    ranks = []
    for mode in range(tensor_data.ndim):
        U, S, _ = np.linalg.svd(unfold(tensor_data, mode), full_matrices=False)
        explained_var = np.cumsum(S**2) / np.sum(S**2)
        rank = np.argmax(explained_var >= explained_var_threshold) + 1
        ranks.append(min(rank, tensor_data.shape[mode]))
    return ranks


def create_reconstruction(df_calc, rank=[10, 5, 5], method="tucker"):
    missing_mask = df_calc.isna()
    missing_count = missing_mask.sum().sum()
    if missing_count > 0:
        print(f"Warning: {missing_count} missing values detected. Imputed with median.")

    # Calculate medians only for columns with missing values
    columns_with_missing = missing_mask.any()
    medians = df_calc.loc[:, columns_with_missing].median()
    df_calc = df_calc.fillna(medians)

    # Get the unique tickers and dates, and sort them
    tickers = sorted(df_calc.index.get_level_values("ticker").unique())
    dates = sorted(df_calc.index.get_level_values("date").unique())

    # Create an OrderedDict to maintain ticker order
    ticker_order = OrderedDict((ticker, i) for i, ticker in enumerate(tickers))

    # Create a MultiIndex with all combinations of tickers and dates
    multi_index = pd.MultiIndex.from_product([tickers, dates], names=["ticker", "date"])

    # Reindex the DataFrame with the new MultiIndex and fill missing values with 0.5
    df_filled = df_calc.reindex(multi_index, fill_value=0.5)

    # Normalize the input data
    scaler = StandardScaler()
    df_normalized = pd.DataFrame(
        scaler.fit_transform(df_filled),
        index=df_filled.index,
        columns=df_filled.columns,
    )

    # Reshape the normalized data into a tensor
    tensor_data = np.array(df_normalized).reshape(
        len(tickers), len(dates), len(df_normalized.columns)
    )

    rank = estimate_rank(tensor_data, 0.95)
    print(f"Estimated rank: {rank}")

    # Apply tensor decomposition
    if method == "tucker":
        core, factors = tucker(tensor_data, rank=rank)
    elif method == "parafac":
        factors = parafac(tensor_data, rank=rank[0])
    else:
        raise ValueError("Invalid method. Choose 'tucker' or 'parafac'.")

    # Extract the factors
    ticker_factor = factors[0]
    date_factor = factors[1]
    feature_factor = factors[2]

    # Normalize the factor matrices
    normalized_ticker_factor = ticker_factor / np.linalg.norm(
        ticker_factor, axis=1, keepdims=True
    )
    normalized_date_factor = date_factor / np.linalg.norm(
        date_factor, axis=1, keepdims=True
    )
    normalized_feature_factor = feature_factor / np.linalg.norm(
        feature_factor, axis=1, keepdims=True
    )

    # Compute distance using cosine similarity
    def cosine_distance(X):
        return np.array([cosine(a, b) for a in X for b in X]).reshape(len(X), len(X))

    ticker_distance = cosine_distance(normalized_ticker_factor)
    date_distance = cosine_distance(normalized_date_factor)
    feature_distance = cosine_distance(normalized_feature_factor)

    # Ensure the ticker order is maintained in the final DataFrame
    ticker_dist_df = pd.DataFrame(ticker_distance, index=tickers, columns=tickers)
    ticker_dist_df = ticker_dist_df.reindex(index=tickers, columns=tickers)

    date_dist_df = pd.DataFrame(date_distance, index=dates, columns=dates)
    feature_dist_df = pd.DataFrame(
        feature_distance, index=df_filled.columns, columns=df_filled.columns
    )

    return ticker_dist_df, date_dist_df, feature_dist_df


def distance_calc(
    df_factors,
    orient="cross-sectional",
    on="date",
    distance="cosine",
    metric="pearson",
    calculations=["mean"],
):
    if orient == "time-series":
        result = calculate_distance_matrix(df_factors, on=on, metric=metric)

    elif orient == "panel":
        ticker_sim_df, date_sim_df, feature_sim_df = create_reconstruction(df_factors)
        if on == "date":
            return date_sim_df
        else:
            return ticker_sim_df
    else:
        result, agg_df = distance_cross(
            df_factors, on=on, metric_list=calculations, distance=distance
        )

    return result



def relative_distance_calc(
    df_factors,
    orient="cross-sectional",
    on="date",
    distance="cosine",
    metric="pearson",
    calculations=["mean"],
):
    """
    Calculates the relative distance matrix based on the initial distance calculation
    and then computes the bar S matrix.

    :param df_factors: DataFrame containing the data.
    :param orient: Orientation for the initial distance calculation.
    :param on: The level to group on ('ticker' or 'date').
    :param distance: The distance metric to use ('cosine', 'euclidean', etc.).
    :param metric: The metric to use for time-series distance calculation.
    :param calculations: List of calculations to perform in distance_cross.
    :return: DataFrame representing the normalized bar S matrix.
    """
    # First, calculate the initial distance matrix
    distance_matrix = distance_calc(
        df_factors,
        orient=orient,
        on=on,
        distance=distance,
        metric=metric,
        calculations=calculations,
    )

    # Now, proceed with the relative distance calculation
    shape = distance_matrix.shape
    if shape[0] != shape[1]:
        raise ValueError('You have to pass a square matrix')

    cosine_similarity = distance_matrix.values
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
        bar_S_matrix,
        index=distance_matrix.index,
        columns=distance_matrix.columns,
    )

    return bar_S_matrix



