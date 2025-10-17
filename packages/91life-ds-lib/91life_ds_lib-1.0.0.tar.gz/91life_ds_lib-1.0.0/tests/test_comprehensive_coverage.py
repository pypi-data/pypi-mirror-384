"""
Comprehensive test coverage for all actual methods in the library
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from ninetyone_life_ds.data.loader import DataLoader
from ninetyone_life_ds.data.explorer import DataExplorer
from ninetyone_life_ds.features.selector import FeatureSelector
from ninetyone_life_ds.features.preprocessor import DataPreprocessor
from ninetyone_life_ds.visualization.plotter import Visualizer
from ninetyone_life_ds.reports.generator import ReportGenerator
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestComprehensiveCoverage:
    """Comprehensive tests for all actual methods"""

    @pytest.fixture
    def sample_data(self):
        """Create comprehensive sample data"""
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
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    # DataLoader Tests
    def test_data_loader_comprehensive(self, sample_data, temp_dir):
        """Test all DataLoader methods"""
        loader = DataLoader()
        
        # Test CSV loading
        csv_path = os.path.join(temp_dir, 'test.csv')
        sample_data.to_csv(csv_path, index=False)
        loaded_data = loader.load_csv(csv_path)
        assert isinstance(loaded_data, pd.DataFrame)
        
        # Test Parquet loading
        parquet_path = os.path.join(temp_dir, 'test.parquet')
        sample_data.to_parquet(parquet_path, index=False)
        loaded_data = loader.load_parquet(parquet_path)
        assert isinstance(loaded_data, pd.DataFrame)
        
        # Test JSON loading
        json_path = os.path.join(temp_dir, 'test.json')
        sample_data.to_json(json_path, orient='records')
        loaded_data = loader.load_json(json_path)
        assert isinstance(loaded_data, pd.DataFrame)
        
        # Test Excel loading
        excel_path = os.path.join(temp_dir, 'test.xlsx')
        sample_data.to_excel(excel_path, index=False)
        loaded_data = loader.load_excel(excel_path)
        assert isinstance(loaded_data, pd.DataFrame)
        
        # Test text loading
        txt_path = os.path.join(temp_dir, 'test.txt')
        sample_data.to_csv(txt_path, index=False, sep='\t')
        loaded_data = loader.load_text(txt_path)
        assert isinstance(loaded_data, pd.DataFrame)
        
        # Test auto-detect loading
        loaded_data = loader.load_dataset(csv_path)
        assert isinstance(loaded_data, pd.DataFrame)
        
        # Test chunked loading
        loaded_data = loader.load_csv(csv_path, chunksize=50)
        assert isinstance(loaded_data, pd.DataFrame)

    # DataExplorer Tests
    def test_data_explorer_comprehensive(self, sample_data):
        """Test all DataExplorer methods"""
        explorer = DataExplorer()
        
        # Test basic info
        result = explorer.analyze_basic_info(sample_data)
        assert isinstance(result, dict)
        assert 'shape' in result
        
        # Test missing data analysis
        result = explorer.analyze_missing_data(sample_data)
        assert isinstance(result, dict)
        assert 'missing_counts' in result
        
        # Test data quality analysis
        result = explorer.analyze_data_quality(sample_data)
        assert isinstance(result, dict)
        assert 'completeness_ratio' in result
        
        # Test statistical patterns
        result = explorer.analyze_statistical_patterns(sample_data)
        assert isinstance(result, dict)
        assert 'descriptive_stats' in result
        
        # Test distributions
        result = explorer.analyze_distributions(sample_data)
        assert isinstance(result, dict)
        assert 'numeric_distributions' in result
        
        # Test data patterns
        result = explorer.analyze_data_patterns(sample_data)
        assert isinstance(result, dict)
        assert 'missing_patterns' in result
        
        # Test detailed quality analysis
        result = explorer.analyze_data_quality_detailed(sample_data)
        assert isinstance(result, dict)
        assert 'duplicate_rows' in result
        
        # Test comprehensive report
        result = explorer.generate_comprehensive_report(sample_data)
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        
        # Test ML readiness score
        result = explorer.calculate_data_readiness_score(sample_data)
        assert isinstance(result, dict)
        assert 'is_ready_for_ml' in result

    # FeatureSelector Tests
    def test_feature_selector_comprehensive(self, sample_data):
        """Test all FeatureSelector methods"""
        selector = FeatureSelector()
        
        # Test variance threshold selection
        result = selector.select_variance_threshold(sample_data, threshold=0.01)
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test correlation-based selection
        result = selector.select_correlation_based(sample_data, threshold=0.8)
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test mutual information selection
        result = selector.select_mutual_information(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test tree-based selection
        result = selector.select_tree_based(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test L1 regularization selection
        result = selector.select_l1_regularization(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test RFE selection
        result = selector.select_rfe(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test univariate statistical selection
        result = selector.select_univariate_statistical(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test consensus selection
        result = selector.consensus_feature_selection(
            sample_data, 
            methods=['variance', 'correlation'],
            target_col='target'
        )
        assert isinstance(result, dict)
        assert 'selected_features' in result
        
        # Test feature selection report
        result = selector.generate_feature_selection_report(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'summary' in result

    # DataPreprocessor Tests
    def test_data_preprocessor_comprehensive(self, sample_data):
        """Test all DataPreprocessor methods"""
        preprocessor = DataPreprocessor()
        
        # Test missing value handling
        result = preprocessor.handle_missing_values(sample_data, strategy='mean')
        assert isinstance(result, pd.DataFrame)
        
        # Test outlier handling
        result = preprocessor.handle_outliers(sample_data, method='iqr')
        assert isinstance(result, pd.DataFrame)
        
        # Test feature scaling
        result = preprocessor.scale_features(sample_data, method='standard')
        assert isinstance(result, pd.DataFrame)
        
        # Test categorical encoding
        result = preprocessor.encode_categorical_features(sample_data, method='onehot')
        assert isinstance(result, pd.DataFrame)
        
        # Test class imbalance handling
        result = preprocessor.handle_class_imbalance(sample_data, target_col='target')
        assert isinstance(result, pd.DataFrame)
        
        # Test data splitting
        result = preprocessor.split_data(sample_data, target_col='target')
        assert isinstance(result, dict)
        assert 'X_train' in result
        
        # Test preprocessing pipeline
        result = preprocessor.create_preprocessing_pipeline()
        assert result is not None
        
        # Test get fitted transformers
        result = preprocessor.get_fitted_transformers()
        assert isinstance(result, dict)
        
        # Test transform new data
        result = preprocessor.transform_new_data(sample_data.head(10))
        assert isinstance(result, pd.DataFrame)

    # Visualizer Tests
    def test_visualizer_comprehensive(self, sample_data, temp_dir):
        """Test all Visualizer methods"""
        visualizer = Visualizer()
        
        # Test missing data plot
        result = visualizer.plot_missing_data(sample_data)
        assert result is not None
        
        # Test distributions plot
        result = visualizer.plot_distributions(sample_data)
        assert result is not None
        
        # Test correlations plot
        result = visualizer.plot_correlations(sample_data)
        assert result is not None
        
        # Test feature importance plot
        feature_scores = {'numeric_1': 0.8, 'numeric_2': 0.6, 'numeric_3': 0.4}
        result = visualizer.plot_feature_importance(feature_scores)
        assert result is not None
        
        # Test data quality summary plot
        result = visualizer.plot_data_quality_summary(sample_data)
        assert result is not None
        
        # Test interactive plot
        result = visualizer.create_interactive_plot(sample_data, plot_type='scatter')
        assert result is not None
        
        # Test export plots
        plots = {'missing_data': visualizer.plot_missing_data(sample_data)}
        result = visualizer.export_plots(plots, output_dir=temp_dir)
        assert result is not None

    # ReportGenerator Tests
    def test_report_generator_comprehensive(self, sample_data, temp_dir):
        """Test all ReportGenerator methods"""
        generator = ReportGenerator(output_dir=temp_dir)
        
        # Test YData profiling report
        with patch('ydata_profiling.ProfileReport') as mock_profile:
            mock_report = MagicMock()
            mock_report.to_file.return_value = None
            mock_profile.return_value = mock_report
            result = generator.generate_ydata_profiling_report(sample_data)
            assert result is not None
        
        # Test Sweetviz report
        with patch('sweetviz.analyze') as mock_analyze:
            mock_report = MagicMock()
            mock_report.show_html.return_value = None
            mock_analyze.return_value = mock_report
            result = generator.generate_sweetviz_report(sample_data)
            assert result is not None
        
        # Test comprehensive analysis report
        result = generator.generate_comprehensive_analysis_report(sample_data)
        assert isinstance(result, dict)
        assert 'dataset_info' in result
        
        # Test automated profiling reports
        result = generator.generate_automated_profiling_reports(sample_data)
        assert isinstance(result, dict)
        assert 'comprehensive_report' in result
        
        # Test custom report creation
        template_path = os.path.join(temp_dir, 'template.html')
        output_path = os.path.join(temp_dir, 'report.html')
        
        # Create a simple template
        with open(template_path, 'w') as f:
            f.write('<html><body>{{ dataset_name }}</body></html>')
        
        result = generator.create_custom_report(
            sample_data, 
            template_path=template_path, 
            output_path=output_path
        )
        assert result is not None

    # Edge Cases and Error Handling
    def test_edge_cases_comprehensive(self):
        """Test edge cases and error handling"""
        
        # Test with empty dataframe
        empty_df = pd.DataFrame()
        explorer = DataExplorer()
        
        with pytest.raises(DataValidationError):
            explorer.analyze_basic_info(empty_df)
        
        # Test with single column
        single_col_df = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
        result = explorer.analyze_basic_info(single_col_df)
        assert isinstance(result, dict)
        
        # Test with constant column
        constant_df = pd.DataFrame({
            'constant': [1, 1, 1, 1, 1],
            'variable': [1, 2, 3, 4, 5]
        })
        result = explorer.analyze_basic_info(constant_df)
        assert isinstance(result, dict)
        
        # Test with all missing column
        all_missing_df = pd.DataFrame({
            'all_missing': [np.nan, np.nan, np.nan, np.nan, np.nan],
            'normal': [1, 2, 3, 4, 5]
        })
        result = explorer.analyze_basic_info(all_missing_df)
        assert isinstance(result, dict)

    # Integration Tests
    def test_integration_workflow(self, sample_data, temp_dir):
        """Test complete workflow integration"""
        
        # 1. Load data
        loader = DataLoader()
        csv_path = os.path.join(temp_dir, 'integration_test.csv')
        sample_data.to_csv(csv_path, index=False)
        data = loader.load_csv(csv_path)
        
        # 2. Explore data
        explorer = DataExplorer()
        basic_info = explorer.analyze_basic_info(data)
        missing_analysis = explorer.analyze_missing_data(data)
        quality_analysis = explorer.analyze_data_quality(data)
        
        # 3. Select features
        selector = FeatureSelector()
        feature_selection = selector.consensus_feature_selection(
            data, 
            methods=['variance', 'correlation'],
            target_col='target'
        )
        
        # 4. Preprocess data
        preprocessor = DataPreprocessor()
        processed_data = preprocessor.handle_missing_values(data, strategy='mean')
        processed_data = preprocessor.scale_features(processed_data, method='standard')
        
        # 5. Visualize data
        visualizer = Visualizer()
        missing_plot = visualizer.plot_missing_data(processed_data)
        dist_plot = visualizer.plot_distributions(processed_data)
        
        # 6. Generate reports
        generator = ReportGenerator(output_dir=temp_dir)
        comprehensive_report = generator.generate_comprehensive_analysis_report(processed_data)
        
        # Assertions
        assert isinstance(basic_info, dict)
        assert isinstance(missing_analysis, dict)
        assert isinstance(quality_analysis, dict)
        assert isinstance(feature_selection, dict)
        assert isinstance(processed_data, pd.DataFrame)
        assert missing_plot is not None
        assert dist_plot is not None
        assert isinstance(comprehensive_report, dict)

    # Performance Tests
    def test_performance_large_dataset(self, temp_dir):
        """Test performance with larger dataset"""
        
        # Create larger dataset
        np.random.seed(42)
        large_data = pd.DataFrame({
            'numeric_1': np.random.normal(100, 15, 1000),
            'numeric_2': np.random.exponential(2, 1000),
            'numeric_3': np.random.uniform(0, 100, 1000),
            'categorical_1': np.random.choice(['A', 'B', 'C', 'D', 'E'], 1000),
            'categorical_2': np.random.choice(['X', 'Y', 'Z'], 1000),
            'target': np.random.choice([0, 1], 1000)
        })
        
        # Test with chunked loading
        loader = DataLoader(chunk_size=100)
        csv_path = os.path.join(temp_dir, 'large_test.csv')
        large_data.to_csv(csv_path, index=False)
        
        loaded_data = loader.load_csv(csv_path, chunksize=200)
        assert isinstance(loaded_data, pd.DataFrame)
        assert len(loaded_data) == 1000
        
        # Test exploration with large dataset
        explorer = DataExplorer()
        result = explorer.analyze_basic_info(loaded_data)
        assert isinstance(result, dict)
        assert result['shape'][0] == 1000
        
        # Test feature selection with large dataset
        selector = FeatureSelector()
        result = selector.select_variance_threshold(loaded_data, threshold=0.01)
        assert isinstance(result, dict)
        assert 'selected_features' in result

    # Cloud Storage Tests (Mocked)
    def test_cloud_storage_mocked(self):
        """Test cloud storage functionality with mocks"""
        
        loader = DataLoader()
        
        # Test cloud path detection
        is_cloud, provider = loader._is_cloud_path("s3://bucket/file.csv")
        assert is_cloud is True
        assert provider == "s3"
        
        is_cloud, provider = loader._is_cloud_path("gs://bucket/file.csv")
        assert is_cloud is True
        assert provider == "gcp"
        
        is_cloud, provider = loader._is_cloud_path("minio://bucket/file.csv")
        assert is_cloud is True
        assert provider == "minio"
        
        is_cloud, provider = loader._is_cloud_path("azure://bucket/file.csv")
        assert is_cloud is True
        assert provider == "azure"
        
        # Test cloud path parsing
        bucket, key = loader._parse_cloud_path("s3://my-bucket/path/to/file.csv")
        assert bucket == "my-bucket"
        assert key == "path/to/file.csv"
        
        bucket, key = loader._parse_cloud_path("azure://my-container/path/to/file.csv")
        assert bucket == "my-container"
        assert key == "path/to/file.csv"

    # Configuration Tests
    def test_configuration_handling(self):
        """Test configuration handling"""
        
        from ninetyone_life_ds.core.config import config
        
        # Test default values
        assert config.default_chunk_size == 100000
        assert config.max_memory_usage == 0.8
        assert config.log_level == "INFO"
        
        # Test configuration update
        config.update(default_chunk_size=50000)
        assert config.default_chunk_size == 50000
        
        # Reset for other tests
        config.update(default_chunk_size=100000)

    # Logging Tests
    def test_logging_functionality(self):
        """Test logging functionality"""
        
        from ninetyone_life_ds.core.logger import LoggerMixin
        
        class TestLogger(LoggerMixin):
            def test_method(self):
                self.logger.info("Test log message")
                return True
        
        test_logger = TestLogger()
        result = test_logger.test_method()
        assert result is True

    # Exception Handling Tests
    def test_exception_handling(self):
        """Test custom exception handling"""
        
        from ninetyone_life_ds.core.exceptions import (
            DataLoadingError, 
            DataValidationError, 
            FeatureSelectionError,
            PreprocessingError,
            VisualizationError,
            ReportGenerationError,
            CloudStorageError
        )
        
        # Test that exceptions can be raised and caught
        with pytest.raises(DataLoadingError):
            raise DataLoadingError("Test error")
        
        with pytest.raises(DataValidationError):
            raise DataValidationError("Test error")
        
        with pytest.raises(FeatureSelectionError):
            raise FeatureSelectionError("Test error")
        
        with pytest.raises(PreprocessingError):
            raise PreprocessingError("Test error")
        
        with pytest.raises(VisualizationError):
            raise VisualizationError("Test error")
        
        with pytest.raises(ReportGenerationError):
            raise ReportGenerationError("Test error")
        
        with pytest.raises(CloudStorageError):
            raise CloudStorageError("Test error")
