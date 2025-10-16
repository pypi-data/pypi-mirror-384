"""
Adapter for converting statsmodels outputs into standardized format.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from ..utils import detect_test_type, get_test_name


class StatsmodelsAdapter:
    """
    Adapter for statsmodels statistical test results.
    """
    
    def __init__(self, result: Any):
        """
        Initialize the adapter with a statsmodels result.
        
        Args:
            result: statsmodels test result object
        """
        self.result = result
        self.test_type = detect_test_type(result)
        
    def to_standardized(self) -> Dict[str, Any]:
        """
        Convert statsmodels result to standardized format.
        
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
            'coefficients': self._extract_coefficients(),
            'model_info': self._extract_model_info(),
            'additional_info': self._extract_additional_info()
        }
        
        return standardized
    
    def _extract_statistic(self) -> Optional[Union[float, Dict[str, float]]]:
        """Extract test statistic(s)."""
        if hasattr(self.result, 'statistic'):
            stat = self.result.statistic
            if isinstance(stat, (int, float)):
                return float(stat)
            elif hasattr(stat, '__len__') and len(stat) == 1:
                return float(stat[0])
            else:
                # Multiple statistics (e.g., F-test with multiple components)
                return {f'stat_{i}': float(s) for i, s in enumerate(stat)}
        
        # For regression results, extract F-statistic
        if hasattr(self.result, 'fvalue'):
            return float(self.result.fvalue)
        
        return None
    
    def _extract_p_value(self) -> Optional[Union[float, Dict[str, float]]]:
        """Extract p-value(s)."""
        if hasattr(self.result, 'pvalue'):
            pval = self.result.pvalue
            if isinstance(pval, (int, float)):
                return float(pval)
            elif hasattr(pval, '__len__') and len(pval) == 1:
                return float(pval[0])
            else:
                # Multiple p-values
                return {f'p_{i}': float(p) for i, p in enumerate(pval)}
        
        # For regression results, extract F-test p-value
        if hasattr(self.result, 'f_pvalue'):
            return float(self.result.f_pvalue)
        
        return None
    
    def _extract_df(self) -> Optional[Union[float, Dict[str, float]]]:
        """Extract degrees of freedom."""
        if hasattr(self.result, 'df_resid') and hasattr(self.result, 'df_model'):
            return {
                'model': float(self.result.df_model),
                'residual': float(self.result.df_resid),
                'total': float(self.result.df_model + self.result.df_resid)
            }
        elif hasattr(self.result, 'df'):
            return float(self.result.df)
        return None
    
    def _extract_effect_size(self) -> Optional[Dict[str, float]]:
        """Extract effect size measures."""
        effect_sizes = {}
        
        # R-squared
        if hasattr(self.result, 'rsquared'):
            effect_sizes['r_squared'] = float(self.result.rsquared)
        
        # Adjusted R-squared
        if hasattr(self.result, 'rsquared_adj'):
            effect_sizes['r_squared_adj'] = float(self.result.rsquared_adj)
        
        # Partial eta squared (for ANOVA)
        if hasattr(self.result, 'ess') and hasattr(self.result, 'ssr'):
            ess = float(self.result.ess)
            ssr = float(self.result.ssr)
            total_ss = ess + ssr
            if total_ss > 0:
                effect_sizes['eta_squared'] = ess / total_ss
        
        return effect_sizes if effect_sizes else None
    
    def _extract_ci(self) -> Optional[Dict[str, List[float]]]:
        """Extract confidence intervals."""
        if hasattr(self.result, 'conf_int'):
            ci = self.result.conf_int()
            if isinstance(ci, pd.DataFrame):
                return {
                    'lower': ci.iloc[:, 0].tolist(),
                    'upper': ci.iloc[:, 1].tolist()
                }
        return None
    
    def _extract_sample_size(self) -> Optional[Dict[str, int]]:
        """Extract sample size information."""
        if hasattr(self.result, 'nobs'):
            return {'total': int(self.result.nobs)}
        return None
    
    def _extract_coefficients(self) -> Optional[List[Dict[str, Any]]]:
        """Extract coefficient information for regression models."""
        if not hasattr(self.result, 'params'):
            return None
        
        coefs = []
        params = self.result.params
        pvalues = getattr(self.result, 'pvalues', None)
        std_errors = getattr(self.result, 'bse', None)
        conf_int = getattr(self.result, 'conf_int', None)
        
        # Get variable names
        if hasattr(self.result, 'model') and hasattr(self.result.model, 'exog_names'):
            var_names = self.result.model.exog_names
        elif hasattr(params, 'index'):
            var_names = params.index.tolist()
        else:
            var_names = [f'var_{i}' for i in range(len(params))]
        
        for i, var_name in enumerate(var_names):
            coef_info = {
                'variable': var_name,
                'coefficient': float(params.iloc[i]) if hasattr(params, 'iloc') else float(params[i]),
                'p_value': float(pvalues.iloc[i]) if pvalues is not None and hasattr(pvalues, 'iloc') else None,
                'std_error': float(std_errors.iloc[i]) if std_errors is not None and hasattr(std_errors, 'iloc') else None
            }
            
            # Add confidence interval if available
            if conf_int is not None:
                try:
                    ci = conf_int()
                    if isinstance(ci, pd.DataFrame):
                        coef_info['ci_lower'] = float(ci.iloc[i, 0])
                        coef_info['ci_upper'] = float(ci.iloc[i, 1])
                except:
                    pass
            
            coefs.append(coef_info)
        
        return coefs
    
    def _extract_model_info(self) -> Optional[Dict[str, Any]]:
        """Extract model-specific information."""
        model_info = {}
        
        # Model fit statistics
        if hasattr(self.result, 'aic'):
            model_info['aic'] = float(self.result.aic)
        if hasattr(self.result, 'bic'):
            model_info['bic'] = float(self.result.bic)
        if hasattr(self.result, 'llf'):
            model_info['log_likelihood'] = float(self.result.llf)
        
        # Residual information
        if hasattr(self.result, 'resid'):
            residuals = self.result.resid
            model_info['residual_mean'] = float(np.mean(residuals))
            model_info['residual_std'] = float(np.std(residuals))
        
        return model_info if model_info else None
    
    def _extract_additional_info(self) -> Dict[str, Any]:
        """Extract any additional information specific to the test."""
        additional = {}
        
        # Add any other attributes that might be useful
        for attr in ['method', 'use_t', 'use_f']:
            if hasattr(self.result, attr):
                additional[attr] = getattr(self.result, attr)
        
        # For regression results, add more details
        if self.test_type == 'regression':
            if hasattr(self.result, 'fittedvalues'):
                additional['fitted_values_available'] = True
            if hasattr(self.result, 'resid'):
                additional['residuals_available'] = True
        
        return additional
    
    def is_supported(self) -> bool:
        """
        Check if this result type is supported by the adapter.
        
        Returns:
            True if supported, False otherwise
        """
        supported_types = [
            'regression', 'anova', 'ttest', 'f_test', 'contrast'
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
            if isinstance(statistic, dict):
                stat_str = f"F = {statistic.get('stat_0', 'N/A')}"
            else:
                stat_str = f"{statistic:.3f}"
            
            if isinstance(p_value, dict):
                p_str = f"p = {p_value.get('p_0', 'N/A')}"
            else:
                p_str = f"p = {p_value:.3f}"
            
            significance = "significant" if (isinstance(p_value, float) and p_value < 0.05) else "not significant"
            return f"{test_name}: {stat_str}, {p_str} ({significance})"
        
        return f"{test_name}: Result available"
