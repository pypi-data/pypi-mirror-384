"""
Chart Explanation Module using Gemini via Ephemeral Token Broker

This module provides functionality to automatically explain chart metadata
using Google's Gemini model through a secure ephemeral token broker.
"""

import requests
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from IPython.display import display, Markdown
from google import genai
from google.genai import types

# Configuration
BROKER_URL = "https://gemini-ephemeral-broker-y7o724zyfq-uc.a.run.app"
SOVAI_TOKEN = "22fd808d-0947-45f1-995a-82346b921f0f"

# Caching configuration
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "explanations")
DATA_CACHE_DIR = os.path.join(CACHE_DIR, "data")
EXPLANATION_CACHE_DIR = os.path.join(CACHE_DIR, "explanations")


def _ensure_cache_dirs():
    """Ensure cache directories exist."""
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    os.makedirs(EXPLANATION_CACHE_DIR, exist_ok=True)


def _get_cache_path(category: str, plot_name: str, data_type: str = "data") -> str:
    """
    Get the cache path for a given category, plot name, and data type.
    
    Parameters:
    -----------
    category : str
        The category (e.g., "signal_evaluation")
    plot_name : str
        The name of the specific plot/analysis
    data_type : str
        Either "data" or "explanations"
        
    Returns:
    --------
    str : Full path to the cache file
    """
    if data_type == "data":
        base_dir = DATA_CACHE_DIR
    else:
        base_dir = EXPLANATION_CACHE_DIR
    
    category_dir = os.path.join(base_dir, category)
    os.makedirs(category_dir, exist_ok=True)
    
    return os.path.join(category_dir, f"{plot_name}.json")


def cache_chart_data(category: str, plot_name: str, chart_card: Dict[str, Any]) -> None:
    """
    Cache chart data hierarchically.
    
    Parameters:
    -----------
    category : str
        The category (e.g., "signal_evaluation")
    plot_name : str
        The name of the specific plot/analysis
    chart_card : dict
        Chart metadata and statistics
    """
    _ensure_cache_dirs()
    cache_path = _get_cache_path(category, plot_name, "data")
    
    cache_data = {
        "category": category,
        "plot_name": plot_name,
        "timestamp": datetime.now().isoformat(),
        "chart_card": chart_card
    }
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error caching chart data: {e}")


def cache_explanation(category: str, plot_name: str, explanation: str) -> None:
    """
    Cache explanation hierarchically.
    
    Parameters:
    -----------
    category : str
        The category (e.g., "signal_evaluation")
    plot_name : str
        The name of the specific plot/analysis
    explanation : str
        The generated explanation
    """
    _ensure_cache_dirs()
    cache_path = _get_cache_path(category, plot_name, "explanations")
    
    cache_data = {
        "category": category,
        "plot_name": plot_name,
        "timestamp": datetime.now().isoformat(),
        "explanation": explanation
    }
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error caching explanation: {e}")


def get_cached_data(category: str = None, plot_name: str = None) -> Dict[str, Any]:
    """
    Retrieve cached data and explanations.
    
    Parameters:
    -----------
    category : str, optional
        Filter by category. If None, returns all categories
    plot_name : str, optional
        Filter by plot name. If None, returns all plots in category
        
    Returns:
    --------
    dict : Hierarchical dictionary of cached data and explanations
    """
    _ensure_cache_dirs()
    result = {"data": {}, "explanations": {}}
    
    # Get data
    if category is None:
        # Get all categories
        if os.path.exists(DATA_CACHE_DIR):
            for cat in os.listdir(DATA_CACHE_DIR):
                cat_dir = os.path.join(DATA_CACHE_DIR, cat)
                if os.path.isdir(cat_dir):
                    result["data"][cat] = {}
                    for plot_file in os.listdir(cat_dir):
                        if plot_file.endswith('.json'):
                            plot_name_key = plot_file[:-5]  # Remove .json
                            try:
                                with open(os.path.join(cat_dir, plot_file), 'r') as f:
                                    cached = json.load(f)
                                    result["data"][cat][plot_name_key] = cached
                            except Exception as e:
                                print(f"Error reading cached data {plot_file}: {e}")
    else:
        # Get specific category
        cat_dir = os.path.join(DATA_CACHE_DIR, category)
        if os.path.exists(cat_dir):
            result["data"][category] = {}
            for plot_file in os.listdir(cat_dir):
                if plot_file.endswith('.json'):
                    plot_name_key = plot_file[:-5]  # Remove .json
                    try:
                        with open(os.path.join(cat_dir, plot_file), 'r') as f:
                            cached = json.load(f)
                            if plot_name is None or cached["plot_name"] == plot_name_key:
                                result["data"][category][plot_name_key] = cached
                    except Exception as e:
                        print(f"Error reading cached data {plot_file}: {e}")
    
    # Get explanations
    if category is None:
        # Get all categories
        if os.path.exists(EXPLANATION_CACHE_DIR):
            for cat in os.listdir(EXPLANATION_CACHE_DIR):
                cat_dir = os.path.join(EXPLANATION_CACHE_DIR, cat)
                if os.path.isdir(cat_dir):
                    result["explanations"][cat] = {}
                    for plot_file in os.listdir(cat_dir):
                        if plot_file.endswith('.json'):
                            plot_name_key = plot_file[:-5]  # Remove .json
                            try:
                                with open(os.path.join(cat_dir, plot_file), 'r') as f:
                                    cached = json.load(f)
                                    result["explanations"][cat][plot_name_key] = cached
                            except Exception as e:
                                print(f"Error reading cached explanation {plot_file}: {e}")
    else:
        # Get specific category
        cat_dir = os.path.join(EXPLANATION_CACHE_DIR, category)
        if os.path.exists(cat_dir):
            result["explanations"][category] = {}
            for plot_file in os.listdir(cat_dir):
                if plot_file.endswith('.json'):
                    plot_name_key = plot_file[:-5]  # Remove .json
                    try:
                        with open(os.path.join(cat_dir, plot_file), 'r') as f:
                            cached = json.load(f)
                            if plot_name is None or cached["plot_name"] == plot_name_key:
                                result["explanations"][category][plot_name_key] = cached
                    except Exception as e:
                        print(f"Error reading cached explanation {plot_file}: {e}")
    
    return result


def list_cached_categories() -> list:
    """
    List all available categories in the cache.
    
    Returns:
    --------
    list : List of category names
    """
    _ensure_cache_dirs()
    categories = set()
    
    for cache_type in [DATA_CACHE_DIR, EXPLANATION_CACHE_DIR]:
        if os.path.exists(cache_type):
            categories.update(os.listdir(cache_type))
    
    return sorted(list(categories))


def list_cached_plots(category: str) -> list:
    """
    List all available plots for a given category.
    
    Parameters:
    -----------
    category : str
        The category to list plots for
        
    Returns:
    --------
    list : List of plot names
    """
    _ensure_cache_dirs()
    plots = set()
    
    for cache_type in [DATA_CACHE_DIR, EXPLANATION_CACHE_DIR]:
        cat_dir = os.path.join(cache_type, category)
        if os.path.exists(cat_dir):
            for plot_file in os.listdir(cat_dir):
                if plot_file.endswith('.json'):
                    plots.add(plot_file[:-5])  # Remove .json
    
    return sorted(list(plots))


def get_ephemeral_token(sovai_token: str = SOVAI_TOKEN, broker_url: str = BROKER_URL) -> Optional[str]:
    """
    Get ephemeral token from the broker using Sovai key.
    
    Parameters:
    -----------
    sovai_token : str
        The Sovai authentication token
    broker_url : str
        The broker endpoint URL
        
    Returns:
    --------
    str or None : Ephemeral token if successful, None otherwise
    """
    headers = {
        "X-User-Token": sovai_token
    }
    
    try:
        response = requests.get(
            f"{broker_url}/token",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['token']
        else:
            print(f"Failed to get ephemeral token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error getting ephemeral token: {e}")
        return None


async def explain_chart_async(
    chart_card: Dict[str, Any],
    key_stats: Dict[str, Any],
    description: str,
    ephemeral_token: str
) -> str:
    """
    Use Gemini to explain the chart using metadata.
    
    Parameters:
    -----------
    chart_card : dict
        Chart metadata including title, axes, series info
    key_stats : dict
        Key statistics from the chart
    description : str
        Chart description
    ephemeral_token : str
        Ephemeral token for Gemini API
        
    Returns:
    --------
    str : Markdown explanation of the chart
    """
    try:
        # Create client with ephemeral token
        client = genai.Client(
            api_key=ephemeral_token,
            http_options=types.HttpOptions(api_version="v1alpha")
        )
        
        model = "gemini-2.5-flash"
        config = {"response_modalities": ["TEXT"]}
        
        # Construct prompt with comprehensive metadata
        prompt = f"""You are a financial data analyst. Explain this chart in clear, concise language.

**Chart Title:** {chart_card.get('title', 'Untitled')}

**Description:** {description}

**Chart Details:**
- X-axis: {chart_card.get('x_axis', 'N/A')}
- Y-axis: {chart_card.get('y_axis', 'N/A')}"""

        # Add secondary y-axis if present
        if chart_card.get('y2_axis'):
            prompt += f"\n- Secondary Y-axis: {chart_card.get('y2_axis')}"

        # Add series information
        prompt += f"\n- Number of data series: {chart_card.get('series_count', 0)}"
        if chart_card.get('series_names'):
            series_list = chart_card.get('series_names')[:10]  # Limit to first 10
            prompt += f"\n- Series: {', '.join(series_list)}"

        prompt += f"""

**Key Statistics:**
{chr(10).join([f"- {k}: {v}" for k, v in key_stats.items()])}

**Date Range:** {chart_card.get('date_range', {}).get('start', 'N/A')} to {chart_card.get('date_range', {}).get('end', 'N/A')}"""

        # Add total periods if available
        if chart_card.get('date_range', {}).get('total_periods'):
            prompt += f" ({chart_card['date_range']['total_periods']} periods)"

        prompt += """

Provide a 2-3 paragraph explanation that:
1. Summarizes what the chart shows
2. Highlights the most important insights from the key statistics
3. Explains what patterns or trends are visible
4. Provides context for interpreting the results

Write in markdown format with appropriate formatting."""

        async with client.aio.live.connect(model=model, config=config) as session:
            await session.send(input=prompt, end_of_turn=True)
            
            explanation = ""
            async for response in session.receive():
                if response.text:
                    explanation += response.text
            
            return explanation
            
    except Exception as e:
        return f"**Error generating explanation:** {str(e)}"


def _run_async_in_sync(coro):
    """
    Run an async coroutine in a sync context.
    Handles both environments with and without existing event loops.
    """
    # Apply nest_asyncio to handle nested event loops (e.g., in Jupyter)
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    
    # Try to get or create event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already have a running loop, just run the coroutine on it
            return loop.run_until_complete(coro)
        else:
            # Have a loop but it's not running, run the coroutine
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No loop exists, create new one and run
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def explain_chart(
    fig,
    display_explanation: bool = True,
    category: str = None,
    plot_name: str = None
) -> Optional[str]:
    """
    Synchronous wrapper to explain a chart with LLM metadata.
    
    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        The Plotly figure with LLM metadata
    display_explanation : bool
        Whether to display the explanation immediately
    category : str, optional
        Category for caching (e.g., "signal_evaluation")
    plot_name : str, optional
        Plot name for caching (e.g., "performance_metrics")
        
    Returns:
    --------
    str or None : The explanation markdown, or None if failed
    """
    # Check if figure has metadata
    if not hasattr(fig.layout, 'meta') or not fig.layout.meta:
        if display_explanation:
            display(Markdown("⚠️ **Chart does not have metadata for explanation.**"))
        return None
    
    metadata = fig.layout.meta
    
    # Extract metadata components
    chart_card = metadata.get('chart_card', {})
    key_stats = chart_card.get('key_statistics', {})
    description = chart_card.get('description', '')
    
    if not key_stats:
        if display_explanation:
            display(Markdown("⚠️ **No key statistics available for explanation.**"))
        return None
    
    # Auto-generate category and plot_name from metadata if not provided
    if category is None or plot_name is None:
        title = chart_card.get('title', 'untitled')
        if category is None:
            # First check if category is stored in figure metadata
            if 'category' in metadata:
                category = metadata['category']
            else:
                # Fallback: Try to detect category from title
                title_lower = title.lower()
                
                # Check for signal-related terms
                if any(term in title_lower for term in ['signal', 'decile', 'sharpe', 'cumulative_returns', 'performance']):
                    category = "signal_evaluation"
                # Check for other patterns
                elif "_" in title:
                    parts = title.split("_")
                    if len(parts) >= 2:
                        category = parts[0]
                else:
                    category = "general"
        
        if plot_name is None:
            # Use title as plot name, sanitize it
            plot_name = title.lower().replace(" ", "_").replace("/", "_").replace("\\", "_").replace("(", "").replace(")", "").replace(",", "")
    
    # Cache the chart data
    cache_chart_data(category, plot_name, chart_card)
    
    # Get ephemeral token
    ephemeral_token = get_ephemeral_token()
    
    if not ephemeral_token:
        if display_explanation:
            display(Markdown("❌ **Failed to get ephemeral token. Cannot generate explanation.**"))
        return None
    
    # Generate explanation
    try:
        # Run async function in sync context with proper event loop handling
        explanation = _run_async_in_sync(explain_chart_async(
            chart_card=chart_card,
            key_stats=key_stats,
            description=description,
            ephemeral_token=ephemeral_token
        ))
        
        # Cache the explanation
        cache_explanation(category, plot_name, explanation)
        
        if display_explanation:
            display(Markdown("---"))
            display(Markdown("## 🤖 Chart Explanation"))
            display(Markdown(explanation))
            display(Markdown("---"))
        
        return explanation
        
    except Exception as e:
        error_msg = f"❌ **Error generating explanation:** {str(e)}"
        if display_explanation:
            display(Markdown(error_msg))
        return None


def auto_explain_chart(fig):
    """
    Automatically explain a chart after it's created.
    
    This is a convenience function that can be called after
    generating any plot to get an AI explanation.
    
    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        The Plotly figure to explain
        
    Returns:
    --------
    plotly.graph_objects.Figure : The same figure (for chaining)
    """
    explain_chart(fig, display_explanation=True)
    return fig
