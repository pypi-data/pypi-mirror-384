import numpy as np
import numba

## nice examples here https://github.com/ulf1/numpy-fracdiff/blob/main/examples/profile-fractional-differentiation.ipynb


@numba.njit(cache=True)
def frac_weights_5(d: float, m: int) -> np.ndarray:
    w = [1.0]  # Use 1.0 instead of 1 to ensure float type
    for k in range(1, m + 1):
        w.append(-w[-1] * ((d - k + 1) / k))
    return np.array(w)

def fractional_diff(series, d, m):
    weights = frac_weights_5(d, m)
    return series.rolling(window=len(weights), min_periods=1).apply(
        lambda x: np.dot(x, weights[: len(x)]), raw=True
    )