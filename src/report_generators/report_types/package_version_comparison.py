"""
Package Version Comparison Report
Compares package versions between Design (current) and Discover (latest available)
"""

from typing import Dict, Any, List
from ..base_report import BaseReport
from utils.logger import get_logger

logger = get_logger(__name__)


class PackageVersionComparisonReport(BaseReport):
    """Generates package version comparison report"""
    
    def get_report_name(self) -> str:
        return "package_version_comparison"
    
    def get_report_title(self) -> str:
        return "Package Version Comparison (Design vs Discover)"
    
    def generate(self) -> Dict[str, Any]:
        """Generate package version comparison data"""
        logger.info("Generating Package Version Comparison report...")
        
        # Query packages with version information
        query = """
        SELECT 
            p.Id as package_id,
            p.Name as package_name,
            p.Version as current_version,
            p.Vendor as vendor,
            p.Mode as mode,
            p.ShortText as description,
            p.ModifiedDate as last_modified,
            p.ModifiedBy as modified_by
        FROM package p
        WHERE p.tenant_id = ?
        ORDER BY p.Name
        """
        
        packages = self.execute_query(query, (self.tenant_id,))
        
        # Load Discover version data if available
        discover_query = """
        SELECT 
            PackageID as package_id,
            DiscoverVersion as latest_version,
            CASE 
                WHEN CurrentVersion = DiscoverVersion THEN 'Up to date'
                WHEN DiscoverVersion = 'Manual check needed' THEN 'Manual check needed'
                ELSE 'Update available'
            END as version_status
        FROM package_discover_version
        WHERE tenant_id = ?
        """
        
        discover_versions = {}
        try:
            discover_data = self.execute_query(discover_query, (self.tenant_id,))
            for row in discover_data:
                discover_versions[row['package_id']] = {
                    'latest_version': row['latest_version'],
                    'status': row['version_status']
                }
        except:
            # Table may not exist if Discover check wasn't run
            logger.warning("Discover version data not available")
        
        # Process and categorize packages
        report_data = []
        stats = {
            'total_packages': 0,
            'custom_packages': 0,
            'standard_packages': 0,
            'up_to_date': 0,
            'outdated': 0,
            'no_version_info': 0
        }
        
        for pkg in packages:
            stats['total_packages'] += 1
            
            # Determine if custom or standard
            vendor = pkg.get('vendor') or ''
            is_custom = not vendor or vendor.strip() == ''
            
            if is_custom:
                stats['custom_packages'] += 1
                package_type = 'Custom'
            else:
                stats['standard_packages'] += 1
                if pkg.get('mode') == 'EDIT_ALLOWED':
                    package_type = 'Standard (Editable)'
                else:
                    package_type = 'Standard (Config-Only)'
            
            # Get Discover version info
            package_id = pkg['package_id']
            discover_info = discover_versions.get(package_id, {})
            latest_version = discover_info.get('latest_version', 'N/A')
            
            # Determine status
            if is_custom:
                status = 'Custom'
                status_class = 'info'
            elif latest_version == 'N/A':
                status = 'No Version Info'
                status_class = 'secondary'
                stats['no_version_info'] += 1
            elif pkg['current_version'] == latest_version:
                status = 'Up-to-date'
                status_class = 'success'
                stats['up_to_date'] += 1
            else:
                status = 'Outdated'
                status_class = 'warning'
                stats['outdated'] += 1
            
            report_data.append({
                'package_id': package_id,
                'package_name': pkg['package_name'],
                'current_version': pkg['current_version'] or 'N/A',
                'latest_version': latest_version,
                'vendor': vendor or 'Custom',
                'package_type': package_type,
                'mode': pkg.get('mode', 'N/A'),
                'status': status,
                'status_class': status_class,
                'description': pkg.get('description', ''),
                'last_modified': self.format_date(pkg.get('last_modified')),
                'modified_by': pkg.get('modified_by', 'N/A')
            })
        
        self.report_data = {
            'packages': report_data,
            'stats': stats,
            'columns': [
                {'key': 'package_name', 'label': 'Package Name', 'sortable': True},
                {'key': 'current_version', 'label': 'Current Version', 'sortable': True},
                {'key': 'latest_version', 'label': 'Latest Version', 'sortable': True},
                {'key': 'status', 'label': 'Status', 'sortable': True},
                {'key': 'package_type', 'label': 'Type', 'sortable': True},
                {'key': 'vendor', 'label': 'Vendor', 'sortable': True},
                {'key': 'last_modified', 'label': 'Last Modified', 'sortable': True}
            ]
        }
        
        logger.info(f"  Found {stats['total_packages']} packages")
        logger.info(f"  Custom: {stats['custom_packages']}, Standard: {stats['standard_packages']}")
        
        return self.report_data
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        if not self.report_data:
            self.generate()
        
        stats = self.report_data.get('stats', {})
        return {
            'total_packages': stats.get('total_packages', 0),
            'outdated_packages': stats.get('outdated', 0),
            'custom_packages': stats.get('custom_packages', 0)
        }
    
    def get_chart_data(self) -> List[Dict[str, Any]]:
        """Get chart data for visualization"""
        if not self.report_data:
            self.generate()
        
        stats = self.report_data.get('stats', {})
        
        return [
            {
                'chart_id': 'package_status_pie',
                'chart_type': 'pie',
                'title': 'Package Version Status',
                'data': {
                    'labels': ['Up-to-date', 'Outdated', 'Custom', 'No Version Info'],
                    'values': [
                        stats.get('up_to_date', 0),
                        stats.get('outdated', 0),
                        stats.get('custom_packages', 0),
                        stats.get('no_version_info', 0)
                    ],
                    'colors': ['#28a745', '#ffc107', '#17a2b8', '#6c757d']
                }
            }
        ]