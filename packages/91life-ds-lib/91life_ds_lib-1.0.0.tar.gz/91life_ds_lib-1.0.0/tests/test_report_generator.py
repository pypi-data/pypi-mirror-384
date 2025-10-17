"""
Tests for ReportGenerator class
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock
from ninetyone_life_ds.reports.generator import ReportGenerator
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestReportGenerator:
    """Test cases for ReportGenerator"""

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
    def test_generate_ydata_report(self, mock_profile_report, report_generator, sample_data):
        """Test YData profiling report generation"""
        mock_report = MagicMock()
        mock_report.to_file.return_value = None
        mock_profile_report.return_value = mock_report
        
        result = report_generator.generate_ydata_report(sample_data)
        
        assert result is not None
        assert isinstance(result, str)
        mock_profile_report.assert_called_once()
        mock_report.to_file.assert_called_once()

    @patch('ydata_profiling.ProfileReport')
    def test_generate_ydata_report_custom_params(self, mock_profile_report, report_generator, sample_data):
        """Test YData profiling report generation with custom parameters"""
        mock_report = MagicMock()
        mock_report.to_file.return_value = None
        mock_profile_report.return_value = mock_report
        
        result = report_generator.generate_ydata_report(
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

    def test_generate_custom_report(self, report_generator, sample_data):
        """Test custom report generation"""
        result = report_generator.generate_custom_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_generate_custom_report_custom_params(self, report_generator, sample_data):
        """Test custom report generation with custom parameters"""
        result = report_generator.generate_custom_report(
            sample_data,
            dataset_name="Custom Dataset",
            include_plots=True
        )
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_generate_html_report(self, report_generator, sample_data):
        """Test HTML report generation"""
        result = report_generator.generate_html_report(sample_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('.html')

    def test_generate_html_report_custom_params(self, report_generator, sample_data):
        """Test HTML report generation with custom parameters"""
        result = report_generator.generate_html_report(
            sample_data,
            title="Custom HTML Report",
            template="default"
        )
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('.html')

    def test_generate_json_report(self, report_generator, sample_data):
        """Test JSON report generation"""
        result = report_generator.generate_json_report(sample_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('.json')

    def test_generate_json_report_custom_params(self, report_generator, sample_data):
        """Test JSON report generation with custom parameters"""
        result = report_generator.generate_json_report(
            sample_data,
            filename="custom_report.json"
        )
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('.json')

    def test_generate_summary_report(self, report_generator, sample_data):
        """Test summary report generation"""
        result = report_generator.generate_summary_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'overview' in result
        assert 'data_quality_score' in result
        assert 'key_insights' in result
        assert 'recommendations' in result

    def test_generate_summary_report_custom_params(self, report_generator, sample_data):
        """Test summary report generation with custom parameters"""
        result = report_generator.generate_summary_report(
            sample_data,
            include_statistics=True,
            include_plots=False
        )
        
        assert isinstance(result, dict)
        assert 'overview' in result
        assert 'data_quality_score' in result
        assert 'key_insights' in result
        assert 'recommendations' in result

    def test_generate_comparison_report(self, report_generator, sample_data):
        """Test comparison report generation"""
        # Create a second dataset for comparison
        sample_data_2 = sample_data.copy()
        sample_data_2['numeric_1'] = sample_data_2['numeric_1'] * 1.1
        
        result = report_generator.generate_comparison_report(
            sample_data,
            sample_data_2,
            dataset_names=['Dataset 1', 'Dataset 2']
        )
        
        assert isinstance(result, dict)
        assert 'comparison_summary' in result
        assert 'differences' in result
        assert 'recommendations' in result

    def test_generate_comparison_report_custom_params(self, report_generator, sample_data):
        """Test comparison report generation with custom parameters"""
        sample_data_2 = sample_data.copy()
        sample_data_2['numeric_1'] = sample_data_2['numeric_1'] * 1.1
        
        result = report_generator.generate_comparison_report(
            sample_data,
            sample_data_2,
            dataset_names=['Dataset 1', 'Dataset 2'],
            include_statistical_tests=True
        )
        
        assert isinstance(result, dict)
        assert 'comparison_summary' in result
        assert 'differences' in result
        assert 'recommendations' in result

    def test_generate_executive_summary(self, report_generator, sample_data):
        """Test executive summary generation"""
        result = report_generator.generate_executive_summary(sample_data)
        
        assert isinstance(result, dict)
        assert 'executive_summary' in result
        assert 'key_findings' in result
        assert 'business_impact' in result
        assert 'next_steps' in result

    def test_generate_executive_summary_custom_params(self, report_generator, sample_data):
        """Test executive summary generation with custom parameters"""
        result = report_generator.generate_executive_summary(
            sample_data,
            audience='technical',
            include_recommendations=True
        )
        
        assert isinstance(result, dict)
        assert 'executive_summary' in result
        assert 'key_findings' in result
        assert 'business_impact' in result
        assert 'next_steps' in result

    def test_generate_data_dictionary(self, report_generator, sample_data):
        """Test data dictionary generation"""
        result = report_generator.generate_data_dictionary(sample_data)
        
        assert isinstance(result, dict)
        assert 'columns' in result
        assert 'data_types' in result
        assert 'descriptions' in result

    def test_generate_data_dictionary_custom_params(self, report_generator, sample_data):
        """Test data dictionary generation with custom parameters"""
        custom_descriptions = {
            'numeric_1': 'First numeric feature',
            'categorical_1': 'First categorical feature'
        }
        
        result = report_generator.generate_data_dictionary(
            sample_data,
            custom_descriptions=custom_descriptions
        )
        
        assert isinstance(result, dict)
        assert 'columns' in result
        assert 'data_types' in result
        assert 'descriptions' in result

    def test_generate_quality_assessment(self, report_generator, sample_data):
        """Test quality assessment generation"""
        result = report_generator.generate_quality_assessment(sample_data)
        
        assert isinstance(result, dict)
        assert 'quality_score' in result
        assert 'issues' in result
        assert 'recommendations' in result

    def test_generate_quality_assessment_custom_params(self, report_generator, sample_data):
        """Test quality assessment generation with custom parameters"""
        result = report_generator.generate_quality_assessment(
            sample_data,
            include_detailed_analysis=True
        )
        
        assert isinstance(result, dict)
        assert 'quality_score' in result
        assert 'issues' in result
        assert 'recommendations' in result

    def test_generate_statistical_report(self, report_generator, sample_data):
        """Test statistical report generation"""
        result = report_generator.generate_statistical_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'descriptive_statistics' in result
        assert 'correlations' in result
        assert 'distributions' in result

    def test_generate_statistical_report_custom_params(self, report_generator, sample_data):
        """Test statistical report generation with custom parameters"""
        result = report_generator.generate_statistical_report(
            sample_data,
            include_hypothesis_tests=True
        )
        
        assert isinstance(result, dict)
        assert 'descriptive_statistics' in result
        assert 'correlations' in result
        assert 'distributions' in result

    def test_generate_ml_readiness_report(self, report_generator, sample_data):
        """Test ML readiness report generation"""
        result = report_generator.generate_ml_readiness_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'readiness_score' in result
        assert 'data_quality' in result
        assert 'feature_engineering' in result
        assert 'recommendations' in result

    def test_generate_ml_readiness_report_custom_params(self, report_generator, sample_data):
        """Test ML readiness report generation with custom parameters"""
        result = report_generator.generate_ml_readiness_report(
            sample_data,
            target_column='target',
            task_type='classification'
        )
        
        assert isinstance(result, dict)
        assert 'readiness_score' in result
        assert 'data_quality' in result
        assert 'feature_engineering' in result
        assert 'recommendations' in result

    def test_generate_comprehensive_report(self, report_generator, sample_data):
        """Test comprehensive report generation"""
        result = report_generator.generate_comprehensive_report(sample_data)
        
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        assert 'data_quality' in result
        assert 'statistical_summary' in result
        assert 'recommendations' in result

    def test_generate_comprehensive_report_custom_params(self, report_generator, sample_data):
        """Test comprehensive report generation with custom parameters"""
        result = report_generator.generate_comprehensive_report(
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
            report_generator.generate_custom_report(empty_df)

    def test_single_column_dataframe(self, report_generator):
        """Test handling of single column dataframe"""
        single_col_df = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
        
        result = report_generator.generate_custom_report(single_col_df)
        assert isinstance(result, dict)

    def test_constant_column_dataframe(self, report_generator):
        """Test handling of constant column dataframe"""
        constant_df = pd.DataFrame({
            'constant': [1, 1, 1, 1, 1],
            'variable': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.generate_custom_report(constant_df)
        assert isinstance(result, dict)

    def test_all_missing_column(self, report_generator):
        """Test handling of all missing column"""
        all_missing_df = pd.DataFrame({
            'all_missing': [np.nan, np.nan, np.nan, np.nan, np.nan],
            'normal': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.generate_custom_report(all_missing_df)
        assert isinstance(result, dict)

    def test_missing_target_column(self, report_generator, sample_data):
        """Test handling of missing target column"""
        with pytest.raises(ValueError):
            report_generator.generate_ml_readiness_report(
                sample_data,
                target_column='nonexistent'
            )

    def test_invalid_output_directory(self):
        """Test handling of invalid output directory"""
        with pytest.raises(ValueError):
            ReportGenerator(output_dir='/invalid/path/that/does/not/exist')

    def test_create_output_directory(self, temp_dir):
        """Test creation of output directory"""
        new_dir = os.path.join(temp_dir, 'new_reports')
        generator = ReportGenerator(output_dir=new_dir)
        
        # Directory should be created
        assert os.path.exists(new_dir)

    def test_generate_report_with_custom_filename(self, report_generator, sample_data):
        """Test report generation with custom filename"""
        result = report_generator.generate_html_report(
            sample_data,
            filename="custom_report.html"
        )
        
        assert result is not None
        assert "custom_report.html" in result

    def test_generate_report_with_timestamp(self, report_generator, sample_data):
        """Test report generation with timestamp"""
        result = report_generator.generate_json_report(sample_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('.json')

    def test_generate_multiple_reports(self, report_generator, sample_data):
        """Test generation of multiple reports"""
        html_report = report_generator.generate_html_report(sample_data)
        json_report = report_generator.generate_json_report(sample_data)
        summary_report = report_generator.generate_summary_report(sample_data)
        
        assert html_report is not None
        assert json_report is not None
        assert isinstance(summary_report, dict)

    def test_generate_report_with_large_dataset(self, report_generator):
        """Test report generation with large dataset"""
        # Create a larger dataset
        large_data = pd.DataFrame({
            'col1': np.random.normal(0, 1, 10000),
            'col2': np.random.exponential(1, 10000),
            'col3': np.random.choice(['A', 'B', 'C'], 10000)
        })
        
        result = report_generator.generate_custom_report(large_data)
        assert isinstance(result, dict)

    def test_generate_report_with_mixed_data_types(self, report_generator, sample_data):
        """Test report generation with mixed data types"""
        result = report_generator.generate_custom_report(sample_data)
        assert isinstance(result, dict)
        assert 'dataset_info' in result

    def test_generate_report_with_datetime_columns(self, report_generator):
        """Test report generation with datetime columns"""
        datetime_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'value': np.random.normal(100, 10, 100)
        })
        
        result = report_generator.generate_custom_report(datetime_data)
        assert isinstance(result, dict)

    def test_generate_report_with_boolean_columns(self, report_generator):
        """Test report generation with boolean columns"""
        boolean_data = pd.DataFrame({
            'bool_col': [True, False, True, False, True],
            'value': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.generate_custom_report(boolean_data)
        assert isinstance(result, dict)

    def test_generate_report_with_duplicate_columns(self, report_generator):
        """Test report generation with duplicate columns"""
        duplicate_data = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col1': [6, 7, 8, 9, 10]  # This will create a duplicate column name
        })
        
        result = report_generator.generate_custom_report(duplicate_data)
        assert isinstance(result, dict)

    def test_generate_report_with_special_characters(self, report_generator):
        """Test report generation with special characters in data"""
        special_data = pd.DataFrame({
            'special_col': ['@#$%', '&*()', '!@#', '$%^', '&*()'],
            'normal_col': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.generate_custom_report(special_data)
        assert isinstance(result, dict)

    def test_generate_report_with_unicode_characters(self, report_generator):
        """Test report generation with unicode characters"""
        unicode_data = pd.DataFrame({
            'unicode_col': ['αβγ', 'δεζ', 'ηθι', 'κλμ', 'νξο'],
            'normal_col': [1, 2, 3, 4, 5]
        })
        
        result = report_generator.generate_custom_report(unicode_data)
        assert isinstance(result, dict)
