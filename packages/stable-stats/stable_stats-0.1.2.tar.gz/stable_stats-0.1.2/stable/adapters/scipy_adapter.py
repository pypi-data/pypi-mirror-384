"""
Adapter for converting scipy.stats outputs into standardized format.
"""

from typing import Any, Dict, Optional, Union
import numpy as np
from ..utils import detect_test_type, get_test_name


class ScipyAdapter:
    """
    Adapter for scipy.stats statistical test results.
    """
    
    def __init__(self, result: Any):
        """
        Initialize the adapter with a scipy.stats result.
        
        Args:
            result: scipy.stats test result object
        """
        self.result = result
        self.test_type = detect_test_type(result)
        
    def to_standardized(self) -> Dict[str, Any]:
        """
        Convert scipy.stats result to standardized format.
        
        Returns:
            Dictionary with standardized statistical results
        """
        standardized = {
            'test_name': get_test_name(self.test_type),
            'test_type': self.test_type,
            'statistic': self._extract_statistic(),
            'p_value': self._extract_p_value(),
            'degrees_of_freedom': self._extract_df(),
            'effect_size': self._extract_effect_size(),
            'confidence_interval': self._extract_ci(),
            'sample_size': self._extract_sample_size(),
            'additional_info': self._extract_additional_info()
        }
        
        return standardized
    
    def _extract_statistic(self) -> Optional[float]:
        """Extract test statistic."""
        if hasattr(self.result, 'statistic'):
            return float(self.result.statistic)
        return None
    
    def _extract_p_value(self) -> Optional[float]:
        """Extract p-value."""
        if hasattr(self.result, 'pvalue'):
            return float(self.result.pvalue)
        return None
    
    def _extract_df(self) -> Optional[Union[float, Dict[str, float]]]:
        """Extract degrees of freedom."""
        if hasattr(self.result, 'df'):
            return float(self.result.df)
        elif hasattr(self.result, 'df_denom') and hasattr(self.result, 'df_num'):
            return {
                'numerator': float(self.result.df_num),
                'denominator': float(self.result.df_denom)
            }
        return None
    
    def _extract_effect_size(self) -> Optional[float]:
        """Extract effect size if available."""
        # For t-tests, we might be able to calculate Cohen's d
        if self.test_type == 'ttest' and hasattr(self.result, 'statistic'):
            # This is a simplified calculation - in practice, you'd need the sample sizes
            # For now, we'll just return the t-statistic as a rough effect size indicator
            return float(self.result.statistic)
        return None
    
    def _extract_ci(self) -> Optional[Dict[str, float]]:
        """Extract confidence interval if available."""
        if hasattr(self.result, 'confidence_interval'):
            ci = self.result.confidence_interval
            if hasattr(ci, 'low') and hasattr(ci, 'high'):
                return {
                    'lower': float(ci.low),
                    'upper': float(ci.high)
                }
        return None
    
    def _extract_sample_size(self) -> Optional[Dict[str, int]]:
        """Extract sample size information if available."""
        # This is tricky for scipy results as they don't always store sample sizes
        # We'll try to infer from the result object
        if hasattr(self.result, 'n_obs'):
            return {'total': int(self.result.n_obs)}
        return None
    
    def _extract_additional_info(self) -> Dict[str, Any]:
        """Extract any additional information specific to the test."""
        additional = {}
        
        # Add any other attributes that might be useful
        for attr in ['alternative', 'method']:
            if hasattr(self.result, attr):
                additional[attr] = getattr(self.result, attr)
        
        # For specific test types, add relevant information
        if self.test_type == 'ttest':
            if hasattr(self.result, 'alternative'):
                additional['alternative_hypothesis'] = self.result.alternative
        
        elif self.test_type == 'anova':
            if hasattr(self.result, 'df_denom'):
                additional['error_df'] = float(self.result.df_denom)
        
        elif self.test_type == 'chi2':
            if hasattr(self.result, 'expected_freq'):
                additional['expected_frequencies'] = self.result.expected_freq.tolist()
        
        return additional
    
    def is_supported(self) -> bool:
        """
        Check if this result type is supported by the adapter.
        
        Returns:
            True if supported, False otherwise
        """
        supported_types = [
            'ttest', 'ttest_ind', 'ttest_rel', 'ttest_1samp',
            'anova', 'f_oneway', 'chi2', 'ks_test',
            'mannwhitneyu', 'wilcoxon', 'kruskal', 'friedman'
        ]
        return self.test_type in supported_types
    
    def get_summary(self) -> str:
        """
        Get a brief summary of the test result.
        
        Returns:
            String summary of the test
        """
        if not self.is_supported():
            return f"Unsupported test type: {self.test_type}"
        
        standardized = self.to_standardized()
        test_name = standardized['test_name']
        statistic = standardized['statistic']
        p_value = standardized['p_value']
        
        if statistic is not None and p_value is not None:
            significance = "significant" if p_value < 0.05 else "not significant"
            return f"{test_name}: {statistic:.3f}, p = {p_value:.3f} ({significance})"
        
        return f"{test_name}: Result available"
