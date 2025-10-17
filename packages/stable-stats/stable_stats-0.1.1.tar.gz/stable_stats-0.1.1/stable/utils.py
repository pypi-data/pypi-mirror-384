"""
Utility functions for the Stable package.
"""

import re
from typing import Any, Dict, Optional, Union


def detect_test_type(result: Any) -> str:
    """
    Detect the type of statistical test from the result object.
    
    Args:
        result: Statistical test result object
        
    Returns:
        String identifier for the test type
    """
    # Get the class name
    class_name = result.__class__.__name__
    
    # Get the module name
    module_name = result.__class__.__module__
    
    # Scipy stats tests
    if 'scipy' in module_name:
        if 'TtestResult' in class_name:
            return 'ttest'
        elif 'F_onewayResult' in class_name:
            return 'anova'
        elif 'Chi2Result' in class_name:
            return 'chi2'
        elif 'KstestResult' in class_name:
            return 'ks_test'
        elif 'MannwhitneyuResult' in class_name:
            return 'mannwhitneyu'
        elif 'WilcoxonResult' in class_name:
            return 'wilcoxon'
        elif 'KruskalResult' in class_name:
            return 'kruskal'
        elif 'FriedmanchisquareResult' in class_name:
            return 'friedman'
    
    # Statsmodels tests
    elif 'statsmodels' in module_name:
        if 'RegressionResults' in class_name:
            return 'regression'
        elif 'AnovaResults' in class_name:
            return 'anova'
        elif 'TTestResults' in class_name:
            return 'ttest'
        elif 'ContrastResults' in class_name:
            return 'contrast'
    
    # Fallback: try to infer from attributes
    if hasattr(result, 'statistic') and hasattr(result, 'pvalue'):
        if hasattr(result, 'df'):
            return 'ttest'
        elif hasattr(result, 'df_denom'):
            return 'f_test'
        else:
            return 'generic_test'
    
    return 'unknown'


def format_p_value(p_value: float, alpha: float = 0.05) -> str:
    """
    Format p-value with significance stars.
    
    Args:
        p_value: The p-value to format
        alpha: Significance level (default 0.05)
        
    Returns:
        Formatted p-value string with significance stars
    """
    if p_value < 0.001:
        return f"{p_value:.3f}***"
    elif p_value < 0.01:
        return f"{p_value:.3f}**"
    elif p_value < alpha:
        return f"{p_value:.3f}*"
    else:
        return f"{p_value:.3f}"


def format_effect_size(effect_size: float, effect_type: str = "cohen_d") -> str:
    """
    Format effect size with interpretation.
    
    Args:
        effect_size: The effect size value
        effect_type: Type of effect size (cohen_d, eta_squared, etc.)
        
    Returns:
        Formatted effect size string
    """
    if effect_type == "cohen_d":
        if abs(effect_size) < 0.2:
            interpretation = "negligible"
        elif abs(effect_size) < 0.5:
            interpretation = "small"
        elif abs(effect_size) < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"
        
        return f"{effect_size:.3f} ({interpretation})"
    
    return f"{effect_size:.3f}"


def format_confidence_interval(ci_lower, ci_upper, confidence: float = 0.95) -> str:
    """
    Format confidence interval.
    
    Args:
        ci_lower: Lower bound of confidence interval (can be float or list)
        ci_upper: Upper bound of confidence interval (can be float or list)
        confidence: Confidence level (default 0.95)
        
    Returns:
        Formatted confidence interval string
    """
    conf_percent = int(confidence * 100)
    
    # Handle list inputs (multiple confidence intervals)
    if isinstance(ci_lower, list) and isinstance(ci_upper, list):
        if len(ci_lower) == 1 and len(ci_upper) == 1:
            return f"[{ci_lower[0]:.3f}, {ci_upper[0]:.3f}]"
        else:
            # Multiple intervals - return first one for now
            return f"[{ci_lower[0]:.3f}, {ci_upper[0]:.3f}]"
    
    # Handle single values
    return f"[{ci_lower:.3f}, {ci_upper:.3f}]"


def get_test_name(test_type: str) -> str:
    """
    Get human-readable test name from test type.
    
    Args:
        test_type: Test type identifier
        
    Returns:
        Human-readable test name
    """
    test_names = {
        'ttest': 't-test',
        'ttest_ind': 'Independent t-test',
        'ttest_rel': 'Paired t-test',
        'ttest_1samp': 'One-sample t-test',
        'anova': 'ANOVA',
        'f_oneway': 'One-way ANOVA',
        'chi2': 'Chi-square test',
        'ks_test': 'Kolmogorov-Smirnov test',
        'mannwhitneyu': 'Mann-Whitney U test',
        'wilcoxon': 'Wilcoxon signed-rank test',
        'kruskal': 'Kruskal-Wallis test',
        'friedman': 'Friedman test',
        'regression': 'Linear Regression',
        'f_test': 'F-test',
        'contrast': 'Contrast Test',
        'generic_test': 'Statistical Test',
        'unknown': 'Unknown Test'
    }
    
    return test_names.get(test_type, test_type)


def round_to_significant_digits(value: float, digits: int = 3) -> float:
    """
    Round a number to a specified number of significant digits.
    
    Args:
        value: The number to round
        digits: Number of significant digits
        
    Returns:
        Rounded number
    """
    if value == 0:
        return 0.0
    
    import math
    return round(value, digits - int(math.floor(math.log10(abs(value)))) - 1)


def clean_variable_name(name: str) -> str:
    """
    Clean variable names for display.
    
    Args:
        name: Variable name to clean
        
    Returns:
        Cleaned variable name
    """
    # Remove common prefixes/suffixes
    name = re.sub(r'^x\d+_', '', name)
    name = re.sub(r'^C\(', '', name)
    name = re.sub(r'\)$', '', name)
    
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    
    # Capitalize first letter of each word
    name = name.title()
    
    return name


def validate_input(result: Any) -> bool:
    """
    Validate that the input is a statistical test result.
    
    Args:
        result: Object to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check if it's from a known statistical library
    module_name = result.__class__.__module__
    is_statistical = any(lib in module_name for lib in ['scipy', 'statsmodels', 'pingouin'])
    
    if not is_statistical:
        return False
    
    # For scipy results, check for basic statistical test attributes
    if 'scipy' in module_name:
        required_attrs = ['statistic', 'pvalue']
        has_required = all(hasattr(result, attr) for attr in required_attrs)
        return has_required
    
    # For statsmodels results, check for model attributes
    elif 'statsmodels' in module_name:
        # Check for regression results
        if hasattr(result, 'params') and hasattr(result, 'pvalues'):
            return True
        # Check for other statsmodels results
        elif hasattr(result, 'statistic') and hasattr(result, 'pvalue'):
            return True
        # Check for test results
        elif hasattr(result, 'fvalue') and hasattr(result, 'f_pvalue'):
            return True
    
    return False
