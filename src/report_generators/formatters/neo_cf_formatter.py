"""
NEO to CF Migration Assessment Report Formatter
SAP BTP themed HTML report generator with compact design
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class NeoToCFFormatter:
    """Generates SAP BTP themed HTML report for NEO to CF migration assessment"""
    
    # SAP BTP Color Scheme (from Cloud Transport Management)
    COLORS = {
        'primary_blue': '#0A6ED1',
        'dark_blue': '#0854A0',
        'light_blue': '#EDF5FA',
        'success_green': '#2E844A',
        'warning_orange': '#F0AB00',
        'error_red': '#E52929',
        'text_dark': '#32363A',
        'text_gray': '#6A6D70',
        'border_gray': '#E5E5E5',
        'background': '#F7F7F7',
        'white': '#FFFFFF'
    }
    
    def __init__(self, report_title: str, tenant_id: str, captured_at: str):
        self.report_title = report_title
        self.tenant_id = tenant_id
        self.captured_at = captured_at
    
    def generate_html(self, data: Dict[str, Any], output_file: Path):
        """Generate complete HTML report"""
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report_title} - {self.tenant_id}</title>
    
    <!-- Bootstrap 5.3 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- DataTables CSS -->
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    
    <!-- DataTables Buttons CSS -->
    <link href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css" rel="stylesheet">
    
    <style>
{self._generate_css()}
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
{self._generate_header(data)}
        
        <!-- Navigation Tabs -->
{self._generate_tabs()}
        
        <!-- Tab Content -->
        <div class="tab-content" id="reportTabContent">
{self._generate_tab_executive_summary(data)}
{self._generate_tab_package_analysis(data)}
{self._generate_tab_version_comparison(data)}
{self._generate_tab_deployment_status(data)}
{self._generate_tab_systems_adapters(data)}
        </div>
        
        <!-- Footer -->
{self._generate_footer(data)}
    </div>
    
    <!-- JavaScript -->
{self._generate_javascript(data)}
</body>
</html>"""
        
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_css(self) -> str:
        """Generate SAP BTP themed CSS"""
        return f"""
        /* SAP BTP Theme */
        :root {{
            --sap-blue: {self.COLORS['primary_blue']};
            --sap-dark-blue: {self.COLORS['dark_blue']};
            --sap-light-blue: {self.COLORS['light_blue']};
            --sap-green: {self.COLORS['success_green']};
            --sap-orange: {self.COLORS['warning_orange']};
            --sap-red: {self.COLORS['error_red']};
            --sap-text-dark: {self.COLORS['text_dark']};
            --sap-text-gray: {self.COLORS['text_gray']};
            --sap-border: {self.COLORS['border_gray']};
            --sap-background: {self.COLORS['background']};
        }}
        
        body {{
            background-color: var(--sap-background);
            font-family: '72', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            color: var(--sap-text-dark);
            font-size: 14px;
            line-height: 1.5;
        }}
        
        /* Header */
        .report-header {{
            background-color: var(--sap-blue);
            color: white;
            padding: 24px 32px;
            border-radius: 4px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .report-header h1 {{
            margin: 0 0 8px 0;
            font-size: 24px;
            font-weight: 400;
        }}
        
        .report-meta {{
            font-size: 13px;
            opacity: 0.95;
        }}
        
        /* KPI Cards */
        .kpi-card {{
            background: white;
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid var(--sap-border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        .kpi-number {{
            font-size: 32px;
            font-weight: 600;
            color: var(--sap-dark-blue);
            margin: 0;
            line-height: 1.2;
        }}
        
        .kpi-label {{
            color: var(--sap-text-gray);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }}
        
        /* Tabs */
        .nav-tabs {{
            border-bottom: 1px solid var(--sap-border);
            margin-bottom: 24px;
        }}
        
        .nav-tabs .nav-link {{
            color: var(--sap-text-gray);
            border: none;
            padding: 12px 20px;
            font-weight: 500;
            font-size: 14px;
            border-radius: 4px 4px 0 0;
        }}
        
        .nav-tabs .nav-link:hover {{
            color: var(--sap-blue);
            background-color: var(--sap-light-blue);
        }}
        
        .nav-tabs .nav-link.active {{
            color: var(--sap-blue);
            background-color: white;
            border: 1px solid var(--sap-border);
            border-bottom-color: white;
            margin-bottom: -1px;
        }}
        
        /* Content Cards */
        .content-card {{
            background: white;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid var(--sap-border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        .content-card h3 {{
            color: var(--sap-dark-blue);
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--sap-light-blue);
            font-size: 16px;
            font-weight: 600;
        }}
        
        /* Horizontal Stacked Bar Charts */
        .bar-chart-container {{
            background: white;
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid var(--sap-border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        .bar-chart-container h4 {{
            color: var(--sap-dark-blue);
            margin-bottom: 16px;
            font-size: 14px;
            font-weight: 600;
        }}
        
        .stacked-bar {{
            display: flex;
            width: 100%;
            height: 40px;
            border-radius: 4px;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            margin-bottom: 16px;
        }}
        
        .bar-segment {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 12px;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .bar-segment:hover {{
            opacity: 0.85;
            transform: scaleY(1.05);
            cursor: pointer;
        }}
        
        .bar-segment span {{
            white-space: nowrap;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}
        
        .bar-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-top: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 12px;
            color: var(--sap-text-dark);
        }}
        
        .legend-color {{
            width: 14px;
            height: 14px;
            border-radius: 3px;
            margin-right: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        
        .legend-label {{
            font-weight: 500;
        }}
        
        .legend-value {{
            margin-left: 4px;
            color: var(--sap-text-gray);
        }}
        
        /* Alerts */
        .alert-box {{
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 12px;
            border-left: 3px solid;
            font-size: 13px;
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
        .status-badge {{
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: 500;
            font-size: 12px;
            display: inline-block;
        }}
        
        .status-uptodate {{ background-color: #E6F4EA; color: var(--sap-green); }}
        .status-updateavailable {{ background-color: #FFF4E5; color: var(--sap-orange); }}
        .status-manualcheck {{ background-color: #F5F5F5; color: var(--sap-text-gray); }}
        .status-inSync {{ background-color: #E6F4EA; color: var(--sap-green); }}
        .status-outofSync {{ background-color: #FFF4E5; color: var(--sap-orange); }}
        .status-notDeployed {{ background-color: #F5F5F5; color: var(--sap-text-gray); }}
        
        /* DataTables Buttons */
        .dt-buttons {{
            margin-bottom: 12px;
        }}
        
        .dt-button {{
            background-color: white !important;
            border: 1px solid var(--sap-border) !important;
            border-radius: 4px !important;
            padding: 6px 14px !important;
            margin-right: 8px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: var(--sap-text-dark) !important;
            transition: all 0.2s ease !important;
        }}
        
        .dt-button:hover {{
            background-color: var(--sap-light-blue) !important;
            border-color: var(--sap-blue) !important;
            color: var(--sap-blue) !important;
        }}
        
        .dt-button.buttons-excel {{
            background-color: var(--sap-green) !important;
            border-color: var(--sap-green) !important;
            color: white !important;
        }}
        
        .dt-button.buttons-excel:hover {{
            background-color: #236A35 !important;
            border-color: #236A35 !important;
        }}
        
        .dt-button.buttons-csv {{
            background-color: var(--sap-blue) !important;
            border-color: var(--sap-blue) !important;
            color: white !important;
        }}
        
        .dt-button.buttons-csv:hover {{
            background-color: var(--sap-dark-blue) !important;
            border-color: var(--sap-dark-blue) !important;
        }}
        
        /* DataTables */
        .dataTables_wrapper {{
            font-size: 13px;
        }}
        
        .dataTables_wrapper .dataTables_filter {{
            float: none;
            text-align: left;
            margin-bottom: 12px;
        }}
        
        .dataTables_wrapper .dataTables_filter input {{
            border: 1px solid var(--sap-border);
            border-radius: 4px;
            padding: 6px 12px;
            width: 300px;
            font-size: 13px;
        }}
        
        .dataTables_wrapper .dataTables_filter input:focus {{
            outline: none;
            border-color: var(--sap-blue);
            box-shadow: 0 0 0 2px rgba(10, 110, 209, 0.1);
        }}
        
        .dataTables_wrapper .dataTables_length {{
            margin-bottom: 12px;
        }}
        
        .dataTables_wrapper .dataTables_length select {{
            border: 1px solid var(--sap-border);
            border-radius: 4px;
            padding: 6px 32px 6px 12px;
            font-size: 13px;
            background-color: white;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236A6D70' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 8px center;
            background-size: 12px;
            appearance: none;
            -webkit-appearance: none;
            -moz-appearance: none;
            cursor: pointer;
            min-width: 70px;
        }}
        
        .dataTables_wrapper .dataTables_length select:focus {{
            outline: none;
            border-color: var(--sap-blue);
            box-shadow: 0 0 0 2px rgba(10, 110, 209, 0.1);
        }}
        
        .dataTables_wrapper .dataTables_length select:hover {{
            border-color: var(--sap-blue);
        }}
        
        .dataTables_wrapper .dataTables_length label {{
            font-size: 13px;
            color: var(--sap-text-dark);
            font-weight: 400;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .dataTables_wrapper .dataTables_info {{
            font-size: 12px;
            color: var(--sap-text-gray);
        }}
        
        .dataTables_wrapper .dataTables_paginate {{
            margin-top: 12px;
        }}
        
        .dataTables_wrapper .dataTables_paginate .paginate_button {{
            padding: 4px 10px;
            margin: 0 2px;
            border-radius: 3px;
            border: 1px solid var(--sap-border);
            background-color: white;
            color: var(--sap-text-dark);
        }}
        
        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
            background-color: var(--sap-light-blue);
            border-color: var(--sap-blue);
            color: var(--sap-blue);
        }}
        
        .dataTables_wrapper .dataTables_paginate .paginate_button.current {{
            background-color: var(--sap-blue);
            border-color: var(--sap-blue);
            color: white;
        }}
        
        table.dataTable thead th {{
            background-color: var(--sap-light-blue);
            color: var(--sap-dark-blue);
            font-weight: 600;
            border-bottom: 1px solid var(--sap-border);
            padding: 12px 8px;
        }}
        
        table.dataTable tbody tr {{
            border-bottom: 1px solid var(--sap-border);
        }}
        
        table.dataTable tbody tr:hover {{
            background-color: var(--sap-light-blue) !important;
        }}
        
        table.dataTable tbody td {{
            padding: 10px 8px;
        }}
        
        /* Column Filters */
        .column-filters {{
            background-color: var(--sap-light-blue);
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 16px;
        }}
        
        .column-filters select {{
            border: 1px solid var(--sap-border);
            border-radius: 4px;
            padding: 6px 12px;
            margin: 0 8px 8px 0;
            font-size: 13px;
            background-color: white;
            min-width: 150px;
        }}
        
        .column-filters select:focus {{
            outline: none;
            border-color: var(--sap-blue);
            box-shadow: 0 0 0 2px rgba(10, 110, 209, 0.1);
        }}
        
        .column-filters label {{
            font-size: 12px;
            color: var(--sap-text-gray);
            margin-right: 4px;
            font-weight: 500;
        }}
        
        .filter-group {{
            display: inline-block;
            margin-right: 16px;
            margin-bottom: 8px;
        }}
        
        /* Footer */
        .report-footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px 0;
            color: var(--sap-text-gray);
            font-size: 12px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .kpi-number {{ font-size: 24px; }}
            .report-header h1 {{ font-size: 20px; }}
        }}
"""
    
    def _generate_header(self, data: Dict[str, Any]) -> str:
        """Generate report header"""
        metadata = data.get('metadata', {})
        captured_date = metadata.get('report_generated_at', self.captured_at)
        
        return f"""        <div class="report-header">
            <h1>📊 {self.report_title}</h1>
            <div class="report-meta">
                <strong>Tenant:</strong> {self.tenant_id} &nbsp;|&nbsp;
                <strong>Extraction Date:</strong> {captured_date} &nbsp;|&nbsp;
                <strong>Report Version:</strong> {metadata.get('report_version', '1.0')}
            </div>
        </div>"""
    
    def _generate_tabs(self) -> str:
        """Generate navigation tabs"""
        return """        <ul class="nav nav-tabs" id="reportTabs" role="tablist">
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
                    📋 Standard Content Analysis
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="deployment-tab" data-bs-toggle="tab" 
                        data-bs-target="#deployment" type="button" role="tab">
                    📊 Deployment Status
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="systems-tab" data-bs-toggle="tab" 
                        data-bs-target="#systems" type="button" role="tab">
                    🌐 Systems & Adapters
                </button>
            </li>
        </ul>"""
    
    def _generate_stacked_bar(self, data_items: list, title: str) -> str:
        """Generate a horizontal stacked bar chart"""
        total = sum(item['count'] for item in data_items if item['count'] > 0)
        if total == 0:
            return f"""
                <div class="bar-chart-container">
                    <h4>{title}</h4>
                    <p class="text-muted">No data available</p>
                </div>"""
        
        # Generate bar segments
        segments_html = ""
        for item in data_items:
            if item['count'] > 0:
                percentage = (item['count'] / total) * 100
                # Only show label if segment is wide enough
                label = f"{percentage:.0f}%" if percentage >= 8 else ""
                segments_html += f"""
                    <div class="bar-segment" style="flex: {percentage}; background-color: {item['color']};" 
                         title="{item['type']}: {item['count']} ({percentage:.1f}%)">
                        <span>{label}</span>
                    </div>"""
        
        # Generate legend
        legend_html = ""
        for item in data_items:
            if item['count'] > 0:
                percentage = (item['count'] / total) * 100
                legend_html += f"""
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: {item['color']};"></div>
                        <span class="legend-label">{item['type']}</span>
                        <span class="legend-value">({item['count']} • {percentage:.1f}%)</span>
                    </div>"""
        
        return f"""
                <div class="bar-chart-container">
                    <h4>{title}</h4>
                    <div class="stacked-bar">
                        {segments_html}
                    </div>
                    <div class="bar-legend">
                        {legend_html}
                    </div>
                </div>"""
    
    def _generate_tab_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary tab"""
        dashboard = data.get('dashboard', {})
        kpis = dashboard.get('kpis', {})
        
        # KPI Cards
        kpi_html = f"""            <div class="tab-pane fade show active" id="dashboard" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col-md-3 col-sm-6">
                        <div class="kpi-card">
                            <div class="kpi-number">{kpis.get('total_packages', 0)}</div>
                            <div class="kpi-label">Total Packages</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="kpi-card">
                            <div class="kpi-number">{kpis.get('total_artifacts', 0)}</div>
                            <div class="kpi-label">Total Artifacts</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="kpi-card">
                            <div class="kpi-number">{kpis.get('unique_systems', 0)}</div>
                            <div class="kpi-label">Connected Systems</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="kpi-card">
                            <div class="kpi-number" style="color: var(--sap-green);">{kpis.get('readiness_score', 0)}%</div>
                            <div class="kpi-label">Migration Readiness</div>
                        </div>
                    </div>
                </div>"""
        
        # Alerts
        alerts = dashboard.get('alerts', [])
        if alerts:
            kpi_html += """
                <div class="content-card">
                    <h3>🚨 Critical Alerts</h3>"""
            for alert in alerts:
                alert_class = 'alert-warning' if alert['type'] == 'warning' else 'alert-info'
                kpi_html += f"""
                    <div class="alert-box {alert_class}">{alert['message']}</div>"""
            kpi_html += """
                </div>"""
        
        # Package Distribution Bar Chart + Top Packages
        package_dist = dashboard.get('package_distribution', [])
        top_packages = dashboard.get('top_packages', [])
        
        # Generate stacked bar for package distribution
        pkg_bar = self._generate_stacked_bar(package_dist, "📦 Package Distribution")
        
        kpi_html += f"""
                {pkg_bar}
                
                <div class="content-card">
                    <h3>📊 Top 5 Packages by Complexity</h3>
                    <div class="table-responsive">
                        <table class="table table-sm table-hover">
                            <thead>
                                <tr>
                                    <th>Package</th>
                                    <th class="text-center">IFlows</th>
                                    <th class="text-center">Scripts</th>
                                    <th class="text-center">Mappings</th>
                                    <th class="text-center">Total</th>
                                </tr>
                            </thead>
                            <tbody>"""
        
        for pkg in top_packages[:5]:
            mappings = pkg.get('msg_map_count', 0) + pkg.get('val_map_count', 0)
            kpi_html += f"""
                                <tr>
                                    <td>{pkg.get('package_name', 'Unknown')}</td>
                                    <td class="text-center">{pkg.get('iflow_count', 0)}</td>
                                    <td class="text-center">{pkg.get('script_count', 0)}</td>
                                    <td class="text-center">{mappings}</td>
                                    <td class="text-center"><strong>{pkg.get('total_artifacts', 0)}</strong></td>
                                </tr>"""
        
        kpi_html += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>"""
        
        return kpi_html
    
    def _generate_tab_package_analysis(self, data: Dict[str, Any]) -> str:
        """Generate package analysis tab"""
        packages_data = data.get('packages', {})
        packages = packages_data.get('packages', [])
        stats = packages_data.get('stats', {})
        
        # Calculate totals for column headers
        total_iflows = sum(pkg.get('iflow_count', 0) for pkg in packages)
        total_scripts = sum(pkg.get('script_count', 0) for pkg in packages)
        total_msg_maps = sum(pkg.get('msg_map_count', 0) for pkg in packages)
        total_val_maps = sum(pkg.get('val_map_count', 0) for pkg in packages)
        total_artifacts = stats.get('total_artifacts', 0)
        
        html = f"""            <div class="tab-pane fade" id="packages" role="tabpanel">
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
                
                <div class="content-card">
                    <h3>📦 Package Details</h3>
                    <table class="table table-sm table-hover dataTable" id="packagesTable">
                        <thead>
                            <tr>
                                <th>Package Name</th>
                                <th>Type</th>
                                <th class="text-center">IFlows ({total_iflows})</th>
                                <th class="text-center">Scripts ({total_scripts})</th>
                                <th class="text-center">Msg Maps ({total_msg_maps})</th>
                                <th class="text-center">Val Maps ({total_val_maps})</th>
                                <th class="text-center">Total ({total_artifacts})</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for pkg in packages:
            badge_class = 'bg-primary' if pkg['package_type'] == 'Custom' else ('bg-success' if 'Configure-Only' in pkg['package_type'] else 'bg-secondary')
            html += f"""
                            <tr>
                                <td>{pkg['package_name']}</td>
                                <td><span class="badge {badge_class}">{pkg['package_type']}</span></td>
                                <td class="text-center">{pkg['iflow_count']}</td>
                                <td class="text-center">{pkg['script_count']}</td>
                                <td class="text-center">{pkg['msg_map_count']}</td>
                                <td class="text-center">{pkg['val_map_count']}</td>
                                <td class="text-center"><strong>{pkg['total_artifacts']}</strong></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _generate_tab_version_comparison(self, data: Dict[str, Any]) -> str:
        """Generate version comparison tab (NEW!)"""
        version_comp = data.get('version_comparison', {})
        comparisons = version_comp.get('comparisons', [])
        stats = version_comp.get('stats', {})
        discover_available = version_comp.get('stats', {}).get('discover_available', False)
        
        html = f"""            <div class="tab-pane fade" id="versions" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col-md-4">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-green);">
                            <div class="kpi-number" style="color: var(--sap-green);">{stats.get('up_to_date', 0)}</div>
                            <div class="kpi-label">✅ Up-to-date</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-orange);">
                            <div class="kpi-number" style="color: var(--sap-orange);">{stats.get('updates_available', 0)}</div>
                            <div class="kpi-label">⚠️ Updates Available</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-text-gray);">
                            <div class="kpi-number" style="color: var(--sap-text-gray);">{stats.get('manual_check', 0)}</div>
                            <div class="kpi-label">🔍 Manual Check</div>
                        </div>
                    </div>
                </div>"""
        
        if not discover_available:
            html += """
                <div class="alert-box alert-info">
                    <strong>Note:</strong> Discover tenant version data is not available. Enable DOWNLOAD_DISCOVER_VERSIONS in configuration to see version comparisons.
                </div>"""
        
        html += """
                <div class="content-card">
                    <h3>📋 Standard Package Version Comparison</h3>
                    <table class="table table-sm table-hover dataTable" id="versionCompTable">
                        <thead>
                            <tr>
                                <th>Package Name</th>
                                <th class="text-center">Current Version (Design)</th>
                                <th class="text-center">Latest Version (Discover)</th>
                                <th class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for comp in comparisons:
            status = comp.get('status', 'Unknown')
            status_class = 'status-uptodate' if status == 'Up-to-date' else ('status-updateavailable' if status == 'Update available' else 'status-manualcheck')
            
            html += f"""
                            <tr>
                                <td>{comp.get('package_name', 'Unknown')}</td>
                                <td class="text-center">{comp.get('design_version', 'N/A')}</td>
                                <td class="text-center">{comp.get('discover_version', 'N/A')}</td>
                                <td class="text-center"><span class="status-badge {status_class}">{status}</span></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _generate_tab_deployment_status(self, data: Dict[str, Any]) -> str:
        """Generate deployment status tab"""
        versions = data.get('versions', {})
        deployments = versions.get('artifact_deployments', [])
        stats = versions.get('deployment_stats', {})
        
        # Prepare deployment data for stacked bar
        deploy_data = [
            {'type': 'Synced', 'count': stats.get('synced', 0), 'color': '#2E844A'},
            {'type': 'Out of Sync', 'count': stats.get('out_of_sync', 0), 'color': '#F0AB00'},
            {'type': 'Not Deployed', 'count': stats.get('not_deployed', 0), 'color': '#6A6D70'}
        ]
        deploy_bar = self._generate_stacked_bar(deploy_data, "📊 Deployment Status Distribution")
        
        html = f"""            <div class="tab-pane fade" id="deployment" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col-md-4">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-green);">
                            <div class="kpi-number" style="color: var(--sap-green);">{stats.get('synced', 0)}</div>
                            <div class="kpi-label">Synced</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-orange);">
                            <div class="kpi-number" style="color: var(--sap-orange);">{stats.get('out_of_sync', 0)}</div>
                            <div class="kpi-label">Out of Sync</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-text-gray);">
                            <div class="kpi-number" style="color: var(--sap-text-gray);">{stats.get('not_deployed', 0)}</div>
                            <div class="kpi-label">Not Deployed</div>
                        </div>
                    </div>
                </div>
                
                {deploy_bar}
                
                <div class="content-card">
                    <h3>📊 Deployment Status Details</h3>
                    <table class="table table-sm table-hover dataTable" id="deploymentsTable">
                        <thead>
                            <tr>
                                <th>Artifact Name</th>
                                <th>Type</th>
                                <th>Package Name</th>
                                <th class="text-center">Design Version</th>
                                <th class="text-center">Runtime Version</th>
                                <th class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for dep in deployments:
            status = dep.get('deployment_status', 'Unknown')
            status_class = 'status-inSync' if status == 'In Sync' else ('status-outofSync' if status == 'Out of Sync' else 'status-notDeployed')
            
            html += f"""
                            <tr>
                                <td>{dep.get('artifact_name', 'Unknown')}</td>
                                <td>{dep.get('artifact_type', 'Unknown')}</td>
                                <td>{dep.get('package_name', 'Unknown')}</td>
                                <td class="text-center">{dep.get('design_version', 'N/A')}</td>
                                <td class="text-center">{dep.get('runtime_version') or 'N/A'}</td>
                                <td class="text-center"><span class="status-badge {status_class}">{status}</span></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _generate_tab_systems_adapters(self, data: Dict[str, Any]) -> str:
        """Generate systems and adapters tab"""
        systems_data = data.get('systems', {})
        systems = systems_data.get('systems', [])
        adapters = systems_data.get('adapters', [])
        stats = systems_data.get('stats', {})
        
        # Prepare adapter data for stacked bar (top 8)
        adapter_colors = ['#0A6ED1', '#2E844A', '#F0AB00', '#6A6D70', '#E52929', '#00A8E1', '#FF9500', '#8B8B8B']
        adapter_data = []
        for i, adapter in enumerate(adapters[:8]):
            adapter_data.append({
                'type': adapter.get('adapter_type', 'Unknown'),
                'count': adapter.get('total_count', 0),
                'color': adapter_colors[i] if i < len(adapter_colors) else '#8B8B8B'
            })
        adapter_bar = self._generate_stacked_bar(adapter_data, "🔌 Top Adapter Types Distribution")
        
        html = f"""            <div class="tab-pane fade" id="systems" role="tabpanel">
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
                
                {adapter_bar}
                
                <div class="content-card">
                    <h3>🌐 Connected Systems</h3>
                    <table class="table table-sm table-hover dataTable" id="systemsTable">
                        <thead>
                            <tr>
                                <th>System</th>
                                <th>Adapter Type</th>
                                <th>Direction</th>
                                <th class="text-center">Usage Count</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for sys in systems[:50]:  # Limit to top 50 for performance
            html += f"""
                            <tr>
                                <td>{sys.get('system_name', 'Unknown')}</td>
                                <td>{sys.get('adapter_type', 'Unknown')}</td>
                                <td>{sys.get('direction', 'Unknown')}</td>
                                <td class="text-center">{sys.get('usage_count', 0)}</td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="content-card mt-4">
                    <h3>🔌 Adapter Types Summary</h3>
                    <table class="table table-sm table-hover dataTable" id="adaptersTable">
                        <thead>
                            <tr>
                                <th>Adapter Type</th>
                                <th class="text-center">Sender</th>
                                <th class="text-center">Receiver</th>
                                <th class="text-center">Total</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for adapter in adapters:
            html += f"""
                            <tr>
                                <td>{adapter.get('adapter_type', 'Unknown')}</td>
                                <td class="text-center">{adapter.get('sender_count', 0)}</td>
                                <td class="text-center">{adapter.get('receiver_count', 0)}</td>
                                <td class="text-center"><strong>{adapter.get('total_count', 0)}</strong></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _generate_footer(self, data: Dict[str, Any]) -> str:
        """Generate report footer"""
        metadata = data.get('metadata', {})
        generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""        <div class="report-footer">
            <p>SAP Cloud Integration Analyzer Tool</p>
            <p>Generated on {generated_time}</p>
        </div>"""
    
    def _generate_javascript(self, data: Dict[str, Any]) -> str:
        """Generate JavaScript for DataTables with column filters and export buttons"""
        return """    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    
    <!-- DataTables JS -->
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
    
    <!-- DataTables Buttons -->
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.bootstrap5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    
    <script>
        $(document).ready(function() {
            // Common CSV export button configuration
            var buttonConfig = [
                {
                    extend: 'csvHtml5',
                    text: '📄 Export CSV',
                    className: 'buttons-csv'
                }
            ];
            
            // Common DataTable configuration
            var commonConfig = {
                pageLength: 25,
                lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, 'All']],
                responsive: true,
                dom: '<"row"<"col-sm-12 col-md-6"B><"col-sm-12 col-md-6"f>><"row"<"col-sm-6"l><"col-sm-6">>rt<"row"<"col-sm-6"i><"col-sm-6"p>>',
                buttons: buttonConfig
            };
            
            // Initialize all tables with CSV export only (no column filters)
            $('#packagesTable').DataTable($.extend({}, commonConfig, {
                order: [[0, 'asc']]
            }));
            
            $('#versionCompTable').DataTable($.extend({}, commonConfig, {
                order: [[3, 'desc'], [0, 'asc']]
            }));
            
            $('#deploymentsTable').DataTable($.extend({}, commonConfig, {
                order: [[4, 'desc'], [0, 'asc']]
            }));
            
            $('#systemsTable').DataTable($.extend({}, commonConfig, {
                order: [[3, 'desc']]
            }));
            
            $('#adaptersTable').DataTable($.extend({}, commonConfig, {
                order: [[3, 'desc']]
            }));
        });
    </script>"""
