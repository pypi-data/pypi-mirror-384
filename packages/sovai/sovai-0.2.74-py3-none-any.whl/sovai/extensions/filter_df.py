
import pandas as pd
import re
import time
from typing import Union, List, Tuple
from functools import wraps
from rapidfuzz import process, fuzz
from sovai.tools.sec.llm_code_generator import get_openai_key
from collections import deque
from datetime import datetime, timedelta
import openai
from textwrap import dedent
from functools import lru_cache

def with_openai_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        openai.api_key = get_openai_key()
        try:
            return func(*args, **kwargs)
        finally:
            openai.api_key = None
    return wrapper

class Filter:
    _call_timestamps = deque()
    _max_calls_per_minute = 10
    _ask_cache = {}
    verbose = False
    mutable = False
    models = ['gpt-3.5-turbo', 'gpt-4']
    completion_config = {}


    @staticmethod
    @lru_cache(maxsize=1)
    def _load_combined_df():
        return pd.read_parquet("https://storage.googleapis.com/sovai-public/concats/filters/latest.parquet")


    @classmethod
    def _check_rate_limit(cls):
        now = datetime.now()
        while cls._call_timestamps and cls._call_timestamps[0] < now - timedelta(minutes=1):
            cls._call_timestamps.popleft()
        
        if len(cls._call_timestamps) >= cls._max_calls_per_minute:
            raise ValueError("Slow down mate! You've reached the maximum number of filtering attempts per minute.")
        
        cls._call_timestamps.append(now)

    @staticmethod
    def rate_limit_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            Filter._check_rate_limit()
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def _find_best_match(query: str, choices: List[str], threshold: int = 80) -> Union[str, None]:
        best_match = process.extractOne(query, choices, scorer=fuzz.ratio, score_cutoff=threshold)
        return best_match[0] if best_match else None

    @staticmethod
    def _parse_value(value: str) -> Union[float, int]:
        multipliers = {'k': 1e3, 'm': 1e6, 'b': 1e9}
        if value.endswith('%'):
            return float(value.rstrip('%')) / 100
        for suffix, multiplier in multipliers.items():
            if value.lower().endswith(suffix):
                return float(value[:-1]) * multiplier
        return float(value)

    @classmethod
    def _create_standard_query(cls, condition: str, df: pd.DataFrame) -> Tuple[str, str]:
        pattern = r'(\w+)\s*([<>=]+|like|contains)\s*(.+)'
        match = re.match(pattern, condition, re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid condition format: {condition}")

        column, operator, value = match.groups()
        best_match = cls._find_best_match(column, df.columns.tolist())
        if not best_match:
            raise ValueError(f"No close match found for column: {column}")

        original_column = column
        column = best_match
        
        operator = operator.lower().strip()
        value = value.strip()

        is_string_type = df[column].dtype == 'object'

        if operator in ['like', 'contains'] or (operator == '=' and is_string_type):
            query = f"`{column}`.str.contains('{value}', case=False, na=False)"
            display_operator = 'like'
        else:
            parsed_value = cls._parse_value(value)
            query = f"`{column}` {operator} {parsed_value}"
            display_operator = operator

        display_condition = f"{column} ({original_column}) {display_operator} {value}" if column != original_column else condition
        return query, display_condition
    
    @staticmethod
    def _is_simple_condition(condition: str) -> bool:
        simple_pattern = r'\w+\s*([<>=]+|like|contains)\s*.+'
        return bool(re.match(simple_pattern, condition, re.IGNORECASE))

    @staticmethod
    def _split_conditions(condition: str) -> List[str]:
        pattern = r'\s+(?:and|or)\s+(?![^()]*\))'
        conditions = re.split(pattern, condition, flags=re.IGNORECASE)
        return [cond.strip() for cond in conditions if cond.strip()]

    @classmethod
    @rate_limit_decorator
    @with_openai_key
    def _apply_condition_with_retry(cls, df: pd.DataFrame, condition: str, max_retries: int = 3, verbose: bool = False) -> pd.DataFrame:
        original_len = len(df)
        
        sub_conditions = cls._split_conditions(condition)
        if len(sub_conditions) > 1:
            if verbose:
                print(f"Detected multiple conditions: {sub_conditions}")
            for sub_condition in sub_conditions:
                df = cls._apply_condition_with_retry(df, sub_condition, max_retries, verbose)
            return df
        
        if cls._is_simple_condition(condition):
            try:
                query, display_condition = cls._create_standard_query(condition, df)
                filtered_df = df.query(query)
                if len(filtered_df) < original_len:
                    if verbose:
                        print(f"Applied standard filter: {display_condition}")
                    return filtered_df
            except Exception as e:
                if verbose:
                    print(f"Standard filtering failed: {str(e)}. Falling back to GPT method.")
        
        for attempt in range(max_retries):
            try:
                filtered_df = df.ask(condition)
                if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) < original_len:
                    return filtered_df
                elif verbose:
                    print(f"Attempt {attempt + 1}: GPT filtering didn't remove any rows. Retrying...")
                
                alternative_conditions = [f"filter {condition}", f"select {condition}", f"find {condition}"]
                for alt_condition in alternative_conditions:
                    try:
                        filtered_df = df.ask(alt_condition)
                        if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) < original_len:
                            return filtered_df
                    except Exception:
                        pass
                
                columns_str = ", ".join(df.columns)
                general_condition = f"Based on the columns {columns_str}, {condition}"
                filtered_df = df.ask(general_condition)
                if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) < original_len:
                    return filtered_df
            except Exception as e:
                if verbose:
                    print(f"Error on GPT attempt {attempt + 1}: {str(e)}")
            time.sleep(1)
        
        if verbose:
            print("All filtering attempts failed. Returning original DataFrame.")
        return df


    @staticmethod
    def create_table(data, headers):
        col_widths = [max(len(str(x)) for x in col) for col in zip(*data, headers)]
        col_widths = [max(15, width) for width in col_widths]
        
        row_format = '│ {:<{}} │ {:>{}} │ {:>{}} │ {:>{}} │'
        header = row_format.format(headers[0], col_widths[0], 
                                   headers[1], col_widths[1], 
                                   headers[2], col_widths[2], 
                                   headers[3], col_widths[3])
        
        separator = '┼' + '─' * (col_widths[0] + 2) + '┼' + '─' * (col_widths[1] + 2) + '┼' + '─' * (col_widths[2] + 2) + '┼' + '─' * (col_widths[3] + 2) + '┼'
        top_border = '┌' + '─' * (col_widths[0] + 2) + '┬' + '─' * (col_widths[1] + 2) + '┬' + '─' * (col_widths[2] + 2) + '┬' + '─' * (col_widths[3] + 2) + '┐'
        bottom_border = '└' + '─' * (col_widths[0] + 2) + '┴' + '─' * (col_widths[1] + 2) + '┴' + '─' * (col_widths[2] + 2) + '┴' + '─' * (col_widths[3] + 2) + '┘'
        
        rows = []
        for i, row in enumerate(data):
            if i == 0:  # Initial row
                formatted_row = row_format.format(row[0], col_widths[0],
                                                  f"{row[1]:,}", col_widths[1],
                                                  '-', col_widths[2],
                                                  '-', col_widths[3])
            elif i == len(data) - 1:  # Final row
                formatted_row = row_format.format(row[0], col_widths[0],
                                                  f"{data[0][1]:,}", col_widths[1],
                                                  f"{row[2]:,}", col_widths[2],
                                                  f"{row[1]:,}", col_widths[3])
            else:  # Other rows
                formatted_row = row_format.format(row[0], col_widths[0],
                                                  f"{row[1]:,}", col_widths[1],
                                                  f"{row[2]:,}", col_widths[2],
                                                  f"{row[1]:,}", col_widths[3])
            rows.append(formatted_row)
        
        return '\n'.join([top_border, header, separator] + rows[:-1] + [separator, rows[-1], bottom_border])

    @classmethod
    def filter_dataframes(cls, df_multi: pd.DataFrame, conditions: List[str], verbose: bool = False) -> pd.DataFrame:
        df_combined = cls._load_combined_df()
        
        # Calculate initial companies based on df_multi
        if isinstance(df_multi.index, pd.MultiIndex):
            initial_companies = df_multi.index.get_level_values(0).nunique()
        else:
            initial_companies = df_multi.index.nunique()
        
        table_data = [["Initial", initial_companies, "-", "-"]]
        current_df = df_combined.copy()
        condition_counter = 1
        
        previous_companies_left = initial_companies  # Initialize for the first calculation

        for condition in conditions:
            try:
                query, display_condition = cls._create_standard_query(condition, current_df)
                filtered_df = current_df.query(query)
                if len(filtered_df) < len(current_df):
                    filter_type = "Standard filter"
                else:
                    filtered_df = cls._apply_condition_with_retry(current_df, condition, verbose=verbose)
                    filter_type = "LLM filter"
            except Exception:
                filtered_df = cls._apply_condition_with_retry(current_df, condition, verbose=verbose)
                filter_type = "LLM filter"

            print(f"Condition {condition_counter}: {condition} ({filter_type})")

            if filtered_df is None or len(filtered_df) == 0:
                print(f"Warning: Condition {condition_counter} resulted in an empty DataFrame. Skipping this condition.")
                continue

            # Calculate companies_left based on df_multi
            if isinstance(df_multi.index, pd.MultiIndex):
                tickers_in_df_multi = df_multi.index.get_level_values(0).unique()
            else:
                tickers_in_df_multi = df_multi.index.unique()

            filtered_tickers = filtered_df.index.unique()
            companies_left = len(set(filtered_tickers).intersection(set(tickers_in_df_multi)))
            companies_removed = previous_companies_left - companies_left

            table_data.append([f"Condition {condition_counter}", companies_left, companies_removed, companies_left])
            current_df = filtered_df
            condition_counter += 1
            previous_companies_left = companies_left  # Update for next iteration

        final_companies = previous_companies_left
        total_removed = initial_companies - final_companies
        table_data.append(["Final", final_companies, total_removed, final_companies])

        headers = ["Step", "Total Tickers", "Removed", "Left"]
        table = cls.create_table(table_data, headers)
        print("\nFiltering Results:")
        print(table)

        if final_companies == 0:
            print("\nWarning: No companies available after applying all conditions.")
            print("Consider revising the following conditions:")
            for i, condition in enumerate(conditions, 1):
                print(f"  Condition {i}: {condition}")
            return pd.DataFrame()
        elif final_companies < 10:
            print(f"\nWarning: Only {final_companies} companies available. Consider revising some conditions.")

        if df_multi is not None:
            try:
                if isinstance(df_multi.index, pd.MultiIndex):
                    filtered_df_multi = df_multi.loc[df_multi.index.get_level_values(0).isin(current_df.index)]
                else:
                    filtered_df_multi = df_multi.loc[df_multi.index.isin(current_df.index)]
                
                if len(filtered_df_multi) == 0:
                    print("Warning: No matching rows found in df_multi. Returning an empty DataFrame.")
                    return pd.DataFrame()
                
                if len(filtered_df_multi) < len(current_df):
                    print(f"Warning: Only {len(filtered_df_multi)} out of {len(current_df)} filtered companies found in df_multi.")
                
                return filtered_df_multi
            except Exception as e:
                print(f"Error filtering df_multi: {str(e)}")
                return pd.DataFrame()
        else:
            return current_df


    @classmethod
    def filter(cls, conditions: Union[str, List[str]], df_multi: pd.DataFrame = None, verbose: bool = False) -> pd.DataFrame:
        if isinstance(conditions, str):
            conditions = [conditions]
        return cls.filter_dataframes(df_multi, conditions, verbose)