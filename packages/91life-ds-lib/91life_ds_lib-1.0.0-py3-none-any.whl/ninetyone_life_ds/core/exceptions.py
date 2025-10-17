"""
Custom exceptions for 91life Data Science Library
"""


class DataLoadingError(Exception):
    """Raised when data loading fails"""

    pass


class DataValidationError(Exception):
    """Raised when data validation fails"""

    pass


class FeatureSelectionError(Exception):
    """Raised when feature selection fails"""

    pass


class PreprocessingError(Exception):
    """Raised when data preprocessing fails"""

    pass


class VisualizationError(Exception):
    """Raised when visualization generation fails"""

    pass


class ReportGenerationError(Exception):
    """Raised when report generation fails"""

    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""

    pass


class CloudStorageError(Exception):
    """Raised when cloud storage operations fail"""

    pass
