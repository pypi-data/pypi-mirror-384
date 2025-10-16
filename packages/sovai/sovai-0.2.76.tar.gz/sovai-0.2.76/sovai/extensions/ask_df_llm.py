import pandas as pd
import openai
from textwrap import dedent
import re
from typing import Dict, Any, List, Union, Tuple
import io
from sovai.tools.sec.llm_code_generator import get_openai_key
import logging
from rapidfuzz import process, fuzz
import time

# Add these lines at the beginning of the file
logging.getLogger("httpx").setLevel(logging.WARNING)

_ask_cache: Dict[str, Any] = {}

verbose = False
mutable = False
models = ['gpt-3.5-turbo', 'gpt-4']
completion_config = {}

def sample_unique_values(df, max_samples=5):
    sample_data = {}
    for column in df.columns:
        unique_values = df[column].dropna().unique()
        sample = unique_values[:max_samples].tolist()
        sample_data[column] = sample
    return sample_data

def format_sample_data(sample_data):
    formatted_data = "Sample data from the DataFrame:\n\n"
    for column, values in sample_data.items():
        formatted_data += f"{column}:\n"
        for value in values:
            formatted_data += f"  - {value}\n"
        formatted_data += "\n"
    return formatted_data

def find_best_match(query: str, choices: List[str], threshold: int = 80) -> Union[str, None]:
    best_match = process.extractOne(query, choices, scorer=fuzz.ratio, score_cutoff=threshold)
    return best_match[0] if best_match else None

def parse_value(value: str) -> Union[float, int]:
    multipliers = {'k': 1e3, 'm': 1e6, 'b': 1e9}
    if value.endswith('%'):
        return float(value.rstrip('%')) / 100
    for suffix, multiplier in multipliers.items():
        if value.lower().endswith(suffix):
            return float(value[:-1]) * multiplier
    return float(value)

def create_standard_query(condition: str, df: pd.DataFrame) -> Tuple[str, str]:
    pattern = r'(\w+)\s*([<>=]+|like|contains)\s*(.+)'
    match = re.match(pattern, condition, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid condition format: {condition}")

    column, operator, value = match.groups()
    best_match = find_best_match(column, df.columns.tolist())
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
        parsed_value = parse_value(value)
        query = f"`{column}` {operator} {parsed_value}"
        display_operator = operator

    display_condition = f"{column} ({original_column}) {display_operator} {value}" if column != original_column else condition
    return query, display_condition

def is_simple_condition(condition: str) -> bool:
    simple_pattern = r'\w+\s*([<>=]+|like|contains)\s*.+'
    return bool(re.match(simple_pattern, condition, re.IGNORECASE))

def split_conditions(condition: str) -> List[str]:
    pattern = r'\s+(?:and|or)\s+(?![^()]*\))'
    conditions = re.split(pattern, condition, flags=re.IGNORECASE)
    return [cond.strip() for cond in conditions if cond.strip()]

class Ask:
    def __init__(self, *, verbose=None, mutable=None):
        self.verbose = verbose if verbose is not None else globals().get('verbose', False)
        self.mutable = mutable if mutable is not None else globals().get('mutable', False)

    @staticmethod
    def _fill_template(template, **kw):
        result = dedent(template.lstrip('\n').rstrip())
        for k, v in kw.items():
            result = result.replace(f'{{{k}}}', str(v))
        m = re.match(r'\{[a-zA-Z0-9_]*\}', result)
        if m:
            raise Exception(f'Expected variable: {m.group(0)}')
        return result

    def _get_prompt(self, goal, arg):
        if isinstance(arg, pd.DataFrame):
            buf = io.StringIO()
            arg.info(buf=buf)
            df_info = buf.getvalue()
            columns = ", ".join(arg.columns)
            sample_data = sample_unique_values(arg)
            formatted_sample_data = format_sample_data(sample_data)
        else:
            raise ValueError("Input must be a pandas DataFrame for filtering operations.")
        
        return self._fill_template(TEMPLATE, df_info=df_info.strip(), columns=columns, sample_data=formatted_sample_data, goal=goal.strip())

    def _run_prompt(self, prompt):
        global _ask_cache
        if prompt in _ask_cache:
            return _ask_cache[prompt]

        openai.api_key = get_openai_key()

        for model in models:
            try:
                completion = openai.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that writes Python code for DataFrame filtering operations."},
                        {"role": "user", "content": prompt},
                    ],
                    **completion_config,
                )
                result = completion.choices[0].message.content
                _ask_cache[prompt] = result
                return result
            except Exception as e:
                print(f"Error with model {model}: {str(e)}. Trying next model if available.")
                if model == models[-1]:
                    raise Exception("All models failed to generate a response.")
        
        raise Exception("Unexpected error: No models were tried.")

    def _extract_code_block(self, text):
        pattern = r'```(\s*(py|python)\s*\n)?([\s\S]*?)```'
        m = re.search(pattern, text)
        if not m:
            return text
        return m.group(3)

    ## if you want verbose, print Source here.
    def _eval(self, source, *args):
        _args_ = args
        scope = dict(_args_=args)
        try:
            exec(self._fill_template('''
                import pandas as pd
                {source}
                _result_ = process(*_args_)
            ''', source=source), scope)
            result = scope['_result_']
            if not isinstance(result, pd.DataFrame):
                raise ValueError("The function did not return a DataFrame.")
            if len(result) == 0:
                print("Warning: Filtering resulted in an empty DataFrame. Returning original DataFrame.")
                return args[0]
            if len(result) == len(args[0]):
                print("Warning: Filtering did not remove any rows. Check if the condition was applied correctly.")
            return result
        except Exception as e:
            print(f"Error in filtering: {str(e)}. Returning original DataFrame.")
            return args[0]

    def _code(self, goal, arg):
        prompt = self._get_prompt(goal, arg)
        result = self._run_prompt(prompt)
        if self.verbose:
            print()
            print(result)
        return self._extract_code_block(result)

    def code(self, *args):
        print(self._code(*args))

    def prompt(self, *args):
        print(self._get_prompt(*args))

    def __call__(self, goal, *args):
        source = self._code(goal, *args)
        return self._eval(source, *args)

    def apply_condition_with_retry(self, df: pd.DataFrame, condition: str, max_retries: int = 3) -> pd.DataFrame:
        original_len = len(df)
        
        sub_conditions = split_conditions(condition)
        if len(sub_conditions) > 1:
            if self.verbose:
                print(f"Detected multiple conditions: {sub_conditions}")
            for sub_condition in sub_conditions:
                df = self.apply_condition_with_retry(df, sub_condition, max_retries)
            return df
        
        if is_simple_condition(condition):
            try:
                query, display_condition = create_standard_query(condition, df)
                filtered_df = df.query(query)
                if len(filtered_df) < original_len:
                    if self.verbose:
                        print(f"Applied standard filter: {display_condition}")
                    return filtered_df
            except Exception as e:
                if self.verbose:
                    print(f"Standard filtering failed: {str(e)}. Falling back to GPT method.")
        
        for attempt in range(max_retries):
            try:
                filtered_df = self(condition, df)
                if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) < original_len:
                    return filtered_df
                elif self.verbose:
                    print(f"Attempt {attempt + 1}: GPT filtering didn't remove any rows. Retrying...")
                
                alternative_conditions = [f"filter {condition}", f"select {condition}", f"find {condition}"]
                for alt_condition in alternative_conditions:
                    try:
                        filtered_df = self(alt_condition, df)
                        if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) < original_len:
                            return filtered_df
                    except Exception:
                        pass
                
                columns_str = ", ".join(df.columns)
                general_condition = f"Based on the columns {columns_str}, {condition}"
                filtered_df = self(general_condition, df)
                if isinstance(filtered_df, pd.DataFrame) and len(filtered_df) < original_len:
                    return filtered_df
            except Exception as e:
                if self.verbose:
                    print(f"Error on GPT attempt {attempt + 1}: {str(e)}")
            time.sleep(1)
        
        if self.verbose:
            print("All filtering attempts failed. Returning original DataFrame.")
        return df

if not hasattr(pd.DataFrame, 'ask'):
    @pd.api.extensions.register_dataframe_accessor('ask')
    class AskAccessor:
        def __init__(self, pandas_obj):
            self._validate(pandas_obj)
            self._obj = pandas_obj

        @staticmethod
        def _validate(obj):
            if not isinstance(obj, pd.DataFrame):
                raise AttributeError("'ask' accessor is only available for DataFrames.")

        def _ask(self, **kw):
            return Ask(**kw)

        def _data(self, **kw):
            if not globals().get('mutable', False) and not kw.get('mutable'):
                return self._obj.copy()
            return self._obj

        def __call__(self, goal, *args, **kw):
            ask = self._ask(**kw)
            data = self._data(**kw)
            return ask(goal, data, *args)

        def code(self, goal, *args, **kw):
            ask = self._ask(**kw)
            data = self._data(**kw)
            return ask.code(goal, data, *args)

        def prompt(self, goal, *args, **kw):
            ask = self._ask(**kw)
            data = self._data(**kw)
            return ask.prompt(goal, data, *args)

        def apply_condition_with_retry(self, condition, max_retries=3, **kw):
            ask = self._ask(**kw)
            data = self._data(**kw)
            return ask.apply_condition_with_retry(data, condition, max_retries)
else:
    pass

TEMPLATE = """
Write a Python function `process(df)` which takes a pandas DataFrame as input.
DataFrame information:
{df_info}

Available columns: {columns}

Sample data:
{sample_data}

This function should filter the DataFrame based on the following goal: {goal}

Important instructions:
1. Only use columns that are listed in the 'Available columns'.
2. The function must return a filtered DataFrame.
3. If no filtering is possible or if the filtering results in an empty DataFrame, return the original DataFrame with a comment explaining why.
4. Do not use any external libraries other than pandas.
5. Ensure that your filtering logic is correct and doesn't inadvertently return an empty DataFrame.
6. Only define the function without trying to call it!

Write the function in a Python code block with all necessary imports and no example usage.
"""