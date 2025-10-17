"""
Data loading functionality with async support and cloud storage integration
"""

import asyncio
import aiofiles
import pandas as pd
import numpy as np
from typing import Union, Optional, Dict, Any, List, Iterator, Tuple
from pathlib import Path
import io
import json
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

# Cloud storage imports (optional)
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from google.cloud import storage

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from minio import Minio
    from minio.error import S3Error

    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

try:
    from azure.storage.blob import BlobServiceClient, BlobClient
    from azure.core.exceptions import AzureError

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

from ..core.logger import LoggerMixin
from ..core.exceptions import DataLoadingError, CloudStorageError
from ..core.config import config


class DataLoader(LoggerMixin):
    """
    Professional data loader with async support and cloud storage integration

    Supports multiple formats: CSV, Parquet, JSON, Excel, TXT
    Cloud storage: AWS S3, Google Cloud Storage, MinIO
    Memory-efficient chunked loading for large datasets
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        max_memory_usage: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize DataLoader

        Args:
            chunk_size: Size of chunks for large dataset loading
            max_memory_usage: Maximum memory usage ratio (0.0-1.0)
            **kwargs: Additional configuration parameters
        """
        self.chunk_size = chunk_size or config.default_chunk_size
        self.max_memory_usage = max_memory_usage or config.max_memory_usage
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Cloud storage clients (lazy initialization)
        self._s3_client = None
        self._gcp_client = None
        self._minio_client = None
        self._azure_client = None

        self.logger.info(f"DataLoader initialized with chunk_size={self.chunk_size}")

    def _get_memory_usage(self) -> float:
        """Get current memory usage ratio"""
        return psutil.virtual_memory().percent / 100.0

    def _check_memory_usage(self) -> None:
        """Check if memory usage is within limits"""
        if self._get_memory_usage() > self.max_memory_usage:
            self.logger.warning(
                f"Memory usage {self._get_memory_usage():.2%} exceeds limit {self.max_memory_usage:.2%}"
            )
            gc.collect()

    def _get_file_extension(self, file_path: str) -> str:
        """Get file extension from path"""
        return Path(file_path).suffix.lower()

    def _detect_format(self, file_path: str) -> str:
        """Detect file format from extension"""
        ext = self._get_file_extension(file_path)
        format_map = {
            ".csv": "csv",
            ".parquet": "parquet",
            ".json": "json",
            ".xlsx": "excel",
            ".xls": "excel",
            ".txt": "text",
            ".tsv": "csv",
        }
        return format_map.get(ext, "csv")

    def _is_cloud_path(self, file_path: str) -> Tuple[bool, str]:
        """Check if path is a cloud storage path"""
        if file_path.startswith("s3://"):
            return True, "s3"
        elif file_path.startswith("gs://"):
            return True, "gcp"
        elif file_path.startswith("minio://"):
            return True, "minio"
        elif file_path.startswith("azure://") or file_path.startswith("https://") and ".blob.core.windows.net" in file_path:
            return True, "azure"
        return False, ""

    def _parse_cloud_path(self, file_path: str) -> Tuple[str, str]:
        """Parse cloud storage path into bucket and key"""
        if file_path.startswith("s3://"):
            path_parts = file_path[5:].split("/", 1)
            return path_parts[0], path_parts[1] if len(path_parts) > 1 else ""
        elif file_path.startswith("gs://"):
            path_parts = file_path[5:].split("/", 1)
            return path_parts[0], path_parts[1] if len(path_parts) > 1 else ""
        elif file_path.startswith("minio://"):
            path_parts = file_path[8:].split("/", 1)
            return path_parts[0], path_parts[1] if len(path_parts) > 1 else ""
        elif file_path.startswith("azure://"):
            path_parts = file_path[8:].split("/", 1)
            return path_parts[0], path_parts[1] if len(path_parts) > 1 else ""
        elif file_path.startswith("https://") and ".blob.core.windows.net" in file_path:
            # Parse Azure blob URL: https://account.blob.core.windows.net/container/blob
            url_parts = file_path.split("/")
            container = url_parts[3] if len(url_parts) > 3 else ""
            blob_path = "/".join(url_parts[4:]) if len(url_parts) > 4 else ""
            return container, blob_path
        raise ValueError(f"Invalid cloud path format: {file_path}")

    def _get_s3_client(self):
        """Get or create S3 client"""
        if not AWS_AVAILABLE:
            raise CloudStorageError(
                "AWS SDK not available. Install boto3: pip install boto3"
            )

        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=config.aws_access_key_id,
                    aws_secret_access_key=config.aws_secret_access_key,
                    region_name=config.aws_region,
                )
            except NoCredentialsError:
                raise CloudStorageError("AWS credentials not found")
        return self._s3_client

    def _get_gcp_client(self):
        """Get or create GCP client"""
        if not GCP_AVAILABLE:
            raise CloudStorageError(
                "GCP SDK not available. Install google-cloud-storage: pip install google-cloud-storage"
            )

        if self._gcp_client is None:
            try:
                if config.gcp_credentials_path:
                    self._gcp_client = storage.Client.from_service_account_json(
                        config.gcp_credentials_path
                    )
                else:
                    self._gcp_client = storage.Client(project=config.gcp_project_id)
            except Exception as e:
                raise CloudStorageError(f"Failed to initialize GCP client: {e}")
        return self._gcp_client

    def _get_minio_client(self):
        """Get or create MinIO client"""
        if not MINIO_AVAILABLE:
            raise CloudStorageError(
                "MinIO SDK not available. Install minio: pip install minio"
            )

        if self._minio_client is None:
            if not config.minio_endpoint:
                raise CloudStorageError("MinIO endpoint not configured")

            try:
                self._minio_client = Minio(
                    config.minio_endpoint,
                    access_key=config.minio_access_key,
                    secret_key=config.minio_secret_key,
                    secure=config.minio_endpoint.startswith("https://"),
                )
            except Exception as e:
                raise CloudStorageError(f"Failed to initialize MinIO client: {e}")
        return self._minio_client

    def _get_azure_client(self):
        """Get or create Azure Blob Storage client"""
        if not AZURE_AVAILABLE:
            raise CloudStorageError(
                "Azure SDK not available. Install azure-storage-blob: pip install azure-storage-blob"
            )

        if self._azure_client is None:
            try:
                if config.azure_connection_string:
                    self._azure_client = BlobServiceClient.from_connection_string(
                        config.azure_connection_string
                    )
                elif config.azure_account_name and config.azure_account_key:
                    account_url = f"https://{config.azure_account_name}.blob.core.windows.net"
                    self._azure_client = BlobServiceClient(
                        account_url=account_url,
                        credential=config.azure_account_key
                    )
                elif config.azure_account_name and config.azure_sas_token:
                    account_url = f"https://{config.azure_account_name}.blob.core.windows.net"
                    self._azure_client = BlobServiceClient(
                        account_url=account_url,
                        credential=config.azure_sas_token
                    )
                else:
                    raise CloudStorageError("Azure credentials not configured")
            except Exception as e:
                raise CloudStorageError(f"Failed to initialize Azure client: {e}")
        return self._azure_client

    async def _download_from_cloud(self, file_path: str) -> bytes:
        """Download file from cloud storage"""
        is_cloud, provider = self._is_cloud_path(file_path)
        if not is_cloud:
            raise ValueError(f"Not a cloud path: {file_path}")

        bucket, key = self._parse_cloud_path(file_path)

        try:
            if provider == "s3":
                s3_client = self._get_s3_client()
                response = s3_client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()

            elif provider == "gcp":
                gcp_client = self._get_gcp_client()
                bucket_obj = gcp_client.bucket(bucket)
                blob = bucket_obj.blob(key)
                return blob.download_as_bytes()

            elif provider == "minio":
                minio_client = self._get_minio_client()
                response = minio_client.get_object(bucket, key)
                return response.read()

            elif provider == "azure":
                azure_client = self._get_azure_client()
                blob_client = azure_client.get_blob_client(container=bucket, blob=key)
                return blob_client.download_blob().readall()

        except Exception as e:
            raise CloudStorageError(f"Failed to download from {provider}: {e}")

    def load_csv(
        self,
        file_path: str,
        chunksize: Optional[int] = None,
        max_chunks: Optional[int] = None,
        **kwargs,
    ) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
        """
        Load CSV file with chunked processing support

        Args:
            file_path: Path to CSV file (local or cloud)
            chunksize: Size of chunks for large files
            max_chunks: Maximum number of chunks to load
            **kwargs: Additional pandas.read_csv parameters

        Returns:
            DataFrame or iterator of DataFrames
        """
        self.logger.info(f"Loading CSV file: {file_path}")

        try:
            # Check if it's a cloud path
            is_cloud, _ = self._is_cloud_path(file_path)

            if is_cloud:
                # For cloud files, download first then process
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data_bytes = loop.run_until_complete(
                        self._download_from_cloud(file_path)
                    )
                    file_obj = io.BytesIO(data_bytes)
                    file_path = file_obj
                finally:
                    loop.close()

            # Use chunked loading for large files
            if chunksize or self.chunk_size:
                chunk_size = chunksize or self.chunk_size
                self.logger.info(f"Using chunked loading with chunk_size={chunk_size}")

                chunks = []
                chunk_count = 0

                for chunk in pd.read_csv(file_path, chunksize=chunk_size, **kwargs):
                    chunks.append(chunk)
                    chunk_count += 1

                    if max_chunks and chunk_count >= max_chunks:
                        break

                    self._check_memory_usage()

                if len(chunks) == 1:
                    return chunks[0]
                else:
                    self.logger.info(f"Combining {len(chunks)} chunks")
                    return pd.concat(chunks, ignore_index=True)
            else:
                return pd.read_csv(file_path, **kwargs)

        except Exception as e:
            self.logger.error(f"Failed to load CSV file: {e}")
            raise DataLoadingError(f"Failed to load CSV file {file_path}: {e}")

    def load_parquet(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load Parquet file

        Args:
            file_path: Path to Parquet file (local or cloud)
            **kwargs: Additional pandas.read_parquet parameters

        Returns:
            DataFrame
        """
        self.logger.info(f"Loading Parquet file: {file_path}")

        try:
            is_cloud, _ = self._is_cloud_path(file_path)

            if is_cloud:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data_bytes = loop.run_until_complete(
                        self._download_from_cloud(file_path)
                    )
                    file_obj = io.BytesIO(data_bytes)
                    return pd.read_parquet(file_obj, **kwargs)
                finally:
                    loop.close()
            else:
                return pd.read_parquet(file_path, **kwargs)

        except Exception as e:
            self.logger.error(f"Failed to load Parquet file: {e}")
            raise DataLoadingError(f"Failed to load Parquet file {file_path}: {e}")

    def load_json(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load JSON file

        Args:
            file_path: Path to JSON file (local or cloud)
            **kwargs: Additional pandas.read_json parameters

        Returns:
            DataFrame
        """
        self.logger.info(f"Loading JSON file: {file_path}")

        try:
            is_cloud, _ = self._is_cloud_path(file_path)

            if is_cloud:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data_bytes = loop.run_until_complete(
                        self._download_from_cloud(file_path)
                    )
                    file_obj = io.BytesIO(data_bytes)
                    return pd.read_json(file_obj, **kwargs)
                finally:
                    loop.close()
            else:
                return pd.read_json(file_path, **kwargs)

        except Exception as e:
            self.logger.error(f"Failed to load JSON file: {e}")
            raise DataLoadingError(f"Failed to load JSON file {file_path}: {e}")

    def load_excel(
        self,
        file_path: str,
        sheet_name: Union[str, int, List[Union[str, int]]] = 0,
        **kwargs,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Load Excel file

        Args:
            file_path: Path to Excel file (local or cloud)
            sheet_name: Sheet name(s) to load
            **kwargs: Additional pandas.read_excel parameters

        Returns:
            DataFrame or dictionary of DataFrames
        """
        self.logger.info(f"Loading Excel file: {file_path}")

        try:
            is_cloud, _ = self._is_cloud_path(file_path)

            if is_cloud:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data_bytes = loop.run_until_complete(
                        self._download_from_cloud(file_path)
                    )
                    file_obj = io.BytesIO(data_bytes)
                    return pd.read_excel(file_obj, sheet_name=sheet_name, **kwargs)
                finally:
                    loop.close()
            else:
                return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)

        except Exception as e:
            self.logger.error(f"Failed to load Excel file: {e}")
            raise DataLoadingError(f"Failed to load Excel file {file_path}: {e}")

    def load_text(
        self, file_path: str, delimiter: str = "\t", **kwargs
    ) -> pd.DataFrame:
        """
        Load text file (TSV, TXT, etc.)

        Args:
            file_path: Path to text file (local or cloud)
            delimiter: Delimiter character
            **kwargs: Additional pandas.read_csv parameters

        Returns:
            DataFrame
        """
        self.logger.info(f"Loading text file: {file_path}")

        try:
            # Use CSV loader with custom delimiter
            return self.load_csv(file_path, sep=delimiter, **kwargs)

        except Exception as e:
            self.logger.error(f"Failed to load text file: {e}")
            raise DataLoadingError(f"Failed to load text file {file_path}: {e}")

    def load_dataset(
        self, file_path: str, format: Optional[str] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Load dataset with automatic format detection

        Args:
            file_path: Path to dataset file
            format: File format (auto-detected if None)
            **kwargs: Format-specific parameters

        Returns:
            DataFrame
        """
        self.logger.info(f"Loading dataset: {file_path}")

        # Auto-detect format if not specified
        if format is None:
            format = self._detect_format(file_path)

        # Load based on format
        if format == "csv":
            return self.load_csv(file_path, **kwargs)
        elif format == "parquet":
            return self.load_parquet(file_path, **kwargs)
        elif format == "json":
            return self.load_json(file_path, **kwargs)
        elif format == "excel":
            return self.load_excel(file_path, **kwargs)
        elif format == "text":
            return self.load_text(file_path, **kwargs)
        else:
            raise DataLoadingError(f"Unsupported format: {format}")

    async def load_dataset_async(
        self, file_path: str, format: Optional[str] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Asynchronously load dataset

        Args:
            file_path: Path to dataset file
            format: File format (auto-detected if None)
            **kwargs: Format-specific parameters

        Returns:
            DataFrame
        """
        self.logger.info(f"Async loading dataset: {file_path}")

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.load_dataset, file_path, format, **kwargs
        )

    def load_multiple_files(
        self,
        file_paths: List[str],
        format: Optional[str] = None,
        combine: bool = True,
        **kwargs,
    ) -> Union[List[pd.DataFrame], pd.DataFrame]:
        """
        Load multiple files

        Args:
            file_paths: List of file paths
            format: File format (auto-detected if None)
            combine: Whether to combine all DataFrames into one
            **kwargs: Format-specific parameters

        Returns:
            List of DataFrames or combined DataFrame
        """
        self.logger.info(f"Loading {len(file_paths)} files")

        dataframes = []
        for file_path in file_paths:
            try:
                df = self.load_dataset(file_path, format, **kwargs)
                dataframes.append(df)
                self._check_memory_usage()
            except Exception as e:
                self.logger.error(f"Failed to load {file_path}: {e}")
                continue

        if combine and dataframes:
            self.logger.info(f"Combining {len(dataframes)} DataFrames")
            return pd.concat(dataframes, ignore_index=True)

        return dataframes

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
