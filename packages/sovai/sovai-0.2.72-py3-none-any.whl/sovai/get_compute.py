# Inside plot/get_plot.py ##
from .computations.functions import *

COMPUTE_FUNCTION_MAPPER = {
    ("process-pca-plot"): process_pca_plot,
    ("process-bankrupt-plot"): process_bankrupt_plot,
    ("map-accounting-features"): map_bankrupt_features,
    ("risk-aggregates"): more_risk_aggregates
    # Add other mappings as needed
}


def compute(compute_name=None, df=None, **kwargs):
    # Validate input
    if df is None:
        raise ValueError("DataFrame is required")

    # Find the compute function in the mapper
    compute_function = COMPUTE_FUNCTION_MAPPER.get(compute_name)
    if compute_function is None:
        # Handle case where compute_name is not found
        raise ValueError(f"Compute function '{compute_name}' not found")

    # Call the compute function with the DataFrame and any additional keyword arguments
    return compute_function(df, **kwargs)
