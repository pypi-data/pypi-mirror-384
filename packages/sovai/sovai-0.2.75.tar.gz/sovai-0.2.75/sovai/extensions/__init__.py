"""
Extensions module for SovAI.

This module provides extended functionality including:
- Chart explanation using Gemini AI
- Signal evaluation and backtesting
- Various data processing utilities
"""

from .chart_explainer import explain_chart, auto_explain_chart, get_ephemeral_token

__all__ = [
    'explain_chart',
    'auto_explain_chart',
    'get_ephemeral_token',
]
