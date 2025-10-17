# 91life Data Science Library

<div align="center">
  <img src="https://cdn.prod.website-files.com/6464fc5c49a35f360e272b62/6638ee51fb46dea59b4a71c4_Group%201000004653.svg" alt="91.life Logo" width="400"/>
</div>

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-91Life-green.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/91life-ds-lib.svg)](https://pypi.org/project/91life-ds-lib/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://91life-ds-lib.readthedocs.io/)
[![Build Status](https://img.shields.io/github/workflow/status/91life/91life-ds-lib/CI)](https://github.com/91life/91life-ds-lib/actions)
[![Coverage](https://img.shields.io/codecov/c/github/91life/91life-ds-lib)](https://codecov.io/gh/91life/91life-ds-lib)

## Overview

The 91life Data Science Library is a professional, production-ready Python library designed for ML engineers and researchers at [91.life](https://91.life). It provides comprehensive tools for data loading, exploration, feature selection, preprocessing, visualization, and automated reporting.

### Key Features

- **Async Data Loading**: Support for multiple formats (CSV, Parquet, JSON, Excel) with cloud storage integration (AWS S3, Google Cloud, MinIO)
- **Comprehensive Data Exploration**: Automated data quality assessment, missing data analysis, and statistical profiling
- **Advanced Feature Selection**: Multiple methods including variance, correlation, mutual information, tree-based, L1 regularization, and consensus selection
- **Data Preprocessing**: Complete pipeline for missing value handling, outlier treatment, scaling, encoding, and class imbalance
- **Rich Visualizations**: Interactive plots with Plotly, static plots with Matplotlib/Seaborn, and automated dashboards
- **Automated Reporting**: Integration with YData Profiling and Sweetviz, plus custom HTML/JSON reports
- **Clean Architecture**: Domain-Driven Design (DDD) patterns with comprehensive logging and error handling
- **Performance Optimized**: Memory-efficient chunked processing for large datasets

## Installation

### Basic Installation

```bash
pip install 91life-ds-lib
```

### With Cloud Storage Support

```bash
pip install 91life-ds-lib[cloud]
```

### With Profiling Tools

```bash
pip install 91life-ds-lib[profiling]
```

### Development Installation

```bash
git clone https://github.com/91life/91life-ds-lib.git
cd 91life-ds-lib
pip install -e ".[dev]"
```

## Quickstart

```python
from ninetyone_life_ds import DataLoader, DataExplorer, FeatureSelector

# Load data efficiently
loader = DataLoader()
data = loader.load_dataset('your_data.csv')

# Explore data comprehensively
explorer = DataExplorer()
basic_info = explorer.analyze_basic_info(data)
missing_analysis = explorer.analyze_missing_data(data)
readiness_score = explorer.calculate_data_readiness_score(data)

# Select features using consensus method
selector = FeatureSelector()
selected_features = selector.consensus_feature_selection(
    data, 
    target_col='target',
    task_type='classification'
)

print(f"Data readiness: {readiness_score['overall_readiness']}/100")
print(f"Selected features: {len(selected_features['selected_features'])}")
```

## Full Example

See `examples/complete_workflow.py` for a comprehensive demonstration of all library capabilities.

## API Overview

### Core Modules

- **DataLoader**: Efficient data loading with cloud storage support
- **DataExplorer**: Comprehensive data exploration and quality assessment
- **FeatureSelector**: Advanced feature selection with multiple algorithms
- **DataPreprocessor**: Complete preprocessing pipeline
- **Visualizer**: Rich visualizations and interactive plots
- **ReportGenerator**: Automated report generation and profiling

### Main Classes

- `DataLoader`: Handles data loading from various sources and formats
- `DataExplorer`: Performs comprehensive data analysis and quality assessment
- `FeatureSelector`: Implements multiple feature selection algorithms
- `DataPreprocessor`: Provides complete data preprocessing pipeline
- `Visualizer`: Creates professional visualizations and plots
- `ReportGenerator`: Generates comprehensive analysis reports

## Development Setup

### Prerequisites

- Python 3.8+
- pip or conda

### Setup

```bash
# Clone repository
git clone https://github.com/91life/91life-ds-lib.git
cd 91life-ds-lib

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 src/ tests/

# Format code
black src/ tests/

# Type checking
mypy src/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ninetyone_life_ds --cov-report=html

# Run specific test file
pytest tests/test_data_explorer.py -v
```

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && flake8 src/ tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write comprehensive docstrings (Google style)
- Ensure all tests pass
- Maintain test coverage above 90%

## License

This project is licensed under the 91Life License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Company**: [91.life](https://91.life)
- **Author**: Shpat Dobraj
- **Email**: shpatdobraj@91.life
- **Issues**: [GitHub Issues](https://github.com/91life/91life-ds-lib/issues)

## Company Insights

91.life is a technology company focused on data science and machine learning solutions. The company provides professional tools and services for data analysis, with a focus on healthcare and life sciences applications.

For more information about 91.life's services and team, visit [https://91.life](https://91.life).