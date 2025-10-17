"""
Tests for DataLoader class
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from ninetyone_life_ds.data.loader import DataLoader
from ninetyone_life_ds.core.exceptions import DataLoadingError


class TestDataLoader:
    """Test cases for DataLoader class"""

    def test_initialization(self):
        """Test DataLoader initialization"""
        loader = DataLoader()
        assert loader.chunk_size == 100000
        assert loader.max_memory_usage == 0.8

        # Test custom initialization
        loader_custom = DataLoader(chunk_size=50000, max_memory_usage=0.6)
        assert loader_custom.chunk_size == 50000
        assert loader_custom.max_memory_usage == 0.6

    def test_detect_format(self):
        """Test format detection"""
        loader = DataLoader()

        assert loader._detect_format("data.csv") == "csv"
        assert loader._detect_format("data.parquet") == "parquet"
        assert loader._detect_format("data.json") == "json"
        assert loader._detect_format("data.xlsx") == "excel"
        assert loader._detect_format("data.txt") == "text"
        assert loader._detect_format("data.tsv") == "csv"

    def test_is_cloud_path(self):
        """Test cloud path detection"""
        loader = DataLoader()

        is_cloud, provider = loader._is_cloud_path("s3://bucket/file.csv")
        assert is_cloud is True
        assert provider == "s3"

        is_cloud, provider = loader._is_cloud_path("gs://bucket/file.csv")
        assert is_cloud is True
        assert provider == "gcp"

        is_cloud, provider = loader._is_cloud_path("minio://bucket/file.csv")
        assert is_cloud is True
        assert provider == "minio"

        is_cloud, provider = loader._is_cloud_path("local/file.csv")
        assert is_cloud is False
        assert provider == ""

    def test_parse_cloud_path(self):
        """Test cloud path parsing"""
        loader = DataLoader()

        bucket, key = loader._parse_cloud_path("s3://my-bucket/path/to/file.csv")
        assert bucket == "my-bucket"
        assert key == "path/to/file.csv"

        bucket, key = loader._parse_cloud_path("gs://my-bucket/file.csv")
        assert bucket == "my-bucket"
        assert key == "file.csv"

    def test_load_csv(self, test_data_path, sample_data):
        """Test CSV loading"""
        loader = DataLoader()

        # Test basic loading
        loaded_data = loader.load_csv(test_data_path)
        pd.testing.assert_frame_equal(loaded_data, sample_data)

        # Test chunked loading
        loaded_data_chunked = loader.load_csv(test_data_path, chunksize=100)
        assert isinstance(loaded_data_chunked, pd.DataFrame)
        pd.testing.assert_frame_equal(loaded_data_chunked, sample_data)

        # Test with max_chunks
        loaded_data_limited = loader.load_csv(
            test_data_path, chunksize=100, max_chunks=5
        )
        assert len(loaded_data_limited) <= 500  # 5 chunks * 100 rows

    def test_load_parquet(self, test_parquet_path, sample_data):
        """Test Parquet loading"""
        loader = DataLoader()

        loaded_data = loader.load_parquet(test_parquet_path)
        pd.testing.assert_frame_equal(loaded_data, sample_data)

    def test_load_json(self, test_json_path, sample_data):
        """Test JSON loading"""
        loader = DataLoader()

        loaded_data = loader.load_json(test_json_path)
        # JSON loading might change data types, so we compare values
        assert loaded_data.shape == sample_data.shape
        assert list(loaded_data.columns) == list(sample_data.columns)

    def test_load_excel(self, test_excel_path, sample_data):
        """Test Excel loading"""
        loader = DataLoader()

        loaded_data = loader.load_excel(test_excel_path)
        # Excel loading might change data types, so we compare shapes
        assert loaded_data.shape == sample_data.shape
        assert list(loaded_data.columns) == list(sample_data.columns)

    def test_load_text(self, sample_data):
        """Test text file loading"""
        loader = DataLoader()

        # Create a TSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            sample_data.to_csv(f.name, sep="\t", index=False)
            tsv_path = f.name

        try:
            loaded_data = loader.load_text(tsv_path, delimiter="\t")
            pd.testing.assert_frame_equal(loaded_data, sample_data)
        finally:
            os.unlink(tsv_path)

    def test_load_dataset_auto_detect(self, test_data_path, sample_data):
        """Test automatic format detection"""
        loader = DataLoader()

        loaded_data = loader.load_dataset(test_data_path)
        pd.testing.assert_frame_equal(loaded_data, sample_data)

    def test_load_dataset_specified_format(self, test_data_path, sample_data):
        """Test loading with specified format"""
        loader = DataLoader()

        loaded_data = loader.load_dataset(test_data_path, format="csv")
        pd.testing.assert_frame_equal(loaded_data, sample_data)

    def test_load_multiple_files(self, sample_data):
        """Test loading multiple files"""
        loader = DataLoader()

        # Create multiple CSV files
        file_paths = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                sample_data.to_csv(f.name, index=False)
                file_paths.append(f.name)

        try:
            # Test combining multiple files
            combined_data = loader.load_multiple_files(file_paths, combine=True)
            expected_rows = len(sample_data) * 3
            assert len(combined_data) == expected_rows

            # Test without combining
            dataframes = loader.load_multiple_files(file_paths, combine=False)
            assert len(dataframes) == 3
            assert all(isinstance(df, pd.DataFrame) for df in dataframes)

        finally:
            for path in file_paths:
                os.unlink(path)

    def test_load_dataset_nonexistent_file(self):
        """Test loading non-existent file"""
        loader = DataLoader()

        with pytest.raises(DataLoadingError):
            loader.load_dataset("nonexistent_file.csv")

    def test_load_dataset_unsupported_format(self):
        """Test loading with unsupported format"""
        loader = DataLoader()

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test data")
            file_path = f.name

        try:
            with pytest.raises(DataLoadingError):
                loader.load_dataset(file_path, format="xyz")
        finally:
            os.unlink(file_path)

    def test_memory_usage_check(self):
        """Test memory usage checking"""
        loader = DataLoader()

        # Test memory usage calculation
        memory_usage = loader._get_memory_usage()
        assert 0 <= memory_usage <= 1

        # Test memory check (should not raise exception)
        loader._check_memory_usage()

    def test_file_extension_detection(self):
        """Test file extension detection"""
        loader = DataLoader()

        assert loader._get_file_extension("file.csv") == ".csv"
        assert loader._get_file_extension("file.parquet") == ".parquet"
        assert loader._get_file_extension("file.json") == ".json"
        assert loader._get_file_extension("file.xlsx") == ".xlsx"
        assert loader._get_file_extension("file.txt") == ".txt"

    @pytest.mark.asyncio
    async def test_load_dataset_async(self, test_data_path, sample_data):
        """Test async dataset loading"""
        loader = DataLoader()

        loaded_data = await loader.load_dataset_async(test_data_path)
        pd.testing.assert_frame_equal(loaded_data, sample_data)

    def test_chunked_loading_large_file(self, large_sample_data):
        """Test chunked loading with larger dataset"""
        loader = DataLoader(chunk_size=1000)

        # Create a larger CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            large_sample_data.to_csv(f.name, index=False)
            file_path = f.name

        try:
            loaded_data = loader.load_csv(file_path, chunksize=500)
            pd.testing.assert_frame_equal(loaded_data, large_sample_data)
        finally:
            os.unlink(file_path)

    def test_csv_loading_with_parameters(self, sample_data):
        """Test CSV loading with additional parameters"""
        loader = DataLoader()

        # Create CSV with specific parameters
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_data.to_csv(f.name, index=False, sep=";")
            file_path = f.name

        try:
            loaded_data = loader.load_csv(file_path, sep=";")
            pd.testing.assert_frame_equal(loaded_data, sample_data)
        finally:
            os.unlink(file_path)

    def test_cleanup_resources(self):
        """Test resource cleanup"""
        loader = DataLoader()

        # Test that executor is properly initialized
        assert hasattr(loader, "executor")
        assert loader.executor is not None

        # Test cleanup (should not raise exception)
        del loader
