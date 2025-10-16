"""
Markdown exporter for statistical results.
"""

from typing import Any, Dict, List, Optional, Union
from ..utils import format_p_value, format_effect_size, format_confidence_interval


class MarkdownExporter:
    """
    Exporter for converting standardized statistical results to Markdown format.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the exporter with standardized data.
        
        Args:
            data: Standardized statistical results dictionary
        """
        self.data = data
    
    def export(self, title: Optional[str] = None) -> str:
        """
        Export the statistical results to Markdown format.
        
        Args:
            title: Optional title for the table
            
        Returns:
            Markdown formatted string
        """
        markdown_parts = []
        
        # Add title if provided
        if title:
            markdown_parts.append(f"# {title}\n")
        
        # Add test information
        markdown_parts.append(self._format_test_info())
        
        # Add main results table
        markdown_parts.append(self._format_main_table())
        
        # Add coefficients table if available
        if self.data.get('coefficients'):
            markdown_parts.append(self._format_coefficients_table())
        
        # Add model information if available
        if self.data.get('model_info'):
            markdown_parts.append(self._format_model_info())
        
        # Add additional information
        if self.data.get('additional_info'):
            markdown_parts.append(self._format_additional_info())
        
        return "\n".join(markdown_parts)
    
    def _format_test_info(self) -> str:
        """Format basic test information."""
        test_name = self.data.get('test_name', 'Statistical Test')
        test_type = self.data.get('test_type', 'unknown')
        
        info_lines = [f"## {test_name}", ""]
        
        # Add sample size if available
        sample_size = self.data.get('sample_size')
        if sample_size:
            if isinstance(sample_size, dict):
                if 'total' in sample_size:
                    info_lines.append(f"**Sample Size:** {sample_size['total']}")
            else:
                info_lines.append(f"**Sample Size:** {sample_size}")
        
        # Add degrees of freedom if available
        df = self.data.get('degrees_of_freedom')
        if df is not None:
            if isinstance(df, dict):
                df_str = ", ".join([f"{k}: {v}" for k, v in df.items()])
                info_lines.append(f"**Degrees of Freedom:** {df_str}")
            else:
                info_lines.append(f"**Degrees of Freedom:** {df}")
        
        info_lines.append("")
        return "\n".join(info_lines)
    
    def _format_main_table(self) -> str:
        """Format the main results table."""
        lines = ["## Results", ""]
        
        # Create table header
        headers = ["Statistic", "Value", "p-value", "Significance"]
        table_lines = ["| " + " | ".join(headers) + " |"]
        table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Add main statistic row
        statistic = self.data.get('statistic')
        p_value = self.data.get('p_value')
        
        if statistic is not None and p_value is not None:
            # Handle multiple statistics
            if isinstance(statistic, dict):
                for key, value in statistic.items():
                    p_val = p_value.get(key.replace('stat_', 'p_'), p_value) if isinstance(p_value, dict) else p_value
                    significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
                    
                    row = [
                        key.replace('stat_', '').title(),
                        f"{value:.3f}",
                        format_p_value(p_val),
                        significance
                    ]
                    table_lines.append("| " + " | ".join(row) + " |")
            else:
                significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
                row = [
                    "Test Statistic",
                    f"{statistic:.3f}",
                    format_p_value(p_value),
                    significance
                ]
                table_lines.append("| " + " | ".join(row) + " |")
        
        # Add effect size if available
        effect_size = self.data.get('effect_size')
        if effect_size is not None:
            if isinstance(effect_size, dict):
                for key, value in effect_size.items():
                    row = [
                        key.replace('_', ' ').title(),
                        f"{value:.3f}",
                        "",
                        ""
                    ]
                    table_lines.append("| " + " | ".join(row) + " |")
            else:
                row = [
                    "Effect Size",
                    f"{effect_size:.3f}",
                    "",
                    ""
                ]
                table_lines.append("| " + " | ".join(row) + " |")
        
        # Add confidence interval if available
        ci = self.data.get('confidence_interval')
        if ci is not None:
            if isinstance(ci, dict) and 'lower' in ci and 'upper' in ci:
                ci_str = format_confidence_interval(ci['lower'], ci['upper'])
                row = [
                    "95% CI",
                    ci_str,
                    "",
                    ""
                ]
                table_lines.append("| " + " | ".join(row) + " |")
        
        lines.extend(table_lines)
        lines.append("")
        return "\n".join(lines)
    
    def _format_coefficients_table(self) -> str:
        """Format coefficients table for regression models."""
        coefficients = self.data.get('coefficients', [])
        if not coefficients:
            return ""
        
        lines = ["## Coefficients", ""]
        
        # Create table header
        headers = ["Variable", "Coefficient", "SE", "p-value", "95% CI"]
        table_lines = ["| " + " | ".join(headers) + " |"]
        table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Add coefficient rows
        for coef in coefficients:
            variable = coef.get('variable', 'Unknown')
            coefficient = coef.get('coefficient', 0)
            std_error = coef.get('std_error')
            p_value = coef.get('p_value')
            ci_lower = coef.get('ci_lower')
            ci_upper = coef.get('ci_upper')
            
            # Format values
            coef_str = f"{coefficient:.3f}"
            se_str = f"{std_error:.3f}" if std_error is not None else ""
            p_str = format_p_value(p_value) if p_value is not None else ""
            ci_str = format_confidence_interval(ci_lower, ci_upper) if ci_lower is not None and ci_upper is not None else ""
            
            row = [variable, coef_str, se_str, p_str, ci_str]
            table_lines.append("| " + " | ".join(row) + " |")
        
        lines.extend(table_lines)
        lines.append("")
        return "\n".join(lines)
    
    def _format_model_info(self) -> str:
        """Format model information."""
        model_info = self.data.get('model_info', {})
        if not model_info:
            return ""
        
        lines = ["## Model Information", ""]
        
        # Create table for model fit statistics
        headers = ["Statistic", "Value"]
        table_lines = ["| " + " | ".join(headers) + " |"]
        table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Add model statistics
        for key, value in model_info.items():
            if isinstance(value, (int, float)):
                row = [key.replace('_', ' ').title(), f"{value:.3f}"]
                table_lines.append("| " + " | ".join(row) + " |")
        
        lines.extend(table_lines)
        lines.append("")
        return "\n".join(lines)
    
    def _format_additional_info(self) -> str:
        """Format additional information."""
        additional_info = self.data.get('additional_info', {})
        if not additional_info:
            return ""
        
        lines = ["## Additional Information", ""]
        
        for key, value in additional_info.items():
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
            elif isinstance(value, list):
                lines.append(f"**{key.replace('_', ' ').title()}:** {', '.join(map(str, value))}")
        
        lines.append("")
        return "\n".join(lines)
    
    def to_string(self) -> str:
        """Convert to string representation."""
        return self.export()
    
    def __str__(self) -> str:
        """String representation."""
        return self.to_string()
