"""
Simple tests for DataPreprocessor class - testing actual methods that exist
"""

import pytest
import pandas as pd
import numpy as np
from ninetyone_life_ds.features.preprocessor import DataPreprocessor
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestDataPreprocessorSimple:
    """Simple test cases for DataPreprocessor"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric_1': np.random.normal(100, 15, 100),
            'numeric_2': np.random.exponential(2, 100),
            'categorical_1': np.random.choice(['A', 'B', 'C'], 100),
            'categorical_2': np.random.choice(['X', 'Y'], 100),
            'target': np.random.choice([0, 1], 100)
        })
        
        # Add some missing values
        data.loc[0:10, 'numeric_1'] = np.nan
        data.loc[20:25, 'categorical_1'] = np.nan
        
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
            strategy='mean'
        )
        
        assert not result['numeric_1'].isna().any()
        assert result.shape == sample_data.shape

    def test_handle_missing_values_drop(self, preprocessor, sample_data):
        """Test missing value handling with drop strategy"""
        result = preprocessor.handle_missing_values(
            sample_data,
            strategy='drop'
        )
        
        assert not result.isna().any().any()
        assert result.shape[0] < sample_data.shape[0]

    def test_handle_outliers_iqr(self, preprocessor, sample_data):
        """Test outlier handling using IQR method"""
        result = preprocessor.handle_outliers(
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

    def test_scale_features_minmax(self, preprocessor, sample_data):
        """Test feature scaling with min-max scaler"""
        numeric_cols = ['numeric_1', 'numeric_2']
        result = preprocessor.scale_features(
            sample_data,
            method='minmax',
            columns=numeric_cols
        )
        
        assert result.shape == sample_data.shape

    def test_encode_categorical_features_label(self, preprocessor, sample_data):
        """Test categorical encoding with label encoding"""
        categorical_cols = ['categorical_1', 'categorical_2']
        result = preprocessor.encode_categorical_features(
            sample_data,
            method='label',
            columns=categorical_cols
        )
        
        assert result.shape == sample_data.shape

    def test_encode_categorical_features_onehot(self, preprocessor, sample_data):
        """Test categorical encoding with one-hot encoding"""
        categorical_cols = ['categorical_1', 'categorical_2']
        result = preprocessor.encode_categorical_features(
            sample_data,
            method='onehot',
            columns=categorical_cols
        )
        
        # Should have more columns after one-hot encoding
        assert result.shape[1] >= sample_data.shape[1]

    def test_handle_class_imbalance_oversample(self, preprocessor, sample_data):
        """Test class imbalance handling with oversampling"""
        result = preprocessor.handle_class_imbalance(
            sample_data,
            target_column='target',
            method='oversample'
        )
        
        assert result.shape[0] >= sample_data.shape[0]
        assert result.shape[1] == sample_data.shape[1]

    def test_handle_class_imbalance_undersample(self, preprocessor, sample_data):
        """Test class imbalance handling with undersampling"""
        result = preprocessor.handle_class_imbalance(
            sample_data,
            target_column='target',
            method='undersample'
        )
        
        assert result.shape[0] <= sample_data.shape[0]
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

    def test_get_fitted_transformers(self, preprocessor):
        """Test getting fitted transformers"""
        result = preprocessor.get_fitted_transformers()
        assert isinstance(result, dict)

    def test_transform_new_data(self, preprocessor, sample_data):
        """Test transforming new data"""
        # First fit the preprocessor
        preprocessor.handle_missing_values(sample_data, strategy='mean')
        
        # Transform new data
        new_data = sample_data.head(10)
        result = preprocessor.transform_new_data(new_data)
        
        assert result is not None

    def test_empty_dataframe(self, preprocessor):
        """Test handling of empty dataframe"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(DataValidationError):
            preprocessor.handle_missing_values(empty_df)

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

    def test_missing_target_column(self, preprocessor, sample_data):
        """Test handling of missing target column"""
        with pytest.raises(ValueError):
            preprocessor.handle_class_imbalance(
                sample_data,
                target_column='nonexistent',
                method='oversample'
            )

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
            preprocessor.encode_categorical_features(sample_data, method='invalid')

    def test_preprocessing_with_nonexistent_columns(self, preprocessor, sample_data):
        """Test preprocessing with nonexistent columns"""
        with pytest.raises(ValueError):
            preprocessor.scale_features(
                sample_data,
                columns=['nonexistent_col']
            )

    def test_outlier_handling_with_no_numeric_columns(self, preprocessor):
        """Test outlier handling with no numeric columns"""
        categorical_df = pd.DataFrame({
            'cat1': ['A', 'B', 'C'],
            'cat2': ['X', 'Y', 'Z']
        })
        
        result = preprocessor.handle_outliers(categorical_df)
        assert result.shape == categorical_df.shape

    def test_encoding_with_missing_target(self, preprocessor, sample_data):
        """Test encoding with missing target column"""
        with pytest.raises(ValueError):
            preprocessor.encode_categorical_features(
                sample_data,
                method='target',
                columns=['categorical_1'],
                target_column='nonexistent_target'
            )
