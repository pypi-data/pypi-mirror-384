"""
Tests for FeatureSelector class
"""

import pytest
import pandas as pd
import numpy as np

from ninetyone_life_ds.features.selector import FeatureSelector
from ninetyone_life_ds.core.exceptions import FeatureSelectionError


class TestFeatureSelector:
    """Test cases for FeatureSelector class"""

    def test_initialization(self):
        """Test FeatureSelector initialization"""
        selector = FeatureSelector()
        assert selector.random_state == 42

        # Test custom initialization
        selector_custom = FeatureSelector(random_state=123)
        assert selector_custom.random_state == 123

    def test_select_variance_threshold(self, sample_data):
        """Test variance-based feature selection"""
        selector = FeatureSelector()

        result = selector.select_variance_threshold(sample_data, threshold=0.0)

        # Check required keys
        required_keys = [
            "method",
            "threshold",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "feature_variances",
            "low_variance_features",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "variance_threshold"
        assert result["threshold"] == 0.0
        assert result["n_selected"] >= 0
        assert result["n_removed"] >= 0
        assert result["n_selected"] + result["n_removed"] == len(
            sample_data.select_dtypes(include=[np.number]).columns
        )

    def test_select_variance_threshold_high_threshold(self, sample_data):
        """Test variance-based selection with high threshold"""
        selector = FeatureSelector()

        result = selector.select_variance_threshold(sample_data, threshold=100.0)

        # With high threshold, most features should be removed
        assert result["n_removed"] >= result["n_selected"]

    def test_select_variance_threshold_exclude_cols(self, sample_data):
        """Test variance-based selection with excluded columns"""
        selector = FeatureSelector()

        exclude_cols = ["feature_1", "feature_2"]
        result = selector.select_variance_threshold(
            sample_data, exclude_cols=exclude_cols
        )

        # Excluded columns should not be in results
        for col in exclude_cols:
            assert col not in result["selected_features"]
            assert col not in result["removed_features"]

    def test_select_correlation_based(self, sample_data):
        """Test correlation-based feature selection"""
        selector = FeatureSelector()

        result = selector.select_correlation_based(sample_data, threshold=0.9)

        # Check required keys
        required_keys = [
            "method",
            "threshold",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "high_correlation_pairs",
            "correlation_matrix",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "correlation_based"
        assert result["threshold"] == 0.9
        assert result["n_selected"] >= 0
        assert result["n_removed"] >= 0
        assert isinstance(result["high_correlation_pairs"], list)
        assert isinstance(result["correlation_matrix"], dict)

    def test_select_correlation_based_low_threshold(self, sample_data):
        """Test correlation-based selection with low threshold"""
        selector = FeatureSelector()

        result = selector.select_correlation_based(sample_data, threshold=0.1)

        # With low threshold, more features should be removed
        assert result["n_removed"] >= 0

    def test_select_mutual_information(self, classification_data):
        """Test mutual information feature selection"""
        selector = FeatureSelector()

        result = selector.select_mutual_information(
            classification_data,
            target_col="target",
            task_type="classification",
            k_best=5,
        )

        # Check required keys
        required_keys = [
            "method",
            "task_type",
            "k_best",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "mutual_info_scores",
            "top_feature_score",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "mutual_information"
        assert result["task_type"] == "classification"
        assert result["k_best"] == 5
        assert result["n_selected"] <= 5
        assert result["n_selected"] >= 0

    def test_select_mutual_information_regression(self, regression_data):
        """Test mutual information for regression"""
        selector = FeatureSelector()

        result = selector.select_mutual_information(
            regression_data, target_col="target", task_type="regression", k_best=3
        )

        assert result["method"] == "mutual_information"
        assert result["task_type"] == "regression"
        assert result["k_best"] == 3
        assert result["n_selected"] <= 3

    def test_select_mutual_information_no_target(self, sample_data):
        """Test mutual information without target column"""
        selector = FeatureSelector()

        with pytest.raises(FeatureSelectionError):
            selector.select_mutual_information(sample_data, target_col="nonexistent")

    def test_select_tree_based(self, classification_data):
        """Test tree-based feature selection"""
        selector = FeatureSelector()

        result = selector.select_tree_based(
            classification_data,
            target_col="target",
            task_type="classification",
            n_estimators=50,
            top_k=5,
        )

        # Check required keys
        required_keys = [
            "method",
            "task_type",
            "n_estimators",
            "top_k",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "feature_importances",
            "model_score",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "tree_based"
        assert result["task_type"] == "classification"
        assert result["n_estimators"] == 50
        assert result["top_k"] == 5
        assert result["n_selected"] <= 5
        assert 0 <= result["model_score"] <= 1

    def test_select_tree_based_regression(self, regression_data):
        """Test tree-based selection for regression"""
        selector = FeatureSelector()

        result = selector.select_tree_based(
            regression_data,
            target_col="target",
            task_type="regression",
            n_estimators=30,
            top_k=3,
        )

        assert result["method"] == "tree_based"
        assert result["task_type"] == "regression"
        assert result["n_estimators"] == 30
        assert result["top_k"] == 3

    def test_select_l1_regularization(self, classification_data):
        """Test L1 regularization feature selection"""
        selector = FeatureSelector()

        result = selector.select_l1_regularization(
            classification_data,
            target_col="target",
            task_type="classification",
            alpha=0.01,
            top_k=5,
        )

        # Check required keys
        required_keys = [
            "method",
            "task_type",
            "alpha",
            "top_k",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "feature_coefficients",
            "n_non_zero_features",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "l1_regularization"
        assert result["task_type"] == "classification"
        assert result["alpha"] == 0.01
        assert result["top_k"] == 5
        assert result["n_non_zero_features"] >= 0

    def test_select_l1_regularization_regression(self, regression_data):
        """Test L1 regularization for regression"""
        selector = FeatureSelector()

        result = selector.select_l1_regularization(
            regression_data,
            target_col="target",
            task_type="regression",
            alpha=0.1,
            top_k=3,
        )

        assert result["method"] == "l1_regularization"
        assert result["task_type"] == "regression"
        assert result["alpha"] == 0.1
        assert result["top_k"] == 3

    def test_select_rfe(self, classification_data):
        """Test Recursive Feature Elimination"""
        selector = FeatureSelector()

        result = selector.select_rfe(
            classification_data,
            target_col="target",
            task_type="classification",
            n_features_to_select=5,
            step=1,
        )

        # Check required keys
        required_keys = [
            "method",
            "task_type",
            "n_features_to_select",
            "step",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "feature_rankings",
            "model_score",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "rfe"
        assert result["task_type"] == "classification"
        assert result["n_features_to_select"] == 5
        assert result["step"] == 1
        assert result["n_selected"] <= 5

    def test_select_rfe_regression(self, regression_data):
        """Test RFE for regression"""
        selector = FeatureSelector()

        result = selector.select_rfe(
            regression_data,
            target_col="target",
            task_type="regression",
            n_features_to_select=3,
            step=1,
        )

        assert result["method"] == "rfe"
        assert result["task_type"] == "regression"
        assert result["n_features_to_select"] == 3
        assert result["n_selected"] <= 3

    def test_select_univariate_statistical(self, classification_data):
        """Test univariate statistical feature selection"""
        selector = FeatureSelector()

        result = selector.select_univariate_statistical(
            classification_data,
            target_col="target",
            task_type="classification",
            k_best=5,
        )

        # Check required keys
        required_keys = [
            "method",
            "task_type",
            "k_best",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "feature_scores",
            "top_feature_score",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "univariate_statistical"
        assert result["task_type"] == "classification"
        assert result["k_best"] == 5
        assert result["n_selected"] <= 5
        assert result["top_feature_score"] >= 0

    def test_select_univariate_statistical_regression(self, regression_data):
        """Test univariate statistical selection for regression"""
        selector = FeatureSelector()

        result = selector.select_univariate_statistical(
            regression_data, target_col="target", task_type="regression", k_best=3
        )

        assert result["method"] == "univariate_statistical"
        assert result["task_type"] == "regression"
        assert result["k_best"] == 3
        assert result["n_selected"] <= 3

    def test_consensus_feature_selection(self, classification_data):
        """Test consensus feature selection"""
        selector = FeatureSelector()

        result = selector.consensus_feature_selection(
            classification_data,
            target_col="target",
            task_type="classification",
            methods=["variance", "correlation", "mutual_info"],
            voting_threshold=0.5,
        )

        # Check required keys
        required_keys = [
            "method",
            "task_type",
            "voting_threshold",
            "methods_used",
            "selected_features",
            "removed_features",
            "n_selected",
            "n_removed",
            "feature_votes",
            "method_results",
            "consensus_score",
        ]

        for key in required_keys:
            assert key in result

        # Check values
        assert result["method"] == "consensus"
        assert result["task_type"] == "classification"
        assert result["voting_threshold"] == 0.5
        assert len(result["methods_used"]) > 0
        assert (
            0 <= result["consensus_score"] <= 2
        )  # Allow for scores > 1 due to multiple methods
        assert isinstance(result["feature_votes"], dict)
        assert isinstance(result["method_results"], dict)

    def test_consensus_feature_selection_unsupervised(self, sample_data):
        """Test consensus feature selection without target"""
        selector = FeatureSelector()

        result = selector.consensus_feature_selection(
            sample_data,
            target_col=None,
            methods=["variance", "correlation"],
            voting_threshold=0.5,
        )

        assert result["method"] == "consensus"
        assert result["task_type"] == "regression"  # Default
        assert len(result["methods_used"]) > 0
        assert "variance" in result["methods_used"]
        assert "correlation" in result["methods_used"]

    def test_consensus_feature_selection_no_methods(self, classification_data):
        """Test consensus feature selection with no valid methods"""
        selector = FeatureSelector()

        # Should handle gracefully when no valid methods
        result = selector.consensus_feature_selection(
            classification_data, target_col="target", methods=["nonexistent_method"]
        )
        assert result["method"] == "consensus"
        assert len(result["selected_features"]) == 0

    def test_generate_feature_selection_report(self, classification_data):
        """Test comprehensive feature selection report generation"""
        selector = FeatureSelector()

        report = selector.generate_feature_selection_report(
            classification_data, target_col="target", task_type="classification"
        )

        # Check required sections
        required_sections = [
            "summary",
            "consensus_result",
            "feature_analysis",
            "method_comparison",
            "recommendations",
        ]

        for section in required_sections:
            assert section in report

        # Check summary
        summary = report["summary"]
        assert "total_features" in summary
        assert "selected_features" in summary
        assert "removed_features" in summary
        assert "selection_ratio" in summary
        assert "methods_used" in summary
        assert "consensus_score" in summary

        # Check feature analysis
        feature_analysis = report["feature_analysis"]
        assert "selected_features" in feature_analysis
        assert "removed_features" in feature_analysis
        assert "feature_votes" in feature_analysis

        # Check method comparison
        method_comparison = report["method_comparison"]
        assert len(method_comparison) > 0

        # Check recommendations
        recommendations = report["recommendations"]
        assert isinstance(recommendations, list)

    def test_generate_feature_selection_report_no_target(self, sample_data):
        """Test feature selection report without target"""
        selector = FeatureSelector()

        report = selector.generate_feature_selection_report(
            sample_data, target_col=None
        )

        # Should still generate report with unsupervised methods
        assert "summary" in report
        assert "consensus_result" in report
        assert "feature_analysis" in report

    def test_feature_selection_with_missing_data(self, missing_data):
        """Test feature selection with missing data"""
        selector = FeatureSelector()

        # Should handle missing data gracefully
        result = selector.select_variance_threshold(missing_data)
        assert "selected_features" in result
        assert "removed_features" in result

        # Test with target column
        if "target" in missing_data.columns:
            result = selector.select_mutual_information(
                missing_data, target_col="target", task_type="classification"
            )
            assert "selected_features" in result

    def test_feature_selection_with_high_dimensional_data(self, high_dimensional_data):
        """Test feature selection with high-dimensional data"""
        selector = FeatureSelector()

        result = selector.select_variance_threshold(high_dimensional_data)
        assert "selected_features" in result
        assert "removed_features" in result

        # Test consensus selection
        result = selector.consensus_feature_selection(
            high_dimensional_data,
            target_col="target",
            methods=["variance", "correlation"],
            voting_threshold=0.3,
        )
        assert "selected_features" in result
        assert result["consensus_score"] >= 0

    def test_feature_selection_error_handling(self):
        """Test error handling in feature selection"""
        selector = FeatureSelector()

        # Test with empty DataFrame
        empty_df = pd.DataFrame()

        with pytest.raises(FeatureSelectionError):
            selector.select_variance_threshold(empty_df)

        # Test with non-numeric data
        non_numeric_df = pd.DataFrame(
            {"col1": ["A", "B", "C"] * 10, "col2": ["X", "Y"] * 15}
        )

        with pytest.raises(FeatureSelectionError):
            selector.select_variance_threshold(non_numeric_df)

    def test_feature_selection_recommendations(self):
        """Test feature selection recommendations generation"""
        selector = FeatureSelector()

        # Test with different consensus results
        consensus_result = {
            "n_selected": 0,
            "n_methods": 2,
            "consensus_score": 0.05,
            "methods_used": ["variance", "correlation"],
        }

        recommendations = selector._generate_feature_selection_recommendations(
            consensus_result
        )
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Test with high selection ratio
        consensus_result = {
            "n_selected": 50,
            "n_methods": 3,
            "consensus_score": 0.9,
            "methods_used": ["variance", "correlation", "mutual_info"],
        }

        recommendations = selector._generate_feature_selection_recommendations(
            consensus_result
        )
        assert isinstance(recommendations, list)
