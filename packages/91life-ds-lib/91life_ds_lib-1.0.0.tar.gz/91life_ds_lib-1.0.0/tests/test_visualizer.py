"""
Tests for Visualizer class
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from ninetyone_life_ds.visualization.plotter import Visualizer
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestVisualizer:
    """Test cases for Visualizer"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric_1': np.random.normal(100, 15, 1000),
            'numeric_2': np.random.exponential(2, 1000),
            'numeric_3': np.random.uniform(0, 100, 1000),
            'categorical_1': np.random.choice(['A', 'B', 'C'], 1000),
            'categorical_2': np.random.choice(['X', 'Y'], 1000),
            'target': np.random.choice([0, 1], 1000)
        })
        
        # Add some missing values
        data.loc[0:50, 'numeric_1'] = np.nan
        data.loc[100:120, 'categorical_1'] = np.nan
        
        return data

    @pytest.fixture
    def visualizer(self):
        """Create Visualizer instance"""
        return Visualizer()

    def test_initialization(self):
        """Test Visualizer initialization"""
        visualizer = Visualizer()
        assert visualizer.figsize == (12, 8)
        assert visualizer.style == 'whitegrid'
        assert hasattr(visualizer, 'logger')

    def test_initialization_custom_params(self):
        """Test Visualizer initialization with custom parameters"""
        visualizer = Visualizer(figsize=(10, 6), style='darkgrid')
        assert visualizer.figsize == (10, 6)
        assert visualizer.style == 'darkgrid'

    @patch('matplotlib.pyplot.show')
    def test_plot_missing_data(self, mock_show, visualizer, sample_data):
        """Test missing data visualization"""
        visualizer.plot_missing_data(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_missing_data_custom_params(self, mock_show, visualizer, sample_data):
        """Test missing data visualization with custom parameters"""
        visualizer.plot_missing_data(
            sample_data,
            figsize=(10, 6),
            title="Custom Missing Data Plot"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_distributions(self, mock_show, visualizer, sample_data):
        """Test distribution plots"""
        visualizer.plot_distributions(sample_data, columns=['numeric_1', 'numeric_2'])
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_distributions_all_numeric(self, mock_show, visualizer, sample_data):
        """Test distribution plots for all numeric columns"""
        visualizer.plot_distributions(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_distributions_custom_params(self, mock_show, visualizer, sample_data):
        """Test distribution plots with custom parameters"""
        visualizer.plot_distributions(
            sample_data,
            columns=['numeric_1'],
            bins=20,
            kde=True
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_correlations(self, mock_show, visualizer, sample_data):
        """Test correlation heatmap"""
        visualizer.plot_correlations(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_correlations_custom_params(self, mock_show, visualizer, sample_data):
        """Test correlation heatmap with custom parameters"""
        visualizer.plot_correlations(
            sample_data,
            method='spearman',
            figsize=(10, 8),
            title="Custom Correlation Plot"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_boxplots(self, mock_show, visualizer, sample_data):
        """Test boxplot visualization"""
        visualizer.plot_boxplots(sample_data, columns=['numeric_1', 'numeric_2'])
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_boxplots_all_numeric(self, mock_show, visualizer, sample_data):
        """Test boxplot visualization for all numeric columns"""
        visualizer.plot_boxplots(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_scatter_matrix(self, mock_show, visualizer, sample_data):
        """Test scatter matrix plot"""
        visualizer.plot_scatter_matrix(sample_data, columns=['numeric_1', 'numeric_2', 'numeric_3'])
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_scatter_matrix_custom_params(self, mock_show, visualizer, sample_data):
        """Test scatter matrix plot with custom parameters"""
        visualizer.plot_scatter_matrix(
            sample_data,
            columns=['numeric_1', 'numeric_2'],
            alpha=0.6,
            figsize=(10, 10)
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_categorical_counts(self, mock_show, visualizer, sample_data):
        """Test categorical counts visualization"""
        visualizer.plot_categorical_counts(sample_data, columns=['categorical_1', 'categorical_2'])
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_categorical_counts_all_categorical(self, mock_show, visualizer, sample_data):
        """Test categorical counts visualization for all categorical columns"""
        visualizer.plot_categorical_counts(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_categorical_counts_custom_params(self, mock_show, visualizer, sample_data):
        """Test categorical counts visualization with custom parameters"""
        visualizer.plot_categorical_counts(
            sample_data,
            columns=['categorical_1'],
            figsize=(8, 6),
            title="Custom Categorical Plot"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_target_distribution(self, mock_show, visualizer, sample_data):
        """Test target distribution visualization"""
        visualizer.plot_target_distribution(sample_data, target_col='target')
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_target_distribution_custom_params(self, mock_show, visualizer, sample_data):
        """Test target distribution visualization with custom parameters"""
        visualizer.plot_target_distribution(
            sample_data,
            target_col='target',
            figsize=(10, 6),
            title="Custom Target Distribution"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_feature_importance(self, mock_show, visualizer, sample_data):
        """Test feature importance visualization"""
        # Create mock feature importance data
        feature_importance = {
            'numeric_1': 0.3,
            'numeric_2': 0.25,
            'numeric_3': 0.2,
            'categorical_1': 0.15,
            'categorical_2': 0.1
        }
        
        visualizer.plot_feature_importance(feature_importance)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_feature_importance_custom_params(self, mock_show, visualizer, sample_data):
        """Test feature importance visualization with custom parameters"""
        feature_importance = {
            'numeric_1': 0.3,
            'numeric_2': 0.25,
            'numeric_3': 0.2
        }
        
        visualizer.plot_feature_importance(
            feature_importance,
            top_n=5,
            figsize=(10, 6),
            title="Custom Feature Importance"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_data_quality_summary(self, mock_show, visualizer, sample_data):
        """Test data quality summary visualization"""
        visualizer.plot_data_quality_summary(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_data_quality_summary_custom_params(self, mock_show, visualizer, sample_data):
        """Test data quality summary visualization with custom parameters"""
        visualizer.plot_data_quality_summary(
            sample_data,
            figsize=(12, 8),
            title="Custom Data Quality Summary"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_outliers(self, mock_show, visualizer, sample_data):
        """Test outlier visualization"""
        visualizer.plot_outliers(sample_data, columns=['numeric_1', 'numeric_2'])
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_outliers_custom_params(self, mock_show, visualizer, sample_data):
        """Test outlier visualization with custom parameters"""
        visualizer.plot_outliers(
            sample_data,
            columns=['numeric_1'],
            method='iqr',
            figsize=(10, 6)
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_time_series(self, mock_show, visualizer):
        """Test time series visualization"""
        # Create time series data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        ts_data = pd.DataFrame({
            'date': dates,
            'value': np.random.normal(100, 10, 100)
        })
        
        visualizer.plot_time_series(ts_data, x_col='date', y_col='value')
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_time_series_custom_params(self, mock_show, visualizer):
        """Test time series visualization with custom parameters"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        ts_data = pd.DataFrame({
            'date': dates,
            'value': np.random.normal(100, 10, 100)
        })
        
        visualizer.plot_time_series(
            ts_data,
            x_col='date',
            y_col='value',
            figsize=(12, 6),
            title="Custom Time Series"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_heatmap(self, mock_show, visualizer, sample_data):
        """Test heatmap visualization"""
        visualizer.plot_heatmap(sample_data[['numeric_1', 'numeric_2', 'numeric_3']])
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_heatmap_custom_params(self, mock_show, visualizer, sample_data):
        """Test heatmap visualization with custom parameters"""
        visualizer.plot_heatmap(
            sample_data[['numeric_1', 'numeric_2']],
            figsize=(8, 6),
            title="Custom Heatmap"
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_pairwise_relationships(self, mock_show, visualizer, sample_data):
        """Test pairwise relationships visualization"""
        visualizer.plot_pairwise_relationships(
            sample_data,
            columns=['numeric_1', 'numeric_2', 'numeric_3']
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_pairwise_relationships_custom_params(self, mock_show, visualizer, sample_data):
        """Test pairwise relationships visualization with custom parameters"""
        visualizer.plot_pairwise_relationships(
            sample_data,
            columns=['numeric_1', 'numeric_2'],
            kind='reg',
            figsize=(10, 8)
        )
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_create_dashboard(self, mock_show, visualizer, sample_data):
        """Test dashboard creation"""
        visualizer.create_dashboard(sample_data)
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_create_dashboard_custom_params(self, mock_show, visualizer, sample_data):
        """Test dashboard creation with custom parameters"""
        visualizer.create_dashboard(
            sample_data,
            figsize=(16, 12),
            title="Custom Dashboard"
        )
        mock_show.assert_called_once()

    def test_empty_dataframe(self, visualizer):
        """Test handling of empty dataframe"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(DataValidationError):
            visualizer.plot_missing_data(empty_df)

    def test_single_column_dataframe(self, visualizer):
        """Test handling of single column dataframe"""
        single_col_df = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_distributions(single_col_df)

    def test_constant_column_dataframe(self, visualizer):
        """Test handling of constant column dataframe"""
        constant_df = pd.DataFrame({
            'constant': [1, 1, 1, 1, 1],
            'variable': [1, 2, 3, 4, 5]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_distributions(constant_df)

    def test_no_numeric_columns(self, visualizer):
        """Test handling of dataframe with no numeric columns"""
        categorical_df = pd.DataFrame({
            'cat1': ['A', 'B', 'C'],
            'cat2': ['X', 'Y', 'Z']
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_categorical_counts(categorical_df)

    def test_no_categorical_columns(self, visualizer):
        """Test handling of dataframe with no categorical columns"""
        numeric_df = pd.DataFrame({
            'num1': [1, 2, 3, 4, 5],
            'num2': [6, 7, 8, 9, 10]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_distributions(numeric_df)

    def test_missing_target_column(self, visualizer, sample_data):
        """Test handling of missing target column"""
        with pytest.raises(ValueError):
            visualizer.plot_target_distribution(sample_data, target_col='nonexistent')

    def test_invalid_columns(self, visualizer, sample_data):
        """Test handling of invalid columns"""
        with pytest.raises(ValueError):
            visualizer.plot_distributions(sample_data, columns=['nonexistent_col'])

    def test_invalid_correlation_method(self, visualizer, sample_data):
        """Test handling of invalid correlation method"""
        with pytest.raises(ValueError):
            visualizer.plot_correlations(sample_data, method='invalid')

    def test_invalid_outlier_method(self, visualizer, sample_data):
        """Test handling of invalid outlier method"""
        with pytest.raises(ValueError):
            visualizer.plot_outliers(sample_data, method='invalid')

    def test_invalid_pairwise_kind(self, visualizer, sample_data):
        """Test handling of invalid pairwise kind"""
        with pytest.raises(ValueError):
            visualizer.plot_pairwise_relationships(
                sample_data,
                columns=['numeric_1', 'numeric_2'],
                kind='invalid'
            )

    def test_feature_importance_empty_dict(self, visualizer):
        """Test handling of empty feature importance dictionary"""
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_feature_importance({})

    def test_feature_importance_invalid_data(self, visualizer):
        """Test handling of invalid feature importance data"""
        with pytest.raises(ValueError):
            visualizer.plot_feature_importance("invalid_data")

    def test_time_series_missing_columns(self, visualizer):
        """Test handling of missing time series columns"""
        ts_data = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        
        with pytest.raises(ValueError):
            visualizer.plot_time_series(ts_data, x_col='date', y_col='value')

    def test_heatmap_empty_dataframe(self, visualizer):
        """Test handling of empty dataframe for heatmap"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(DataValidationError):
            visualizer.plot_heatmap(empty_df)

    def test_scatter_matrix_insufficient_columns(self, visualizer, sample_data):
        """Test handling of insufficient columns for scatter matrix"""
        with pytest.raises(ValueError):
            visualizer.plot_scatter_matrix(sample_data, columns=['numeric_1'])

    def test_boxplot_insufficient_data(self, visualizer):
        """Test handling of insufficient data for boxplot"""
        small_df = pd.DataFrame({'col1': [1, 2]})
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_boxplots(small_df)

    def test_categorical_counts_with_numeric_data(self, visualizer):
        """Test categorical counts with numeric data"""
        numeric_df = pd.DataFrame({
            'num1': [1, 2, 3, 4, 5],
            'num2': [6, 7, 8, 9, 10]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_categorical_counts(numeric_df)

    def test_outlier_plot_with_no_outliers(self, visualizer):
        """Test outlier plot with no outliers"""
        normal_df = pd.DataFrame({
            'normal': np.random.normal(0, 1, 100)
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_outliers(normal_df, columns=['normal'])

    def test_dashboard_with_mixed_data_types(self, visualizer, sample_data):
        """Test dashboard creation with mixed data types"""
        with patch('matplotlib.pyplot.show'):
            visualizer.create_dashboard(sample_data)

    def test_plot_with_custom_style(self):
        """Test plotting with custom style"""
        visualizer = Visualizer(style='darkgrid')
        
        with patch('matplotlib.pyplot.show'):
            sample_data = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
            visualizer.plot_distributions(sample_data)

    def test_plot_with_custom_figsize(self):
        """Test plotting with custom figure size"""
        visualizer = Visualizer(figsize=(10, 6))
        
        with patch('matplotlib.pyplot.show'):
            sample_data = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
            visualizer.plot_distributions(sample_data)
