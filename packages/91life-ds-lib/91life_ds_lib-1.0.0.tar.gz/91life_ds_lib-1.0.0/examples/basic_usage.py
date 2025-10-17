#!/usr/bin/env python3
"""
Basic usage example for 91life Data Science Library

This example demonstrates the core functionality of the library using
the provided HRX tuple dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Import the library components
from ninetyone_life_ds import (
    DataLoader,
    DataExplorer,
    FeatureSelector,
    DataPreprocessor,
    Visualizer,
    ReportGenerator,
)


def main():
    """Main example function"""
    print("🚀 91life Data Science Library - Basic Usage Example")
    print("=" * 60)

    # Initialize components
    loader = DataLoader(chunk_size=50000)
    explorer = DataExplorer()
    selector = FeatureSelector()
    preprocessor = DataPreprocessor()
    visualizer = Visualizer()
    reporter = ReportGenerator(output_dir="./example_reports")

    # Load the HRX tuple dataset
    print("\n📊 Loading Dataset...")
    dataset_path = Path("notebook/hrx_tuple_dataset.csv")

    if not dataset_path.exists():
        print(f"❌ Dataset not found at {dataset_path}")
        print("Please ensure the HRX tuple dataset is available.")
        return

    try:
        data = loader.load_dataset(str(dataset_path))
        print(f"✅ Dataset loaded successfully: {data.shape}")
        print(f"   Columns: {list(data.columns)}")
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return

    # Basic data exploration
    print("\n🔍 Data Exploration...")
    try:
        basic_info = explorer.analyze_basic_info(data)
        print(f"   Memory usage: {basic_info['memory_usage_mb']:.2f} MB")
        print(f"   Completeness: {basic_info['completeness_ratio']:.2%}")
        print(f"   Duplicate rows: {basic_info['duplicate_count']}")

        missing_analysis = explorer.analyze_missing_data(data)
        print(f"   Missing data: {missing_analysis['missing_percentage']:.2f}%")
        print(f"   Columns with missing: {missing_analysis['columns_with_missing']}")

    except Exception as e:
        print(f"❌ Data exploration failed: {e}")

    # Data quality assessment
    print("\n📈 Data Quality Assessment...")
    try:
        readiness = explorer.calculate_data_readiness_score(data)
        print(f"   Overall readiness score: {readiness['overall_readiness']:.1f}/100")
        print(f"   Readiness level: {readiness['readiness_level']}")
        print(f"   Ready for ML: {readiness['is_ready_for_ml']}")

        if readiness["recommendations"]:
            print("   Recommendations:")
            for rec in readiness["recommendations"][:3]:
                print(f"     • {rec}")

    except Exception as e:
        print(f"❌ Data quality assessment failed: {e}")

    # Feature selection (if target column exists)
    print("\n🎯 Feature Selection...")
    try:
        # Try to identify a potential target column
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        potential_targets = [col for col in numeric_cols if data[col].nunique() < 20]

        if potential_targets:
            target_col = potential_targets[0]
            print(f"   Using '{target_col}' as target column")

            # Perform feature selection
            feature_report = selector.generate_feature_selection_report(
                data=data,
                target_col=target_col,
                task_type=(
                    "classification"
                    if data[target_col].nunique() <= 10
                    else "regression"
                ),
            )

            summary = feature_report["summary"]
            print(f"   Total features: {summary['total_features']}")
            print(f"   Selected features: {summary['selected_features']}")
            print(f"   Selection ratio: {summary['selection_ratio']:.2%}")
            print(f"   Consensus score: {summary['consensus_score']:.2f}")

        else:
            print("   No suitable target column found for supervised feature selection")

    except Exception as e:
        print(f"❌ Feature selection failed: {e}")

    # Data preprocessing
    print("\n🔧 Data Preprocessing...")
    try:
        # Handle missing values
        clean_data, missing_info = preprocessor.handle_missing_values(
            data, strategy="auto", threshold=0.5
        )
        print(
            f"   Missing values handled: {missing_info['original_missing']} -> {missing_info['final_missing']}"
        )

        # Handle outliers
        outlier_data, outlier_info = preprocessor.handle_outliers(
            clean_data, method="iqr", strategy="cap"
        )
        print(
            f"   Outliers handled for {len(outlier_info['outliers_detected'])} columns"
        )

        # Scale features
        numeric_cols = outlier_data.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1:
            scaled_data, scaling_info = preprocessor.scale_features(
                outlier_data, method="standard"
            )
            print(f"   Features scaled: {len(scaling_info['scaled_columns'])} columns")

    except Exception as e:
        print(f"❌ Data preprocessing failed: {e}")

    # Visualization
    print("\n📊 Creating Visualizations...")
    try:
        # Create missing data plot
        missing_plot = visualizer.plot_missing_data(
            data, top_n=10, save_path="./example_reports/missing_data.png", show=False
        )
        print(f"   Missing data plot created")

        # Create distribution plots
        dist_plot = visualizer.plot_distributions(
            data,
            sample_cols=6,
            plot_type="histogram",
            save_path="./example_reports/distributions.png",
            show=False,
        )
        print(f"   Distribution plots created")

        # Create correlation plot
        corr_plot = visualizer.plot_correlations(
            data,
            sample_cols=10,
            save_path="./example_reports/correlations.png",
            show=False,
        )
        print(f"   Correlation plot created")

        # Create data quality summary
        quality_plot = visualizer.plot_data_quality_summary(
            data, save_path="./example_reports/data_quality.png", show=False
        )
        print(f"   Data quality summary created")

    except Exception as e:
        print(f"❌ Visualization failed: {e}")

    # Generate comprehensive report
    print("\n📋 Generating Comprehensive Report...")
    try:
        comprehensive_report = reporter.generate_comprehensive_analysis_report(
            data=data,
            target_col=potential_targets[0] if potential_targets else None,
            task_type=(
                "classification"
                if potential_targets and data[potential_targets[0]].nunique() <= 10
                else "regression"
            ),
            dataset_name="hrx_tuple_dataset",
            include_feature_selection=bool(potential_targets),
            include_visualizations=True,
        )

        print(f"   Comprehensive report generated:")
        print(f"     JSON: {comprehensive_report['json_path']}")
        print(f"     HTML: {comprehensive_report['html_path']}")

    except Exception as e:
        print(f"❌ Report generation failed: {e}")

    print("\n✅ Example completed successfully!")
    print("📁 Check the './example_reports' directory for generated files.")
    print("\n🎉 Thank you for using the 91life Data Science Library!")


if __name__ == "__main__":
    main()
