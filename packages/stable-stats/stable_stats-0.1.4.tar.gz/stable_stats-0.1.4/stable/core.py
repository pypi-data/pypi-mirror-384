"""
Core functionality for the Stable package.
"""

from typing import Any, Dict, List, Optional, Union
from .adapters import ScipyAdapter, StatsmodelsAdapter
from .exporters import MarkdownExporter, ExcelExporter, HTMLExporter
from .utils import validate_input, detect_test_type


class Stable:
    """
    Main class for beautifying statistical outputs into clean tables.
    """
    
    def __init__(self, result: Any):
        """
        Initialize Stable with a statistical test result.
        
        Args:
            result: Statistical test result from scipy, statsmodels, etc.
            
        Raises:
            ValueError: If the input is not a valid statistical test result
        """
        if not validate_input(result):
            raise ValueError("Input must be a valid statistical test result from scipy, statsmodels, or similar library")
        
        self.original_result = result
        self.test_type = detect_test_type(result)
        self._standardized_data: Optional[Dict[str, Any]] = None
        self._adapter: Optional[Union[ScipyAdapter, StatsmodelsAdapter]] = None
        
        # Initialize appropriate adapter
        self._initialize_adapter()
    
    def _initialize_adapter(self) -> None:
        """Initialize the appropriate adapter based on the result type."""
        module_name = self.original_result.__class__.__module__
        
        if 'scipy' in module_name:
            self._adapter = ScipyAdapter(self.original_result)
        elif 'statsmodels' in module_name:
            self._adapter = StatsmodelsAdapter(self.original_result)
        else:
            # Try scipy adapter as fallback
            self._adapter = ScipyAdapter(self.original_result)
    
    @property
    def standardized_data(self) -> Dict[str, Any]:
        """
        Get the standardized data representation.
        
        Returns:
            Dictionary with standardized statistical results
        """
        if self._standardized_data is None:
            if self._adapter is not None:
                self._standardized_data = self._adapter.to_standardized()
            else:
                raise RuntimeError("No adapter available for this result type")
        
        return self._standardized_data
    
    def to_markdown(self, title: Optional[str] = None) -> str:
        """
        Export results to Markdown format.
        
        Args:
            title: Optional title for the table
            
        Returns:
            Markdown formatted string
        """
        exporter = MarkdownExporter(self.standardized_data)
        return exporter.export(title=title)
    
    def to_excel(self, filename: str, sheet_name: str = "Statistical Results") -> None:
        """
        Export results to Excel format.
        
        Args:
            filename: Path to the Excel file to create
            sheet_name: Name of the Excel sheet
        """
        exporter = ExcelExporter(self.standardized_data)
        exporter.export(filename, sheet_name)
    
    def to_html(self, title: Optional[str] = None, include_css: bool = True) -> str:
        """
        Export results to HTML format.
        
        Args:
            title: Optional title for the HTML document
            include_css: Whether to include embedded CSS styles
            
        Returns:
            HTML formatted string
        """
        exporter = HTMLExporter(self.standardized_data)
        return exporter.export(title=title, include_css=include_css)
    
    def to_dataframe(self) -> Any:
        """
        Export results to pandas DataFrame.
        
        Returns:
            pandas DataFrame with the main results
        """
        exporter = ExcelExporter(self.standardized_data)
        return exporter.to_dataframe()
    
    def summary(self) -> str:
        """
        Get a brief summary of the test result.
        
        Returns:
            String summary of the test
        """
        if self._adapter is not None:
            return self._adapter.get_summary()
        return f"Test type: {self.test_type}"
    
    def is_supported(self) -> bool:
        """
        Check if this result type is supported.
        
        Returns:
            True if supported, False otherwise
        """
        if self._adapter is not None:
            return self._adapter.is_supported()
        return False
    
    def get_test_name(self) -> str:
        """
        Get the human-readable test name.
        
        Returns:
            Test name string
        """
        test_name = self.standardized_data.get('test_name', 'Unknown Test')
        return str(test_name)
    
    def get_statistic(self) -> Optional[Union[float, Dict[str, float]]]:
        """
        Get the test statistic(s).
        
        Returns:
            Test statistic value(s)
        """
        return self.standardized_data.get('statistic')
    
    def get_p_value(self) -> Optional[Union[float, Dict[str, float]]]:
        """
        Get the p-value(s).
        
        Returns:
            P-value(s)
        """
        return self.standardized_data.get('p_value')
    
    def get_effect_size(self) -> Optional[Union[float, Dict[str, float]]]:
        """
        Get the effect size(s).
        
        Returns:
            Effect size value(s)
        """
        return self.standardized_data.get('effect_size')
    
    def get_confidence_interval(self) -> Optional[Dict[str, float]]:
        """
        Get the confidence interval.
        
        Returns:
            Confidence interval dictionary with 'lower' and 'upper' keys
        """
        return self.standardized_data.get('confidence_interval')
    
    def get_sample_size(self) -> Optional[Union[int, Dict[str, int]]]:
        """
        Get the sample size information.
        
        Returns:
            Sample size information
        """
        return self.standardized_data.get('sample_size')
    
    def get_degrees_of_freedom(self) -> Optional[Union[float, Dict[str, float]]]:
        """
        Get the degrees of freedom.
        
        Returns:
            Degrees of freedom
        """
        return self.standardized_data.get('degrees_of_freedom')
    
    def get_coefficients(self) -> Optional[list]:
        """
        Get coefficient information (for regression models).
        
        Returns:
            List of coefficient dictionaries
        """
        return self.standardized_data.get('coefficients')
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get model information (for regression models).
        
        Returns:
            Dictionary with model information
        """
        return self.standardized_data.get('model_info')
    
    def get_additional_info(self) -> Optional[Dict[str, Any]]:
        """
        Get additional information.
        
        Returns:
            Dictionary with additional information
        """
        return self.standardized_data.get('additional_info')
    
    def __str__(self) -> str:
        """String representation."""
        return self.summary()
    
    def __repr__(self) -> str:
        """Representation."""
        return f"Stable({self.get_test_name()}, {self.test_type})"
    
    @classmethod
    def from_ttest(cls, group1: Any, group2: Any, **kwargs: Any) -> 'Stable':
        """
        Create Stable instance from a t-test.
        
        Args:
            group1: First group data
            group2: Second group data
            **kwargs: Additional arguments for scipy.stats.ttest_ind
            
        Returns:
            Stable instance
        """
        from scipy import stats
        result = stats.ttest_ind(group1, group2, **kwargs)
        return cls(result)
    
    @classmethod
    def from_anova(cls, *groups: Any, **kwargs: Any) -> 'Stable':
        """
        Create Stable instance from ANOVA.
        
        Args:
            *groups: Groups of data for ANOVA
            **kwargs: Additional arguments for scipy.stats.f_oneway
            
        Returns:
            Stable instance
        """
        from scipy import stats
        result = stats.f_oneway(*groups, **kwargs)
        return cls(result)
    
    @classmethod
    def from_chi2(cls, observed: Any, expected: Optional[Any] = None, **kwargs: Any) -> 'Stable':
        """
        Create Stable instance from chi-square test.
        
        Args:
            observed: Observed frequencies
            expected: Expected frequencies (optional)
            **kwargs: Additional arguments for scipy.stats.chisquare
            
        Returns:
            Stable instance
        """
        from scipy import stats
        if expected is None:
            result = stats.chisquare(observed, **kwargs)
        else:
            result = stats.chisquare(observed, expected, **kwargs)
        return cls(result)
    
    @classmethod
    def from_regression(cls, model_result: Any) -> 'Stable':
        """
        Create Stable instance from a regression model result.
        
        Args:
            model_result: statsmodels regression result object
            
        Returns:
            Stable instance
        """
        return cls(model_result)
