# Inside plot/get_plot.py
import inspect # Still useful for one specific check

# --- Top Level Imports (Keep lightweight) ---
from typing import Optional, Union, Tuple, List, Dict
import importlib # Needed for dynamic imports
# Keep pandas/plotly config at top level as they modify global state
import pandas as pd
import plotly.io as pio

# --- Global Settings ---
# Changing the default plotting backend to Plotly
# Ensure pandas is imported before using pd.options
pd.options.plotting.backend = "plotly"
pd.set_option("display.max_columns", None)
# Setting the default theme for Plotly to a dark mode
pio.templates.default = "plotly_dark"


# --- Helper Functions (Potentially moved or kept if simple) ---

def enable_plotly_in_cell():
    # Lazy load IPython and plotly offline here
    try:
        import IPython
        from IPython.display import display, HTML
        from plotly.offline import init_notebook_mode

        display(
            HTML(
                """<script src="/static/components/requirejs/require.js"></script>"""
            )
        )
        init_notebook_mode(connected=False)
    except ImportError:
        print("Warning: IPython or plotly offline not available. Plotly may not render correctly in this environment.")


def _draw_graphs(data: Union[Dict, List[Dict]]):
    """Helper to draw graphs from database results (if structure is consistent)."""
    # Lazy load the actual plotting utility if needed
    from sovai.utils.plot import plotting_data # Assuming this utility exists
    if isinstance(data, list):
        for plot_dict in data:
             if isinstance(plot_dict, dict):
                  for _, val in plot_dict.items():
                      return plotting_data(val) # Plot first one found
    elif isinstance(data, dict):
        for _, val in data.items():
            return plotting_data(val) # Plot first one found
    else:
         print(f"Warning: _draw_graphs received unexpected data type: {type(data)}")
         return None


def generate_error_message(analysis_type, chart_type, source, verbose):
    """Generates error message, potentially displaying Markdown."""
    try:
         from IPython.display import display, Markdown
         if source == "local":
             code_snippet = (
                 f"# Ensure sovai is imported, e.g., import sovai as sov\n"
                 f"dataset = sov.data('{analysis_type}/monthly') # Or appropriate frequency\n"
                 f"if dataset is not None and not dataset.empty:\n"
                 f"    sov.plot('{analysis_type}', chart_type='{chart_type}', df=dataset)\n"
                 f"else:\n"
                 f"    print('Failed to fetch data.')"
             )
             message = (
                 f"**Input DataFrame `df` is empty or None.** Please provide a valid DataFrame.\n"
                 f"If you intended to fetch data first, you could use:\n\n"
                 f"```python\n{code_snippet}\n```"
             )
             if verbose: # Only display if verbose is True
                 display(Markdown(message))
             return "" # Return empty string as add_text no longer used this way
         else:
             display(Markdown("**An unknown error occurred.**")) # This part might be too generic
             return ""
    except ImportError:
         # Fallback for non-IPython environments
         text_message = ""
         if source == "local":
              text_message = f"Input DataFrame `df` is empty or None. Please fetch data first (e.g., using sov.data(...))."
         else:
              text_message = "An unknown error occurred."
         if verbose: # Print simple text if verbose and IPython not available
             print(text_message)
         return ""


# --- Plot Function Mapper ---
PLOT_FUNCTION_MAPPER = {
    # (dataset_name, chart_type, source, full_history_flag_or_None) : (module_path, function_name)
    ("breakout", "predictions", "local", True): (".plots.breakout.breakout_plots", "get_predict_breakout_plot_for_ticker"),
    ("breakout", "accuracy", "local", True): (".plots.breakout.breakout_plots", "interactive_plot_display_breakout_accuracy"),
    ("accounting/weekly", "balance", "local", False): (".plots.accounting.accounting_plots", "get_balance_sheet_tree_plot_for_ticker"),
    ("accounting", "cashflows", "local", True): (".plots.accounting.accounting_plots", "plot_cash_flows"),
    ("accounting", "assets", "local", True): (".plots.accounting.accounting_plots", "plot_assets"),
    ("ratios", "relative", "local", True): (".plots.ratios.ratios_plots", "plot_ratios_triple"),
    ("ratios", "benchmark", "local", True): (".plots.ratios.ratios_plots", "plot_ratios_benchmark"),
    ("institutional", "flows", "local", True): (".plots.institutional.institutional_plots", "institutional_flows_plot"),
    ("institutional", "prediction", "local", True): (".plots.institutional.institutional_plots", "institutional_flow_predictions_plot"),
    ("insider", "percentile", "local", True): (".plots.insider.insider_plots", "create_parallel_coordinates_plot_single_ticker"),
    ("insider", "flows", "local", True): (".plots.insider.insider_plots", "insider_flows_plot"),
    ("insider", "prediction", "local", True): (".plots.insider.insider_plots", "insider_flow_predictions_plot"),
    ("news", "sentiment", "local", True): (".plots.news.news_plots", "plot_above_sentiment_returns"),
    ("news", "strategy", "local", True): (".plots.news.news_plots", "plot_news_daily"),
    ("news", "analysis", "local", True): (".plots.news.news_plots", "run_dash_news_ts"),
    ("corprisk/risks", "line", "local", True): (".plots.corp_risk.corp_risk_plots", "plotting_corp_risk_line"),
    ("allocation", "line", "local", True): (".plots.allocation.allocation_plots", "create_line_plot_allocation"),
    ("allocation", "stacked", "local", True): (".plots.allocation.allocation_plots", "create_stacked_bar_plot_allocation"),
    ("earnings/surprise", "line", "local", True): (".plots.earnings_surprise.earnings_surprise_plots", "create_earnings_surprise_plot"),
    ("earnings/surprise", "tree", "local", True): (".plots.earnings_surprise.earnings_surprise_plots", "earnings_tree"),
    ("bankruptcy", "compare", "local", True): (".plots.bankruptcy.bankruptcy_plots", "plot_bankruptcy_monthly_line"),
    ("bankruptcy", "pca_clusters", "local", True): (".plots.bankruptcy.bankruptcy_plots", "plot_pca_clusters"),
    ("bankruptcy", "predictions", "local", True): (".plots.bankruptcy.bankruptcy_plots", "plot_ticker_widget"),

    # Database plots use the local _draw_graphs helper
    ("bankruptcy", "shapley", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "pca", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "line", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "similar", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "facet", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "stack", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "box", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "waterfall", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "pca_relation", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "line_relation", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "facet_relation", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "time_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "stack_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "box_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "waterfall_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "confusion_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "classification_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "precision_global", "database"): (None, "_draw_graphs"),
    ("bankruptcy", "lift_global", "database"): (None, "_draw_graphs"),
}


# --- Main Plot Function ---

def plot(
    dataset_name,
    chart_type=None,
    df=None,
    tickers: Optional[List[str]] = None,
    ticker: Optional[str] = None,
    verbose=False,
    purge_cache=False,
    **kwargs, # These are kwargs passed to the main sov.plot() call
):
    """
    Generates plots based on dataset name and chart type.
    Lazily loads required plotting modules.
    """
    from sovai import data as sovai_data

    # Consolidate ticker/tickers from sov.plot() into lookup_tickers for sovai_data
    # and also ensure they are present in kwargs for the plot_function if needed.
    if ticker is not None:
        if isinstance(ticker, str):
            lookup_tickers = [ticker]
            kwargs['ticker'] = ticker # Ensure 'ticker' is in kwargs for plot_func
        elif isinstance(ticker, list):
            lookup_tickers = ticker
            if len(ticker) == 1: # If plot_func expects single 'ticker'
                 kwargs['ticker'] = ticker[0]
            # If plot_func expects 'tickers' (list), it should already be in kwargs if passed as 'tickers='
        else: # Should not happen
            lookup_tickers = None
    elif tickers is not None:
        if isinstance(tickers, str):
            lookup_tickers = [tickers]
            kwargs['tickers'] = [tickers] # Ensure 'tickers' list is in kwargs
        elif isinstance(tickers, list):
            lookup_tickers = tickers
            kwargs['tickers'] = tickers
        else: # Should not happen
            lookup_tickers = None
    else:
        lookup_tickers = None
    
    enable_plotly_in_cell()

    plot_info = None; source = None; full_history = None
    key_local_4 = (dataset_name, chart_type, "local", True)
    key_local_3 = (dataset_name, chart_type, "local", False)
    key_db_3 = (dataset_name, chart_type, "database")

    if key_local_4 in PLOT_FUNCTION_MAPPER:
        source = "local"; full_history = True; plot_info = PLOT_FUNCTION_MAPPER[key_local_4]
    elif key_local_3 in PLOT_FUNCTION_MAPPER:
         source = "local"; full_history = False; plot_info = PLOT_FUNCTION_MAPPER[key_local_3]
    elif key_db_3 in PLOT_FUNCTION_MAPPER:
        source = "database"; plot_info = PLOT_FUNCTION_MAPPER[key_db_3]
    else:
         key_local_any_hist = (dataset_name, chart_type, "local")
         possible_keys = [k for k in PLOT_FUNCTION_MAPPER if k[:3] == key_local_any_hist]
         if possible_keys:
              matched_key = possible_keys[0]
              source = "local"; full_history = matched_key[3]; plot_info = PLOT_FUNCTION_MAPPER[matched_key]
         else:
              raise ValueError(f"Plotting function for dataset='{dataset_name}' with chart_type='{chart_type}' not found.")

    module_path, function_name = plot_info

    plot_function = None
    if module_path:
        try:
            imported_module = importlib.import_module(module_path, package=__package__)
            plot_function = getattr(imported_module, function_name)
        except ImportError as e:
            raise ImportError(f"Could not import plotting module '{module_path}' relative to {__package__}: {e}")
        except AttributeError:
            raise AttributeError(f"Function '{function_name}' not found in module '{module_path}'.")
    elif function_name == "_draw_graphs":
        plot_function = _draw_graphs
    else:
         raise ValueError(f"Invalid plot_info found in mapper: {plot_info} for {dataset_name}, {chart_type}")

    if source == "local":
        data_to_plot = df # User-provided DataFrame
        
        # --- Conditional Data Fetching ---
        # Check if the plot function seems to handle its own data via 'ticker' or 'tickers' params
        # and if it doesn't explicitly take 'df' or a generic first positional for data.
        skip_prefetch = False
        try:
            sig = inspect.signature(plot_function)
            param_names = set(sig.parameters.keys())
            # Heuristic: if it takes 'ticker' or 'tickers' but NOT 'df' or 'data' (common df names)
            # AND doesn't seem to take a generic first positional argument for data (e.g. only has keyword args)
            has_ticker_arg = 'ticker' in param_names or 'tickers' in param_names
            has_df_arg = 'df' in param_names or 'data' in param_names or 'data_df' in param_names
            
            first_param = next(iter(sig.parameters.values()), None)
            is_first_pos_for_data = first_param and \
                                    (first_param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or \
                                     first_param.kind == inspect.Parameter.POSITIONAL_ONLY) and \
                                    first_param.name not in ('ticker', 'tickers') # Not 'ticker' itself

            if has_ticker_arg and not has_df_arg and not is_first_pos_for_data :
                skip_prefetch = True
                if verbose: print(f"Plot function '{function_name}' seems to manage its own data via ticker/tickers; skipping dispatcher prefetch.")
        except ValueError: # Built-in functions might not have inspectable signatures
            pass # Proceed with default prefetch

        if not skip_prefetch and (data_to_plot is None or data_to_plot.empty):
            if verbose:
                generate_error_message(dataset_name, chart_type, source, verbose)
                print(f"Attempting to fetch data for {dataset_name} (tickers: {lookup_tickers}, full_history: {full_history})...")
            try:
                 fetched_data = sovai_data(dataset_name, tickers=lookup_tickers, full_history=full_history)
                 if fetched_data is not None and not fetched_data.empty:
                     data_to_plot = fetched_data
                     if verbose: print(f"Successfully fetched data for {dataset_name}.")
                 else:
                     if verbose: print(f"Failed to fetch data or fetched empty data for {dataset_name}.")
            except Exception as e:
                 if verbose: print(f"Error fetching data for {dataset_name}: {e}")
        
        # --- Call plot function with refined try-except ---
        try:
            if verbose: print(f"Calling plot function '{function_name}'.")
            return plot_function(data_to_plot, **kwargs)
        except TypeError as te:
            # Handle 0-argument function error
            is_zero_arg_error = (
                "takes 0 positional arguments" in str(te) and
                "1 was given" in str(te)
            )
            if is_zero_arg_error:
                if verbose: print(f"TypeError (0-arg): Retrying {function_name} with only kwargs.")
                try:
                    return plot_function(**kwargs) # Retry with only kwargs
                except Exception as e_fallback:
                    print(f"Original TypeError (0-arg) with {function_name}: {te}")
                    print(f"Error in 0-arg fallback for '{function_name}': {e_fallback}")
                    raise e_fallback
            
            # Handle case where plot_function expects specific kwargs (like 'ticker')
            # but received data_to_plot as an unwanted positional argument.
            # This often happens if plot_function is like `def func(ticker=None):`
            # and was called as `func(data_frame, ticker='val')`
            else:
                try:
                    sig = inspect.signature(plot_function)
                    # Filter kwargs to only those accepted by plot_function
                    accepted_kwargs = {
                        k: v for k, v in kwargs.items() 
                        if k in sig.parameters or \
                           any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                    }
                    # If data_to_plot was non-None and function has no clear positional data param,
                    # it might be the cause of the TypeError. Try without it.
                    
                    # Heuristic: Does the function primarily expect keyword args like 'ticker'?
                    # And does not seem to want data_to_plot positionally?
                    param_names = set(sig.parameters.keys())
                    first_param = next(iter(sig.parameters.values()), None)
                    takes_pos_data = first_param and \
                                     (first_param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or \
                                      first_param.kind == inspect.Parameter.POSITIONAL_ONLY) and \
                                     first_param.name not in ('ticker', 'tickers') # and not 'df', 'data' etc.

                    if not takes_pos_data and ('ticker' in param_names or 'tickers' in param_names):
                        if verbose: print(f"TypeError (kwarg-focused func): Retrying {function_name} with accepted kwargs, no positional data.")
                        return plot_function(**accepted_kwargs)
                    else:
                        # Original TypeError was likely valid for other reasons
                        print(f"TypeError calling plot function '{function_name}': {te}. Args: {data_to_plot}, Kwargs: {kwargs}")
                        raise te
                except Exception as e_inspect_fallback:
                    # If inspection or second attempt itself fails, raise original TypeError
                    print(f"Error during TypeError fallback for {function_name}: {e_inspect_fallback}")
                    print(f"Original TypeError calling plot function '{function_name}': {te}. Args: {data_to_plot}, Kwargs: {kwargs}")
                    raise te from None # Raise original te, suppress context from e_inspect_fallback
        except Exception as e:
            print(f"An unexpected error occurred while calling plot function '{function_name}': {e}")
            raise e
    elif source == "database":
        try:
            datasets = sovai_data(
                dataset_name + "/charts",
                chart=chart_type,
                tickers=lookup_tickers,
                purge_cache=purge_cache,
                **kwargs,
            )
        except Exception as e:
             if verbose: print(f"Error fetching database chart data for {dataset_name}: {e}")
             return None

        if datasets is None:
            if verbose: print(f"Failed to retrieve data for {dataset_name}/charts with chart type {chart_type} and tickers {lookup_tickers}")
            return None

        try:
            if isinstance(datasets, list):
                 if plot_function == _draw_graphs:
                      for dataset_item in datasets:
                           if dataset_item is not None:
                                fig = plot_function(dataset_item, **kwargs)
                                if fig: return fig
                      if verbose: print("No plottable data found in the list of datasets for _draw_graphs.")
                      return None
                 else:
                      if verbose: print("Warning: Received a list of datasets for database source, plotting first non-None item.")
                      for dataset_item in datasets:
                          if dataset_item is not None:
                              return plot_function(dataset_item, **kwargs)
                      if verbose: print("No non-None dataset found in the list to plot.")
                      return None
            else:
                 return plot_function(datasets, **kwargs)
        except Exception as e:
             print(f"Error calling plot function '{function_name}' for database data: {e}")
             raise e
    else:
        raise ValueError(f"Source '{source}' derived from mapper is not recognized.")