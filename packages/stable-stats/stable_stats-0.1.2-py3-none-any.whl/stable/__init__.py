"""
Stable - A Python package for beautifying statistical outputs into clean tables.

This package provides a simple interface to convert raw statistical results
from scipy, statsmodels, and other libraries into well-formatted tables
that can be exported to Markdown, Excel, HTML, and other formats.

Example usage:
    from scipy import stats
    from stable import Stable
    
    # Run a test
    result = stats.ttest_ind(group1, group2)
    
    # Beautify
    table = Stable(result)
    print(table.to_markdown())  # Pretty table in console
    table.to_excel("results.xlsx")  # Export to Excel
"""

from .core import Stable

__version__ = "0.1.2"
__author__ = "Christopher Ren"
__email__ = "chris.ren@emory.edu"

__all__ = ["Stable"]
