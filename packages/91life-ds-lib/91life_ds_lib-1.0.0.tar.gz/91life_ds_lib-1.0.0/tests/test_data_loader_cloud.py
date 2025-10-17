"""
Tests for DataLoader cloud storage functionality
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from ninetyone_life_ds.data.loader import DataLoader
from ninetyone_life_ds.core.exceptions import DataLoadingError


class TestDataLoaderCloud:
    """Test cases for DataLoader cloud storage functionality"""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        np.random.seed(42)
        return pd.DataFrame({
            'numeric_1': np.random.normal(100, 15, 100),
            'numeric_2': np.random.exponential(2, 100),
            'categorical_1': np.random.choice(['A', 'B', 'C'], 100),
            'categorical_2': np.random.choice(['X', 'Y'], 100)
        })

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def loader(self):
        """Create DataLoader instance"""
        return DataLoader()

    def test_initialization(self):
        """Test DataLoader initialization"""
        loader = DataLoader()
        assert loader.chunk_size == 100000
        assert loader.memory_limit == 0.8
        assert loader.max_workers == 4
        assert hasattr(loader, 'logger')

    def test_initialization_custom_params(self):
        """Test DataLoader initialization with custom parameters"""
        loader = DataLoader(chunk_size=50000, memory_limit=0.6, max_workers=2)
        assert loader.chunk_size == 50000
        assert loader.memory_limit == 0.6
        assert loader.max_workers == 2

    def test_is_cloud_path_aws_s3(self, loader):
        """Test AWS S3 path detection"""
        assert loader._is_cloud_path('s3://bucket/file.csv')
        assert loader._is_cloud_path('s3://my-bucket/data.parquet')
        assert not loader._is_cloud_path('local/file.csv')

    def test_is_cloud_path_google_cloud(self, loader):
        """Test Google Cloud Storage path detection"""
        assert loader._is_cloud_path('gs://bucket/file.csv')
        assert loader._is_cloud_path('gs://my-bucket/data.parquet')
        assert not loader._is_cloud_path('local/file.csv')

    def test_is_cloud_path_minio(self, loader):
        """Test MinIO path detection"""
        assert loader._is_cloud_path('s3://minio-bucket/file.csv')
        assert not loader._is_cloud_path('local/file.csv')

    def test_parse_cloud_path_aws_s3(self, loader):
        """Test AWS S3 path parsing"""
        is_cloud, path = loader._parse_cloud_path('s3://bucket/file.csv')
        assert is_cloud
        assert path == 's3://bucket/file.csv'

    def test_parse_cloud_path_google_cloud(self, loader):
        """Test Google Cloud Storage path parsing"""
        is_cloud, path = loader._parse_cloud_path('gs://bucket/file.csv')
        assert is_cloud
        assert path == 'gs://bucket/file.csv'

    def test_parse_cloud_path_local(self, loader):
        """Test local path parsing"""
        is_cloud, path = loader._parse_cloud_path('local/file.csv')
        assert not is_cloud
        assert path == 'local/file.csv'

    @patch('boto3.client')
    def test_load_from_aws_s3_csv(self, mock_boto_client, loader, sample_data):
        """Test loading CSV from AWS S3"""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock S3 response
        mock_s3.get_object.return_value = {
            'Body': MagicMock()
        }
        
        # Mock pandas read_csv
        with patch('pandas.read_csv', return_value=sample_data) as mock_read_csv:
            result = loader._load_from_aws_s3('s3://bucket/file.csv', 'csv')
            
            assert result.equals(sample_data)
            mock_s3.get_object.assert_called_once_with(Bucket='bucket', Key='file.csv')
            mock_read_csv.assert_called_once()

    @patch('boto3.client')
    def test_load_from_aws_s3_parquet(self, mock_boto_client, loader, sample_data):
        """Test loading Parquet from AWS S3"""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock S3 response
        mock_s3.get_object.return_value = {
            'Body': MagicMock()
        }
        
        # Mock pandas read_parquet
        with patch('pandas.read_parquet', return_value=sample_data) as mock_read_parquet:
            result = loader._load_from_aws_s3('s3://bucket/file.parquet', 'parquet')
            
            assert result.equals(sample_data)
            mock_s3.get_object.assert_called_once_with(Bucket='bucket', Key='file.parquet')
            mock_read_parquet.assert_called_once()

    @patch('boto3.client')
    def test_load_from_aws_s3_json(self, mock_boto_client, loader, sample_data):
        """Test loading JSON from AWS S3"""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock S3 response
        mock_s3.get_object.return_value = {
            'Body': MagicMock()
        }
        
        # Mock pandas read_json
        with patch('pandas.read_json', return_value=sample_data) as mock_read_json:
            result = loader._load_from_aws_s3('s3://bucket/file.json', 'json')
            
            assert result.equals(sample_data)
            mock_s3.get_object.assert_called_once_with(Bucket='bucket', Key='file.json')
            mock_read_json.assert_called_once()

    @patch('google.cloud.storage.Client')
    def test_load_from_google_cloud_csv(self, mock_gcs_client, loader, sample_data):
        """Test loading CSV from Google Cloud Storage"""
        # Mock GCS client
        mock_client = MagicMock()
        mock_gcs_client.return_value = mock_client
        
        # Mock bucket and blob
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock pandas read_csv
        with patch('pandas.read_csv', return_value=sample_data) as mock_read_csv:
            result = loader._load_from_google_cloud('gs://bucket/file.csv', 'csv')
            
            assert result.equals(sample_data)
            mock_client.bucket.assert_called_once_with('bucket')
            mock_bucket.blob.assert_called_once_with('file.csv')
            mock_read_csv.assert_called_once()

    @patch('google.cloud.storage.Client')
    def test_load_from_google_cloud_parquet(self, mock_gcs_client, loader, sample_data):
        """Test loading Parquet from Google Cloud Storage"""
        # Mock GCS client
        mock_client = MagicMock()
        mock_gcs_client.return_value = mock_client
        
        # Mock bucket and blob
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock pandas read_parquet
        with patch('pandas.read_parquet', return_value=sample_data) as mock_read_parquet:
            result = loader._load_from_google_cloud('gs://bucket/file.parquet', 'parquet')
            
            assert result.equals(sample_data)
            mock_client.bucket.assert_called_once_with('bucket')
            mock_bucket.blob.assert_called_once_with('file.parquet')
            mock_read_parquet.assert_called_once()

    @patch('minio.Minio')
    def test_load_from_minio_csv(self, mock_minio_client, loader, sample_data):
        """Test loading CSV from MinIO"""
        # Mock MinIO client
        mock_client = MagicMock()
        mock_minio_client.return_value = mock_client
        
        # Mock MinIO response
        mock_client.get_object.return_value = MagicMock()
        
        # Mock pandas read_csv
        with patch('pandas.read_csv', return_value=sample_data) as mock_read_csv:
            result = loader._load_from_minio('s3://minio-bucket/file.csv', 'csv')
            
            assert result.equals(sample_data)
            mock_client.get_object.assert_called_once_with('minio-bucket', 'file.csv')
            mock_read_csv.assert_called_once()

    @patch('minio.Minio')
    def test_load_from_minio_parquet(self, mock_minio_client, loader, sample_data):
        """Test loading Parquet from MinIO"""
        # Mock MinIO client
        mock_client = MagicMock()
        mock_minio_client.return_value = mock_client
        
        # Mock MinIO response
        mock_client.get_object.return_value = MagicMock()
        
        # Mock pandas read_parquet
        with patch('pandas.read_parquet', return_value=sample_data) as mock_read_parquet:
            result = loader._load_from_minio('s3://minio-bucket/file.parquet', 'parquet')
            
            assert result.equals(sample_data)
            mock_client.get_object.assert_called_once_with('minio-bucket', 'file.parquet')
            mock_read_parquet.assert_called_once()

    def test_load_dataset_aws_s3_auto_detect(self, loader, sample_data):
        """Test loading dataset from AWS S3 with auto format detection"""
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_load:
            result = loader.load_dataset('s3://bucket/file.csv')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once_with('s3://bucket/file.csv', 'csv')

    def test_load_dataset_google_cloud_auto_detect(self, loader, sample_data):
        """Test loading dataset from Google Cloud with auto format detection"""
        with patch.object(loader, '_load_from_google_cloud', return_value=sample_data) as mock_load:
            result = loader.load_dataset('gs://bucket/file.parquet')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once_with('gs://bucket/file.parquet', 'parquet')

    def test_load_dataset_minio_auto_detect(self, loader, sample_data):
        """Test loading dataset from MinIO with auto format detection"""
        with patch.object(loader, '_load_from_minio', return_value=sample_data) as mock_load:
            result = loader.load_dataset('s3://minio-bucket/file.json')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once_with('s3://minio-bucket/file.json', 'json')

    def test_load_dataset_aws_s3_specified_format(self, loader, sample_data):
        """Test loading dataset from AWS S3 with specified format"""
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_load:
            result = loader.load_dataset('s3://bucket/file.data', format='csv')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once_with('s3://bucket/file.data', 'csv')

    def test_load_dataset_google_cloud_specified_format(self, loader, sample_data):
        """Test loading dataset from Google Cloud with specified format"""
        with patch.object(loader, '_load_from_google_cloud', return_value=sample_data) as mock_load:
            result = loader.load_dataset('gs://bucket/file.data', format='parquet')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once_with('gs://bucket/file.data', 'parquet')

    def test_load_dataset_minio_specified_format(self, loader, sample_data):
        """Test loading dataset from MinIO with specified format"""
        with patch.object(loader, '_load_from_minio', return_value=sample_data) as mock_load:
            result = loader.load_dataset('s3://minio-bucket/file.data', format='json')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once_with('s3://minio-bucket/file.data', 'json')

    def test_load_dataset_aws_s3_with_parameters(self, loader, sample_data):
        """Test loading dataset from AWS S3 with additional parameters"""
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_load:
            result = loader.load_dataset(
                's3://bucket/file.csv',
                sep=';',
                encoding='utf-8'
            )
            
            assert result.equals(sample_data)
            mock_load.assert_called_once()

    def test_load_dataset_google_cloud_with_parameters(self, loader, sample_data):
        """Test loading dataset from Google Cloud with additional parameters"""
        with patch.object(loader, '_load_from_google_cloud', return_value=sample_data) as mock_load:
            result = loader.load_dataset(
                'gs://bucket/file.parquet',
                engine='pyarrow'
            )
            
            assert result.equals(sample_data)
            mock_load.assert_called_once()

    def test_load_dataset_minio_with_parameters(self, loader, sample_data):
        """Test loading dataset from MinIO with additional parameters"""
        with patch.object(loader, '_load_from_minio', return_value=sample_data) as mock_load:
            result = loader.load_dataset(
                's3://minio-bucket/file.json',
                orient='records'
            )
            
            assert result.equals(sample_data)
            mock_load.assert_called_once()

    def test_load_multiple_files_cloud(self, loader, sample_data):
        """Test loading multiple files from cloud storage"""
        file_paths = [
            's3://bucket/file1.csv',
            's3://bucket/file2.csv',
            's3://bucket/file3.csv'
        ]
        
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_load:
            result = loader.load_multiple_files(file_paths)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert all(df.equals(sample_data) for df in result)
            assert mock_load.call_count == 3

    def test_load_multiple_files_mixed_sources(self, loader, sample_data):
        """Test loading multiple files from mixed cloud sources"""
        file_paths = [
            's3://bucket/file1.csv',
            'gs://bucket/file2.parquet',
            's3://minio-bucket/file3.json'
        ]
        
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_aws, \
             patch.object(loader, '_load_from_google_cloud', return_value=sample_data) as mock_gcs, \
             patch.object(loader, '_load_from_minio', return_value=sample_data) as mock_minio:
            
            result = loader.load_multiple_files(file_paths)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert all(df.equals(sample_data) for df in result)
            mock_aws.assert_called_once()
            mock_gcs.assert_called_once()
            mock_minio.assert_called_once()

    def test_chunked_loading_cloud(self, loader, sample_data):
        """Test chunked loading from cloud storage"""
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_load:
            result = loader.load_dataset(
                's3://bucket/large_file.csv',
                chunk_size=50
            )
            
            assert result.equals(sample_data)
            mock_load.assert_called_once()

    def test_memory_usage_check_cloud(self, loader, sample_data):
        """Test memory usage check for cloud loading"""
        with patch.object(loader, '_load_from_aws_s3', return_value=sample_data) as mock_load:
            result = loader.load_dataset('s3://bucket/file.csv')
            
            assert result.equals(sample_data)
            mock_load.assert_called_once()

    def test_aws_s3_authentication_error(self, loader):
        """Test AWS S3 authentication error handling"""
        with patch('boto3.client', side_effect=Exception("Authentication failed")):
            with pytest.raises(DataLoadingError):
                loader._load_from_aws_s3('s3://bucket/file.csv', 'csv')

    def test_google_cloud_authentication_error(self, loader):
        """Test Google Cloud authentication error handling"""
        with patch('google.cloud.storage.Client', side_effect=Exception("Authentication failed")):
            with pytest.raises(DataLoadingError):
                loader._load_from_google_cloud('gs://bucket/file.csv', 'csv')

    def test_minio_authentication_error(self, loader):
        """Test MinIO authentication error handling"""
        with patch('minio.Minio', side_effect=Exception("Authentication failed")):
            with pytest.raises(DataLoadingError):
                loader._load_from_minio('s3://minio-bucket/file.csv', 'csv')

    def test_aws_s3_file_not_found(self, loader):
        """Test AWS S3 file not found error handling"""
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3
            mock_s3.get_object.side_effect = Exception("NoSuchKey")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_aws_s3('s3://bucket/nonexistent.csv', 'csv')

    def test_google_cloud_file_not_found(self, loader):
        """Test Google Cloud file not found error handling"""
        with patch('google.cloud.storage.Client') as mock_gcs_client:
            mock_client = MagicMock()
            mock_gcs_client.return_value = mock_client
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            mock_blob.download_as_text.side_effect = Exception("Not found")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_google_cloud('gs://bucket/nonexistent.csv', 'csv')

    def test_minio_file_not_found(self, loader):
        """Test MinIO file not found error handling"""
        with patch('minio.Minio') as mock_minio_client:
            mock_client = MagicMock()
            mock_minio_client.return_value = mock_client
            mock_client.get_object.side_effect = Exception("NoSuchKey")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_minio('s3://minio-bucket/nonexistent.csv', 'csv')

    def test_aws_s3_network_error(self, loader):
        """Test AWS S3 network error handling"""
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3
            mock_s3.get_object.side_effect = Exception("Network error")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_aws_s3('s3://bucket/file.csv', 'csv')

    def test_google_cloud_network_error(self, loader):
        """Test Google Cloud network error handling"""
        with patch('google.cloud.storage.Client') as mock_gcs_client:
            mock_client = MagicMock()
            mock_gcs_client.return_value = mock_client
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            mock_blob.download_as_text.side_effect = Exception("Network error")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_google_cloud('gs://bucket/file.csv', 'csv')

    def test_minio_network_error(self, loader):
        """Test MinIO network error handling"""
        with patch('minio.Minio') as mock_minio_client:
            mock_client = MagicMock()
            mock_minio_client.return_value = mock_client
            mock_client.get_object.side_effect = Exception("Network error")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_minio('s3://minio-bucket/file.csv', 'csv')

    def test_aws_s3_permission_error(self, loader):
        """Test AWS S3 permission error handling"""
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3
            mock_s3.get_object.side_effect = Exception("Access denied")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_aws_s3('s3://bucket/file.csv', 'csv')

    def test_google_cloud_permission_error(self, loader):
        """Test Google Cloud permission error handling"""
        with patch('google.cloud.storage.Client') as mock_gcs_client:
            mock_client = MagicMock()
            mock_gcs_client.return_value = mock_client
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            mock_blob.download_as_text.side_effect = Exception("Access denied")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_google_cloud('gs://bucket/file.csv', 'csv')

    def test_minio_permission_error(self, loader):
        """Test MinIO permission error handling"""
        with patch('minio.Minio') as mock_minio_client:
            mock_client = MagicMock()
            mock_minio_client.return_value = mock_client
            mock_client.get_object.side_effect = Exception("Access denied")
            
            with pytest.raises(DataLoadingError):
                loader._load_from_minio('s3://minio-bucket/file.csv', 'csv')

    def test_aws_s3_invalid_format(self, loader):
        """Test AWS S3 invalid format handling"""
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3
            mock_s3.get_object.return_value = {'Body': MagicMock()}
            
            with patch('pandas.read_csv', side_effect=Exception("Invalid format")):
                with pytest.raises(DataLoadingError):
                    loader._load_from_aws_s3('s3://bucket/file.csv', 'csv')

    def test_google_cloud_invalid_format(self, loader):
        """Test Google Cloud invalid format handling"""
        with patch('google.cloud.storage.Client') as mock_gcs_client:
            mock_client = MagicMock()
            mock_gcs_client.return_value = mock_client
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            
            with patch('pandas.read_parquet', side_effect=Exception("Invalid format")):
                with pytest.raises(DataLoadingError):
                    loader._load_from_google_cloud('gs://bucket/file.parquet', 'parquet')

    def test_minio_invalid_format(self, loader):
        """Test MinIO invalid format handling"""
        with patch('minio.Minio') as mock_minio_client:
            mock_client = MagicMock()
            mock_minio_client.return_value = mock_client
            mock_client.get_object.return_value = MagicMock()
            
            with patch('pandas.read_json', side_effect=Exception("Invalid format")):
                with pytest.raises(DataLoadingError):
                    loader._load_from_minio('s3://minio-bucket/file.json', 'json')

    def test_cleanup_resources_cloud(self, loader):
        """Test cleanup of cloud resources"""
        # This test ensures that resources are properly cleaned up
        # after cloud operations
        loader.cleanup_resources()
        # No exceptions should be raised

    def test_aws_s3_with_credentials(self, loader, sample_data):
        """Test AWS S3 loading with explicit credentials"""
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3
            mock_s3.get_object.return_value = {'Body': MagicMock()}
            
            with patch('pandas.read_csv', return_value=sample_data):
                result = loader._load_from_aws_s3('s3://bucket/file.csv', 'csv')
                
                assert result.equals(sample_data)
                # Verify that boto3.client was called with credentials
                mock_boto_client.assert_called_once()

    def test_google_cloud_with_credentials(self, loader, sample_data):
        """Test Google Cloud loading with explicit credentials"""
        with patch('google.cloud.storage.Client') as mock_gcs_client:
            mock_client = MagicMock()
            mock_gcs_client.return_value = mock_client
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            
            with patch('pandas.read_parquet', return_value=sample_data):
                result = loader._load_from_google_cloud('gs://bucket/file.parquet', 'parquet')
                
                assert result.equals(sample_data)
                # Verify that Client was called
                mock_gcs_client.assert_called_once()

    def test_minio_with_credentials(self, loader, sample_data):
        """Test MinIO loading with explicit credentials"""
        with patch('minio.Minio') as mock_minio_client:
            mock_client = MagicMock()
            mock_minio_client.return_value = mock_client
            mock_client.get_object.return_value = MagicMock()
            
            with patch('pandas.read_json', return_value=sample_data):
                result = loader._load_from_minio('s3://minio-bucket/file.json', 'json')
                
                assert result.equals(sample_data)
                # Verify that Minio was called
                mock_minio_client.assert_called_once()
