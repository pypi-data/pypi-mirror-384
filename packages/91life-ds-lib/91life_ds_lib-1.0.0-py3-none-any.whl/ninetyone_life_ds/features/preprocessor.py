"""
Data preprocessing functionality with comprehensive cleaning and transformation methods
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    LabelEncoder,
    OneHotEncoder,
    OrdinalEncoder,
)
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
import warnings

from ..core.logger import LoggerMixin
from ..core.exceptions import PreprocessingError
from ..core.config import config


class DataPreprocessor(LoggerMixin):
    """
    Comprehensive data preprocessing with cleaning and transformation methods

    Provides methods for:
    - Missing data handling
    - Outlier detection and treatment
    - Feature scaling and normalization
    - Categorical encoding
    - Class imbalance handling
    - Data splitting
    - Master preprocessing pipeline
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize DataPreprocessor

        Args:
            random_state: Random state for reproducibility
        """
        self.random_state = random_state
        self.logger.info(
            f"DataPreprocessor initialized with random_state={random_state}"
        )

        # Store fitted transformers for pipeline
        self.fitted_transformers = {}

    def handle_missing_values(
        self,
        data: pd.DataFrame,
        strategy: str = "auto",
        threshold: float = 0.5,
        exclude_cols: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle missing values in the dataset

        Args:
            data: Input DataFrame
            strategy: Imputation strategy ('auto', 'mean', 'median', 'mode', 'knn', 'drop')
            threshold: Threshold for dropping columns with high missingness
            exclude_cols: Columns to exclude from imputation

        Returns:
            Tuple of (cleaned_data, imputation_info)
        """
        self.logger.info(f"Handling missing values with strategy={strategy}")

        try:
            data_clean = data.copy()
            exclude_cols = exclude_cols or []

            # Calculate missing statistics
            missing_stats = data_clean.isnull().sum()
            missing_percent = (missing_stats / len(data_clean)) * 100

            imputation_info = {
                "original_missing": missing_stats.sum(),
                "columns_dropped": [],
                "imputation_methods": {},
                "missing_before": missing_stats.to_dict(),
                "missing_after": {},
            }

            # Drop columns with high missingness
            high_missing_cols = missing_percent[
                missing_percent > threshold * 100
            ].index.tolist()
            high_missing_cols = [
                col for col in high_missing_cols if col not in exclude_cols
            ]

            if high_missing_cols:
                data_clean = data_clean.drop(columns=high_missing_cols)
                imputation_info["columns_dropped"] = high_missing_cols
                self.logger.info(
                    f"Dropped {len(high_missing_cols)} columns with >{threshold*100}% missing data"
                )

            # Handle remaining missing values
            remaining_missing = data_clean.isnull().sum()
            cols_with_missing = remaining_missing[remaining_missing > 0].index.tolist()
            cols_with_missing = [
                col for col in cols_with_missing if col not in exclude_cols
            ]

            if cols_with_missing:
                for col in cols_with_missing:
                    col_data = data_clean[col]

                    # Auto-select strategy based on data type
                    if strategy == "auto":
                        if col_data.dtype in ["object", "category"]:
                            col_strategy = "mode"
                        elif col_data.dtype in ["int64", "float64"]:
                            # Check for outliers
                            if col_data.dropna().std() > col_data.dropna().mean() * 2:
                                col_strategy = "median"
                            else:
                                col_strategy = "mean"
                        else:
                            col_strategy = "mode"
                    else:
                        col_strategy = strategy

                    # Apply imputation
                    if col_strategy == "drop":
                        data_clean = data_clean.dropna(subset=[col])
                    elif col_strategy == "mean":
                        imputed_value = col_data.mean()
                        data_clean[col] = col_data.fillna(imputed_value)
                    elif col_strategy == "median":
                        imputed_value = col_data.median()
                        data_clean[col] = col_data.fillna(imputed_value)
                    elif col_strategy == "mode":
                        mode_value = col_data.mode()
                        imputed_value = (
                            mode_value[0]
                            if len(mode_value) > 0
                            else (
                                col_data.dropna().iloc[0]
                                if len(col_data.dropna()) > 0
                                else 0
                            )
                        )
                        data_clean[col] = col_data.fillna(imputed_value)
                    elif col_strategy == "knn":
                        # Use KNN imputation for numeric columns
                        if col_data.dtype in ["int64", "float64"]:
                            numeric_cols = data_clean.select_dtypes(
                                include=[np.number]
                            ).columns.tolist()
                            if len(numeric_cols) > 1:
                                knn_imputer = KNNImputer(n_neighbors=5)
                                data_clean[numeric_cols] = knn_imputer.fit_transform(
                                    data_clean[numeric_cols]
                                )
                                self.fitted_transformers["knn_imputer"] = knn_imputer
                            else:
                                # Fallback to median if only one numeric column
                                imputed_value = col_data.median()
                                data_clean[col] = col_data.fillna(imputed_value)
                        else:
                            # Fallback to mode for non-numeric
                            mode_value = col_data.mode()
                            imputed_value = mode_value[0] if len(mode_value) > 0 else 0
                            data_clean[col] = col_data.fillna(imputed_value)

                    imputation_info["imputation_methods"][col] = col_strategy

                    if col_strategy in ["mean", "median", "mode"]:
                        imputation_info["imputation_methods"][col] = {
                            "method": col_strategy,
                            "value": imputed_value,
                        }

            # Update missing statistics
            imputation_info["missing_after"] = data_clean.isnull().sum().to_dict()
            imputation_info["final_missing"] = data_clean.isnull().sum().sum()

            self.logger.info(
                f"Missing values handled: {imputation_info['original_missing']} -> {imputation_info['final_missing']}"
            )

            return data_clean, imputation_info

        except Exception as e:
            self.logger.error(f"Failed to handle missing values: {e}")
            raise PreprocessingError(f"Failed to handle missing values: {e}")

    def handle_outliers(
        self,
        data: pd.DataFrame,
        method: str = "iqr",
        strategy: str = "cap",
        threshold: float = 1.5,
        exclude_cols: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Detect and handle outliers in the dataset

        Args:
            data: Input DataFrame
            method: Outlier detection method ('iqr', 'zscore', 'isolation_forest')
            strategy: Outlier handling strategy ('cap', 'remove', 'transform')
            threshold: Threshold for outlier detection
            exclude_cols: Columns to exclude from outlier handling

        Returns:
            Tuple of (cleaned_data, outlier_info)
        """
        self.logger.info(f"Handling outliers with method={method}, strategy={strategy}")

        try:
            data_clean = data.copy()
            exclude_cols = exclude_cols or []

            # Select numeric columns
            numeric_cols = data_clean.select_dtypes(
                include=[np.number]
            ).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

            if not numeric_cols:
                self.logger.warning("No numeric columns found for outlier handling")
                return data_clean, {"message": "No numeric columns found"}

            outlier_info = {
                "method": method,
                "strategy": strategy,
                "threshold": threshold,
                "outliers_detected": {},
                "outliers_handled": {},
                "rows_removed": 0,
            }

            outlier_rows = set()

            for col in numeric_cols:
                col_data = data_clean[col].dropna()

                if len(col_data) == 0:
                    continue

                outliers_mask = pd.Series(False, index=data_clean.index)

                if method == "iqr":
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    outliers_mask = (data_clean[col] < lower_bound) | (
                        data_clean[col] > upper_bound
                    )

                elif method == "zscore":
                    z_scores = np.abs((col_data - col_data.mean()) / col_data.std())
                    outliers_mask = z_scores > threshold

                elif method == "isolation_forest":
                    if len(col_data) > 10:  # Minimum samples for isolation forest
                        iso_forest = IsolationForest(
                            contamination=0.1, random_state=self.random_state
                        )
                        outlier_labels = iso_forest.fit_predict(
                            col_data.values.reshape(-1, 1)
                        )
                        outliers_mask = pd.Series(
                            outlier_labels == -1, index=col_data.index
                        )
                    else:
                        outliers_mask = pd.Series(False, index=col_data.index)

                outliers_count = outliers_mask.sum()
                outlier_info["outliers_detected"][col] = {
                    "count": outliers_count,
                    "percentage": (outliers_count / len(data_clean)) * 100,
                }

                if outliers_count > 0:
                    if strategy == "cap":
                        # Cap outliers to bounds
                        if method == "iqr":
                            data_clean.loc[data_clean[col] < lower_bound, col] = (
                                lower_bound
                            )
                            data_clean.loc[data_clean[col] > upper_bound, col] = (
                                upper_bound
                            )
                        elif method == "zscore":
                            mean_val = col_data.mean()
                            std_val = col_data.std()
                            data_clean.loc[
                                data_clean[col] < mean_val - threshold * std_val, col
                            ] = (mean_val - threshold * std_val)
                            data_clean.loc[
                                data_clean[col] > mean_val + threshold * std_val, col
                            ] = (mean_val + threshold * std_val)

                        outlier_info["outliers_handled"][col] = "capped"

                    elif strategy == "remove":
                        # Mark rows for removal
                        outlier_rows.update(data_clean[outliers_mask].index)
                        outlier_info["outliers_handled"][col] = "marked_for_removal"

                    elif strategy == "transform":
                        # Log transform for positive values
                        if (data_clean[col] > 0).all():
                            data_clean[col] = np.log1p(data_clean[col])
                            outlier_info["outliers_handled"][col] = "log_transformed"
                        else:
                            # Square root transform
                            data_clean[col] = np.sqrt(
                                np.abs(data_clean[col])
                            ) * np.sign(data_clean[col])
                            outlier_info["outliers_handled"][col] = "sqrt_transformed"

            # Remove outlier rows if strategy is 'remove'
            if strategy == "remove" and outlier_rows:
                data_clean = data_clean.drop(index=list(outlier_rows))
                outlier_info["rows_removed"] = len(outlier_rows)
                self.logger.info(f"Removed {len(outlier_rows)} rows with outliers")

            self.logger.info(
                f"Outlier handling completed for {len(numeric_cols)} columns"
            )

            return data_clean, outlier_info

        except Exception as e:
            self.logger.error(f"Failed to handle outliers: {e}")
            raise PreprocessingError(f"Failed to handle outliers: {e}")

    def scale_features(
        self,
        data: pd.DataFrame,
        method: str = "standard",
        exclude_cols: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Scale and normalize features

        Args:
            data: Input DataFrame
            method: Scaling method ('standard', 'minmax', 'robust')
            exclude_cols: Columns to exclude from scaling

        Returns:
            Tuple of (scaled_data, scaling_info)
        """
        self.logger.info(f"Scaling features with method={method}")

        try:
            data_scaled = data.copy()
            exclude_cols = exclude_cols or []

            # Select numeric columns
            numeric_cols = data_scaled.select_dtypes(
                include=[np.number]
            ).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

            if not numeric_cols:
                self.logger.warning("No numeric columns found for scaling")
                return data_scaled, {"message": "No numeric columns found"}

            scaling_info = {
                "method": method,
                "scaled_columns": numeric_cols,
                "scaler_params": {},
            }

            # Choose scaler
            if method == "standard":
                scaler = StandardScaler()
            elif method == "minmax":
                scaler = MinMaxScaler()
            elif method == "robust":
                scaler = RobustScaler()
            else:
                raise ValueError(f"Unknown scaling method: {method}")

            # Fit and transform
            data_scaled[numeric_cols] = scaler.fit_transform(data_scaled[numeric_cols])

            # Store scaler for later use
            self.fitted_transformers[f"{method}_scaler"] = scaler

            # Store scaling parameters
            if hasattr(scaler, "mean_"):
                scaling_info["scaler_params"]["mean"] = scaler.mean_.tolist()
            if hasattr(scaler, "scale_"):
                scaling_info["scaler_params"]["scale"] = scaler.scale_.tolist()
            if hasattr(scaler, "min_"):
                scaling_info["scaler_params"]["min"] = scaler.min_.tolist()
            if hasattr(scaler, "max_"):
                scaling_info["scaler_params"]["max"] = scaler.max_.tolist()

            self.logger.info(
                f"Scaled {len(numeric_cols)} columns using {method} scaling"
            )

            return data_scaled, scaling_info

        except Exception as e:
            self.logger.error(f"Failed to scale features: {e}")
            raise PreprocessingError(f"Failed to scale features: {e}")

    def encode_categorical_features(
        self,
        data: pd.DataFrame,
        method: str = "onehot",
        target_col: Optional[str] = None,
        exclude_cols: Optional[List[str]] = None,
        max_categories: int = 10,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Encode categorical features

        Args:
            data: Input DataFrame
            method: Encoding method ('onehot', 'label', 'ordinal', 'target')
            target_col: Target column for target encoding
            exclude_cols: Columns to exclude from encoding
            max_categories: Maximum number of categories for one-hot encoding

        Returns:
            Tuple of (encoded_data, encoding_info)
        """
        self.logger.info(f"Encoding categorical features with method={method}")

        try:
            data_encoded = data.copy()
            exclude_cols = exclude_cols or []

            # Select categorical columns
            categorical_cols = data_encoded.select_dtypes(
                include=["object", "category"]
            ).columns.tolist()
            categorical_cols = [
                col for col in categorical_cols if col not in exclude_cols
            ]

            if not categorical_cols:
                self.logger.warning("No categorical columns found for encoding")
                return data_encoded, {"message": "No categorical columns found"}

            encoding_info = {
                "method": method,
                "encoded_columns": categorical_cols,
                "encoding_details": {},
            }

            for col in categorical_cols:
                col_data = data_encoded[col]
                unique_values = col_data.nunique()

                if method == "onehot" and unique_values <= max_categories:
                    # One-hot encoding
                    dummies = pd.get_dummies(col_data, prefix=col, dummy_na=True)
                    data_encoded = pd.concat([data_encoded, dummies], axis=1)
                    data_encoded = data_encoded.drop(columns=[col])
                    encoding_info["encoding_details"][col] = {
                        "method": "onehot",
                        "categories": unique_values,
                        "new_columns": dummies.columns.tolist(),
                    }

                elif method == "label":
                    # Label encoding
                    le = LabelEncoder()
                    data_encoded[col] = le.fit_transform(col_data.astype(str))
                    self.fitted_transformers[f"label_encoder_{col}"] = le
                    encoding_info["encoding_details"][col] = {
                        "method": "label",
                        "categories": unique_values,
                        "mapping": dict(zip(le.classes_, le.transform(le.classes_))),
                    }

                elif method == "ordinal":
                    # Ordinal encoding (alphabetical order)
                    oe = OrdinalEncoder(
                        handle_unknown="use_encoded_value", unknown_value=-1
                    )
                    data_encoded[col] = oe.fit_transform(
                        col_data.values.reshape(-1, 1)
                    ).flatten()
                    self.fitted_transformers[f"ordinal_encoder_{col}"] = oe
                    encoding_info["encoding_details"][col] = {
                        "method": "ordinal",
                        "categories": unique_values,
                    }

                elif (
                    method == "target"
                    and target_col
                    and target_col in data_encoded.columns
                ):
                    # Target encoding (mean encoding)
                    target_means = data_encoded.groupby(col)[target_col].mean()
                    data_encoded[col] = col_data.map(target_means)
                    encoding_info["encoding_details"][col] = {
                        "method": "target",
                        "categories": unique_values,
                        "target_means": target_means.to_dict(),
                    }

                else:
                    # Default to label encoding
                    le = LabelEncoder()
                    data_encoded[col] = le.fit_transform(col_data.astype(str))
                    self.fitted_transformers[f"label_encoder_{col}"] = le
                    encoding_info["encoding_details"][col] = {
                        "method": "label",
                        "categories": unique_values,
                    }

            self.logger.info(f"Encoded {len(categorical_cols)} categorical columns")

            return data_encoded, encoding_info

        except Exception as e:
            self.logger.error(f"Failed to encode categorical features: {e}")
            raise PreprocessingError(f"Failed to encode categorical features: {e}")

    def handle_class_imbalance(
        self,
        data: pd.DataFrame,
        target_col: str,
        method: str = "smote",
        sampling_strategy: Union[str, float] = "auto",
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Handle class imbalance in classification datasets

        Args:
            data: Input DataFrame
            target_col: Target column name
            method: Balancing method ('smote', 'adasyn', 'undersample', 'smotetomek')
            sampling_strategy: Sampling strategy for balancing
            random_state: Random state for reproducibility

        Returns:
            Tuple of (balanced_data, balancing_info)
        """
        self.logger.info(f"Handling class imbalance with method={method}")

        try:
            if target_col not in data.columns:
                raise PreprocessingError(f"Target column '{target_col}' not found")

            # Check if it's a classification problem
            target_data = data[target_col]
            if target_data.dtype in ["int64", "float64"] and target_data.nunique() > 10:
                self.logger.warning(
                    "Target appears to be continuous - skipping class imbalance handling"
                )
                return data, {"message": "Target appears to be continuous"}

            # Get class distribution
            class_counts = target_data.value_counts()
            imbalance_ratio = class_counts.max() / class_counts.min()

            balancing_info = {
                "method": method,
                "original_distribution": class_counts.to_dict(),
                "imbalance_ratio": imbalance_ratio,
                "sampling_strategy": sampling_strategy,
            }

            # Select features for balancing (exclude target)
            feature_cols = [col for col in data.columns if col != target_col]
            X = data[feature_cols]
            y = data[target_col]

            # Choose balancing method
            random_state = random_state or self.random_state

            if method == "smote":
                sampler = SMOTE(
                    sampling_strategy=sampling_strategy, random_state=random_state
                )
            elif method == "adasyn":
                sampler = ADASYN(
                    sampling_strategy=sampling_strategy, random_state=random_state
                )
            elif method == "undersample":
                sampler = RandomUnderSampler(
                    sampling_strategy=sampling_strategy, random_state=random_state
                )
            elif method == "smotetomek":
                sampler = SMOTETomek(
                    sampling_strategy=sampling_strategy, random_state=random_state
                )
            else:
                raise ValueError(f"Unknown balancing method: {method}")

            # Apply balancing
            X_balanced, y_balanced = sampler.fit_resample(X, y)

            # Create balanced DataFrame
            balanced_data = pd.DataFrame(X_balanced, columns=feature_cols)
            balanced_data[target_col] = y_balanced

            # Update balancing info
            new_class_counts = pd.Series(y_balanced).value_counts()
            balancing_info["new_distribution"] = new_class_counts.to_dict()
            balancing_info["new_imbalance_ratio"] = (
                new_class_counts.max() / new_class_counts.min()
            )
            balancing_info["samples_added"] = len(balanced_data) - len(data)

            self.logger.info(
                f"Class imbalance handled: {len(data)} -> {len(balanced_data)} samples"
            )
            self.logger.info(
                f"Imbalance ratio: {imbalance_ratio:.2f} -> {balancing_info['new_imbalance_ratio']:.2f}"
            )

            return balanced_data, balancing_info

        except Exception as e:
            self.logger.error(f"Failed to handle class imbalance: {e}")
            raise PreprocessingError(f"Failed to handle class imbalance: {e}")

    def split_data(
        self,
        data: pd.DataFrame,
        target_col: str,
        test_size: float = 0.2,
        val_size: float = 0.1,
        stratify: bool = True,
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Split data into train, validation, and test sets

        Args:
            data: Input DataFrame
            target_col: Target column name
            test_size: Proportion of data for test set
            val_size: Proportion of data for validation set
            stratify: Whether to stratify based on target
            random_state: Random state for reproducibility

        Returns:
            Tuple of (train_data, val_data, test_data, split_info)
        """
        self.logger.info(f"Splitting data: test_size={test_size}, val_size={val_size}")

        try:
            if target_col not in data.columns:
                raise PreprocessingError(f"Target column '{target_col}' not found")

            random_state = random_state or self.random_state

            # Calculate split sizes
            total_size = len(data)
            test_samples = int(total_size * test_size)
            val_samples = int(total_size * val_size)
            train_samples = total_size - test_samples - val_samples

            split_info = {
                "total_samples": total_size,
                "train_samples": train_samples,
                "val_samples": val_samples,
                "test_samples": test_samples,
                "train_ratio": train_samples / total_size,
                "val_ratio": val_samples / total_size,
                "test_ratio": test_samples / total_size,
                "stratify": stratify,
            }

            # Prepare for stratification
            stratify_col = data[target_col] if stratify else None

            # First split: train+val vs test
            from sklearn.model_selection import train_test_split

            train_val_data, test_data = train_test_split(
                data,
                test_size=test_size,
                stratify=stratify_col,
                random_state=random_state,
            )

            # Second split: train vs val
            if val_size > 0:
                stratify_col_train = train_val_data[target_col] if stratify else None
                val_ratio = val_size / (1 - test_size)

                train_data, val_data = train_test_split(
                    train_val_data,
                    test_size=val_ratio,
                    stratify=stratify_col_train,
                    random_state=random_state,
                )
            else:
                train_data = train_val_data
                val_data = pd.DataFrame()

            # Update split info with actual sizes
            split_info["actual_train_samples"] = len(train_data)
            split_info["actual_val_samples"] = len(val_data)
            split_info["actual_test_samples"] = len(test_data)

            # Add class distribution info for classification
            if (
                data[target_col].dtype in ["object", "category"]
                or data[target_col].nunique() <= 10
            ):
                split_info["train_class_distribution"] = (
                    train_data[target_col].value_counts().to_dict()
                )
                if len(val_data) > 0:
                    split_info["val_class_distribution"] = (
                        val_data[target_col].value_counts().to_dict()
                    )
                split_info["test_class_distribution"] = (
                    test_data[target_col].value_counts().to_dict()
                )

            self.logger.info(
                f"Data split completed: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}"
            )

            return train_data, val_data, test_data, split_info

        except Exception as e:
            self.logger.error(f"Failed to split data: {e}")
            raise PreprocessingError(f"Failed to split data: {e}")

    def create_preprocessing_pipeline(
        self,
        data: pd.DataFrame,
        target_col: str,
        task_type: str = "regression",
        missing_strategy: str = "auto",
        outlier_method: str = "iqr",
        scaling_method: str = "standard",
        encoding_method: str = "onehot",
        handle_imbalance: bool = False,
        test_size: float = 0.2,
        val_size: float = 0.1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a complete preprocessing pipeline

        Args:
            data: Input DataFrame
            target_col: Target column name
            task_type: 'classification' or 'regression'
            missing_strategy: Strategy for handling missing values
            outlier_method: Method for outlier detection
            scaling_method: Method for feature scaling
            encoding_method: Method for categorical encoding
            handle_imbalance: Whether to handle class imbalance
            test_size: Proportion for test set
            val_size: Proportion for validation set
            **kwargs: Additional parameters for individual steps

        Returns:
            Dictionary with complete preprocessing results
        """
        self.logger.info("Creating complete preprocessing pipeline")

        try:
            pipeline_results = {
                "original_data_shape": data.shape,
                "target_column": target_col,
                "task_type": task_type,
                "pipeline_steps": [],
            }

            current_data = data.copy()

            # Step 1: Handle missing values
            self.logger.info("Step 1: Handling missing values")
            current_data, missing_info = self.handle_missing_values(
                current_data,
                strategy=missing_strategy,
                threshold=kwargs.get("missing_threshold", 0.5),
                exclude_cols=kwargs.get("exclude_cols"),
            )
            pipeline_results["missing_values"] = missing_info
            pipeline_results["pipeline_steps"].append("missing_values")

            # Step 2: Handle outliers
            self.logger.info("Step 2: Handling outliers")
            current_data, outlier_info = self.handle_outliers(
                current_data,
                method=outlier_method,
                strategy=kwargs.get("outlier_strategy", "cap"),
                threshold=kwargs.get("outlier_threshold", 1.5),
                exclude_cols=kwargs.get("exclude_cols"),
            )
            pipeline_results["outliers"] = outlier_info
            pipeline_results["pipeline_steps"].append("outliers")

            # Step 3: Encode categorical features
            self.logger.info("Step 3: Encoding categorical features")
            current_data, encoding_info = self.encode_categorical_features(
                current_data,
                method=encoding_method,
                target_col=target_col,
                exclude_cols=kwargs.get("exclude_cols"),
                max_categories=kwargs.get("max_categories", 10),
            )
            pipeline_results["encoding"] = encoding_info
            pipeline_results["pipeline_steps"].append("encoding")

            # Step 4: Handle class imbalance (classification only)
            if handle_imbalance and task_type == "classification":
                self.logger.info("Step 4: Handling class imbalance")
                current_data, imbalance_info = self.handle_class_imbalance(
                    current_data,
                    target_col=target_col,
                    method=kwargs.get("imbalance_method", "smote"),
                    sampling_strategy=kwargs.get("sampling_strategy", "auto"),
                )
                pipeline_results["class_imbalance"] = imbalance_info
                pipeline_results["pipeline_steps"].append("class_imbalance")

            # Step 5: Scale features
            self.logger.info("Step 5: Scaling features")
            current_data, scaling_info = self.scale_features(
                current_data,
                method=scaling_method,
                exclude_cols=[target_col] + kwargs.get("exclude_cols", []),
            )
            pipeline_results["scaling"] = scaling_info
            pipeline_results["pipeline_steps"].append("scaling")

            # Step 6: Split data
            self.logger.info("Step 6: Splitting data")
            train_data, val_data, test_data, split_info = self.split_data(
                current_data,
                target_col=target_col,
                test_size=test_size,
                val_size=val_size,
                stratify=task_type == "classification",
            )
            pipeline_results["data_split"] = split_info
            pipeline_results["pipeline_steps"].append("data_split")

            # Final results
            pipeline_results["processed_data_shape"] = current_data.shape
            pipeline_results["train_data"] = train_data
            pipeline_results["val_data"] = val_data
            pipeline_results["test_data"] = test_data
            pipeline_results["feature_columns"] = [
                col for col in current_data.columns if col != target_col
            ]

            self.logger.info("Preprocessing pipeline completed successfully")

            return pipeline_results

        except Exception as e:
            self.logger.error(f"Failed to create preprocessing pipeline: {e}")
            raise PreprocessingError(f"Failed to create preprocessing pipeline: {e}")

    def get_fitted_transformers(self) -> Dict[str, Any]:
        """Get all fitted transformers for later use"""
        return self.fitted_transformers.copy()

    def transform_new_data(
        self, data: pd.DataFrame, exclude_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Apply fitted transformers to new data

        Args:
            data: New data to transform
            exclude_cols: Columns to exclude from transformation

        Returns:
            Transformed data
        """
        self.logger.info("Applying fitted transformers to new data")

        try:
            data_transformed = data.copy()
            exclude_cols = exclude_cols or []

            # Apply each fitted transformer
            for name, transformer in self.fitted_transformers.items():
                if "scaler" in name:
                    # Apply scaling to numeric columns
                    numeric_cols = data_transformed.select_dtypes(
                        include=[np.number]
                    ).columns.tolist()
                    numeric_cols = [
                        col for col in numeric_cols if col not in exclude_cols
                    ]
                    if numeric_cols:
                        data_transformed[numeric_cols] = transformer.transform(
                            data_transformed[numeric_cols]
                        )

                elif "encoder" in name:
                    # Apply encoding to specific column
                    col_name = name.replace("label_encoder_", "").replace(
                        "ordinal_encoder_", ""
                    )
                    if col_name in data_transformed.columns:
                        if "label" in name:
                            data_transformed[col_name] = transformer.transform(
                                data_transformed[col_name].astype(str)
                            )
                        else:
                            data_transformed[col_name] = transformer.transform(
                                data_transformed[col_name].values.reshape(-1, 1)
                            ).flatten()

            self.logger.info("New data transformation completed")

            return data_transformed

        except Exception as e:
            self.logger.error(f"Failed to transform new data: {e}")
            raise PreprocessingError(f"Failed to transform new data: {e}")
