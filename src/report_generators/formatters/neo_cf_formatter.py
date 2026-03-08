"""
NEO to CF Migration Assessment Report Formatter
Modern tabbed HTML report with SAP BTP theme
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json


class NeoToCFFormatter:
    """Generate modern tabbed HTML report for NEO to CF migration assessment"""
    
    def __init__(self, report_title: str, tenant_id: str, captured_at: str):
        self.report_title = report_title
        self.tenant_id = tenant_id
        self.captured_at = captured_at
    
    def generate_html(self, report_data: Dict[str, Any], output_file: Path) -> None:
        """Generate standalone HTML report with embedded resources"""
        html_content = self._create_html_document(report_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _create_html_document(self, report_data: Dict[str, Any]) -> str:
        """Create complete HTML document with SAP BTP theme"""
        
        metadata = report_data.get('metadata', {})
        dashboard = report_data.get('dashboard', {})
        packages = report_data.get('packages', {})
        versions = report_data.get('versions', {})
        systems = report_data.get('systems', {})
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report_title} - {self.tenant_id}</title>
    
    <!-- Bootstrap 5.3 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- DataTables CSS -->
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <style>
        /* SAP BTP Color Scheme */
        :root {{
            --sap-blue: #0070F2;
            --sap-dark-blue: #0040B0;
            --sap-light-blue: #E8F3FF;
            --sap-green: #0F7D0F;
            --sap-orange: #E76500;
            --sap-red: #BB0000;
            --sap-gray: #5E696E;
            --sap-light-gray: #F5F5F5;
        }}
        
        body {{
            background-color: var(--sap-light-gray);
            font-family: '72', 'Segoe UI', Tahoma, sans-serif;
            padding-top: 20px;
            padding-bottom: 40px;
        }}
        
        .report-header {{
            background: linear-gradient(135deg, var(--sap-blue) 0%, var(--sap-dark-blue) 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .report-header h1 {{
            margin: 0 0 15px 0;
            font-size: 2rem;
            font-weight: 300;
        }}
        
        .report-meta {{
            font-size: 0.9rem;
            opacity: 0.95;
        }}
        
        /* KPI Cards */
        .kpi-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 4px solid var(--sap-blue);
        }}
        
        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        .kpi-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--sap-dark-blue);
            margin: 0;
        }}
        
        .kpi-label {{
            color: var(--sap-gray);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 5px;
        }}
        
        /* Tabs */
        .nav-tabs {{
            border-bottom: 2px solid var(--sap-light-blue);
            margin-bottom: 30px;
        }}
        
        .nav-tabs .nav-link {{
            color: var(--sap-gray);
            border: none;
            padding: 12px 24px;
            font-weight: 500;
            transition: all 0.3s;
        }}
        
        .nav-tabs .nav-link:hover {{
            color: var(--sap-blue);
            background-color: var(--sap-light-blue);
            border: none;
        }}
        
        .nav-tabs .nav-link.active {{
            color: white;
            background-color: var(--sap-blue);
            border: none;
            border-radius: 8px 8px 0 0;
        }}
        
        /* Content Cards */
        .content-card {{
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .content-card h3 {{
            color: var(--sap-dark-blue);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--sap-light-blue);
            font-size: 1.4rem;
            font-weight: 500;
        }}
        
        /* Charts */
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 350px;
        }}
        
        /* Alerts */
        .alert-sap {{
            border-left: 4px solid;
            border-radius: 4px;
            padding: 15px 20px;
            margin-bottom: 15px;
        }}
        
        .alert-warning {{
            background-color: #FFF4E5;
            border-left-color: var(--sap-orange);
            color: #856404;
        }}
        
        .alert-info {{
            background-color: var(--sap-light-blue);
            border-left-color: var(--sap-blue);
            color: #004085;
        }}
        
        /* Status Badges */
        .badge-custom {{
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 0.85rem;
        }}
        
        .status-synced {{ background-color: #E6F4EA; color: var(--sap-green); }}
        .status-outofSync {{ background-color: #FFF4E5; color: var(--sap-orange); }}
        .status-notDeployed {{ background-color: #F5F5F5; color: var(--sap-gray); }}
        .status-current {{ background-color: #E6F4EA; color: var(--sap-green); }}
        .status-outdated {{ background-color: #FDECEA; color: var(--sap-red); }}
        
        /* DataTables Customization */
        .dataTables_wrapper {{
            padding: 0;
        }}
        
        table.dataTable {{
            border-collapse: collapse !important;
            font-size: 0.9rem;
        }}
        
        table.dataTable thead th {{
            background-color: var(--sap-light-blue);
            color: var(--sap-dark-blue);
            font-weight: 600;
            border-bottom: 2px solid var(--sap-blue);
        }}
        
        table.dataTable tbody tr:hover {{
            background-color: var(--sap-light-blue) !important;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .kpi-number {{ font-size: 2rem; }}
            .report-header h1 {{ font-size: 1.5rem; }}
        }}
        
        /* Print styles */
        @media print {{
            .no-print {{ display: none; }}
            body {{ background: white; }}
        }}
    </style>
</head>
<body>
    <div class="container-fluid px-4">
        <!-- Header -->
        <div class="report-header">
            <h1>📊 {self.report_title}</h1>
            <div class="report-meta">
                <strong>Tenant:</strong> {metadata.get('tenant_id', 'N/A')} &nbsp;|&nbsp;
                <strong>Extraction Date:</strong> {metadata.get('report_generated_at', 'N/A')} &nbsp;|&nbsp;
                <strong>Report Version:</strong> {metadata.get('report_version', '1.0')}
            </div>
        </div>
        
        <!-- Navigation Tabs -->
        <ul class="nav nav-tabs no-print" id="reportTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="dashboard-tab" data-bs-toggle="tab" 
                        data-bs-target="#dashboard" type="button" role="tab">
                    🎯 Executive Summary
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="packages-tab" data-bs-toggle="tab" 
                        data-bs-target="#packages" type="button" role="tab">
                    📦 Package Analysis
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="versions-tab" data-bs-toggle="tab" 
                        data-bs-target="#versions" type="button" role="tab">
                    🔄 Version & Deployment
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="systems-tab" data-bs-toggle="tab" 
                        data-bs-target="#systems" type="button" role="tab">
                    🌐 Systems & Adapters
                </button>
            </li>
        </ul>
        
        <!-- Tab Content -->
        <div class="tab-content" id="reportTabContent">
            
            <!-- Tab 1: Executive Summary / Dashboard -->
            <div class="tab-pane fade show active" id="dashboard" role="tabpanel">
                {self._generate_dashboard_tab(dashboard)}
            </div>
            
            <!-- Tab 2: Package Analysis -->
            <div class="tab-pane fade" id="packages" role="tabpanel">
                {self._generate_packages_tab(packages)}
            </div>
            
            <!-- Tab 3: Version & Deployment -->
            <div class="tab-pane fade" id="versions" role="tabpanel">
                {self._generate_versions_tab(versions)}
            </div>
            
            <!-- Tab 4: Systems & Adapters -->
            <div class="tab-pane fade" id="systems" role="tabpanel">
                {self._generate_systems_tab(systems)}
            </div>
            
        </div>
        
        <!-- Footer -->
        <div class="text-center mt-5 mb-3" style="color: var(--sap-gray); font-size: 0.9rem;">
            <p class="mb-1">SAP Cloud Integration Analyzer Tool</p>
            <p class="mb-0">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <!-- Bootstrap 5.3 JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- jQuery (required for DataTables) -->
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    
    <!-- DataTables JS -->
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.bootstrap5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js"></script>
    
    <script>
        // Report Data
        var reportData = {json.dumps(report_data)};
        
        // Initialize DataTables when document is ready
        $(document).ready(function() {{
            // Initialize all data tables with common settings
            $('.data-table').DataTable({{
                pageLength: 25,
                lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
                responsive: true,
                order: [[0, 'asc']]
            }});
            
            // Initialize charts
            initCharts();
        }});
        
        function initCharts() {{
            {self._generate_chart_js(dashboard, versions, systems)}
        }}
    </script>
</body>
</html>"""
    
    def _generate_dashboard_tab(self, dashboard: Dict[str, Any]) -> str:
        """Generate executive summary dashboard tab"""
        kpis = dashboard.get('kpis', {})
        alerts = dashboard.get('alerts', [])
        top_packages = dashboard.get('top_packages', [])
        
        # KPI Cards
        kpi_html = f"""
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-number">{kpis.get('total_packages', 0)}</div>
                    <div class="kpi-label">Total Packages</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-number">{kpis.get('total_artifacts', 0)}</div>
                    <div class="kpi-label">Total Artifacts</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-number">{kpis.get('unique_systems', 0)}</div>
                    <div class="kpi-label">Connected Systems</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card" style="border-left-color: var(--sap-green);">
                    <div class="kpi-number" style="color: var(--sap-green);">{kpis.get('readiness_score', 0)}%</div>
                    <div class="kpi-label">Migration Readiness</div>
                </div>
            </div>
        </div>
        """
        
        # Alerts Section
        alerts_html = ""
        if alerts:
            alerts_html = '<div class="content-card"><h3>🚨 Critical Alerts</h3>'
            for alert in alerts:
                alert_type = alert.get('type', 'info')
                alert_class = 'alert-warning' if alert_type == 'warning' else 'alert-info'
                alerts_html += f'<div class="alert-sap {alert_class}">{self._escape_html(alert.get("message", ""))}</div>'
            alerts_html += '</div>'
        
        # Charts and Top Packages
        content_html = f"""
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 style="color: var(--sap-dark-blue); margin-bottom: 20px;">Package Distribution</h4>
                    <canvas id="packageDistChart"></canvas>
                </div>
            </div>
            <div class="col-md-6">
                <div class="content-card">
                    <h3>📊 Top 5 Packages by Complexity</h3>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Package</th>
                                    <th>IFlows</th>
                                    <th>Scripts</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'''
                                <tr>
                                    <td>{self._escape_html(pkg.get("package_name", ""))}</td>
                                    <td>{pkg.get("iflow_count", 0)}</td>
                                    <td>{pkg.get("script_count", 0)}</td>
                                    <td><strong>{pkg.get("total_artifacts", 0)}</strong></td>
                                </tr>
                                ''' for pkg in top_packages])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return kpi_html + alerts_html + content_html
    
    def _generate_packages_tab(self, packages: Dict[str, Any]) -> str:
        """Generate package analysis tab"""
        package_list = packages.get('packages', [])
        stats = packages.get('stats', {})
        
        stats_html = f"""
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="kpi-card">
                    <div class="kpi-number">{stats.get('total_packages', 0)}</div>
                    <div class="kpi-label">Total Packages</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="kpi-card">
                    <div class="kpi-number">{stats.get('total_artifacts', 0)}</div>
                    <div class="kpi-label">Total Artifacts</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="kpi-card">
                    <div class="kpi-number">{stats.get('avg_artifacts_per_package', 0)}</div>
                    <div class="kpi-label">Avg Artifacts/Package</div>
                </div>
            </div>
        </div>
        """
        
        table_rows = []
        for pkg in package_list:
            pkg_type = pkg.get('package_type', 'Unknown')
            type_class = 'primary' if 'Custom' in pkg_type else ('success' if 'Read-Only' in pkg_type else 'secondary')
            
            table_rows.append(f'''
                <tr>
                    <td>{self._escape_html(pkg.get("package_name", ""))}</td>
                    <td><span class="badge bg-{type_class}">{self._escape_html(pkg_type)}</span></td>
                    <td>{pkg.get("iflow_count", 0)}</td>
                    <td>{pkg.get("script_count", 0)}</td>
                    <td>{pkg.get("msg_map_count", 0)}</td>
                    <td>{pkg.get("val_map_count", 0)}</td>
                    <td><strong>{pkg.get("total_artifacts", 0)}</strong></td>
                </tr>
            ''')
        
        table_html = f'''
        <div class="content-card">
            <h3>📦 Package Details</h3>
            <table class="table table-striped table-hover data-table" id="packagesTable">
                <thead>
                    <tr>
                        <th>Package Name</th>
                        <th>Type</th>
                        <th>IFlows</th>
                        <th>Scripts</th>
                        <th>Msg Maps</th>
                        <th>Val Maps</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
        '''
        
        return stats_html + table_html
    
    def _generate_versions_tab(self, versions: Dict[str, Any]) -> str:
        """Generate version and deployment status tab"""
        deployments = versions.get('artifact_deployments', [])
        dep_stats = versions.get('deployment_stats', {})
        
        stats_html = f"""
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="kpi-card" style="border-left-color: var(--sap-green);">
                    <div class="kpi-number" style="color: var(--sap-green);">{dep_stats.get('synced', 0)}</div>
                    <div class="kpi-label">Synced</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="kpi-card" style="border-left-color: var(--sap-orange);">
                    <div class="kpi-number" style="color: var(--sap-orange);">{dep_stats.get('out_of_sync', 0)}</div>
                    <div class="kpi-label">Out of Sync</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="kpi-card" style="border-left-color: var(--sap-gray);">
                    <div class="kpi-number" style="color: var(--sap-gray);">{dep_stats.get('not_deployed', 0)}</div>
                    <div class="kpi-label">Not Deployed</div>
                </div>
            </div>
        </div>
        """
        
        chart_html = '''
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 style="color: var(--sap-dark-blue); margin-bottom: 20px;">Deployment Status</h4>
                    <canvas id="deploymentChart"></canvas>
                </div>
            </div>
        </div>
        '''
        
        table_rows = []
        for dep in deployments:
            status = dep.get('deployment_status', 'Unknown')
            status_class = f'status-{status.replace(" ", "")}'
            
            table_rows.append(f'''
                <tr>
                    <td>{self._escape_html(dep.get("artifact_name", ""))}</td>
                    <td>{self._escape_html(dep.get("package_name", ""))}</td>
                    <td>{self._escape_html(dep.get("design_version", "N/A"))}</td>
                    <td>{self._escape_html(dep.get("runtime_version", "N/A"))}</td>
                    <td><span class="badge-custom {status_class}">{self._escape_html(status)}</span></td>
                </tr>
            ''')
        
        table_html = f'''
        <div class="content-card">
            <h3>🔄 Deployment Status Details</h3>
            <table class="table table-striped table-hover data-table" id="deploymentsTable">
                <thead>
                    <tr>
                        <th>Artifact</th>
                        <th>Package</th>
                        <th>Design Version</th>
                        <th>Runtime Version</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
        '''
        
        return stats_html + chart_html + table_html
    
    def _generate_systems_tab(self, systems: Dict[str, Any]) -> str:
        """Generate systems and adapters tab"""
        system_list = systems.get('systems', [])
        adapter_list = systems.get('adapters', [])
        stats = systems.get('stats', {})
        
        stats_html = f"""
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="kpi-card">
                    <div class="kpi-number">{stats.get('unique_systems', 0)}</div>
                    <div class="kpi-label">Unique Systems</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="kpi-card">
                    <div class="kpi-number">{stats.get('total_adapters', 0)}</div>
                    <div class="kpi-label">Total Adapter Instances</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="kpi-card">
                    <div class="kpi-number">{stats.get('adapter_types', 0)}</div>
                    <div class="kpi-label">Adapter Types</div>
                </div>
            </div>
        </div>
        """
        
        chart_html = '''
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="chart-container">
                    <h4 style="color: var(--sap-dark-blue); margin-bottom: 20px;">Adapter Distribution</h4>
                    <canvas id="adapterChart"></canvas>
                </div>
            </div>
        </div>
        '''
        
        # Systems table
        system_rows = []
        for sys in system_list[:50]:  # Limit to first 50 for performance
            system_rows.append(f'''
                <tr>
                    <td>{self._escape_html(sys.get("system_name", ""))}</td>
                    <td>{self._escape_html(sys.get("adapter_type", ""))}</td>
                    <td>{self._escape_html(sys.get("direction", ""))}</td>
                    <td>{sys.get("usage_count", 0)}</td>
                </tr>
            ''')
        
        systems_table = f'''
        <div class="content-card">
            <h3>🌐 Connected Systems</h3>
            <table class="table table-striped table-hover data-table" id="systemsTable">
                <thead>
                    <tr>
                        <th>System</th>
                        <th>Adapter Type</th>
                        <th>Direction</th>
                        <th>Usage Count</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(system_rows)}
                </tbody>
            </table>
        </div>
        '''
        
        # Adapters table
        adapter_rows = []
        for adp in adapter_list:
            adapter_rows.append(f'''
                <tr>
                    <td>{self._escape_html(adp.get("adapter_type", ""))}</td>
                    <td>{adp.get("sender_count", 0)}</td>
                    <td>{adp.get("receiver_count", 0)}</td>
                    <td><strong>{adp.get("total_count", 0)}</strong></td>
                </tr>
            ''')
        
        adapters_table = f'''
        <div class="content-card mt-4">
            <h3>🔌 Adapter Types Summary</h3>
            <table class="table table-striped table-hover data-table" id="adaptersTable">
                <thead>
                    <tr>
                        <th>Adapter Type</th>
                        <th>Sender</th>
                        <th>Receiver</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(adapter_rows)}
                </tbody>
            </table>
        </div>
        '''
        
        return stats_html + chart_html + systems_table + adapters_table
    
    def _generate_chart_js(self, dashboard: Dict[str, Any], versions: Dict[str, Any], systems: Dict[str, Any]) -> str:
        """Generate Chart.js initialization code"""
        package_dist = dashboard.get('package_distribution', [])
        dep_stats = versions.get('deployment_stats', {})
        adapters = systems.get('adapters', [])
        
        return f"""
            // Package Distribution Donut Chart
            if (document.getElementById('packageDistChart')) {{
                new Chart(document.getElementById('packageDistChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: {json.dumps([p['type'] for p in package_dist])},
                        datasets: [{{
                            data: {json.dumps([p['count'] for p in package_dist])},
                            backgroundColor: {json.dumps([p['color'] for p in package_dist])},
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
                                labels: {{ padding: 15, font: {{ size: 13 }} }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Deployment Status Donut Chart
            if (document.getElementById('deploymentChart')) {{
                new Chart(document.getElementById('deploymentChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Synced', 'Out of Sync', 'Not Deployed'],
                        datasets: [{{
                            data: [{dep_stats.get('synced', 0)}, {dep_stats.get('out_of_sync', 0)}, {dep_stats.get('not_deployed', 0)}],
                            backgroundColor: ['#0F7D0F', '#E76500', '#5E696E'],
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
                                labels: {{ padding: 15, font: {{ size: 13 }} }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Adapter Distribution Donut Chart
            if (document.getElementById('adapterChart')) {{
                new Chart(document.getElementById('adapterChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: {json.dumps([a['adapter_type'] for a in adapters[:8]])},
                        datasets: [{{
                            data: {json.dumps([a['total_count'] for a in adapters[:8]])},
                            backgroundColor: ['#0070F2', '#0F7D0F', '#E76500', '#5E696E', '#BB0000', '#00A8E1', '#FF9500', '#6A6D70'],
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
                                labels: {{ padding: 15, font: {{ size: 12 }} }}
                            }}
                        }}
                    }}
                }});
            }}
        """
    
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