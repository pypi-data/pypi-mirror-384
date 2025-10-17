"""
Adapters for converting statistical outputs from different libraries
into standardized format for the Stable package.
"""

from .scipy_adapter import ScipyAdapter
from .statsmodels_adapter import StatsmodelsAdapter

__all__ = ["ScipyAdapter", "StatsmodelsAdapter"]
