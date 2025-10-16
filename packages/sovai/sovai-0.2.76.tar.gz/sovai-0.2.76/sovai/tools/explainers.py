"""
Explanation tools for charts, tables, and overall analysis.
This module contains all the implementation details for the explain functionality.
"""

from typing import Optional, Union
import pandas as pd


def explain(input_obj, display_explanation=True, category=None, plot_name=None, force_refresh=False, return_plot=True):
    """
    Unified explain function that intelligently routes based on input type.
    
    Parameters:
    -----------
    input_obj : plotly.graph_objects.Figure, str, or SignalEvaluator
        Either:
        - A Plotly figure to explain (single chart)
        - A string category name for overall explanation (e.g., "signal_evaluation")
        - A SignalEvaluator object to explain performance_table
    display_explanation : bool
        Whether to display the explanation immediately
    category : str, optional
        For chart explanations: category for caching (auto-detected if not provided)
    plot_name : str, optional
        For chart explanations: plot name for caching (auto-detected if not provided)
    force_refresh : bool
        For overall explanations: whether to regenerate even if cached
    return_plot : bool
        For chart explanations: whether to return both explanation and plot
        
    Returns:
    --------
    str or dict : 
        - For category input: explanation markdown string, or None if failed
        - For plot input: dict with 'explanation' and 'plot' keys if return_plot=True, 
                         or just explanation string if return_plot=False
        - For SignalEvaluator: explanation markdown string, or None if failed
    
    Examples:
    ---------
    >>> # Explain a single chart (returns both explanation and plot)
    >>> result = sov.explain(evaluator.performance_plot)
    >>> print(result['explanation'])  # Explanation text
    >>> result['plot']  # The plot figure
    
    >>> # Explain overall category
    >>> sov.explain("signal_evaluation")
    
    >>> # Explain performance table from evaluator
    >>> sov.explain(evaluator.performance_table)
    >>> sov.explain(evaluator)
    """
    from ..extensions.chart_explainer import explain_chart
    from ..extensions.table_explainer import explain_table, explain_performance_table
    
    # Check if input is None
    if input_obj is None:
        if display_explanation:
            from IPython.display import display, Markdown
            display(Markdown("❌ **Cannot explain None object.**"))
        return None
    
    # Check if input is a dict with DataFrames (from performance_table)
    if isinstance(input_obj, dict):
        # Check if it's a dict of DataFrames (e.g., from statistics())
        if all(isinstance(v, pd.DataFrame) for v in input_obj.values()):
            # Combine all DataFrames with their titles
            combined_explanation = []
            
            for key, df in input_obj.items():
                # Convert key to a nice title
                title = key.replace("_", " ").title()
                
                # Determine table type
                table_type = "performance_stats" if "stats" in key.lower() else "general"
                
                explanation = explain_table(
                    table_data=df,
                    title=title,
                    description=None,
                    table_type=table_type,
                    display_explanation=False,
                    category=category,
                    plot_name=plot_name,
                    cache_data=True
                )
                
                if explanation:
                    combined_explanation.append(f"### {title}\n\n{explanation}")
            
            full_explanation = "\n\n---\n\n".join(combined_explanation)
            
            if display_explanation and full_explanation:
                from IPython.display import display, Markdown
                display(Markdown("---"))
                display(Markdown("## 📊 Performance Table Explanation"))
                display(Markdown(full_explanation))
                display(Markdown("---"))
                return None
            else:
                return full_explanation
    
    # Check if input is a string (category name for overall explanation)
    if isinstance(input_obj, str):
        from ..extensions.overall_explainers import explain_overall as _explain_overall
        result = _explain_overall(
            category=input_obj, 
            display_explanation=False,  # We'll handle display ourselves
            force_refresh=force_refresh
        )
        
        if display_explanation and result is not None:
            from IPython.display import display, Markdown
            display(Markdown("---"))
            display(Markdown("## 🤖 Overall Analysis"))
            display(Markdown(result))
            display(Markdown("---"))
            # Suppress the return output when displaying
            return None
        else:
            return result
    
    # Check if input is a SignalEvaluator object
    try:
        from ..extensions.signal_evaluation import SignalEvaluator
        if isinstance(input_obj, SignalEvaluator):
            # Explain the performance table
            explanation = explain_performance_table(
                input_obj, 
                display_explanation=False,  # We'll handle display ourselves
                cache_data=True
            )
            
            if display_explanation and explanation is not None:
                from IPython.display import display, Markdown
                display(Markdown("---"))
                display(Markdown("## 📊 Performance Table Explanation"))
                display(Markdown(explanation))
                display(Markdown("---"))
                return None
            else:
                return explanation
    except ImportError:
        pass
    
    # Check if input is a pandas DataFrame (table data)
    if isinstance(input_obj, pd.DataFrame):
        # Auto-detect table characteristics
        title = "Data Table"
        table_type = "general"
        
        # Try to infer table type from column names
        col_names_str = ' '.join(str(col).lower() for col in input_obj.columns)
        if any(term in col_names_str for term in ['sharpe', 'return', 'volatility', 'drawdown', 'profit', 'loss', 'trades']):
            table_type = "performance_stats"
            title = "Performance Statistics"
        elif any(term in col_names_str for term in ['drawdown', 'peak', 'valley', 'recovery']):
            table_type = "drawdown_analysis"
            title = "Drawdown Analysis"
        
        explanation = explain_table(
            table_data=input_obj,
            title=title,
            description=None,
            table_type=table_type,
            display_explanation=False,  # We'll handle display ourselves
            category=category,
            plot_name=plot_name,
            cache_data=True
        )
        
        if display_explanation and explanation is not None:
            from IPython.display import display, Markdown
            display(Markdown("---"))
            display(Markdown("## 📊 Table Explanation"))
            display(Markdown(explanation))
            display(Markdown("---"))
            return None
        else:
            return explanation
    
    # Otherwise, assume it's a figure object
    explanation = explain_chart(
        input_obj, 
        display_explanation=False,  # We'll handle display ourselves
        category=category, 
        plot_name=plot_name
    )
    
    if return_plot and explanation is not None:
        # Create combined display with explanation at top and plot below
        from IPython.display import display, Markdown
        
        if display_explanation:
            display(Markdown("---"))
            display(Markdown("## 🤖 Chart Explanation"))
            display(Markdown(explanation))
            display(Markdown("---"))
            display(Markdown("## 📊 Chart"))
            display(input_obj)
        
        # When display_explanation=True, suppress the return output by returning None
        # but still provide access to the data if needed
        if display_explanation:
            # Store the result in a temporary attribute for access if needed
            result = {
                'explanation': explanation,
                'plot': input_obj
            }
            # Attach to function for access if user really needs it
            explain._last_result = result
            return None
        else:
            return {
                'explanation': explanation,
                'plot': input_obj
            }
    else:
        # Just return the explanation (original behavior)
        if display_explanation and explanation is not None:
            from IPython.display import display, Markdown
            display(Markdown("---"))
            display(Markdown("## 🤖 Chart Explanation"))
            display(Markdown(explanation))
            display(Markdown("---"))
        
        return explanation


def auto_explain(fig, category=None, plot_name=None):
    """
    Automatically explain a chart after it's created.
    This is a convenience function that can be called after
    generating any plot to get an AI explanation.
    
    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        The Plotly figure to explain
    category : str, optional
        Category for caching (e.g., "signal_evaluation")
    plot_name : str, optional
        Plot name for caching (e.g., "performance_metrics")
        
    Returns:
    --------
    plotly.graph_objects.Figure : The same figure (for chaining)
    """
    from ..extensions.chart_explainer import explain_chart
    explain_chart(fig, display_explanation=True, category=category, plot_name=plot_name)
    return fig


def explain_overall(category, display_explanation=True, force_refresh=False):
    """
    Generate a comprehensive explanation for an entire category of analyses.
    
    Parameters:
    -----------
    category : str
        The category to explain (e.g., "signal_evaluation")
    display_explanation : bool
        Whether to display the explanation immediately
    force_refresh : bool
        Whether to regenerate the explanation even if cached
        
    Returns:
    --------
    str or None : The comprehensive explanation markdown, or None if failed
    """
    from ..extensions.overall_explainers import explain_overall as _explain_overall
    return _explain_overall(category=category, display_explanation=display_explanation, force_refresh=force_refresh)


def explain_signal_evaluation(display_explanation=True):
    """
    Convenience function to generate overall explanation for signal_evaluation.
    
    Parameters:
    -----------
    display_explanation : bool
        Whether to display the explanation immediately
        
    Returns:
    --------
    str or None : The comprehensive explanation markdown, or None if failed
    """
    from ..extensions.overall_explainers import explain_signal_evaluation as _explain_signal_evaluation
    return _explain_signal_evaluation(display_explanation=display_explanation)


def list_available_categories():
    """
    List all categories that have cached data.
    
    Returns:
    --------
    list : List of available categories
    """
    from ..extensions.overall_explainers import list_available_categories as _list_available_categories
    return _list_available_categories()


def list_category_plots(category):
    """
    List all plots available for a specific category.
    
    Parameters:
    -----------
    category : str
        The category to list plots for
        
    Returns:
    --------
    list : List of plot names
    """
    from ..extensions.overall_explainers import list_category_plots as _list_category_plots
    return _list_category_plots(category)


def get_category_summary(category):
    """
    Get a summary of all cached data and explanations for a category.
    
    Parameters:
    -----------
    category : str
        The category to summarize
        
    Returns:
    --------
    dict : Summary of cached data and explanations
    """
    from ..extensions.overall_explainers import get_category_summary as _get_category_summary
    return _get_category_summary(category)


def explain_performance_table(evaluator, display_explanation=True, cache_data=True):
    """
    Explain the performance table from a SignalEvaluator.
    
    Parameters:
    -----------
    evaluator : SignalEvaluator
        The SignalEvaluator instance with performance_table
    display_explanation : bool
        Whether to display the explanation immediately
    cache_data : bool
        Whether to cache the table data and explanation
        
    Returns:
    --------
    str or None : The explanation markdown, or None if failed
    """
    from ..extensions.table_explainer import explain_performance_table as _explain_performance_table
    return _explain_performance_table(
        evaluator, 
        display_explanation=display_explanation, 
        cache_data=cache_data
    )


def explain_drawdown_table(evaluator, display_explanation=True, cache_data=True):
    """
    Explain the drawdown table from a SignalEvaluator.
    
    Parameters:
    -----------
    evaluator : SignalEvaluator
        The SignalEvaluator instance with drawdown_table
    display_explanation : bool
        Whether to display the explanation immediately
    cache_data : bool
        Whether to cache the table data and explanation
        
    Returns:
    --------
    str or None : The explanation markdown, or None if failed
    """
    from ..extensions.table_explainer import explain_drawdown_table as _explain_drawdown_table
    return _explain_drawdown_table(
        evaluator, 
        display_explanation=display_explanation, 
        cache_data=cache_data
    )


def explain_table_data(table_data, title, description=None, table_type="general", display_explanation=True, cache_data=True):
    """
    Explain any pandas DataFrame table with LLM analysis.
    
    Parameters:
    -----------
    table_data : pd.DataFrame
        The table data to explain
    title : str
        Table title
    description : str, optional
        Table description
    table_type : str
        Type of table (e.g., "performance_stats", "drawdown_analysis")
    display_explanation : bool
        Whether to display the explanation immediately
    cache_data : bool
        Whether to cache the table data and explanation
        
    Returns:
    --------
    str or None : The explanation markdown, or None if failed
    """
    from ..extensions.table_explainer import explain_table as _explain_table
    return _explain_table(
        table_data=table_data,
        title=title,
        description=description,
        table_type=table_type,
        display_explanation=display_explanation,
        cache_data=cache_data
    )


def get_cached_table_explanations(category=None, plot_name=None):
    """
    Retrieve cached table explanations.
    
    Parameters:
    -----------
    category : str, optional
        Filter by category
    plot_name : str, optional
        Filter by plot name
        
    Returns:
    --------
    dict : Cached table explanations
    """
    from ..extensions.table_explainer import get_cached_table_explanations as _get_cached_table_explanations
    return _get_cached_table_explanations(category=category, plot_name=plot_name)


def list_available_table_categories():
    """
    List all categories that have cached table explanations.
    
    Returns:
    --------
    list : List of available categories
    """
    from ..extensions.table_explainer import list_available_table_categories as _list_available_table_categories
    return _list_available_table_categories()
