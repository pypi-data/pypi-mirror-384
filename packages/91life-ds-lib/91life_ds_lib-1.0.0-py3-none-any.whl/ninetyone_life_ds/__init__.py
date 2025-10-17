"""
91life Data Science Library

A professional data science library for ML engineers and researchers at 91.life.
Provides comprehensive tools for data loading, exploration, feature selection,
preprocessing, visualization, and reporting.

Author: 91.life Data Science Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "91.life Data Science Team"
__email__ = "data-science@91.life"

# Core imports
from .core.config import Config
from .core.logger import get_logger

# Data module imports
from .data.loader import DataLoader
from .data.explorer import DataExplorer

# Feature module imports
from .features.selector import FeatureSelector
from .features.preprocessor import DataPreprocessor

# Visualization module imports
from .visualization.plotter import Visualizer

# Reports module imports
from .reports.generator import ReportGenerator

__all__ = [
    # Core
    "Config",
    "get_logger",
    # Data
    "DataLoader",
    "DataExplorer",
    # Features
    "FeatureSelector",
    "DataPreprocessor",
    # Visualization
    "Visualizer",
    # Reports
    "ReportGenerator",
]
