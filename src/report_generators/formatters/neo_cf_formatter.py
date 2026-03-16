"""
NEO to CF Migration Assessment Report Formatter
SAP BTP themed HTML report generator with compact design
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json


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
{self._generate_tab_version_comparison(data)}
{self._generate_tab_package_analysis(data)}
{self._generate_tab_deployment_status(data)}
{self._generate_tab_systems_adapters(data)}
{self._generate_tab_environment_variables(data)}
{self._generate_tab_certificate_mappings(data)}
{self._generate_tab_keystore(data)}
{self._generate_tab_download_errors(data)}
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
            background-color: #2084cf;
            color: white;
            padding: 24px 32px;
            border-radius: 8px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(32, 132, 207, 0.2);
        }}
        
        .report-header h1 {{
            margin: 0;
            font-size: 26px;
            font-weight: 500;
        }}
        
        .report-meta {{
            font-size: 13px;
            opacity: 0.95;
            margin-top: 8px;
        }}
        
        /* KPI Cards */
        .kpi-card {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid var(--sap-border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            height: 100%;
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
            border-radius: 12px 12px 0 0;
            transition: all 0.3s ease;
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
        .status-expired {{ background-color: #FCEAEA; color: var(--sap-red); }}
        
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
            margin-top: 10px;
        }}
        
        .dataTables_wrapper .dataTables_paginate .page-link {{
            padding: 2px 8px;
            font-size: 12px;
            line-height: 1.5;
            color: var(--sap-text-dark);
            background-color: white;
            border-color: var(--sap-border);
        }}
        
        .dataTables_wrapper .dataTables_paginate .page-link:hover {{
            background-color: var(--sap-light-blue);
            border-color: var(--sap-blue);
            color: var(--sap-blue);
        }}
        
        .dataTables_wrapper .dataTables_paginate .page-item.active .page-link {{
            background-color: var(--sap-blue);
            border-color: var(--sap-blue);
            color: white;
        }}
        
        .dataTables_wrapper .dataTables_paginate .page-item.disabled .page-link {{
            color: #b0b3b5;
            background-color: white;
            border-color: var(--sap-border);
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
        
        tr.iflow-btn-row-active > td {{
            background-color: #BDE0FA !important;
            box-shadow: inset 0 2px 0 0 #0A6ED1, inset 0 -2px 0 0 #0A6ED1;
        }}
        
        /* Connected Systems table – address column wraps long URLs */
        #systemsTable td:nth-child(2) {{
            word-break: break-word;
            overflow-wrap: anywhere;
            max-width: 320px;
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
        subaccount_type = metadata.get('subaccount_type', 'CF')
        subaccount_label = 'Cloud Foundry' if subaccount_type == 'CF' else 'NEO'

        return f"""        <div class="report-header">
            <h1>📊 {self.report_title}</h1>
            <div class="report-meta">
                <strong>Tenant Name:</strong> {self.tenant_id} &nbsp;|&nbsp;
                <strong>Subaccount Type:</strong> {subaccount_label} &nbsp;|&nbsp;
                <strong>Extraction Date:</strong> {captured_date}
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
                <button class="nav-link" id="versions-tab" data-bs-toggle="tab"
                        data-bs-target="#versions" type="button" role="tab">
                    📋 Standard Content Analysis
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="packages-tab" data-bs-toggle="tab"
                        data-bs-target="#packages" type="button" role="tab">
                    📦 Package Analysis
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="deployment-tab" data-bs-toggle="tab"
                        data-bs-target="#deployment" type="button" role="tab">
                    📊 Artifact Analysis
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="systems-tab" data-bs-toggle="tab" 
                        data-bs-target="#systems" type="button" role="tab">
                    🌐 Systems & Adapters
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="envvars-tab" data-bs-toggle="tab" 
                        data-bs-target="#envvars" type="button" role="tab">
                    🔧 Environment Variables
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="certmappings-tab" data-bs-toggle="tab" 
                        data-bs-target="#certmappings" type="button" role="tab">
                    🔐 Certificate-User Mappings
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="keystore-tab" data-bs-toggle="tab"
                        data-bs-target="#keystore" type="button" role="tab">
                    🔑 Keystore
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="downloaderrors-tab" data-bs-toggle="tab"
                        data-bs-target="#downloaderrors" type="button" role="tab">
                    ⚠️ Download Errors
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
                label = f"{percentage:.0f}%"
                # For narrow segments, let the label overflow visibly
                overflow_style = "overflow:visible;white-space:nowrap;" if percentage < 8 else ""
                segments_html += f"""
                    <div class="bar-segment" style="flex: {percentage}; background-color: {item['color']};{overflow_style}"
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
        
        # Calculate totals for column headers and KPI cards
        total_iflows = sum(pkg.get('iflow_count', 0) for pkg in packages)
        total_scripts = sum(pkg.get('script_count', 0) for pkg in packages)
        total_msg_maps = sum(pkg.get('msg_map_count', 0) for pkg in packages)
        total_val_maps = sum(pkg.get('val_map_count', 0) for pkg in packages)
        total_artifacts = stats.get('total_artifacts', 0)
        
        # Package type counts
        count_editable   = sum(1 for p in packages if p.get('package_type') == 'Standard (Editable)')
        count_readonly   = sum(1 for p in packages if p.get('package_type') == 'Standard (Configure-Only)')
        count_custom     = sum(1 for p in packages if p.get('package_type') == 'Custom')

        # Readiness counts for percentage bar
        pkg_green  = sum(1 for p in packages if p.get('migration_readiness') == 'Green')
        pkg_amber  = sum(1 for p in packages if p.get('migration_readiness') == 'Amber')
        pkg_red    = sum(1 for p in packages if p.get('migration_readiness') == 'Red')

        readiness_bar_data = [
            {'type': 'Ready',         'count': pkg_green, 'color': '#2E844A'},
            {'type': 'Needs Check',   'count': pkg_amber, 'color': '#F0AB00'},
            {'type': 'Action Needed', 'count': pkg_red,   'color': '#E52929'},
        ]
        readiness_bar = self._generate_stacked_bar(readiness_bar_data, "📊 Package Migration Readiness Distribution")

        html = f"""            <div class="tab-pane fade" id="packages" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{stats.get('total_packages', 0)}</div>
                            <div class="kpi-label">Total Packages</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid #5E696E;">
                            <div class="kpi-number" style="color:#5E696E;">{count_editable}</div>
                            <div class="kpi-label">Standard (Editable)</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid var(--sap-green);">
                            <div class="kpi-number" style="color:var(--sap-green);">{count_readonly}</div>
                            <div class="kpi-label">Standard (Configure-Only)</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid var(--sap-blue);">
                            <div class="kpi-number" style="color:var(--sap-blue);">{count_custom}</div>
                            <div class="kpi-label">Custom</div>
                        </div>
                    </div>
                </div>

                {readiness_bar}

                <div class="content-card">
                    <h3>📦 Package Details</h3>
                    <div style="display:flex;gap:14px;align-items:center;margin-bottom:10px;font-size:12px;color:#5E696E;">
                        <span style="font-weight:600;">Migration Readiness:</span>
                        <span>🟢 Ready</span>
                        <span>🟡 Needs Check</span>
                        <span>🔴 Action Needed</span>
                        <span style="font-style:italic;">(click indicator for details)</span>
                    </div>
                    <table class="table table-sm table-hover dataTable" id="packagesTable">
                        <thead>
                            <tr>
                                <th style="width:30%">Package Name</th>
                                <th style="width:14%">Package Type</th>
                                <th style="width:10%" class="text-center">Readiness</th>
                                <th style="width:8%" class="text-center">IFlows ({total_iflows})</th>
                                <th style="width:8%" class="text-center">Scripts ({total_scripts})</th>
                                <th style="width:8%" class="text-center">Msg Maps ({total_msg_maps})</th>
                                <th style="width:8%" class="text-center">Val Maps ({total_val_maps})</th>
                                <th style="width:6%" class="text-center">Total ({total_artifacts})</th>
                            </tr>
                        </thead>
                        <tbody>"""

        _pkg_styles = {
            'Custom':                    ('#EDF5FA', '#0A6ED1'),
            'Standard (Editable)':       ('#F5F5F5', '#5E696E'),
            'Standard (Configure-Only)': ('#E6F4EA', '#2E844A'),
        }
        _readiness_icon = {'Green': ('🟢', 3), 'Amber': ('🟡', 2), 'Red': ('🔴', 1)}
        for pkg in packages:
            pkg_type = pkg.get('package_type', 'Custom')
            pt_bg, pt_color = _pkg_styles.get(pkg_type, ('#F5F5F5', '#6A6D70'))

            readiness = pkg.get('migration_readiness', 'Green')
            r_icon, r_sort = _readiness_icon.get(readiness, ('⚪', 0))
            checks_json = json.dumps(pkg.get('readiness_checks', []), ensure_ascii=False).replace('"', '&quot;')
            pkg_name = pkg.get('package_name', '')
            pkg_name_escaped = pkg_name.replace('"', '&quot;')

            html += f"""
                            <tr>
                                <td>{pkg_name}</td>
                                <td><span style="display:inline-block;padding:2px 7px;border-radius:3px;font-size:11px;font-weight:600;background:{pt_bg};color:{pt_color};">{pkg_type}</span></td>
                                <td class="text-center" data-order="{r_sort}"><a href="#" class="readiness-badge" data-name="{pkg_name_escaped}" data-checks="{checks_json}" style="text-decoration:none;font-size:16px;cursor:pointer;">{r_icon}</a></td>
                                <td class="text-center">{pkg.get('iflow_count', 0)}</td>
                                <td class="text-center">{pkg.get('script_count', 0)}</td>
                                <td class="text-center">{pkg.get('msg_map_count', 0)}</td>
                                <td class="text-center">{pkg.get('val_map_count', 0)}</td>
                                <td class="text-center"><strong>{pkg.get('total_artifacts', 0)}</strong></td>
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
        """Generate artifact analysis tab (formerly deployment status)"""
        versions = data.get('versions', {})
        deployments = versions.get('artifact_deployments', [])
        stats = versions.get('deployment_stats', {})

        # Artifact type counts
        count_iflows  = sum(1 for d in deployments if d.get('artifact_type') == 'Integration Flow')
        count_scripts = sum(1 for d in deployments if d.get('artifact_type') == 'Script Collection')
        count_mm      = sum(1 for d in deployments if d.get('artifact_type') == 'Message Mapping')
        count_vm      = sum(1 for d in deployments if d.get('artifact_type') == 'Value Mapping')
        total_artifacts = len(deployments)

        # Readiness counts for stacked bar
        r_green = stats.get('readiness_green', 0)
        r_amber = stats.get('readiness_amber', 0)
        r_red   = stats.get('readiness_red', 0)
        readiness_bar_data = [
            {'type': 'Ready',         'count': r_green, 'color': '#2E844A'},
            {'type': 'Needs Check',   'count': r_amber, 'color': '#F0AB00'},
            {'type': 'Action Needed', 'count': r_red,   'color': '#E52929'},
        ]
        readiness_bar = self._generate_stacked_bar(readiness_bar_data, "📊 Migration Readiness Distribution")

        html = f"""            <div class="tab-pane fade" id="deployment" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{total_artifacts}</div>
                            <div class="kpi-label">Total Artifacts</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-blue);">
                            <div class="kpi-number" style="color: var(--sap-blue);">{count_iflows}</div>
                            <div class="kpi-label">Integration Flows</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-green);">
                            <div class="kpi-number" style="color: var(--sap-green);">{count_scripts}</div>
                            <div class="kpi-label">Script Collections</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-orange);">
                            <div class="kpi-number" style="color: var(--sap-orange);">{count_mm}</div>
                            <div class="kpi-label">Message Mappings</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left: 3px solid #5E696E;">
                            <div class="kpi-number" style="color: #5E696E;">{count_vm}</div>
                            <div class="kpi-label">Value Mappings</div>
                        </div>
                    </div>
                </div>

                {readiness_bar}

                <div class="content-card">
                    <h3>📋 Artifact Details</h3>
                    <div style="display:flex;gap:14px;align-items:center;margin-bottom:10px;font-size:12px;color:#5E696E;">
                        <span style="font-weight:600;">Migration Readiness:</span>
                        <span>🟢 Ready</span>
                        <span>🟡 Needs Check</span>
                        <span>🔴 Action Needed</span>
                        <span style="font-style:italic;">(click indicator for details)</span>
                    </div>
                    <table class="table table-sm table-hover dataTable" id="deploymentsTable">
                        <thead>
                            <tr>
                                <th style="width:28%">Artifact Name</th>
                                <th style="width:14%">Artifact Type</th>
                                <th style="width:26%">Package Name</th>
                                <th style="width:8%" class="text-center">Readiness</th>
                                <th style="width:12%" class="text-center">Design Version</th>
                                <th style="width:12%" class="text-center">Deployed Version</th>
                            </tr>
                        </thead>
                        <tbody>"""

        _readiness_icon = {'Green': ('🟢', 3), 'Amber': ('🟡', 2), 'Red': ('🔴', 1)}
        for dep in deployments:
            readiness = dep.get('migration_readiness', 'Green')
            r_icon, r_sort = _readiness_icon.get(readiness, ('⚪', 0))
            checks_json = json.dumps(dep.get('readiness_checks', []), ensure_ascii=False).replace('"', '&quot;')
            art_name = dep.get('artifact_name', 'Unknown')
            art_name_escaped = art_name.replace('"', '&quot;')

            html += f"""
                            <tr>
                                <td>{art_name}</td>
                                <td>{dep.get('artifact_type', 'Unknown')}</td>
                                <td>{dep.get('package_name', 'Unknown')}</td>
                                <td class="text-center" data-order="{r_sort}"><a href="#" class="readiness-badge" data-name="{art_name_escaped}" data-checks="{checks_json}" style="text-decoration:none;font-size:16px;cursor:pointer;">{r_icon}</a></td>
                                <td class="text-center">{dep.get('design_version', 'N/A')}</td>
                                <td class="text-center">{dep.get('runtime_version') or 'Not Deployed'}</td>
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

        # Adapter column totals
        total_sender   = sum(a.get('sender_count', 0) for a in adapters)
        total_receiver = sum(a.get('receiver_count', 0) for a in adapters)
        total_all      = sum(a.get('total_count', 0) for a in adapters)
        
        # Prepare adapter data for stacked bar (top 10)
        adapter_colors = ['#0A6ED1', '#2E844A', '#F0AB00', '#6A6D70', '#E52929', '#00A8E1', '#FF9500', '#8B8B8B', '#7B61FF', '#00B4D8']
        adapter_data = []
        for i, adapter in enumerate(adapters[:10]):
            adapter_data.append({
                'type': adapter.get('adapter_type', 'Unknown'),
                'count': adapter.get('total_count', 0),
                'color': adapter_colors[i] if i < len(adapter_colors) else '#8B8B8B'
            })
        adapter_bar = self._generate_stacked_bar(adapter_data, "🔌 Top 10 Adapter Types Distribution")
        
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
                    <div style="font-size:12px;color:#5E696E;margin-bottom:10px;font-style:italic;">Click the numbered badges to see which IFlows use each system.</div>
                    <table class="table table-sm table-hover dataTable" id="systemsTable">
                        <thead>
                            <tr>
                                <th style="width:18%">System Name</th>
                                <th style="width:38%">Address/URL</th>
                                <th style="width:16%" title="ProcessDirect adapters (used for internal IFlow routing) are excluded from this list">Adapter Type ℹ️</th>
                                <th style="width:13%">Direction</th>
                                <th style="width:9%" class="text-center">Used in # IFlows</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for sys in systems:
            iflow_count = sys.get('iflow_count', 0)
            iflow_names = sys.get('iflow_names', '') or ''
            system_name = sys.get('system_name', 'Unknown')
            # Escape single/double quotes in iflow names for safe HTML attribute usage
            address_url = sys.get('address_url', 'N/A')
            iflow_names_escaped = iflow_names.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
            system_name_escaped = system_name.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
            address_url_escaped = address_url.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
            
            if iflow_count > 0 and iflow_names:
                count_cell = f'<a href="#" class="badge bg-primary text-white iflow-usage-btn" data-iflows="{iflow_names_escaped}" data-system="{system_name_escaped}" data-address="{address_url_escaped}" style="text-decoration:none; cursor:pointer;">{iflow_count}</a>'
            else:
                count_cell = str(iflow_count)
            
            html += f"""
                            <tr>
                                <td>{system_name}</td>
                                <td>{sys.get('address_url', 'N/A')}</td>
                                <td>{sys.get('adapter_type', 'Unknown')}</td>
                                <td>{sys.get('direction', 'Unknown')}</td>
                                <td class="text-center">{count_cell}</td>
                            </tr>"""
        
        html += f"""
                        </tbody>
                    </table>
                </div>

                <div class="content-card mt-4">
                    <h3>🔌 Adapter Types Summary</h3>
                    <div style="font-size:12px;color:#5E696E;margin-bottom:10px;font-style:italic;">Click the Sender or Receiver counts to see which IFlows use each adapter.</div>
                    <table class="table table-sm table-hover dataTable" id="adaptersTable">
                        <thead>
                            <tr>
                                <th>Adapter Type</th>
                                <th class="text-center">Sender ({total_sender})</th>
                                <th class="text-center">Receiver ({total_receiver})</th>
                                <th class="text-center">Total ({total_all})</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for adapter in adapters:
            at = adapter.get('adapter_type', 'Unknown')
            at_escaped = at.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
            sender_count = adapter.get('sender_count', 0)
            receiver_count = adapter.get('receiver_count', 0)
            sender_iflows = (adapter.get('sender_iflows') or '').replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')
            receiver_iflows = (adapter.get('receiver_iflows') or '').replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;')

            if sender_count > 0 and sender_iflows:
                sender_cell = f'<a href="#" class="badge bg-primary text-white iflow-usage-btn" data-iflows="{sender_iflows}" data-system="{at_escaped}" data-address="Sender" style="text-decoration:none;cursor:pointer;">{sender_count}</a>'
            else:
                sender_cell = str(sender_count)

            if receiver_count > 0 and receiver_iflows:
                receiver_cell = f'<a href="#" class="badge bg-primary text-white iflow-usage-btn" data-iflows="{receiver_iflows}" data-system="{at_escaped}" data-address="Receiver" style="text-decoration:none;cursor:pointer;">{receiver_count}</a>'
            else:
                receiver_cell = str(receiver_count)

            html += f"""
                            <tr>
                                <td>{at}</td>
                                <td class="text-center">{sender_cell}</td>
                                <td class="text-center">{receiver_cell}</td>
                                <td class="text-center"><strong>{adapter.get('total_count', 0)}</strong></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- IFlow Usage Modal -->
            <div class="modal fade" id="iflowUsageModal" tabindex="-1" aria-labelledby="iflowUsageModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header" style="background-color: #EDF5FA; border-bottom: 1px solid #E5E5E5;">
                            <h5 class="modal-title" id="iflowUsageModalLabel" style="color: #0854A0;">
                                \U0001f517 IFlows using: <span id="modalSystemName" style="font-weight:700;"></span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="modalIFlowList"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Readiness Detail Modal -->
            <div class="modal fade" id="readinessModal" tabindex="-1" aria-labelledby="readinessModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header" style="background-color: #EDF5FA; border-bottom: 1px solid #E5E5E5;">
                            <h5 class="modal-title" id="readinessModalLabel" style="color: #0854A0;">Migration Readiness</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="readinessModalBody"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>"""
        
        return html
    
    def _generate_tab_environment_variables(self, data: Dict[str, Any]) -> str:
        """Generate environment variables tab"""
        env_vars_data = data.get('environment_variables', {})
        
        if not env_vars_data.get('available', False):
            return """            <div class="tab-pane fade" id="envvars" role="tabpanel">
                <div class="alert-box alert-info">
                    <strong>Note:</strong> Environment variable data is not available. This feature requires PARSE_IFLW_CONTENT=true and EXTRACT_IFLOW_CONTENT=true in configuration.
                </div>
            </div>"""
        
        variables = env_vars_data.get('variables', [])
        stats = env_vars_data.get('stats', {})
        by_file_type = stats.get('by_file_type', {})
        by_parent_type = stats.get('by_parent_type', {})
        
        # Calculate unique variables count from the data
        unique_vars = set()
        for var in variables:
            var_list = var.get('variables', '').split('|')
            unique_vars.update([v.strip() for v in var_list if v.strip()])
        
        unique_vars_count = len(unique_vars)
        
        html = f"""            <div class="tab-pane fade" id="envvars" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid var(--sap-blue);">
                            <div class="kpi-number" style="color:var(--sap-blue);">{unique_vars_count}</div>
                            <div class="kpi-label">Unique HC_ Variables</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{stats.get('total_files', 0)}</div>
                            <div class="kpi-label">Total Files</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid #2E844A;">
                            <div class="kpi-number" style="color:#2E844A;">{by_file_type.get('groovyScript', 0)}</div>
                            <div class="kpi-label">Groovy Script</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid #8B4513;">
                            <div class="kpi-number" style="color:#8B4513;">{by_file_type.get('javascript', 0)}</div>
                            <div class="kpi-label">JavaScript</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card" style="border-left:3px solid #0854A0;">
                            <div class="kpi-number" style="color:#0854A0;">{by_file_type.get('xslt', 0)}</div>
                            <div class="kpi-label">XSLT</div>
                        </div>
                    </div>
                </div>
                
                <div class="content-card">
                    <h3>🔧 Environment Variables Usage</h3>
                    <table class="table table-sm table-hover dataTable" id="envVarsTable">
                        <thead>
                            <tr>
                                <th style="width:14%">File Name</th>
                                <th style="width:9%">File Type</th>
                                <th style="width:6%" class="text-center"># Variables</th>
                                <th style="width:16%">Variable Names</th>
                                <th style="width:9%">Artifact Type</th>
                                <th style="width:25%">Artifact Name</th>
                                <th style="width:21%">Package Name</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        # File type display mapping: db value → (label, bg colour, text colour)
        _ft_styles = {
            'groovyScript': ('GROOVY SCRIPT', '#E6F4EA', '#2E844A'),
            'javascript':   ('JAVASCRIPT',    '#FFF4E5', '#8B4513'),
            'xslt':         ('XSLT',          '#EDF5FA', '#0854A0'),
        }
        
        for var in variables:
            # Format variable list (pipe-separated to comma-separated)
            var_list = var.get('variables', '').replace('|', ', ')
            
            raw_ft  = var.get('file_type', '')
            ft_label, ft_bg, ft_color = _ft_styles.get(raw_ft, (raw_ft.upper() if raw_ft else 'UNKNOWN', '#F5F5F5', '#6A6D70'))
            ft_badge = f'<span style="display:inline-block;padding:2px 7px;border-radius:3px;font-size:11px;font-weight:600;background:{ft_bg};color:{ft_color};">{ft_label}</span>'

            _parent_type_labels = {'Iflow': 'Integration Flow', 'IFlow': 'Integration Flow',
                                   'ScriptCollection': 'Script Collection',
                                   'PartnerDirectory': 'Partner Directory'}
            raw_pt = var.get('parent_type', '')
            parent_type_display = _parent_type_labels.get(raw_pt, raw_pt)
            
            html += f"""
                            <tr>
                                <td><code>{var.get('file_name', 'Unknown')}</code></td>
                                <td>{ft_badge}</td>
                                <td class="text-center"><strong>{var.get('var_count', 0)}</strong></td>
                                <td><code>{var_list}</code></td>
                                <td>{parent_type_display}</td>
                                <td>{var.get('parent_name', 'Unknown')}</td>
                                <td>{var.get('package_name', 'Unknown')}</td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _generate_tab_certificate_mappings(self, data: Dict[str, Any]) -> str:
        """Generate certificate-to-user mappings tab (NEO only)"""
        cert_data = data.get('certificate_mappings', {})
        
        if not cert_data.get('available', False):
            if cert_data.get('skipped_cf'):
                msg = "Certificate-to-user mappings are not applicable to Cloud Foundry (CF) subaccounts. This feature is only available for NEO subaccounts, where certificate-based user authentication requires explicit mapping configuration."
            else:
                msg = "Certificate-to-user mapping data is not available. This may indicate a CF subaccount (where this feature does not exist) or that the data was not downloaded."
            return f"""            <div class="tab-pane fade" id="certmappings" role="tabpanel">
                <div class="alert-box alert-info">
                    <strong>Note:</strong> {msg}
                </div>
            </div>"""
        
        mappings = cert_data.get('mappings', [])
        stats = cert_data.get('stats', {})
        
        html = f"""            <div class="tab-pane fade" id="certmappings" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="kpi-card">
                            <div class="kpi-number">{stats.get('total_mappings', 0)}</div>
                            <div class="kpi-label">Total Mappings</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-green);">
                            <div class="kpi-number" style="color: var(--sap-green);">{stats.get('active', 0)}</div>
                            <div class="kpi-label">✅ Active</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-orange);">
                            <div class="kpi-number" style="color: var(--sap-orange);">{stats.get('expiring_soon', 0)}</div>
                            <div class="kpi-label">⚠️ Expiring Soon</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-red);">
                            <div class="kpi-number" style="color: var(--sap-red);">{stats.get('expired', 0)}</div>
                            <div class="kpi-label">🔴 Expired</div>
                        </div>
                    </div>
                </div>
                
                <div class="content-card">
                    <h3>🔐 Certificate-to-User Mappings</h3>
                    <table class="table table-sm table-hover dataTable" id="certMappingsTable">
                        <thead>
                            <tr>
                                <th>Certificate Subject</th>
                                <th>Issued By</th>
                                <th>Mapped User</th>
                                <th class="text-center">Valid From</th>
                                <th class="text-center">Valid Until</th>
                                <th class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for mapping in mappings:
            status = mapping.get('status', 'Unknown')
            if status == 'Active':
                status_class = 'status-inSync'
            elif status == 'Expiring Soon':
                status_class = 'status-outofSync'
            elif status == 'Expired':
                status_class = 'status-expired'
            else:
                status_class = 'status-notDeployed'
            
            # Extract CN from Subject and Issuer
            subject_cn = self._extract_cn_for_display(mapping.get('IssuedTo', ''))
            issuer_cn = self._extract_cn_for_display(mapping.get('IssuedBy', ''))
            
            valid_from = mapping.get('ValidFrom', 'N/A')[:10] if mapping.get('ValidFrom') else 'N/A'
            valid_to = mapping.get('ValidTo', 'N/A')[:10] if mapping.get('ValidTo') else 'N/A'
            
            html += f"""
                            <tr>
                                <td title="{mapping.get('IssuedTo', '')}">{subject_cn}</td>
                                <td title="{mapping.get('IssuedBy', '')}">{issuer_cn}</td>
                                <td>{mapping.get('User', 'Unknown')}</td>
                                <td class="text-center">{valid_from}</td>
                                <td class="text-center">{valid_to}</td>
                                <td class="text-center"><span class="status-badge {status_class}">{status}</span></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _generate_tab_keystore(self, data: Dict[str, Any]) -> str:
        """Generate keystore view tab"""
        keystore_data = data.get('keystore', {})
        entries = keystore_data.get('entries', [])
        stats = keystore_data.get('stats', {})
        by_type = stats.get('by_type', {})
        by_key_type = stats.get('by_key_type', {})
        
        html = f"""            <div class="tab-pane fade" id="keystore" role="tabpanel">
                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <div class="kpi-card">
                            <div class="kpi-number">{stats.get('total_entries', 0)}</div>
                            <div class="kpi-label">Total Entries</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-green);">
                            <div class="kpi-number" style="color: var(--sap-green);">{stats.get('active', 0)}</div>
                            <div class="kpi-label">✅ Active</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-orange);">
                            <div class="kpi-number" style="color: var(--sap-orange);">{stats.get('expiring_soon', 0)}</div>
                            <div class="kpi-label">⚠️ Expiring Soon</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="kpi-card" style="border-left: 3px solid var(--sap-red);">
                            <div class="kpi-number" style="color: var(--sap-red);">{stats.get('expired', 0)}</div>
                            <div class="kpi-label">🔴 Expired</div>
                        </div>
                    </div>
                </div>
                
                <div class="content-card">
                    <h3>🔑 Keystore Entries</h3>
                    <table class="table table-sm table-hover dataTable" id="keystoreTable">
                        <thead>
                            <tr>
                                <th>Alias</th>
                                <th>Type</th>
                                <th>Subject</th>
                                <th>Issuer</th>
                                <th class="text-center">Valid From</th>
                                <th class="text-center">Valid Until</th>
                                <th class="text-center">Key Type</th>
                                <th class="text-center">Key Size</th>
                                <th class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for entry in entries:
            status = entry.get('status', 'Unknown')
            if status == 'Active':
                status_class = 'status-inSync'
            elif status == 'Expiring Soon':
                status_class = 'status-outofSync'
            elif status == 'Expired':
                status_class = 'status-expired'
            else:
                status_class = 'status-notDeployed'
            
            subject_cn = entry.get('subject_cn', 'Unknown')
            issuer_cn = entry.get('issuer_cn', 'Unknown')
            
            html += f"""
                            <tr>
                                <td>{entry.get('Alias', 'Unknown')}</td>
                                <td>{entry.get('Type', 'Unknown')}</td>
                                <td title="{entry.get('SubjectDN', '')}">{subject_cn}</td>
                                <td title="{entry.get('IssuerDN', '')}">{issuer_cn}</td>
                                <td class="text-center">{entry.get('valid_from_formatted', 'N/A')}</td>
                                <td class="text-center">{entry.get('valid_until_formatted', 'N/A')}</td>
                                <td class="text-center">{entry.get('KeyType', 'N/A')}</td>
                                <td class="text-center">{entry.get('KeySize', 'N/A')}</td>
                                <td class="text-center"><span class="status-badge {status_class}">{status}</span></td>
                            </tr>"""
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>"""
        
        return html
    
    def _extract_cn_for_display(self, dn: str) -> str:
        """Extract CN from Distinguished Name for display"""
        if not dn:
            return 'Unknown'
        
        # Look for CN= in the DN string
        parts = dn.split(',')
        for part in parts:
            part = part.strip()
            if part.startswith('CN='):
                return part[3:]  # Remove 'CN=' prefix
        
        # If no CN found, return first 50 chars
        return dn[:50] + '...' if len(dn) > 50 else dn

    def _generate_tab_download_errors(self, data: Dict[str, Any]) -> str:
        """Generate download errors tab"""
        err_data = data.get('download_errors', {})

        if not err_data.get('available', False):
            return """            <div class="tab-pane fade" id="downloaderrors" role="tabpanel">
                <div class="alert-box alert-info">
                    <strong>Note:</strong> No download error data is available for this run.
                </div>
            </div>"""

        errors = err_data.get('errors', [])
        stats = err_data.get('stats', {})

        if not errors:
            return """            <div class="tab-pane fade" id="downloaderrors" role="tabpanel">
                <div class="alert-box" style="background-color:#E6F4EA;border-left:4px solid #2E844A;padding:16px;border-radius:4px;">
                    <strong style="color:#2E844A;">All downloads completed successfully.</strong> No errors were encountered during data extraction.
                </div>
            </div>"""

        total = stats.get('total_errors', 0)
        by_type = stats.get('by_artifact_type', {})
        by_error = stats.get('by_error_type', {})

        html = f"""            <div class="tab-pane fade" id="downloaderrors" role="tabpanel">
                <div class="content-card">
                    <h3>⚠️ Download Errors ({total})</h3>
                    <table class="table table-sm table-hover dataTable" id="downloadErrorsTable">
                        <thead>
                            <tr>
                                <th style="width:22%">Package / Artifact</th>
                                <th style="width:14%">Type</th>
                                <th style="width:8%" class="text-center">Error Code</th>
                                <th style="width:14%">Error Type</th>
                                <th style="width:32%">Error Message</th>
                                <th style="width:10%">Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>"""

        _error_colors = {
            '403': ('#FFF4E5', '#8B4513'),
            '401': ('#F8D7DA', '#721C24'),
            '404': ('#F8D7DA', '#721C24'),
            '500': ('#F8D7DA', '#721C24'),
        }
        for err in errors:
            code = str(err.get('error_code', ''))
            ec_bg, ec_color = _error_colors.get(code, ('#F5F5F5', '#6A6D70'))
            ts = err.get('timestamp', '')
            if 'T' in ts:
                ts = ts.split('T')[0] + ' ' + ts.split('T')[1][:8]

            html += f"""
                            <tr>
                                <td>{err.get('package_id', 'Unknown')}</td>
                                <td>{err.get('artifact_type', '').replace('_', ' ').title()}</td>
                                <td class="text-center"><span style="display:inline-block;padding:2px 7px;border-radius:3px;font-size:11px;font-weight:600;background:{ec_bg};color:{ec_color};">{code}</span></td>
                                <td>{err.get('error_type', '').replace('_', ' ').title()}</td>
                                <td style="font-size:12px;">{err.get('error_message', '')}</td>
                                <td style="font-size:11px;color:#5E696E;">{ts}</td>
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
        # Sanitise tenant_id for safe embedding in a JS double-quoted string
        tenant_safe = self.tenant_id.replace('\\', '\\\\').replace('"', '\\"')
        
        js = """    <!-- Bootstrap JS -->
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
        var _tenantId = "__TENANT_ID__";
        var _extractionDate = "__EXTRACTION_DATE__";

        $(document).ready(function() {
            // Returns a CSV button config with a per-table filename
            function makeBtn(tableName) {
                return [{
                    extend: 'csvHtml5',
                    text: '\U0001F4C4 Export CSV',
                    className: 'buttons-csv',
                    filename: _tenantId + '_' + _extractionDate + '_' + tableName
                }];
            }
            
            // Common DataTable configuration (buttons set per-table via makeBtn)
            var commonConfig = {
                pageLength: 25,
                lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, 'All']],
                responsive: true,
                dom: '<"row"<"col-sm-12 col-md-6"B><"col-sm-12 col-md-6"f>><"row"<"col-sm-6"l><"col-sm-6">>rt<"row"<"col-sm-6"i><"col-sm-6"p>>'
            };
            
            $('#packagesTable').DataTable($.extend({}, commonConfig, {
                order: [[2, 'desc'], [0, 'asc']],
                autoWidth: false,
                columnDefs: [{ targets: [2], type: 'num' }],
                buttons: makeBtn('Packages')
            }));
            
            $('#versionCompTable').DataTable($.extend({}, commonConfig, {
                order: [[3, 'desc'], [0, 'asc']],
                buttons: makeBtn('Standard_Content')
            }));
            
            $('#deploymentsTable').DataTable($.extend({}, commonConfig, {
                order: [[3, 'asc'], [0, 'asc']],
                autoWidth: false,
                buttons: makeBtn('Artifact_Analysis')
            }));
            
            $('#systemsTable').DataTable($.extend({}, commonConfig, {
                order: [[4, 'desc']],
                autoWidth: false,
                buttons: makeBtn('Connected_Systems')
            }));
            
            $('#adaptersTable').DataTable($.extend({}, commonConfig, {
                order: [[3, 'desc']],
                buttons: makeBtn('Adapter_Types')
            }));
            
            $('#envVarsTable').DataTable($.extend({}, commonConfig, {
                order: [[2, 'desc'], [0, 'asc']],
                autoWidth: false,
                buttons: makeBtn('Environment_Variables')
            }));
            
            $('#certMappingsTable').DataTable($.extend({}, commonConfig, {
                order: [[5, 'desc'], [4, 'asc']],
                buttons: makeBtn('Certificate_Mappings')
            }));
            
            $('#keystoreTable').DataTable($.extend({}, commonConfig, {
                order: [[8, 'desc'], [5, 'asc']],
                buttons: makeBtn('Keystore')
            }));

            $('#downloadErrorsTable').DataTable($.extend({}, commonConfig, {
                order: [[5, 'desc']],
                buttons: makeBtn('Download_Errors')
            }));
            
            // IFlow usage drill-down click handler
            $(document).on('click', '.iflow-usage-btn', function(e) {
                e.preventDefault();
                // Highlight the clicked row; clear any previous highlight
                $('.iflow-btn-row-active').removeClass('iflow-btn-row-active');
                $(this).closest('tr').addClass('iflow-btn-row-active');
                var system  = $(this).data('system');
                var address = $(this).data('address') || '';
                var iflowsRaw = $(this).data('iflows');
                var entries = String(iflowsRaw).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
                // Modal title: system name + address URL (middle-dot separator)
                var titleText = system + (address && address !== 'N/A' ? ' \u00b7 ' + address : '');
                $('#modalSystemName').text(titleText);
                // Parse name|||package entries and render as a table
                // Column order: # | Package Name | IFlow Name
                var tableHtml = '<table class="table table-sm table-hover mb-0" style="table-layout:fixed;width:100%;">'
                    + '<thead><tr>'
                    + '<th style="width:32px">#</th>'
                    + '<th style="width:46%">Package Name</th>'
                    + '<th style="width:46%">IFlow Name</th>'
                    + '</tr></thead><tbody>';
                entries.forEach(function(entry, idx) {
                    var sep = entry.indexOf('|||');
                    var iflowName = sep >= 0 ? entry.substring(0, sep).trim() : entry.trim();
                    var pkgName   = sep >= 0 ? entry.substring(sep + 3).trim() : '';
                    tableHtml += '<tr>'
                        + '<td class="text-muted">' + (idx + 1) + '</td>'
                        + '<td style="word-break:break-word;overflow-wrap:anywhere;">' + $('<div>').text(pkgName).html() + '</td>'
                        + '<td style="word-break:break-word;overflow-wrap:anywhere;">' + $('<div>').text(iflowName).html() + '</td>'
                        + '</tr>';
                });
                tableHtml += '</tbody></table>';
                $('#modalIFlowList').html(tableHtml);
                var modal = new bootstrap.Modal(document.getElementById('iflowUsageModal'));
                modal.show();
            });
            
            // Remove row highlight when the modal is dismissed
            document.getElementById('iflowUsageModal').addEventListener('hidden.bs.modal', function() {
                $('.iflow-btn-row-active').removeClass('iflow-btn-row-active');
            });

            // Readiness badge click handler — opens modal with check details
            $(document).on('click', '.readiness-badge', function(e) {
                e.preventDefault();
                var name = $(this).data('name');
                var checksRaw = $(this).data('checks');
                var checks = (typeof checksRaw === 'string') ? JSON.parse(checksRaw) : checksRaw;
                var statusIcon = {Green: '🟢', Amber: '🟡', Red: '🔴'};
                var statusColor = {Green: '#2E844A', Amber: '#856404', Red: '#C9190B'};
                var html = '<table class="table table-sm mb-0"><tbody>';
                checks.forEach(function(c) {
                    var icon = statusIcon[c.status] || '⚪';
                    var color = statusColor[c.status] || '#6A6D70';
                    html += '<tr><td style="width:24px;vertical-align:top;">' + icon + '</td>'
                        + '<td><strong style="color:' + color + ';">' + $('<span>').text(c.check).html() + '</strong><br>'
                        + '<span style="font-size:12px;color:#5E696E;">' + $('<span>').text(c.detail).html() + '</span>';
                    if (c.files && c.files.length > 0) {
                        html += '<ul style="margin:4px 0 0;padding-left:18px;font-size:11px;color:#5E696E;">';
                        c.files.forEach(function(f) {
                            html += '<li>' + $('<span>').text(f).html() + '</li>';
                        });
                        html += '</ul>';
                    }
                    html += '</td></tr>';
                });
                html += '</tbody></table>';
                $('#readinessModalLabel').text('Migration Readiness — ' + name);
                $('#readinessModalBody').html(html);
                var modal = new bootstrap.Modal(document.getElementById('readinessModal'));
                modal.show();
            });
        });
    </script>"""
        
        # Extract date portion from captured_at for CSV filenames (YYYYMMDD_HHMMSS)
        extraction_date = self.captured_at[:10].replace('-', '') if self.captured_at else ''

        return js.replace('__TENANT_ID__', tenant_safe).replace('__EXTRACTION_DATE__', extraction_date)
