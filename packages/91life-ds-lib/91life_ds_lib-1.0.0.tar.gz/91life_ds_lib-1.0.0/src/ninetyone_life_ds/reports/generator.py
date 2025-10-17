"""
Automated report generation and profiling functionality
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import datetime
from jinja2 import Template
import warnings

# Optional profiling libraries
try:
    from ydata_profiling import ProfileReport
    YDATA_AVAILABLE = True
except ImportError:
    YDATA_AVAILABLE = False

try:
    import sweetviz as sv
    SWEETVIZ_AVAILABLE = True
except ImportError:
    SWEETVIZ_AVAILABLE = False

from ..core.logger import LoggerMixin
from ..core.exceptions import ReportGenerationError
from ..core.config import config
from ..data.explorer import DataExplorer
from ..features.selector import FeatureSelector
from ..visualization.plotter import Visualizer


class ReportGenerator(LoggerMixin):
    """
    Comprehensive report generation with automated profiling and analysis
    
    Provides methods for:
    - Automated data profiling reports
    - Comprehensive analysis reports
    - Executive summaries
    - HTML/PDF report generation
    - Custom report templates
    """
    
    def __init__(
        self,
        output_dir: str = './reports',
        include_automated_profiling: bool = True,
        template_dir: Optional[str] = None
    ):
        """
        Initialize ReportGenerator
        
        Args:
            output_dir: Default output directory for reports
            include_automated_profiling: Whether to include automated profiling tools
            template_dir: Directory for custom report templates
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.include_automated_profiling = include_automated_profiling
        self.template_dir = Path(template_dir) if template_dir else None
        
        # Initialize components
        self.explorer = DataExplorer()
        self.selector = FeatureSelector()
        self.visualizer = Visualizer()
        
        self.logger.info(f"ReportGenerator initialized with output_dir={output_dir}")
    
    def generate_ydata_profiling_report(
        self,
        data: pd.DataFrame,
        dataset_name: str = 'dataset',
        title: str = 'Data Profiling Report',
        minimal: bool = False,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate YData profiling report
        
        Args:
            data: Input DataFrame
            dataset_name: Name of the dataset
            title: Report title
            minimal: Whether to generate minimal report
            save_path: Path to save the report
        
        Returns:
            Dictionary with report information
        """
        self.logger.info("Generating YData profiling report")
        
        try:
            if not YDATA_AVAILABLE:
                raise ReportGenerationError("YData profiling not available. Install with: pip install ydata-profiling")
            
            # Configure profiling
            profile_config = {
                'title': title,
                'dataset': {'name': dataset_name},
                'infer_dtypes': True,
                'correlations': {
                    'pearson': {'calculate': True},
                    'spearman': {'calculate': True},
                    'kendall': {'calculate': False},
                    'phi_k': {'calculate': True},
                    'cramers': {'calculate': True}
                },
                'missing_diagrams': {
                    'matrix': True,
                    'bar': True,
                    'heatmap': True,
                    'dendrogram': True
                },
                'interactions': {
                    'continuous': True,
                    'targets': []
                },
                'samples': {
                    'head': 5,
                    'tail': 5
                }
            }
            
            if minimal:
                profile_config['correlations'] = {'pearson': {'calculate': False}}
                profile_config['missing_diagrams'] = {'matrix': True, 'bar': True}
                profile_config['interactions'] = {'continuous': False}
            
            # Generate profile
            profile = ProfileReport(
                data,
                title=title,
                config=profile_config
            )
            
            # Save report
            if save_path is None:
                save_path = self.output_dir / f"{dataset_name}_ydata_report.html"
            
            profile.to_file(str(save_path))
            
            report_info = {
                'report_type': 'ydata_profiling',
                'dataset_name': dataset_name,
                'title': title,
                'save_path': str(save_path),
                'minimal': minimal,
                'data_shape': data.shape,
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            self.logger.info(f"YData profiling report saved to {save_path}")
            
            return report_info
            
        except Exception as e:
            self.logger.error(f"Failed to generate YData profiling report: {e}")
            raise ReportGenerationError(f"Failed to generate YData profiling report: {e}")
    
    def generate_sweetviz_report(
        self,
        data: pd.DataFrame,
        target_col: Optional[str] = None,
        dataset_name: str = 'dataset',
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Sweetviz profiling report
        
        Args:
            data: Input DataFrame
            target_col: Target column for analysis
            dataset_name: Name of the dataset
            save_path: Path to save the report
        
        Returns:
            Dictionary with report information
        """
        self.logger.info("Generating Sweetviz profiling report")
        
        try:
            if not SWEETVIZ_AVAILABLE:
                raise ReportGenerationError("Sweetviz not available. Install with: pip install sweetviz")
            
            # Generate report
            if target_col and target_col in data.columns:
                report = sv.analyze(data, target_feat=target_col)
            else:
                report = sv.analyze(data)
            
            # Save report
            if save_path is None:
                save_path = self.output_dir / f"{dataset_name}_sweetviz_report.html"
            
            report.show_html(str(save_path))
            
            report_info = {
                'report_type': 'sweetviz',
                'dataset_name': dataset_name,
                'target_column': target_col,
                'save_path': str(save_path),
                'data_shape': data.shape,
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            self.logger.info(f"Sweetviz report saved to {save_path}")
            
            return report_info
            
        except Exception as e:
            self.logger.error(f"Failed to generate Sweetviz report: {e}")
            raise ReportGenerationError(f"Failed to generate Sweetviz report: {e}")
    
    def generate_comprehensive_analysis_report(
        self,
        data: pd.DataFrame,
        target_col: Optional[str] = None,
        task_type: str = 'regression',
        dataset_name: str = 'dataset',
        include_feature_selection: bool = True,
        include_visualizations: bool = True,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report
        
        Args:
            data: Input DataFrame
            target_col: Target column for analysis
            task_type: Type of ML task ('regression' or 'classification')
            dataset_name: Name of the dataset
            include_feature_selection: Whether to include feature selection analysis
            include_visualizations: Whether to include visualizations
            save_path: Path to save the report
        
        Returns:
            Dictionary with comprehensive report information
        """
        self.logger.info("Generating comprehensive analysis report")
        
        try:
            report_data = {
                'dataset_name': dataset_name,
                'target_column': target_col,
                'task_type': task_type,
                'generated_at': datetime.datetime.now().isoformat(),
                'data_shape': data.shape
            }
            
            # 1. Basic data exploration
            self.logger.info("Performing basic data exploration")
            exploration_results = self.explorer.generate_comprehensive_analysis(data)
            report_data['data_exploration'] = exploration_results
            
            # 2. Feature selection analysis
            if include_feature_selection and target_col:
                self.logger.info("Performing feature selection analysis")
                try:
                    feature_selection_results = self.selector.generate_feature_selection_report(
                        data=data,
                        target_col=target_col,
                        task_type=task_type
                    )
                    report_data['feature_selection'] = feature_selection_results
                except Exception as e:
                    self.logger.warning(f"Feature selection failed: {e}")
                    report_data['feature_selection'] = {'error': str(e)}
            
            # 3. Visualizations
            if include_visualizations:
                self.logger.info("Generating visualizations")
                visualization_results = {}
                
                try:
                    # Missing data plot
                    missing_plot = self.visualizer.plot_missing_data(data, show=False)
                    visualization_results['missing_data'] = missing_plot
                except Exception as e:
                    self.logger.warning(f"Missing data plot failed: {e}")
                
                try:
                    # Distribution plots
                    dist_plot = self.visualizer.plot_distributions(data, show=False)
                    visualization_results['distributions'] = dist_plot
                except Exception as e:
                    self.logger.warning(f"Distribution plot failed: {e}")
                
                try:
                    # Correlation plot
                    corr_plot = self.visualizer.plot_correlations(data, show=False)
                    visualization_results['correlations'] = corr_plot
                except Exception as e:
                    self.logger.warning(f"Correlation plot failed: {e}")
                
                try:
                    # Data quality summary
                    quality_plot = self.visualizer.plot_data_quality_summary(data, show=False)
                    visualization_results['data_quality'] = quality_plot
                except Exception as e:
                    self.logger.warning(f"Data quality plot failed: {e}")
                
                report_data['visualizations'] = visualization_results
            
            # 4. Generate executive summary
            executive_summary = self._generate_executive_summary(report_data)
            report_data['executive_summary'] = executive_summary
            
            # 5. Save report
            if save_path is None:
                save_path = self.output_dir / f"{dataset_name}_comprehensive_report.json"
            
            with open(save_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            # 6. Generate HTML report
            html_path = save_path.with_suffix('.html')
            self._generate_html_report(report_data, html_path)
            
            report_info = {
                'report_type': 'comprehensive_analysis',
                'dataset_name': dataset_name,
                'json_path': str(save_path),
                'html_path': str(html_path),
                'data_shape': data.shape,
                'generated_at': datetime.datetime.now().isoformat(),
                'sections_included': list(report_data.keys())
            }
            
            self.logger.info(f"Comprehensive analysis report saved to {save_path}")
            
            return report_info
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive analysis report: {e}")
            raise ReportGenerationError(f"Failed to generate comprehensive analysis report: {e}")
    
    def _generate_executive_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from report data"""
        try:
            summary = {
                'dataset_overview': {},
                'data_quality_assessment': {},
                'key_findings': [],
                'recommendations': [],
                'readiness_for_ml': {}
            }
            
            # Dataset overview
            if 'data_exploration' in report_data:
                basic_info = report_data['data_exploration'].get('basic_info', {})
                summary['dataset_overview'] = {
                    'shape': basic_info.get('shape', 'Unknown'),
                    'memory_usage_mb': basic_info.get('memory_usage_mb', 0),
                    'completeness_ratio': basic_info.get('completeness_ratio', 0),
                    'data_types': basic_info.get('dtypes', {})
                }
            
            # Data quality assessment
            if 'data_exploration' in report_data:
                readiness = report_data['data_exploration'].get('readiness_assessment', {})
                summary['data_quality_assessment'] = {
                    'overall_score': readiness.get('overall_readiness', 0),
                    'readiness_level': readiness.get('readiness_level', 'Unknown'),
                    'is_ready_for_ml': readiness.get('is_ready_for_ml', False)
                }
            
            # Key findings
            key_findings = []
            
            if 'data_exploration' in report_data:
                missing_data = report_data['data_exploration'].get('missing_data', {})
                if missing_data.get('missing_percentage', 0) > 10:
                    key_findings.append(f"High missing data: {missing_data.get('missing_percentage', 0):.1f}%")
                
                quality = report_data['data_exploration'].get('data_quality', {})
                duplicates = quality.get('duplicates', {})
                if duplicates.get('row_duplicate_percentage', 0) > 5:
                    key_findings.append(f"Duplicate rows: {duplicates.get('row_duplicate_percentage', 0):.1f}%")
            
            if 'feature_selection' in report_data:
                feature_summary = report_data['feature_selection'].get('summary', {})
                if feature_summary.get('selection_ratio', 0) < 0.1:
                    key_findings.append("Very few features selected - consider feature engineering")
                elif feature_summary.get('selection_ratio', 0) > 0.8:
                    key_findings.append("Most features selected - consider more aggressive selection")
            
            summary['key_findings'] = key_findings
            
            # Recommendations
            recommendations = []
            
            if 'data_exploration' in report_data:
                readiness = report_data['data_exploration'].get('readiness_assessment', {})
                recommendations.extend(readiness.get('recommendations', []))
            
            if 'feature_selection' in report_data:
                feature_recs = report_data['feature_selection'].get('recommendations', [])
                recommendations.extend(feature_recs)
            
            summary['recommendations'] = recommendations
            
            # ML readiness
            summary['readiness_for_ml'] = {
                'overall_score': summary['data_quality_assessment'].get('overall_score', 0),
                'ready': summary['data_quality_assessment'].get('is_ready_for_ml', False),
                'next_steps': recommendations[:3] if recommendations else ['Review data quality issues']
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate executive summary: {e}")
            return {'error': str(e)}
    
    def _generate_html_report(self, report_data: Dict[str, Any], html_path: Path) -> None:
        """Generate HTML report from report data"""
        try:
            # Simple HTML template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ dataset_name }} - Data Analysis Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                    .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; }
                    .warning { color: #d9534f; }
                    .success { color: #5cb85c; }
                    .info { color: #5bc0de; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{ dataset_name }} - Data Analysis Report</h1>
                    <p>Generated on: {{ generated_at }}</p>
                    <p>Dataset Shape: {{ data_shape[0] }} rows × {{ data_shape[1] }} columns</p>
                </div>
                
                {% if executive_summary %}
                <div class="section">
                    <h2>Executive Summary</h2>
                    <div class="metric">
                        <strong>Overall Score:</strong> {{ executive_summary.data_quality_assessment.overall_score|round(1) }}/100
                    </div>
                    <div class="metric">
                        <strong>ML Ready:</strong> 
                        <span class="{% if executive_summary.data_quality_assessment.is_ready_for_ml %}success{% else %}warning{% endif %}">
                            {{ executive_summary.data_quality_assessment.is_ready_for_ml }}
                        </span>
                    </div>
                    <div class="metric">
                        <strong>Readiness Level:</strong> {{ executive_summary.data_quality_assessment.readiness_level }}
                    </div>
                    
                    {% if executive_summary.key_findings %}
                    <h3>Key Findings</h3>
                    <ul>
                        {% for finding in executive_summary.key_findings %}
                        <li>{{ finding }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if executive_summary.recommendations %}
                    <h3>Recommendations</h3>
                    <ul>
                        {% for rec in executive_summary.recommendations %}
                        <li>{{ rec }}</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
                {% endif %}
                
                {% if data_exploration %}
                <div class="section">
                    <h2>Data Exploration</h2>
                    {% if data_exploration.basic_info %}
                    <h3>Basic Information</h3>
                    <div class="metric">Memory Usage: {{ data_exploration.basic_info.memory_usage_mb|round(2) }} MB</div>
                    <div class="metric">Completeness: {{ (data_exploration.basic_info.completeness_ratio * 100)|round(1) }}%</div>
                    {% endif %}
                    
                    {% if data_exploration.missing_data %}
                    <h3>Missing Data</h3>
                    <div class="metric">Total Missing: {{ data_exploration.missing_data.missing_percentage|round(1) }}%</div>
                    <div class="metric">Columns with Missing: {{ data_exploration.missing_data.columns_with_missing }}</div>
                    {% endif %}
                </div>
                {% endif %}
                
                {% if feature_selection %}
                <div class="section">
                    <h2>Feature Selection</h2>
                    {% if feature_selection.summary %}
                    <div class="metric">Total Features: {{ feature_selection.summary.total_features }}</div>
                    <div class="metric">Selected Features: {{ feature_selection.summary.selected_features }}</div>
                    <div class="metric">Selection Ratio: {{ (feature_selection.summary.selection_ratio * 100)|round(1) }}%</div>
                    {% endif %}
                </div>
                {% endif %}
                
                <div class="section">
                    <h2>Report Details</h2>
                    <p>This report was generated using the 91life Data Science Library.</p>
                    <p>For more detailed analysis, please refer to the JSON report file.</p>
                </div>
            </body>
            </html>
            """
            
            template = Template(html_template)
            html_content = template.render(**report_data)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report saved to {html_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
    
    def generate_automated_profiling_reports(
        self,
        data: pd.DataFrame,
        dataset_name: str = 'dataset',
        target_col: Optional[str] = None,
        include_ydata: bool = True,
        include_sweetviz: bool = True,
        include_comprehensive: bool = True
    ) -> Dict[str, Any]:
        """
        Generate all available automated profiling reports
        
        Args:
            data: Input DataFrame
            dataset_name: Name of the dataset
            target_col: Target column for analysis
            include_ydata: Whether to include YData profiling
            include_sweetviz: Whether to include Sweetviz profiling
            include_comprehensive: Whether to include comprehensive analysis
        
        Returns:
            Dictionary with all generated reports information
        """
        self.logger.info("Generating all automated profiling reports")
        
        try:
            reports_info = {
                'dataset_name': dataset_name,
                'target_column': target_col,
                'generated_at': datetime.datetime.now().isoformat(),
                'reports': {}
            }
            
            # Generate YData profiling report
            if include_ydata and YDATA_AVAILABLE:
                try:
                    ydata_report = self.generate_ydata_profiling_report(
                        data=data,
                        dataset_name=dataset_name
                    )
                    reports_info['reports']['ydata_profiling'] = ydata_report
                except Exception as e:
                    self.logger.warning(f"YData profiling failed: {e}")
                    reports_info['reports']['ydata_profiling'] = {'error': str(e)}
            
            # Generate Sweetviz report
            if include_sweetviz and SWEETVIZ_AVAILABLE:
                try:
                    sweetviz_report = self.generate_sweetviz_report(
                        data=data,
                        target_col=target_col,
                        dataset_name=dataset_name
                    )
                    reports_info['reports']['sweetviz'] = sweetviz_report
                except Exception as e:
                    self.logger.warning(f"Sweetviz profiling failed: {e}")
                    reports_info['reports']['sweetviz'] = {'error': str(e)}
            
            # Generate comprehensive analysis report
            if include_comprehensive:
                try:
                    comprehensive_report = self.generate_comprehensive_analysis_report(
                        data=data,
                        target_col=target_col,
                        dataset_name=dataset_name
                    )
                    reports_info['reports']['comprehensive_analysis'] = comprehensive_report
                except Exception as e:
                    self.logger.warning(f"Comprehensive analysis failed: {e}")
                    reports_info['reports']['comprehensive_analysis'] = {'error': str(e)}
            
            # Save reports summary
            summary_path = self.output_dir / f"{dataset_name}_reports_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(reports_info, f, indent=2, default=str)
            
            reports_info['summary_path'] = str(summary_path)
            
            self.logger.info(f"All profiling reports generated. Summary saved to {summary_path}")
            
            return reports_info
            
        except Exception as e:
            self.logger.error(f"Failed to generate automated profiling reports: {e}")
            raise ReportGenerationError(f"Failed to generate automated profiling reports: {e}")
    
    def create_custom_report(
        self,
        data: pd.DataFrame,
        template_path: str,
        output_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create custom report using Jinja2 template
        
        Args:
            data: Input DataFrame
            template_path: Path to Jinja2 template file
            output_path: Path to save the custom report
            **kwargs: Additional data to pass to template
        
        Returns:
            Dictionary with custom report information
        """
        self.logger.info(f"Creating custom report from template {template_path}")
        
        try:
            # Load template
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            template = Template(template_content)
            
            # Prepare template data
            template_data = {
                'data': data,
                'data_shape': data.shape,
                'generated_at': datetime.datetime.now().isoformat(),
                **kwargs
            }
            
            # Render template
            rendered_content = template.render(**template_data)
            
            # Save report
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            
            report_info = {
                'report_type': 'custom',
                'template_path': template_path,
                'output_path': output_path,
                'data_shape': data.shape,
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            self.logger.info(f"Custom report saved to {output_path}")
            
            return report_info
            
        except Exception as e:
            self.logger.error(f"Failed to create custom report: {e}")
            raise ReportGenerationError(f"Failed to create custom report: {e}")
