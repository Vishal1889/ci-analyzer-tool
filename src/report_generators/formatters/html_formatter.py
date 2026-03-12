"""
HTML Report Formatter
Generates HTML reports with Bootstrap styling and Chart.js visualizations
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json


class HTMLFormatter:
    """Generate HTML reports from report data"""
    
    def __init__(self, report_title: str, tenant_id: str, captured_at: str):
        """
        Initialize HTML formatter
        
        Args:
            report_title: Title of the report
            tenant_id: Tenant identifier
            captured_at: Capture timestamp
        """
        self.report_title = report_title
        self.tenant_id = tenant_id
        self.captured_at = captured_at
    
    def generate_html(self, report_data: Dict[str, Any], output_file: Path) -> None:
        """
        Generate HTML report file
        
        Args:
            report_data: Report data dictionary
            output_file: Output HTML file path
        """
        html_content = self._create_html_document(report_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _create_html_document(self, report_data: Dict[str, Any]) -> str:
        """Create complete HTML document"""
        
        # Determine report type and generate appropriate content
        if 'packages' in report_data:
            body_content = self._generate_package_version_comparison(report_data)
        elif 'variables' in report_data:
            body_content = self._generate_environment_variables(report_data)
        elif 'package_types' in report_data:
            body_content = self._generate_package_statistics(report_data)
        else:
            body_content = self._generate_generic_report(report_data)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report_title} - {self.tenant_id}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            background-color: #f8f9fa;
            padding-top: 20px;
            padding-bottom: 40px;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9rem;
            text-transform: uppercase;
        }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .data-table {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .badge-custom {{
            padding: 8px 12px;
            border-radius: 5px;
            font-weight: 500;
        }}
        .status-success {{ background-color: #d4edda; color: #155724; }}
        .status-warning {{ background-color: #fff3cd; color: #856404; }}
        .status-info {{ background-color: #d1ecf1; color: #0c5460; }}
        .status-secondary {{ background-color: #e2e3e5; color: #383d41; }}
        .footer {{
            text-align: center;
            color: #6c757d;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
        table {{
            font-size: 0.9rem;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>{self.report_title}</h1>
            <p class="mb-0">
                <strong>Tenant:</strong> {self.tenant_id} &nbsp;|&nbsp;
                <strong>Generated:</strong> {self._format_timestamp(self.captured_at)}
            </p>
        </div>
        
        {body_content}
        
        <div class="footer">
            <p class="mb-0">SAP Cloud Integration Analyzer Tool</p>
            <p class="text-muted small">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
    
    def _generate_package_version_comparison(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML for Package Version Comparison report"""
        stats = report_data.get('stats', {})
        packages = report_data.get('packages', [])
        
        # Stats cards
        stats_html = f"""
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('total_packages', 0)}</div>
                    <div class="stat-label">Total Packages</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('custom_packages', 0)}</div>
                    <div class="stat-label">Custom Packages</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('up_to_date', 0)}</div>
                    <div class="stat-label">Up-to-date</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('outdated', 0)}</div>
                    <div class="stat-label">Outdated</div>
                </div>
            </div>
        </div>
        """
        
        # Chart
        chart_data = {
            'labels': ['Up-to-date', 'Outdated', 'Custom', 'No Version Info'],
            'data': [
                stats.get('up_to_date', 0),
                stats.get('outdated', 0),
                stats.get('custom_packages', 0),
                stats.get('no_version_info', 0)
            ]
        }
        
        chart_html = f"""
        <div class="chart-container">
            <h3 class="mb-3">Package Version Status</h3>
            <canvas id="statusChart" style="max-height: 400px;"></canvas>
        </div>
        <script>
            const ctx = document.getElementById('statusChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(chart_data['labels'])},
                    datasets: [{{
                        data: {json.dumps(chart_data['data'])},
                        backgroundColor: ['#28a745', '#ffc107', '#17a2b8', '#6c757d'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                padding: 20,
                                font: {{
                                    size: 14
                                }}
                            }}
                        }},
                        title: {{
                            display: false
                        }}
                    }}
                }}
            }});
        </script>
        """
        
        # Packages table
        table_rows = []
        for pkg in packages:
            status_class = {
                'success': 'status-success',
                'warning': 'status-warning',
                'info': 'status-info',
                'secondary': 'status-secondary'
            }.get(pkg.get('status_class', 'secondary'), 'status-secondary')
            
            table_rows.append(f"""
                <tr>
                    <td>{self._escape_html(pkg.get('package_name', ''))}</td>
                    <td>{self._escape_html(pkg.get('current_version', 'N/A'))}</td>
                    <td>{self._escape_html(pkg.get('latest_version', 'N/A'))}</td>
                    <td><span class="badge-custom {status_class}">{self._escape_html(pkg.get('status', ''))}</span></td>
                    <td>{self._escape_html(pkg.get('package_type', ''))}</td>
                    <td>{self._escape_html(pkg.get('vendor', ''))}</td>
                </tr>
            """)
        
        table_html = f"""
        <div class="data-table">
            <h3 class="mb-3">Package Details</h3>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Package Name</th>
                            <th>Current Version</th>
                            <th>Latest Version</th>
                            <th>Status</th>
                            <th>Type</th>
                            <th>Vendor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return stats_html + chart_html + table_html
    
    def _generate_environment_variables(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML for Environment Variables report"""
        stats = report_data.get('stats', {})
        variables = report_data.get('variables', [])
        
        # Stats cards
        stats_html = f"""
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('total_variables', 0)}</div>
                    <div class="stat-label">Unique Variables</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('total_usages', 0)}</div>
                    <div class="stat-label">Total Usages</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('files_with_vars', 0)}</div>
                    <div class="stat-label">Files with Variables</div>
                </div>
            </div>
        </div>
        """
        
        # Variables table
        table_rows = []
        for var in variables:
            usages = var.get('usages', [])
            usage_count = len(usages)
            
            # Create usage details (show all usages — DataTables handles pagination)
            usage_details = []
            for usage in usages:
                usage_details.append(
                    f"<li><small>{self._escape_html(usage.get('file_path', ''))} "
                    f"({self._escape_html(usage.get('parent_type', ''))})</small></li>"
                )
            
            usage_html = f"<ul class='mb-0'>{''.join(usage_details)}</ul>" if usage_details else "None"
            
            table_rows.append(f"""
                <tr>
                    <td><code>{self._escape_html(var.get('variable_name', ''))}</code></td>
                    <td>{usage_count}</td>
                    <td>{usage_html}</td>
                </tr>
            """)
        
        table_html = f"""
        <div class="data-table">
            <h3 class="mb-3">Environment Variables (HC_ Variables)</h3>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Variable Name</th>
                            <th>Usage Count</th>
                            <th>Used In</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows) if table_rows else '<tr><td colspan="3" class="text-center">No environment variables found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return stats_html + table_html
    
    def _generate_package_statistics(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML for Package Statistics report"""
        stats = report_data.get('stats', {})
        package_types = report_data.get('package_types', [])
        
        # Stats cards
        stats_html = f"""
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('total_packages', 0)}</div>
                    <div class="stat-label">Total Packages</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('total_iflows', 0)}</div>
                    <div class="stat-label">Total IFlows</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('custom_packages', 0)}</div>
                    <div class="stat-label">Custom Packages</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <div class="stat-number">{stats.get('standard_packages', 0)}</div>
                    <div class="stat-label">Standard Packages</div>
                </div>
            </div>
        </div>
        """
        
        # Chart
        if package_types:
            labels = [pt.get('package_type', '') for pt in package_types]
            data = [pt.get('count', 0) for pt in package_types]
            
            chart_html = f"""
            <div class="chart-container">
                <h3 class="mb-3">Package Type Distribution</h3>
                <canvas id="typeChart" style="max-height: 400px;"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('typeChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: [{{
                            label: 'Number of Packages',
                            data: {json.dumps(data)},
                            backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    stepSize: 1
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
            """
        else:
            chart_html = ""
        
        # Package types table
        table_rows = []
        for pt in package_types:
            table_rows.append(f"""
                <tr>
                    <td>{self._escape_html(pt.get('package_type', ''))}</td>
                    <td>{pt.get('count', 0)}</td>
                    <td>{pt.get('iflow_count', 0)}</td>
                    <td>{self._escape_html(pt.get('description', ''))}</td>
                </tr>
            """)
        
        table_html = f"""
        <div class="data-table">
            <h3 class="mb-3">Package Type Breakdown</h3>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Package Type</th>
                            <th>Package Count</th>
                            <th>IFlow Count</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows) if table_rows else '<tr><td colspan="4" class="text-center">No package data available</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return stats_html + chart_html + table_html
    
    def _generate_generic_report(self, report_data: Dict[str, Any]) -> str:
        """Generate generic HTML for unknown report types"""
        return f"""
        <div class="data-table">
            <h3 class="mb-3">Report Data</h3>
            <pre class="bg-light p-3">{json.dumps(report_data, indent=2)}</pre>
        </div>
        """
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if text is None:
            return ''
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))