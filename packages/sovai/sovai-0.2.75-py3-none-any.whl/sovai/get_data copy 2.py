from typing import Optional, Union, Tuple, List, Dict, Any, Callable, TypeVar
import re
import time
import functools
from datetime import datetime
import hashlib
import json
import logging
from collections import defaultdict
from functools import lru_cache
from io import BytesIO

# Third-party imports
import pandas as pd
import numpy as np
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError
import boto3
import polars as pl
import pyarrow.parquet as pq
import plotly.graph_objects as go

# Local imports
from sovai.api_config import ApiConfig
from sovai.errors.sovai_errors import InvalidInputData
from sovai.utils.converter import convert_data2df, process_dataframe
from sovai.utils.stream import stream_data, stream_data_pyarrow
from sovai.utils.datetime_formats import datetime_format
from sovai.utils.client_side import client_side_frame
from sovai.utils.client_side_s3 import load_frame_s3
from sovai.utils.client_side_s3_part_high import load_frame_s3_partitioned_high
from sovai.utils.verbose_utils import verbose_mode

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic return types
T = TypeVar('T')
DataFrameType = Union[pd.DataFrame, pl.DataFrame, 'CustomDataFrame']

# Check for full installation
try:
   from sovai.extensions.pandas_extensions import CustomDataFrame
   from sovai.utils.plot import plotting_data
   HAS_FULL_INSTALL = True
except ImportError:
   HAS_FULL_INSTALL = False
   logger.warning("Running with limited installation. Some features unavailable.")


def is_full_installation() -> bool:
   """
   Check if the full package is installed including optional dependencies.
   
   Returns:
       bool: True if full installation is available, False otherwise
   """
   return HAS_FULL_INSTALL


# Global cache for query results
_query_cache = {}


class ApiRequestHandler:
   """
   Centralized handler for API requests with robust error handling,
   automatic retry capability, and consistent response processing.
   
   This class encapsulates all HTTP communication logic, providing:
   - Consistent authentication and headers
   - Configurable retry policies with exponential backoff
   - Proper error handling and logging
   - Timeout management
   """
   
   def __init__(
       self,
       base_url: str,
       token: str,
       verify_ssl: bool = True,
       max_retries: int = 3,
       backoff_factor: float = 0.5,
       timeout: tuple = (5, 30),  # (connect timeout, read timeout)
       logger: Optional[logging.Logger] = None
   ):
       """
       Initialize the API request handler.
       
       Args:
           base_url: Base URL for the API
           token: Authentication token
           verify_ssl: Whether to verify SSL certificates
           max_retries: Maximum number of retry attempts for failed requests
           backoff_factor: Factor to determine wait time between retries
           timeout: Tuple of (connection timeout, read timeout) in seconds
           logger: Optional logger instance; uses module logger if not provided
       """
       self.base_url = base_url.rstrip('/')
       self.token = token
       self.verify_ssl = verify_ssl
       self.max_retries = max_retries
       self.backoff_factor = backoff_factor
       self.timeout = timeout
       self.headers = {"Authorization": f"Bearer {token}"}
       self.logger = logger or logging.getLogger(__name__)
   
   def _should_retry(self, exception: Exception, attempt: int) -> bool:
       """
       Determine if a failed request should be retried.
       
       Args:
           exception: The exception that occurred
           attempt: Current attempt number (1-based)
           
       Returns:
           True if request should be retried, False otherwise
       """
       # Don't retry if we've hit the max attempts
       if attempt >= self.max_retries:
           return False
       
       # Retry on connection issues
       if isinstance(exception, ConnectionError):
           return True
       
       # Retry on timeouts
       if isinstance(exception, Timeout):
           return True
       
       # Retry on 5xx server errors
       if isinstance(exception, HTTPError):
           status_code = getattr(getattr(exception, 'response', None), 'status_code', 0)
           if status_code >= 500:
               return True
       
       # Don't retry other errors (like 4xx client errors)
       return False
   
   def get(
       self, 
       endpoint: str, 
       params: Optional[Dict[str, Any]] = None, 
       stream: bool = False,
       body: Optional[Dict[str, Any]] = None
   ) -> requests.Response:
       """
       Make a GET request to the API with proper error handling and retry logic.
       
       Args:
           endpoint: API endpoint path
           params: Query parameters
           stream: Whether to stream the response
           body: Optional request body
           
       Returns:
           requests.Response object
           
       Raises:
           InvalidInputData: For 404 errors with detailed message
           HTTPError: For other HTTP errors
           ConnectionError: For network connectivity issues
           TimeoutError: For request timeouts
       """
       # Ensure endpoint starts with "/"
       if not endpoint.startswith('/'):
           endpoint = f"/{endpoint}"
           
       url = f"{self.base_url}{endpoint}"
       self.logger.debug(f"GET {url} with params={params}")
       
       last_exception = None
       
       # Attempt the request with retries
       for attempt in range(1, self.max_retries + 2):  # +2 because range is exclusive
           try:
               response = requests.get(
                   url=url,
                   headers=self.headers,
                   params=params,
                   data=body,
                   stream=stream,
                   verify=self.verify_ssl,
                   timeout=self.timeout
               )
               response.raise_for_status()
               self.logger.debug(f"Request successful (status: {response.status_code})")
               return response
               
           except Exception as e:
               last_exception = e
               
               if self._should_retry(e, attempt):
                   # Calculate wait time with exponential backoff
                   wait_time = self.backoff_factor * (2 ** (attempt - 1))
                   self.logger.warning(
                       f"Request failed with {type(e).__name__}: {str(e)}. "
                       f"Retrying in {wait_time:.2f}s (attempt {attempt}/{self.max_retries})"
                   )
                   time.sleep(wait_time)
               else:
                   # No more retries, handle the error
                   break
       
       # If we reached here, all retries failed or we didn't retry
       self.logger.error(f"Request failed after {attempt} attempt(s): {last_exception}")
       
       # Handle specific error cases
       if isinstance(last_exception, HTTPError):
           response = getattr(last_exception, 'response', None)
           if response and response.status_code == 404:
               try:
                   error_data = response.json()
                   error_data.update({"status_code": 404, "error": str(last_exception)})
                   raise InvalidInputData(str(error_data))
               except (ValueError, KeyError, AttributeError):
                   # JSON parsing failed, raise the original exception
                   pass
           
           # Re-raise HTTP errors
           raise last_exception
       
       elif isinstance(last_exception, ConnectionError):
           raise ConnectionError(f"Failed to connect to {url}. Please check your network connection.")
       
       elif isinstance(last_exception, Timeout):
           raise TimeoutError(f"Request to {url} timed out after {self.timeout[1]} seconds.")
       
       # Re-raise any other exceptions
       raise last_exception or RuntimeError("Unknown error occurred during API request")


# Initialize verbose mode handler
# verbose_mode = VerboseMode()


# Endpoint configurations
ENDPOINT_TO_TICKER = {
   "/risks": "",
   "/government/traffic/domains": "",
   "/government/traffic/agencies": "",
   "/bankruptcy": "",
   "/bankruptcy/shapleys": "",
   "/bankruptcy/description": "",
   "/corprisk/accounting": "",
   "/corprisk/events": "",
   "/corprisk/misstatement": "",
   "/corprisk/risks": "",
   "/bankruptcy/risks": "",
   "/breakout": "",
   "/breakout/median": "",
   "/institutional/trading": "",
   "/institutional/flow_prediction": "",
   "/news/daily": "",
   "/news/match_quality": "",
   "/news/within_article": "",
   "/news/relevance": "",
   "/news/magnitude": "",
   "/news/sentiment": "",
   "/news/article_count": "",
   "/news/associated_people": "",
   "/news/associated_companies": "",
   "/news/tone": "",
   "/news/positive": "",
   "/news/negative": "",
   "/news/polarity": "",
   "/news/activeness": "",
   "/news/pronouns": "",
   "/news/word_count": "",
   "/news/sentiment_score": "", # was None before?

   "/insider/trading": "",

   "/wikipedia/views": "",
   "/accounting/weekly": "",
   "/visas/h1b": "",
   "/factors/accounting": "",
   "/factors/alternative": "",
   "/factors/comprehensive": "",
   "/factors/coefficients": "",
   "/factors/standard_errors": "",
   "/factors/t_statistics": "",
   "/factors/model_metrics": "",
   "/ratios/normal": "",
   "/ratios/relative": "",
   "/movies/boxoffice": "",
   "/complaints/private": "",
   "/complaints/public": "",
   "/short/over_shorted": "",
   "/short/volume": "",
   "/earnings/surprise": "",
   "/news/topic_probability": "",
   "/news/polarity_score": "",
   "/macro/features": "",
   "/congress": "",
   "/market/closeadj": "",
   "/lobbying/public": "",
   "/liquidity/price_improvement": "",
   "/liquidity/market_opportunity": "",
   "/trials/predict": "",
   "/trials/describe": "",
   "/trials/all/predict": "",
   "/trials/all/decribe": "",
   "/trials/all": "",

    "/patents/applications": "",
    "/patents/grants": "",
    
    "/clinical/trials": "",



    "/spending/awards": "",
    "/spending/compensation": "",
    "/spending/competition": "",
    "/spending/contracts": "",
    "/spending/entities": "",
    "/spending/location": "",
    "/spending/product": "",
    "/spending/transactions": "",
    "/lobbying/data": ""

}

# Define endpoint sets for different processing methods
CLIENT_SIDE_ENDPOINTS_GCS = {
#    "ratios/relative",
   "market/prices",
   "market/closeadj",
   "short/volume",
#    "complaints/public",
   "complaints/private",
   "lobbying/public",
}

CLIENT_SIDE_ENDPOINTS_S3 = {
   "sec/10k",
   "trials/predict",
   "trials/describe",
   "trials/all/predict",
   "trials/all/decribe",
   "trials/all",
}

CLIENT_SIDE_ENDPOINTS_S3_PART_HIGH = {
   "patents/applications",
   "patents/grants",

   "clinical/trials",


   "spending/awards",
   "spending/compensation",
   "spending/competition",
   "spending/contracts",
   "spending/entities", 
   "spending/location",
   "spending/product",

   "spending/transactions",

   "lobbying",

   "accounting/weekly",

   "insider/trading",

   "ratios/normal",
   "ratios/relative",

   "complaints/public",

   "factors/accounting",
   "factors/alternative",
   "factors/comprehensive",
   "factors/coefficients",
   "factors/standard_errors",
   "factors/t_statistics",
   "factors/model_metrics",

   "breakout",

    "corprisk/risks",
    "corprisk/accounting",
    "corprisk/events",
    "corprisk/misstatements",

   "visas/h1b",

   "wikipedia/views",

    "short/volume",
    "short/maker",
    "short/over_shorted",

    "institutional/trading"

}



ENDPOINT_ALIASES = {
    "clinical/predict": {
        "target_endpoint": "clinical/trials",
        "columns": [
            'ticker', 'date', 'source', 'subsidiary', 'sponsor', 
            'trial_id', 'official_title', 'success_prediction', 
            'economic_effect', 'duration_prediction', 'success_composite'
        ]
    }
    # --- Add other aliases here in the future ---
    # "some/alias": {
    #     "target_endpoint": "real/endpoint",
    #     "columns": ["col1", "col2", "date", "ticker"] # Ensure essential columns are included
    # }
}


# Define handlers for different endpoint types
ENDPOINT_HANDLERS = [
   (CLIENT_SIDE_ENDPOINTS_GCS, client_side_frame, "Grabbing GCS client side"),
   (CLIENT_SIDE_ENDPOINTS_S3, load_frame_s3, "Grabbing S3 client side"),
   (CLIENT_SIDE_ENDPOINTS_S3_PART_HIGH, load_frame_s3_partitioned_high, "Grabbing S3 Partitioned High client side"),
]

# Parameter synonym mapping
PARAM_SYNONYMS = {
   "start": "start_date",
   "from_date": "start_date",
   "end": "end_date",
   "to_date": "end_date",
   "ticker": "tickers",
   "symbol": "tickers",
   "columns_name": "columns",
   "col": "columns",
   "cols": "columns",
}


def normalize_endpoint(endpoint: str) -> str:
   """
   Normalize an endpoint by removing trailing/leading slashes.
   
   Args:
       endpoint: API endpoint path
       
   Returns:
       Normalized endpoint string
   """
   return endpoint.strip("/").strip()


def map_synonyms(params: Dict[str, Any]) -> Dict[str, Any]:
   """
   Map parameter synonyms to their canonical names.
   
   Args:
       params: Dictionary of parameters
       
   Returns:
       Dictionary with standardized parameter names
   """
   return {PARAM_SYNONYMS.get(key, key): value for key, value in params.items()}


def is_all(tickers: Optional[Union[str, List[str]]]) -> bool:
   """
   Check if tickers parameter represents 'all tickers'.
   
   Args:
       tickers: Ticker symbol(s) to check
       
   Returns:
       True if tickers indicates 'all', False otherwise
   """
   # Special values that indicate all tickers
   ALL_PATTERNS = ["ENTIRE", "ALL", "FULL", ""]

   # Return False if tickers is None
   if tickers is None:
       return False

   # Convert string to list if necessary
   if isinstance(tickers, str):
       tickers = [tickers]

   # Check if any ticker matches the pattern
   return any(ticker.upper() in ALL_PATTERNS for ticker in tickers)


def get_ticker_from_endpoint(
   endpoint: str, 
   tickers: Optional[Union[str, List[str]]], 
   endpoint_to_ticker_map: Dict[str, str]
) -> Optional[Union[str, List[str]]]:
   """
   Determine the appropriate ticker value based on endpoint and tickers.
   
   Args:
       endpoint: The API endpoint
       tickers: Current tickers value
       endpoint_to_ticker_map: Mapping of endpoints to ticker values
       
   Returns:
       Appropriate ticker value
   """
   if tickers is None or tickers is False:
       # Check if the endpoint is in the map and return its value
       return endpoint_to_ticker_map.get(endpoint, tickers)
   return tickers


def load_df_from_wasabi(
   bucket_name: str, 
   file_name: str, 
   access_key: str, 
   secret_key: str
) -> Union[pd.DataFrame, 'CustomDataFrame']:
   """
   Load a DataFrame from Wasabi S3-compatible storage.
   
   Args:
       bucket_name: S3 bucket name
       file_name: Path to file within bucket
       access_key: Wasabi access key
       secret_key: Wasabi secret key
       
   Returns:
       DataFrame containing the loaded data
       
   Raises:
       boto3.exceptions.Boto3Error: If there's an issue with S3 connection
       IOError: If there's an issue reading the file
       ValueError: If there's an issue parsing the parquet data
   """
   logger.debug(f"Loading DataFrame from Wasabi S3: {bucket_name}/{file_name}")
   
   try:
       s3_client = boto3.client(
           "s3",
           endpoint_url="https://s3.wasabisys.com",
           aws_access_key_id=access_key,
           aws_secret_access_key=secret_key,
       )
       
       parquet_buffer = BytesIO()
       s3_client.download_fileobj(bucket_name, file_name, parquet_buffer)
       parquet_buffer.seek(0)
       
       df = pq.read_table(source=parquet_buffer).to_pandas()
       
       logger.debug(f"Successfully loaded DataFrame with shape {df.shape}")
       return CustomDataFrame(df) if HAS_FULL_INSTALL else df
       
   except Exception as e:
       logger.error(f"Failed to load DataFrame from Wasabi S3: {str(e)}")
       raise


def read_parquet(url: str, use_polars: bool = False) -> DataFrameType:
   """
   Read parquet file from URL using either pandas or polars.
   
   Args:
       url: URL pointing to parquet file
       use_polars: If True, use polars instead of pandas
       
   Returns:
       DataFrame containing the data
       
   Raises:
       ValueError: If the URL is invalid
       IOError: If there's an issue downloading the file
       Exception: For any other errors during loading
   """
   logger.debug(f"Reading parquet from URL: {url}")
   
   try:
       if use_polars:
           df = pl.read_parquet(url)
           logger.debug(f"Successfully loaded Polars DataFrame with shape {df.shape}")
           return df
       else:
           df = pd.read_parquet(url)
           result = CustomDataFrame(df) if HAS_FULL_INSTALL else df
           logger.debug(f"Successfully loaded Pandas DataFrame with shape {df.shape}")
           return result
           
   except Exception as e:
       logger.error(f"Failed to read parquet from URL {url}: {str(e)}")
       raise


# def filter_data(
#    data: DataFrameType,
#    columns: Optional[Union[str, List[str]]] = None,
#    start_date: Optional[str] = None,
#    end_date: Optional[str] = None,
#    use_polars: bool = False,
#    date_column: str = 'date'
# ) -> DataFrameType:
#    """
#    Filter DataFrame based on columns and date range.
   
#    Args:
#        data: Input DataFrame
#        columns: Columns to select
#        start_date: Start date for filtering (YYYY-MM-DD)
#        end_date: End date for filtering (YYYY-MM-DD)
#        use_polars: Whether to use polars instead of pandas
#        date_column: The column name containing date values
       
#    Returns:
#        Filtered DataFrame
#    """
#    # Process columns parameter
#    if columns:
#        if isinstance(columns, str):
#            columns = [col.strip() for col in columns.split(',')]
#    else:
#        columns = data.columns.to_list() if use_polars else list(data.columns)
   
#    # Always include these columns if they exist
#    essential_columns = ['calculation', date_column, 'ticker']
#    for col in essential_columns:
#        if col in data.columns and col not in columns:
#            columns.insert(0, col)
   
#    if use_polars:
#        # Polars implementation
#        # Select columns
#        data = data.select(columns)
       
#        # Apply date filtering
#        if start_date or end_date:
#            if date_column in data.columns:
#                if start_date:
#                    data = data.filter(pl.col(date_column) >= pl.Date.parse(start_date))
#                if end_date:
#                    data = data.filter(pl.col(date_column) <= pl.Date.parse(end_date))
#            else:
#                # Handle date in index if not in columns
#                data = data.with_row_count('temp_index')
#                if start_date:
#                    data = data.filter(pl.col('temp_index').cast(pl.Date) >= pl.Date.parse(start_date))
#                if end_date:
#                    data = data.filter(pl.col('temp_index').cast(pl.Date) <= pl.Date.parse(end_date))
#                data = data.drop('temp_index')
#    else:
#        # Pandas implementation
#        # Column filtering
#        data = data[columns]
       
#        # Date filtering
#        if start_date or end_date:
#            if date_column in data.columns:
#                data[date_column] = pd.to_datetime(data[date_column])
#                if start_date:
#                    data = data[data[date_column] >= pd.to_datetime(start_date)]
#                if end_date:
#                    data = data[data[date_column] <= pd.to_datetime(end_date)]
#            elif isinstance(data.index, pd.DatetimeIndex):
#                if start_date:
#                    data = data[data.index >= pd.to_datetime(start_date)]
#                if end_date:
#                    data = data[data.index <= pd.to_datetime(end_date)]
#            elif isinstance(data.index, pd.MultiIndex) and any(isinstance(level, pd.DatetimeIndex) for level in data.index.levels):
#                date_level = next((level for level in data.index.levels if isinstance(level, pd.DatetimeIndex)), None)
#                if date_level:
#                    if start_date:
#                        data = data[data.index.get_level_values(date_level.name) >= pd.to_datetime(start_date)]
#                    if end_date:
#                        data = data[data.index.get_level_values(date_level.name) <= pd.to_datetime(end_date)]
#                else:
#                    logger.warning("Unable to filter by date. No DatetimeIndex level found in MultiIndex.")
#            else:
#                logger.warning(f"Unable to filter by date. {date_column} column or DatetimeIndex not found.")
   
#    return data


# Define the default columns to always remove if they exist
DEFAULT_COLUMNS_TO_REMOVE = ['ticker_partitioned', 'date_partitioned', 'year_partitioned', 'month_partitioned', 'day_partitioned']


def filter_data(
   data: DataFrameType,
   columns: Optional[Union[str, List[str]]] = None,
   start_date: Optional[str] = None,
   end_date: Optional[str] = None,
   use_polars: bool = False,
   date_column: str = 'date'
) -> DataFrameType:
   """
   Filter DataFrame based on columns and date range, and remove default unwanted columns.
   
   Args:
       data: Input DataFrame
       columns: Columns to select. If None, all columns are initially considered.
       start_date: Start date for filtering (YYYY-MM-DD)
       end_date: End date for filtering (YYYY-MM-DD)
       use_polars: Whether to use polars instead of pandas
       date_column: The column name containing date values
       
   Returns:
       Filtered DataFrame
   """
   if data is None or (hasattr(data, 'empty') and data.empty):
       verbose_mode.log("filter_data received None or empty DataFrame, returning as is.")
       return data

   # Determine the initial list of columns to work with
   current_columns_list: List[str]
   all_data_columns = data.columns.to_list() if use_polars else list(data.columns)

   if columns:
       if isinstance(columns, str):
           current_columns_list = [col.strip() for col in columns.split(',') if col.strip()]
       elif isinstance(columns, list):
           current_columns_list = [str(col).strip() for col in columns if str(col).strip()]
       else:
           current_columns_list = all_data_columns[:] # Fallback to all columns if 'columns' is an unexpected type
       
       # Ensure requested columns actually exist in the data, to prevent errors later
       current_columns_list = [col for col in current_columns_list if col in all_data_columns]
       if not current_columns_list and columns: # User asked for columns, but none were valid
            logger.warning(f"None of the requested columns {columns} were found in the DataFrame. Returning DataFrame with all original columns before default removal and date filtering.")
            current_columns_list = all_data_columns[:]

   else:
       current_columns_list = all_data_columns[:] # No columns specified, start with all
   
   verbose_mode.log(f"Initial columns after user specification (or all): {current_columns_list}")

   # Always include these essential columns if they exist in the original data
   essential_columns = ['calculation', date_column, 'ticker']
   for col in essential_columns:
       if col in all_data_columns and col not in current_columns_list:
           current_columns_list.insert(0, col) # Add to the beginning
   
   verbose_mode.log(f"Columns after ensuring essentials: {current_columns_list}")

   # --- New Step: Remove default unwanted columns ---
   columns_to_keep_after_default_removal = []
   removed_by_default = []
   for col in current_columns_list:
       if col not in DEFAULT_COLUMNS_TO_REMOVE:
           columns_to_keep_after_default_removal.append(col)
       else:
           if col in all_data_columns: # Make sure it actually exists to log its removal
               removed_by_default.append(col)
   
   if removed_by_default:
       verbose_mode.log(f"Default columns removed: {removed_by_default}")
   
   current_columns_list = columns_to_keep_after_default_removal
   verbose_mode.log(f"Columns after default removal: {current_columns_list}")

   # Ensure there are still columns to select, otherwise, what to do?
   # If current_columns_list is empty, selecting would cause an error.
   # This might happen if all columns were default-to-remove or user asked for non-existing cols.
   if not current_columns_list:
       if all_data_columns: # If there were columns initially
           logger.warning("After processing, no columns remain to be selected. This might be due to all columns being part of the default removal list or invalid user-specified columns. The original DataFrame structure (pre-column-filtering) will be used for date filtering if applicable.")
           # In this case, we proceed with date filtering on the original 'data' columns,
           # as no valid column selection was made.
           # Or, we could return an empty DF if the intention is that no columns means no data.
           # For now, let's use all_data_columns for selection before date filtering if current_columns_list becomes empty.
           # This means default removal effectively didn't happen if it emptied the list.
           # A better approach if list is empty: select nothing, which leads to an empty df (for pandas data[[]]).
           # For safety, if list is empty, it implies we want an empty dataframe in terms of columns.
           pass # The selection below will handle an empty list appropriately (empty df for pandas)


   # Select/filter columns
   if use_polars:
       # Polars implementation
       if not current_columns_list and all_data_columns: # If list is empty but data had columns
           data = data.select([]) # Select no columns, results in empty df with 0 columns
       elif current_columns_list:
           data = data.select(current_columns_list)
       # If current_columns_list is empty AND all_data_columns was empty, data is already 0-column df
       
       # Apply date filtering
       if date_column in data.columns and (start_date or end_date):
           date_series = data[date_column]
           # Ensure the date column is of a type that can be parsed or compared
           # Polars is usually good with this if data is already in Date/Datetime type
           try:
               if start_date:
                   data = data.filter(pl.col(date_column) >= datetime.strptime(start_date, '%Y-%m-%d'))
               if end_date:
                   data = data.filter(pl.col(date_column) <= datetime.strptime(end_date, '%Y-%m-%d'))
           except Exception as e: # Catch errors if date column is not parsable to date/datetime
               logger.warning(f"Polars: Could not apply date filter on column '{date_column}' due to parsing or type error: {e}. Column type: {date_series.dtype}")

       # No direct equivalent for index-based date filtering in Polars without explicit conversion
   else:
       # Pandas implementation
       if not current_columns_list and all_data_columns: # If list is empty but data had columns
           data = data[[]] # Select no columns, results in empty df with 0 columns
       elif current_columns_list:
           # Only select if current_columns_list is not empty to avoid error with data[[]] if it was intended to keep all
           data = data[current_columns_list]
       # If current_columns_list is empty AND all_data_columns was empty, data is already 0-column df

       # Date filtering
       if date_column in data.columns and (start_date or end_date):
           try:
               # Ensure data[date_column] is actually datetime
               if not pd.api.types.is_datetime64_any_dtype(data[date_column]):
                   data[date_column] = pd.to_datetime(data[date_column], errors='coerce')
               
               # Filter out NaT values that may result from coerce if original dates were bad
               data = data[data[date_column].notna()]

               if start_date:
                   data = data[data[date_column] >= pd.to_datetime(start_date)]
               if end_date:
                   data = data[data[date_column] <= pd.to_datetime(end_date)]
           except Exception as e:
               logger.warning(f"Pandas: Could not apply date filter on column '{date_column}' due to parsing or type error: {e}")

       elif isinstance(data.index, pd.DatetimeIndex) and (start_date or end_date):
           # This part is tricky if columns were just changed.
           # If data is now a subset of columns, its index remains.
           if start_date:
               data = data[data.index >= pd.to_datetime(start_date)]
           if end_date:
               data = data[data.index <= pd.to_datetime(end_date)]
       # Note: MultiIndex date filtering omitted for brevity as it adds complexity after column subsetting.
       # Consider if it's still needed or how it interacts with column changes.

   verbose_mode.log(f"Shape of data after all filtering: {data.shape if hasattr(data, 'shape') else 'N/A'}")
   return data


def find_tickers(
   sample_identifiers: List[str], 
   df_codes: pd.DataFrame, 
   verbose: bool = False
) -> List[str]:
   """
   Find canonical ticker symbols from various identifier types.
   
   Args:
       sample_identifiers: List of identifiers (tickers, CUSIPs, CIKs, etc.)
       df_codes: DataFrame containing identifier mappings
       verbose: Whether to print detailed mapping information
       
   Returns:
       List of mapped ticker symbols
   """
   # Regex patterns for different identifier types
   cusip_pattern = re.compile(r'^[A-Za-z0-9]{9}$')
   cik_pattern = re.compile(r'^\d{10}$')
   openfigi_pattern = re.compile(r'^BBG[A-Za-z0-9]{9}$')

   # Classify identifiers by type
   classified = defaultdict(set)
   
   for identifier in sample_identifiers:
       if identifier and identifier != 'None':
           identifier = str(identifier).strip()
           if openfigi_pattern.match(identifier):
               classified['openfigis'].add(identifier)
           elif cik_pattern.match(identifier):
               classified['ciks'].add(identifier)
           elif cusip_pattern.match(identifier):
               classified['cusips'].add(identifier)
           else:
               classified['tickers'].add(identifier)

   # Column groups for different identifier types
   ticker_columns = ['ticker', 'ticker_1', 'ticker_2', 'ticker_3', 'ticker_4']
   cusip_columns = ['cusip', 'cusip_1']

   # Create boolean masks for each identifier type
   masks = pd.DataFrame(index=df_codes.index)

   # Direct ticker matches
   masks['ticker_match'] = df_codes['ticker'].isin(classified['tickers'])

   # Alternative ticker matches
   alt_ticker_df = df_codes[ticker_columns[1:]]
   masks['alt_ticker_match'] = alt_ticker_df.isin(classified['tickers']).any(axis=1)

   # CUSIP matches
   cusip_df = df_codes[cusip_columns]
   masks['cusip_match'] = cusip_df.isin(classified['cusips']).any(axis=1)

   # CIK matches
   masks['cik_match'] = df_codes['cik'].isin(classified['ciks'])

   # OpenFIGI matches
   masks['openfigi_match'] = df_codes['top_level_openfigi_id'].isin(classified['openfigis'])

   # Combine matches where the 'ticker' is valid
   masks['valid_ticker'] = masks['ticker_match'] | masks['cusip_match'] | masks['cik_match'] | masks['openfigi_match']
   masks['any_match'] = masks['valid_ticker'] | (masks['alt_ticker_match'] & masks['valid_ticker'])

   # Extract matching rows
   matching_rows = df_codes[masks['any_match']].copy()
   matching_masks = masks.loc[matching_rows.index]

   # Generate verbose output if requested
   if verbose:
       mappings = []

       # For direct matches
       direct_matches = matching_rows[matching_masks['ticker_match']]
       for ticker in direct_matches['ticker']:
           mappings.append(f"{ticker} -> {ticker} (Direct match)")

       # For alternative ticker matches where 'ticker' is valid
       alt_matches = matching_rows[~matching_masks['ticker_match'] & matching_masks['alt_ticker_match'] & matching_masks['valid_ticker']]
       for idx, row in alt_matches.iterrows():
           alt_tickers = row[ticker_columns[1:]].dropna()
           matching_alt_tickers = alt_tickers[alt_tickers.isin(classified['tickers'])]
           if not matching_alt_tickers.empty:
               alt_ticker = matching_alt_tickers.iloc[0]
               main_ticker = row['ticker']
               mappings.append(f"{alt_ticker} -> {main_ticker} (Alternative ticker match)")

       # For CUSIP matches
       cusip_matches = matching_rows[~matching_masks['ticker_match'] & ~matching_masks['alt_ticker_match'] & matching_masks['cusip_match']]
       for idx, row in cusip_matches.iterrows():
           cusips = row[cusip_columns].dropna()
           matching_cusips = cusips[cusips.isin(classified['cusips'])]
           if not matching_cusips.empty:
               cusip = matching_cusips.iloc[0]
               mappings.append(f"{cusip} -> {row['ticker']} (CUSIP match)")

       # For CIK matches
       cik_matches = matching_rows[
           ~matching_masks['ticker_match'] & 
           ~matching_masks['alt_ticker_match'] & 
           ~matching_masks['cusip_match'] & 
           matching_masks['cik_match']
       ]
       for idx, row in cik_matches.iterrows():
           mappings.append(f"{row['cik']} -> {row['ticker']} (CIK match)")

       # For OpenFIGI matches
       openfigi_matches = matching_rows[
           ~matching_masks['ticker_match'] & 
           ~matching_masks['alt_ticker_match'] & 
           ~matching_masks['cusip_match'] & 
           ~matching_masks['cik_match'] & 
           matching_masks['openfigi_match']
       ]
       for idx, row in openfigi_matches.iterrows():
           mappings.append(f"{row['top_level_openfigi_id']} -> {row['ticker']} (OpenFIGI match)")

       # Print all mappings
       if mappings:
           logger.info("Identifier mapping results:")
           print("\n".join(mappings))
       else:
           logger.warning("No identifier mappings found")

   # Return unique tickers
   result = matching_rows['ticker'].unique().tolist()
   logger.debug(f"Mapped {len(sample_identifiers)} identifiers to {len(result)} unique tickers")
   return result

@lru_cache(maxsize=1)
def _get_ticker_codes_df():
    logger.debug("Loading ticker mapping codes...")
    try:
        return pd.read_parquet("data/codes.parq")
    except Exception as e:
        logger.error(f"Failed to load ticker mapping data: {e}")
        raise ValueError(f"Cannot perform ticker mapping: {e}")


def ticker_mapper(params: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
   """
   Map various identifiers to canonical ticker symbols.
   
   Args:
       params: Parameters dictionary containing tickers
       verbose: Whether to print detailed mapping information
       
   Returns:
       Updated parameters with mapped tickers
   """
   # Extract the tickers parameter
   tickers = params.get('tickers')
   
   if verbose:
       logger.info(f"Original tickers: {tickers}")

   # Load ticker mapping data
   try:
       df_codes = _get_ticker_codes_df()
   except Exception as e:
       logger.error(f"Failed to load ticker mapping data: {e}")
       raise ValueError(f"Cannot perform ticker mapping: {e}")

   # Parse tickers into a list
   if isinstance(tickers, str):
       tickers_list = [ticker.strip() for ticker in tickers.split(',')]
   elif isinstance(tickers, list):
       tickers_list = tickers
   else:
       raise ValueError(f"Unexpected type for tickers: {type(tickers)}")

   if verbose:
       logger.info(f"Tickers list: {tickers_list}")

   # Map tickers
   mapped_tickers = find_tickers(tickers_list, df_codes, verbose=verbose)

   if verbose:
       logger.info(f"Mapped tickers: {mapped_tickers}")

   # Update params with mapped tickers
   params['tickers'] = ','.join(mapped_tickers)

   if verbose:
       logger.info(f"Final tickers string: {params['tickers']}")

   return params


def _prepare_params(**kwargs) -> Dict[str, str]:
   """
   Prepare parameters for API request.
   
   Args:
       **kwargs: Parameters to prepare
       
   Returns:
       Dictionary of prepared parameters
   """
   finish_params = {}

   # Convert list parameters to comma-separated strings
   if isinstance(kwargs.get("tickers", None), list):
       kwargs["tickers"] = ",".join(kwargs["tickers"])

   if isinstance(kwargs.get("columns", None), list):
       kwargs["columns"] = ",".join(kwargs["columns"])

   # Convert all parameters to strings
   for server_param, client_param in kwargs.items():
       if client_param is not None:
           finish_params[server_param] = str(client_param)

   return finish_params


def _prepare_endpoint(endpoint: str, params: dict) -> Tuple[str, dict]:
   """
   Prepare endpoint and parameters for API request.
   
   Args:
       endpoint: API endpoint path
       params: Parameters dictionary
       
   Returns:
       Tuple of (processed endpoint, remaining parameters)
   """
   # Ensure endpoint starts with "/"
   if not endpoint.startswith("/"):
       endpoint = "/" + endpoint
   
   # Extract parameters from endpoint
   endpoint_params_key = re.findall(r"\{(.*?)\}", endpoint)
   endpoint_params = {
       key: value for key, value in params.items() if key in endpoint_params_key
   }
   
   # Separate other parameters
   other_params = {
       key: value for key, value in params.items() if key not in endpoint_params_key
   }
   
   # Process datetime parameters
   _uniform_datetime_params(other_params)
   
   # Format endpoint with parameters
   if endpoint_params:
       endpoint = endpoint.format(**endpoint_params)
   
   return endpoint.lower(), other_params

def _uniform_datetime_params(datetime_params: Dict[str, str]) -> None:
    """
    Standardize datetime parameter formats.
    
    Args:
        datetime_params: Dictionary of parameters that may contain dates
    """
    for key, val in datetime_params.items():
        if "date" in key.lower() and val is not None:
            for _format in datetime_format:
                try:
                    origin_datetime = datetime.strptime(val, _format)
                    datetime_params[key] = origin_datetime.strftime(datetime_format[0])
                    break
                except ValueError:
                    continue


def _draw_graphs(data: Union[Dict, List[Dict]]) -> Optional[go.Figure]:
    """
    Generate plots from data.
    
    Args:
        data: Data to plot
        
    Returns:
        Plotly figure object if successful, None otherwise
    """
    try:
        if isinstance(data, list):
            for plot in data:
                for _, val in plot.items():
                    return plotting_data(val)
        else:
            for _, val in data.items():
                return plotting_data(val)
    except Exception as e:
        logger.error(f"Error generating graph: {e}")
        return None


def set_dark_mode(fig: go.Figure) -> go.Figure:
    """
    Apply dark mode styling to a Plotly figure.
    
    Args:
        fig: Plotly figure to style
        
    Returns:
        Styled figure
    """
    return fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(10, 10, 10, 1)",
        paper_bgcolor="rgba(10, 10, 10, 1)",
    )


def optimize_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame by downcasting numeric columns.
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Memory-optimized DataFrame
    """
    # Make a copy to avoid modifying the original
    df_optimized = df.copy()
    
    # Downcast numeric columns to most efficient types
    for col in df_optimized.select_dtypes(include=['int']).columns:
        df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
        
    for col in df_optimized.select_dtypes(include=['float']).columns:
        df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
    
    # Convert object columns to categories if they have few unique values
    for col in df_optimized.select_dtypes(include=['object']).columns:
        unique_count = df_optimized[col].nunique()
        if unique_count < len(df_optimized) * 0.5:  # If fewer than 50% unique values
            df_optimized[col] = df_optimized[col].astype('category')
    
    return df_optimized


@functools.lru_cache(maxsize=128)
def get_api_handler() -> ApiRequestHandler:
    """
    Get or create an ApiRequestHandler singleton with cached configuration.
    
    Returns:
        Configured ApiRequestHandler instance
    """
    return ApiRequestHandler(
        base_url=ApiConfig.base_url,
        token=ApiConfig.token,
        verify_ssl=ApiConfig.verify_ssl,
        logger=logger
    )

def data(
    endpoint: str,
    tickers: Optional[Union[str, List[str]]] = None,
    chart: Optional[str] = None,
    columns: Optional[str] = None,
    version: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    plot: bool = False,
    limit: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    use_polars: bool = False,
    purge_cache: bool = False,
    parquet: bool = True,
    frequency: Optional[str] = None,
    verbose: bool = False,
    full_history: bool = False,
    source: Optional[str] = None,
) -> Union[DataFrameType, go.Figure, None]:
    """
    Main function to retrieve data from the API.
    
    This function serves as the primary entry point for retrieving financial data
    across various endpoints with support for different parameters.
    
    Args:
        endpoint: API endpoint path
        tickers: Stock symbols or identifiers
        chart: Chart type if generating visualizations
        columns: Columns to select
        version: API version
        start_date: Start date for filtering (YYYY-MM-DD)
        end_date: End date for filtering (YYYY-MM-DD)
        plot: Whether to generate a plot
        limit: Maximum number of rows to return
        params: Additional parameters dictionary
        body: Request body dictionary
        use_polars: Whether to use polars instead of pandas
        purge_cache: Whether to ignore cached results
        parquet: Whether to use parquet format
        frequency: Data frequency (daily, weekly, etc.)
        verbose: Whether to print detailed information
        full_history: Whether to retrieve full history regardless of dates
        
    Returns:
        DataFrame, Figure, or None depending on request
        
    Raises:
        InvalidInputData: For validation errors
        ConnectionError: For network connectivity issues
        TimeoutError: For request timeouts
        ValueError: For issues with parameter preparation
        Exception: For other errors during data retrieval
    """
    # Set verbose mode based on parameter
    verbose_mode.toggle_verbose(verbose)
    verbose_mode.log(f"Starting data request for endpoint: {endpoint}")
    
    result_data = None  # Initialize the return value

    # Initialize and process parameters
    params = params or {}
    params = map_synonyms(params)

    # --- MODIFIED SECTION: Alias Handling ---
    original_endpoint_request = endpoint # Keep track for logging
    forced_columns = None # Will store columns if an alias forces them
    normalized_req_endpoint = normalize_endpoint(endpoint) 

    if normalized_req_endpoint in ENDPOINT_ALIASES:
        alias_config = ENDPOINT_ALIASES[normalized_req_endpoint]
        target_endpoint = alias_config['target_endpoint']
        forced_columns_list = alias_config['columns']
        verbose_mode.log(f"Endpoint alias detected: '{original_endpoint_request}' maps to '{target_endpoint}' with predefined columns.")
        
        endpoint = target_endpoint # *Overwrite* endpoint for the rest of the function
        columns = forced_columns_list # *Overwrite* columns parameter
        
        # Ensure the 'columns' value in the main 'params' dict is also updated
        # This is crucial for cache key generation and potentially for client-side handlers
        # Convert list to string if needed for _prepare_params consistency
        params['columns'] = ",".join(forced_columns_list) 

    else:
        # If not an alias, handle the columns parameter normally
        # Convert list to string if provided as list initially
        if isinstance(columns, list):
             columns_str = ",".join(columns)
        else:
             columns_str = columns # It's already a string or None
        # Update params dict if columns were passed directly to the function
        if columns is not None:
            params['columns'] = columns_str
    # --- END MODIFIED SECTION ---


    # Force full_history if date range is specified
    if start_date is not None or end_date is not None:
        full_history = True
        verbose_mode.log("Enabling full_history due to date range specification")

    # Update params with prepared values
    try:

        # Make sure to use the potentially updated 'columns' value from params dict
        # if it exists, otherwise use the function argument (which might be None or overridden)
        current_columns = params.get("columns", columns) 
        # Convert back to string if it was forced as a list earlier
        if isinstance(current_columns, list):
            current_columns = ",".join(current_columns)

        params.update(
            _prepare_params(
                tickers=params.get("tickers", tickers),
                chart=params.get("chart", chart),
                version=params.get("version", version),
                from_date=params.get("start_date", start_date),
                to_date=params.get("end_date", end_date),
                limit=params.get("limit", limit),
                columns=params.get("columns", columns),
                parquet=params.get("parquet", parquet),
                frequency=params.get("frequency", frequency),
                full_history=params.get("full_history", full_history),
                source=params.get("source", source),  # Add source parameter here
            )
        )
    except Exception as e:
        verbose_mode.log(f"Parameter preparation error: {e}")
        raise ValueError(f"Failed to prepare request parameters: {e}")
    
    # Prepare endpoint and parameters
    endpoint, params = _prepare_endpoint(endpoint, params)
    verbose_mode.log(f"Prepared endpoint: {endpoint}")
    
    # Configure request
    params = params or None
    url = ApiConfig.base_url + endpoint
    verbose_mode.log(f"Full URL: {url} with params: {params}")

    # Create a unique cache key
    cache_key = hashlib.sha256(
        json.dumps([url, params], sort_keys=True).encode()
    ).hexdigest()
    verbose_mode.log(f"Cache key: {cache_key}")

    # Handle cache operations
    if purge_cache and cache_key in _query_cache:
        del _query_cache[cache_key]
        verbose_mode.log("Purged cache entry")

    if not purge_cache and cache_key in _query_cache:
        verbose_mode.log("Using cached data")
        result_data = _query_cache[cache_key]
    else:
        # Process normalized endpoint for handler matching
        normalized_endpoint = normalize_endpoint(endpoint)

        # Try client-side handlers for specific endpoints
        handler_result = None

        # Get the columns value to pass to handlers (use the string version from params)
        handler_columns_arg = params.get('columns') 

        for endpoint_set, handler_func, message in ENDPOINT_HANDLERS:
            if (
                normalized_endpoint in endpoint_set and
                (tickers is not None or start_date is not None or end_date is not None) and
                frequency is None
            ):
                verbose_mode.log(message)
                verbose_mode.log(f"Calling client-side handler with tickers={tickers}, start_date={start_date}, end_date={end_date}")
                try:
                    handler_result = handler_func(
                        normalized_endpoint, tickers, handler_columns_arg, start_date, end_date
                    )
                    _query_cache[cache_key] = handler_result
                    result_data = handler_result
                    # print(handler_result)
                    break
                except Exception as e:
                    verbose_mode.log(f"Client-side handler error for {normalized_endpoint}: {e}")
                    # Fall through to API request if client-side handler fails

        # Only proceed with API request if no handler result
        if result_data is None:
            try:
                # Perform ticker mapping if needed
                if tickers is not None and not is_all(tickers):
                    verbose_mode.log("Mapping ticker symbols")
                    params = ticker_mapper(params, verbose)

                # Create API request handler
                api_handler = get_api_handler()
                
                # Make API request with retry logic
                verbose_mode.log("Sending API request")
                res = api_handler.get(
                    endpoint=endpoint,
                    params=params,
                    body=body,
                    stream=True
                )
                
                verbose_mode.log(f"Response received - Status: {res.status_code}, Content-Type: {res.headers.get('content-type')}")
                
                # Get appropriate ticker for endpoint
                tickers = get_ticker_from_endpoint(endpoint, tickers, ENDPOINT_TO_TICKER)
                verbose_mode.log(f"Using tickers: {tickers}")

                # Get response metadata
                data_format = res.headers.get("X-Data-Format")
                content_type = res.headers["content-type"]
                plot_header = res.headers.get("X-Plotly-Data")
                
                # Handle binary data (parquet)
                if (content_type == "application/octet-stream") and not plot_header:
                    if data_format == "pyarrow":
                        verbose_mode.log("Processing pyarrow data stream")
                        data_result = stream_data_pyarrow(res)
                    else:
                        verbose_mode.log("Processing binary data stream")
                        data_result = stream_data(res)
                    
                    # Wrap in CustomDataFrame if available
                    if HAS_FULL_INSTALL:
                        data_result = CustomDataFrame(data_result)
                    else:
                        data_result = pd.DataFrame(data_result)
                    
                    _query_cache[cache_key] = data_result
                    result_data = data_result

                    
                
                # Handle 'all tickers' case
                elif is_all(tickers):
                    verbose_mode.log("Processing 'all tickers' response")
                    urls = [u.strip() for u in res.text.strip('"').split(',') if u.strip()]
                    data_result = None
                    
                    # Try each URL until successful
                    for i, url in enumerate(urls):
                        verbose_mode.log(f"Attempting URL {i+1}/{len(urls)}: {url}")
                        try:
                            data_result = read_parquet(url, use_polars=use_polars)
                            verbose_mode.log(f"Successfully downloaded data from URL {i+1}")
                            break
                        except Exception as e:
                            verbose_mode.log(f"Failed to download from URL {i+1}: {str(e)}")
                    
                    if data_result is None:
                        error_msg = "Failed to download data from all provided URLs"
                        verbose_mode.log(error_msg)
                        raise Exception(error_msg)
                    
                    filter_columns_arg = columns
                    if isinstance(columns, str): # filter_data might prefer list
                        filter_columns_arg = [c.strip() for c in columns.split(',')] if columns else None

                    # Apply filters
                    verbose_mode.log("Applying filters to data")
                    data_result = filter_data(
                        data_result, 
                        columns=filter_columns_arg, 
                        start_date=start_date, 
                        end_date=end_date, 
                        use_polars=use_polars
                    )

                    # Wrap in CustomDataFrame if available
                    if HAS_FULL_INSTALL and not use_polars:
                        data_result = CustomDataFrame(data_result)

                    _query_cache[cache_key] = data_result
                    result_data = data_result


                    # result_data = process_dataframe(result_data)


                    # Before returning, apply source filtering if applicable
                    if (result_data is not None and 
                        source is not None and 
                        hasattr(result_data, 'filter') and 
                        'source' not in result_data.columns):
                        
                        if source == "delisted":
                            verbose_mode.log("Filtering for delisted securities")
                            result_data = result_data.filter(["isdelisted=Y"])
                        elif source == "listed":
                            verbose_mode.log("Filtering for listed securities")
                            result_data = result_data.filter(["isdelisted=N"])
                    
                # Handle JSON data
                elif not plot_header:
                    verbose_mode.log("Processing JSON response")
                    json_data = res.json()
                    if HAS_FULL_INSTALL:
                        data_result = CustomDataFrame(convert_data2df(json_data))
                    else:
                        data_result = pd.DataFrame(convert_data2df(json_data))

                    _query_cache[cache_key] = data_result
                    result_data = data_result


                # Handle plot data
                if plot_header:
                    verbose_mode.log("Processing plot data")
                    if HAS_FULL_INSTALL:
                        import pickle
                        try:
                            # Unpickle the data
                            pickle_bytes = res.content
                            fig = pickle.loads(pickle_bytes)
                            fig = go.Figure(json.loads(fig))
                            fig = set_dark_mode(fig)
                            result_data = fig
                        except Exception as e:
                            verbose_mode.log(f"Failed to process plot data: {e}")
                            result_data = None
                    else:
                        verbose_mode.log("Plotting is only available with the full installation. Please install 'sovai[full]' to use this feature.")
                        result_data = None
                
                # Generate plot if requested
                if plot and result_data is not None and not plot_header:
                    verbose_mode.log("Generating plot from data")
                    if HAS_FULL_INSTALL:
                        result_data = _draw_graphs(result_data)
                    else:
                        verbose_mode.log("Plotting is only available with the full installation. Please install 'sovai[full]' to use this feature.")
                        result_data = None
                    
            except InvalidInputData as err:
                verbose_mode.log(f"Invalid input data: {err}")
                raise
                
            except (ConnectionError, TimeoutError) as err:
                verbose_mode.log(f"Network error: {err}")
                raise ConnectionError(f"Could not connect to API: {err}")
                
            except Exception as err:
                verbose_mode.log(f"API request error: {err}")
                raise


    result_data = process_dataframe(result_data)


    # --- Final Check: Ensure alias columns are applied if data wasn't filtered before ---
    # This is a safety net in case a data path (e.g., direct API return without 'all tickers')
    # didn't explicitly filter columns based on the overridden parameter.
    if forced_columns is not None and result_data is not None and isinstance(result_data, (pd.DataFrame, pl.DataFrame)):
         # Check if columns need filtering (some might be missing if already filtered)
         current_cols = list(result_data.columns)
         cols_to_keep = [col for col in forced_columns_list if col in current_cols]
         if set(cols_to_keep) != set(current_cols):
             verbose_mode.log(f"Applying final column filter for alias: {cols_to_keep}")
             if isinstance(result_data, pd.DataFrame):
                 result_data = result_data[cols_to_keep]
             elif isinstance(result_data, pl.DataFrame):
                 result_data = result_data.select(cols_to_keep)
                 

    return result_data


async def fetch_multiple_tickers(
    endpoint: str,
    tickers: List[str],
    **kwargs
) -> Dict[str, DataFrameType]:
    """
    Fetch data for multiple tickers concurrently using asyncio.
    
    Args:
        endpoint: API endpoint
        tickers: List of ticker symbols
        **kwargs: Additional parameters for the data function
        
    Returns:
        Dictionary mapping tickers to their respective DataFrames
        
    Example:
        ```python
        # Fetch data for multiple tickers concurrently
        import asyncio
        
        results = asyncio.run(fetch_multiple_tickers(
            endpoint="/market/closeadj",
            tickers=["AAPL", "MSFT", "GOOGL"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        ))
        
        # Access individual ticker data
        aapl_data = results.get("AAPL")
        ```
    """
    import asyncio
    import concurrent.futures
    
    results = {}
    
    # Create a thread pool for running synchronous functions concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        futures = []
        
        # Create a future for each ticker
        for ticker in tickers:
            future = loop.run_in_executor(
                executor,
                lambda t=ticker: data(endpoint=endpoint, tickers=t, **kwargs)
            )
            futures.append((ticker, future))
        
        # Gather results as they complete
        for ticker, future in futures:
            try:
                result = await future
                results[ticker] = result
            except Exception as e:
                verbose_mode.log(f"Error fetching data for ticker {ticker}: {e}")
                results[ticker] = None
            
    return results


# ------------------------------------------------------------------------
# Code Explanation
# ------------------------------------------------------------------------
"""
This module provides a comprehensive API client for retrieving financial data from the SovAI API.
It implements multiple data retrieval strategies, efficient caching, and flexible data processing
capabilities.

Core Architecture Overview:
--------------------------
This library is designed around several key components:

1. UNIFIED API INTERFACE:
   The main 'data()' function serves as the primary entry point, providing a consistent
   interface for fetching financial data across various endpoints with support for
   different parameters (tickers, date ranges, formats).

2. DATA SOURCE ABSTRACTION:
   The code abstracts away the complexities of different data sources (GCS, S3, API)
   through specialized endpoint handlers, allowing for transparent access regardless
   of where the data is stored.

3. IDENTIFIER RESOLUTION:
   Financial identifiers (tickers, CUSIPs, CIKs, OpenFIGI IDs) are automatically
   resolved to canonical ticker symbols through the ticker mapping system.

4. PERFORMANCE OPTIMIZATION:
   - Results caching with hash-based keys
   - Stream processing for large datasets
   - Support for both pandas and polars DataFrames
   - Efficient filtering and processing

5. ROBUST ERROR HANDLING:
   Comprehensive exception handling with appropriate logging ensures the code
   gracefully handles API errors, network issues, and data processing failures.

Technical Implementation Details:
-------------------------------
- Type Safety: Comprehensive type hints prevent errors and improve IDE support
- Modular Design: Functions are organized by responsibility for maintainability
- Logging System: Configurable verbose mode for debugging and tracing
- Parameter Processing: Standardization of API parameters with synonym support
- Data Filtering: Post-retrieval filtering capabilities for columns and date ranges
- Visualization: Integration with Plotly for data visualization

Usage Example:
------------
```python
from sovai import data

# Set your API token
from sovai.api_config import ApiConfig
ApiConfig.token = "your_token_here"

# Retrieve closing prices for Apple and Microsoft
result = data(
    endpoint="/market/closeadj",
    tickers="AAPL,MSFT",
    start_date="2023-01-01",
    end_date="2023-12-31",
    verbose=True
)

# Display the first few rows
print(result.head())"
"```"
"""
