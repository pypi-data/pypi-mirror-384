"""
Feature selection functionality with multiple methods and consensus approach
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from sklearn.feature_selection import (
    VarianceThreshold,
    SelectKBest,
    SelectPercentile,
    f_classif,
    f_regression,
    mutual_info_classif,
    mutual_info_regression,
    RFE,
    SelectFromModel,
)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LassoCV, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mutual_info_score
from scipy.stats import pearsonr, spearmanr
import warnings

from ..core.logger import LoggerMixin
from ..core.exceptions import FeatureSelectionError
from ..core.config import config


class FeatureSelector(LoggerMixin):
    """
    Comprehensive feature selection with multiple methods and consensus approach

    Supports both supervised and unsupervised feature selection methods:
    - Variance-based selection
    - Correlation-based selection
    - Mutual information
    - Tree-based importance
    - L1 regularization (Lasso)
    - Recursive Feature Elimination (RFE)
    - Univariate statistical tests
    - Consensus feature selection
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize FeatureSelector

        Args:
            random_state: Random state for reproducibility
        """
        self.random_state = random_state
        self.logger.info(
            f"FeatureSelector initialized with random_state={random_state}"
        )

    def select_variance_threshold(
        self,
        data: pd.DataFrame,
        threshold: float = 0.0,
        exclude_cols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Select features based on variance threshold

        Args:
            data: Input DataFrame
            threshold: Variance threshold (features with variance below this will be removed)
            exclude_cols: Columns to exclude from selection

        Returns:
            Dictionary with selection results
        """
        self.logger.info(
            f"Performing variance-based feature selection with threshold={threshold}"
        )

        try:
            # Prepare data
            numeric_data = data.select_dtypes(include=[np.number])

            if exclude_cols:
                numeric_data = numeric_data.drop(
                    columns=[col for col in exclude_cols if col in numeric_data.columns]
                )

            if numeric_data.empty:
                raise FeatureSelectionError(
                    "No numeric columns found for variance selection"
                )

            # Apply variance threshold
            selector = VarianceThreshold(threshold=threshold)
            selector.fit(numeric_data)

            # Get selected features
            selected_features = numeric_data.columns[selector.get_support()].tolist()
            removed_features = numeric_data.columns[~selector.get_support()].tolist()

            # Calculate feature variances
            variances = numeric_data.var()

            results = {
                "method": "variance_threshold",
                "threshold": threshold,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "feature_variances": variances.to_dict(),
                "low_variance_features": [
                    col for col in removed_features if variances[col] < threshold
                ],
            }

            self.logger.info(
                f"Selected {len(selected_features)} features, removed {len(removed_features)}"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed variance-based selection: {e}")
            raise FeatureSelectionError(f"Failed variance-based selection: {e}")

    def select_correlation_based(
        self,
        data: pd.DataFrame,
        threshold: float = 0.9,
        exclude_cols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Select features based on correlation threshold

        Args:
            data: Input DataFrame
            threshold: Correlation threshold (features with correlation above this will be removed)
            exclude_cols: Columns to exclude from selection

        Returns:
            Dictionary with selection results
        """
        self.logger.info(
            f"Performing correlation-based feature selection with threshold={threshold}"
        )

        try:
            # Prepare data
            numeric_data = data.select_dtypes(include=[np.number])

            if exclude_cols:
                numeric_data = numeric_data.drop(
                    columns=[col for col in exclude_cols if col in numeric_data.columns]
                )

            if numeric_data.empty:
                raise FeatureSelectionError(
                    "No numeric columns found for correlation selection"
                )

            # Calculate correlation matrix
            corr_matrix = numeric_data.corr().abs()

            # Find highly correlated pairs
            high_corr_pairs = []
            features_to_remove = set()

            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    feature1 = corr_matrix.columns[i]
                    feature2 = corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]

                    if corr_value > threshold:
                        high_corr_pairs.append(
                            {
                                "feature1": feature1,
                                "feature2": feature2,
                                "correlation": corr_value,
                            }
                        )

                        # Remove the feature with lower variance
                        var1 = numeric_data[feature1].var()
                        var2 = numeric_data[feature2].var()

                        if var1 < var2:
                            features_to_remove.add(feature1)
                        else:
                            features_to_remove.add(feature2)

            # Get selected features
            selected_features = [
                col for col in numeric_data.columns if col not in features_to_remove
            ]
            removed_features = list(features_to_remove)

            results = {
                "method": "correlation_based",
                "threshold": threshold,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "high_correlation_pairs": high_corr_pairs,
                "correlation_matrix": corr_matrix.to_dict(),
            }

            self.logger.info(
                f"Selected {len(selected_features)} features, removed {len(removed_features)}"
            )
            self.logger.info(f"Found {len(high_corr_pairs)} highly correlated pairs")

            return results

        except Exception as e:
            self.logger.error(f"Failed correlation-based selection: {e}")
            raise FeatureSelectionError(f"Failed correlation-based selection: {e}")

    def select_mutual_information(
        self,
        data: pd.DataFrame,
        target_col: str,
        task_type: str = "regression",
        k_best: int = 10,
    ) -> Dict[str, Any]:
        """
        Select features based on mutual information

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            k_best: Number of top features to select

        Returns:
            Dictionary with selection results
        """
        self.logger.info(
            f"Performing mutual information feature selection for {task_type}"
        )

        try:
            # Prepare data
            X = data.drop(columns=[target_col])
            y = data[target_col]

            # Select numeric features
            numeric_features = X.select_dtypes(include=[np.number])

            if numeric_features.empty:
                raise FeatureSelectionError(
                    "No numeric features found for mutual information selection"
                )

            # Handle missing values
            X_clean = numeric_features.fillna(numeric_features.median())
            y_clean = y.fillna(y.median() if task_type == "regression" else y.mode()[0])

            # Calculate mutual information
            if task_type == "classification":
                mi_scores = mutual_info_classif(
                    X_clean, y_clean, random_state=self.random_state
                )
            else:
                mi_scores = mutual_info_regression(
                    X_clean, y_clean, random_state=self.random_state
                )

            # Create feature scores dataframe
            mi_df = pd.DataFrame(
                {"feature": numeric_features.columns, "mutual_info_score": mi_scores}
            ).sort_values("mutual_info_score", ascending=False)

            # Select top k features
            selected_features = mi_df.head(k_best)["feature"].tolist()
            removed_features = mi_df.tail(len(mi_df) - k_best)["feature"].tolist()

            results = {
                "method": "mutual_information",
                "task_type": task_type,
                "k_best": k_best,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "mutual_info_scores": mi_df.to_dict("records"),
                "top_feature_score": (
                    mi_df.iloc[0]["mutual_info_score"] if len(mi_df) > 0 else 0
                ),
            }

            self.logger.info(
                f"Selected {len(selected_features)} features based on mutual information"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed mutual information selection: {e}")
            raise FeatureSelectionError(f"Failed mutual information selection: {e}")

    def select_tree_based(
        self,
        data: pd.DataFrame,
        target_col: str,
        task_type: str = "regression",
        n_estimators: int = 100,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Select features based on tree-based importance

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            n_estimators: Number of trees in the forest
            top_k: Number of top features to select

        Returns:
            Dictionary with selection results
        """
        self.logger.info(f"Performing tree-based feature selection for {task_type}")

        try:
            # Prepare data
            X = data.drop(columns=[target_col])
            y = data[target_col]

            # Select numeric features
            numeric_features = X.select_dtypes(include=[np.number])

            if numeric_features.empty:
                raise FeatureSelectionError(
                    "No numeric features found for tree-based selection"
                )

            # Handle missing values
            X_clean = numeric_features.fillna(numeric_features.median())
            y_clean = y.fillna(y.median() if task_type == "regression" else y.mode()[0])

            # Train tree-based model
            if task_type == "classification":
                model = RandomForestClassifier(
                    n_estimators=n_estimators, random_state=self.random_state, n_jobs=-1
                )
            else:
                model = RandomForestRegressor(
                    n_estimators=n_estimators, random_state=self.random_state, n_jobs=-1
                )

            model.fit(X_clean, y_clean)

            # Get feature importances
            importance_df = pd.DataFrame(
                {
                    "feature": numeric_features.columns,
                    "importance": model.feature_importances_,
                }
            ).sort_values("importance", ascending=False)

            # Select top k features
            selected_features = importance_df.head(top_k)["feature"].tolist()
            removed_features = importance_df.tail(len(importance_df) - top_k)[
                "feature"
            ].tolist()

            results = {
                "method": "tree_based",
                "task_type": task_type,
                "n_estimators": n_estimators,
                "top_k": top_k,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "feature_importances": importance_df.to_dict("records"),
                "top_feature_importance": (
                    importance_df.iloc[0]["importance"] if len(importance_df) > 0 else 0
                ),
                "model_score": model.score(X_clean, y_clean),
            }

            self.logger.info(
                f"Selected {len(selected_features)} features based on tree importance"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed tree-based selection: {e}")
            raise FeatureSelectionError(f"Failed tree-based selection: {e}")

    def select_l1_regularization(
        self,
        data: pd.DataFrame,
        target_col: str,
        task_type: str = "regression",
        alpha: float = 0.01,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Select features based on L1 regularization (Lasso)

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            alpha: Regularization strength
            top_k: Number of top features to select

        Returns:
            Dictionary with selection results
        """
        self.logger.info(
            f"Performing L1 regularization feature selection for {task_type}"
        )

        try:
            # Prepare data
            X = data.drop(columns=[target_col])
            y = data[target_col]

            # Select numeric features
            numeric_features = X.select_dtypes(include=[np.number])

            if numeric_features.empty:
                raise FeatureSelectionError(
                    "No numeric features found for L1 regularization selection"
                )

            # Handle missing values and scale features
            X_clean = numeric_features.fillna(numeric_features.median())
            y_clean = y.fillna(y.median() if task_type == "regression" else y.mode()[0])

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_clean)

            # Train L1 regularized model
            if task_type == "classification":
                # Handle multi-class classification
                if len(y_clean.unique()) > 2:
                    model = LogisticRegression(
                        penalty="l1",
                        solver="liblinear",
                        C=1 / alpha,
                        random_state=self.random_state,
                        max_iter=1000,
                    )
                else:
                    model = LogisticRegression(
                        penalty="l1",
                        solver="liblinear",
                        C=1 / alpha,
                        random_state=self.random_state,
                        max_iter=1000,
                    )
            else:
                model = LassoCV(
                    alphas=[alpha], random_state=self.random_state, max_iter=1000
                )

            model.fit(X_scaled, y_clean)

            # Get feature coefficients
            if hasattr(model, "coef_"):
                coefficients = model.coef_
                if len(coefficients.shape) > 1:
                    coefficients = coefficients[0]  # For multi-class
            else:
                coefficients = model.coef_

            # Create feature importance dataframe
            importance_df = pd.DataFrame(
                {
                    "feature": numeric_features.columns,
                    "coefficient": coefficients,
                    "abs_coefficient": np.abs(coefficients),
                }
            ).sort_values("abs_coefficient", ascending=False)

            # Select top k features with non-zero coefficients
            non_zero_features = importance_df[importance_df["abs_coefficient"] > 0]
            selected_features = non_zero_features.head(top_k)["feature"].tolist()
            removed_features = importance_df[importance_df["abs_coefficient"] == 0][
                "feature"
            ].tolist()

            results = {
                "method": "l1_regularization",
                "task_type": task_type,
                "alpha": alpha,
                "top_k": top_k,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "feature_coefficients": importance_df.to_dict("records"),
                "n_non_zero_features": len(non_zero_features),
                "model_score": (
                    model.score(X_scaled, y_clean) if hasattr(model, "score") else None
                ),
            }

            self.logger.info(
                f"Selected {len(selected_features)} features with L1 regularization"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed L1 regularization selection: {e}")
            raise FeatureSelectionError(f"Failed L1 regularization selection: {e}")

    def select_rfe(
        self,
        data: pd.DataFrame,
        target_col: str,
        task_type: str = "regression",
        n_features_to_select: int = 10,
        step: int = 1,
    ) -> Dict[str, Any]:
        """
        Select features using Recursive Feature Elimination (RFE)

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            n_features_to_select: Number of features to select
            step: Number of features to remove at each step

        Returns:
            Dictionary with selection results
        """
        self.logger.info(f"Performing RFE feature selection for {task_type}")

        try:
            # Prepare data
            X = data.drop(columns=[target_col])
            y = data[target_col]

            # Select numeric features
            numeric_features = X.select_dtypes(include=[np.number])

            if numeric_features.empty:
                raise FeatureSelectionError(
                    "No numeric features found for RFE selection"
                )

            # Handle missing values
            X_clean = numeric_features.fillna(numeric_features.median())
            y_clean = y.fillna(y.median() if task_type == "regression" else y.mode()[0])

            # Choose base estimator
            if task_type == "classification":
                if len(y_clean.unique()) > 2:
                    base_estimator = LogisticRegression(
                        random_state=self.random_state, max_iter=1000
                    )
                else:
                    base_estimator = LogisticRegression(
                        random_state=self.random_state, max_iter=1000
                    )
            else:
                base_estimator = LassoCV(random_state=self.random_state, max_iter=1000)

            # Apply RFE
            selector = RFE(
                estimator=base_estimator,
                n_features_to_select=n_features_to_select,
                step=step,
            )

            selector.fit(X_clean, y_clean)

            # Get selected features
            selected_features = numeric_features.columns[
                selector.get_support()
            ].tolist()
            removed_features = numeric_features.columns[
                ~selector.get_support()
            ].tolist()

            # Get feature rankings
            rankings = pd.DataFrame(
                {"feature": numeric_features.columns, "ranking": selector.ranking_}
            ).sort_values("ranking")

            results = {
                "method": "rfe",
                "task_type": task_type,
                "n_features_to_select": n_features_to_select,
                "step": step,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "feature_rankings": rankings.to_dict("records"),
                "model_score": selector.score(X_clean, y_clean),
            }

            self.logger.info(f"Selected {len(selected_features)} features using RFE")

            return results

        except Exception as e:
            self.logger.error(f"Failed RFE selection: {e}")
            raise FeatureSelectionError(f"Failed RFE selection: {e}")

    def select_univariate_statistical(
        self,
        data: pd.DataFrame,
        target_col: str,
        task_type: str = "regression",
        k_best: int = 10,
    ) -> Dict[str, Any]:
        """
        Select features using univariate statistical tests

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            k_best: Number of top features to select

        Returns:
            Dictionary with selection results
        """
        self.logger.info(
            f"Performing univariate statistical feature selection for {task_type}"
        )

        try:
            # Prepare data
            X = data.drop(columns=[target_col])
            y = data[target_col]

            # Select numeric features
            numeric_features = X.select_dtypes(include=[np.number])

            if numeric_features.empty:
                raise FeatureSelectionError(
                    "No numeric features found for univariate selection"
                )

            # Handle missing values
            X_clean = numeric_features.fillna(numeric_features.median())
            y_clean = y.fillna(y.median() if task_type == "regression" else y.mode()[0])

            # Choose statistical test
            if task_type == "classification":
                score_func = f_classif
            else:
                score_func = f_regression

            # Apply univariate selection
            selector = SelectKBest(score_func=score_func, k=k_best)
            selector.fit(X_clean, y_clean)

            # Get selected features
            selected_features = numeric_features.columns[
                selector.get_support()
            ].tolist()
            removed_features = numeric_features.columns[
                ~selector.get_support()
            ].tolist()

            # Get feature scores
            scores_df = pd.DataFrame(
                {
                    "feature": numeric_features.columns,
                    "score": selector.scores_,
                    "p_value": selector.pvalues_,
                }
            ).sort_values("score", ascending=False)

            results = {
                "method": "univariate_statistical",
                "task_type": task_type,
                "k_best": k_best,
                "selected_features": selected_features,
                "removed_features": removed_features,
                "n_selected": len(selected_features),
                "n_removed": len(removed_features),
                "feature_scores": scores_df.to_dict("records"),
                "top_feature_score": (
                    scores_df.iloc[0]["score"] if len(scores_df) > 0 else 0
                ),
            }

            self.logger.info(
                f"Selected {len(selected_features)} features using univariate tests"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed univariate statistical selection: {e}")
            raise FeatureSelectionError(f"Failed univariate statistical selection: {e}")

    def consensus_feature_selection(
        self,
        data: pd.DataFrame,
        target_col: Optional[str] = None,
        task_type: str = "regression",
        methods: Optional[List[str]] = None,
        voting_threshold: float = 0.5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Perform consensus feature selection using multiple methods

        Args:
            data: Input DataFrame
            target_col: Target column name (required for supervised methods)
            task_type: 'classification' or 'regression'
            methods: List of methods to use for consensus
            voting_threshold: Minimum fraction of methods that must select a feature
            **kwargs: Additional parameters for individual methods

        Returns:
            Dictionary with consensus selection results
        """
        self.logger.info("Performing consensus feature selection")

        try:
            # Default methods
            if methods is None:
                methods = config.default_feature_selection_methods.copy()

            # Separate supervised and unsupervised methods
            supervised_methods = [
                "mutual_info",
                "tree_based",
                "l1_regularization",
                "rfe",
                "univariate_statistical",
            ]
            unsupervised_methods = ["variance", "correlation"]

            # Filter methods based on target availability
            if target_col is None:
                methods = [m for m in methods if m in unsupervised_methods]
                self.logger.info(
                    "No target column provided, using unsupervised methods only"
                )
            else:
                # Ensure target column exists
                if target_col not in data.columns:
                    raise FeatureSelectionError(
                        f"Target column '{target_col}' not found in data"
                    )

            if not methods:
                raise FeatureSelectionError(
                    "No valid methods available for consensus selection"
                )

            # Run individual methods
            method_results = {}
            all_selected_features = []

            for method in methods:
                try:
                    self.logger.info(f"Running {method} feature selection")

                    if method == "variance":
                        result = self.select_variance_threshold(
                            data,
                            threshold=kwargs.get("variance_threshold", 0.0),
                            exclude_cols=kwargs.get("exclude_cols"),
                        )
                    elif method == "correlation":
                        result = self.select_correlation_based(
                            data,
                            threshold=kwargs.get("correlation_threshold", 0.9),
                            exclude_cols=kwargs.get("exclude_cols"),
                        )
                    elif method == "mutual_info":
                        result = self.select_mutual_information(
                            data,
                            target_col=target_col,
                            task_type=task_type,
                            k_best=kwargs.get("k_best", 10),
                        )
                    elif method == "tree_based":
                        result = self.select_tree_based(
                            data,
                            target_col=target_col,
                            task_type=task_type,
                            n_estimators=kwargs.get("n_estimators", 100),
                            top_k=kwargs.get("top_k", 10),
                        )
                    elif method == "l1_regularization":
                        result = self.select_l1_regularization(
                            data,
                            target_col=target_col,
                            task_type=task_type,
                            alpha=kwargs.get("alpha", 0.01),
                            top_k=kwargs.get("top_k", 10),
                        )
                    elif method == "rfe":
                        result = self.select_rfe(
                            data,
                            target_col=target_col,
                            task_type=task_type,
                            n_features_to_select=kwargs.get("n_features_to_select", 10),
                            step=kwargs.get("step", 1),
                        )
                    elif method == "univariate_statistical":
                        result = self.select_univariate_statistical(
                            data,
                            target_col=target_col,
                            task_type=task_type,
                            k_best=kwargs.get("k_best", 10),
                        )
                    else:
                        self.logger.warning(f"Unknown method: {method}")
                        continue

                    method_results[method] = result
                    all_selected_features.extend(result["selected_features"])

                except Exception as e:
                    self.logger.error(f"Failed to run {method}: {e}")
                    continue

            # Calculate consensus
            feature_votes = {}
            for feature in set(all_selected_features):
                votes = sum(
                    1
                    for result in method_results.values()
                    if feature in result["selected_features"]
                )
                feature_votes[feature] = votes / len(method_results)

            # Select features based on voting threshold
            consensus_features = [
                feature
                for feature, vote_ratio in feature_votes.items()
                if vote_ratio >= voting_threshold
            ]

            # Sort by vote ratio
            consensus_features.sort(key=lambda x: feature_votes[x], reverse=True)

            # Get all features for comparison
            all_features = data.select_dtypes(include=[np.number]).columns.tolist()
            if target_col and target_col in all_features:
                all_features.remove(target_col)

            removed_features = [f for f in all_features if f not in consensus_features]

            results = {
                "method": "consensus",
                "task_type": task_type,
                "voting_threshold": voting_threshold,
                "methods_used": list(method_results.keys()),
                "selected_features": consensus_features,
                "removed_features": removed_features,
                "n_selected": len(consensus_features),
                "n_removed": len(removed_features),
                "feature_votes": feature_votes,
                "method_results": method_results,
                "consensus_score": (
                    len(consensus_features) / len(all_features) if all_features else 0
                ),
            }

            self.logger.info(
                f"Consensus selected {len(consensus_features)} features from {len(method_results)} methods"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed consensus feature selection: {e}")
            raise FeatureSelectionError(f"Failed consensus feature selection: {e}")

    def generate_feature_selection_report(
        self,
        data: pd.DataFrame,
        target_col: Optional[str] = None,
        task_type: str = "regression",
        methods: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feature selection report

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            methods: List of methods to include in report
            **kwargs: Additional parameters for methods

        Returns:
            Dictionary with comprehensive feature selection report
        """
        self.logger.info("Generating comprehensive feature selection report")

        try:
            # Run consensus selection
            consensus_result = self.consensus_feature_selection(
                data=data,
                target_col=target_col,
                task_type=task_type,
                methods=methods,
                **kwargs,
            )

            # Generate summary statistics
            all_features = data.select_dtypes(include=[np.number]).columns.tolist()
            if target_col and target_col in all_features:
                all_features.remove(target_col)

            summary = {
                "total_features": len(all_features),
                "selected_features": len(consensus_result["selected_features"]),
                "removed_features": len(consensus_result["removed_features"]),
                "selection_ratio": (
                    len(consensus_result["selected_features"]) / len(all_features)
                    if all_features
                    else 0
                ),
                "methods_used": len(consensus_result["methods_used"]),
                "consensus_score": consensus_result["consensus_score"],
            }

            # Create comprehensive report
            report = {
                "summary": summary,
                "consensus_result": consensus_result,
                "feature_analysis": {
                    "selected_features": consensus_result["selected_features"],
                    "removed_features": consensus_result["removed_features"],
                    "feature_votes": consensus_result["feature_votes"],
                },
                "method_comparison": {
                    method: {
                        "n_selected": result["n_selected"],
                        "selected_features": result["selected_features"][:10],  # Top 10
                        "method_specific_info": {
                            k: v
                            for k, v in result.items()
                            if k
                            not in [
                                "selected_features",
                                "removed_features",
                                "n_selected",
                                "n_removed",
                            ]
                        },
                    }
                    for method, result in consensus_result["method_results"].items()
                },
                "recommendations": self._generate_feature_selection_recommendations(
                    consensus_result
                ),
            }

            self.logger.info("Feature selection report generated successfully")

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate feature selection report: {e}")
            raise FeatureSelectionError(
                f"Failed to generate feature selection report: {e}"
            )

    def _generate_feature_selection_recommendations(
        self, consensus_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on feature selection results"""
        recommendations = []

        n_selected = consensus_result["n_selected"]
        n_methods = len(consensus_result["methods_used"])
        consensus_score = consensus_result["consensus_score"]

        if n_selected == 0:
            recommendations.append(
                "No features were selected - consider relaxing selection criteria"
            )
        elif n_selected < 5:
            recommendations.append(
                "Very few features selected - consider using more features or different methods"
            )
        elif n_selected > 50:
            recommendations.append(
                "Many features selected - consider using more aggressive selection criteria"
            )

        if consensus_score < 0.1:
            recommendations.append(
                "Low consensus among methods - consider manual feature engineering"
            )
        elif consensus_score > 0.8:
            recommendations.append(
                "High consensus among methods - selected features are likely important"
            )

        if n_methods < 3:
            recommendations.append(
                "Consider using more feature selection methods for better consensus"
            )

        return recommendations
