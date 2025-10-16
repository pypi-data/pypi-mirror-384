import pandas as pd
import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD, FactorAnalysis
from sklearn.random_projection import GaussianRandomProjection
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

import warnings


import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def fillna_df(df, verbose=False):
    """Preprocess the panel data."""
    try:
        # Check for inf values
        has_inf = np.isinf(df.values).any()
        if has_inf:
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            if verbose:
                print("Replaced inf values with NaN")
        
        # Check for NaN values
        has_nan = df.isna().any().any()
        if has_nan:
            if verbose:
                print("NaN values found. Filling...")
            df = df.groupby(level="ticker").ffill()
            df = df.groupby(level="ticker").bfill()
            
            # Check if there are still NaNs after filling
            remaining_nan = df.isna().any().any()
            if remaining_nan:
                if verbose:
                    print("Some NaN values could not be filled. Dropping those rows.")
                df.dropna(inplace=True)
            else:
                if verbose:
                    print("All NaN values successfully filled")
        else:
            if verbose:
                print("No NaN values found. Skipping fill operations.")
        
        if verbose:
            print("Final shape:", df.shape)
        return df
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        return None

def check_and_scale_data(df):
    """
    Check if data is scaled in any fashion, and scale it only if it's not scaled.
    Returns:
    - pd.DataFrame: Original or scaled data
    """
    # Convert to numpy array for faster operations
    data = df.values
    
    # Compute stats using numpy (much faster than pandas)
    means = np.mean(data, axis=0)
    stds = np.std(data, axis=0)
    mins = np.min(data, axis=0)
    maxs = np.max(data, axis=0)
    ranges = maxs - mins

    # Check if data is already scaled in any fashion
    is_scaled = (
        np.all(ranges < 2) or  # This covers 0-1 scaling, z-score, and other common scalings
        (np.all(np.abs(means) < 1) and np.all(stds < 10)) or  # More relaxed check for any reasonable scaling
        np.all(np.divide(ranges, np.abs(means), out=np.ones_like(ranges), where=means!=0) < 10)  # Check if the range is not too large compared to the mean
    )

    if is_scaled:
        # print("Data appears to be already scaled. Skipping scaling operation.")
        return df
    
    # If not scaled in any sense, apply StandardScaler
    print("Data is not scaled. Applying StandardScaler.")
    scaler = StandardScaler(with_mean=True, with_std=True)
    scaled_data = scaler.fit_transform(data)
    
    # Return as DataFrame
    return pd.DataFrame(scaled_data, index=df.index, columns=df.columns)

def postprocess_reduced_data(reduced_data, original_df):
    """Convert reduced data back to panel format."""
    try:
        result_df = pd.DataFrame(
            reduced_data,
            index=original_df.index,
            columns=[f"component_{i}" for i in range(reduced_data.shape[1])],
        )
        return result_df
    except Exception as e:
        print(f"Error in postprocessing: {e}")
        return None

import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD, FactorAnalysis
from sklearn.random_projection import GaussianRandomProjection

def dimensionality_reduction(df, method, explained_variance=0.95, n_components=None, random_state=42):
    """
    Apply dimensionality reduction technique.
    
    Parameters:
    - df: pandas DataFrame
    - method: str, dimensionality reduction method
    - explained_variance: float, amount of variance to be explained (default: 0.95)
    - n_components: int or None, number of components (takes precedence over explained_variance if provided)
    - random_state: int, random state for reproducibility
    
    Returns:
    - reduced_data: pandas DataFrame with reduced dimensions
    """
    df = fillna_df(df)
    df = check_and_scale_data(df)
    
    reducer_methods = {
        "pca": PCA,
        "truncated_svd": TruncatedSVD,
        "factor_analysis": FactorAnalysis,
        "gaussian_random_projection": GaussianRandomProjection,
        
    }
    
    if n_components is not None:
        reducer = reducer_methods[method](n_components=n_components, random_state=random_state)
    else:
        if method in ["pca", "truncated_svd"]:
            # For PCA and TruncatedSVD, we can use explained_variance
            temp_reducer = reducer_methods[method](n_components=min(df.shape[1], df.shape[0]), random_state=random_state)
            temp_reducer.fit(df)
            cumulative_variance_ratio = np.cumsum(temp_reducer.explained_variance_ratio_)
            n_components = np.argmax(cumulative_variance_ratio >= explained_variance) + 1
        else:
            # For other methods, use a proportion of features
            n_components = max(1, int(df.shape[1] * explained_variance))
        
        reducer = reducer_methods[method](n_components=n_components, random_state=random_state)
    
    reduced_data = reducer.fit_transform(df)
    reduced_data = postprocess_reduced_data(reduced_data, df)
    
    return reduced_data