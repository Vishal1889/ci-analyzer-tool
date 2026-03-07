"""
Package Statistics Report
Shows distribution of package types (Custom, Standard-Editable, Standard Config-Only)
"""

from typing import Dict, Any, List
from ..base_report import BaseReport
from utils.logger import get_logger

logger = get_logger(__name__)


class PackageStatisticsReport(BaseReport):
    """Generates package statistics report"""
    
    def get_report_name(self) -> str:
        return "package_statistics"
    
    def get_report_title(self) -> str:
        return "Package Type Distribution"
    
    def generate(self) -> Dict[str, Any]:
        """Generate package statistics data"""
        logger.info("Generating Package Statistics report...")
        
        query = """
        SELECT 
            p.Id as package_id,
            p.Name as package_name,
            p.Vendor as vendor,
            p.Mode as mode,
            p.Version as version
        FROM package p
        WHERE p.tenant_id = ?
        ORDER BY p.Name
        """
        
        packages = self.execute_query(query, (self.tenant_id,))
        
        stats = {
            'total': 0,
            'custom': 0,
            'standard_editable': 0,
            'standard_config_only': 0
        }
        
        report_data = []
        
        for pkg in packages:
            stats['total'] += 1
            vendor = pkg.get('vendor') or ''
            mode = pkg.get('mode', '')
            
            if not vendor or vendor.strip() == '':
                package_type = 'Custom'
                stats['custom'] += 1
            elif mode == 'EDIT_ALLOWED':
                package_type = 'Standard (Editable)'
                stats['standard_editable'] += 1
            else:
                package_type = 'Standard (Config-Only)'
                stats['standard_config_only'] += 1
            
            report_data.append({
                'package_name': pkg.get('package_name', 'N/A'),
                'package_type': package_type,
                'vendor': vendor or 'Custom',
                'mode': mode,
                'version': pkg.get('version', 'N/A')
            })
        
        self.report_data = {
            'packages': report_data,
            'stats': stats,
            'columns': [
                {'key': 'package_name', 'label': 'Package Name', 'sortable': True},
                {'key': 'package_type', 'label': 'Type', 'sortable': True},
                {'key': 'vendor', 'label': 'Vendor', 'sortable': True},
                {'key': 'version', 'label': 'Version', 'sortable': True}
            ]
        }
        
        logger.info(f"  Total: {stats['total']}, Custom: {stats['custom']}, "
                   f"Standard Editable: {stats['standard_editable']}, "
                   f"Config-Only: {stats['standard_config_only']}")
        
        return self.report_data
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        if not self.report_data:
            self.generate()
        return self.report_data.get('stats', {})
    
    def get_chart_data(self) -> List[Dict[str, Any]]:
        if not self.report_data:
            self.generate()
        
        stats = self.report_data.get('stats', {})
        return [{
            'chart_id': 'package_types_pie',
            'chart_type': 'pie',
            'title': 'Package Type Distribution',
            'data': {
                'labels': ['Custom', 'Standard (Editable)', 'Standard (Config-Only)'],
                'values': [stats.get('custom', 0), stats.get('standard_editable', 0), 
                          stats.get('standard_config_only', 0)],
                'colors': ['#17a2b8', '#28a745', '#ffc107']
            }
        }]