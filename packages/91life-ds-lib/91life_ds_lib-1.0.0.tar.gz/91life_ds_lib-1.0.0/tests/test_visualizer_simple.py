"""
Simple tests for Visualizer class - testing actual methods that exist
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from ninetyone_life_ds.visualization.plotter import Visualizer
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestVisualizerSimple:
    """Simple test cases for Visualizer"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric_1': np.random.normal(100, 15, 100),
            'numeric_2': np.random.exponential(2, 100),
            'numeric_3': np.random.uniform(0, 100, 100),
            'categorical_1': np.random.choice(['A', 'B', 'C'], 100),
            'categorical_2': np.random.choice(['X', 'Y'], 100),
            'target': np.random.choice([0, 1], 100)
        })
        
        # Add some missing values
        data.loc[0:10, 'numeric_1'] = np.nan
        data.loc[20:25, 'categorical_1'] = np.nan
        
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
    def test_create_interactive_plot(self, mock_show, visualizer, sample_data):
        """Test interactive plot creation"""
        visualizer.create_interactive_plot(
            sample_data,
            plot_type='scatter',
            x='numeric_1',
            y='numeric_2'
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

    def test_export_plots(self, visualizer, sample_data):
        """Test plot export functionality"""
        with patch('matplotlib.pyplot.savefig') as mock_savefig:
            visualizer.export_plots(
                sample_data,
                output_dir='test_output',
                formats=['png', 'pdf']
            )
            mock_savefig.assert_called()

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
            visualizer.plot_data_quality_summary(categorical_df)

    def test_no_categorical_columns(self, visualizer):
        """Test handling of dataframe with no categorical columns"""
        numeric_df = pd.DataFrame({
            'num1': [1, 2, 3, 4, 5],
            'num2': [6, 7, 8, 9, 10]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_distributions(numeric_df)

    def test_invalid_columns(self, visualizer, sample_data):
        """Test handling of invalid columns"""
        with pytest.raises(ValueError):
            visualizer.plot_distributions(sample_data, columns=['nonexistent_col'])

    def test_invalid_correlation_method(self, visualizer, sample_data):
        """Test handling of invalid correlation method"""
        with pytest.raises(ValueError):
            visualizer.plot_correlations(sample_data, method='invalid')

    def test_feature_importance_empty_dict(self, visualizer):
        """Test handling of empty feature importance dictionary"""
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_feature_importance({})

    def test_feature_importance_invalid_data(self, visualizer):
        """Test handling of invalid feature importance data"""
        with pytest.raises(ValueError):
            visualizer.plot_feature_importance("invalid_data")

    def test_export_plots_invalid_format(self, visualizer, sample_data):
        """Test export plots with invalid format"""
        with pytest.raises(ValueError):
            visualizer.export_plots(
                sample_data,
                output_dir='test_output',
                formats=['invalid_format']
            )

    def test_create_interactive_plot_invalid_type(self, visualizer, sample_data):
        """Test create interactive plot with invalid type"""
        with pytest.raises(ValueError):
            visualizer.create_interactive_plot(
                sample_data,
                plot_type='invalid_type',
                x='numeric_1',
                y='numeric_2'
            )

    def test_create_interactive_plot_missing_columns(self, visualizer, sample_data):
        """Test create interactive plot with missing columns"""
        with pytest.raises(ValueError):
            visualizer.create_interactive_plot(
                sample_data,
                plot_type='scatter',
                x='nonexistent_col',
                y='numeric_2'
            )

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

    def test_plot_with_mixed_data_types(self, visualizer, sample_data):
        """Test plotting with mixed data types"""
        with patch('matplotlib.pyplot.show'):
            visualizer.create_dashboard(sample_data)

    def test_plot_with_large_dataset(self, visualizer):
        """Test plotting with large dataset"""
        # Create a larger dataset
        large_data = pd.DataFrame({
            'col1': np.random.normal(0, 1, 1000),
            'col2': np.random.exponential(1, 1000),
            'col3': np.random.choice(['A', 'B', 'C'], 1000)
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_distributions(large_data)

    def test_plot_with_datetime_columns(self, visualizer):
        """Test plotting with datetime columns"""
        datetime_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'value': np.random.normal(100, 10, 100)
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_distributions(datetime_data)

    def test_plot_with_boolean_columns(self, visualizer):
        """Test plotting with boolean columns"""
        boolean_data = pd.DataFrame({
            'bool_col': [True, False, True, False, True],
            'value': [1, 2, 3, 4, 5]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_data_quality_summary(boolean_data)

    def test_plot_with_special_characters(self, visualizer):
        """Test plotting with special characters in data"""
        special_data = pd.DataFrame({
            'special_col': ['@#$%', '&*()', '!@#', '$%^', '&*()'],
            'normal_col': [1, 2, 3, 4, 5]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_data_quality_summary(special_data)

    def test_plot_with_unicode_characters(self, visualizer):
        """Test plotting with unicode characters"""
        unicode_data = pd.DataFrame({
            'unicode_col': ['αβγ', 'δεζ', 'ηθι', 'κλμ', 'νξο'],
            'normal_col': [1, 2, 3, 4, 5]
        })
        
        with patch('matplotlib.pyplot.show'):
            visualizer.plot_data_quality_summary(unicode_data)
