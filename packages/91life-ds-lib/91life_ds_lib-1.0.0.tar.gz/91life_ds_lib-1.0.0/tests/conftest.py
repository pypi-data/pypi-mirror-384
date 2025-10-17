"""
Pytest configuration and fixtures for 91life Data Science Library tests
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os


@pytest.fixture
def sample_data():
    """Create sample dataset for testing"""
    np.random.seed(42)

    # Create a realistic dataset with various data types and patterns
    n_samples = 1000

    data = {
        # Numeric features
        "feature_1": np.random.normal(100, 15, n_samples),
        "feature_2": np.random.exponential(2, n_samples),
        "feature_3": np.random.uniform(0, 100, n_samples),
        "feature_4": np.random.poisson(5, n_samples),
        "feature_5": np.random.gamma(2, 2, n_samples),
        # Categorical features
        "category_1": np.random.choice(["A", "B", "C", "D"], n_samples),
        "category_2": np.random.choice(["X", "Y", "Z"], n_samples),
        "binary_feature": np.random.choice([0, 1], n_samples),
        # Target variable (regression)
        "target_regression": np.random.normal(50, 10, n_samples),
        # Target variable (classification)
        "target_classification": np.random.choice(
            [0, 1, 2], n_samples, p=[0.5, 0.3, 0.2]
        ),
    }

    df = pd.DataFrame(data)

    # Add some missing values
    df.loc[np.random.choice(df.index, 50), "feature_1"] = np.nan
    df.loc[np.random.choice(df.index, 30), "category_1"] = np.nan

    # Add some outliers
    df.loc[np.random.choice(df.index, 10), "feature_2"] = df["feature_2"].max() * 3

    return df


@pytest.fixture
def large_sample_data():
    """Create larger sample dataset for performance testing"""
    np.random.seed(42)

    n_samples = 10000
    n_features = 50

    # Create numeric features
    data = {}
    for i in range(n_features):
        data[f"feature_{i}"] = np.random.normal(0, 1, n_samples)

    # Add target
    data["target"] = np.random.choice([0, 1], n_samples)

    df = pd.DataFrame(data)

    # Add missing values
    missing_indices = np.random.choice(df.index, 1000, replace=False)
    df.loc[missing_indices, "feature_0"] = np.nan

    return df


@pytest.fixture
def test_data_path(sample_data):
    """Create temporary CSV file with test data"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_data.to_csv(f.name, index=False)
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def test_parquet_path(sample_data):
    """Create temporary Parquet file with test data"""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        sample_data.to_parquet(f.name, index=False)
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def test_json_path(sample_data):
    """Create temporary JSON file with test data"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        sample_data.to_json(f.name, orient="records", indent=2)
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def test_excel_path(sample_data):
    """Create temporary Excel file with test data"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        sample_data.to_excel(f.name, index=False)
        yield f.name

    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def regression_data():
    """Create regression dataset"""
    np.random.seed(42)

    n_samples = 500
    X = np.random.randn(n_samples, 10)
    y = X[:, 0] + 2 * X[:, 1] + np.random.randn(n_samples) * 0.1

    feature_names = [f"feature_{i}" for i in range(10)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y

    return df


@pytest.fixture
def classification_data():
    """Create classification dataset"""
    np.random.seed(42)

    n_samples = 500
    n_features = 8

    # Create features with different importance levels
    X = np.random.randn(n_samples, n_features)

    # Create target with some relationship to features
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y

    return df


@pytest.fixture
def imbalanced_data():
    """Create imbalanced classification dataset"""
    np.random.seed(42)

    n_samples = 1000
    n_features = 5

    X = np.random.randn(n_samples, n_features)

    # Create imbalanced target (90% class 0, 10% class 1)
    y = np.random.choice([0, 1], n_samples, p=[0.9, 0.1])

    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y

    return df


@pytest.fixture
def high_dimensional_data():
    """Create high-dimensional dataset"""
    np.random.seed(42)

    n_samples = 200
    n_features = 100

    X = np.random.randn(n_samples, n_features)
    y = np.random.choice([0, 1], n_samples)

    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y

    return df


@pytest.fixture
def missing_data():
    """Create dataset with various missing data patterns"""
    np.random.seed(42)

    n_samples = 1000
    n_features = 10

    X = np.random.randn(n_samples, n_features)

    # Add different missing patterns
    # Random missing
    missing_indices = np.random.choice(n_samples, 100, replace=False)
    X[missing_indices, 0] = np.nan

    # Block missing (consecutive rows)
    X[200:250, 1] = np.nan

    # High missing percentage
    missing_indices = np.random.choice(n_samples, 800, replace=False)
    X[missing_indices, 2] = np.nan

    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = np.random.choice([0, 1], n_samples)

    return df


@pytest.fixture
def outlier_data():
    """Create dataset with outliers"""
    np.random.seed(42)

    n_samples = 1000
    n_features = 5

    X = np.random.randn(n_samples, n_features)

    # Add outliers
    X[0:10, 0] = X[:, 0].max() * 5  # Extreme outliers
    X[10:20, 1] = X[:, 1].min() * 3  # Negative outliers

    feature_names = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = np.random.choice([0, 1], n_samples)

    return df


@pytest.fixture
def categorical_data():
    """Create dataset with categorical features"""
    np.random.seed(42)

    n_samples = 1000

    data = {
        "numeric_1": np.random.normal(0, 1, n_samples),
        "numeric_2": np.random.exponential(1, n_samples),
        "categorical_1": np.random.choice(["A", "B", "C"], n_samples),
        "categorical_2": np.random.choice(["X", "Y"], n_samples),
        "ordinal_1": np.random.choice([1, 2, 3, 4, 5], n_samples),
        "binary_1": np.random.choice([0, 1], n_samples),
        "high_cardinality": np.random.choice(
            [f"cat_{i}" for i in range(50)], n_samples
        ),
        "target": np.random.choice([0, 1], n_samples),
    }

    return pd.DataFrame(data)


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "cloud: Cloud storage tests")
    config.addinivalue_line("markers", "profiling: Profiling tests")
