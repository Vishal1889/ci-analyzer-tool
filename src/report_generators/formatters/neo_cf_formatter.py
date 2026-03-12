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
{self._generate_tab_environment_variables(data)}
{self._generate_tab_certificate_mappings(data)}
{self._generate_tab_keystore(data)}
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
        
        return f"""        <div class="report-header">
            <h1>📊 {self.report_title}</h1>
            <div class="report-meta">
                <strong>Tenant:</strong> {self.tenant_id} &nbsp;|&nbsp;
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
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="envvars-tab" data-bs-toggle="tab" 
                        data-bs-target="#envvars" type="button" role="tab">
                    🔧 Environment Variables
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="certmappings-tab" data-bs-toggle="tab" 
                        data-bs-target="#certmappings" type="button" role="tab">
                    🔐 Certificate Mappings
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="keystore-tab" data-bs-toggle="tab" 
                        data-bs-target="#keystore" type="button" role="tab">
                    🔑 Keystore
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
        
        # MRS Section (only when pre-computed scores are available)
        mci_summary = kpis.get('mci_summary', {})
        if kpis.get('mci_available') and mci_summary:
            overall_mrs  = mci_summary.get('overall_mrs', 0)
            custom_mrs   = mci_summary.get('custom_mrs', 0)
            standard_mrs = mci_summary.get('standard_mrs', 0)
            tag_counts   = mci_summary.get('tag_counts', {})
            
            # Colour band for overall MRS (higher = better = greener)
            if overall_mrs >= 76:
                mrs_color, mrs_label = 'var(--sap-green)', '🟢 Ready'
            elif overall_mrs >= 51:
                mrs_color, mrs_label = '#F0AB00', '🟡 Mostly Ready'
            elif overall_mrs >= 26:
                mrs_color, mrs_label = '#E65100', '🟠 Needs Work'
            else:
                mrs_color, mrs_label = 'var(--sap-red)', '🔴 Not Ready'
            
            kpi_html += f"""
                <div class="content-card">
                    <h3>🎯 Migration Readiness Score (MRS)</h3>
                    <div class="row g-3 mb-3">
                        <div class="col-md-4">
                            <div class="kpi-card" style="border-left:4px solid {mrs_color};text-align:center;">
                                <div style="font-size:48px;font-weight:700;color:{mrs_color};line-height:1.1;">{overall_mrs}</div>
                                <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--sap-text-gray);margin-top:4px;">Overall Readiness Score <span style="font-weight:400;">(0–100)</span></div>
                                <div style="font-size:13px;font-weight:600;color:{mrs_color};margin-top:6px;">{mrs_label}</div>
                                <div style="font-size:11px;color:var(--sap-text-gray);margin-top:2px;">Higher score = more ready for migration</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="kpi-card" style="border-left:3px solid var(--sap-blue);">
                                <div class="kpi-number" style="color:var(--sap-blue);">{custom_mrs}</div>
                                <div class="kpi-label">Custom Packages Readiness</div>
                                <div style="font-size:11px;color:var(--sap-text-gray);margin-top:4px;">Avg readiness of custom packages</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="kpi-card" style="border-left:3px solid #5E696E;">
                                <div class="kpi-number" style="color:#5E696E;">{standard_mrs}</div>
                                <div class="kpi-label">Standard Packages Readiness</div>
                                <div style="font-size:11px;color:var(--sap-text-gray);margin-top:4px;">Avg readiness of standard packages</div>
                            </div>
                        </div>
                    </div>
                    <div class="row g-3">
                        <div class="col">
                            <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
                                <span style="font-size:12px;color:var(--sap-text-gray);font-weight:600;">Readiness Distribution:</span>
                                <span style="padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:#E6F4EA;color:#2E844A;">🟢 Ready (76–100): {tag_counts.get('Ready', 0)} pkgs</span>
                                <span style="padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:#FFF3CD;color:#856404;">🟡 Mostly Ready (51–75): {tag_counts.get('Mostly Ready', 0)} pkgs</span>
                                <span style="padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:#FFE0B2;color:#E65100;">🟠 Needs Work (26–50): {tag_counts.get('Needs Work', 0)} pkgs</span>
                                <span style="padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:#F8D7DA;color:#721C24;">🔴 Not Ready (0–25): {tag_counts.get('Not Ready', 0)} pkgs</span>
                            </div>
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
        
        # MRS stats derived from per-package data
        scored_pkgs   = [p for p in packages if p.get('readiness_score') is not None]
        mrs_available = len(scored_pkgs) > 0
        avg_mrs       = round(sum(p['readiness_score'] for p in scored_pkgs) / len(scored_pkgs)) if scored_pkgs else None
        
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
                    {'<div class="col"><div class="kpi-card" style="border-left:3px solid var(--sap-green);"><div class="kpi-number" style="color:var(--sap-green);">' + str(avg_mrs) + '</div><div class="kpi-label">Avg Readiness Score</div></div></div>' if mrs_available and avg_mrs is not None else ''}
                </div>
                
                <div class="content-card">
                    <h3>📦 Package Details</h3>
                    <table class="table table-sm table-hover dataTable" id="packagesTable">
                        <thead>
                            <tr>
                                <th style="width:33%">Package Name</th>
                                <th style="width:14%">Package Type</th>
                                <th style="width:11%" class="text-center">Readiness Score</th>
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
        _readiness_styles = {
            'Ready':        ('#E6F4EA', '#2E844A', '🟢'),
            'Mostly Ready': ('#FFF3CD', '#856404', '🟡'),
            'Needs Work':   ('#FFE0B2', '#E65100', '🟠'),
            'Not Ready':    ('#F8D7DA', '#721C24', '🔴'),
        }
        for pkg in packages:
            pkg_type = pkg.get('package_type', 'Custom')
            pt_bg, pt_color = _pkg_styles.get(pkg_type, ('#F5F5F5', '#6A6D70'))
            
            # Readiness Score cell
            tag   = pkg.get('readiness_tag')
            score = pkg.get('readiness_score')
            if tag and score is not None:
                rs_bg, rs_color, rs_icon = _readiness_styles.get(tag, ('#F5F5F5', '#6A6D70', ''))
                readiness_cell = (
                    f'<span style="display:inline-block;padding:2px 7px;border-radius:3px;'
                    f'font-size:11px;font-weight:600;background:{rs_bg};color:{rs_color};">'
                    f'{rs_icon} {tag}</span>'
                    f' <span style="font-size:11px;color:var(--sap-text-gray);">{int(score)}</span>'
                )
                sort_val = score
            else:
                readiness_cell = '<span style="color:var(--sap-text-gray);font-size:12px;">—</span>'
                sort_val = -1
            
            html += f"""
                            <tr>
                                <td>{pkg.get('package_name', '')}</td>
                                <td><span style="display:inline-block;padding:2px 7px;border-radius:3px;font-size:11px;font-weight:600;background:{pt_bg};color:{pt_color};">{pkg_type}</span></td>
                                <td class="text-center" data-order="{sort_val}">{readiness_cell}</td>
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
                            <div class="kpi-label">In Sync</div>
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
                                <th style="width:28%">Artifact Name</th>
                                <th style="width:14%">Artifact Type</th>
                                <th style="width:28%">Package Name</th>
                                <th style="width:12%" class="text-center">Design Version</th>
                                <th style="width:12%" class="text-center">Deployed Version</th>
                                <th style="width:6%" class="text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody>"""
        
        for dep in deployments:
            status = dep.get('deployment_status', 'Unknown')
            status_class = 'status-inSync' if status == 'In Sync' else ('status-outofSync' if status == 'Out of Sync' else 'status-notDeployed')
            sort_order = 1 if status == 'Out of Sync' else (2 if status == 'Not Deployed' else 3)
            
            html += f"""
                            <tr>
                                <td>{dep.get('artifact_name', 'Unknown')}</td>
                                <td>{dep.get('artifact_type', 'Unknown')}</td>
                                <td>{dep.get('package_name', 'Unknown')}</td>
                                <td class="text-center">{dep.get('design_version', 'N/A')}</td>
                                <td class="text-center">{dep.get('runtime_version') or 'Not Deployed'}</td>
                                <td class="text-center" data-order="{sort_order}"><span class="status-badge {status_class}">{status}</span></td>
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
            </div>"""
        
        return html
    
    def _generate_tab_environment_variables(self, data: Dict[str, Any]) -> str:
        """Generate environment variables tab"""
        env_vars_data = data.get('environment_variables', {})
        
        if not env_vars_data.get('available', False):
            return """            <div class="tab-pane fade" id="envvars" role="tabpanel">
                <div class="alert-box alert-info">
                    <strong>Note:</strong> Environment variable data is not available. This feature requires PARSE_BPMN_CONTENT=true and EXTRACT_IFLOW_CONTENT=true in configuration.
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
                        <div class="kpi-card">
                            <div class="kpi-number">{unique_vars_count}</div>
                            <div class="kpi-label">Unique HC_ Variables</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{stats.get('total_files', 0)}</div>
                            <div class="kpi-label">Total</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{by_file_type.get('groovyScript', 0)}</div>
                            <div class="kpi-label">Groovy Script</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{by_file_type.get('javascript', 0)}</div>
                            <div class="kpi-label">JavaScript</div>
                        </div>
                    </div>
                    <div class="col">
                        <div class="kpi-card">
                            <div class="kpi-number">{by_file_type.get('xslt', 0)}</div>
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
            
            html += f"""
                            <tr>
                                <td><code>{var.get('file_name', 'Unknown')}</code></td>
                                <td>{ft_badge}</td>
                                <td class="text-center"><strong>{var.get('var_count', 0)}</strong></td>
                                <td><code>{var_list}</code></td>
                                <td>{var.get('parent_type', '')}</td>
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
            return """            <div class="tab-pane fade" id="certmappings" role="tabpanel">
                <div class="alert-box alert-info">
                    <strong>Note:</strong> Certificate-to-user mappings are not available. This feature is only available for NEO subaccounts. CF subaccounts use different authentication mechanisms.
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
        
        $(document).ready(function() {
            // Returns a CSV button config with a per-table filename
            function makeBtn(tableName) {
                return [{
                    extend: 'csvHtml5',
                    text: '\U0001F4C4 Export CSV',
                    className: 'buttons-csv',
                    filename: _tenantId + '_' + tableName
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
                order: [[5, 'asc'], [0, 'asc']],
                autoWidth: false,
                buttons: makeBtn('Deployment_Status')
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
        });
    </script>"""
        
        return js.replace('__TENANT_ID__', tenant_safe)
