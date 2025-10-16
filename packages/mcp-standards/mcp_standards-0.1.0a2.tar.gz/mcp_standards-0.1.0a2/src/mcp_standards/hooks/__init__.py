"""Claude Code Hooks Integration for Automatic Learning

This module provides intelligent hooks that capture tool executions
and automatically extract learning patterns to improve Claude Code over time.
"""

from .capture_hook import capture_tool_execution
from .significance_scorer import SignificanceScorer
from .pattern_extractor import PatternExtractor

__all__ = [
    'capture_tool_execution',
    'SignificanceScorer',
    'PatternExtractor',
]
