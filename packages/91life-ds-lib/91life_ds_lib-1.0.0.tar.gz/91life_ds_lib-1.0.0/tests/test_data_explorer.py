"""
Tests for DataExplorer class
"""

import pytest
import pandas as pd
import numpy as np

from ninetyone_life_ds.data.explorer import DataExplorer
from ninetyone_life_ds.core.exceptions import DataValidationError


class TestDataExplorer:
    """Test cases for DataExplorer class"""

    def test_initialization(self):
        """Test DataExplorer initialization"""
        explorer = DataExplorer()
        assert explorer.sample_size == 10

        # Test custom initialization
        explorer_custom = DataExplorer(sample_size=20)
        assert explorer_custom.sample_size == 20

    def test_analyze_basic_info(self, sample_data):
        """Test basic dataset information analysis"""
        explorer = DataExplorer()

        info = explorer.analyze_basic_info(sample_data)

        # Check required keys
        required_keys = [
            "shape",
            "memory_usage",
            "memory_usage_mb",
            "dtypes",
            "columns",
            "index_type",
            "has_duplicates",
            "duplicate_count",
            "total_cells",
            "non_null_cells",
            "null_cells",
            "completeness_ratio",
        ]

        for key in required_keys:
            assert key in info

        # Check values
        assert info["shape"] == sample_data.shape
        assert info["memory_usage_mb"] > 0
        assert info["completeness_ratio"] >= 0
        assert info["completeness_ratio"] <= 1
        assert info["columns"] == list(sample_data.columns)

    def test_analyze_missing_data(self, sample_data):
        """Test missing data analysis"""
        explorer = DataExplorer()

        analysis = explorer.analyze_missing_data(sample_data, threshold=0.5)

        # Check required keys
        required_keys = [
            "total_missing",
            "missing_percentage",
            "columns_with_missing",
            "columns_with_high_missing",
            "missing_by_column",
            "missing_percent_by_column",
            "high_missing_columns",
            "missing_patterns",
            "recommendations",
        ]

        for key in required_keys:
            assert key in analysis

        # Check values
        assert analysis["total_missing"] >= 0
        assert 0 <= analysis["missing_percentage"] <= 100
        assert analysis["columns_with_missing"] >= 0
        assert analysis["columns_with_high_missing"] >= 0

    def test_analyze_missing_data_custom_threshold(self, sample_data):
        """Test missing data analysis with custom threshold"""
        explorer = DataExplorer()

        # Test with very low threshold
        analysis = explorer.analyze_missing_data(sample_data, threshold=0.01)
        assert analysis["columns_with_high_missing"] >= 0

        # Test with very high threshold
        analysis = explorer.analyze_missing_data(sample_data, threshold=0.99)
        assert analysis["columns_with_high_missing"] >= 0

    def test_analyze_data_quality(self, sample_data):
        """Test data quality analysis"""
        explorer = DataExplorer()

        quality = explorer.analyze_data_quality(sample_data)

        # Check required keys
        required_keys = [
            "duplicates",
            "cardinality",
            "type_consistency",
            "outliers",
            "data_types",
        ]

        for key in required_keys:
            assert key in quality

        # Check duplicate analysis
        assert "row_duplicates" in quality["duplicates"]
        assert "row_duplicate_percentage" in quality["duplicates"]
        assert quality["duplicates"]["row_duplicates"] >= 0
        assert 0 <= quality["duplicates"]["row_duplicate_percentage"] <= 100

    def test_analyze_statistical_patterns(self, sample_data):
        """Test statistical patterns analysis"""
        explorer = DataExplorer()

        stats = explorer.analyze_statistical_patterns(sample_data, sample_cols=5)

        # Check required keys
        required_keys = [
            "descriptive_stats",
            "correlation_matrix",
            "skewness",
            "kurtosis",
            "normality_tests",
        ]

        for key in required_keys:
            assert key in stats

        # Check descriptive stats
        assert isinstance(stats["descriptive_stats"], dict)
        assert len(stats["descriptive_stats"]) > 0

        # Check correlation matrix
        assert isinstance(stats["correlation_matrix"], dict)

    def test_analyze_statistical_patterns_no_numeric(self):
        """Test statistical patterns analysis with no numeric columns"""
        explorer = DataExplorer()

        # Create data with only categorical columns
        data = pd.DataFrame({"cat1": ["A", "B", "C"] * 10, "cat2": ["X", "Y"] * 15})

        stats = explorer.analyze_statistical_patterns(data)
        assert "message" in stats
        assert "No numeric columns found" in stats["message"]

    def test_analyze_distributions(self, sample_data):
        """Test distribution analysis"""
        explorer = DataExplorer()

        distributions = explorer.analyze_distributions(sample_data, sample_cols=5)

        # Check required keys
        required_keys = [
            "value_ranges",
            "distribution_types",
            "zero_values",
            "negative_values",
            "constant_columns",
        ]

        for key in required_keys:
            assert key in distributions

        # Check value ranges
        assert isinstance(distributions["value_ranges"], dict)
        assert len(distributions["value_ranges"]) > 0

        # Check distribution types
        assert isinstance(distributions["distribution_types"], dict)

    def test_analyze_distributions_no_numeric(self):
        """Test distribution analysis with no numeric columns"""
        explorer = DataExplorer()

        # Create data with only categorical columns
        data = pd.DataFrame({"cat1": ["A", "B", "C"] * 10, "cat2": ["X", "Y"] * 15})

        distributions = explorer.analyze_distributions(data)
        assert "message" in distributions
        assert "No numeric columns found" in distributions["message"]

    def test_calculate_data_readiness_score(self, sample_data):
        """Test data readiness score calculation"""
        explorer = DataExplorer()

        readiness = explorer.calculate_data_readiness_score(sample_data)

        # Check required keys
        required_keys = [
            "scores",
            "overall_readiness",
            "readiness_level",
            "recommendations",
            "is_ready_for_ml",
        ]

        for key in required_keys:
            assert key in readiness

        # Check scores
        score_keys = [
            "completeness",
            "missing_data",
            "duplicates",
            "type_consistency",
            "size_adequacy",
            "overall",
        ]
        for key in score_keys:
            assert key in readiness["scores"]
            assert 0 <= readiness["scores"][key] <= 100

        # Check overall readiness
        assert 0 <= readiness["overall_readiness"] <= 100
        assert readiness["readiness_level"] in [
            "Excellent",
            "Good",
            "Fair",
            "Poor",
            "Very Poor",
        ]
        assert isinstance(readiness["is_ready_for_ml"], (bool, np.bool_))
        assert isinstance(readiness["recommendations"], list)

    def test_generate_comprehensive_analysis(self, sample_data):
        """Test comprehensive analysis generation"""
        explorer = DataExplorer()

        analysis = explorer.generate_comprehensive_analysis(sample_data)

        # Check required sections
        required_sections = [
            "basic_info",
            "missing_data",
            "data_quality",
            "statistical_patterns",
            "distributions",
            "readiness_assessment",
        ]

        for section in required_sections:
            assert section in analysis

        # Check that each section has content
        for section in required_sections:
            assert analysis[section] is not None
            assert len(analysis[section]) > 0

    def test_missing_patterns_analysis(self, missing_data):
        """Test missing patterns analysis"""
        explorer = DataExplorer()

        analysis = explorer.analyze_missing_data(missing_data)

        # Check missing patterns
        assert "missing_patterns" in analysis
        patterns = analysis["missing_patterns"]

        assert "completely_missing_rows" in patterns
        assert "completely_missing_cols" in patterns
        assert "missing_clusters" in patterns

        # Check that patterns are analyzed
        assert patterns["completely_missing_rows"] >= 0
        assert patterns["completely_missing_cols"] >= 0
        assert isinstance(patterns["missing_clusters"], list)

    def test_cardinality_analysis(self, categorical_data):
        """Test cardinality analysis"""
        explorer = DataExplorer()

        quality = explorer.analyze_data_quality(categorical_data)

        # Check cardinality analysis
        assert "cardinality" in quality
        cardinality = quality["cardinality"]

        # Should have cardinality info for categorical columns
        assert len(cardinality) > 0

        for col, info in cardinality.items():
            assert "unique_values" in info
            assert "total_values" in info
            assert "cardinality_ratio" in info
            assert "is_high_cardinality" in info
            assert "is_low_cardinality" in info

            assert 0 <= info["cardinality_ratio"] <= 1
            assert isinstance(info["is_high_cardinality"], bool)
            assert isinstance(info["is_low_cardinality"], bool)

    def test_outlier_analysis(self, outlier_data):
        """Test outlier analysis"""
        explorer = DataExplorer()

        quality = explorer.analyze_data_quality(outlier_data)

        # Check outlier analysis
        assert "outliers" in quality
        outliers = quality["outliers"]

        # Should have outlier info for numeric columns
        assert len(outliers) > 0

        for col, info in outliers.items():
            assert "count" in info
            assert "percentage" in info
            assert "bounds" in info

            assert info["count"] >= 0
            assert 0 <= info["percentage"] <= 100
            assert "lower" in info["bounds"]
            assert "upper" in info["bounds"]

    def test_type_consistency_analysis(self, categorical_data):
        """Test type consistency analysis"""
        explorer = DataExplorer()

        quality = explorer.analyze_data_quality(categorical_data)

        # Check type consistency analysis
        assert "type_consistency" in quality
        type_consistency = quality["type_consistency"]

        # Should have type consistency info for object columns
        assert len(type_consistency) > 0

        for col, consistency_type in type_consistency.items():
            assert consistency_type in [
                "Could be numeric",
                "Could be datetime",
                "Text/Categorical",
            ]

    def test_readiness_level_classification(self):
        """Test readiness level classification"""
        explorer = DataExplorer()

        # Test different score ranges
        assert explorer._get_readiness_level(95) == "Excellent"
        assert explorer._get_readiness_level(85) == "Good"
        assert explorer._get_readiness_level(75) == "Fair"
        assert explorer._get_readiness_level(65) == "Poor"
        assert explorer._get_readiness_level(45) == "Very Poor"

    def test_empty_dataframe(self):
        """Test analysis with empty DataFrame"""
        explorer = DataExplorer()

        empty_df = pd.DataFrame()

        # Should handle empty DataFrame gracefully
        result = explorer.analyze_basic_info(empty_df)
        assert result["shape"] == (0, 0)
        assert (
            result["memory_usage_mb"] < 0.01
        )  # Very small memory usage for empty DataFrame

    def test_single_column_dataframe(self):
        """Test analysis with single column DataFrame"""
        explorer = DataExplorer()

        single_col_df = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})

        # Should work with single column
        info = explorer.analyze_basic_info(single_col_df)
        assert info["shape"] == (5, 1)

        quality = explorer.analyze_data_quality(single_col_df)
        assert "duplicates" in quality

    def test_constant_column_dataframe(self):
        """Test analysis with constant column DataFrame"""
        explorer = DataExplorer()

        constant_df = pd.DataFrame({"col1": [1, 1, 1, 1, 1]})

        # Should handle constant columns
        distributions = explorer.analyze_distributions(constant_df)
        assert "constant_columns" in distributions
        assert len(distributions["constant_columns"]) > 0

    def test_analyze_data_patterns(self, sample_data):
        """Test data patterns analysis"""
        explorer = DataExplorer()
        result = explorer.analyze_data_patterns(sample_data, sample_size=5)

        assert "categorical" in result
        assert "numeric_stats" in result
        assert "numeric_columns_count" in result
        assert "categorical_columns_count" in result
        assert "total_columns" in result
        assert isinstance(result["categorical"], pd.DataFrame)
        assert isinstance(result["numeric_columns_count"], int)
        assert isinstance(result["categorical_columns_count"], int)

    def test_analyze_statistical_patterns(self, sample_data):
        """Test statistical patterns analysis"""
        explorer = DataExplorer()
        result = explorer.analyze_statistical_patterns(sample_data, sample_cols=5)

        assert "descriptive_stats" in result
        assert "correlation_matrix" in result
        assert "skewness" in result
        assert "kurtosis" in result
        assert "normality_tests" in result
        assert isinstance(result["descriptive_stats"], dict)
        assert isinstance(result["correlation_matrix"], dict)

    def test_analyze_data_quality_detailed(self, sample_data):
        """Test detailed data quality analysis"""
        explorer = DataExplorer()
        result = explorer.analyze_data_quality_detailed(sample_data)

        assert "duplicate_rows" in result
        assert "duplicate_percentage" in result
        assert "high_cardinality_cols" in result
        assert "constant_cols" in result
        assert "mixed_type_cols" in result
        assert "infinite_value_cols" in result
        assert "zero_variance_cols" in result
        assert "warnings" in result
        assert "total_warnings" in result
        assert isinstance(result["duplicate_rows"], (int, np.integer))
        assert isinstance(result["warnings"], list)
        assert isinstance(result["total_warnings"], int)

    def test_generate_comprehensive_report(self, sample_data):
        """Test comprehensive report generation"""
        explorer = DataExplorer()
        result = explorer.generate_comprehensive_report(
            sample_data, dataset_name="Test Dataset", perform_clustering=False
        )

        assert "dataset_name" in result
        assert "generated_at" in result
        assert "total_rows" in result
        assert "total_columns" in result
        assert "basic_info" in result
        assert "missing_data" in result
        assert "patterns" in result
        assert "statistics" in result
        assert "quality" in result
        assert "clustering" in result
        assert "readiness" in result
        assert "summary" in result
        assert result["dataset_name"] == "Test Dataset"
        assert isinstance(result["total_rows"], int)
        assert isinstance(result["total_columns"], int)
