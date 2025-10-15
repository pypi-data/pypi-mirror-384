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
import os # Added import
import pickle # Added import

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
from sovai.utils.verbose_utils import verbose_mode # Assuming VerboseMode is properly defined here

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
   CustomDataFrame = pd.DataFrame # Fallback if not available
   plotting_data = lambda x: None # Fallback
   logger.warning("Running with limited installation. Some features unavailable.")


def is_full_installation() -> bool:
   return HAS_FULL_INSTALL


# Define cache directory
CACHE_DIR = "cache"

# Helper function to save data to disk cache
def _save_to_disk_cache(key: str, data_to_cache: Any, cache_dir: str, verbose_logger: Any):
    """
    Saves data to the disk cache.
    DataFrames (pandas, polars, CustomDataFrame) are saved as Parquet.
    Plotly Figures are saved as Pickle.
    """
    os.makedirs(cache_dir, exist_ok=True)
    parquet_path = os.path.join(cache_dir, f"{key}.parquet")
    pickle_path = os.path.join(cache_dir, f"{key}.pkl")

    if isinstance(data_to_cache, (pd.DataFrame, pl.DataFrame)): # Covers CustomDataFrame as it inherits from pd.DataFrame
        try:
            if isinstance(data_to_cache, pl.DataFrame):
                data_to_cache.write_parquet(parquet_path)
            else: # pd.DataFrame or CustomDataFrame
                data_to_cache.to_parquet(parquet_path)
            verbose_logger.log(f"Saved to Parquet cache: {parquet_path}")
        except Exception as e:
            verbose_logger.log(f"Error saving to Parquet cache {parquet_path}: {e}. Cache file might not be created or be corrupted.")
            if os.path.exists(parquet_path):
                try:
                    os.remove(parquet_path)
                except Exception as rem_e:
                    verbose_logger.log(f"Could not remove potentially corrupted cache file {parquet_path}: {rem_e}")
    elif HAS_FULL_INSTALL and isinstance(data_to_cache, go.Figure):
        try:
            with open(pickle_path, 'wb') as f:
                pickle.dump(data_to_cache, f)
            verbose_logger.log(f"Saved Plotly figure to Pickle cache: {pickle_path}")
        except Exception as e:
            verbose_logger.log(f"Error saving to Pickle cache {pickle_path}: {e}. Cache file might not be created or be corrupted.")
            if os.path.exists(pickle_path):
                try:
                    os.remove(pickle_path)
                except Exception as rem_e:
                    verbose_logger.log(f"Could not remove potentially corrupted cache file {pickle_path}: {rem_e}")
    else:
        verbose_logger.log(f"Data type {type(data_to_cache)} not supported for disk caching. Skipping cache save.")


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
# verbose_mode = VerboseMode() # This should be initialized where VerboseMode is defined


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
   if tickers is None or tickers is False: # False seems unusual here, but keeping original logic
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
       
       # Read into pandas DataFrame first
       df_pandas = pq.read_table(source=parquet_buffer).to_pandas()
       
       logger.debug(f"Successfully loaded DataFrame with shape {df_pandas.shape}")
       return CustomDataFrame(df_pandas) if HAS_FULL_INSTALL else df_pandas
       
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
           # Read as pandas DataFrame first
           df_pandas = pd.read_parquet(url)
           result = CustomDataFrame(df_pandas) if HAS_FULL_INSTALL else df_pandas
           logger.debug(f"Successfully loaded Pandas DataFrame with shape {df_pandas.shape}")
           return result
           
   except Exception as e:
       logger.error(f"Failed to read parquet from URL {url}: {str(e)}")
       raise


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

   current_columns_list: List[str]
   all_data_columns = list(data.columns) # Works for both pandas and polars

   if columns:
       if isinstance(columns, str):
           current_columns_list = [col.strip() for col in columns.split(',') if col.strip()]
       elif isinstance(columns, list):
           current_columns_list = [str(col).strip() for col in columns if str(col).strip()]
       else:
           current_columns_list = all_data_columns[:] 
       
       current_columns_list = [col for col in current_columns_list if col in all_data_columns]
       if not current_columns_list and columns:
            logger.warning(f"None of the requested columns {columns} were found in the DataFrame. Proceeding with all original columns before default removal and date filtering.")
            current_columns_list = all_data_columns[:]
   else:
       current_columns_list = all_data_columns[:] 
   
   verbose_mode.log(f"Initial columns after user specification (or all): {current_columns_list}")

   essential_columns = ['calculation', date_column, 'ticker']
   for col in essential_columns:
       if col in all_data_columns and col not in current_columns_list:
           current_columns_list.insert(0, col)
   
   verbose_mode.log(f"Columns after ensuring essentials: {current_columns_list}")

   columns_to_keep_after_default_removal = []
   removed_by_default = []
   for col in current_columns_list:
       if col not in DEFAULT_COLUMNS_TO_REMOVE:
           columns_to_keep_after_default_removal.append(col)
       else:
           if col in all_data_columns:
               removed_by_default.append(col)
   
   if removed_by_default:
       verbose_mode.log(f"Default columns removed: {removed_by_default}")
   
   current_columns_list = columns_to_keep_after_default_removal
   verbose_mode.log(f"Columns after default removal: {current_columns_list}")

   # Select/filter columns
   filtered_data = data # Start with the original data, then apply selections/filters

   if use_polars:
       if not current_columns_list and all_data_columns:
           filtered_data = filtered_data.select([]) 
       elif current_columns_list:
           # Ensure all selected columns exist to prevent Polars error
           valid_cols_for_polars = [col for col in current_columns_list if col in filtered_data.columns]
           if not valid_cols_for_polars and current_columns_list : # Requested columns but none are valid
                logger.warning(f"Polars: None of the columns {current_columns_list} exist after processing. Resulting DataFrame will have no columns if selection is applied strictly.")
                # Depending on desired behavior, either select([]) or keep original columns for date filtering
                filtered_data = filtered_data.select([]) # Strict: select no columns
           elif valid_cols_for_polars:
                 filtered_data = filtered_data.select(valid_cols_for_polars)

       if date_column in filtered_data.columns and (start_date or end_date):
           try:
               date_dt_type = pl.Datetime if filtered_data[date_column].dtype == pl.Datetime else pl.Date
               if start_date:
                   filtered_data = filtered_data.filter(pl.col(date_column) >= datetime.strptime(start_date, '%Y-%m-%d').cast(date_dt_type))
               if end_date:
                   filtered_data = filtered_data.filter(pl.col(date_column) <= datetime.strptime(end_date, '%Y-%m-%d').cast(date_dt_type))
           except Exception as e:
               logger.warning(f"Polars: Could not apply date filter on column '{date_column}': {e}. Column type: {filtered_data[date_column].dtype}")
   else: # Pandas
       if not current_columns_list and all_data_columns:
           filtered_data = filtered_data[[]]
       elif current_columns_list:
           # Ensure all selected columns exist to prevent Pandas KeyError
           valid_cols_for_pandas = [col for col in current_columns_list if col in filtered_data.columns]
           if not valid_cols_for_pandas and current_columns_list:
                logger.warning(f"Pandas: None of the columns {current_columns_list} exist after processing. Resulting DataFrame will have no columns.")
                filtered_data = filtered_data[[]] # Strict: select no columns
           elif valid_cols_for_pandas:
                 filtered_data = filtered_data[valid_cols_for_pandas]


       if date_column in filtered_data.columns and (start_date or end_date):
           try:
               if not pd.api.types.is_datetime64_any_dtype(filtered_data[date_column]):
                   filtered_data = filtered_data.copy() # Avoid SettingWithCopyWarning
                   filtered_data.loc[:, date_column] = pd.to_datetime(filtered_data[date_column], errors='coerce')
               
               filtered_data = filtered_data[filtered_data[date_column].notna()]

               if start_date:
                   filtered_data = filtered_data[filtered_data[date_column] >= pd.to_datetime(start_date)]
               if end_date:
                   filtered_data = filtered_data[filtered_data[date_column] <= pd.to_datetime(end_date)]
           except Exception as e:
               logger.warning(f"Pandas: Could not apply date filter on column '{date_column}': {e}")
       elif isinstance(filtered_data.index, pd.DatetimeIndex) and (start_date or end_date):
           if start_date:
               filtered_data = filtered_data[filtered_data.index >= pd.to_datetime(start_date)]
           if end_date:
               filtered_data = filtered_data[filtered_data.index <= pd.to_datetime(end_date)]

   verbose_mode.log(f"Shape of data after all filtering: {filtered_data.shape if hasattr(filtered_data, 'shape') else 'N/A'}")
   return filtered_data


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
       if identifier and identifier != 'None': # Ensure 'None' string is skipped
           identifier_str = str(identifier).strip()
           if not identifier_str: # Skip empty strings after strip
               continue
           if openfigi_pattern.match(identifier_str):
               classified['openfigis'].add(identifier_str)
           elif cik_pattern.match(identifier_str):
               classified['ciks'].add(identifier_str)
           elif cusip_pattern.match(identifier_str):
               classified['cusips'].add(identifier_str)
           else:
               classified['tickers'].add(identifier_str)


   # Column groups for different identifier types
   ticker_columns = ['ticker', 'ticker_1', 'ticker_2', 'ticker_3', 'ticker_4']
   cusip_columns = ['cusip', 'cusip_1']

   # Create boolean masks for each identifier type
   masks = pd.DataFrame(index=df_codes.index) # Ensure masks align with df_codes

   # Ensure df_codes columns are string type for comparison, handle NaNs
   df_codes_str = df_codes.astype(str)


   # Direct ticker matches
   masks['ticker_match'] = df_codes_str['ticker'].isin(classified['tickers']) if 'tickers' in classified else False

   # Alternative ticker matches
   alt_ticker_match_any = pd.Series(False, index=df_codes.index)
   if 'tickers' in classified and classified['tickers']: # Check if there are tickers to match
        for col in ticker_columns[1:]:
            if col in df_codes_str.columns:
                alt_ticker_match_any |= df_codes_str[col].isin(classified['tickers'])
   masks['alt_ticker_match'] = alt_ticker_match_any


   # CUSIP matches
   cusip_match_any = pd.Series(False, index=df_codes.index)
   if 'cusips' in classified and classified['cusips']:
        for col in cusip_columns:
            if col in df_codes_str.columns:
                cusip_match_any |= df_codes_str[col].isin(classified['cusips'])
   masks['cusip_match'] = cusip_match_any


   # CIK matches
   masks['cik_match'] = df_codes_str['cik'].isin(classified['ciks']) if 'ciks' in classified and 'cik' in df_codes_str.columns else False

   # OpenFIGI matches
   masks['openfigi_match'] = df_codes_str['top_level_openfigi_id'].isin(classified['openfigis']) \
        if 'openfigis' in classified and 'top_level_openfigi_id' in df_codes_str.columns else False


   # Combine matches where the 'ticker' is valid
   masks['valid_ticker'] = masks['ticker_match'] | masks['cusip_match'] | masks['cik_match'] | masks['openfigi_match']
   masks['any_match'] = masks['valid_ticker'] | (masks['alt_ticker_match'] & masks['valid_ticker']) # Original logic for any_match

   # Extract matching rows
   matching_rows = df_codes[masks['any_match']].copy() # Use original df_codes for data, masks for filtering
   matching_masks_subset = masks.loc[matching_rows.index] # Subset of masks for matching_rows


   # Generate verbose output if requested
   if verbose:
       mappings = []

       # For direct matches
       direct_matches_rows = matching_rows[matching_masks_subset['ticker_match']]
       for ticker_val in direct_matches_rows['ticker']:
           mappings.append(f"{ticker_val} -> {ticker_val} (Direct match)")

       # For alternative ticker matches where 'ticker' is valid
       alt_matches_rows = matching_rows[
           ~matching_masks_subset['ticker_match'] & 
           matching_masks_subset['alt_ticker_match'] & 
           matching_masks_subset['valid_ticker']
       ]
       for idx, row in alt_matches_rows.iterrows():
           alt_tickers_series = row[ticker_columns[1:]].dropna() # Operate on original row data
           # Ensure alt_tickers_series contains strings for .isin()
           matching_alt_tickers = alt_tickers_series.astype(str)[alt_tickers_series.astype(str).isin(classified.get('tickers', set()))]

           if not matching_alt_tickers.empty:
               alt_ticker = matching_alt_tickers.iloc[0]
               main_ticker = row['ticker']
               mappings.append(f"{alt_ticker} -> {main_ticker} (Alternative ticker match)")
       
       # CUSIP, CIK, OpenFIGI matches similar verbose logic, ensuring to use matching_masks_subset and classified sets
       # For CUSIP matches
       cusip_matches_rows = matching_rows[
           ~matching_masks_subset['ticker_match'] & 
           ~matching_masks_subset['alt_ticker_match'] & 
           matching_masks_subset['cusip_match']
       ]
       for idx, row in cusip_matches_rows.iterrows():
           cusips_series = row[cusip_columns].dropna()
           matching_cusips = cusips_series.astype(str)[cusips_series.astype(str).isin(classified.get('cusips', set()))]
           if not matching_cusips.empty:
               cusip = matching_cusips.iloc[0]
               mappings.append(f"{cusip} -> {row['ticker']} (CUSIP match)")

       # For CIK matches
       cik_matches_rows = matching_rows[
           ~matching_masks_subset['ticker_match'] & 
           ~matching_masks_subset['alt_ticker_match'] & 
           ~matching_masks_subset['cusip_match'] & 
           matching_masks_subset['cik_match']
       ]
       for idx, row in cik_matches_rows.iterrows(): # cik is a single column
           if str(row['cik']) in classified.get('ciks', set()): # Check if this row's CIK was in the input
                mappings.append(f"{row['cik']} -> {row['ticker']} (CIK match)")


       # For OpenFIGI matches
       openfigi_matches_rows = matching_rows[
           ~matching_masks_subset['ticker_match'] & 
           ~matching_masks_subset['alt_ticker_match'] & 
           ~matching_masks_subset['cusip_match'] & 
           ~matching_masks_subset['cik_match'] & 
           matching_masks_subset['openfigi_match']
       ]
       for idx, row in openfigi_matches_rows.iterrows():
           if str(row['top_level_openfigi_id']) in classified.get('openfigis', set()):
                mappings.append(f"{row['top_level_openfigi_id']} -> {row['ticker']} (OpenFIGI match)")


       if mappings:
           logger.info("Identifier mapping results:")
           print("\n".join(mappings)) # Consider using logger.info for all lines if print is not desired
       else:
           logger.info("No identifier mappings found for the provided inputs.") # Changed from warning to info


   result = matching_rows['ticker'].unique().tolist()
   logger.debug(f"Mapped {len(sample_identifiers)} identifiers to {len(result)} unique tickers")
   return result

@lru_cache(maxsize=1)
def _get_ticker_codes_df():
    logger.debug("Loading ticker mapping codes...")
    try:
        # Assuming codes.parq is in a subdirectory accessible via relative path
        # If data/ is relative to the script execution, this is fine.
        # Otherwise, a more robust path mechanism might be needed.
        return pd.read_parquet("data/codes.parq")
    except Exception as e:
        logger.error(f"Failed to load ticker mapping data (data/codes.parq): {e}")
        # Consider if this should raise a more specific error or if ValueError is appropriate
        raise ValueError(f"Cannot perform ticker mapping due to data loading failure: {e}")


def ticker_mapper(params: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
   """
   Map various identifiers to canonical ticker symbols.
   
   Args:
       params: Parameters dictionary containing tickers
       verbose: Whether to print detailed mapping information
       
   Returns:
       Updated parameters with mapped tickers
   """
   tickers_param = params.get('tickers') # Use a different variable name
   
   if verbose:
       logger.info(f"Original tickers parameter: {tickers_param}")

   df_codes = _get_ticker_codes_df() # Relies on lru_cache for efficiency

   tickers_list = []
   if isinstance(tickers_param, str):
       tickers_list = [ticker.strip() for ticker in tickers_param.split(',') if ticker.strip()]
   elif isinstance(tickers_param, list):
       tickers_list = [str(t).strip() for t in tickers_param if str(t).strip()] # Ensure all elements are strings and stripped
   elif tickers_param is None:
       logger.info("No tickers provided for mapping.")
       # params['tickers'] will remain None or not be set if it wasn't there.
       return params 
   else:
       # This case should ideally not happen if _prepare_params standardizes types,
       # but good to have a safeguard.
       logger.warning(f"Unexpected type for tickers: {type(tickers_param)}. Attempting to proceed, but mapping may be incorrect.")
       try: # Attempt conversion if possible, otherwise, treat as empty or raise.
           tickers_list = [str(tickers_param).strip()] if str(tickers_param).strip() else []
       except:
           raise ValueError(f"Unhandled type for tickers for mapping: {type(tickers_param)}")


   if not tickers_list:
       logger.info("Ticker list is empty after parsing. No mapping to perform.")
       params['tickers'] = "" # Standardize to empty string for no tickers, or keep as original (None)?
       return params

   if verbose:
       logger.info(f"Tickers list for mapping: {tickers_list}")

   mapped_tickers = find_tickers(tickers_list, df_codes, verbose=verbose)

   if verbose:
       logger.info(f"Mapped tickers: {mapped_tickers}")

   params['tickers'] = ','.join(mapped_tickers) # Update params with comma-separated string of mapped tickers

   if verbose:
       logger.info(f"Final tickers string in params: {params['tickers']}")

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
   # This ensures consistency before they are put into `finish_params`
   if "tickers" in kwargs and isinstance(kwargs["tickers"], list):
       kwargs["tickers"] = ",".join(map(str, kwargs["tickers"])) # Ensure all elements are strings

   if "columns" in kwargs and isinstance(kwargs["columns"], list):
       kwargs["columns"] = ",".join(map(str, kwargs["columns"])) # Ensure all elements are strings

   # Convert all parameters to strings, skip None values
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
   
   # Extract parameters from endpoint placeholders like {param_name}
   # These are path parameters.
   endpoint_params_keys = re.findall(r"\{(.*?)\}", endpoint)
   
   # Parameters that will be part of the URL path
   path_params_values = {}
   # Parameters that will be query parameters
   query_params_values = {}

   for key, value in params.items():
       if key in endpoint_params_keys:
           path_params_values[key] = value
       else:
           query_params_values[key] = value
   
   # Process datetime parameters within query_params
   _uniform_datetime_params(query_params_values) # Modifies query_params_values in place
   
   # Format endpoint with path parameters
   if path_params_values:
       try:
           processed_endpoint = endpoint.format(**path_params_values)
       except KeyError as e:
           # This means a placeholder in the endpoint string doesn't have a corresponding value in path_params_values
           # which implies it wasn't in the original params or was mistyped.
           logger.error(f"Missing parameter for endpoint formatting: {e}. Endpoint: {endpoint}, Path Params: {path_params_values}")
           raise ValueError(f"Endpoint placeholder {e} not found in provided parameters.") from e
   else:
       processed_endpoint = endpoint
   
   return processed_endpoint.lower(), query_params_values


def _uniform_datetime_params(datetime_params: Dict[str, str]) -> None:
    """
    Standardize datetime parameter formats. Modifies the input dict in place.
    
    Args:
        datetime_params: Dictionary of parameters that may contain dates
    """
    for key, val in datetime_params.items():
        if val is not None and isinstance(val, str) and "date" in key.lower(): # Ensure val is string
            original_val = val # For logging if parsing fails
            parsed = False
            for fmt in datetime_format: # datetime_format should be a list of format strings
                try:
                    dt_obj = datetime.strptime(val, fmt)
                    datetime_params[key] = dt_obj.strftime(datetime_format[0]) # Standardize to first format
                    parsed = True
                    break 
                except ValueError:
                    continue # Try next format
            if not parsed:
                logger.debug(f"Date parameter '{key}' with value '{original_val}' did not match any known formats: {datetime_format}. Leaving as is.")


def _draw_graphs(data: Union[Dict, List[Dict]]) -> Optional[go.Figure]:
    """
    Generate plots from data.
    
    Args:
        data: Data to plot, expected to be dict or list of dicts where values are plottable.
        
    Returns:
        Plotly figure object if successful, None otherwise
    """
    if not HAS_FULL_INSTALL:
        logger.warning("Plotting unavailable: Full installation required for plotting features.")
        return None
    try:
        # This function expects `plotting_data` to handle the actual plotting logic
        # based on the structure of `val`.
        if isinstance(data, list):
            if not data: # Empty list
                logger.debug("Empty list provided to _draw_graphs, no plot generated.")
                return None
            # Original logic iterates and returns for the first item's value.
            # This might not be intended if multiple plots are possible from a list.
            # Assuming it plots the first plottable item found.
            for item in data:
                if isinstance(item, dict):
                    for _, val in item.items():
                        # plotting_data should return a go.Figure or None
                        fig = plotting_data(val)
                        if fig: return fig 
            logger.debug("No plottable data found in the list for _draw_graphs.")
            return None

        elif isinstance(data, dict):
            if not data: # Empty dict
                logger.debug("Empty dict provided to _draw_graphs, no plot generated.")
                return None
            for _, val in data.items():
                fig = plotting_data(val)
                if fig: return fig
            logger.debug("No plottable data found in the dict for _draw_graphs.")
            return None
        else:
            logger.warning(f"Unsupported data type for _draw_graphs: {type(data)}. Expected dict or list.")
            return None

    except Exception as e:
        logger.error(f"Error generating graph with _draw_graphs: {e}")
        return None


def set_dark_mode(fig: go.Figure) -> go.Figure:
    """
    Apply dark mode styling to a Plotly figure.
    
    Args:
        fig: Plotly figure to style
        
    Returns:
        Styled figure
    """
    if not isinstance(fig, go.Figure): # Check if it's actually a figure
        logger.warning("set_dark_mode received non-Figure object. Returning as is.")
        return fig
    return fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(10, 10, 10, 1)", # Slightly less opaque than pure black for better visibility
        paper_bgcolor="rgba(10, 10, 10, 1)",
        font=dict(color="white") # Ensure text is visible
    )


def optimize_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a pandas DataFrame by downcasting numeric columns.
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Memory-optimized DataFrame
    """
    if not isinstance(df, pd.DataFrame):
        logger.warning("optimize_memory_usage expects a pandas DataFrame. Returning input as is.")
        return df

    df_optimized = df.copy() # Work on a copy
    
    # Downcast numeric columns
    for col in df_optimized.select_dtypes(include=['integer', 'int64', 'int32', 'int16', 'int8']).columns:
        try:
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
        except Exception as e:
            logger.debug(f"Could not downcast integer column {col}: {e}")

    for col in df_optimized.select_dtypes(include=['float', 'float64', 'float32']).columns:
        try:
            df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
        except Exception as e:
            logger.debug(f"Could not downcast float column {col}: {e}")
    
    # Convert object columns to categories if cardinality is low
    for col in df_optimized.select_dtypes(include=['object']).columns:
        try:
            num_unique_values = df_optimized[col].nunique()
            num_total_values = len(df_optimized[col])
            if num_unique_values / num_total_values < 0.5: # If unique values are less than 50%
                df_optimized[col] = df_optimized[col].astype('category')
        except Exception as e: # Handle potential errors with nunique() or astype() on complex objects
            logger.debug(f"Could not convert object column {col} to category: {e}")
    
    return df_optimized


@functools.lru_cache(maxsize=128) # This caches the ApiRequestHandler instance itself
def get_api_handler() -> ApiRequestHandler:
    """
    Get or create an ApiRequestHandler singleton with cached configuration.
    
    Returns:
        Configured ApiRequestHandler instance
    """
    logger.debug("Initializing ApiRequestHandler (or retrieving from lru_cache).")
    return ApiRequestHandler(
        base_url=ApiConfig.base_url,
        token=ApiConfig.token,
        verify_ssl=ApiConfig.verify_ssl,
        logger=logger # Pass the module logger
    )

# Main data retrieval function
def data(
    endpoint: str,
    tickers: Optional[Union[str, List[str]]] = None,
    chart: Optional[str] = None,
    columns: Optional[Union[str,List[str]]] = None, # Allow list for columns
    version: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    plot: bool = False,
    limit: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    use_polars: bool = False,
    purge_cache: bool = False,
    parquet: bool = True, # `parquet` param seems to imply format preference
    frequency: Optional[str] = None,
    verbose: bool = False,
    full_history: bool = False,
    source: Optional[str] = None,
) -> Union[DataFrameType, go.Figure, None]:
    """
    Main function to retrieve data from the API.
    Caches results to disk in 'cache/' directory (Parquet for DataFrames, Pickle for Figures).
    """
    verbose_mode.toggle_verbose(verbose)
    verbose_mode.log(f"Starting data request for endpoint: {endpoint}, use_polars: {use_polars}")
    
    result_data: Union[DataFrameType, go.Figure, None] = None 

    # Initialize and process parameters
    # If params is None, create new dict. Otherwise, use a copy to avoid modifying caller's dict.
    current_params = (params or {}).copy()
    current_params = map_synonyms(current_params)

    original_endpoint_request = endpoint 
    forced_columns_list: Optional[List[str]] = None # For alias column enforcement

    normalized_req_endpoint = normalize_endpoint(endpoint) 

    if normalized_req_endpoint in ENDPOINT_ALIASES:
        alias_config = ENDPOINT_ALIASES[normalized_req_endpoint]
        target_endpoint = alias_config['target_endpoint']
        forced_columns_list = alias_config['columns'] # This is a list
        verbose_mode.log(f"Endpoint alias detected: '{original_endpoint_request}' maps to '{target_endpoint}' with predefined columns: {forced_columns_list}")
        
        endpoint = target_endpoint # Overwrite endpoint for the rest of the function
        columns = forced_columns_list # Overwrite `columns` function argument (which might be passed to _prepare_params)
                                      # This also means forced_columns_list takes precedence.
    
    # If `columns` function arg was provided, it might override alias or be the primary source
    # The `_prepare_params` will take `columns` from its arguments.
    # Update `current_params` with function arguments that are not None,
    # allowing explicit function args to override anything in the `params` dict.
    
    # Consolidate function arguments into current_params, ensuring direct args take precedence
    # over values in the initial `params` dict.
    # The `columns` variable holds the alias-defined columns if an alias matched,
    # or the original function argument `columns` if no alias.
    
    local_args_for_prepare = {
        "tickers": tickers, "chart": chart, "version": version,
        "start_date": start_date, "end_date": end_date, # These will be mapped to from_date/to_date by _prepare_params logic if PARAM_SYNONYMS is setup for it. Or handle here.
        "from_date": start_date, "to_date": end_date, # Explicitly pass for _prepare_params
        "limit": limit, "columns": columns, # `columns` is now correctly set (original, or from alias)
        "parquet": parquet, "frequency": frequency,
        "full_history": full_history, "source": source
    }

    # Update current_params: values from local_args_for_prepare (function arguments)
    # override anything that was in the initial `params` dictionary.
    for key, val in local_args_for_prepare.items():
        if val is not None: # Only override if function arg was actually provided
            current_params[key] = val
    
    # If columns is a list, _prepare_params will convert it to string.
    # Ensure `current_params['columns']` reflects the correct state of `columns` variable.
    if columns is not None: # `columns` could be from alias (list) or func arg (str/list)
        current_params['columns'] = columns


    if current_params.get("start_date") is not None or current_params.get("end_date") is not None:
        current_params["full_history"] = True # Force full_history if date range specified
        verbose_mode.log("Enabling full_history due to date range specification.")

    try:
        # _prepare_params expects kwargs, so unpack current_params
        prepared_api_params = _prepare_params(**current_params)
    except Exception as e:
        verbose_mode.log(f"Parameter preparation error: {e}")
        raise ValueError(f"Failed to prepare request parameters: {e}") from e
    
    # Prepare endpoint and separate path/query parameters
    # `endpoint` is the potentially alias-redirected one. `prepared_api_params` contains all.
    final_endpoint_path, query_params_for_api = _prepare_endpoint(endpoint, prepared_api_params)
    verbose_mode.log(f"Final endpoint path for API: {final_endpoint_path}, Query Params: {query_params_for_api}")

    # Create cache key based on the final request elements
    # Use ApiConfig.base_url, final_endpoint_path, and query_params_for_api
    cache_key_input = [ApiConfig.base_url + final_endpoint_path, query_params_for_api]
    try:
        cache_key = hashlib.sha256(json.dumps(cache_key_input, sort_keys=True).encode()).hexdigest()
    except TypeError as e: # Handle non-serializable items if any slipped into query_params
        verbose_mode.log(f"Error generating cache key due to non-serializable params: {e}. Params: {query_params_for_api}")
        # Fallback or raise, for now, let's make a simple key that might lead to more misses
        cache_key = hashlib.sha256(str(cache_key_input).encode()).hexdigest() 
        verbose_mode.log(f"Using fallback cache key: {cache_key}")

    verbose_mode.log(f"Cache key: {cache_key}")

    cache_file_path_parquet = os.path.join(CACHE_DIR, f"{cache_key}.parquet")
    cache_file_path_pickle = os.path.join(CACHE_DIR, f"{cache_key}.pkl")

    if purge_cache:
        for pth in [cache_file_path_parquet, cache_file_path_pickle]:
            if os.path.exists(pth):
                try:
                    os.remove(pth)
                    verbose_mode.log(f"Purged cache file: {pth}")
                except Exception as e:
                    verbose_mode.log(f"Error purging cache file {pth}: {e}")
    
    if not purge_cache:
        if os.path.exists(cache_file_path_parquet):
            verbose_mode.log(f"Cache hit. Loading from Parquet cache: {cache_file_path_parquet}")
            try:
                if use_polars:
                    result_data = pl.read_parquet(cache_file_path_parquet)
                else:
                    df_pd = pd.read_parquet(cache_file_path_parquet)
                    result_data = CustomDataFrame(df_pd) if HAS_FULL_INSTALL else df_pd
                verbose_mode.log(f"Successfully loaded from Parquet. Shape: {result_data.shape if hasattr(result_data, 'shape') else 'N/A'}")
            except Exception as e:
                verbose_mode.log(f"Error loading from Parquet cache {cache_file_path_parquet}: {e}. Attempting to refetch.")
                result_data = None
                if os.path.exists(cache_file_path_parquet): os.remove(cache_file_path_parquet) # Remove bad cache
        
        elif os.path.exists(cache_file_path_pickle):
            verbose_mode.log(f"Cache hit. Loading from Pickle cache: {cache_file_path_pickle}")
            try:
                with open(cache_file_path_pickle, 'rb') as f:
                    loaded_obj = pickle.load(f)
                if HAS_FULL_INSTALL and isinstance(loaded_obj, go.Figure):
                    result_data = loaded_obj
                    verbose_mode.log("Successfully loaded Plotly figure from Pickle cache.")
                elif not HAS_FULL_INSTALL and isinstance(loaded_obj, go.Figure):
                     result_data = loaded_obj # Still load it, user might handle it or it might fail later
                     verbose_mode.log("Loaded Plotly figure, but full install not detected. Plotting features may be limited.")
                else: # Not a figure or unexpected
                    verbose_mode.log(f"Loaded unexpected object type {type(loaded_obj)} from Pickle cache. Discarding.")
                    result_data = None
                    if os.path.exists(cache_file_path_pickle): os.remove(cache_file_path_pickle)
            except Exception as e:
                verbose_mode.log(f"Error loading from Pickle cache {cache_file_path_pickle}: {e}. Attempting to refetch.")
                result_data = None
                if os.path.exists(cache_file_path_pickle): os.remove(cache_file_path_pickle) # Remove bad cache
    
    if result_data is None: # Cache miss or error, fetch new data
        verbose_mode.log("Cache miss or error in loading. Proceeding to fetch data.")
        
        # `final_endpoint_path` is normalized (e.g. /foo/bar, not foo/bar)
        # `normalize_endpoint` is for map lookups (foo/bar)
        normalized_api_endpoint = normalize_endpoint(final_endpoint_path) 
        
        # Client-side handlers
        # Note: tickers, start_date, end_date passed to handlers are the original function arguments
        # This matches the original code's apparent intention.
        # `columns` arg for handler uses the potentially alias-modified `columns` variable.
        # `handler_columns_arg` should reflect the string form if `columns` is a list.
        handler_columns_str_arg = None
        if isinstance(columns, list):
            handler_columns_str_arg = ",".join(columns)
        elif isinstance(columns, str):
            handler_columns_str_arg = columns


        for endpoint_set, handler_func, message in ENDPOINT_HANDLERS:
            if (normalized_api_endpoint in endpoint_set and
                (tickers is not None or start_date is not None or end_date is not None) and
                frequency is None): # Original conditions for client-side handlers
                verbose_mode.log(message)
                verbose_mode.log(f"Calling client-side handler: {handler_func.__name__} with tickers={tickers}, start_date={start_date}, end_date={end_date}, columns_arg='{handler_columns_str_arg}'")
                try:
                    handler_output = handler_func(
                        normalized_api_endpoint, tickers, handler_columns_str_arg, start_date, end_date
                    )
                    if handler_output is not None:
                        _save_to_disk_cache(cache_key, handler_output, CACHE_DIR, verbose_mode)
                        result_data = handler_output
                    break 
                except Exception as e:
                    verbose_mode.log(f"Client-side handler {handler_func.__name__} error for {normalized_api_endpoint}: {e}")
        
        if result_data is None: # No client-side handler success, proceed to API
            try:
                # Ticker mapping uses `query_params_for_api` which contains 'tickers' string if provided
                if query_params_for_api.get('tickers') and not is_all(query_params_for_api.get('tickers')):
                    verbose_mode.log("Mapping ticker symbols via API path.")
                    # ticker_mapper expects a dict and modifies 'tickers' key in it.
                    # It returns the modified dict.
                    query_params_for_api = ticker_mapper(query_params_for_api, verbose)

                api_handler = get_api_handler()
                verbose_mode.log(f"Sending API GET request to: {final_endpoint_path} with params: {query_params_for_api}")
                res = api_handler.get(
                    endpoint=final_endpoint_path, # Already includes base_url via handler
                    params=query_params_for_api,
                    body=body, # Original `body` function argument
                    stream=True
                )
                verbose_mode.log(f"API Response - Status: {res.status_code}, Content-Type: {res.headers.get('content-type')}")
                
                # `tickers` (original func arg) is used for `get_ticker_from_endpoint` logic.
                # This determines behavior for "all tickers" type responses.
                effective_tickers_for_logic = get_ticker_from_endpoint(final_endpoint_path, tickers, ENDPOINT_TO_TICKER)
                verbose_mode.log(f"Effective tickers for API response logic: {effective_tickers_for_logic}")

                data_format = res.headers.get("X-Data-Format")
                content_type = res.headers.get("content-type", "") # Ensure content_type is a string
                plot_header = res.headers.get("X-Plotly-Data")
                
                api_fetched_data: Any = None # Holds data from this API path before assigning to result_data

                if (content_type.startswith("application/octet-stream")) and not plot_header:
                    if data_format == "pyarrow":
                        verbose_mode.log("Processing pyarrow data stream")
                        raw_data = stream_data_pyarrow(res) # Might be Arrow Table
                    else:
                        verbose_mode.log("Processing binary data stream")
                        raw_data = stream_data(res) # Might be pandas DataFrame

                    # Ensure correct DataFrame type based on use_polars and installation
                    if use_polars:
                        if isinstance(raw_data, pd.DataFrame): api_fetched_data = pl.from_pandas(raw_data)
                        elif hasattr(raw_data, "to_polars"): api_fetched_data = raw_data.to_polars() # Arrow Table
                        else: api_fetched_data = pl.DataFrame(raw_data) # General fallback
                    else: # Pandas output
                        if hasattr(raw_data, "to_pandas"): df_pd = raw_data.to_pandas() # Arrow Table
                        elif not isinstance(raw_data, pd.DataFrame): df_pd = pd.DataFrame(raw_data)
                        else: df_pd = raw_data
                        api_fetched_data = CustomDataFrame(df_pd) if HAS_FULL_INSTALL else df_pd
                
                elif is_all(effective_tickers_for_logic):
                    verbose_mode.log("Processing 'all tickers' response (expecting URLs to Parquet files)")
                    # Ensure res.text is valid before splitting
                    urls_str = res.text.strip('"') if res.text else ""
                    urls_list = [u.strip() for u in urls_str.split(',') if u.strip()]
                    
                    temp_df = None
                    for i, item_url in enumerate(urls_list):
                        verbose_mode.log(f"Attempting URL {i+1}/{len(urls_list)}: {item_url}")
                        try:
                            temp_df = read_parquet(item_url, use_polars=use_polars) # read_parquet handles CustomDataFrame for pandas
                            verbose_mode.log(f"Successfully downloaded data from URL {i+1}. Shape: {temp_df.shape}")
                            break
                        except Exception as e:
                            verbose_mode.log(f"Failed to download from URL {i+1} ({item_url}): {str(e)}")
                    
                    if temp_df is None and urls_list: # Check if urls_list was non-empty
                        raise Exception("Failed to download data from all provided URLs for 'all tickers'.")
                    elif not urls_list:
                        verbose_mode.log("No URLs provided in 'all tickers' response. Result will be empty/None.")
                        # temp_df is already None, so api_fetched_data will be None.
                    
                    api_fetched_data = temp_df # Could be None if no URLs or all failed

                    if api_fetched_data is not None:
                        # `columns` is the var holding original or alias-forced columns list/str
                        filter_cols_arg = columns 
                        if isinstance(columns, str): # filter_data expects list or str that it splits
                            filter_cols_arg = [c.strip() for c in columns.split(',')] if columns else None
                        
                        verbose_mode.log(f"Applying filters to 'all tickers' data. Columns: {filter_cols_arg}, Start: {start_date}, End: {end_date}")
                        api_fetched_data = filter_data(
                            api_fetched_data, columns=filter_cols_arg, 
                            start_date=start_date, end_date=end_date, use_polars=use_polars
                        )
                        # filter_data already handles CustomDataFrame wrapping if use_polars=False and HAS_FULL_INSTALL.

                        # Source filtering for 'all tickers' data
                        if source is not None and api_fetched_data is not None and not api_fetched_data.empty:
                            if 'isdelisted' in api_fetched_data.columns:
                                verbose_mode.log(f"Applying source filtering: {source}")
                                if isinstance(api_fetched_data, (pd.DataFrame, CustomDataFrame)): # Pandas path
                                    if source == "delisted": api_fetched_data = api_fetched_data[api_fetched_data['isdelisted'] == 'Y']
                                    elif source == "listed": api_fetched_data = api_fetched_data[api_fetched_data['isdelisted'] == 'N']
                                elif isinstance(api_fetched_data, pl.DataFrame): # Polars path
                                    if source == "delisted": api_fetched_data = api_fetched_data.filter(pl.col('isdelisted') == 'Y')
                                    elif source == "listed": api_fetched_data = api_fetched_data.filter(pl.col('isdelisted') == 'N')
                            else:
                                verbose_mode.log(f"Source filtering for '{source}' skipped: 'isdelisted' column not found.")
                
                elif content_type.startswith("application/json") and not plot_header:
                    verbose_mode.log("Processing JSON response")
                    json_data = res.json()
                    df_from_json = convert_data2df(json_data) # Typically returns pd.DataFrame
                    if use_polars:
                        api_fetched_data = pl.from_pandas(df_from_json)
                    elif HAS_FULL_INSTALL:
                        api_fetched_data = CustomDataFrame(df_from_json)
                    else:
                        api_fetched_data = df_from_json

                if plot_header: # API itself indicates the response is a plot
                    verbose_mode.log("Processing plot data from API (X-Plotly-Data header)")
                    if HAS_FULL_INSTALL:
                        try:
                            pickle_bytes = res.content
                            # Original code: fig = pickle.loads(); fig = go.Figure(json.loads(fig))
                            # This implies the pickled object is a JSON string representing the figure.
                            fig_json_representation = pickle.loads(pickle_bytes)
                            fig_obj = go.Figure(json.loads(fig_json_representation))
                            api_fetched_data = set_dark_mode(fig_obj)
                        except Exception as e:
                            verbose_mode.log(f"Failed to process plot data from API header: {e}")
                            api_fetched_data = None 
                    else:
                        verbose_mode.log("Plotting from API header unavailable: Full installation required.")
                        api_fetched_data = None
                
                # If `plot=True` was passed as argument, and we have data that is NOT already a figure
                if plot and api_fetched_data is not None and not isinstance(api_fetched_data, go.Figure):
                    verbose_mode.log("Generating plot from fetched data (plot=True argument)")
                    if HAS_FULL_INSTALL:
                        # _draw_graphs expects dict or list of dicts.
                        # If api_fetched_data is a DataFrame, this call might not be suitable.
                        # Assuming _draw_graphs is for specific JSON-like structures that can be plotted.
                        if isinstance(api_fetched_data, (dict, list)):
                             plotted_fig = _draw_graphs(api_fetched_data)
                             if plotted_fig: api_fetched_data = plotted_fig # Replace data with figure
                        else:
                             verbose_mode.log("Plot generation (plot=True) from DataFrame data is not directly supported by _draw_graphs. Returning DataFrame.")
                    else:
                        verbose_mode.log("Plotting (plot=True) unavailable: Full installation required.")
                
                if api_fetched_data is not None:
                    _save_to_disk_cache(cache_key, api_fetched_data, CACHE_DIR, verbose_mode)
                    result_data = api_fetched_data
                # If api_fetched_data is None (e.g. all URLs failed for 'all_tickers'), result_data remains None here.

            except InvalidInputData as err: verbose_mode.log(f"Invalid input data: {err}"); raise
            except (ConnectionError, TimeoutError) as err: verbose_mode.log(f"Network error: {err}"); raise ConnectionError(f"Could not connect to API: {err}")
            except Exception as err: verbose_mode.log(f"API request error: {err}"); raise
    
    if result_data is not None:
        result_data = process_dataframe(result_data) # process_dataframe should handle Figures gracefully

        if forced_columns_list is not None and isinstance(result_data, (pd.DataFrame, pl.DataFrame)):
            current_data_cols = list(result_data.columns)
            cols_to_select_for_alias = [col for col in forced_columns_list if col in current_data_cols]
            
            if set(cols_to_select_for_alias) != set(current_data_cols): # Only re-select if different
                if cols_to_select_for_alias or not forced_columns_list : # Select if any valid cols, or if forced_columns was empty (select all valid ones)
                    verbose_mode.log(f"Applying final column filter for alias. Keeping: {cols_to_select_for_alias}")
                    if isinstance(result_data, pd.DataFrame): # Catches CustomDataFrame too
                        result_data = result_data[cols_to_select_for_alias]
                    elif isinstance(result_data, pl.DataFrame):
                        result_data = result_data.select(cols_to_select_for_alias)
                elif not cols_to_select_for_alias and forced_columns_list: # No valid columns found for non-empty forced_list
                     verbose_mode.log(f"Warning: Alias requested columns {forced_columns_list}, but none were found in the final processed data. Data remains as is.")

    return result_data


async def fetch_multiple_tickers(
    endpoint: str,
    tickers: List[str],
    **kwargs
) -> Dict[str, Union[DataFrameType, go.Figure, None]]: # Updated return type hint
    """
    Fetch data for multiple tickers concurrently using asyncio.
    
    Args:
        endpoint: API endpoint
        tickers: List of ticker symbols
        **kwargs: Additional parameters for the data function
        
    Returns:
        Dictionary mapping tickers to their respective DataFrames or Figures
    """
    import asyncio
    import concurrent.futures
    
    results: Dict[str, Union[DataFrameType, go.Figure, None]] = {}
    
    # Using ThreadPoolExecutor as `data` function is synchronous (contains network I/O)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        # Create a list of asyncio Future objects wrapped around executor submissions
        # Each future corresponds to a call to the `data` function for a single ticker
        async_futures = [
            loop.run_in_executor(
                executor,
                functools.partial(data, endpoint=endpoint, tickers=ticker, **kwargs) # Use functools.partial
            )
            for ticker in tickers
        ]
        
        # Wait for all futures to complete and gather results
        # `asyncio.gather` returns a list of results in the same order as input futures
        all_results_list = await asyncio.gather(*async_futures, return_exceptions=True)
        
        # Map results back to tickers
        for i, ticker_symbol in enumerate(tickers):
            result_item = all_results_list[i]
            if isinstance(result_item, Exception):
                verbose_mode.log(f"Error fetching data for ticker {ticker_symbol}: {result_item}")
                results[ticker_symbol] = None # Store None or the exception itself if preferred
            else:
                results[ticker_symbol] = result_item
            
    return results


# ------------------------------------------------------------------------
# Code Explanation (unchanged from original, describes general architecture)
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
   - Results caching with hash-based keys (now to disk: Parquet for DataFrames, Pickle for Figures)
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
from sovai import data # Assuming this module is named sovai.py or in sovai package

# Set your API token
from sovai.api_config import ApiConfig # Ensure ApiConfig is accessible
ApiConfig.token = "your_token_here"
ApiConfig.base_url = "your_api_base_url_here" # Ensure base_url is set

# Retrieve closing prices for Apple and Microsoft
# result = data(
#     endpoint="/market/closeadj",
#     tickers="AAPL,MSFT",
#     start_date="2023-01-01",
#     end_date="2023-12-31",
#     verbose=True
# )

# if result is not None and hasattr(result, 'head'):
#    print(result.head())
# elif result is not None:
#    print(type(result)) # e.g. if it's a Plotly Figure

# Example for concurrent fetching:
# import asyncio
# async def main():
#     results = await fetch_multiple_tickers(
#         endpoint="/market/closeadj",
#         tickers=["AAPL", "MSFT", "GOOGL"],
#         start_date="2023-01-01",
#         end_date="2023-12-31"
#     )
#     for ticker, df in results.items():
#         if df is not None and hasattr(df, 'head'):
#             print(f"--- {ticker} ---")
#             print(df.head())
#         elif df is not None:
#             print(f"--- {ticker} --- (type: {type(df)})")


# if __name__ == "__main__":
#    asyncio.run(main())
"""