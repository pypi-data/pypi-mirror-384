"""
Data exploration and quality assessment functionality
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from ..core.logger import LoggerMixin
from ..core.exceptions import DataValidationError


class DataExplorer(LoggerMixin):
    """
    Comprehensive data exploration and quality assessment

    Provides methods for:
    - Basic dataset information
    - Missing data analysis
    - Data quality checks
    - Statistical analysis
    - Distribution analysis
    - Data readiness scoring
    """

    def __init__(self, sample_size: int = 10):
        """
        Initialize DataExplorer

        Args:
            sample_size: Number of columns to sample for detailed analysis
        """
        self.sample_size = sample_size
        self.logger.info(f"DataExplorer initialized with sample_size={sample_size}")

    def analyze_basic_info(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze basic dataset information

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with basic dataset information
        """
        self.logger.info("Analyzing basic dataset information")

        try:
            info = {
                "shape": data.shape,
                "memory_usage": data.memory_usage(deep=True).sum(),
                "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
                "dtypes": data.dtypes.value_counts().to_dict(),
                "columns": list(data.columns),
                "index_type": str(type(data.index)),
                "has_duplicates": data.duplicated().any(),
                "duplicate_count": data.duplicated().sum(),
                "total_cells": data.shape[0] * data.shape[1],
                "non_null_cells": data.count().sum(),
                "null_cells": data.isnull().sum().sum(),
                "completeness_ratio": data.count().sum()
                / (data.shape[0] * data.shape[1]),
            }

            self.logger.info(f"Dataset shape: {info['shape']}")
            self.logger.info(f"Memory usage: {info['memory_usage_mb']:.2f} MB")
            self.logger.info(f"Completeness: {info['completeness_ratio']:.2%}")

            return info

        except Exception as e:
            self.logger.error(f"Failed to analyze basic info: {e}")
            raise DataValidationError(f"Failed to analyze basic info: {e}")

    def analyze_missing_data(
        self, data: pd.DataFrame, threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Analyze missing data patterns

        Args:
            data: Input DataFrame
            threshold: Threshold for high missingness (0-1)

        Returns:
            Dictionary with missing data analysis
        """
        self.logger.info(f"Analyzing missing data with threshold={threshold}")

        try:
            missing_stats = data.isnull().sum()
            missing_percent = (missing_stats / len(data)) * 100

            analysis = {
                "total_missing": missing_stats.sum(),
                "missing_percentage": (
                    missing_stats.sum() / (data.shape[0] * data.shape[1])
                )
                * 100,
                "columns_with_missing": (missing_stats > 0).sum(),
                "columns_with_high_missing": (missing_percent > threshold * 100).sum(),
                "missing_by_column": missing_stats.to_dict(),
                "missing_percent_by_column": missing_percent.to_dict(),
                "high_missing_columns": missing_percent[
                    missing_percent > threshold * 100
                ].to_dict(),
                "missing_patterns": self._analyze_missing_patterns(data),
                "recommendations": self._get_missing_data_recommendations(
                    missing_percent, threshold
                ),
            }

            self.logger.info(f"Total missing values: {analysis['total_missing']}")
            self.logger.info(
                f"Columns with missing data: {analysis['columns_with_missing']}"
            )
            self.logger.info(
                f"High missing columns (>={threshold*100}%): {analysis['columns_with_high_missing']}"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze missing data: {e}")
            raise DataValidationError(f"Failed to analyze missing data: {e}")

    def _analyze_missing_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in missing data"""
        missing_matrix = data.isnull()

        # Check for completely missing rows/columns
        completely_missing_rows = missing_matrix.all(axis=1).sum()
        completely_missing_cols = missing_matrix.all(axis=0).sum()

        # Check for missing data clusters
        missing_clusters = []
        for col in data.columns:
            if data[col].isnull().any():
                missing_indices = data[data[col].isnull()].index.tolist()
                if len(missing_indices) > 1:
                    # Check for consecutive missing values
                    consecutive_gaps = []
                    start = missing_indices[0]
                    end = missing_indices[0]

                    for i in range(1, len(missing_indices)):
                        if missing_indices[i] == end + 1:
                            end = missing_indices[i]
                        else:
                            if end - start > 0:
                                consecutive_gaps.append((start, end))
                            start = missing_indices[i]
                            end = missing_indices[i]

                    if end - start > 0:
                        consecutive_gaps.append((start, end))

                    if consecutive_gaps:
                        missing_clusters.append(
                            {"column": col, "consecutive_gaps": consecutive_gaps}
                        )

        return {
            "completely_missing_rows": completely_missing_rows,
            "completely_missing_cols": completely_missing_cols,
            "missing_clusters": missing_clusters,
        }

    def _get_missing_data_recommendations(
        self, missing_percent: pd.Series, threshold: float
    ) -> List[str]:
        """Generate recommendations for missing data handling"""
        recommendations = []

        high_missing_cols = missing_percent[missing_percent > threshold * 100]

        if len(high_missing_cols) > 0:
            recommendations.append(
                f"Consider dropping {len(high_missing_cols)} columns with >{threshold*100}% missing data"
            )

        if missing_percent.max() > 0.8:
            recommendations.append(
                "Some columns have >80% missing data - consider exclusion"
            )

        if missing_percent.sum() > 0:
            recommendations.append("Implement missing data imputation strategy")

        if missing_percent.min() == 0:
            recommendations.append(
                "Some columns are complete - use as reference for imputation"
            )

        return recommendations

    def analyze_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data quality issues

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with data quality analysis
        """
        self.logger.info("Analyzing data quality")

        try:
            quality_issues = {
                "duplicates": {
                    "row_duplicates": data.duplicated().sum(),
                    "row_duplicate_percentage": (data.duplicated().sum() / len(data))
                    * 100,
                },
                "cardinality": {},
                "type_consistency": {},
                "outliers": {},
                "data_types": data.dtypes.value_counts().to_dict(),
            }

            # Analyze cardinality for each column
            for col in data.columns:
                if data[col].dtype == "object":
                    unique_count = data[col].nunique()
                    total_count = len(data[col])
                    cardinality_ratio = unique_count / total_count

                    quality_issues["cardinality"][col] = {
                        "unique_values": unique_count,
                        "total_values": total_count,
                        "cardinality_ratio": cardinality_ratio,
                        "is_high_cardinality": cardinality_ratio > 0.9,
                        "is_low_cardinality": cardinality_ratio < 0.01,
                    }

            # Check for type consistency
            for col in data.columns:
                if data[col].dtype == "object":
                    # Check if column could be numeric
                    try:
                        pd.to_numeric(data[col], errors="raise")
                        quality_issues["type_consistency"][col] = "Could be numeric"
                    except (ValueError, TypeError):
                        # Check if column could be datetime
                        try:
                            pd.to_datetime(data[col], errors="raise")
                            quality_issues["type_consistency"][
                                col
                            ] = "Could be datetime"
                        except (ValueError, TypeError):
                            quality_issues["type_consistency"][col] = "Text/Categorical"

            # Basic outlier detection for numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
                quality_issues["outliers"][col] = {
                    "count": len(outliers),
                    "percentage": (len(outliers) / len(data)) * 100,
                    "bounds": {"lower": lower_bound, "upper": upper_bound},
                }

            self.logger.info(
                f"Found {quality_issues['duplicates']['row_duplicates']} duplicate rows"
            )
            self.logger.info(
                f"Analyzed cardinality for {len(quality_issues['cardinality'])} columns"
            )

            return quality_issues

        except Exception as e:
            self.logger.error(f"Failed to analyze data quality: {e}")
            raise DataValidationError(f"Failed to analyze data quality: {e}")

    def analyze_statistical_patterns(
        self, data: pd.DataFrame, sample_cols: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze statistical patterns in the data

        Args:
            data: Input DataFrame
            sample_cols: Number of columns to sample for detailed analysis

        Returns:
            Dictionary with statistical analysis
        """
        self.logger.info("Analyzing statistical patterns")

        try:
            sample_cols = sample_cols or self.sample_size
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(numeric_cols) == 0:
                return {"message": "No numeric columns found for statistical analysis"}

            # Sample columns if too many
            if len(numeric_cols) > sample_cols:
                numeric_cols = numeric_cols[:sample_cols]
                self.logger.info(f"Sampling {sample_cols} numeric columns for analysis")

            stats_analysis = {
                "descriptive_stats": data[numeric_cols].describe().to_dict(),
                "correlation_matrix": data[numeric_cols].corr().to_dict(),
                "skewness": data[numeric_cols].skew().to_dict(),
                "kurtosis": data[numeric_cols].kurtosis().to_dict(),
                "normality_tests": {},
            }

            # Normality tests for each numeric column
            for col in numeric_cols:
                col_data = data[col].dropna()
                if len(col_data) > 3:  # Minimum sample size for tests
                    try:
                        shapiro_stat, shapiro_p = stats.shapiro(col_data)
                        stats_analysis["normality_tests"][col] = {
                            "shapiro_wilk": {
                                "statistic": shapiro_stat,
                                "p_value": shapiro_p,
                            },
                            "is_normal": shapiro_p > 0.05,
                        }
                    except Exception as e:
                        self.logger.warning(f"Failed normality test for {col}: {e}")
                        stats_analysis["normality_tests"][col] = {"error": str(e)}

            self.logger.info(
                f"Analyzed statistical patterns for {len(numeric_cols)} columns"
            )

            return stats_analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze statistical patterns: {e}")
            raise DataValidationError(f"Failed to analyze statistical patterns: {e}")

    def analyze_distributions(
        self, data: pd.DataFrame, sample_cols: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze data distributions

        Args:
            data: Input DataFrame
            sample_cols: Number of columns to sample for detailed analysis

        Returns:
            Dictionary with distribution analysis
        """
        self.logger.info("Analyzing data distributions")

        try:
            sample_cols = sample_cols or self.sample_size
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(numeric_cols) == 0:
                return {"message": "No numeric columns found for distribution analysis"}

            # Sample columns if too many
            if len(numeric_cols) > sample_cols:
                numeric_cols = numeric_cols[:sample_cols]

            distribution_analysis = {
                "value_ranges": {},
                "distribution_types": {},
                "zero_values": {},
                "negative_values": {},
                "constant_columns": [],
            }

            for col in numeric_cols:
                col_data = data[col].dropna()

                if len(col_data) == 0:
                    continue

                # Value ranges
                distribution_analysis["value_ranges"][col] = {
                    "min": col_data.min(),
                    "max": col_data.max(),
                    "range": col_data.max() - col_data.min(),
                    "mean": col_data.mean(),
                    "median": col_data.median(),
                    "std": col_data.std(),
                }

                # Distribution type
                if col_data.nunique() == 1:
                    distribution_analysis["constant_columns"].append(col)
                    distribution_analysis["distribution_types"][col] = "constant"
                elif col_data.nunique() == 2:
                    distribution_analysis["distribution_types"][col] = "binary"
                elif col_data.nunique() <= 10:
                    distribution_analysis["distribution_types"][col] = "discrete"
                else:
                    distribution_analysis["distribution_types"][col] = "continuous"

                # Special value analysis
                distribution_analysis["zero_values"][col] = (col_data == 0).sum()
                distribution_analysis["negative_values"][col] = (col_data < 0).sum()

            self.logger.info(f"Analyzed distributions for {len(numeric_cols)} columns")
            self.logger.info(
                f"Found {len(distribution_analysis['constant_columns'])} constant columns"
            )

            return distribution_analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze distributions: {e}")
            raise DataValidationError(f"Failed to analyze distributions: {e}")

    def calculate_data_readiness_score(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate data readiness score for machine learning

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with data readiness assessment
        """
        self.logger.info("Calculating data readiness score")

        try:
            # Get basic info
            basic_info = self.analyze_basic_info(data)
            missing_analysis = self.analyze_missing_data(data)
            quality_analysis = self.analyze_data_quality(data)

            # Calculate scores (0-100)
            scores = {}

            # Completeness score
            completeness_score = basic_info["completeness_ratio"] * 100
            scores["completeness"] = completeness_score

            # Missing data score
            missing_penalty = missing_analysis["missing_percentage"]
            missing_score = max(0, 100 - missing_penalty)
            scores["missing_data"] = missing_score

            # Duplicate score
            duplicate_penalty = quality_analysis["duplicates"][
                "row_duplicate_percentage"
            ]
            duplicate_score = max(0, 100 - duplicate_penalty)
            scores["duplicates"] = duplicate_score

            # Data type consistency score
            type_issues = len(
                [
                    v
                    for v in quality_analysis["type_consistency"].values()
                    if "Could be" in v
                ]
            )
            type_score = max(0, 100 - (type_issues / len(data.columns)) * 100)
            scores["type_consistency"] = type_score

            # Size adequacy score
            size_score = min(100, (data.shape[0] / 1000) * 10)  # 1000 rows = 10 points
            scores["size_adequacy"] = size_score

            # Overall score
            overall_score = np.mean(list(scores.values()))
            scores["overall"] = overall_score

            # Recommendations
            recommendations = []
            if completeness_score < 80:
                recommendations.append("Improve data completeness")
            if missing_score < 80:
                recommendations.append("Address missing data issues")
            if duplicate_score < 90:
                recommendations.append("Remove duplicate records")
            if type_score < 80:
                recommendations.append("Fix data type inconsistencies")
            if size_score < 50:
                recommendations.append("Consider collecting more data")

            readiness_assessment = {
                "scores": scores,
                "overall_readiness": overall_score,
                "readiness_level": self._get_readiness_level(overall_score),
                "recommendations": recommendations,
                "is_ready_for_ml": overall_score >= 70,
            }

            self.logger.info(f"Data readiness score: {overall_score:.1f}/100")
            self.logger.info(
                f"Readiness level: {readiness_assessment['readiness_level']}"
            )

            return readiness_assessment

        except Exception as e:
            self.logger.error(f"Failed to calculate data readiness score: {e}")
            raise DataValidationError(f"Failed to calculate data readiness score: {e}")

    def _get_readiness_level(self, score: float) -> str:
        """Get readiness level based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Poor"
        else:
            return "Very Poor"

    def analyze_data_patterns(
        self, data: pd.DataFrame, sample_size: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze data patterns, distinct values, and distributions

        Args:
            data: Input DataFrame
            sample_size: Number of columns to sample for detailed analysis

        Returns:
            Dictionary with pattern analysis results
        """
        self.logger.info(f"Analyzing data patterns with sample_size={sample_size}")

        try:
            # Separate numeric and categorical columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            categorical_cols = data.select_dtypes(include=["object", "bool"]).columns

            self.logger.info(
                f"Found {len(numeric_cols)} numeric and {len(categorical_cols)} categorical columns"
            )

            # Analyze categorical columns
            cat_analysis = []
            for col in categorical_cols:
                n_unique = data[col].nunique()
                n_nulls = data[col].isnull().sum()
                cat_analysis.append(
                    {
                        "column": col,
                        "distinct_values": n_unique,
                        "null_count": n_nulls,
                        "null_pct": (n_nulls / len(data)) * 100,
                    }
                )

            cat_df = pd.DataFrame(cat_analysis).sort_values(
                "distinct_values", ascending=False
            )

            # Analyze numeric columns
            numeric_stats = None
            if len(numeric_cols) > 0:
                # Get basic statistics for numeric columns with non-null values
                numeric_stats = data[numeric_cols].describe().T
                numeric_stats["null_count"] = data[numeric_cols].isnull().sum()
                numeric_stats["null_pct"] = (
                    numeric_stats["null_count"] / len(data)
                ) * 100

            results = {
                "categorical": cat_df,
                "numeric_stats": numeric_stats,
                "numeric_columns_count": len(numeric_cols),
                "categorical_columns_count": len(categorical_cols),
                "total_columns": len(data.columns),
            }

            self.logger.info(
                f"Data patterns analysis completed: {len(cat_df)} categorical, {len(numeric_cols)} numeric columns"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed to analyze data patterns: {e}")
            raise DataValidationError(f"Failed to analyze data patterns: {e}")

    def analyze_data_quality_detailed(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data quality issues and provide detailed warnings

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with detailed quality analysis
        """
        self.logger.info("Performing detailed data quality analysis")

        try:
            warnings_list = []

            # 1. Duplicate Detection
            duplicate_rows = data.duplicated().sum()
            duplicate_pct = (duplicate_rows / len(data)) * 100

            if duplicate_pct > 5:
                warnings_list.append(
                    f"HIGH: {duplicate_pct:.2f}% duplicate rows detected"
                )
            elif duplicate_pct > 0:
                warnings_list.append(
                    f"MEDIUM: {duplicate_pct:.2f}% duplicate rows detected"
                )

            # 2. Cardinality Analysis
            high_cardinality_cols = []
            low_cardinality_cols = []

            for col in data.columns:
                unique_count = data[col].nunique()
                unique_ratio = unique_count / len(data)

                # High cardinality (potential ID columns)
                if unique_ratio > 0.95 and unique_count > 100:
                    high_cardinality_cols.append((col, unique_count, unique_ratio))

                # Low cardinality (potential constant columns)
                if unique_count == 1:
                    low_cardinality_cols.append((col, unique_count))

            if len(high_cardinality_cols) > 0:
                warnings_list.append(
                    f"INFO: {len(high_cardinality_cols)} high cardinality columns (potential IDs)"
                )

            if len(low_cardinality_cols) > 0:
                warnings_list.append(
                    f"HIGH: {len(low_cardinality_cols)} constant columns (no variance)"
                )

            # 3. Data Type Consistency
            mixed_type_cols = []
            for col in data.select_dtypes(include=["object"]).columns:
                if data[col].notna().sum() > 0:
                    sample_types = data[col].dropna().apply(type).unique()
                    if len(sample_types) > 1:
                        mixed_type_cols.append((col, len(sample_types)))

            if len(mixed_type_cols) > 0:
                warnings_list.append(
                    f"MEDIUM: {len(mixed_type_cols)} columns with mixed data types"
                )

            # 4. Infinite and Special Values
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            inf_cols = []

            for col in numeric_cols:
                inf_count = np.isinf(data[col]).sum()
                if inf_count > 0:
                    inf_cols.append((col, inf_count))

            if len(inf_cols) > 0:
                warnings_list.append(
                    f"HIGH: {len(inf_cols)} columns contain infinite values"
                )

            # 5. Zero Variance Columns
            zero_var_cols = []
            for col in numeric_cols:
                if data[col].notna().sum() > 0:
                    variance = data[col].var()
                    if variance == 0 or pd.isna(variance):
                        zero_var_cols.append(col)

            if len(zero_var_cols) > 0:
                warnings_list.append(
                    f"MEDIUM: {len(zero_var_cols)} numeric columns have zero variance"
                )

            results = {
                "duplicate_rows": duplicate_rows,
                "duplicate_percentage": duplicate_pct,
                "high_cardinality_cols": high_cardinality_cols,
                "constant_cols": low_cardinality_cols,
                "mixed_type_cols": mixed_type_cols,
                "infinite_value_cols": inf_cols,
                "zero_variance_cols": zero_var_cols,
                "warnings": warnings_list,
                "total_warnings": len(warnings_list),
            }

            self.logger.info(
                f"Data quality analysis completed: {len(warnings_list)} warnings found"
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed to analyze data quality: {e}")
            raise DataValidationError(f"Failed to analyze data quality: {e}")

    def generate_comprehensive_report(
        self,
        data: pd.DataFrame,
        dataset_name: str = "Dataset",
        perform_clustering: bool = False,
        n_clusters: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive data exploration report combining all analysis methods

        Args:
            data: Input DataFrame
            dataset_name: Name of the dataset for the report
            perform_clustering: Whether to perform clustering analysis
            n_clusters: Number of clusters for K-means

        Returns:
            Dictionary with comprehensive report
        """
        self.logger.info(f"Generating comprehensive report for {dataset_name}")

        try:
            report = {
                "dataset_name": dataset_name,
                "generated_at": pd.Timestamp.now().isoformat(),
                "total_rows": data.shape[0],
                "total_columns": data.shape[1],
            }

            # 1. Basic Information
            self.logger.info("Analyzing basic dataset information...")
            report["basic_info"] = self.analyze_basic_info(data)

            # 2. Missing Data
            self.logger.info("Analyzing missing data patterns...")
            report["missing_data"] = self.analyze_missing_data(data, threshold=0.5)

            # 3. Data Patterns
            self.logger.info("Analyzing data patterns and distributions...")
            report["patterns"] = self.analyze_data_patterns(data, sample_size=10)

            # 4. Statistical Analysis
            self.logger.info("Performing statistical analysis...")
            report["statistics"] = self.analyze_statistical_patterns(
                data, sample_cols=10
            )

            # 5. Data Quality
            self.logger.info("Performing data quality analysis...")
            report["quality"] = self.analyze_data_quality_detailed(data)

            # 6. Clustering (optional)
            if perform_clustering:
                self.logger.info("Performing clustering analysis...")
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                valid_cols = [
                    col for col in numeric_cols if data[col].notna().sum() > 100
                ]

                if len(valid_cols) >= 2:
                    # Select subset of data for clustering
                    cluster_data = data[valid_cols].dropna()

                    if len(cluster_data) > n_clusters:
                        # Standardize the data
                        scaler = StandardScaler()
                        scaled_data = scaler.fit_transform(
                            cluster_data.iloc[:, : min(5, len(valid_cols))]
                        )

                        # Perform K-means clustering
                        kmeans = KMeans(
                            n_clusters=n_clusters, random_state=42, n_init=10
                        )
                        clusters = kmeans.fit_predict(scaled_data)

                        cluster_counts = pd.Series(clusters).value_counts().sort_index()

                        report["clustering"] = {
                            "n_clusters": n_clusters,
                            "cluster_counts": cluster_counts.to_dict(),
                            "features_used": list(
                                cluster_data.columns[: min(5, len(valid_cols))]
                            ),
                            "total_samples": len(clusters),
                        }

                        self.logger.info(
                            f"Clustering completed with {n_clusters} clusters"
                        )
                    else:
                        self.logger.warning("Insufficient data for clustering analysis")
                        report["clustering"] = None
                else:
                    self.logger.warning("Insufficient numeric columns for clustering")
                    report["clustering"] = None
            else:
                report["clustering"] = None

            # 7. Data Readiness Score
            self.logger.info("Calculating data readiness score...")
            report["readiness"] = self.calculate_data_readiness_score(data)

            # Summary
            report["summary"] = {
                "total_rows": data.shape[0],
                "total_columns": data.shape[1],
                "memory_usage_mb": report["basic_info"]["memory_usage_mb"],
                "missing_percentage": report["missing_data"]["missing_percentage"],
                "quality_warnings": len(report["quality"]["warnings"]),
                "readiness_score": report["readiness"]["overall_readiness"],
                "readiness_level": report["readiness"]["readiness_level"],
            }

            self.logger.info(
                f"Comprehensive report generated successfully for {dataset_name}"
            )

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {e}")
            raise DataValidationError(f"Failed to generate comprehensive report: {e}")

    def generate_comprehensive_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data analysis report

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with complete analysis
        """
        self.logger.info("Generating comprehensive data analysis")

        try:
            analysis = {
                "basic_info": self.analyze_basic_info(data),
                "missing_data": self.analyze_missing_data(data),
                "data_quality": self.analyze_data_quality(data),
                "statistical_patterns": self.analyze_statistical_patterns(data),
                "distributions": self.analyze_distributions(data),
                "readiness_assessment": self.calculate_data_readiness_score(data),
            }

            self.logger.info("Comprehensive analysis completed successfully")

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive analysis: {e}")
            raise DataValidationError(f"Failed to generate comprehensive analysis: {e}")
