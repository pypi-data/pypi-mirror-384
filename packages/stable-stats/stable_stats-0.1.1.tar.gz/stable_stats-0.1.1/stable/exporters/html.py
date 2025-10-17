"""
HTML exporter for statistical results.
"""

from typing import Any, Dict, List, Optional, Union
from ..utils import format_p_value, format_effect_size, format_confidence_interval


class HTMLExporter:
    """
    Exporter for converting standardized statistical results to HTML format.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the exporter with standardized data.
        
        Args:
            data: Standardized statistical results dictionary
        """
        self.data = data
    
    def export(self, title: Optional[str] = None, include_css: bool = True) -> str:
        """
        Export the statistical results to HTML format.
        
        Args:
            title: Optional title for the HTML document
            include_css: Whether to include embedded CSS styles
            
        Returns:
            HTML formatted string
        """
        html_parts = []
        
        # Add HTML document structure
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='en'>")
        html_parts.append("<head>")
        html_parts.append("    <meta charset='UTF-8'>")
        html_parts.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        
        if title:
            html_parts.append(f"    <title>{title}</title>")
        else:
            html_parts.append("    <title>Statistical Results</title>")
        
        if include_css:
            html_parts.append(self._get_css_styles())
        
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        # Add main content
        if title:
            html_parts.append(f"    <h1>{title}</h1>")
        
        # Add test information
        html_parts.append(self._format_test_info())
        
        # Add main results table
        html_parts.append(self._format_main_table())
        
        # Add coefficients table if available
        if self.data.get('coefficients'):
            html_parts.append(self._format_coefficients_table())
        
        # Add model information if available
        if self.data.get('model_info'):
            html_parts.append(self._format_model_info())
        
        # Add additional information
        if self.data.get('additional_info'):
            html_parts.append(self._format_additional_info())
        
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the HTML document."""
        return """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .info-item {
            background-color: #ecf0f1;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        
        .info-label {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .info-value {
            color: #34495e;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        th {
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e8f4f8;
        }
        
        .significance {
            font-weight: bold;
        }
        
        .sig-001 {
            color: #e74c3c;
        }
        
        .sig-01 {
            color: #f39c12;
        }
        
        .sig-05 {
            color: #f1c40f;
        }
        
        .sig-ns {
            color: #95a5a6;
        }
        
        .additional-info {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        
        .additional-info h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        
        .additional-info p {
            margin: 5px 0;
        }
    </style>"""
    
    def _format_test_info(self) -> str:
        """Format basic test information."""
        test_name = self.data.get('test_name', 'Statistical Test')
        test_type = self.data.get('test_type', 'unknown')
        
        info_items = []
        
        # Add sample size if available
        sample_size = self.data.get('sample_size')
        if sample_size:
            if isinstance(sample_size, dict):
                for key, value in sample_size.items():
                    info_items.append(f'<div class="info-item"><span class="info-label">Sample Size ({key}):</span> <span class="info-value">{value}</span></div>')
            else:
                info_items.append(f'<div class="info-item"><span class="info-label">Sample Size:</span> <span class="info-value">{sample_size}</span></div>')
        
        # Add degrees of freedom if available
        df = self.data.get('degrees_of_freedom')
        if df is not None:
            if isinstance(df, dict):
                for key, value in df.items():
                    info_items.append(f'<div class="info-item"><span class="info-label">Degrees of Freedom ({key}):</span> <span class="info-value">{value}</span></div>')
            else:
                info_items.append(f'<div class="info-item"><span class="info-label">Degrees of Freedom:</span> <span class="info-value">{df}</span></div>')
        
        if info_items:
            return f'<div class="info-grid">{"".join(info_items)}</div>'
        return ""
    
    def _format_main_table(self) -> str:
        """Format the main results table."""
        html_parts = ['<h2>Results</h2>']
        html_parts.append('<table>')
        html_parts.append('    <thead>')
        html_parts.append('        <tr>')
        html_parts.append('            <th>Statistic</th>')
        html_parts.append('            <th>Value</th>')
        html_parts.append('            <th>p-value</th>')
        html_parts.append('            <th>Significance</th>')
        html_parts.append('        </tr>')
        html_parts.append('    </thead>')
        html_parts.append('    <tbody>')
        
        statistic = self.data.get('statistic')
        p_value = self.data.get('p_value')
        
        if statistic is not None and p_value is not None:
            if isinstance(statistic, dict):
                for key, value in statistic.items():
                    p_val = p_value.get(key.replace('stat_', 'p_'), p_value) if isinstance(p_value, dict) else p_value
                    significance_class = self._get_significance_class(p_val)
                    significance_text = self._get_significance_text(p_val)
                    
                    html_parts.append('        <tr>')
                    html_parts.append(f'            <td>{key.replace("stat_", "").title()}</td>')
                    html_parts.append(f'            <td>{value:.3f}</td>')
                    html_parts.append(f'            <td>{format_p_value(p_val)}</td>')
                    html_parts.append(f'            <td class="significance {significance_class}">{significance_text}</td>')
                    html_parts.append('        </tr>')
            else:
                significance_class = self._get_significance_class(p_value)
                significance_text = self._get_significance_text(p_value)
                
                html_parts.append('        <tr>')
                html_parts.append('            <td>Test Statistic</td>')
                html_parts.append(f'            <td>{statistic:.3f}</td>')
                html_parts.append(f'            <td>{format_p_value(p_value)}</td>')
                html_parts.append(f'            <td class="significance {significance_class}">{significance_text}</td>')
                html_parts.append('        </tr>')
        
        # Add effect size if available
        effect_size = self.data.get('effect_size')
        if effect_size is not None:
            if isinstance(effect_size, dict):
                for key, value in effect_size.items():
                    html_parts.append('        <tr>')
                    html_parts.append(f'            <td>{key.replace("_", " ").title()}</td>')
                    html_parts.append(f'            <td>{value:.3f}</td>')
                    html_parts.append('            <td>-</td>')
                    html_parts.append('            <td>-</td>')
                    html_parts.append('        </tr>')
            else:
                html_parts.append('        <tr>')
                html_parts.append('            <td>Effect Size</td>')
                html_parts.append(f'            <td>{effect_size:.3f}</td>')
                html_parts.append('            <td>-</td>')
                html_parts.append('            <td>-</td>')
                html_parts.append('        </tr>')
        
        # Add confidence interval if available
        ci = self.data.get('confidence_interval')
        if ci is not None:
            if isinstance(ci, dict) and 'lower' in ci and 'upper' in ci:
                ci_str = format_confidence_interval(ci['lower'], ci['upper'])
                html_parts.append('        <tr>')
                html_parts.append('            <td>95% CI</td>')
                html_parts.append(f'            <td>{ci_str}</td>')
                html_parts.append('            <td>-</td>')
                html_parts.append('            <td>-</td>')
                html_parts.append('        </tr>')
        
        html_parts.append('    </tbody>')
        html_parts.append('</table>')
        
        return '\n'.join(html_parts)
    
    def _format_coefficients_table(self) -> str:
        """Format coefficients table for regression models."""
        coefficients = self.data.get('coefficients', [])
        if not coefficients:
            return ""
        
        html_parts = ['<h2>Coefficients</h2>']
        html_parts.append('<table>')
        html_parts.append('    <thead>')
        html_parts.append('        <tr>')
        html_parts.append('            <th>Variable</th>')
        html_parts.append('            <th>Coefficient</th>')
        html_parts.append('            <th>SE</th>')
        html_parts.append('            <th>p-value</th>')
        html_parts.append('            <th>95% CI</th>')
        html_parts.append('        </tr>')
        html_parts.append('    </thead>')
        html_parts.append('    <tbody>')
        
        for coef in coefficients:
            variable = coef.get('variable', 'Unknown')
            coefficient = coef.get('coefficient', 0)
            std_error = coef.get('std_error')
            p_value = coef.get('p_value')
            ci_lower = coef.get('ci_lower')
            ci_upper = coef.get('ci_upper')
            
            # Format values
            coef_str = f"{coefficient:.3f}"
            se_str = f"{std_error:.3f}" if std_error is not None else "-"
            p_str = format_p_value(p_value) if p_value is not None else "-"
            ci_str = format_confidence_interval(ci_lower, ci_upper) if ci_lower is not None and ci_upper is not None else "-"
            
            html_parts.append('        <tr>')
            html_parts.append(f'            <td>{variable}</td>')
            html_parts.append(f'            <td>{coef_str}</td>')
            html_parts.append(f'            <td>{se_str}</td>')
            html_parts.append(f'            <td>{p_str}</td>')
            html_parts.append(f'            <td>{ci_str}</td>')
            html_parts.append('        </tr>')
        
        html_parts.append('    </tbody>')
        html_parts.append('</table>')
        
        return '\n'.join(html_parts)
    
    def _format_model_info(self) -> str:
        """Format model information."""
        model_info = self.data.get('model_info', {})
        if not model_info:
            return ""
        
        html_parts = ['<h2>Model Information</h2>']
        html_parts.append('<table>')
        html_parts.append('    <thead>')
        html_parts.append('        <tr>')
        html_parts.append('            <th>Statistic</th>')
        html_parts.append('            <th>Value</th>')
        html_parts.append('        </tr>')
        html_parts.append('    </thead>')
        html_parts.append('    <tbody>')
        
        for key, value in model_info.items():
            if isinstance(value, (int, float)):
                html_parts.append('        <tr>')
                html_parts.append(f'            <td>{key.replace("_", " ").title()}</td>')
                html_parts.append(f'            <td>{value:.3f}</td>')
                html_parts.append('        </tr>')
        
        html_parts.append('    </tbody>')
        html_parts.append('</table>')
        
        return '\n'.join(html_parts)
    
    def _format_additional_info(self) -> str:
        """Format additional information."""
        additional_info = self.data.get('additional_info', {})
        if not additional_info:
            return ""
        
        html_parts = ['<div class="additional-info">']
        html_parts.append('    <h3>Additional Information</h3>')
        
        for key, value in additional_info.items():
            if isinstance(value, (str, int, float, bool)):
                html_parts.append(f'    <p><strong>{key.replace("_", " ").title()}:</strong> {value}</p>')
            elif isinstance(value, list):
                html_parts.append(f'    <p><strong>{key.replace("_", " ").title()}:</strong> {", ".join(map(str, value))}</p>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _get_significance_class(self, p_value: float) -> str:
        """Get CSS class for significance level."""
        if p_value < 0.001:
            return "sig-001"
        elif p_value < 0.01:
            return "sig-01"
        elif p_value < 0.05:
            return "sig-05"
        else:
            return "sig-ns"
    
    def _get_significance_text(self, p_value: float) -> str:
        """Get significance text."""
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        else:
            return "ns"
    
    def to_string(self) -> str:
        """Convert to string representation."""
        return self.export()
    
    def __str__(self) -> str:
        """String representation."""
        return self.to_string()
