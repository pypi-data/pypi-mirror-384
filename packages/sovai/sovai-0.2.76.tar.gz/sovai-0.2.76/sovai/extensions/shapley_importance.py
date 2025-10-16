import pandas as pd
import numpy as np
import random
from lightgbm import LGBMClassifier
from sklearn.cluster import KMeans, MeanShift, HDBSCAN
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.preprocessing import StandardScaler
import shap
from joblib import Parallel, delayed
import hashlib
from scipy import stats
import os
import warnings

def hash_of_df(df, sample_size=100):
    df_sample = (
        df.sample(n=min(sample_size, len(df)), random_state=42).to_string().encode()
    )
    return hashlib.sha256(df_sample).hexdigest()

class ClusteringExplainer:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = None
        self.shap_values = None

    def fit(self, X, y):
        classes_weights = compute_sample_weight(class_weight="balanced", y=y)
        self.model = LGBMClassifier(
            objective="multiclass", random_state=self.random_state
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(X, y, sample_weight=classes_weights)
        explainer = shap.Explainer(self.model)
        self.shap_values = explainer(X)

    def get_shap_values_df(self, X):
        mean_shap_values = np.abs(self.shap_values.values).mean(axis=1)
        return pd.DataFrame(mean_shap_values, columns=X.columns)

def simulation_task(df, i, clustering_method, kmeans_random_state, lgbm_random_state):
    X = df.sample(n=min(5000, len(df)), random_state=i).reset_index(drop=True)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if clustering_method == "KMEANS":
        num_clusters = random.randint(5, 10)
        clustering = KMeans(n_clusters=num_clusters, random_state=kmeans_random_state)
    elif clustering_method == "MEANSHIFT":
        clustering = MeanShift()
    elif clustering_method == "HDBSCAN":
        clustering = HDBSCAN(min_cluster_size=5)
    else:
        raise ValueError(f"Unsupported clustering method: {clustering_method}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clustering.fit(X_scaled)

    y = clustering.labels_
    if clustering_method == "HDBSCAN":
        noise_label = max(y) + 1
        y[y == -1] = noise_label

    clust_explnr = ClusteringExplainer(random_state=lgbm_random_state)
    clust_explnr.fit(X_scaled, y)
    return clust_explnr.get_shap_values_df(X)

def run_simulations_frame(df, num_simulations=4, clustering_method="KMEANS"):
    data_hash = hash_of_df(df)
    tasks = []
    for i in range(num_simulations):
        random.seed(int(data_hash, 16) + i)
        kmeans_random_state = random.randint(0, 1000)
        lgbm_random_state = random.randint(0, 1000)
        tasks.append(
            delayed(simulation_task)(
                df, i, clustering_method, kmeans_random_state, lgbm_random_state
            )
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        all_shap_values = Parallel(n_jobs=-1, verbose=0)(tasks)

    avg_shap_values = pd.concat(all_shap_values).groupby(level=0).mean()
    # avg_shap_values.index = df.index

    feature_importance = pd.DataFrame(
        {
            "feature": avg_shap_values.columns,
            "importance": avg_shap_values.mean().values,
        }
    )
    feature_importance["importance_percentile"] = stats.percentileofscore(
        feature_importance["importance"], feature_importance["importance"]
    )
    return feature_importance.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)

# Usage example:
# importance_df = run_simulations(df, num_simulations=4, clustering_method='KMEANS')