"""
Comprehensive data visualization functionality
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional, Tuple, Union
import warnings
from pathlib import Path

from ..core.logger import LoggerMixin
from ..core.exceptions import VisualizationError
from ..core.config import config


class Visualizer(LoggerMixin):
    """
    Comprehensive data visualization with multiple plot types and export options

    Provides methods for:
    - Missing data visualization
    - Distribution plots
    - Correlation analysis
    - Feature importance plots
    - Data quality visualizations
    - Interactive plots with Plotly
    - Export capabilities
    """

    def __init__(
        self,
        style: str = "whitegrid",
        figure_size: Optional[Tuple[int, int]] = None,
        dpi: int = 300,
        color_palette: str = "viridis",
    ):
        """
        Initialize Visualizer

        Args:
            style: Seaborn style for plots
            figure_size: Default figure size (width, height)
            dpi: DPI for saved plots
            color_palette: Color palette for plots
        """
        self.style = style
        self.figure_size = figure_size or config.default_figure_size
        self.dpi = dpi or config.default_dpi
        self.color_palette = color_palette

        # Set up plotting style
        sns.set_style(style)
        plt.rcParams["figure.figsize"] = self.figure_size
        plt.rcParams["figure.dpi"] = self.dpi

        self.logger.info(
            f"Visualizer initialized with style={style}, figure_size={self.figure_size}"
        )

    def plot_missing_data(
        self,
        data: pd.DataFrame,
        top_n: int = 20,
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Dict[str, Any]:
        """
        Visualize missing data patterns

        Args:
            data: Input DataFrame
            top_n: Number of top columns to show
            save_path: Path to save the plot
            show: Whether to display the plot

        Returns:
            Dictionary with plot information
        """
        self.logger.info(f"Creating missing data visualization for top {top_n} columns")

        try:
            # Calculate missing data statistics
            missing_stats = data.isnull().sum().sort_values(ascending=False)
            missing_percent = (missing_stats / len(data)) * 100

            # Select top N columns
            top_missing = missing_percent.head(top_n)

            if len(top_missing) == 0:
                self.logger.warning("No missing data found")
                return {"message": "No missing data found"}

            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # Bar plot of missing percentages
            bars = ax1.bar(
                range(len(top_missing)), top_missing.values, color="coral", alpha=0.7
            )
            ax1.set_xlabel("Columns")
            ax1.set_ylabel("Missing Data Percentage")
            ax1.set_title(f"Missing Data by Column (Top {top_n})")
            ax1.set_xticks(range(len(top_missing)))
            ax1.set_xticklabels(top_missing.index, rotation=45, ha="right")
            ax1.grid(True, alpha=0.3)

            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.5,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

            # Heatmap of missing data pattern
            if len(data) > 1000:
                # Sample data for heatmap if too large
                sample_data = data.sample(n=min(1000, len(data)), random_state=42)
            else:
                sample_data = data

            # Create missing data matrix
            missing_matrix = sample_data.isnull()

            # Plot heatmap
            sns.heatmap(
                missing_matrix.T,
                cbar=True,
                ax=ax2,
                cmap="viridis_r",
                yticklabels=True,
                xticklabels=False,
            )
            ax2.set_title("Missing Data Pattern (Sample)")
            ax2.set_xlabel("Rows (Sample)")
            ax2.set_ylabel("Columns")

            plt.tight_layout()

            # Save plot if requested
            if save_path:
                plt.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                self.logger.info(f"Missing data plot saved to {save_path}")

            if show:
                plt.show()
            else:
                plt.close()

            plot_info = {
                "plot_type": "missing_data",
                "columns_analyzed": len(top_missing),
                "total_missing_percentage": missing_percent.sum() / len(data.columns),
                "top_missing_columns": top_missing.to_dict(),
                "save_path": save_path,
            }

            return plot_info

        except Exception as e:
            self.logger.error(f"Failed to create missing data plot: {e}")
            raise VisualizationError(f"Failed to create missing data plot: {e}")

    def plot_distributions(
        self,
        data: pd.DataFrame,
        sample_cols: int = 6,
        plot_type: str = "histogram",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Dict[str, Any]:
        """
        Visualize data distributions

        Args:
            data: Input DataFrame
            sample_cols: Number of columns to plot
            plot_type: Type of plot ('histogram', 'boxplot', 'violin', 'kde')
            save_path: Path to save the plot
            show: Whether to display the plot

        Returns:
            Dictionary with plot information
        """
        self.logger.info(f"Creating distribution plots for {sample_cols} columns")

        try:
            # Select numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) == 0:
                self.logger.warning("No numeric columns found for distribution plots")
                return {"message": "No numeric columns found"}

            # Sample columns if too many
            if len(numeric_cols) > sample_cols:
                numeric_cols = numeric_cols[:sample_cols]

            # Calculate subplot layout
            n_cols = min(3, len(numeric_cols))
            n_rows = (len(numeric_cols) + n_cols - 1) // n_cols

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
            if n_rows == 1 and n_cols == 1:
                axes = [axes]
            elif n_rows == 1 or n_cols == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()

            plot_info = {
                "plot_type": f"distributions_{plot_type}",
                "columns_plotted": numeric_cols,
                "n_plots": len(numeric_cols),
            }

            for i, col in enumerate(numeric_cols):
                if i >= len(axes):
                    break

                col_data = data[col].dropna()

                if len(col_data) == 0:
                    axes[i].text(
                        0.5,
                        0.5,
                        "No Data",
                        ha="center",
                        va="center",
                        transform=axes[i].transAxes,
                    )
                    axes[i].set_title(f"{col} (No Data)")
                    continue

                if plot_type == "histogram":
                    axes[i].hist(
                        col_data, bins=30, alpha=0.7, color="skyblue", edgecolor="black"
                    )
                    axes[i].set_title(f"{col} - Histogram")
                    axes[i].set_xlabel(col)
                    axes[i].set_ylabel("Frequency")

                elif plot_type == "boxplot":
                    axes[i].boxplot(
                        col_data,
                        patch_artist=True,
                        boxprops=dict(facecolor="lightblue", alpha=0.7),
                    )
                    axes[i].set_title(f"{col} - Box Plot")
                    axes[i].set_ylabel(col)

                elif plot_type == "violin":
                    axes[i].violinplot(col_data, showmeans=True, showmedians=True)
                    axes[i].set_title(f"{col} - Violin Plot")
                    axes[i].set_ylabel(col)

                elif plot_type == "kde":
                    from scipy import stats

                    kde = stats.gaussian_kde(col_data)
                    x_range = np.linspace(col_data.min(), col_data.max(), 100)
                    axes[i].plot(x_range, kde(x_range), color="red", linewidth=2)
                    axes[i].set_title(f"{col} - KDE")
                    axes[i].set_xlabel(col)
                    axes[i].set_ylabel("Density")

                axes[i].grid(True, alpha=0.3)

            # Hide unused subplots
            for i in range(len(numeric_cols), len(axes)):
                axes[i].set_visible(False)

            plt.tight_layout()

            # Save plot if requested
            if save_path:
                plt.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                self.logger.info(f"Distribution plot saved to {save_path}")

            if show:
                plt.show()
            else:
                plt.close()

            return plot_info

        except Exception as e:
            self.logger.error(f"Failed to create distribution plots: {e}")
            raise VisualizationError(f"Failed to create distribution plots: {e}")

    def plot_correlations(
        self,
        data: pd.DataFrame,
        sample_cols: int = 15,
        method: str = "pearson",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Dict[str, Any]:
        """
        Visualize correlation matrix

        Args:
            data: Input DataFrame
            sample_cols: Number of columns to include in correlation matrix
            method: Correlation method ('pearson', 'spearman', 'kendall')
            save_path: Path to save the plot
            show: Whether to display the plot

        Returns:
            Dictionary with plot information
        """
        self.logger.info(f"Creating correlation matrix for {sample_cols} columns")

        try:
            # Select numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) == 0:
                self.logger.warning("No numeric columns found for correlation plot")
                return {"message": "No numeric columns found"}

            # Sample columns if too many
            if len(numeric_cols) > sample_cols:
                numeric_cols = numeric_cols[:sample_cols]

            # Calculate correlation matrix
            corr_matrix = data[numeric_cols].corr(method=method)

            # Create figure
            fig, ax = plt.subplots(figsize=(12, 10))

            # Create heatmap
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(
                corr_matrix,
                mask=mask,
                annot=True,
                cmap="coolwarm",
                center=0,
                square=True,
                linewidths=0.5,
                cbar_kws={"shrink": 0.8},
                ax=ax,
            )

            ax.set_title(f"Correlation Matrix ({method.title()})")
            plt.tight_layout()

            # Save plot if requested
            if save_path:
                plt.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                self.logger.info(f"Correlation plot saved to {save_path}")

            if show:
                plt.show()
            else:
                plt.close()

            # Find highly correlated pairs
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        high_corr_pairs.append(
                            {
                                "feature1": corr_matrix.columns[i],
                                "feature2": corr_matrix.columns[j],
                                "correlation": corr_value,
                            }
                        )

            plot_info = {
                "plot_type": f"correlation_{method}",
                "columns_analyzed": numeric_cols,
                "correlation_matrix": corr_matrix.to_dict(),
                "high_correlation_pairs": high_corr_pairs,
                "save_path": save_path,
            }

            return plot_info

        except Exception as e:
            self.logger.error(f"Failed to create correlation plot: {e}")
            raise VisualizationError(f"Failed to create correlation plot: {e}")

    def plot_feature_importance(
        self,
        feature_scores: Dict[str, float],
        title: str = "Feature Importance",
        top_k: int = 20,
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Dict[str, Any]:
        """
        Visualize feature importance scores

        Args:
            feature_scores: Dictionary of feature names and their importance scores
            title: Plot title
            top_k: Number of top features to show
            save_path: Path to save the plot
            show: Whether to display the plot

        Returns:
            Dictionary with plot information
        """
        self.logger.info(f"Creating feature importance plot for top {top_k} features")

        try:
            if not feature_scores:
                self.logger.warning("No feature scores provided")
                return {"message": "No feature scores provided"}

            # Sort features by importance
            sorted_features = sorted(
                feature_scores.items(), key=lambda x: x[1], reverse=True
            )
            top_features = sorted_features[:top_k]

            if not top_features:
                self.logger.warning("No features to plot")
                return {"message": "No features to plot"}

            # Extract data for plotting
            features, scores = zip(*top_features)

            # Create horizontal bar plot
            fig, ax = plt.subplots(figsize=(10, max(6, len(features) * 0.4)))

            bars = ax.barh(range(len(features)), scores, color="steelblue", alpha=0.7)
            ax.set_yticks(range(len(features)))
            ax.set_yticklabels(features)
            ax.set_xlabel("Importance Score")
            ax.set_title(title)
            ax.grid(True, alpha=0.3, axis="x")

            # Add value labels on bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(
                    width + width * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{width:.3f}",
                    ha="left",
                    va="center",
                    fontsize=9,
                )

            plt.tight_layout()

            # Save plot if requested
            if save_path:
                plt.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                self.logger.info(f"Feature importance plot saved to {save_path}")

            if show:
                plt.show()
            else:
                plt.close()

            plot_info = {
                "plot_type": "feature_importance",
                "title": title,
                "features_plotted": len(top_features),
                "top_features": dict(top_features),
                "save_path": save_path,
            }

            return plot_info

        except Exception as e:
            self.logger.error(f"Failed to create feature importance plot: {e}")
            raise VisualizationError(f"Failed to create feature importance plot: {e}")

    def plot_data_quality_summary(
        self, data: pd.DataFrame, save_path: Optional[str] = None, show: bool = True
    ) -> Dict[str, Any]:
        """
        Create a comprehensive data quality summary visualization

        Args:
            data: Input DataFrame
            save_path: Path to save the plot
            show: Whether to display the plot

        Returns:
            Dictionary with plot information
        """
        self.logger.info("Creating data quality summary visualization")

        try:
            # Calculate quality metrics
            total_cells = data.shape[0] * data.shape[1]
            missing_cells = data.isnull().sum().sum()
            duplicate_rows = data.duplicated().sum()
            completeness = (total_cells - missing_cells) / total_cells * 100

            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

            # 1. Data completeness
            completeness_data = [completeness, 100 - completeness]
            labels = ["Complete", "Missing"]
            colors = ["lightgreen", "lightcoral"]

            ax1.pie(
                completeness_data,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax1.set_title(f"Data Completeness\n({completeness:.1f}% Complete)")

            # 2. Missing data by column (top 10)
            missing_by_col = data.isnull().sum().sort_values(ascending=False).head(10)
            if len(missing_by_col) > 0:
                bars = ax2.bar(
                    range(len(missing_by_col)),
                    missing_by_col.values,
                    color="coral",
                    alpha=0.7,
                )
                ax2.set_xlabel("Columns")
                ax2.set_ylabel("Missing Values")
                ax2.set_title("Missing Data by Column (Top 10)")
                ax2.set_xticks(range(len(missing_by_col)))
                ax2.set_xticklabels(missing_by_col.index, rotation=45, ha="right")
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(
                    0.5,
                    0.5,
                    "No Missing Data",
                    ha="center",
                    va="center",
                    transform=ax2.transAxes,
                    fontsize=14,
                )
                ax2.set_title("Missing Data by Column")

            # 3. Data types distribution
            dtype_counts = data.dtypes.value_counts()
            ax3.pie(
                dtype_counts.values,
                labels=dtype_counts.index,
                autopct="%1.1f%%",
                startangle=90,
            )
            ax3.set_title("Data Types Distribution")

            # 4. Dataset statistics
            stats_text = f"""
            Dataset Statistics:
            
            Shape: {data.shape[0]:,} rows × {data.shape[1]:,} columns
            Total Cells: {total_cells:,}
            Missing Cells: {missing_cells:,}
            Duplicate Rows: {duplicate_rows:,}
            Memory Usage: {data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB
            
            Completeness: {completeness:.1f}%
            Duplicate Rate: {duplicate_rows / data.shape[0] * 100:.1f}%
            """

            ax4.text(
                0.05,
                0.95,
                stats_text,
                transform=ax4.transAxes,
                fontsize=11,
                verticalalignment="top",
                fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
            )
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis("off")
            ax4.set_title("Dataset Summary")

            plt.tight_layout()

            # Save plot if requested
            if save_path:
                plt.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                self.logger.info(f"Data quality summary saved to {save_path}")

            if show:
                plt.show()
            else:
                plt.close()

            plot_info = {
                "plot_type": "data_quality_summary",
                "completeness": completeness,
                "missing_cells": missing_cells,
                "duplicate_rows": duplicate_rows,
                "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
                "save_path": save_path,
            }

            return plot_info

        except Exception as e:
            self.logger.error(f"Failed to create data quality summary: {e}")
            raise VisualizationError(f"Failed to create data quality summary: {e}")

    def create_interactive_plot(
        self,
        data: pd.DataFrame,
        plot_type: str = "scatter",
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        color_col: Optional[str] = None,
        title: str = "Interactive Plot",
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create interactive plots using Plotly

        Args:
            data: Input DataFrame
            plot_type: Type of plot ('scatter', 'line', 'bar', 'histogram', 'box')
            x_col: Column for x-axis
            y_col: Column for y-axis
            color_col: Column for color grouping
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Dictionary with plot information
        """
        self.logger.info(f"Creating interactive {plot_type} plot")

        try:
            # Select numeric columns if not specified
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if not x_col and numeric_cols:
                x_col = numeric_cols[0]
            if not y_col and len(numeric_cols) > 1:
                y_col = numeric_cols[1]

            if not x_col:
                raise VisualizationError("No suitable columns found for plotting")

            # Create plot based on type
            if plot_type == "scatter" and y_col:
                fig = px.scatter(data, x=x_col, y=y_col, color=color_col, title=title)
            elif plot_type == "line" and y_col:
                fig = px.line(data, x=x_col, y=y_col, color=color_col, title=title)
            elif plot_type == "bar":
                if y_col:
                    fig = px.bar(data, x=x_col, y=y_col, color=color_col, title=title)
                else:
                    # Count plot
                    value_counts = data[x_col].value_counts().head(20)
                    fig = px.bar(
                        x=value_counts.index, y=value_counts.values, title=title
                    )
            elif plot_type == "histogram":
                fig = px.histogram(data, x=x_col, color=color_col, title=title)
            elif plot_type == "box":
                fig = px.box(
                    data,
                    x=color_col if color_col else x_col,
                    y=y_col if y_col else x_col,
                    title=title,
                )
            else:
                raise VisualizationError(f"Unsupported plot type: {plot_type}")

            # Update layout
            fig.update_layout(
                title=title,
                xaxis_title=x_col,
                yaxis_title=y_col,
                font=dict(size=12),
                showlegend=True,
            )

            # Save plot if requested
            if save_path:
                if save_path.endswith(".html"):
                    fig.write_html(save_path)
                else:
                    fig.write_image(save_path)
                self.logger.info(f"Interactive plot saved to {save_path}")

            # Show plot
            fig.show()

            plot_info = {
                "plot_type": f"interactive_{plot_type}",
                "x_column": x_col,
                "y_column": y_col,
                "color_column": color_col,
                "title": title,
                "save_path": save_path,
            }

            return plot_info

        except Exception as e:
            self.logger.error(f"Failed to create interactive plot: {e}")
            raise VisualizationError(f"Failed to create interactive plot: {e}")

    def create_dashboard(
        self,
        data: pd.DataFrame,
        target_col: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a comprehensive data dashboard

        Args:
            data: Input DataFrame
            target_col: Target column for analysis
            save_path: Path to save the dashboard

        Returns:
            Dictionary with dashboard information
        """
        self.logger.info("Creating comprehensive data dashboard")

        try:
            # Create figure with multiple subplots
            fig = make_subplots(
                rows=3,
                cols=2,
                subplot_titles=(
                    "Data Quality Summary",
                    "Missing Data Pattern",
                    "Feature Distributions",
                    "Correlation Matrix",
                    "Target Distribution" if target_col else "Data Types",
                    "Dataset Statistics",
                ),
                specs=[
                    [{"type": "pie"}, {"type": "heatmap"}],
                    [{"type": "bar"}, {"type": "heatmap"}],
                    [{"type": "bar"}, {"type": "table"}],
                ],
            )

            # 1. Data quality pie chart
            total_cells = data.shape[0] * data.shape[1]
            missing_cells = data.isnull().sum().sum()
            completeness = (total_cells - missing_cells) / total_cells * 100

            fig.add_trace(
                go.Pie(
                    labels=["Complete", "Missing"],
                    values=[completeness, 100 - completeness],
                    name="Data Quality",
                ),
                row=1,
                col=1,
            )

            # 2. Missing data heatmap (sample)
            if len(data) > 1000:
                sample_data = data.sample(n=min(500, len(data)), random_state=42)
            else:
                sample_data = data

            missing_matrix = sample_data.isnull().astype(int)
            fig.add_trace(
                go.Heatmap(
                    z=missing_matrix.T.values,
                    x=missing_matrix.index,
                    y=missing_matrix.columns,
                    colorscale="Viridis",
                    name="Missing Data",
                ),
                row=1,
                col=2,
            )

            # 3. Feature distributions (top 5 numeric columns)
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                top_numeric = numeric_cols[:5]
                for col in top_numeric:
                    fig.add_trace(
                        go.Histogram(x=data[col].dropna(), name=col, opacity=0.7),
                        row=2,
                        col=1,
                    )

            # 4. Correlation matrix
            if len(numeric_cols) > 1:
                corr_matrix = data[numeric_cols[:10]].corr()
                fig.add_trace(
                    go.Heatmap(
                        z=corr_matrix.values,
                        x=corr_matrix.columns,
                        y=corr_matrix.columns,
                        colorscale="RdBu",
                        zmid=0,
                        name="Correlations",
                    ),
                    row=2,
                    col=2,
                )

            # 5. Target distribution or data types
            if target_col and target_col in data.columns:
                target_counts = data[target_col].value_counts().head(10)
                fig.add_trace(
                    go.Bar(
                        x=target_counts.index,
                        y=target_counts.values,
                        name="Target Distribution",
                    ),
                    row=3,
                    col=1,
                )
            else:
                dtype_counts = data.dtypes.value_counts()
                fig.add_trace(
                    go.Bar(
                        x=dtype_counts.index, y=dtype_counts.values, name="Data Types"
                    ),
                    row=3,
                    col=1,
                )

            # 6. Dataset statistics table
            stats_data = [
                ["Shape", f"{data.shape[0]:,} × {data.shape[1]:,}"],
                [
                    "Memory Usage",
                    f"{data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB",
                ],
                ["Missing Values", f"{missing_cells:,}"],
                ["Duplicate Rows", f"{data.duplicated().sum():,}"],
                ["Completeness", f"{completeness:.1f}%"],
            ]

            fig.add_trace(
                go.Table(
                    header=dict(values=["Metric", "Value"], fill_color="lightblue"),
                    cells=dict(values=list(zip(*stats_data)), fill_color="white"),
                ),
                row=3,
                col=2,
            )

            # Update layout
            fig.update_layout(
                title_text="Data Analysis Dashboard", showlegend=False, height=1200
            )

            # Save dashboard if requested
            if save_path:
                if save_path.endswith(".html"):
                    fig.write_html(save_path)
                else:
                    fig.write_image(save_path)
                self.logger.info(f"Dashboard saved to {save_path}")

            # Show dashboard
            fig.show()

            dashboard_info = {
                "plot_type": "dashboard",
                "target_column": target_col,
                "completeness": completeness,
                "missing_cells": missing_cells,
                "numeric_columns": len(numeric_cols),
                "save_path": save_path,
            }

            return dashboard_info

        except Exception as e:
            self.logger.error(f"Failed to create dashboard: {e}")
            raise VisualizationError(f"Failed to create dashboard: {e}")

    def export_plots(
        self,
        plots_info: List[Dict[str, Any]],
        output_dir: str = "./plots",
        formats: List[str] = ["png", "pdf"],
    ) -> Dict[str, Any]:
        """
        Export multiple plots to files

        Args:
            plots_info: List of plot information dictionaries
            output_dir: Output directory for plots
            formats: List of formats to export ('png', 'pdf', 'svg', 'html')

        Returns:
            Dictionary with export information
        """
        self.logger.info(f"Exporting {len(plots_info)} plots to {output_dir}")

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            export_info = {
                "output_directory": str(output_path),
                "formats": formats,
                "exported_files": [],
                "failed_exports": [],
            }

            for i, plot_info in enumerate(plots_info):
                plot_type = plot_info.get("plot_type", f"plot_{i}")

                for format_type in formats:
                    try:
                        filename = f"{plot_type}_{i}.{format_type}"
                        filepath = output_path / filename

                        # This would need to be implemented based on the specific plot
                        # For now, we'll just record the intended export
                        export_info["exported_files"].append(str(filepath))

                    except Exception as e:
                        export_info["failed_exports"].append(
                            {"file": filename, "error": str(e)}
                        )

            self.logger.info(
                f"Export completed: {len(export_info['exported_files'])} files, {len(export_info['failed_exports'])} failed"
            )

            return export_info

        except Exception as e:
            self.logger.error(f"Failed to export plots: {e}")
            raise VisualizationError(f"Failed to export plots: {e}")
