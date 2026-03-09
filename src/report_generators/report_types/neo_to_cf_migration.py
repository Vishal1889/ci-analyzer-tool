"""
NEO to CF Migration Assessment Report
Comprehensive migration readiness analysis
"""

from typing import Dict, Any, List
from ..base_report import BaseReport
from utils.logger import get_logger

logger = get_logger(__name__)


class NeoToCFMigrationReport(BaseReport):
    """Generates NEO to CF migration assessment report"""
    
    def get_report_name(self) -> str:
        return "neo_to_cf_migration_assessment"
    
    def get_report_title(self) -> str:
        return "NEO to CF Migration Assessment Report"
    
    def generate(self) -> Dict[str, Any]:
        """Generate comprehensive migration assessment data"""
        logger.info("Generating NEO to CF Migration Assessment report...")
        
        # Generate all sections
        metadata = self._generate_metadata()
        dashboard = self._generate_dashboard()
        packages = self._generate_package_analysis()
        versions = self._generate_version_deployment()
        systems = self._generate_systems_adapters()
        
        self.report_data = {
            'metadata': metadata,
            'dashboard': dashboard,
            'packages': packages,
            'versions': versions,
            'systems': systems
        }
        
        logger.info(f"  Generated migration assessment with {len(self.report_data)} sections")
        
        return self.report_data
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate report metadata"""
        return {
            'tenant_id': self.tenant_id,
            'captured_at': self.captured_at,
            'report_generated_at': self.format_date(self.captured_at),
            'report_version': '1.0'
        }
    
    def _generate_dashboard(self) -> Dict[str, Any]:
        """Generate executive summary dashboard data"""
        
        # Get package counts by type
        package_query = """
        SELECT 
            COUNT(*) as total_packages,
            SUM(CASE WHEN (Vendor IS NULL OR Vendor = '') THEN 1 ELSE 0 END) as custom_packages,
            SUM(CASE WHEN Vendor IS NOT NULL AND Vendor != '' AND Mode = 'READ_ONLY' THEN 1 ELSE 0 END) as standard_readonly,
            SUM(CASE WHEN Vendor IS NOT NULL AND Vendor != '' AND Mode = 'EDIT_ALLOWED' THEN 1 ELSE 0 END) as standard_editable
        FROM package
        WHERE tenant_id = ?
        """
        pkg_stats = self.execute_query(package_query, (self.tenant_id,))
        pkg_data = pkg_stats[0] if pkg_stats else {}
        
        # Get artifact counts
        iflow_count = self.execute_scalar(
            "SELECT COUNT(*) FROM iflow WHERE tenant_id = ?",
            (self.tenant_id,)
        ) or 0
        
        script_count = self.execute_scalar(
            "SELECT COUNT(*) FROM script_collection WHERE tenant_id = ?",
            (self.tenant_id,)
        ) or 0
        
        msg_map_count = self.execute_scalar(
            "SELECT COUNT(*) FROM message_mapping WHERE tenant_id = ?",
            (self.tenant_id,)
        ) or 0
        
        val_map_count = self.execute_scalar(
            "SELECT COUNT(*) FROM value_mapping WHERE tenant_id = ?",
            (self.tenant_id,)
        ) or 0
        
        # Get unique systems count from bpmn_channel table
        systems_query = """
        SELECT COUNT(DISTINCT LOWER(TRIM(COALESCE(address, system)))) as unique_systems
        FROM bpmn_channel
        WHERE tenant_id = ?
        AND (address IS NOT NULL OR system IS NOT NULL)
        AND TRIM(COALESCE(address, system, '')) != ''
        """
        systems_count = self.execute_scalar(systems_query, (self.tenant_id,)) or 0
        
        # Calculate migration readiness score (simplified)
        total_artifacts = iflow_count + script_count + msg_map_count + val_map_count
        readiness_score = 85  # Placeholder - can be calculated based on various factors
        
        # Get critical alerts
        alerts = []
        
        # Check for outdated packages (placeholder - need Discover data)
        outdated_query = """
        SELECT COUNT(*) FROM package 
        WHERE tenant_id = ? 
        AND ModifiedDate < date('now', '-180 days')
        """
        outdated_count = self.execute_scalar(outdated_query, (self.tenant_id,)) or 0
        if outdated_count > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{outdated_count} package(s) not modified in 6+ months'
            })
        
        # Check for undeployed IFlows
        undeployed_query = """
        SELECT COUNT(DISTINCT i.Id) 
        FROM iflow i
        LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id
        WHERE i.tenant_id = ? AND r.Id IS NULL
        """
        undeployed_count = self.execute_scalar(undeployed_query, (self.tenant_id,)) or 0
        if undeployed_count > 0:
            alerts.append({
                'type': 'info',
                'message': f'{undeployed_count} IFlow(s) not deployed to runtime'
            })
        
        # Package distribution for donut chart
        package_distribution = [
            {
                'type': 'Custom Packages',
                'count': pkg_data.get('custom_packages', 0),
                'color': '#0070F2'
            },
            {
                'type': 'Standard (Read-Only)',
                'count': pkg_data.get('standard_readonly', 0),
                'color': '#0F7D0F'
            },
            {
                'type': 'Standard (Editable)',
                'count': pkg_data.get('standard_editable', 0),
                'color': '#5E696E'
            }
        ]
        
        # Top 5 packages by artifact count
        top_packages_query = """
        SELECT 
            p.Name as package_name,
            p.Mode as mode,
            COUNT(DISTINCT i.Id) as iflow_count,
            COUNT(DISTINCT sc.Name) as script_count,
            COUNT(DISTINCT mm.Id) as msg_map_count,
            COUNT(DISTINCT vm.Id) as val_map_count,
            (COUNT(DISTINCT i.Id) + COUNT(DISTINCT sc.Name) + 
             COUNT(DISTINCT mm.Id) + COUNT(DISTINCT vm.Id)) as total_artifacts
        FROM package p
        LEFT JOIN iflow i ON p.Id = i.PackageId AND p.tenant_id = i.tenant_id
        LEFT JOIN script_collection sc ON p.Id = sc.PackageId AND p.tenant_id = sc.tenant_id
        LEFT JOIN message_mapping mm ON p.Id = mm.PackageId AND p.tenant_id = mm.tenant_id
        LEFT JOIN value_mapping vm ON p.Id = vm.PackageId AND p.tenant_id = vm.tenant_id
        WHERE p.tenant_id = ?
        GROUP BY p.Name, p.Mode
        ORDER BY total_artifacts DESC
        LIMIT 5
        """
        top_packages = self.execute_query(top_packages_query, (self.tenant_id,))
        
        return {
            'kpis': {
                'total_packages': pkg_data.get('total_packages', 0),
                'custom_packages': pkg_data.get('custom_packages', 0),
                'standard_readonly': pkg_data.get('standard_readonly', 0),
                'standard_editable': pkg_data.get('standard_editable', 0),
                'total_iflows': iflow_count,
                'total_scripts': script_count,
                'total_msg_maps': msg_map_count,
                'total_val_maps': val_map_count,
                'total_artifacts': total_artifacts,
                'unique_systems': systems_count,
                'readiness_score': readiness_score
            },
            'package_distribution': package_distribution,
            'alerts': alerts,
            'top_packages': top_packages
        }
    
    def _generate_package_analysis(self) -> Dict[str, Any]:
        """Generate detailed package analysis"""
        
        # Package details with artifact counts
        query = """
        SELECT 
            p.Id as package_id,
            p.Name as package_name,
            p.Vendor as vendor,
            p.Mode as mode,
            p.Version as version,
            p.ShortText as description,
            CASE 
                WHEN (p.Vendor IS NULL OR p.Vendor = '') THEN 'Custom'
                WHEN p.Mode = 'READ_ONLY' THEN 'Standard (Read-Only)'
                WHEN p.Mode = 'EDIT_ALLOWED' THEN 'Standard (Editable)'
                ELSE 'Unknown'
            END as package_type,
            COUNT(DISTINCT i.Id) as iflow_count,
            COUNT(DISTINCT sc.Name) as script_count,
            COUNT(DISTINCT mm.Id) as msg_map_count,
            COUNT(DISTINCT vm.Id) as val_map_count,
            (COUNT(DISTINCT i.Id) + COUNT(DISTINCT sc.Name) + 
             COUNT(DISTINCT mm.Id) + COUNT(DISTINCT vm.Id)) as total_artifacts
        FROM package p
        LEFT JOIN iflow i ON p.Id = i.PackageId AND p.tenant_id = i.tenant_id
        LEFT JOIN script_collection sc ON p.Id = sc.PackageId AND p.tenant_id = sc.tenant_id
        LEFT JOIN message_mapping mm ON p.Id = mm.PackageId AND p.tenant_id = mm.tenant_id
        LEFT JOIN value_mapping vm ON p.Id = vm.PackageId AND p.tenant_id = vm.tenant_id
        WHERE p.tenant_id = ?
        GROUP BY p.Id, p.Name, p.Vendor, p.Mode, p.Version, p.ShortText
        ORDER BY total_artifacts DESC, p.Name
        """
        
        packages = self.execute_query(query, (self.tenant_id,))
        
        # Calculate statistics
        stats = {
            'total_packages': len(packages),
            'total_artifacts': sum(pkg['total_artifacts'] for pkg in packages),
            'avg_artifacts_per_package': round(sum(pkg['total_artifacts'] for pkg in packages) / len(packages), 1) if packages else 0
        }
        
        return {
            'packages': packages,
            'stats': stats
        }
    
    def _generate_version_deployment(self) -> Dict[str, Any]:
        """Generate version comparison and deployment status"""
        
        # Package version info
        package_versions_query = """
        SELECT 
            p.Id as package_id,
            p.Name as package_name,
            p.Version as current_version,
            p.ModifiedDate as last_modified,
            'N/A' as latest_version,
            CASE 
                WHEN p.ModifiedDate < date('now', '-180 days') THEN 'Outdated'
                ELSE 'Current'
            END as version_status
        FROM package p
        WHERE p.tenant_id = ?
        ORDER BY p.Name
        """
        package_versions = self.execute_query(package_versions_query, (self.tenant_id,))
        
        # IFlow deployment status
        iflow_deployment_query = """
        SELECT 
            i.Id as artifact_id,
            i.Name as artifact_name,
            'IFlow' as artifact_type,
            p.Name as package_name,
            i.Version as design_version,
            r.Version as runtime_version,
            CASE 
                WHEN r.Id IS NULL THEN 'Not Deployed'
                WHEN i.Version = r.Version THEN 'Synced'
                ELSE 'Out of Sync'
            END as deployment_status,
            i.ModifiedDate as last_modified
        FROM iflow i
        INNER JOIN package p ON i.PackageId = p.Id AND i.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id
        WHERE i.tenant_id = ?
        ORDER BY deployment_status DESC, p.Name, i.Name
        """
        iflow_deployments = self.execute_query(iflow_deployment_query, (self.tenant_id,))
        
        # Calculate deployment statistics
        deployment_stats = {
            'synced': len([d for d in iflow_deployments if d['deployment_status'] == 'Synced']),
            'out_of_sync': len([d for d in iflow_deployments if d['deployment_status'] == 'Out of Sync']),
            'not_deployed': len([d for d in iflow_deployments if d['deployment_status'] == 'Not Deployed'])
        }
        
        return {
            'package_versions': package_versions,
            'artifact_deployments': iflow_deployments,
            'deployment_stats': deployment_stats
        }
    
    def _generate_systems_adapters(self) -> Dict[str, Any]:
        """Generate systems and adapter analysis"""
        
        # Unique systems with adapter details from bpmn_channel table
        systems_query = """
        SELECT DISTINCT
            TRIM(LOWER(COALESCE(address, system))) as system_id,
            COALESCE(address, system) as system_name,
            componentType as adapter_type,
            type as direction,
            COUNT(DISTINCT iflowId) as usage_count
        FROM bpmn_channel
        WHERE tenant_id = ?
        AND (address IS NOT NULL OR system IS NOT NULL)
        AND TRIM(COALESCE(address, system, '')) != ''
        GROUP BY TRIM(LOWER(COALESCE(address, system))), COALESCE(address, system), componentType, type
        ORDER BY usage_count DESC, system_name
        """
        systems = self.execute_query(systems_query, (self.tenant_id,))
        
        # Adapter type distribution using correct column names
        adapter_query = """
        SELECT 
            componentType as adapter_type,
            SUM(CASE WHEN type LIKE '%Sender%' THEN 1 ELSE 0 END) as sender_count,
            SUM(CASE WHEN type LIKE '%Receiver%' THEN 1 ELSE 0 END) as receiver_count,
            COUNT(*) as total_count
        FROM bpmn_channel
        WHERE tenant_id = ?
        AND componentType IS NOT NULL
        GROUP BY componentType
        ORDER BY total_count DESC
        """
        adapters = self.execute_query(adapter_query, (self.tenant_id,))
        
        # Calculate statistics
        stats = {
            'unique_systems': len(systems),
            'total_adapters': sum(a['total_count'] for a in adapters),
            'adapter_types': len(adapters)
        }
        
        return {
            'systems': systems,
            'adapters': adapters,
            'stats': stats
        }
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        if not self.report_data:
            self.generate()
        
        dashboard = self.report_data.get('dashboard', {})
        kpis = dashboard.get('kpis', {})
        
        return {
            'total_packages': kpis.get('total_packages', 0),
            'total_artifacts': kpis.get('total_artifacts', 0),
            'readiness_score': kpis.get('readiness_score', 0)
        }