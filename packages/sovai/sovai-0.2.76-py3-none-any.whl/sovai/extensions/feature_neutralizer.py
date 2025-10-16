import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.linalg import qr, svd
import warnings


def gram_schmidt_orthogonalization(df):
    """
    Applies Gram-Schmidt process to orthogonalize the features of the DataFrame.
    Returns a new DataFrame with orthogonalized features in the original scale.
    """
    X = df.values
    scaler = StandardScaler()
    X_standardized = scaler.fit_transform(X)
    n_features = X_standardized.shape[1]
    Q = np.zeros_like(X_standardized)
    for i in range(n_features):
        q = X_standardized[:, i]
        for j in range(i):
            q = q - np.dot(Q[:, j], X_standardized[:, i]) * Q[:, j]
        Q[:, i] = q / np.linalg.norm(q)
    # Inverse transform to original scale
    Q_inverse_transformed = scaler.inverse_transform(Q)
    return pd.DataFrame(Q_inverse_transformed, columns=df.columns, index=df.index)


def pca_neutralization(df):
    """
    Neutralizes features using PCA by removing all but the last principal component.
    """
    scaler = StandardScaler()
    X_standardized = scaler.fit_transform(df)

    pca = PCA(n_components=df.shape[1])
    X_pca = pca.fit_transform(X_standardized)

    # Zero out all but the last component
    X_pca[:, :-1] = 0

    # Transform back to original space
    X_neutralized = pca.inverse_transform(X_pca)

    # Inverse transform to original scale
    X_inverse_transformed = scaler.inverse_transform(X_neutralized)

    return pd.DataFrame(X_inverse_transformed, columns=df.columns, index=df.index)


def qr_neutralization(df):
    """
    Neutralizes features using QR decomposition.
    """
    scaler = StandardScaler()
    X_standardized = scaler.fit_transform(df)

    Q, R = qr(X_standardized, mode="economic")

    # Inverse transform to original scale
    Q_inverse_transformed = scaler.inverse_transform(Q)

    return pd.DataFrame(Q_inverse_transformed, columns=df.columns, index=df.index)


def svd_neutralization(df):
    """
    Neutralizes features using SVD by setting all but the smallest singular value to zero.
    """
    scaler = StandardScaler()
    X_standardized = scaler.fit_transform(df)

    U, s, Vt = svd(X_standardized, full_matrices=False)

    # Zero out all but the last singular value
    s[:-1] = 0

    # Reconstruct the matrix
    X_neutralized = U @ np.diag(s) @ Vt

    # Inverse transform to original scale
    X_inverse_transformed = scaler.inverse_transform(X_neutralized)

    return pd.DataFrame(X_inverse_transformed, columns=df.columns, index=df.index)


def iterative_regression_neutralization(df, max_iter=100, tol=1e-6):
    """
    Neutralizes features using iterative regression.
    """
    X = df.values
    scaler = StandardScaler()
    X_standardized = scaler.fit_transform(X)

    n_features = X_standardized.shape[1]
    X_neutralized = X_standardized.copy()

    for _ in range(max_iter):
        X_prev = X_neutralized.copy()

        for i in range(n_features):
            y = X_standardized[:, i]
            X_others = np.delete(X_neutralized, i, axis=1)

            beta = np.linalg.lstsq(X_others, y, rcond=None)[0]
            X_neutralized[:, i] = y - X_others @ beta

        if np.max(np.abs(X_neutralized - X_prev)) < tol:
            break

    # Inverse transform to original scale
    X_inverse_transformed = scaler.inverse_transform(X_neutralized)

    return pd.DataFrame(X_inverse_transformed, columns=df.columns, index=df.index)


def orthogonalize_features_function(df, method="gram_schmidt"):
    """
    Orthogonalizes the features of the DataFrame using the specified method.

    Parameters:
    method (str): Method to use for orthogonalization.
                  Options: 'gram_schmidt', 'qr'

    Returns:
    CustomDataFrame: DataFrame with orthogonalized features
    """
    orthogonalization_methods = {
        "gram_schmidt": gram_schmidt_orthogonalization,
        "qr": qr_neutralization,  # Note: This is actually orthogonalization when used this way
    }

    if method not in orthogonalization_methods:
        raise ValueError(
            f"Invalid orthogonalization method. Choose from: {', '.join(orthogonalization_methods.keys())}"
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        orthogonalized_features = orthogonalization_methods[method](df)

    return orthogonalized_features


def neutralize_features_function(df, method="pca"):
    """
    Neutralizes the features of the DataFrame using the specified method.

    Parameters:
    method (str): Method to use for neutralization.
                  Options: 'pca', 'svd', 'iterative_regression'

    Returns:
    CustomDataFrame: DataFrame with neutralized features
    """
    neutralization_methods = {
        "pca": pca_neutralization,
        "svd": svd_neutralization,
        "iterative_regression": iterative_regression_neutralization,
    }

    if method not in neutralization_methods:
        raise ValueError(
            f"Invalid neutralization method. Choose from: {', '.join(neutralization_methods.keys())}"
        )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        neutralized_features = neutralization_methods[method](df)

    return neutralized_features
