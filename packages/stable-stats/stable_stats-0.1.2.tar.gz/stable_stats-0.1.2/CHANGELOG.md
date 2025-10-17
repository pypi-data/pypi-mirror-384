# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of the Stable package
- Support for scipy.stats statistical tests (t-tests, ANOVA, chi-square, etc.)
- Support for statsmodels regression results
- Multiple export formats: Markdown, Excel, HTML, pandas DataFrame
- Automatic test type detection
- Pretty formatting with significance stars and confidence intervals
- Class methods for direct statistical analysis
- Comprehensive documentation and examples

### Features
- **Adapters**: ScipyAdapter and StatsmodelsAdapter for input handling
- **Exporters**: MarkdownExporter, ExcelExporter, HTMLExporter for output formatting
- **Core**: Stable class with intuitive API
- **Utils**: Helper functions for formatting and validation

## [0.1.0] - 2024-01-XX

### Added
- Initial release
- Basic statistical test support
- Export to multiple formats
- Documentation and examples
