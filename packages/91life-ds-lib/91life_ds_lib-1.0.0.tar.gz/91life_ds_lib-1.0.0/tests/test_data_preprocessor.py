"""
Tests for DataPreprocessor class
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from ninetyone_life_ds.features.preprocessor import DataPreprocessor
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestDataPreprocessor:
    """Test cases for DataPreprocessor"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric_1': np.random.normal(100, 15, 1000),
            'numeric_2': np.random.exponential(2, 1000),
            'categorical_1': np.random.choice(['A', 'B', 'C'], 1000),
            'categorical_2': np.random.choice(['X', 'Y'], 1000),
            'target': np.random.choice([0, 1], 1000)
        })
        
        # Add some missing values
        data.loc[0:50, 'numeric_1'] = np.nan
        data.loc[100:120, 'categorical_1'] = np.nan
        
        # Add some outliers
        data.loc[0:10, 'numeric_1'] = 1000
        
        return data

    @pytest.fixture
    def preprocessor(self):
        """Create DataPreprocessor instance"""
        return DataPreprocessor()

    def test_initialization(self):
        """Test DataPreprocessor initialization"""
        preprocessor = DataPreprocessor()
        assert preprocessor.random_state == 42
        assert hasattr(preprocessor, 'logger')

    def test_handle_missing_values_mean(self, preprocessor, sample_data):
        """Test missing value handling with mean strategy"""
        result = preprocessor.handle_missing_values(
            sample_data, 
            strategy='mean',
            numeric_strategy='mean',
            categorical_strategy='most_frequent'
        )
        
        assert not result['numeric_1'].isna().any()
        assert not result['categorical_1'].isna().any()
        assert result.shape == sample_data.shape

    def test_handle_missing_values_median(self, preprocessor, sample_data):
        """Test missing value handling with median strategy"""
        result = preprocessor.handle_missing_values(
            sample_data,
            strategy='median',
            numeric_strategy='median',
            categorical_strategy='most_frequent'
        )
        
        assert not result['numeric_1'].isna().any()
        assert not result['categorical_1'].isna().any()

    def test_handle_missing_values_drop(self, preprocessor, sample_data):
        """Test missing value handling with drop strategy"""
        result = preprocessor.handle_missing_values(
            sample_data,
            strategy='drop'
        )
        
        assert not result.isna().any().any()
        assert result.shape[0] < sample_data.shape[0]

    def test_handle_missing_values_auto(self, preprocessor, sample_data):
        """Test missing value handling with auto strategy"""
        result = preprocessor.handle_missing_values(
            sample_data,
            strategy='auto'
        )
        
        assert not result.isna().any().any()

    def test_detect_outliers_iqr(self, preprocessor, sample_data):
        """Test outlier detection using IQR method"""
        result = preprocessor.detect_outliers(
            sample_data,
            method='iqr',
            columns=['numeric_1', 'numeric_2']
        )
        
        assert 'outliers' in result
        assert 'outlier_counts' in result
        assert 'outlier_percentages' in result
        assert isinstance(result['outliers'], dict)

    def test_detect_outliers_zscore(self, preprocessor, sample_data):
        """Test outlier detection using Z-score method"""
        result = preprocessor.detect_outliers(
            sample_data,
            method='zscore',
            threshold=3.0,
            columns=['numeric_1', 'numeric_2']
        )
        
        assert 'outliers' in result
        assert 'outlier_counts' in result
        assert 'outlier_percentages' in result

    def test_detect_outliers_isolation_forest(self, preprocessor, sample_data):
        """Test outlier detection using Isolation Forest"""
        result = preprocessor.detect_outliers(
            sample_data,
            method='isolation_forest',
            columns=['numeric_1', 'numeric_2']
        )
        
        assert 'outliers' in result
        assert 'outlier_counts' in result
        assert 'outlier_percentages' in result

    def test_remove_outliers(self, preprocessor, sample_data):
        """Test outlier removal"""
        result = preprocessor.remove_outliers(
            sample_data,
            method='iqr',
            columns=['numeric_1', 'numeric_2']
        )
        
        assert result.shape[0] <= sample_data.shape[0]
        assert result.shape[1] == sample_data.shape[1]

    def test_scale_features_standard(self, preprocessor, sample_data):
        """Test feature scaling with standard scaler"""
        numeric_cols = ['numeric_1', 'numeric_2']
        result = preprocessor.scale_features(
            sample_data,
            method='standard',
            columns=numeric_cols
        )
        
        assert result.shape == sample_data.shape
        # Check that scaled features have mean ~0 and std ~1
        for col in numeric_cols:
            if not result[col].isna().all():
                assert abs(result[col].mean()) < 0.1
                assert abs(result[col].std() - 1.0) < 0.1

    def test_scale_features_minmax(self, preprocessor, sample_data):
        """Test feature scaling with min-max scaler"""
        numeric_cols = ['numeric_1', 'numeric_2']
        result = preprocessor.scale_features(
            sample_data,
            method='minmax',
            columns=numeric_cols
        )
        
        assert result.shape == sample_data.shape
        # Check that scaled features are in [0, 1] range
        for col in numeric_cols:
            if not result[col].isna().all():
                assert result[col].min() >= 0
                assert result[col].max() <= 1

    def test_scale_features_robust(self, preprocessor, sample_data):
        """Test feature scaling with robust scaler"""
        numeric_cols = ['numeric_1', 'numeric_2']
        result = preprocessor.scale_features(
            sample_data,
            method='robust',
            columns=numeric_cols
        )
        
        assert result.shape == sample_data.shape

    def test_encode_categorical_label(self, preprocessor, sample_data):
        """Test categorical encoding with label encoding"""
        categorical_cols = ['categorical_1', 'categorical_2']
        result = preprocessor.encode_categorical(
            sample_data,
            method='label',
            columns=categorical_cols
        )
        
        assert result.shape == sample_data.shape
        # Check that categorical columns are now numeric
        for col in categorical_cols:
            assert pd.api.types.is_numeric_dtype(result[col])

    def test_encode_categorical_onehot(self, preprocessor, sample_data):
        """Test categorical encoding with one-hot encoding"""
        categorical_cols = ['categorical_1', 'categorical_2']
        result = preprocessor.encode_categorical(
            sample_data,
            method='onehot',
            columns=categorical_cols
        )
        
        # Should have more columns after one-hot encoding
        assert result.shape[1] > sample_data.shape[1]

    def test_encode_categorical_target(self, preprocessor, sample_data):
        """Test categorical encoding with target encoding"""
        categorical_cols = ['categorical_1', 'categorical_2']
        result = preprocessor.encode_categorical(
            sample_data,
            method='target',
            columns=categorical_cols,
            target_col='target'
        )
        
        assert result.shape == sample_data.shape
        # Check that categorical columns are now numeric
        for col in categorical_cols:
            assert pd.api.types.is_numeric_dtype(result[col])

    def test_handle_class_imbalance_oversample(self, preprocessor, sample_data):
        """Test class imbalance handling with oversampling"""
        result = preprocessor.handle_class_imbalance(
            sample_data,
            target_col='target',
            method='oversample'
        )
        
        assert result.shape[0] >= sample_data.shape[0]
        assert result.shape[1] == sample_data.shape[1]

    def test_handle_class_imbalance_undersample(self, preprocessor, sample_data):
        """Test class imbalance handling with undersampling"""
        result = preprocessor.handle_class_imbalance(
            sample_data,
            target_col='target',
            method='undersample'
        )
        
        assert result.shape[0] <= sample_data.shape[0]
        assert result.shape[1] == sample_data.shape[1]

    def test_handle_class_imbalance_smote(self, preprocessor, sample_data):
        """Test class imbalance handling with SMOTE"""
        result = preprocessor.handle_class_imbalance(
            sample_data,
            target_col='target',
            method='smote'
        )
        
        assert result.shape[0] >= sample_data.shape[0]
        assert result.shape[1] == sample_data.shape[1]

    def test_split_data(self, preprocessor, sample_data):
        """Test data splitting"""
        X = sample_data.drop('target', axis=1)
        y = sample_data['target']
        
        X_train, X_test, y_train, y_test = preprocessor.split_data(
            X, y, test_size=0.2, random_state=42
        )
        
        assert X_train.shape[0] + X_test.shape[0] == X.shape[0]
        assert y_train.shape[0] + y_test.shape[0] == y.shape[0]
        assert X_train.shape[1] == X.shape[1]

    def test_create_preprocessing_pipeline(self, preprocessor, sample_data):
        """Test preprocessing pipeline creation"""
        pipeline = preprocessor.create_preprocessing_pipeline(
            numeric_columns=['numeric_1', 'numeric_2'],
            categorical_columns=['categorical_1', 'categorical_2'],
            target_column='target'
        )
        
        assert pipeline is not None
        assert hasattr(pipeline, 'fit_transform')

    def test_apply_preprocessing_pipeline(self, preprocessor, sample_data):
        """Test preprocessing pipeline application"""
        pipeline = preprocessor.create_preprocessing_pipeline(
            numeric_columns=['numeric_1', 'numeric_2'],
            categorical_columns=['categorical_1', 'categorical_2'],
            target_column='target'
        )
        
        result = preprocessor.apply_preprocessing_pipeline(
            sample_data,
            pipeline,
            target_column='target'
        )
        
        assert result is not None
        assert isinstance(result, dict)

    def test_validate_data(self, preprocessor, sample_data):
        """Test data validation"""
        result = preprocessor.validate_data(sample_data)
        
        assert isinstance(result, dict)
        assert 'is_valid' in result
        assert 'issues' in result

    def test_get_data_summary(self, preprocessor, sample_data):
        """Test data summary generation"""
        result = preprocessor.get_data_summary(sample_data)
        
        assert isinstance(result, dict)
        assert 'shape' in result
        assert 'missing_values' in result
        assert 'data_types' in result

    def test_empty_dataframe(self, preprocessor):
        """Test handling of empty dataframe"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(DataValidationError):
            preprocessor.handle_missing_values(empty_df)

    def test_invalid_strategy(self, preprocessor, sample_data):
        """Test invalid strategy handling"""
        with pytest.raises(ValueError):
            preprocessor.handle_missing_values(sample_data, strategy='invalid')

    def test_invalid_scaling_method(self, preprocessor, sample_data):
        """Test invalid scaling method handling"""
        with pytest.raises(ValueError):
            preprocessor.scale_features(sample_data, method='invalid')

    def test_invalid_encoding_method(self, preprocessor, sample_data):
        """Test invalid encoding method handling"""
        with pytest.raises(ValueError):
            preprocessor.encode_categorical(sample_data, method='invalid')

    def test_missing_target_column(self, preprocessor, sample_data):
        """Test missing target column handling"""
        with pytest.raises(ValueError):
            preprocessor.handle_class_imbalance(
                sample_data,
                target_col='nonexistent',
                method='oversample'
            )

    def test_single_column_dataframe(self, preprocessor):
        """Test handling of single column dataframe"""
        single_col_df = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
        
        result = preprocessor.handle_missing_values(single_col_df)
        assert result.shape == single_col_df.shape

    def test_constant_column_dataframe(self, preprocessor):
        """Test handling of constant column dataframe"""
        constant_df = pd.DataFrame({
            'constant': [1, 1, 1, 1, 1],
            'variable': [1, 2, 3, 4, 5]
        })
        
        result = preprocessor.scale_features(constant_df, columns=['constant', 'variable'])
        assert result.shape == constant_df.shape

    def test_all_missing_column(self, preprocessor):
        """Test handling of all missing column"""
        all_missing_df = pd.DataFrame({
            'all_missing': [np.nan, np.nan, np.nan, np.nan, np.nan],
            'normal': [1, 2, 3, 4, 5]
        })
        
        result = preprocessor.handle_missing_values(all_missing_df, strategy='drop')
        assert result.shape[1] == 1  # Only normal column should remain

    def test_preprocessing_with_nonexistent_columns(self, preprocessor, sample_data):
        """Test preprocessing with nonexistent columns"""
        with pytest.raises(ValueError):
            preprocessor.scale_features(
                sample_data,
                columns=['nonexistent_col']
            )

    def test_outlier_detection_with_no_numeric_columns(self, preprocessor):
        """Test outlier detection with no numeric columns"""
        categorical_df = pd.DataFrame({
            'cat1': ['A', 'B', 'C'],
            'cat2': ['X', 'Y', 'Z']
        })
        
        result = preprocessor.detect_outliers(categorical_df)
        assert result['outliers'] == {}
        assert result['outlier_counts'] == {}
        assert result['outlier_percentages'] == {}

    def test_encoding_with_missing_target(self, preprocessor, sample_data):
        """Test encoding with missing target column"""
        with pytest.raises(ValueError):
            preprocessor.encode_categorical(
                sample_data,
                method='target',
                columns=['categorical_1'],
                target_col='nonexistent_target'
            )
