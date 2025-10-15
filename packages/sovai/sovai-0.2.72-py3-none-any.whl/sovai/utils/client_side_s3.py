import pyarrow.dataset as ds
from pyarrow.fs import S3FileSystem
import pyarrow as pa
import pandas as pd
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from sovai.tools.authentication import authentication


# Try to import CustomDataFrame, use regular DataFrame if not available
try:
    from sovai.extensions.pandas_extensions import CustomDataFrame
    HAS_CUSTOM_DATAFRAME = True
except ImportError:
    HAS_CUSTOM_DATAFRAME = False
    CustomDataFrame = pd.DataFrame  # Fallback to regular DataFrame


@lru_cache(maxsize=2)
def get_cached_s3_filesystem(storage_provider):
    return authentication.get_s3_filesystem_pickle(storage_provider, verbose=True)

def process_partition(storage_provider, base_path, identifier_column, identifier=None, columns=None, filters=None):
    s3 = get_cached_s3_filesystem(storage_provider)
    
    if identifier:
        base_path += f"/{identifier_column}={identifier}"
    
    dataset = ds.dataset(base_path, filesystem=s3, format='parquet')
    
    if filters:
        operator_map = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            'in': lambda a, b: a.isin(b),
            'not in': lambda a, b: ~a.isin(b),
            'like': lambda a, b: a.match_substring(b),
        }
        schema = dataset.schema
        filter_expr = None
        for col, op, val in filters:
            if op not in operator_map:
                raise ValueError(f"Unsupported operator '{op}' in filters.")
            field = ds.field(col)
            field_type = schema.field(col).type
            if pa.types.is_timestamp(field_type) or pa.types.is_date(field_type):
                val = pd.to_datetime(val)
            elif pa.types.is_integer(field_type):
                val = int(val)
            elif pa.types.is_floating(field_type):
                val = float(val)
            condition = operator_map[op](field, val)
            filter_expr = condition if filter_expr is None else filter_expr & condition
    else:
        filter_expr = None
    
    table = dataset.to_table(columns=columns, filter=filter_expr, use_threads=True)
    df = table.to_pandas(use_threads=True)
    
    if identifier:
        df[identifier_column] = identifier

        df = df[[identifier_column] + [col for col in df.columns if col != identifier_column]]

    
    return df

import numpy as np

def client_side_s3_frame(config, identifiers, columns, start_date, end_date):
    storage_provider = "digitalocean"  # Default to DigitalOcean
    base_path = config["storage_provider"][storage_provider]
    identifier_column = config.get("identifier_column")

    filters = []
    if start_date:
        filters.append(('date', '>=', start_date))
    if end_date:
        filters.append(('date', '<=', end_date))

    if not identifiers:
        # Load the entire database
        return process_partition(storage_provider, base_path, identifier_column, columns=columns, filters=filters)
    else:
        identifiers = map_identifier(identifiers, input_identifier='ticker', output_identifier=identifier_column)

    # Use numpy.isscalar to check if identifiers is a single value
    if np.isscalar(identifiers):
        # Single identifier
        identifier = identifiers
        return process_partition(storage_provider, base_path, identifier_column, identifier=identifier, columns=columns, filters=filters)
    
    # Multiple identifiers
    with ThreadPoolExecutor() as executor:
        futures = []
        for identifier in identifiers:
            futures.append(executor.submit(process_partition, storage_provider, base_path, identifier_column, identifier, columns, filters))
        
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    
    df = pd.concat(results, ignore_index=True)
    return df

    # if 'filing_date' in df.columns:
    #     df['date'] = pd.to_datetime(df['filing_date'])
    # elif 'date' not in df.columns:
    #     raise ValueError("Neither 'filing_date' nor 'date' column found in the data")
    
    # df.set_index([identifier_column, 'date'], inplace=True)
    # df.sort_index(inplace=True)
    
    return df

import pandas as pd
import numpy as np

def map_identifier(input_values, input_identifier='ticker', output_identifier='cik', trailing_zero_removal=True):
    """
    Map from one identifier to another using the df_codes DataFrame.
    Handles string, single-item list, and multiple-item lists as input.
    Uses vectorization for improved performance.
    
    :param input_values: The input identifier value(s) to map from (string, list, or array-like)
    :param input_identifier: The type of input identifier (default: 'ticker')
    :param output_identifier: The type of output identifier (default: 'cik')
    :param trailing_zero_removal: If True, convert CIK to int (default: True)
    :return: Mapped identifier value(s), same type as input
    """
    df_codes = pd.read_parquet("data/codes.parq")

    # Check if the identifier columns exist in df_codes
    if input_identifier not in df_codes.columns or output_identifier not in df_codes.columns:
        raise ValueError(f"Identifier '{input_identifier}' or '{output_identifier}' not found in the DataFrame")
    
    # Convert input to numpy array for consistent handling
    if isinstance(input_values, str):
        input_array = np.array([input_values])
        input_is_string = True
    else:
        input_array = np.array(input_values)
        input_is_string = False
    
    # Ensure all input values are strings
    input_array = np.char.strip(input_array.astype(str))
    
    # Create a dictionary for fast lookup
    mapping_dict = dict(zip(df_codes[input_identifier], df_codes[output_identifier]))
    
    # Vectorized mapping
    result = np.vectorize(mapping_dict.get)(input_array)
    
    # Convert to int if trailing_zero_removal is True and output is CIK
    if trailing_zero_removal and output_identifier.lower() == 'cik':
        result = np.where(result == None, 0, result)  # Replace None with 0
        result = result.astype(np.int32)  # Convert to int64
    
    # Return result in the same format as input
    if input_is_string:
        return result[0]
    elif len(input_array) == 1:
        return result[0]
    else:
        return result.tolist()



def load_frame_s3(endpoint, tickers=None, columns=None, start_date=None, end_date=None):

    endpoint_config = {
        "sec/10k": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-filings/tenk",
                "wasabi": "sovai-filings/tenk"
            },
            "identifier_column": "cik",
            "partitioned": True,
    
        },
        "patents/applications": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-patents-export/applications",
                "wasabi": "sovai-patents-export/applications"
            },
            "identifier_columns": ["date_partitioned", "ticker_partitioned"],
            "partitioned": True,
        },
        "trials/predict": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-clinical-trials-export/prediction_public",
                "wasabi": "sovai-clinical-trials-export/prediction_public"
            },
            "identifier_column": "ticker",
            "partitioned": True,
        },
        "trials/describe": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-clinical-trials-export/describe_public",
                "wasabi": "sovai-clinical-trials-export/describe_public"
            },
            "identifier_column": "ticker",
            "partitioned": True,
        },
        "trials/all": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-clinical-trials-export/describe_all",
                "wasabi": "sovai-clinical-trials-export/describe_all"
            },
            "identifier_column": "ticker",
            "partitioned": True,
        },
        "trials/all/predict": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-clinical-trials-export/prediction_all",
                "wasabi": "sovai-clinical-trials-export/prediction_all"
            },
            "identifier_column": "ticker",
            "partitioned": True,
        },
        "trials/all/decribe": {
            "storage_provider": {
                "digitalocean": "sovai/sovai-clinical-trials-export/describe_all",
                "wasabi": "sovai-clinical-trials-export/describe_all"
            },
            "identifier_column": "ticker",
            "partitioned": True,
        },
    }
    
    if endpoint not in endpoint_config:
        raise ValueError(f"Invalid endpoint: {endpoint}")
    
    config = endpoint_config[endpoint]

    
    
    df_frame = client_side_s3_frame(
        config,
        tickers,
        columns,
        start_date,
        end_date
    )

    
    if HAS_CUSTOM_DATAFRAME:
        return CustomDataFrame(df_frame)
    else:
        return df_frame  # Returns a regular pandas DataFrame if CustomDataFrame is not available

