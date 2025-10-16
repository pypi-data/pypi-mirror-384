# Stable

A Python package for beautifying statistical outputs from scipy, statsmodels, and other libraries into clean, publication-ready tables.

## Features

- **Automatic Detection**: Recognizes common statistical tests (t-tests, ANOVA, chi-square, regression, etc.)
- **Multiple Export Formats**: Markdown, Excel, HTML, and pandas DataFrame
- **Pretty Formatting**: Rounded decimals, significance stars, confidence intervals
- **Flexible Input**: Works with scipy.stats and statsmodels results
- **Easy to Use**: Simple API with methods like `.to_markdown()`, `.to_excel()`

## Installation

### From PyPI (recommended)

```bash
pip install stable-stats
```

### From source

```bash
git clone https://github.com/Chris-R030307/StaTable.git
cd StaTable
pip install -e .
```

### Development installation

```bash
git clone https://github.com/Chris-R030307/StaTable.git
cd StaTable
pip install -e ".[dev,test]"
```

### Dependencies

The package requires:
- Python 3.7+
- numpy >= 1.19.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- statsmodels >= 0.12.0
- openpyxl >= 3.0.0 (for Excel export)

## Quick Start

```python
from scipy import stats
from stable import Stable

# Run a statistical test
result = stats.ttest_ind(group1, group2)

# Beautify the results
table = Stable(result)

# Export to different formats
print(table.to_markdown())  # Pretty table in console
table.to_excel("results.xlsx")  # Export to Excel
html_output = table.to_html()  # Get HTML string
```

## Examples

### T-test

```python
import numpy as np
from scipy import stats
from stable import Stable

# Generate sample data
np.random.seed(42)
group1 = np.random.normal(100, 15, 30)
group2 = np.random.normal(110, 15, 30)

# Run t-test
result = stats.ttest_ind(group1, group2)

# Beautify
stable = Stable(result)
print(stable.to_markdown())
```

Output:
```markdown
## Independent t-test

**Sample Size:** 30

## Results

| Statistic | Value | p-value | Significance |
|-----------|-------|---------|--------------|
| Test Statistic | -2.108 | 0.039* | * |

Effect Size: -2.108
```

### ANOVA

```python
# Generate data for 3 groups
group_a = np.random.normal(50, 10, 25)
group_b = np.random.normal(55, 10, 25)
group_c = np.random.normal(60, 10, 25)

# Run ANOVA
result = stats.f_oneway(group_a, group_b, group_c)

# Beautify
stable = Stable(result)
print(stable.to_markdown())
```

### Linear Regression

```python
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Generate sample data
x = np.random.normal(0, 1, 100)
y = 2 * x + np.random.normal(0, 0.5, 100)
df = pd.DataFrame({'x': x, 'y': y})

# Run regression
model = ols('y ~ x', data=df).fit()

# Beautify
stable = Stable(model)
print(stable.to_markdown())
```

### Direct Analysis Methods

```python
# Direct t-test
stable = Stable.from_ttest(group1, group2)

# Direct ANOVA
stable = Stable.from_anova(group_a, group_b, group_c)

# Direct chi-square
observed = [20, 30, 25, 25]
expected = [25, 25, 25, 25]
stable = Stable.from_chi2(observed, expected)
```

## Supported Statistical Tests

### Scipy.stats
- t-tests (independent, paired, one-sample)
- ANOVA (one-way)
- Chi-square tests
- Kolmogorov-Smirnov tests
- Mann-Whitney U test
- Wilcoxon signed-rank test
- Kruskal-Wallis test
- Friedman test

### Statsmodels
- Linear regression
- ANOVA
- t-tests
- F-tests
- Contrast tests

## Export Formats

### Markdown
```python
markdown_output = stable.to_markdown(title="My Analysis")
print(markdown_output)
```

### Excel
```python
stable.to_excel("results.xlsx", sheet_name="Analysis")
```

### HTML
```python
html_output = stable.to_html(title="My Analysis", include_css=True)
```

### Pandas DataFrame
```python
df = stable.to_dataframe()
```

## API Reference

### Stable Class

#### Methods

- `to_markdown(title=None)`: Export to Markdown format
- `to_excel(filename, sheet_name="Statistical Results")`: Export to Excel
- `to_html(title=None, include_css=True)`: Export to HTML
- `to_dataframe()`: Export to pandas DataFrame
- `summary()`: Get brief summary of results
- `is_supported()`: Check if result type is supported

#### Properties

- `get_test_name()`: Get human-readable test name
- `get_statistic()`: Get test statistic(s)
- `get_p_value()`: Get p-value(s)
- `get_effect_size()`: Get effect size(s)
- `get_confidence_interval()`: Get confidence interval
- `get_sample_size()`: Get sample size information
- `get_degrees_of_freedom()`: Get degrees of freedom
- `get_coefficients()`: Get coefficient information (regression)
- `get_model_info()`: Get model information (regression)

#### Class Methods

- `Stable.from_ttest(group1, group2, **kwargs)`: Direct t-test
- `Stable.from_anova(*groups, **kwargs)`: Direct ANOVA
- `Stable.from_chi2(observed, expected=None, **kwargs)`: Direct chi-square
- `Stable.from_regression(model_result)`: From regression result

## Package Structure

```
stable/
├── __init__.py              # Main package interface
├── core.py                  # Core Stable class
├── utils.py                 # Helper functions
├── adapters/                # Input adapters
│   ├── scipy_adapter.py     # Scipy.stats adapter
│   └── statsmodels_adapter.py # Statsmodels adapter
└── exporters/               # Output exporters
    ├── markdown.py          # Markdown exporter
    ├── excel.py             # Excel exporter
    └── html.py              # HTML exporter
```

## Requirements

- Python 3.7+
- numpy >= 1.19.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- statsmodels >= 0.12.0
- openpyxl >= 3.0.0 (for Excel export)

## Development

### Setup Development Environment

```bash
git clone <repository-url>
cd stable
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Example

```bash
python example_usage.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Future Features

- Support for more statistical libraries (pingouin, sklearn)
- Interactive tables (Plotly dashboards)
- Custom templates (APA style, clinical reports)
- LaTeX export
- More effect size calculations
- Power analysis integration
