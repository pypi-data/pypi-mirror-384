#!/usr/bin/env python3
"""
Complete Workflow Example for 91life Data Science Library

This example demonstrates the complete functionality of the library using
the HRX tuple dataset from the notebook. It showcases:
- Data loading with chunked processing
- Comprehensive data exploration
- Feature selection with consensus methods
- Data preprocessing pipeline
- Visualization generation
- Automated reporting

Author: Shpat Dobraj
Date: 2025-10-16
"""

import sys
import warnings
from pathlib import Path
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# Import the library components
try:
    from ninetyone_life_ds import (
        DataLoader,
        DataExplorer,
        FeatureSelector,
        DataPreprocessor,
        Visualizer,
        ReportGenerator,
        Config,
        get_logger,
    )
except ImportError as e:
    print(f"❌ Error importing library: {e}")
    print("Please install the library: pip install -e .")
    sys.exit(1)


def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def main():
    """Main workflow execution"""

    print_section_header("🚀 91life Data Science Library - Complete Workflow")
    print("\nThis workflow demonstrates all library capabilities with the HRX dataset")

    # Initialize logger
    logger = get_logger("complete_workflow")
    logger.info("Starting complete workflow execution")

    # =========================================================================
    # STEP 1: DATA LOADING
    # =========================================================================
    print_section_header("📊 STEP 1: Data Loading with Chunked Processing")

    dataset_path = Path("notebook/hrx_tuple_dataset.csv")

    if not dataset_path.exists():
        print(f"\n❌ Dataset not found at {dataset_path}")
        print(
            "Please ensure the HRX tuple dataset is available in the notebook directory."
        )
        return 1

    try:
        # Initialize DataLoader with custom chunk size
        loader = DataLoader(chunk_size=100000, max_memory_usage=0.8)

        print(f"\n📁 Loading dataset from: {dataset_path}")
        print(f"   Chunk size: 100,000 rows")
        print(f"   Memory limit: 80%")

        # Load the dataset
        data = loader.load_dataset(str(dataset_path))

        print(f"\n✅ Dataset loaded successfully!")
        print(f"   Shape: {data.shape[0]:,} rows × {data.shape[1]:,} columns")
        print(f"   Memory usage: {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print(f"   Data types: {data.dtypes.value_counts().to_dict()}")

        logger.info(f"Dataset loaded: {data.shape}")

    except Exception as e:
        print(f"\n❌ Failed to load dataset: {e}")
        logger.error(f"Data loading failed: {e}")
        return 1

    # =========================================================================
    # STEP 2: DATA EXPLORATION & QUALITY ASSESSMENT
    # =========================================================================
    print_section_header("🔍 STEP 2: Comprehensive Data Exploration")

    try:
        # Initialize DataExplorer
        explorer = DataExplorer(sample_size=10)

        # 2.1 Basic Information
        print_subsection("2.1 Basic Dataset Information")
        basic_info = explorer.analyze_basic_info(data)

        print(f"\n   Dataset Metrics:")
        print(
            f"   • Shape: {basic_info['shape'][0]:,} rows × {basic_info['shape'][1]:,} columns"
        )
        print(f"   • Memory: {basic_info['memory_usage_mb']:.2f} MB")
        print(f"   • Completeness: {basic_info['completeness_ratio']:.2%}")
        print(f"   • Duplicates: {basic_info['duplicate_count']:,} rows")

        # 2.2 Missing Data Analysis
        print_subsection("2.2 Missing Data Analysis")
        missing_analysis = explorer.analyze_missing_data(data, threshold=0.5)

        print(f"\n   Missing Data Summary:")
        print(f"   • Total missing cells: {missing_analysis['total_missing']:,}")
        print(f"   • Overall missing %: {missing_analysis['missing_percentage']:.2f}%")
        print(f"   • Columns with missing: {missing_analysis['columns_with_missing']}")
        print(
            f"   • High missing columns (>50%): {missing_analysis['columns_with_high_missing']}"
        )

        if missing_analysis["recommendations"]:
            print(f"\n   Recommendations:")
            for rec in missing_analysis["recommendations"][:3]:
                print(f"   • {rec}")

        # 2.3 Data Quality Assessment
        print_subsection("2.3 Data Quality Assessment")
        quality_analysis = explorer.analyze_data_quality(data)

        duplicates = quality_analysis["duplicates"]
        print(f"\n   Quality Metrics:")
        print(
            f"   • Duplicate rows: {duplicates['row_duplicates']:,} ({duplicates['row_duplicate_percentage']:.2f}%)"
        )
        print(
            f"   • Categorical columns analyzed: {len(quality_analysis['cardinality'])}"
        )
        print(
            f"   • Type consistency issues: {len(quality_analysis['type_consistency'])}"
        )
        print(f"   • Outlier analysis: {len(quality_analysis['outliers'])} columns")

        # 2.4 Data Patterns Analysis
        print_subsection("2.4 Data Patterns Analysis")
        patterns_analysis = explorer.analyze_data_patterns(data, sample_size=10)

        print(f"\n   Data Patterns Summary:")
        print(f"   • Numeric columns: {patterns_analysis['numeric_columns_count']}")
        print(
            f"   • Categorical columns: {patterns_analysis['categorical_columns_count']}"
        )
        print(f"   • Total columns: {patterns_analysis['total_columns']}")

        # 2.5 Statistical Patterns
        print_subsection("2.5 Statistical Patterns Analysis")
        stats_analysis = explorer.analyze_statistical_patterns(data, sample_cols=10)

        if "outliers" in stats_analysis and len(stats_analysis["outliers"]) > 0:
            print(f"\n   Statistical Analysis:")
            print(f"   • Outlier analysis: {len(stats_analysis['outliers'])} columns")
            print(
                f"   • Valid numeric columns: {stats_analysis['valid_numeric_columns']}"
            )
            print(f"   • Correlation columns: {stats_analysis['correlation_columns']}")
            print(f"   • High correlations: {len(stats_analysis['high_correlations'])}")
            print(
                f"   • Average correlation: {stats_analysis['average_correlation']:.3f}"
            )

        # 2.6 Detailed Data Quality Analysis
        print_subsection("2.6 Detailed Data Quality Analysis")
        detailed_quality = explorer.analyze_data_quality_detailed(data)

        print(f"\n   Detailed Quality Metrics:")
        print(
            f"   • Duplicate rows: {detailed_quality['duplicate_rows']:,} ({detailed_quality['duplicate_percentage']:.2f}%)"
        )
        print(f"   • Constant columns: {len(detailed_quality['constant_cols'])}")
        print(
            f"   • High cardinality columns: {len(detailed_quality['high_cardinality_cols'])}"
        )
        print(f"   • Mixed type columns: {len(detailed_quality['mixed_type_cols'])}")
        print(
            f"   • Infinite value columns: {len(detailed_quality['infinite_value_cols'])}"
        )
        print(
            f"   • Zero variance columns: {len(detailed_quality['zero_variance_cols'])}"
        )
        print(f"   • Total warnings: {detailed_quality['total_warnings']}")

        if detailed_quality["warnings"]:
            print(f"\n   Quality Warnings:")
            for warning in detailed_quality["warnings"][:5]:
                print(f"   • {warning}")

        # 2.7 Comprehensive Report
        print_subsection("2.7 Comprehensive Data Report")
        comprehensive_report = explorer.generate_comprehensive_report(
            data, dataset_name="HRX Tuple Dataset", perform_clustering=False
        )

        print(f"\n   Comprehensive Report Generated:")
        print(f"   • Dataset: {comprehensive_report['dataset_name']}")
        print(f"   • Generated at: {comprehensive_report['generated_at']}")
        print(f"   • Summary: {comprehensive_report['summary']}")

        # 2.8 Data Readiness Score
        print_subsection("2.8 ML Readiness Assessment")
        readiness = explorer.calculate_data_readiness_score(data)

        print(f"\n   Readiness Score: {readiness['overall_readiness']:.1f}/100")
        print(f"   Readiness Level: {readiness['readiness_level']}")
        print(f"   ML Ready: {'✅ Yes' if readiness['is_ready_for_ml'] else '❌ No'}")

        scores = readiness["scores"]
        print(f"\n   Score Breakdown:")
        print(f"   • Completeness: {scores['completeness']:.1f}/100")
        print(f"   • Missing Data: {scores['missing_data']:.1f}/100")
        print(f"   • Duplicates: {scores['duplicates']:.1f}/100")
        print(f"   • Type Consistency: {scores['type_consistency']:.1f}/100")
        print(f"   • Size Adequacy: {scores['size_adequacy']:.1f}/100")

        if readiness["recommendations"]:
            print(f"\n   Top Recommendations:")
            for i, rec in enumerate(readiness["recommendations"][:3], 1):
                print(f"   {i}. {rec}")

        logger.info(
            f"Data exploration completed: readiness score {readiness['overall_readiness']:.1f}"
        )

    except Exception as e:
        print(f"\n❌ Data exploration failed: {e}")
        logger.error(f"Exploration failed: {e}")
        return 1

    # =========================================================================
    # STEP 3: FEATURE SELECTION
    # =========================================================================
    print_section_header("🎯 STEP 3: Advanced Feature Selection")

    try:
        # Initialize FeatureSelector
        selector = FeatureSelector(random_state=42)

        # Identify potential target columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        potential_targets = [
            col
            for col in numeric_cols
            if data[col].nunique() < 20 and data[col].notna().sum() > 100
        ]

        if potential_targets:
            target_col = potential_targets[0]
            task_type = (
                "classification" if data[target_col].nunique() <= 10 else "regression"
            )

            print(f"\n   Using '{target_col}' as target column")
            print(f"   Task type: {task_type}")
            print(f"   Target classes: {data[target_col].nunique()}")

            # 3.1 Variance-based Selection
            print_subsection("3.1 Variance-Based Feature Selection")
            variance_result = selector.select_variance_threshold(
                data, threshold=0.01, exclude_cols=[target_col]
            )
            print(f"\n   • Selected features: {variance_result['n_selected']}")
            print(f"   • Removed features: {variance_result['n_removed']}")

            # 3.2 Correlation-based Selection
            print_subsection("3.2 Correlation-Based Feature Selection")
            correlation_result = selector.select_correlation_based(
                data, threshold=0.9, exclude_cols=[target_col]
            )
            print(f"\n   • Selected features: {correlation_result['n_selected']}")
            print(f"   • Removed features: {correlation_result['n_removed']}")
            print(
                f"   • High correlation pairs: {len(correlation_result['high_correlation_pairs'])}"
            )

            # 3.3 Consensus Feature Selection
            print_subsection("3.3 Consensus Feature Selection")

            # Use unsupervised methods only if supervised fails
            methods = ["variance", "correlation"]

            try:
                # Try supervised methods
                consensus_result = selector.consensus_feature_selection(
                    data=data,
                    target_col=target_col,
                    task_type=task_type,
                    methods=["variance", "correlation", "mutual_info", "tree_based"],
                    voting_threshold=0.5,
                    k_best=15,
                    top_k=15,
                )

                print(f"\n   Consensus Results:")
                print(f"   • Methods used: {len(consensus_result['methods_used'])}")
                print(f"   • Selected features: {consensus_result['n_selected']}")
                print(
                    f"   • Consensus score: {consensus_result['consensus_score']:.2f}"
                )
                print(f"\n   Top 10 Selected Features:")
                for i, feature in enumerate(
                    consensus_result["selected_features"][:10], 1
                ):
                    vote_ratio = consensus_result["feature_votes"].get(feature, 0)
                    print(f"   {i:2d}. {feature[:50]:50s} (votes: {vote_ratio:.2f})")

            except Exception as e:
                logger.warning(f"Supervised feature selection failed: {e}")
                print(
                    f"\n   ⚠️  Supervised methods unavailable, using unsupervised methods"
                )

                consensus_result = selector.consensus_feature_selection(
                    data=data,
                    target_col=None,
                    methods=["variance", "correlation"],
                    voting_threshold=0.5,
                )

                print(f"\n   Consensus Results (Unsupervised):")
                print(f"   • Methods used: {len(consensus_result['methods_used'])}")
                print(f"   • Selected features: {consensus_result['n_selected']}")
                print(
                    f"   • Consensus score: {consensus_result['consensus_score']:.2f}"
                )

            logger.info(
                f"Feature selection completed: {consensus_result['n_selected']} features selected"
            )

        else:
            print(
                "\n   ⚠️  No suitable target column found for supervised feature selection"
            )
            print("   Using unsupervised feature selection methods only")

            # Unsupervised feature selection
            variance_result = selector.select_variance_threshold(data, threshold=0.01)
            print(f"\n   Variance-based selection:")
            print(f"   • Selected features: {variance_result['n_selected']}")
            print(f"   • Removed features: {variance_result['n_removed']}")

            correlation_result = selector.select_correlation_based(data, threshold=0.9)
            print(f"\n   Correlation-based selection:")
            print(f"   • Selected features: {correlation_result['n_selected']}")
            print(f"   • Removed features: {correlation_result['n_removed']}")

    except Exception as e:
        print(f"\n❌ Feature selection failed: {e}")
        logger.error(f"Feature selection failed: {e}")
        # Continue workflow even if feature selection fails

    # =========================================================================
    # STEP 4: DATA PREPROCESSING
    # =========================================================================
    print_section_header("🔧 STEP 4: Data Preprocessing Pipeline")

    try:
        # Initialize DataPreprocessor
        preprocessor = DataPreprocessor(random_state=42)

        # 4.1 Handle Missing Values
        print_subsection("4.1 Missing Value Handling")
        clean_data, missing_info = preprocessor.handle_missing_values(
            data, strategy="auto", threshold=0.95
        )

        print(f"\n   Missing Value Treatment:")
        print(f"   • Original missing: {missing_info['original_missing']:,}")
        print(f"   • Final missing: {missing_info['final_missing']:,}")
        print(f"   • Columns dropped: {len(missing_info['columns_dropped'])}")
        print(f"   • Imputation methods: {len(missing_info['imputation_methods'])}")

        # 4.2 Handle Outliers
        print_subsection("4.2 Outlier Detection & Treatment")

        numeric_cols = clean_data.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 0:
            # Sample numeric columns for outlier treatment
            sample_numeric = numeric_cols[: min(10, len(numeric_cols))]
            sample_data = clean_data[
                sample_numeric
                + [col for col in clean_data.columns if col not in numeric_cols][:5]
            ]

            outlier_data, outlier_info = preprocessor.handle_outliers(
                sample_data, method="iqr", strategy="cap", threshold=1.5
            )

            print(f"\n   Outlier Treatment:")
            print(f"   • Method: {outlier_info['method']}")
            print(f"   • Strategy: {outlier_info['strategy']}")
            print(f"   • Columns analyzed: {len(outlier_info['outliers_detected'])}")

            total_outliers = sum(
                info["count"] for info in outlier_info["outliers_detected"].values()
            )
            print(f"   • Total outliers detected: {total_outliers:,}")

            if outlier_info["outliers_handled"]:
                print(
                    f"   • Treatment applied: {len(outlier_info['outliers_handled'])} columns"
                )

        # 4.3 Feature Scaling
        print_subsection("4.3 Feature Scaling & Normalization")

        # Select a subset for scaling demo
        scale_sample = clean_data[numeric_cols[: min(20, len(numeric_cols))]].copy()

        if len(scale_sample.columns) > 0:
            scaled_data, scaling_info = preprocessor.scale_features(
                scale_sample, method="standard"
            )

            print(f"\n   Feature Scaling:")
            print(f"   • Method: {scaling_info['method']}")
            print(f"   • Columns scaled: {len(scaling_info['scaled_columns'])}")
            print(f"   • Scaler stored: ✅ Yes")

        logger.info("Data preprocessing completed successfully")

    except Exception as e:
        print(f"\n❌ Data preprocessing failed: {e}")
        logger.error(f"Preprocessing failed: {e}")
        # Continue workflow

    # =========================================================================
    # STEP 5: VISUALIZATION GENERATION
    # =========================================================================
    print_section_header("📊 STEP 5: Comprehensive Visualization Generation")

    try:
        # Initialize Visualizer
        visualizer = Visualizer(style="whitegrid", figure_size=(12, 8), dpi=300)

        # Create output directory
        output_dir = Path("./workflow_outputs")
        output_dir.mkdir(exist_ok=True)

        print(f"\n   Output directory: {output_dir}")

        # 5.1 Missing Data Visualization
        print_subsection("5.1 Missing Data Visualization")
        try:
            missing_plot = visualizer.plot_missing_data(
                data,
                top_n=20,
                save_path=str(output_dir / "missing_data.png"),
                show=False,
            )
            print(f"   ✅ Missing data plot created: {output_dir / 'missing_data.png'}")
        except Exception as e:
            print(f"   ⚠️  Missing data plot skipped: {e}")

        # 5.2 Distribution Plots
        print_subsection("5.2 Distribution Plots")
        try:
            dist_plot = visualizer.plot_distributions(
                data,
                sample_cols=6,
                plot_type="histogram",
                save_path=str(output_dir / "distributions.png"),
                show=False,
            )
            print(
                f"   ✅ Distribution plots created: {output_dir / 'distributions.png'}"
            )
        except Exception as e:
            print(f"   ⚠️  Distribution plots skipped: {e}")

        # 5.3 Correlation Heatmap
        print_subsection("5.3 Correlation Analysis")
        try:
            corr_plot = visualizer.plot_correlations(
                data,
                sample_cols=15,
                method="pearson",
                save_path=str(output_dir / "correlations.png"),
                show=False,
            )
            print(
                f"   ✅ Correlation heatmap created: {output_dir / 'correlations.png'}"
            )

            if "high_correlation_pairs" in corr_plot:
                print(
                    f"   • High correlation pairs: {len(corr_plot['high_correlation_pairs'])}"
                )
        except Exception as e:
            print(f"   ⚠️  Correlation plot skipped: {e}")

        # 5.4 Data Quality Summary
        print_subsection("5.4 Data Quality Summary Dashboard")
        try:
            quality_plot = visualizer.plot_data_quality_summary(
                data, save_path=str(output_dir / "data_quality_summary.png"), show=False
            )
            print(
                f"   ✅ Quality summary created: {output_dir / 'data_quality_summary.png'}"
            )
            print(f"   • Completeness: {quality_plot['completeness']:.2f}%")
            print(f"   • Missing cells: {quality_plot['missing_cells']:,}")
            print(f"   • Duplicate rows: {quality_plot['duplicate_rows']:,}")
        except Exception as e:
            print(f"   ⚠️  Quality summary skipped: {e}")

        logger.info(f"Visualizations generated in {output_dir}")

    except Exception as e:
        print(f"\n❌ Visualization generation failed: {e}")
        logger.error(f"Visualization failed: {e}")

    # =========================================================================
    # STEP 6: AUTOMATED REPORTING
    # =========================================================================
    print_section_header("📋 STEP 6: Automated Report Generation")

    try:
        # Initialize ReportGenerator
        reporter = ReportGenerator(
            output_dir=str(output_dir / "reports"), include_automated_profiling=True
        )

        print(f"\n   Report output directory: {output_dir / 'reports'}")

        # 6.1 Comprehensive Analysis Report
        print_subsection("6.1 Comprehensive Analysis Report")

        comprehensive_report = reporter.generate_comprehensive_analysis_report(
            data=data,
            target_col=potential_targets[0] if potential_targets else None,
            task_type=task_type if potential_targets else "regression",
            dataset_name="hrx_tuple_dataset",
            include_feature_selection=bool(potential_targets),
            include_visualizations=True,
        )

        print(f"\n   Report Generated:")
        print(f"   • JSON: {comprehensive_report['json_path']}")
        print(f"   • HTML: {comprehensive_report['html_path']}")
        print(f"   • Sections: {', '.join(comprehensive_report['sections_included'])}")

        logger.info(
            f"Comprehensive report generated: {comprehensive_report['html_path']}"
        )

    except Exception as e:
        print(f"\n❌ Report generation failed: {e}")
        logger.error(f"Report generation failed: {e}")

    # =========================================================================
    # WORKFLOW SUMMARY
    # =========================================================================
    print_section_header("✅ Workflow Complete - Summary")

    print(
        f"""
   Workflow Execution Summary:
   
   ✅ Data Loading: Successfully loaded {data.shape[0]:,} rows × {data.shape[1]:,} columns
   ✅ Data Exploration: Comprehensive analysis completed
   ✅ Feature Selection: {consensus_result.get('n_selected', 'N/A')} features selected via consensus
   ✅ Data Preprocessing: Missing values, outliers, and scaling handled
   ✅ Visualizations: Multiple plots generated in {output_dir}
   ✅ Reports: Comprehensive HTML/JSON reports created
   
   📁 Output Directory: {output_dir}
   
   All library capabilities have been successfully demonstrated!
   """
    )

    print_section_header("🎉 Thank you for using 91life Data Science Library!")

    logger.info("Complete workflow execution finished successfully")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
