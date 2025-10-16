"""
Overall Explainers Module

This module provides functionality to generate comprehensive explanations
across multiple charts and analyses within a category. It leverages the
hierarchical caching system from chart_explainer to aggregate data and
explanations for holistic insights. Now includes support for table explanations.
"""

import json
from typing import Dict, Any, Optional, List
from IPython.display import display, Markdown
from .chart_explainer import (
    get_cached_data, 
    list_cached_categories, 
    list_cached_plots,
    get_ephemeral_token,
    _run_async_in_sync
)
import requests
from google import genai
from google.genai import types


async def generate_overall_explanation_async(
    category: str,
    cached_data: Dict[str, Any],
    ephemeral_token: str
) -> str:
    """
    Generate an overall explanation using Gemini AI.
    
    Parameters:
    -----------
    category : str
        The category to explain (e.g., "signal_evaluation")
    cached_data : dict
        Hierarchical cached data and explanations
    ephemeral_token : str
        Ephemeral token for Gemini API
        
    Returns:
    --------
    str : Comprehensive overall explanation
    """
    try:
        # Create client with ephemeral token
        client = genai.Client(
            api_key=ephemeral_token,
            http_options=types.HttpOptions(api_version="v1alpha")
        )
        
        model = "gemini-2.5-flash"
        config = {"response_modalities": ["TEXT"]}
        
        # Count charts and tables
        data_items = cached_data.get('data', {}).get(category, {})
        chart_count = len([item for item in data_items.values() if 'x_axis' in item.get('chart_card', {})])
        table_count = len(data_items) - chart_count
        
        # Build comprehensive summary
        prompt = f"""You are a senior financial analyst providing a comprehensive analysis of the {category} results.

## OVERALL ANALYSIS SUMMARY

**Category:** {category}
**Total Visualizations:** {len(data_items)} ({chart_count} charts, {table_count} tables)

### Individual Analyses (Charts and Tables):

**IMPORTANT**: Tables contain PRIMARY QUANTITATIVE DATA. Pay attention to table metrics (Sharpe ratios, returns, drawdowns, etc.) and integrate them thoroughly into your analysis. Tables are NOT secondary to charts - they provide the concrete numbers that validate visual patterns.
"""
        
        # Add data for each plot/table
        for plot_name, plot_data in cached_data.get('data', {}).get(category, {}).items():
            chart_card = plot_data.get('chart_card', {})
            key_stats = chart_card.get('key_statistics', {})
            title = chart_card.get('title', plot_name)
            
            # Determine if this is a chart or table
            is_table = 'table_type' in chart_card or 'rows' in chart_card
            
            if is_table:
                prompt += f"""

#### {title.replace('_', ' ').title()} 📊 (TABLE - PRIMARY DATA SOURCE)

**Table Structure:**
- Rows: {chart_card.get('rows', 'N/A')}
- Columns: {chart_card.get('columns', 'N/A')}
- Table Type: {chart_card.get('table_type', 'N/A')}
- Column Names: {', '.join(chart_card.get('column_names', [])[:15])}{'...' if len(chart_card.get('column_names', [])) > 15 else ''}

**ALL KEY METRICS (Critical for Analysis):**"""
                # Show ALL statistics for tables since they're the core quantitative data
                for stat_name, stat_value in key_stats.items():
                    prompt += f"\n- **{stat_name}**: {stat_value}"
                
                # Add sample data if available
                sample_data = chart_card.get('sample_data')
                if sample_data:
                    prompt += f"\n\n**Sample Data (First Few Rows):**\n```\n{sample_data}\n```"
                
            else:
                prompt += f"""

#### {title.replace('_', ' ').title()} (Chart)

**Chart Details:**
- X-axis: {chart_card.get('x_axis', 'N/A')}
- Y-axis: {chart_card.get('y_axis', 'N/A')}
- Series Count: {chart_card.get('series_count', 'N/A')}

**Key Statistics:**"""
                # Limit chart stats to first 10 to keep prompt manageable
                for stat_name, stat_value in list(key_stats.items())[:10]:
                    prompt += f"\n- {stat_name}: {stat_value}"
            
            # Add explanation if available
            explanation_data = cached_data.get('explanations', {}).get(category, {}).get(plot_name)
            if explanation_data:
                explanation = explanation_data.get('explanation', '')
                if is_table:
                    # Emphasize table explanations more prominently
                    prompt += f"\n\n**📋 DETAILED TABLE ANALYSIS:**\n{explanation}\n"
                else:
                    prompt += f"\n\n**Previous Chart Analysis:** {explanation}\n"
        
        prompt += f"""

## TASK: Comprehensive Overall Analysis

Based on all the individual chart data and table metrics above, provide a comprehensive overall analysis that includes:

1. **Executive Summary**: A high-level overview of what the {category} analysis reveals
2. **Key Insights**: The most important findings across all metrics, charts, AND TABLES. Specifically integrate the quantitative metrics from tables (e.g., Sharpe ratios, returns, drawdowns, profit factors) into your insights.
3. **Patterns and Trends**: Cross-reference patterns between charts and table data. For example, if a chart shows visual patterns, validate with specific numbers from the tables.
4. **Performance Assessment**: Overall evaluation of the {category} performance using BOTH visual patterns AND specific metrics from tables
5. **Actionable Recommendations**: Specific insights based on the concrete numbers in the tables combined with visual trends
6. **Data Quality Notes**: Any observations about data completeness or reliability

**CRITICAL INSTRUCTIONS:**
- Give EQUAL WEIGHT to table data and chart visualizations
- Always cite specific metrics from tables (e.g., "with a Sharpe Ratio of 0.95")
- Cross-reference table numbers with chart patterns (e.g., "The table shows X metric at Y value, which aligns with the visual pattern in Chart Z")
- Do NOT treat tables as secondary information sources - they contain the primary quantitative evidence

Write in a professional, analytical tone suitable for financial stakeholders. Use markdown formatting with appropriate headers, bullet points, and emphasis. Aim for 4-6 comprehensive paragraphs that synthesize all the individual analyses into a coherent whole.
"""

        async with client.aio.live.connect(model=model, config=config) as session:
            await session.send(input=prompt, end_of_turn=True)
            
            explanation = ""
            async for response in session.receive():
                if response.text:
                    explanation += response.text
            
            return explanation
            
    except Exception as e:
        return f"**Error generating overall explanation:** {str(e)}"


def explain_overall(
    category: str,
    display_explanation: bool = True,
    force_refresh: bool = False
) -> Optional[str]:
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
    # Get cached data for the category
    cached_data = get_cached_data(category=category)
    
    if not cached_data.get('data', {}).get(category):
        if display_explanation:
            display(Markdown(f"⚠️ **No cached data found for category '{category}'.**"))
        return None
    
    # Check if we have any explanations
    if not cached_data.get('explanations', {}).get(category):
        if display_explanation:
            display(Markdown(f"⚠️ **No cached explanations found for category '{category}'.**"))
            display(Markdown("Please generate individual chart explanations first using `sov.explain()`"))
        return None
    
    # Get ephemeral token
    ephemeral_token = get_ephemeral_token()
    
    if not ephemeral_token:
        if display_explanation:
            display(Markdown("❌ **Failed to get ephemeral token. Cannot generate explanation.**"))
        return None
    
    # Generate overall explanation
    try:
        # Run async function in sync context
        explanation = _run_async_in_sync(generate_overall_explanation_async(
            category=category,
            cached_data=cached_data,
            ephemeral_token=ephemeral_token
        ))
        
        if display_explanation:
            display(Markdown("---"))
            display(Markdown(f"## 🎯 Overall Analysis: {category.replace('_', ' ').title()}"))
            display(Markdown(explanation))
            display(Markdown("---"))
        
        return explanation
        
    except Exception as e:
        error_msg = f"❌ **Error generating overall explanation:** {str(e)}"
        if display_explanation:
            display(Markdown(error_msg))
        return None


def explain_signal_evaluation(display_explanation: bool = True) -> Optional[str]:
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
    return explain_overall("signal_evaluation", display_explanation=display_explanation)


def get_category_summary(category: str) -> Dict[str, Any]:
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
    cached_data = get_cached_data(category=category)
    
    summary = {
        "category": category,
        "total_plots": len(cached_data.get('data', {}).get(category, {})),
        "plots_with_explanations": len(cached_data.get('explanations', {}).get(category, {})),
        "plots": []
    }
    
    # Add details for each plot
    for plot_name in cached_data.get('data', {}).get(category, {}):
        plot_summary = {
            "name": plot_name,
            "has_data": True,
            "has_explanation": plot_name in cached_data.get('explanations', {}).get(category, {}),
            "title": None,
            "last_updated": None
        }
        
        # Get title and timestamp from data
        plot_data = cached_data['data'][category].get(plot_name, {})
        chart_card = plot_data.get('chart_card', {})
        plot_summary["title"] = chart_card.get('title', plot_name)
        plot_summary["last_updated"] = plot_data.get('timestamp')
        
        summary["plots"].append(plot_summary)
    
    return summary


def list_available_categories() -> List[str]:
    """
    List all categories that have cached data.
    
    Returns:
    --------
    list : List of available categories
    """
    return list_cached_categories()


def list_category_plots(category: str) -> List[str]:
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
    return list_cached_plots(category)


def cache_overall_explanation(category: str, explanation: str) -> None:
    """
    Cache an overall explanation for a category.
    
    Parameters:
    -----------
    category : str
        The category name
    explanation : str
        The overall explanation to cache
    """
    from .chart_explainer import cache_explanation
    cache_explanation(category, "overall_analysis", explanation)


def get_cached_overall_explanation(category: str) -> Optional[str]:
    """
    Get a cached overall explanation for a category.
    
    Parameters:
    -----------
    category : str
        The category name
        
    Returns:
    --------
    str or None : The cached explanation, or None if not found
    """
    cached_data = get_cached_data(category=category, plot_name="overall_analysis")
    explanations = cached_data.get('explanations', {}).get(category, {}).get('overall_analysis')
    
    if explanations:
        return explanations.get('explanation')
    return None
