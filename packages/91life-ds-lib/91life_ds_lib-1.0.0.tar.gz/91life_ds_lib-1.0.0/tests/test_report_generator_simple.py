"""
Simple tests for ReportGenerator class - testing actual methods that exist
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock
from ninetyone_life_ds.reports.generator import ReportGenerator
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestReportGeneratorSimple:
    """Simple test cases for ReportGenerator"""

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
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def report_generator(self, temp_dir):
        """Create ReportGenerator instance"""
        return ReportGenerator(output_dir=temp_dir)

    def test_initialization(self, temp_dir):
        """Test ReportGenerator initialization"""
        generator = ReportGenerator(output_dir=temp_dir)
        assert generator.output_dir == temp_dir
        assert hasattr(generator, 'logger')

    def test_initialization_default_output_dir(self):
        """Test ReportGenerator initialization with default output directory"""
        generator = ReportGenerator()
        assert generator.output_dir == 'reports'

    @patch('ydata_profiling.ProfileReport')
    def test_generate_ydata_profiling_report(self, mock_profile_report, report_generator, sample_data):
        """Test YData profiling report generation"""
        mock_report = MagicMock()
        mock_report.to_file.return_value = None
        mock_profile_report.return_value = mock_report
        
        result = report_generator.generate_ydata_profiling_report(sample_data)
        
        assert result is not None
        assert isinstance(result, str)
        mock_profile_report.assert_called_once()
        mock_report.to_file.assert_called_once()

    @patch('ydata_profiling.ProfileReport')
    def test_generate_ydata_profiling_report_custom_params(self, mock_profile_report, report_generator, sample_data):
        """Test YData profiling report generation with custom parameters"""
        mock_report = MagicMock()
        mock_report.to_file.return_value = None
        mock_profile_report.return_value = mock_report
        
        result = report_generator.generate_ydata_profiling_report(
            sample_data,
            title="Custom YData Report",
            minimal=True
        )
        
        assert result is not None
        assert isinstance(result, str)

    @patch('sweetviz.analyze')
    def test_generate_sweetviz_report(self, mock_analyze, report_generator, sample_data):
        """Test Sweetviz report generation"""
        mock_report = MagicMock()
        mock_report.show_html.return_value = None
        mock_analyze.return_value = mock_report
        
        result = report_generator.generate_sweetviz_report(sample_data)
        
        assert result is not None
        assert isinstance(result, str)
        mock_analyze.assert_called_once()
        mock_report.show_html.assert_called_once()

    @patch('sweetviz.analyze')
    def test_generate_sweetviz_report_with_target(self, mock_analyze, report_generator, sample_data):
        """Test Sweetviz report generation with target column"""
        mock_report = MagicMock()
        mock_report.show_html.return_value = None
        mock_analyze.return_value = mock_report
        
        result = report_generator.generate_sweetviz_report(
            sample_data,
            target_col='target'
        )
        
        assert result is not None
        assert isinstance(result, str)

    def test_generate_comprehensive_analysis_report(self, report_generator, sample_data):
        """Test comprehensive analysis report generation"""
        result = report_generator.generate_comprehensive_analysis_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_generate_comprehensive_analysis_report_custom_params(self, report_generator, sample_data):
        """Test comprehensive analysis report generation with custom parameters"""
        result = report_generator.generate_comprehensive_analysis_report(
            sample_data,
            dataset_name="Custom Dataset",
            include_plots=True
        )
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_generate_automated_profiling_reports(self, report_generator, sample_data):
        """Test automated profiling reports generation"""
        result = report_generator.generate_automated_profiling_reports(sample_data)
        
        assert isinstance(result, dict)
        assert 'ydata_report' in result
        assert 'sweetviz_report' in result
        assert 'comprehensive_report' in result

    def test_generate_automated_profiling_reports_custom_params(self, report_generator, sample_data):
        """Test automated profiling reports generation with custom parameters"""
        result = report_generator.generate_automated_profiling_reports(
            sample_data,
            include_ydata=True,
            include_sweetviz=True,
            include_comprehensive=True
        )
        
        assert isinstance(result, dict)
        assert 'ydata_report' in result
        assert 'sweetviz_report' in result
        assert 'comprehensive_report' in result

    def test_create_custom_report(self, report_generator, sample_data):
        """Test custom report creation"""
        result = report_generator.create_custom_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_create_custom_report_custom_params(self, report_generator, sample_data):
        """Test custom report creation with custom parameters"""
        result = report_generator.create_custom_report(
            sample_data,
            dataset_name="Custom Dataset",
            include_plots=True,
            include_statistical_tests=True
        )
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_empty_dataframe(self, report_generator):
        """Test handling of empty dataframe"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(DataValidationError):
            report_generator.create_custom_report(empty_df)

    def test_single_column_dataframe(self, report_generator):
        """Test handling of single column dataframe"""
        single_col_df = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
        
        result = report_generator.create_custom_report(single_col_df)
        assert isinstance(result, dict)

    def test_constant_column_dataframe(self, report_generator):
        """Test handling of constant column dataframe"""
        constant_df = pd.DataFrame({
            'constant': [1, 1, 1, 1, 1],
            'variable': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.create_custom_report(constant_df)
        assert isinstance(result, dict)

    def test_all_missing_column(self, report_generator):
        """Test handling of all missing column"""
        all_missing_df = pd.DataFrame({
            'all_missing': [np.nan, np.nan, np.nan, np.nan, np.nan],
            'normal': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.create_custom_report(all_missing_df)
        assert isinstance(result, dict)

    def test_create_output_directory(self, temp_dir):
        """Test creation of output directory"""
        new_dir = os.path.join(temp_dir, 'new_reports')
        generator = ReportGenerator(output_dir=new_dir)
        
        # Directory should be created
        assert os.path.exists(new_dir)

    def test_generate_report_with_large_dataset(self, report_generator):
        """Test report generation with large dataset"""
        # Create a larger dataset
        large_data = pd.DataFrame({
            'col1': np.random.normal(0, 1, 1000),
            'col2': np.random.exponential(1, 1000),
            'col3': np.random.choice(['A', 'B', 'C'], 1000)
        })
        
        result = report_generator.create_custom_report(large_data)
        assert isinstance(result, dict)

    def test_generate_report_with_mixed_data_types(self, report_generator, sample_data):
        """Test report generation with mixed data types"""
        result = report_generator.create_custom_report(sample_data)
        assert isinstance(result, dict)
        assert 'dataset_info' in result

    def test_generate_report_with_datetime_columns(self, report_generator):
        """Test report generation with datetime columns"""
        datetime_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'value': np.random.normal(100, 10, 100)
        })
        
        result = report_generator.create_custom_report(datetime_data)
        assert isinstance(result, dict)

    def test_generate_report_with_boolean_columns(self, report_generator):
        """Test report generation with boolean columns"""
        boolean_data = pd.DataFrame({
            'bool_col': [True, False, True, False, True],
            'value': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.create_custom_report(boolean_data)
        assert isinstance(result, dict)

    def test_generate_report_with_duplicate_columns(self, report_generator):
        """Test report generation with duplicate columns"""
        duplicate_data = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col1': [6, 7, 8, 9, 10]  # This will create a duplicate column name
        })
        
        result = report_generator.create_custom_report(duplicate_data)
        assert isinstance(result, dict)

    def test_generate_report_with_special_characters(self, report_generator):
        """Test report generation with special characters in data"""
        special_data = pd.DataFrame({
            'special_col': ['@#$%', '&*()', '!@#', '$%^', '&*()'],
            'normal_col': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.create_custom_report(special_data)
        assert isinstance(result, dict)

    def test_generate_report_with_unicode_characters(self, report_generator):
        """Test report generation with unicode characters"""
        unicode_data = pd.DataFrame({
            'unicode_col': ['αβγ', 'δεζ', 'ηθι', 'κλμ', 'νξο'],
            'normal_col': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.create_custom_report(unicode_data)
        assert isinstance(result, dict)

    def test_generate_multiple_reports(self, report_generator, sample_data):
        """Test generation of multiple reports"""
        ydata_report = report_generator.generate_ydata_profiling_report(sample_data)
        sweetviz_report = report_generator.generate_sweetviz_report(sample_data)
        comprehensive_report = report_generator.generate_comprehensive_analysis_report(sample_data)
        
        assert ydata_report is not None
        assert sweetviz_report is not None
        assert isinstance(comprehensive_report, dict)

    def test_generate_automated_reports_with_missing_target(self, report_generator, sample_data):
        """Test automated reports generation with missing target column"""
        result = report_generator.generate_automated_profiling_reports(
            sample_data,
            target_col='nonexistent_target'
        )
        
        assert isinstance(result, dict)

    def test_create_custom_report_with_missing_target(self, report_generator, sample_data):
        """Test custom report creation with missing target column"""
        result = report_generator.create_custom_report(
            sample_data,
            target_column='nonexistent_target'
        )
        
        assert isinstance(result, dict)

    def test_generate_comprehensive_report_with_missing_target(self, report_generator, sample_data):
        """Test comprehensive report generation with missing target column"""
        result = report_generator.generate_comprehensive_analysis_report(
            sample_data,
            target_column='nonexistent_target'
        )
        
        assert isinstance(result, dict)

    def test_generate_ydata_report_with_missing_target(self, report_generator, sample_data):
        """Test YData report generation with missing target column"""
        with patch('ydata_profiling.ProfileReport') as mock_profile_report:
            mock_report = MagicMock()
            mock_report.to_file.return_value = None
            mock_profile_report.return_value = mock_report
            
            result = report_generator.generate_ydata_profiling_report(
                sample_data,
                target_col='nonexistent_target'
            )
            
            assert result is not None
            assert isinstance(result, str)

    def test_generate_sweetviz_report_with_missing_target(self, report_generator, sample_data):
        """Test Sweetviz report generation with missing target column"""
        with patch('sweetviz.analyze') as mock_analyze:
            mock_report = MagicMock()
            mock_report.show_html.return_value = None
            mock_analyze.return_value = mock_report
            
            result = report_generator.generate_sweetviz_report(
                sample_data,
                target_col='nonexistent_target'
            )
            
            assert result is not None
            assert isinstance(result, str)
