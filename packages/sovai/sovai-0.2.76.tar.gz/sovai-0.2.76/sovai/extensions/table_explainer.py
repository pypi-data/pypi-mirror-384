"""
Table Explanation Module using Gemini via Ephemeral Token Broker

This module provides functionality to automatically explain table data
using Google's Gemini model through a secure ephemeral token broker.
It integrates with the existing chart explanation caching system.
"""

import requests
import asyncio
import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from IPython.display import display, Markdown
from google import genai
from google.genai import types

# Import existing caching functions from chart_explainer
from .chart_explainer import (
    get_ephemeral_token,
    _run_async_in_sync,
    cache_chart_data,
    cache_explanation,
    get_cached_data
)


def _generate_table_metadata(
    table_data: pd.DataFrame,
    title: str,
    description: Optional[str] = None,
    table_type: str = "general"
) -> Dict[str, Any]:
    """
    Generate metadata for a table similar to chart cards for figures.
    
    Parameters:
    -----------
    table_data : pd.DataFrame
        The table data to analyze
    title : str
        Table title
    description : str, optional
        Table description
    table_type : str
        Type of table (e.g., "performance_stats", "drawdown_analysis")
        
    Returns:
    --------
    dict : Table metadata card
    """
    # Basic table info
    metadata = {
        'title': title,
        'table_type': table_type,
        'description': description or f"Table with {len(table_data)} rows and {len(table_data.columns)} columns",
        'rows': len(table_data),
        'columns': len(table_data),
        'column_names': list(table_data.columns),
    }
    
    # Data type analysis
    numeric_columns = table_data.select_dtypes(include=['number']).columns.tolist()
    text_columns = table_data.select_dtypes(include=['object']).columns.tolist()
    
    metadata['numeric_columns'] = numeric_columns
    metadata['text_columns'] = text_columns
    
    # Key statistics for numeric columns
    key_stats = {}
    for col in numeric_columns[:10]:  # Limit to first 10 numeric columns
        try:
            series = pd.to_numeric(table_data[col], errors='coerce').dropna()
            if len(series) > 0:
                key_stats[f"{col}_mean"] = f"{series.mean():.4f}"
                key_stats[f"{col}_std"] = f"{series.std():.4f}"
                key_stats[f"{col}_min"] = f"{series.min():.4f}"
                key_stats[f"{col}_max"] = f"{series.max():.4f}"
        except:
            pass
    
    # Add summary statistics for the table
    try:
        metadata['total_cells'] = len(table_data) * len(table_data.columns)
        metadata['null_cells'] = table_data.isnull().sum().sum()
        metadata['null_percentage'] = f"{(metadata['null_cells'] / metadata['total_cells'] * 100):.2f}%"
    except:
        metadata['total_cells'] = 0
        metadata['null_cells'] = 0
        metadata['null_percentage'] = "0%"
    
    if key_stats:
        metadata['key_statistics'] = key_stats
    
    return metadata


def _extract_table_summary(table_data: pd.DataFrame, max_rows: int = 10) -> str:
    """
    Extract a readable summary of the table data for LLM analysis.
    
    Parameters:
    -----------
    table_data : pd.DataFrame
        The table data
    max_rows : int
        Maximum number of rows to include in summary
        
    Returns:
    --------
    str : Formatted table summary
    """
    if table_data.empty:
        return "Empty table"
    
    # Get column names and types
    col_info = []
    for col in table_data.columns:
        dtype = str(table_data[col].dtype)
        sample_vals = table_data[col].dropna().head(3).tolist()
        sample_str = ", ".join([str(v) for v in sample_vals])
        col_info.append(f"{col} ({dtype}): {sample_str}")
    
    summary = f"Columns: {'; '.join(col_info)}\n\n"
    
    # Add sample data
    sample_data = table_data.head(max_rows).to_string(index=False)
    summary += f"Sample data (first {min(max_rows, len(table_data))} rows):\n{sample_data}"
    
    return summary


async def explain_table_async(
    table_data: pd.DataFrame,
    table_metadata: Dict[str, Any],
    ephemeral_token: str
) -> str:
    """
    Use Gemini to explain the table using metadata.
    
    Parameters:
    -----------
    table_data : pd.DataFrame
        The table data to explain
    table_metadata : dict
        Table metadata including title, description, and key stats
    ephemeral_token : str
        Ephemeral token for Gemini API
        
    Returns:
    --------
    str : Markdown explanation of the table
    """
    try:
        # Create client with ephemeral token
        client = genai.Client(
            api_key=ephemeral_token,
            http_options=types.HttpOptions(api_version="v1alpha")
        )
        
        model = "gemini-2.5-flash"
        config = {"response_modalities": ["TEXT"]}
        
        # Extract table summary
        table_summary = _extract_table_summary(table_data)
        
        # Construct prompt with comprehensive metadata
        prompt = f"""You are a financial data analyst. Explain this table in clear, concise language.

**Table Title:** {table_metadata.get('title', 'Untitled Table')}

**Description:** {table_metadata.get('description', 'No description available')}

**Table Details:**
- Rows: {table_metadata.get('rows', 'N/A')}
- Columns: {table_metadata.get('columns', 'N/A')}
- Table Type: {table_metadata.get('table_type', 'general')}"""

        # Add column information
        numeric_cols = table_metadata.get('numeric_columns', [])
        text_cols = table_metadata.get('text_columns', [])
        if numeric_cols:
            prompt += f"\n- Numeric Columns: {', '.join(numeric_cols[:10])}"
        if text_cols:
            prompt += f"\n- Text Columns: {', '.join(text_cols[:10])}"

        # Add data quality info
        null_pct = table_metadata.get('null_percentage', '0%')
        prompt += f"\n- Data Completeness: {100 - float(null_pct.rstrip('%')):.1f}% complete ({null_pct} null values)"

        prompt += f"""

**Key Statistics:"""
        key_stats = table_metadata.get('key_statistics', {})
        for stat_name, stat_value in list(key_stats.items())[:15]:  # Limit to first 15 stats
            prompt += f"\n- {stat_name}: {stat_value}"

        prompt += f"""

**Table Data Summary:**
{table_summary}

Provide a 2-3 paragraph explanation that:
1. Summarizes what the table shows and its purpose
2. Highlights the most important insights from the key statistics
3. Explains what patterns or trends are visible in the data
4. Provides context for interpreting the results

Write in markdown format with appropriate formatting. Focus on actionable insights and what the data means for financial analysis or decision-making."""

        async with client.aio.live.connect(model=model, config=config) as session:
            await session.send(input=prompt, end_of_turn=True)
            
            explanation = ""
            async for response in session.receive():
                if response.text:
                    explanation += response.text
            
            return explanation
            
    except Exception as e:
        return f"**Error generating table explanation:** {str(e)}"


def explain_table(
    table_data: pd.DataFrame,
    title: str,
    description: Optional[str] = None,
    table_type: str = "general",
    display_explanation: bool = True,
    category: str = None,
    plot_name: str = None,
    cache_data: bool = True
) -> Optional[str]:
    """
    Generate an explanation for a table with LLM analysis.
    
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
    category : str, optional
        Category for caching (e.g., "signal_evaluation")
    plot_name : str, optional
        Plot name for caching (e.g., "performance_metrics")
    cache_data : bool
        Whether to cache the table data and explanation
        
    Returns:
    --------
    str or None : The explanation markdown, or None if failed
    """
    if table_data.empty:
        if display_explanation:
            display(Markdown("⚠️ **Table is empty. Cannot generate explanation.**"))
        return None
    
    # Auto-generate category and plot_name from title if not provided
    if category is None or plot_name is None:
        if category is None:
            # Try to detect category from title or table_type
            title_lower = title.lower()
            # All tables from signal_evaluation.py should be under signal_evaluation category
            if any(term in title_lower for term in ['performance', 'statistics', 'stats', 'sharpe', 'returns', 'drawdown', 'risk', 'pnl', 'profit', 'loss']):
                category = "signal_evaluation"
            elif any(term in title_lower for term in ['turnover', 'holding']):
                category = "portfolio_analysis"
            else:
                category = "general"
        
        if plot_name is None:
            # Use title as plot name, sanitize it
            plot_name = title.lower().replace(" ", "_").replace("/", "_").replace("\\", "_").replace("(", "").replace(")", "").replace(",", "")
    
    # Generate table metadata
    table_metadata = _generate_table_metadata(table_data, title, description, table_type)
    
    # Create a chart-like card for caching compatibility
    chart_card = {
        'title': title,
        'table_type': table_type,
        'description': description or table_metadata['description'],
        'key_statistics': table_metadata.get('key_statistics', {}),
        'rows': table_metadata['rows'],
        'columns': table_metadata['columns'],
        'column_names': table_metadata['column_names'],
    }
    
    # Cache the table data if requested
    if cache_data:
        cache_chart_data(category, plot_name, chart_card)
    
    # Get ephemeral token
    ephemeral_token = get_ephemeral_token()
    
    if not ephemeral_token:
        if display_explanation:
            display(Markdown("❌ **Failed to get ephemeral token. Cannot generate explanation.**"))
        return None
    
    # Generate explanation
    try:
        # Run async function in sync context
        explanation = _run_async_in_sync(explain_table_async(
            table_data=table_data,
            table_metadata=table_metadata,
            ephemeral_token=ephemeral_token
        ))
        
        # Cache the explanation if requested
        if cache_data:
            cache_explanation(category, plot_name, explanation)
        
        if display_explanation:
            display(Markdown("---"))
            display(Markdown("## 📊 Table Explanation"))
            display(Markdown(explanation))
            display(Markdown("---"))
        
        return explanation
        
    except Exception as e:
        error_msg = f"❌ **Error generating table explanation:** {str(e)}"
        if display_explanation:
            display(Markdown(error_msg))
        return None


def explain_performance_table(
    evaluator,
    display_explanation: bool = True,
    cache_data: bool = True
) -> Optional[str]:
    """
    Convenience function to explain the performance table from a SignalEvaluator.
    
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
    try:
        # Get the performance table data
        # Note: The statistics() function displays tables directly, so we need to extract the data
        # We'll reconstruct the data from the evaluator's internal state
        
        # Calculate the stats data (similar to statistics() function but return DataFrames)
        from .signal_evaluation import calculate_stats, preprocess_stats
        
        all_trades_stats = preprocess_stats(calculate_stats(evaluator.resampled_returns, evaluator.holdings[evaluator.rebalance_mask]))
        short_trades_stats = preprocess_stats(
            calculate_stats(evaluator.resampled_returns, evaluator.holdings[evaluator.rebalance_mask].where(evaluator.holdings[evaluator.rebalance_mask] < 0, 0))
        )
        long_trades_stats = preprocess_stats(
            calculate_stats(evaluator.resampled_returns, evaluator.holdings[evaluator.rebalance_mask].where(evaluator.holdings[evaluator.rebalance_mask] > 0, 0))
        )
        
        # Create summary stats DataFrame
        summary_stats = pd.DataFrame(
            {
                "All trades": all_trades_stats,
                "Short trades": short_trades_stats,
                "Long trades": long_trades_stats,
            },
            index=[
                "Total number of round_trips",
                "Percent profitable",
                "Winning round_trips",
                "Losing round_trips",
            ],
        )
        
        # Create PnL stats DataFrame
        pnl_stats = pd.DataFrame(
            {
                "All trades": all_trades_stats,
                "Short trades": short_trades_stats,
                "Long trades": long_trades_stats,
            },
            index=[
                "Total profit",
                "Gross profit",
                "Gross loss",
                "Profit factor",
                "Avg. trade net profit",
                "Avg. winning trade",
                "Avg. losing trade",
                "Ratio Avg. Win:Avg. Loss",
                "Largest winning trade",
                "Largest losing trade",
            ],
        )
        
        # Combine both tables into one comprehensive table
        combined_stats = pd.concat([summary_stats, pnl_stats])
        
        return explain_table(
            table_data=combined_stats,
            title="Performance Statistics Summary",
            description="Comprehensive performance metrics including trade statistics and profit/loss analysis for all trades, short trades, and long trades.",
            table_type="performance_stats",
            display_explanation=display_explanation,
            category="signal_evaluation",
            plot_name="performance_table",
            cache_data=cache_data
        )
        
    except Exception as e:
        error_msg = f"❌ **Error explaining performance table:** {str(e)}"
        if display_explanation:
            display(Markdown(error_msg))
        return None


def explain_drawdown_table(
    evaluator,
    display_explanation: bool = True,
    cache_data: bool = True
) -> Optional[str]:
    """
    Convenience function to explain the drawdown table from a SignalEvaluator.
    
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
    try:
        # Get portfolio returns for drawdown analysis
        portfolio_returns = evaluator.position_returns.mean(axis=1)
        
        # Extract drawdown data (similar to draw_down_statistics function)
        from .signal_evaluation import calculate_metrics, find_drawdown_periods, create_basic_info_table, create_drawdown_table
        
        # Preprocess returns
        portfolio_returns.index = pd.to_datetime(portfolio_returns.index)
        portfolio_returns = portfolio_returns.sort_index()
        
        # Find first valid index
        valid_mask = (portfolio_returns.notna()) & (portfolio_returns.abs() > 1e-10)
        if valid_mask.any():
            first_valid_idx = portfolio_returns.index[valid_mask.argmax()]
            portfolio_returns = portfolio_returns.loc[first_valid_idx:]
        
        start_date = portfolio_returns.index[0]
        while start_date.weekday() != 4:
            start_date += pd.Timedelta(days=1)
        
        end_date = portfolio_returns.index[-1]
        while end_date.weekday() != 4:
            end_date -= pd.Timedelta(days=1)
        
        out_of_sample_start = "2022-01-07"
        
        in_sample_returns = portfolio_returns[start_date:out_of_sample_start]
        out_of_sample_returns = portfolio_returns[out_of_sample_start:end_date]
        all_returns = portfolio_returns[start_date:end_date]
        
        # Create metrics table
        metrics_df = pd.DataFrame(
            {
                "In-sample": calculate_metrics(in_sample_returns),
                "Out-of-sample": calculate_metrics(out_of_sample_returns),
                "All": calculate_metrics(all_returns),
            }
        )
        
        metrics_df = metrics_df.apply(lambda x: x.map("{:.3f}".format))
        metrics_df.loc["Gross leverage"] = "1.000"
        
        # Create drawdown periods table
        worst_drawdowns = find_drawdown_periods(all_returns)
        drawdown_table = create_drawdown_table(worst_drawdowns)
        
        # Create basic info table
        basic_info = create_basic_info_table(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            out_of_sample_start,
        )
        
        # Combine all tables
        combined_table = pd.concat([
            basic_info.set_index('Start date' if 'Start date' in basic_info.columns else basic_info.columns[0]),
            drawdown_table.set_index('Net drawdown in %' if 'Net drawdown in %' in drawdown_table.columns else drawdown_table.columns[1]),
            metrics_df
        ])
        
        return explain_table(
            table_data=combined_table,
            title="Drawdown Analysis Summary",
            description="Comprehensive drawdown analysis including basic information, worst drawdown periods, and performance metrics across in-sample, out-of-sample, and full periods.",
            table_type="drawdown_analysis",
            display_explanation=display_explanation,
            category="signal_evaluation",
            plot_name="drawdown_table",
            cache_data=cache_data
        )
        
    except Exception as e:
        error_msg = f"❌ **Error explaining drawdown table:** {str(e)}"
        if display_explanation:
            display(Markdown(error_msg))
        return None


def get_cached_table_explanations(category: str = None, plot_name: str = None) -> Dict[str, Any]:
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
    return get_cached_data(category, plot_name)


def list_available_table_categories() -> List[str]:
    """
    List all categories that have cached table explanations.
    
    Returns:
    --------
    list : List of available categories
    """
    cached_data = get_cached_data()
    categories = []
    
    for category in cached_data.get('explanations', {}):
        for plot_name in cached_data['explanations'][category]:
            # Check if this is a table explanation (table_type in metadata)
            explanation_data = cached_data['explanations'][category][plot_name]
            if 'table' in plot_name.lower() or 'stats' in plot_name.lower():
                if category not in categories:
                    categories.append(category)
    
    return categories
