# Lightweight built-in imports can stay global
import random
import hashlib
import warnings
# import os # Removed as it was unused

# Note: Imports below are moved into functions/methods to defer loading cost,
# potentially speeding up the initial import of this script.

def hash_of_df(df, sample_size=100):
    """Calculates a SHA256 hash of a sampled portion of a DataFrame."""
    # Import pandas here as it's needed for DataFrame operations
    import pandas as pd

    df_sample = (
        df.sample(n=min(sample_size, len(df)), random_state=42).to_string().encode()
    )
    return hashlib.sha256(df_sample).hexdigest()

class ClusteringExplainer:
    """
    Trains a classifier to predict cluster labels and provides SHAP explanations.
    """
    def __init__(self, random_state=42):
        """Initializes the explainer and scaler."""
        # Import StandardScaler here as it's used for self.scaler
        from sklearn.preprocessing import StandardScaler

        self.random_state = random_state
        self.model = None
        self.explainer = None
        # Initialize scaler here after import
        self.scaler = StandardScaler()

    def fit(self, X, y):
        """Fits the LGBM classifier and creates the SHAP explainer."""
        # Imports needed specifically for fitting the model and explainer
        from lightgbm import LGBMClassifier
        from sklearn.utils.class_weight import compute_sample_weight
        import shap

        classes_weights = compute_sample_weight(class_weight="balanced", y=y)
        self.model = LGBMClassifier(
            objective="multiclass",
            random_state=self.random_state,
            verbose=-1,
            force_col_wise=True,
            min_gain_to_split=0.01
        )
        # Catch warnings during model fitting (e.g., from LightGBM)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(X, y, sample_weight=classes_weights)

        # Create SHAP explainer after model is trained
        self.explainer = shap.Explainer(self.model)

    def get_shap_values(self, X):
        """Gets SHAP values using the trained explainer."""
        # No new imports needed here, uses self.explainer created in fit()
        if self.explainer is None:
            raise RuntimeError("Explainer not available. Call fit() method first.")
        return self.explainer(X)

def get_shap_values_for_dataset(df, clustering_method="KMEANS", n_clusters=10, random_state=42, sample_size=5000):
    """
    Performs clustering, trains a model, and calculates mean absolute SHAP values.
    """
    # Imports needed for this function's operations
    import pandas as pd
    import numpy as np
    from sklearn.cluster import KMeans, MeanShift, HDBSCAN
    from sklearn.preprocessing import StandardScaler # Needed again for local scaler instance

    # Sample for clustering and model training
    X_sample = df.sample(n=min(sample_size, len(df)), random_state=random_state)

    # Create and fit a local scaler for the sample
    scaler = StandardScaler()
    X_sample_scaled = scaler.fit_transform(X_sample)

    # Select and fit the clustering algorithm
    if clustering_method == "KMEANS":
        # Use random module (imported globally)
        num_clusters = random.randint(5, 10)
        clustering = KMeans(n_clusters=num_clusters, random_state=random_state, n_init=10) # Added n_init
    elif clustering_method == "MEANSHIFT":
        clustering = MeanShift()
    elif clustering_method == "HDBSCAN":
        clustering = HDBSCAN(min_cluster_size=5)
    else:
        raise ValueError(f"Unsupported clustering method: {clustering_method}")

    # Catch warnings during clustering (e.g., convergence warnings)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clustering.fit(X_sample_scaled)

    y_sample = clustering.labels_

    # Handle noise points from HDBSCAN if necessary
    if clustering_method == "HDBSCAN":
        # Check if noise points exist (-1 label)
        if -1 in y_sample:
            noise_label = np.max(y_sample) + 1
            y_sample[y_sample == -1] = noise_label # Assign noise points to a new cluster index

    # Create and fit the explainer using the clustered sample
    clust_explnr = ClusteringExplainer(random_state=random_state)
    clust_explnr.fit(X_sample_scaled, y_sample) # This triggers imports within ClusteringExplainer.fit

    # Transform the entire dataset using the scaler fitted on the sample
    X_full_scaled = scaler.transform(df)

    # Get SHAP values for the entire scaled dataset
    shap_values = clust_explnr.get_shap_values(X_full_scaled)

    # Calculate mean absolute SHAP values across classes for each feature
    # shap_values.values is typically (n_samples, n_features, n_classes) or (n_samples, n_features)
    if len(shap_values.values.shape) == 3:
         mean_abs_shap = np.mean(np.abs(shap_values.values), axis=2)
    else: # If it's already 2D (e.g., binary classification or regression SHAP)
         mean_abs_shap = np.abs(shap_values.values)

    # Create DataFrame for the results
    mean_abs_shap_df = pd.DataFrame(mean_abs_shap, columns=df.columns, index=df.index)

    return mean_abs_shap_df

def run_simulations_frame_global(df, num_simulations=4, clustering_method="KMEANS"):
    """
    Runs multiple simulations of SHAP value calculation in parallel and averages.
    """
    # Imports needed for parallel execution and DataFrame manipulation
    from joblib import Parallel, delayed
    import pandas as pd

    data_hash = hash_of_df(df) # Uses function defined above (triggers its pandas import if first call)
    tasks = []
    for i in range(num_simulations):
        # Use random module (imported globally)
        # Seed random state for reproducibility within the loop based on data hash
        current_seed = int(data_hash, 16) + i
        random.seed(current_seed)
        # Generate distinct random states for clustering and model training per simulation
        sim_random_state = random.randint(0, 2**32 - 1) # Use a large range for random state

        tasks.append(
            delayed(get_shap_values_for_dataset)(
                df, clustering_method, 10, sim_random_state # Pass simulation-specific state
            )
        ) # This implicitly calls get_shap_values_for_dataset (triggering its imports)

    # Catch warnings during parallel execution
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Run tasks in parallel, n_jobs=-1 uses all available CPU cores
        all_shap_values = Parallel(n_jobs=-1, verbose=0)(tasks)

    # Concatenate results and calculate the mean SHAP values grouped by index
    # Assumes df.index is a MultiIndex with 'ticker' and 'date' levels
    if isinstance(df.index, pd.MultiIndex) and all(level in df.index.names for level in ['ticker', 'date']):
         avg_shap_values = pd.concat(all_shap_values).abs().groupby(level=["ticker", "date"]).mean()
    else:
         # Fallback if index is not the expected MultiIndex (might need adjustment)
         # This assumes the index from the original df was preserved in mean_abs_shap_df
         # The previous reset_index().groupby() might be safer if index structure varies
         print("Warning: DataFrame index is not a MultiIndex with 'ticker' and 'date'. Averaging over the entire index.")
         avg_shap_values = pd.concat(all_shap_values).abs().mean()


    return avg_shap_values

def run_simulations_global_importance(df, num_simulations=4, clustering_method="KMEANS"):
    """
    Calculates overall feature importance based on averaged SHAP values.
    """
    # Imports needed for DataFrame creation and statistical calculation
    import pandas as pd
    from scipy import stats

    # Get the averaged SHAP values per instance/group
    avg_shap_values = run_simulations_frame_global(
        df, num_simulations=num_simulations, clustering_method=clustering_method
        ) # Triggers imports in run_simulations_frame_global if not already loaded

    # Calculate the mean importance across all instances/groups for each feature
    feature_importance_values = avg_shap_values.mean(axis=0)

    # Create the feature importance DataFrame
    feature_importance = pd.DataFrame(
        {
            "feature": feature_importance_values.index,
            "importance": feature_importance_values.values,
        }
    )

    # Calculate percentile rank for each feature's importance
    feature_importance["importance_percentile"] = feature_importance["importance"].apply(
        lambda x: stats.percentileofscore(feature_importance["importance"], x, kind='rank')
    )
    # Alternative using numpy might be faster for large numbers of features:
    # feature_importance["importance_percentile"] = feature_importance["importance"].rank(pct=True) * 100

    # Sort by importance percentile descending
    return feature_importance.sort_values(
        "importance_percentile", ascending=False
    ).reset_index(drop=True)


# Usage example:
# Assuming 'df' is your pandas DataFrame with features and a MultiIndex ('ticker', 'date')
# importance_df = run_simulations_global_importance(df, num_simulations=10, clustering_method='KMEANS')
# print(importance_df)