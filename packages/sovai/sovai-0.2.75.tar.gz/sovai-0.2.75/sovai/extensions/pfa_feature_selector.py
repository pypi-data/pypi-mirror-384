import pandas as pd
import numpy as np
import random
import hashlib
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import euclidean_distances
from collections import defaultdict
from joblib import Parallel, delayed
from scipy import stats


def hash_of_df(df, sample_size=100):
    df_sample = df.head(min(sample_size, len(df))).to_string().encode()
    return hashlib.sha256(df_sample).hexdigest()


class PFA(object):
    def __init__(self, n_features_to_select=None):
        self.n_features_to_select = n_features_to_select

    def fit_transform(self, X, kmeans_random_state):
        sc = StandardScaler()
        X = sc.fit_transform(X)
        pca = PCA().fit(X)
        A_q = pca.components_.T

        n_features_to_select = self.n_features_to_select or max(1, X.shape[1] // 2)
        clusternumber = min(n_features_to_select, X.shape[1])

        kmeans = KMeans(n_clusters=clusternumber, random_state=kmeans_random_state).fit(
            A_q
        )
        clusters = kmeans.predict(A_q)
        cluster_centers = kmeans.cluster_centers_
        dists = defaultdict(list)
        for i, c in enumerate(clusters):
            dist = euclidean_distances([A_q[i, :]], [cluster_centers[c, :]])[0][0]
            dists[c].append((i, dist))

        selected_features = []
        for cluster in dists:
            selected_feature = min(dists[cluster], key=lambda x: x[1])
            selected_features.append(selected_feature)

        return dict(selected_features)


def run_pfa_simulations(df, num_simulations=4, n_features_to_select=None):
    warnings.filterwarnings("ignore", category=UserWarning)
    data_hash = hash_of_df(df)
    feature_distances = defaultdict(list)
    tasks = []

    for i in range(num_simulations):
        random.seed(int(data_hash, 16) + i)
        kmeans_random_state = random.randint(0, 1000)
        pfa = PFA(n_features_to_select)
        tasks.append(delayed(pfa.fit_transform)(df.values, kmeans_random_state))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        simulation_results = Parallel(n_jobs=-1)(tasks)

    for result in simulation_results:
        for feature, distance in result.items():
            feature_distances[feature].append(distance)

    # Calculate average distance (lower is better)
    avg_distances = {
        feature: np.mean(distances) if distances else np.inf
        for feature, distances in feature_distances.items()
    }

    # Create DataFrame with results
    result_df = pd.DataFrame(
        {
            "feature": df.columns,
            "importance": [
                1 / (avg_distances.get(i, np.inf) + 1e-10)
                for i in range(len(df.columns))
            ],
        }
    )

    # Calculate percentiles (higher is better)
    result_df["importance_percentile"] = stats.percentileofscore(
        result_df["importance"], result_df["importance"]
    )

    # Sort by importance percentile in descending order
    result_df = result_df.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

    return result_df


# Usage
# df_importance = run_pfa_simulations(df_returns, num_simulations=4, n_features_to_select=30)
