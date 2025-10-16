from typing import Union, Any, List
from itertools import chain
import pandas as pd

from sovai.utils.helpers import dict_depth, evenly_dict_contains_list

import pandas as pd


def process_dataframe(df):
    """
    Processes the DataFrame to convert 'Date' column to datetime and sets appropriate indices.

    It handles different naming conventions for 'Date' and 'ticker(s)' columns.
    If 'Date' column exists, it is converted to datetime and set as an index.
    If 'ticker' or 'tickers' column also exists, a MultiIndex of ('ticker(s)', 'Date') is created.

    :param df: The DataFrame to process.
    :return: The processed DataFrame with the 'Date' as the datetime index or a MultiIndex with 'ticker(s)' and 'Date'.
    """
    # Possible column name variations
    date_variations = ["Date", "date", "Dates", "dates"]
    ticker_variations = ["Ticker", "ticker", "Tickers", "tickers"]

    # Identify the correct 'Date' column
    date_column = next((col for col in df.columns if col in date_variations), None)

    # Identify the correct 'ticker' column
    ticker_column = next((col for col in df.columns if col in ticker_variations), None)

    if date_column:
        df[date_column] = pd.to_datetime(
            df[date_column], errors="coerce"
        )  # Convert to datetime and coerce errors
        df.dropna(
            subset=[date_column], inplace=True
        )  # Drop rows where 'Date' couldn't be converted

        if ticker_column:
            df.set_index(
                [ticker_column, date_column], inplace=True
            )  # Set a MultiIndex with 'ticker(s)' and 'Date'
        else:
            df.set_index(date_column, inplace=True)  # Set 'Date' column as the index

    return df.sort_index()


# Example usage:
# df = pd.read_csv('your_file.csv')
# df = process_dataframe(df)


def convert_data2df(response: Union[dict, list]) -> Union[pd.DataFrame, Any]:
    """
    This function gets a nested dict or list from API, then processes it:
    - If "response" is a DataFrame, it returns it directly.
    - If "response" is a dict with a depth of 1 and evenly contains lists, it converts it to a DataFrame.
    - If "response" is a list and not charts data, it converts it to a DataFrame.
    If "response" is a dict containing 'data' and 'columns_order', it will reorder the DataFrame columns accordingly.

    :param response: raw data from api
    :return: DataFrame or the original response if it cannot be converted
    """
    # Check if response is already a DataFrame
    if isinstance(response, pd.DataFrame):
        return df

    # Check for data and columns_order in response
    if (
        isinstance(response, dict)
        and "data" in response
        and "columns_order" in response
    ):
        df = pd.DataFrame(response["data"])
        # Ensure all columns_order items are strings and exist in the DataFrame
        columns_order = [col for col in response["columns_order"] if col in df.columns]
        return process_dataframe(df[columns_order])

    # Convert dict with evenly contains lists to DataFrame
    if isinstance(response, dict) and (dict_depth(response) <= 1):
        if evenly_dict_contains_list(response):
            return process_dataframe(pd.DataFrame(response))

    # Convert list to DataFrame, provided it's not chart data
    if isinstance(response, list):
        # print("a list is returned")
        is_charts = any("chart" in name.lower() for item in response for name in item)
        if is_charts:
            print("its a chart")
        else:
            return process_dataframe(pd.DataFrame(response))

    # Return the original response if it cannot be converted to a DataFrame
    return response


# def convert_data2df(responce: Union[dict, list]) -> Union[pd.DataFrame, Any]:
#     """
#     This function get nested dict from API, then splits data
#     by fields inside the structure all "data" structure convert to DataFrame
#     and left return back as a dict

#     :param dict responce: raw data from api
#     :return pd.DataFrame
#     """
#     if isinstance(responce, pd.DataFrame):
#         return responce
#     if isinstance(responce, dict) and (dict_depth(responce) <= 1):
#         if evenly_dict_contains_list(responce):
#             return pd.DataFrame(responce)
#         return responce
#     if isinstance(responce, list):
#         is_charts = [
#             True for name in list(chain.from_iterable([item.keys() for item in responce])) if "chart" in name.lower()
#         ]
#         if not is_charts:
#             return pd.DataFrame(responce)
#     return responce
