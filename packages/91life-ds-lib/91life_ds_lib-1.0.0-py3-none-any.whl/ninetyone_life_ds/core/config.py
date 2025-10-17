"""
Configuration management for 91life Data Science Library
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Configuration class for 91life Data Science Library

    Supports environment variables and configuration files.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )

    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")

    # Data loading configuration
    default_chunk_size: int = Field(
        default=100000, description="Default chunk size for data loading"
    )
    max_memory_usage: float = Field(
        default=0.8, description="Maximum memory usage ratio"
    )

    # Cloud storage configuration
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key"
    )
    aws_region: str = Field(default="us-east-1", description="AWS region")

    gcp_project_id: Optional[str] = Field(default=None, description="GCP project ID")
    gcp_credentials_path: Optional[str] = Field(
        default=None, description="GCP credentials file path"
    )

    minio_endpoint: Optional[str] = Field(default=None, description="MinIO endpoint")
    minio_access_key: Optional[str] = Field(
        default=None, description="MinIO access key"
    )
    minio_secret_key: Optional[str] = Field(
        default=None, description="MinIO secret key"
    )

    # Azure Blob Storage configuration
    azure_account_name: Optional[str] = Field(
        default=None, description="Azure Storage account name"
    )
    azure_account_key: Optional[str] = Field(
        default=None, description="Azure Storage account key"
    )
    azure_connection_string: Optional[str] = Field(
        default=None, description="Azure Storage connection string"
    )
    azure_sas_token: Optional[str] = Field(
        default=None, description="Azure Storage SAS token"
    )

    # Feature selection configuration
    default_feature_selection_methods: List[str] = Field(
        default=[
            "variance",
            "correlation",
            "mutual_info",
            "tree_based",
            "l1_regularization",
        ],
        description="Default feature selection methods",
    )

    # Visualization configuration
    default_figure_size: Tuple[int, int] = Field(
        default=(12, 8), description="Default figure size"
    )
    default_dpi: int = Field(default=300, description="Default DPI for plots")
    default_style: str = Field(default="whitegrid", description="Default seaborn style")

    # Report configuration
    default_output_dir: str = Field(
        default="./reports", description="Default output directory"
    )
    include_automated_profiling: bool = Field(
        default=True, description="Include automated profiling in reports"
    )

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a file"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Load environment variables from file
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

        return cls()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return self.dict()

    def update(self, **kwargs) -> None:
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")


# Global configuration instance
config = Config()
