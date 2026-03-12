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
        version_comparison = self._generate_version_comparison()
        versions = self._generate_version_deployment()
        systems = self._generate_systems_adapters()
        env_vars = self._generate_environment_variables()
        cert_mappings = self._generate_certificate_mappings()
        keystore = self._generate_keystore_view()
        
        # Load pre-computed MRS scores and enrich dashboard + packages
        mci_data = self._generate_migration_scores()
        if mci_data.get('available'):
            # Inject MRS summary into dashboard KPIs
            dashboard['kpis']['mci_summary'] = mci_data['summary']
            dashboard['kpis']['mci_available'] = True
            # Override the old readiness_score KPI with the rule-based MRS
            dashboard['kpis']['readiness_score'] = mci_data['summary'].get('overall_mrs', 0)
            # Enrich per-package data with MRS scores
            mci_by_pkg = {p['package_id']: p for p in mci_data.get('packages', [])}
            for pkg in packages.get('packages', []):
                pkg_id = pkg.get('package_id')
                mci_pkg = mci_by_pkg.get(pkg_id, {})
                pkg['readiness_score'] = mci_pkg.get('readiness_score')
                pkg['readiness_tag'] = mci_pkg.get('readiness_tag')
                pkg['rule1a'] = mci_pkg.get('rule1a', 0)
                pkg['rule1b'] = mci_pkg.get('rule1b', 0)
                pkg['rule2'] = mci_pkg.get('rule2', 0)
                pkg['rule3'] = mci_pkg.get('rule3', 0)
                pkg['rule4'] = mci_pkg.get('rule4', 0)
                pkg['rule5'] = mci_pkg.get('rule5', 0)
                pkg['rule6'] = mci_pkg.get('rule6', 0)
        else:
            dashboard['kpis']['mci_summary'] = {}
            dashboard['kpis']['mci_available'] = False
        
        self.report_data = {
            'metadata': metadata,
            'dashboard': dashboard,
            'packages': packages,
            'version_comparison': version_comparison,
            'versions': versions,
            'systems': systems,
            'environment_variables': env_vars,
            'certificate_mappings': cert_mappings,
            'keystore': keystore,
            'migration_scores': mci_data
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
        # Logic: Custom = EDIT_ALLOWED + Not PartnerContent + Not SAP Vendor
        package_query = """
        SELECT 
            COUNT(*) as total_packages,
            SUM(CASE WHEN Mode = 'READ_ONLY' THEN 1 ELSE 0 END) as standard_readonly,
            SUM(CASE WHEN Mode != 'READ_ONLY' AND (PartnerContent = 1 OR LOWER(Vendor) LIKE '%sap%') THEN 1 ELSE 0 END) as standard_editable,
            SUM(CASE WHEN Mode != 'READ_ONLY' AND (PartnerContent != 1 OR PartnerContent IS NULL) AND (LOWER(Vendor) NOT LIKE '%sap%' OR Vendor IS NULL OR TRIM(Vendor) = '') THEN 1 ELSE 0 END) as custom_packages
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
        
        # Get unique systems count from bpmn_channel table (table may not exist if BPMN parsing disabled)
        # Excludes ProcessDirect (internal routing) — consistent with Systems & Adapters tab
        systems_count = 0
        try:
            systems_query = """
            SELECT COUNT(DISTINCT LOWER(TRIM(COALESCE(address, system)))) as unique_systems
            FROM bpmn_channel
            WHERE tenant_id = ?
            AND (address IS NOT NULL OR system IS NOT NULL)
            AND TRIM(COALESCE(address, system, '')) != ''
            AND componentType != 'ProcessDirect'
            """
            systems_count = self.execute_scalar(systems_query, (self.tenant_id,)) or 0
        except Exception:
            logger.debug("  bpmn_channel table not available — systems count set to 0")
        
        # Calculate migration readiness score based on multiple factors
        total_artifacts = iflow_count + script_count + msg_map_count + val_map_count
        readiness_score = self._calculate_readiness_score(
            pkg_data=pkg_data,
            iflow_count=iflow_count,
            total_artifacts=total_artifacts,
            systems_count=systems_count
        )
        
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
        
        # Package distribution for bar chart (always include all types, even if zero)
        package_distribution = [
            {
                'type': 'Custom Packages',
                'count': pkg_data.get('custom_packages', 0),
                'color': '#0070F2',
                'order': 1
            },
            {
                'type': 'Standard (Editable)',
                'count': pkg_data.get('standard_editable', 0),
                'color': '#5E696E',
                'order': 2
            },
            {
                'type': 'Standard (Configure-Only)',
                'count': pkg_data.get('standard_readonly', 0),
                'color': '#0F7D0F',
                'order': 3
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
    
    def _generate_version_comparison(self) -> Dict[str, Any]:
        """Generate Design vs Discover version comparison"""
        
        # Try to get Discover version data if available
        discover_query = """
        SELECT 
            PackageID as package_id,
            PackageName as package_name,
            CurrentVersion as design_version,
            DiscoverVersion as discover_version,
            CASE 
                WHEN CurrentVersion = DiscoverVersion THEN 'Up-to-date'
                WHEN DiscoverVersion = 'Manual check needed' THEN 'Manual check needed'
                ELSE 'Update available'
            END as status
        FROM package_discover_version
        WHERE tenant_id = ?
        ORDER BY status DESC, package_name
        """
        
        comparison_data = []
        discover_available = False
        
        try:
            comparison_data = self.execute_query(discover_query, (self.tenant_id,))
            discover_available = True
            logger.info(f"  Loaded {len(comparison_data)} package version comparisons from Discover")
        except:
            logger.info("  Discover version data not available")
            # Fallback: Get package list without Discover versions
            fallback_query = """
            SELECT 
                p.Id as package_id,
                p.Name as package_name,
                p.Vendor as vendor,
                p.Version as design_version,
                'N/A' as discover_version,
                'No Discover data' as status,
                p.ModifiedDate as last_modified
            FROM package p
            WHERE p.tenant_id = ?
            AND p.Vendor IS NOT NULL 
            AND p.Vendor != ''
            ORDER BY p.Name
            """
            comparison_data = self.execute_query(fallback_query, (self.tenant_id,))
        
        # Calculate statistics
        stats = {
            'total_packages': len(comparison_data),
            'up_to_date': len([p for p in comparison_data if p['status'] == 'Up-to-date']),
            'updates_available': len([p for p in comparison_data if p['status'] == 'Update available']),
            'manual_check': len([p for p in comparison_data if p['status'] in ['Manual check needed', 'No Discover data']]),
            'discover_available': discover_available
        }
        
        return {
            'comparisons': comparison_data,
            'stats': stats
        }
    
    def _generate_package_analysis(self) -> Dict[str, Any]:
        """Generate detailed package analysis"""
        
        # Package details with artifact counts
        # Using same logic as Dashboard for package type classification
        query = """
        SELECT 
            p.Id as package_id,
            p.Name as package_name,
            p.Vendor as vendor,
            p.Mode as mode,
            p.Version as version,
            p.ShortText as description,
            CASE 
                WHEN p.Mode = 'READ_ONLY' THEN 'Standard (Configure-Only)'
                WHEN p.Mode != 'READ_ONLY' AND (p.PartnerContent = 1 OR LOWER(p.Vendor) LIKE '%sap%') THEN 'Standard (Editable)'
                WHEN p.Mode != 'READ_ONLY' AND (p.PartnerContent != 1 OR p.PartnerContent IS NULL) AND (LOWER(p.Vendor) NOT LIKE '%sap%' OR p.Vendor IS NULL OR TRIM(p.Vendor) = '') THEN 'Custom'
                ELSE 'Custom'
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
        GROUP BY p.Id, p.Name, p.Vendor, p.Mode, p.Version, p.ShortText, p.PartnerContent
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
        
        # All artifacts deployment status (IFlows, Script Collections, Message Mappings, Value Mappings)
        all_artifacts_query = """
        SELECT 
            i.Id as artifact_id,
            i.Name as artifact_name,
            'Integration Flow' as artifact_type,
            p.Name as package_name,
            CASE 
                WHEN i.Version = 'Active' THEN 'Draft'
                ELSE i.Version
            END as design_version,
            r.Version as runtime_version,
            CASE 
                WHEN r.Id IS NULL THEN 'Not Deployed'
                WHEN i.Version = r.Version THEN 'In Sync'
                ELSE 'Out of Sync'
            END as deployment_status,
            i.ModifiedAt as last_modified
        FROM iflow i
        INNER JOIN package p ON i.PackageId = p.Id AND i.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id
        WHERE i.tenant_id = ?
        
        UNION ALL
        
        SELECT 
            sc.Id as artifact_id,
            sc.Name as artifact_name,
            'Script Collection' as artifact_type,
            p.Name as package_name,
            CASE 
                WHEN sc.Version = 'Active' THEN 'Draft'
                ELSE sc.Version
            END as design_version,
            r.Version as runtime_version,
            CASE 
                WHEN r.Id IS NULL THEN 'Not Deployed'
                WHEN sc.Version = r.Version THEN 'In Sync'
                ELSE 'Out of Sync'
            END as deployment_status,
            NULL as last_modified
        FROM script_collection sc
        INNER JOIN package p ON sc.PackageId = p.Id AND sc.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON sc.Id = r.Id AND r.Type = 'SCRIPT_COLLECTION' AND sc.tenant_id = r.tenant_id
        WHERE sc.tenant_id = ?
        
        UNION ALL
        
        SELECT 
            mm.Id as artifact_id,
            mm.Name as artifact_name,
            'Message Mapping' as artifact_type,
            p.Name as package_name,
            CASE 
                WHEN mm.Version = 'Active' THEN 'Draft'
                ELSE mm.Version
            END as design_version,
            r.Version as runtime_version,
            CASE 
                WHEN r.Id IS NULL THEN 'Not Deployed'
                WHEN mm.Version = r.Version THEN 'In Sync'
                ELSE 'Out of Sync'
            END as deployment_status,
            NULL as last_modified
        FROM message_mapping mm
        INNER JOIN package p ON mm.PackageId = p.Id AND mm.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON mm.Id = r.Id AND r.Type = 'MESSAGE_MAPPING' AND mm.tenant_id = r.tenant_id
        WHERE mm.tenant_id = ?
        
        UNION ALL
        
        SELECT 
            vm.Id as artifact_id,
            vm.Name as artifact_name,
            'Value Mapping' as artifact_type,
            p.Name as package_name,
            CASE 
                WHEN vm.Version = 'Active' THEN 'Draft'
                ELSE vm.Version
            END as design_version,
            r.Version as runtime_version,
            CASE 
                WHEN r.Id IS NULL THEN 'Not Deployed'
                WHEN vm.Version = r.Version THEN 'In Sync'
                ELSE 'Out of Sync'
            END as deployment_status,
            NULL as last_modified
        FROM value_mapping vm
        INNER JOIN package p ON vm.PackageId = p.Id AND vm.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON vm.Id = r.Id AND r.Type = 'VALUE_MAPPING' AND vm.tenant_id = r.tenant_id
        WHERE vm.tenant_id = ?
        
        ORDER BY deployment_status DESC, package_name, artifact_name
        """
        iflow_deployments = self.execute_query(all_artifacts_query, (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id))
        
        # Calculate deployment statistics
        deployment_stats = {
            'synced': len([d for d in iflow_deployments if d['deployment_status'] == 'In Sync']),
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

        # Check bpmn_channel table exists first
        try:
            self.execute_scalar("SELECT COUNT(*) FROM bpmn_channel WHERE tenant_id = ?", (self.tenant_id,))
        except Exception:
            logger.info("  bpmn_channel table not available — skipping systems/adapters section")
            return {
                'systems': [],
                'adapters': [],
                'stats': {'unique_systems': 0, 'total_adapters': 0, 'adapter_types': 0}
            }

        # Unique systems with adapter details from bpmn_channel table
        # Excludes ProcessDirect (internal routing) and separates system name from URL
        # Joins iflow table to get human-readable iflow names for drill-down
        systems_query = """
        SELECT
            COALESCE(bc.system, 'Unknown') as system_name,
            COALESCE(bc.address, 'N/A') as address_url,
            bc.componentType as adapter_type,
            REPLACE(REPLACE(bc.type, 'Endpoint', ''), 'endpoint', '') as direction,
            COUNT(DISTINCT bc.iflowId) as iflow_count,
            GROUP_CONCAT(DISTINCT COALESCE(i.Name, bc.iflowId) || '|||' || COALESCE(p.Name, 'Unknown Package')) as iflow_names
        FROM bpmn_channel bc
        LEFT JOIN iflow i ON bc.iflowId = i.Id AND bc.tenant_id = i.tenant_id
        LEFT JOIN package p ON i.PackageId = p.Id AND i.tenant_id = p.tenant_id
        WHERE bc.tenant_id = ?
        AND (bc.address IS NOT NULL OR bc.system IS NOT NULL)
        AND TRIM(COALESCE(bc.address, bc.system, '')) != ''
        AND bc.componentType != 'ProcessDirect'
        GROUP BY COALESCE(bc.system, 'Unknown'), COALESCE(bc.address, 'N/A'), bc.componentType, REPLACE(REPLACE(bc.type, 'Endpoint', ''), 'endpoint', '')
        ORDER BY iflow_count DESC, system_name
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
        
        # Unique systems = distinct (system_name, address_url) pairs
        # (len(systems) would over-count because it groups by adapter type + direction too)
        unique_system_pairs = len(set(
            (s.get('system_name', ''), s.get('address_url', ''))
            for s in systems
        ))
        stats = {
            'unique_systems': unique_system_pairs,
            'total_adapters': sum(a['total_count'] for a in adapters),
            'adapter_types': len(adapters)
        }
        
        return {
            'systems': systems,
            'adapters': adapters,
            'stats': stats
        }
    
    def _generate_environment_variables(self) -> Dict[str, Any]:
        """Generate environment variables analysis"""
        
        # Check if table exists
        try:
            self.execute_scalar(
                "SELECT COUNT(*) FROM environment_variable_check WHERE tenant_id = ?",
                (self.tenant_id,)
            )
        except:
            logger.info("  Environment variables table not available")
            return {
                'variables': [],
                'stats': {
                    'total_variables': 0,
                    'total_files': 0,
                    'by_file_type': {},
                    'by_parent_type': {}
                },
                'available': False
            }
        
        # Get file-level details — JOIN package/iflow/script_collection for human-readable names
        variables_query = """
        SELECT 
            evc.fileName as file_name,
            evc.fileType as file_type,
            evc.envVariableCount as var_count,
            evc.envVariableList as variables,
            COALESCE(i.Name, sc.Name, evc.parentName) as parent_name,
            evc.parentType as parent_type,
            COALESCE(p.Name, evc.packageId) as package_name
        FROM environment_variable_check evc
        LEFT JOIN package p ON evc.packageId = p.Id AND evc.tenant_id = p.tenant_id
        LEFT JOIN iflow i ON evc.parentName = i.Id AND evc.tenant_id = i.tenant_id
        LEFT JOIN script_collection sc ON evc.parentName = sc.Id AND evc.tenant_id = sc.tenant_id
        WHERE evc.tenant_id = ?
        ORDER BY COALESCE(i.Name, sc.Name, evc.parentName), evc.fileName
        """
        variables = self.execute_query(variables_query, (self.tenant_id,))
        
        # Get statistics - count unique variables (not files)
        unique_vars_query = """
        SELECT COUNT(DISTINCT envVariableList) as unique_vars
        FROM (
            SELECT TRIM(value) as envVariableList
            FROM environment_variable_check,
            json_each('["' || REPLACE(envVariableList, '|', '","') || '"]')
            WHERE tenant_id = ?
        )
        """
        unique_vars_count = self.execute_scalar(unique_vars_query, (self.tenant_id,)) or 0
        
        # Total files using variables
        total_files = self.execute_scalar(
            "SELECT COUNT(*) FROM environment_variable_check WHERE tenant_id = ?",
            (self.tenant_id,)
        ) or 0
        
        # Breakdown by file type
        file_type_query = """
        SELECT fileType, COUNT(*) as count
        FROM environment_variable_check
        WHERE tenant_id = ?
        GROUP BY fileType
        """
        file_types = self.execute_query(file_type_query, (self.tenant_id,))
        by_file_type = {ft['fileType']: ft['count'] for ft in file_types}
        
        # Breakdown by parent type
        parent_type_query = """
        SELECT parentType, COUNT(*) as count
        FROM environment_variable_check
        WHERE tenant_id = ?
        GROUP BY parentType
        """
        parent_types = self.execute_query(parent_type_query, (self.tenant_id,))
        by_parent_type = {pt['parentType']: pt['count'] for pt in parent_types}
        
        logger.info(f"  Found {unique_vars_count} unique environment variables in {total_files} files")
        
        return {
            'variables': variables,
            'stats': {
                'total_variables': len(variables),
                'total_files': total_files,
                'by_file_type': by_file_type,
                'by_parent_type': by_parent_type
            },
            'available': True
        }
    
    def _generate_certificate_mappings(self) -> Dict[str, Any]:
        """Generate certificate-to-user mappings (NEO only)"""
        
        # Check if table exists (NEO only)
        try:
            self.execute_scalar(
                "SELECT COUNT(*) FROM security_certificate_user_mapping WHERE tenant_id = ?",
                (self.tenant_id,)
            )
        except:
            logger.info("  Certificate-to-user mappings not available (CF tenant or table missing)")
            return {
                'mappings': [],
                'stats': {
                    'total_mappings': 0,
                    'active': 0,
                    'expired': 0,
                    'expiring_soon': 0,
                    'unique_users': 0
                },
                'available': False
            }
        
        # Get certificate mappings with expiry status
        from datetime import datetime, timedelta
        
        mappings_query = """
        SELECT 
            IssuedBy,
            IssuedTo,
            User,
            SerialNumber,
            ValidFrom,
            ValidTo,
            MappingId
        FROM security_certificate_user_mapping
        WHERE tenant_id = ?
        ORDER BY ValidTo DESC
        """
        mappings = self.execute_query(mappings_query, (self.tenant_id,))
        
        # Calculate expiry status for each mapping
        now = datetime.now()
        expiry_threshold = now + timedelta(days=90)
        
        active_count = 0
        expired_count = 0
        expiring_soon_count = 0
        unique_users = set()
        
        for mapping in mappings:
            unique_users.add(mapping['User'])
            
            # Parse ValidTo date (format: 2024-12-18T09:54:08+00:00)
            try:
                valid_to_str = mapping['ValidTo']
                # Remove timezone for simple parsing
                if '+' in valid_to_str:
                    valid_to_str = valid_to_str.split('+')[0]
                elif 'Z' in valid_to_str:
                    valid_to_str = valid_to_str.replace('Z', '')
                
                valid_to = datetime.fromisoformat(valid_to_str)
                
                if valid_to < now:
                    mapping['status'] = 'Expired'
                    expired_count += 1
                elif valid_to < expiry_threshold:
                    mapping['status'] = 'Expiring Soon'
                    expiring_soon_count += 1
                else:
                    mapping['status'] = 'Active'
                    active_count += 1
                    
                # Add days until expiry
                days_until_expiry = (valid_to - now).days
                mapping['days_until_expiry'] = days_until_expiry
                
            except Exception as e:
                logger.warning(f"Could not parse date {mapping.get('ValidTo')}: {e}")
                mapping['status'] = 'Unknown'
                mapping['days_until_expiry'] = None
        
        logger.info(f"  Found {len(mappings)} certificate-to-user mappings ({active_count} active, {expired_count} expired)")
        
        return {
            'mappings': mappings,
            'stats': {
                'total_mappings': len(mappings),
                'active': active_count,
                'expired': expired_count,
                'expiring_soon': expiring_soon_count,
                'unique_users': len(unique_users)
            },
            'available': True
        }
    
    def _generate_keystore_view(self) -> Dict[str, Any]:
        """Generate keystore/certificate view"""
        
        # Get keystore entries
        keystore_query = """
        SELECT 
            Alias,
            Type,
            SubjectDN,
            IssuerDN,
            ValidNotBefore,
            ValidNotAfter,
            KeyType,
            KeySize,
            SignatureAlgorithm,
            Status as entry_status,
            Owner,
            SerialNumber
        FROM security_keystore_entry
        WHERE tenant_id = ?
        ORDER BY ValidNotAfter DESC
        """
        entries = self.execute_query(keystore_query, (self.tenant_id,))
        
        # Calculate expiry status for each entry
        from datetime import datetime, timedelta
        now = datetime.now()
        expiry_threshold = now + timedelta(days=90)
        
        active_count = 0
        expired_count = 0
        expiring_soon_count = 0
        type_breakdown = {}
        key_type_breakdown = {}
        
        for entry in entries:
            # Track types
            entry_type = entry.get('Type', 'Unknown')
            type_breakdown[entry_type] = type_breakdown.get(entry_type, 0) + 1
            
            key_type = entry.get('KeyType', 'Unknown')
            key_type_breakdown[key_type] = key_type_breakdown.get(key_type, 0) + 1
            
            # Parse ValidNotAfter date (format: /Date(timestamp)/)
            try:
                valid_after_str = entry['ValidNotAfter']
                if valid_after_str and '/Date(' in valid_after_str:
                    # Extract timestamp from /Date(timestamp)/
                    timestamp_ms = int(valid_after_str.split('(')[1].split(')')[0])
                    valid_after = datetime.fromtimestamp(timestamp_ms / 1000)
                    
                    if valid_after < now:
                        entry['status'] = 'Expired'
                        expired_count += 1
                    elif valid_after < expiry_threshold:
                        entry['status'] = 'Expiring Soon'
                        expiring_soon_count += 1
                    else:
                        entry['status'] = 'Active'
                        active_count += 1
                    
                    # Add days until expiry
                    days_until_expiry = (valid_after - now).days
                    entry['days_until_expiry'] = days_until_expiry
                    
                    # Format dates for display
                    entry['valid_from_formatted'] = self._parse_odata_date(entry.get('ValidNotBefore', ''))
                    entry['valid_until_formatted'] = valid_after.strftime('%Y-%m-%d')
                else:
                    entry['status'] = 'Unknown'
                    entry['days_until_expiry'] = None
                    
            except Exception as e:
                logger.warning(f"Could not parse date {entry.get('ValidNotAfter')}: {e}")
                entry['status'] = 'Unknown'
                entry['days_until_expiry'] = None
            
            # Extract CN from Subject and Issuer
            entry['subject_cn'] = self._extract_cn(entry.get('SubjectDN', ''))
            entry['issuer_cn'] = self._extract_cn(entry.get('IssuerDN', ''))
        
        logger.info(f"  Found {len(entries)} keystore entries ({active_count} active, {expired_count} expired)")
        
        return {
            'entries': entries,
            'stats': {
                'total_entries': len(entries),
                'active': active_count,
                'expired': expired_count,
                'expiring_soon': expiring_soon_count,
                'by_type': type_breakdown,
                'by_key_type': key_type_breakdown
            }
        }
    
    def _parse_odata_date(self, date_str: str) -> str:
        """Parse SAP OData date format /Date(timestamp)/"""
        if not date_str or '/Date(' not in date_str:
            return 'N/A'
        
        try:
            from datetime import datetime
            timestamp_ms = int(date_str.split('(')[1].split(')')[0])
            dt = datetime.fromtimestamp(timestamp_ms / 1000)
            return dt.strftime('%Y-%m-%d')
        except:
            return 'N/A'
    
    def _extract_cn(self, dn: str) -> str:
        """Extract CN (Common Name) from Distinguished Name"""
        if not dn:
            return 'Unknown'
        
        # Look for CN= in the DN string
        parts = dn.split(',')
        for part in parts:
            part = part.strip()
            if part.startswith('CN='):
                return part[3:]  # Remove 'CN=' prefix
        
        return dn  # Return full DN if CN not found
    
    def _generate_migration_scores(self) -> Dict[str, Any]:
        """Read pre-computed MCI scores from package_migration_score table"""
        try:
            self.execute_scalar(
                "SELECT COUNT(*) FROM package_migration_score WHERE tenant_id = ?",
                (self.tenant_id,)
            )
        except Exception:
            logger.info("  package_migration_score table not available — MCI scores not pre-computed yet")
            return {'packages': [], 'summary': {}, 'available': False}
        
        scores_query = """
        SELECT 
            package_id, package_name, package_type,
            rule1a_score as rule1a, rule1b_score as rule1b,
            rule2_score as rule2, rule3_score as rule3,
            rule4_score as rule4, rule5_score as rule5,
            rule6_score as rule6,
            total_score, readiness_score, readiness_tag, computed_at
        FROM package_migration_score
        WHERE tenant_id = ?
        ORDER BY readiness_score DESC, package_name
        """
        packages = self.execute_query(scores_query, (self.tenant_id,))
        
        if not packages:
            return {'packages': [], 'summary': {}, 'available': True}
        
        custom_pkgs = [p for p in packages if p.get('package_type') == 'Custom']
        standard_pkgs = [p for p in packages if p.get('package_type') != 'Custom']
        
        overall_mrs = round(sum(p['readiness_score'] for p in packages) / len(packages))
        custom_mrs = round(sum(p['readiness_score'] for p in custom_pkgs) / len(custom_pkgs)) if custom_pkgs else 0
        standard_mrs = round(sum(p['readiness_score'] for p in standard_pkgs) / len(standard_pkgs)) if standard_pkgs else 0
        
        tag_counts = {'Ready': 0, 'Mostly Ready': 0, 'Needs Work': 0, 'Not Ready': 0}
        for p in packages:
            tag = p.get('readiness_tag', 'Not Ready')
            if tag in tag_counts:
                tag_counts[tag] += 1
        
        summary = {
            'overall_mrs': overall_mrs,
            'custom_mrs': custom_mrs,
            'standard_mrs': standard_mrs,
            'tag_counts': tag_counts,
            'total_packages_scored': len(packages),
        }
        
        logger.info(f"  Loaded MRS scores for {len(packages)} packages — Overall MRS: {overall_mrs}")
        return {'packages': packages, 'summary': summary, 'available': True}
    
    def _calculate_readiness_score(self, pkg_data: Dict, iflow_count: int, 
                                   total_artifacts: int, systems_count: int) -> int:
        """
        Calculate migration readiness score (0-100) based on multiple factors
        
        Scoring Methodology:
        1. Package Composition (30 points):
           - Standard Read-Only packages are easiest to migrate (30 points)
           - Standard Editable packages need configuration review (20 points)
           - Custom packages require thorough analysis (10 points)
        
        2. Deployment Status (25 points):
           - High deployment sync rate indicates stability
           - Measures design vs runtime alignment
        
        3. Version Currency (20 points):
           - Recent modifications suggest active maintenance
           - Packages not modified in 6+ months may need review
        
        4. Complexity (15 points):
           - Fewer artifacts per package = simpler migration
           - Complexity penalty for high artifact counts
        
        5. Integration Density (10 points):
           - Fewer unique systems = simpler connectivity migration
           - System count vs artifact ratio
        
        Returns:
            int: Readiness score between 0-100
        """
        score = 0.0
        
        # 1. Package Composition Score (30 points max)
        total_packages = pkg_data.get('total_packages', 0)
        if total_packages > 0:
            standard_readonly = pkg_data.get('standard_readonly', 0)
            standard_editable = pkg_data.get('standard_editable', 0)
            custom_packages = pkg_data.get('custom_packages', 0)
            
            # Weighted scoring: Read-Only=1.0, Editable=0.67, Custom=0.33
            composition_score = (
                (standard_readonly * 1.0) +
                (standard_editable * 0.67) +
                (custom_packages * 0.33)
            ) / total_packages
            score += composition_score * 30
            
            logger.debug(f"  Package Composition: {composition_score * 30:.1f}/30 points")
        
        # 2. Deployment Status Score (25 points max)
        if iflow_count > 0:
            # Get deployment sync data
            deploy_query = """
            SELECT 
                SUM(CASE WHEN r.Id IS NOT NULL AND i.Version = r.Version THEN 1 ELSE 0 END) as synced,
                COUNT(*) as total
            FROM iflow i
            LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id
            WHERE i.tenant_id = ?
            """
            deploy_stats = self.execute_query(deploy_query, (self.tenant_id,))
            if deploy_stats:
                synced = deploy_stats[0].get('synced', 0)
                total = deploy_stats[0].get('total', 1)
                sync_ratio = synced / total if total > 0 else 0
                deployment_score = sync_ratio * 25
                score += deployment_score
                logger.debug(f"  Deployment Sync: {deployment_score:.1f}/25 points ({synced}/{total} synced)")
        
        # 3. Version Currency Score (20 points max)
        if total_packages > 0:
            # Check how many packages are recently modified (within 180 days)
            recent_query = """
            SELECT COUNT(*) 
            FROM package 
            WHERE tenant_id = ? 
            AND ModifiedDate >= date('now', '-180 days')
            """
            recent_count = self.execute_scalar(recent_query, (self.tenant_id,)) or 0
            currency_ratio = recent_count / total_packages
            currency_score = currency_ratio * 20
            score += currency_score
            logger.debug(f"  Version Currency: {currency_score:.1f}/20 points ({recent_count}/{total_packages} recently modified)")
        
        # 4. Complexity Score (15 points max)
        if total_packages > 0 and total_artifacts > 0:
            avg_artifacts = total_artifacts / total_packages
            # Lower complexity is better: score inversely proportional to artifact count
            # Assume baseline of 5 artifacts/package as "simple"
            # 1-5 artifacts = full points, 6-10 = reduced, 11+ = further reduced
            if avg_artifacts <= 5:
                complexity_score = 15
            elif avg_artifacts <= 10:
                complexity_score = 15 * (1 - ((avg_artifacts - 5) / 10))
            else:
                complexity_score = 15 * (1 - ((avg_artifacts - 5) / 20))
            
            complexity_score = max(0, complexity_score)  # Ensure non-negative
            score += complexity_score
            logger.debug(f"  Complexity: {complexity_score:.1f}/15 points (avg {avg_artifacts:.1f} artifacts/package)")
        
        # 5. Integration Density Score (10 points max)
        if total_artifacts > 0:
            # Lower system-to-artifact ratio is better (more reuse)
            if systems_count == 0:
                integration_score = 10  # No external systems = simplest
            else:
                system_ratio = systems_count / total_artifacts
                # Ideal ratio: < 0.5 systems per artifact
                if system_ratio <= 0.5:
                    integration_score = 10
                elif system_ratio <= 1.0:
                    integration_score = 10 * (1 - ((system_ratio - 0.5) / 0.5))
                else:
                    integration_score = 5 * (1 / system_ratio)
                
                integration_score = min(10, max(0, integration_score))
            
            score += integration_score
            logger.debug(f"  Integration Density: {integration_score:.1f}/10 points ({systems_count} systems for {total_artifacts} artifacts)")
        
        # Round to nearest integer
        final_score = round(score)
        logger.info(f"  Migration Readiness Score: {final_score}/100")
        
        return final_score
    
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
