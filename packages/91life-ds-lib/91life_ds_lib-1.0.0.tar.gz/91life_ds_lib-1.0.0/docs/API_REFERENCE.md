# API Reference

## Overview

The 91life Data Science Library provides a comprehensive set of tools for data analysis, feature selection, preprocessing, visualization, and reporting. This document provides detailed API reference for all public classes and methods.

## Core Modules

### DataLoader

The `DataLoader` class provides efficient data loading capabilities with support for multiple formats and cloud storage.

#### Constructor

```python
DataLoader(chunk_size: int = 100000, memory_limit: float = 0.8, max_workers: int = 4)
```

**Parameters:**
- `chunk_size` (int): Size of chunks for large file processing (default: 100000)
- `memory_limit` (float): Memory usage limit as fraction of total memory (default: 0.8)
- `max_workers` (int): Maximum number of worker threads (default: 4)

#### Methods

##### `load_dataset(file_path: str, format: Optional[str] = None, **kwargs) -> pd.DataFrame`

Load a dataset from various sources and formats.

**Parameters:**
- `file_path` (str): Path to the data file or cloud storage URI
- `format` (Optional[str]): File format ('csv', 'parquet', 'json', 'excel', 'txt')
- `**kwargs`: Additional parameters passed to the specific loader

**Returns:**
- `pd.DataFrame`: Loaded dataset

**Example:**
```python
loader = DataLoader()
data = loader.load_dataset('data.csv')
cloud_data = loader.load_dataset('s3://bucket/data.parquet')
```

##### `load_csv(file_path: str, **kwargs) -> pd.DataFrame`

Load CSV file with customizable parameters.

**Parameters:**
- `file_path` (str): Path to CSV file
- `**kwargs`: Additional pandas.read_csv parameters

**Returns:**
- `pd.DataFrame`: Loaded CSV data

##### `load_parquet(file_path: str, **kwargs) -> pd.DataFrame`

Load Parquet file.

**Parameters:**
- `file_path` (str): Path to Parquet file
- `**kwargs`: Additional pandas.read_parquet parameters

**Returns:**
- `pd.DataFrame`: Loaded Parquet data

##### `load_json(file_path: str, **kwargs) -> pd.DataFrame`

Load JSON file.

**Parameters:**
- `file_path` (str): Path to JSON file
- `**kwargs`: Additional pandas.read_json parameters

**Returns:**
- `pd.DataFrame`: Loaded JSON data

##### `load_excel(file_path: str, **kwargs) -> pd.DataFrame`

Load Excel file.

**Parameters:**
- `file_path` (str): Path to Excel file
- `**kwargs`: Additional pandas.read_excel parameters

**Returns:**
- `pd.DataFrame`: Loaded Excel data

### DataExplorer

The `DataExplorer` class provides comprehensive data exploration and quality assessment capabilities.

#### Constructor

```python
DataExplorer(sample_size: int = 10)
```

**Parameters:**
- `sample_size` (int): Number of columns to sample for detailed analysis (default: 10)

#### Methods

##### `analyze_basic_info(data: pd.DataFrame) -> Dict[str, Any]`

Analyze basic information about the dataset.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `shape`: Dataset dimensions
  - `total_rows`: Number of rows
  - `total_columns`: Number of columns
  - `memory_usage_mb`: Memory usage in MB
  - `completeness_ratio`: Ratio of non-null values
  - `duplicate_rows`: Number of duplicate rows

**Example:**
```python
explorer = DataExplorer()
info = explorer.analyze_basic_info(data)
print(f"Dataset shape: {info['shape']}")
print(f"Memory usage: {info['memory_usage_mb']:.2f} MB")
```

##### `analyze_missing_data(data: pd.DataFrame, threshold: float = 0.1) -> Dict[str, Any]`

Analyze missing data patterns and provide recommendations.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `threshold` (float): Threshold for missing data percentage (default: 0.1)

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `total_missing`: Total number of missing values
  - `missing_percentage`: Percentage of missing values
  - `missing_by_column`: Missing data per column
  - `recommendations`: List of recommendations

##### `analyze_statistical_patterns(data: pd.DataFrame, sample_cols: Optional[int] = None) -> Dict[str, Any]`

Analyze statistical patterns in numeric columns.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `sample_cols` (Optional[int]): Number of columns to sample

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `descriptive_stats`: Descriptive statistics
  - `correlation_matrix`: Correlation matrix
  - `skewness`: Skewness values
  - `kurtosis`: Kurtosis values
  - `normality_tests`: Normality test results

##### `calculate_data_readiness_score(data: pd.DataFrame) -> Dict[str, Any]`

Calculate a comprehensive data readiness score for machine learning.

**Parameters:**
- `data` (pd.DataFrame): Input dataset

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `overall_readiness`: Overall readiness score (0-100)
  - `readiness_level`: Readiness level category
  - `is_ready_for_ml`: Boolean indicating ML readiness
  - `recommendations`: List of improvement recommendations

### FeatureSelector

The `FeatureSelector` class provides advanced feature selection capabilities using multiple algorithms.

#### Constructor

```python
FeatureSelector(random_state: int = 42)
```

**Parameters:**
- `random_state` (int): Random seed for reproducibility (default: 42)

#### Methods

##### `select_variance_threshold(data: pd.DataFrame, threshold: float = 0.01, exclude_cols: Optional[List[str]] = None) -> Dict[str, Any]`

Select features based on variance threshold.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `threshold` (float): Variance threshold (default: 0.01)
- `exclude_cols` (Optional[List[str]]): Columns to exclude from selection

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `selected_features`: List of selected feature names
  - `removed_features`: List of removed feature names
  - `method`: Selection method used

##### `select_correlation_based(data: pd.DataFrame, threshold: float = 0.8, exclude_cols: Optional[List[str]] = None) -> Dict[str, Any]`

Select features based on correlation analysis.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `threshold` (float): Correlation threshold (default: 0.8)
- `exclude_cols` (Optional[List[str]]): Columns to exclude from selection

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `selected_features`: List of selected feature names
  - `high_correlations`: List of high correlation pairs
  - `method`: Selection method used

##### `select_mutual_information(data: pd.DataFrame, target_col: str, task_type: str = 'classification', k: int = 10) -> Dict[str, Any]`

Select features based on mutual information.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `target_col` (str): Target column name
- `task_type` (str): Task type ('classification' or 'regression')
- `k` (int): Number of features to select

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `selected_features`: List of selected feature names
  - `scores`: Mutual information scores
  - `method`: Selection method used

##### `consensus_feature_selection(data: pd.DataFrame, target_col: Optional[str] = None, methods: Optional[List[str]] = None, task_type: str = 'classification') -> Dict[str, Any]`

Perform consensus feature selection using multiple methods.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `target_col` (Optional[str]): Target column name
- `methods` (Optional[List[str]]): List of methods to use
- `task_type` (str): Task type ('classification' or 'regression')

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `selected_features`: List of selected feature names
  - `consensus_score`: Consensus score
  - `methods_used`: List of methods used
  - `method`: Selection method used

### DataPreprocessor

The `DataPreprocessor` class provides comprehensive data preprocessing capabilities.

#### Constructor

```python
DataPreprocessor(random_state: int = 42)
```

**Parameters:**
- `random_state` (int): Random seed for reproducibility (default: 42)

#### Methods

##### `handle_missing_values(data: pd.DataFrame, strategy: str = 'auto', **kwargs) -> pd.DataFrame`

Handle missing values in the dataset.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `strategy` (str): Missing value handling strategy
- `**kwargs`: Additional parameters

**Returns:**
- `pd.DataFrame`: Dataset with missing values handled

##### `detect_outliers(data: pd.DataFrame, method: str = 'iqr', **kwargs) -> Dict[str, Any]`

Detect outliers in the dataset.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `method` (str): Outlier detection method
- `**kwargs`: Additional parameters

**Returns:**
- `Dict[str, Any]`: Dictionary containing outlier information

##### `scale_features(data: pd.DataFrame, method: str = 'standard', **kwargs) -> pd.DataFrame`

Scale features in the dataset.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `method` (str): Scaling method
- `**kwargs`: Additional parameters

**Returns:**
- `pd.DataFrame`: Dataset with scaled features

### Visualizer

The `Visualizer` class provides comprehensive data visualization capabilities.

#### Constructor

```python
Visualizer(figsize: Tuple[int, int] = (12, 8), style: str = 'whitegrid')
```

**Parameters:**
- `figsize` (Tuple[int, int]): Figure size (default: (12, 8))
- `style` (str): Matplotlib style (default: 'whitegrid')

#### Methods

##### `plot_missing_data(data: pd.DataFrame, **kwargs) -> None`

Create missing data visualization.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `**kwargs`: Additional plotting parameters

##### `plot_distributions(data: pd.DataFrame, columns: Optional[List[str]] = None, **kwargs) -> None`

Create distribution plots for numeric columns.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `columns` (Optional[List[str]]): Columns to plot
- `**kwargs`: Additional plotting parameters

##### `plot_correlations(data: pd.DataFrame, method: str = 'pearson', **kwargs) -> None`

Create correlation heatmap.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `method` (str): Correlation method
- `**kwargs`: Additional plotting parameters

### ReportGenerator

The `ReportGenerator` class provides automated report generation capabilities.

#### Constructor

```python
ReportGenerator(output_dir: str = 'reports')
```

**Parameters:**
- `output_dir` (str): Output directory for reports (default: 'reports')

#### Methods

##### `generate_ydata_report(data: pd.DataFrame, title: str = 'Data Profiling Report', **kwargs) -> str`

Generate YData profiling report.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `title` (str): Report title
- `**kwargs`: Additional parameters

**Returns:**
- `str`: Path to generated report

##### `generate_sweetviz_report(data: pd.DataFrame, target_col: Optional[str] = None, **kwargs) -> str`

Generate Sweetviz report.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `target_col` (Optional[str]): Target column name
- `**kwargs`: Additional parameters

**Returns:**
- `str`: Path to generated report

##### `generate_custom_report(data: pd.DataFrame, dataset_name: str = 'Dataset', **kwargs) -> Dict[str, Any]`

Generate custom analysis report.

**Parameters:**
- `data` (pd.DataFrame): Input dataset
- `dataset_name` (str): Dataset name
- `**kwargs`: Additional parameters

**Returns:**
- `Dict[str, Any]`: Dictionary containing report data

## Error Handling

The library provides comprehensive error handling through custom exceptions:

### DataValidationError

Raised when data validation fails.

```python
from ninetyone_life_ds.core.exceptions import DataValidationError
```

### FeatureSelectionError

Raised when feature selection fails.

```python
from ninetyone_life_ds.core.exceptions import FeatureSelectionError
```

### DataLoadingError

Raised when data loading fails.

```python
from ninetyone_life_ds.core.exceptions import DataLoadingError
```

## Configuration

The library uses Pydantic for configuration management:

```python
from ninetyone_life_ds.core.config import Config

config = Config()
```

Configuration can be customized through environment variables or by modifying the config object.

## Logging

All classes inherit from `LoggerMixin` and provide comprehensive logging:

```python
from ninetyone_life_ds.core.logger import LoggerMixin

class MyClass(LoggerMixin):
    def __init__(self):
        self.logger.info("Initialized")
```

## Examples

### Complete Workflow Example

```python
from ninetyone_life_ds import DataLoader, DataExplorer, FeatureSelector, Visualizer

# Load data
loader = DataLoader()
data = loader.load_dataset('data.csv')

# Explore data
explorer = DataExplorer()
basic_info = explorer.analyze_basic_info(data)
missing_analysis = explorer.analyze_missing_data(data)
readiness_score = explorer.calculate_data_readiness_score(data)

# Select features
selector = FeatureSelector()
selected_features = selector.consensus_feature_selection(
    data, 
    target_col='target',
    task_type='classification'
)

# Visualize results
visualizer = Visualizer()
visualizer.plot_missing_data(data)
visualizer.plot_distributions(data)
visualizer.plot_correlations(data)

print(f"Data readiness: {readiness_score['overall_readiness']}/100")
print(f"Selected features: {len(selected_features['selected_features'])}")
```

### Cloud Storage Example

```python
from ninetyone_life_ds import DataLoader

# Load from AWS S3
loader = DataLoader()
s3_data = loader.load_dataset('s3://my-bucket/data.parquet')

# Load from Google Cloud Storage
gcs_data = loader.load_dataset('gs://my-bucket/data.csv')

# Load from MinIO
minio_data = loader.load_dataset('s3://minio-bucket/data.json')
```

### Feature Selection Example

```python
from ninetyone_life_ds import FeatureSelector

selector = FeatureSelector()

# Variance-based selection
variance_result = selector.select_variance_threshold(data, threshold=0.01)

# Correlation-based selection
correlation_result = selector.select_correlation_based(data, threshold=0.8)

# Mutual information selection
mi_result = selector.select_mutual_information(
    data, 
    target_col='target',
    task_type='classification',
    k=10
)

# Consensus selection
consensus_result = selector.consensus_feature_selection(
    data,
    target_col='target',
    methods=['variance', 'correlation', 'mutual_info'],
    task_type='classification'
)
```

## Performance Considerations

- Use chunked loading for large datasets
- Configure memory limits appropriately
- Use sampling for exploratory analysis
- Enable parallel processing where available
- Monitor memory usage during processing

## Best Practices

1. **Data Loading**: Use appropriate chunk sizes for large datasets
2. **Feature Selection**: Combine multiple methods for robust selection
3. **Visualization**: Use appropriate plot types for data types
4. **Error Handling**: Always handle exceptions appropriately
5. **Logging**: Enable logging for debugging and monitoring
6. **Configuration**: Use environment variables for sensitive settings
