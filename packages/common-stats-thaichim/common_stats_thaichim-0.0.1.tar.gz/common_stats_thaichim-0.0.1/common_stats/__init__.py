"""
Common Stats - A library for basic statistical calculations.

This module provides functions to calculate basic statistics, including:
- Mean
- Median
- Mode
- Standard Deviation
"""

from .statistics import mean, median, mode, standard_deviation

__all__ = ['mean', 'median', 'mode', 'standard_deviation']

def __version__():
    """Return the version of the simple_stats package."""
    return "0.0.1"

def describe():
    """Print a description of the package and its features."""
    description = (
        "Common Stats Library\n"
        "Version: {}\n"
        "Provides basic statistical calculations including:\n"
        "  - Mean\n"
        "  - Median\n"
        "  - Mode\n"
        "  - Standard Deviation\n"
    ).format(__version__())
    print(description)