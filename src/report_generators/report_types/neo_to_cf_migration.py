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

    def __init__(self, db_path, tenant_id: str, captured_at: str, subaccount_type: str = 'CF'):
        super().__init__(db_path, tenant_id, captured_at)
        self.subaccount_type = subaccount_type
    
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
        keystore = self._generate_keystore_view()
        download_errors = self._generate_download_errors()

        # Certificate mappings only exist on NEO subaccounts
        if self.subaccount_type == 'NEO':
            cert_mappings = self._generate_certificate_mappings()
        else:
            cert_mappings = {'mappings': [], 'stats': {}, 'available': False, 'skipped_cf': True}

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
            'download_errors': download_errors,
        }
        
        logger.info(f"  Generated migration assessment with {len(self.report_data)} sections")
        
        return self.report_data
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate report metadata"""
        return {
            'tenant_id': self.tenant_id,
            'captured_at': self.captured_at,
            'report_generated_at': self.format_date(self.captured_at),
            'report_version': '1.0',
            'subaccount_type': self.subaccount_type
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
        
        # Get unique systems count from iflw_channel table (table may not exist if IFLW parsing disabled)
        # Counts distinct (system, address) PAIRS — identical logic to the Systems & Adapters tab.
        # Excludes ProcessDirect (internal IFlow-to-IFlow routing, not an external system).
        systems_count = 0
        try:
            systems_query = """
            SELECT COUNT(*) as unique_systems
            FROM (
                SELECT DISTINCT
                    COALESCE(system, 'Unknown') as system_name,
                    COALESCE(address, 'N/A') as address_url
                FROM iflw_channel
                WHERE tenant_id = ?
                AND (address IS NOT NULL OR system IS NOT NULL)
                AND TRIM(COALESCE(address, system, '')) != ''
                AND componentType != 'ProcessDirect'
            )
            """
            systems_count = self.execute_scalar(systems_query, (self.tenant_id,)) or 0
        except Exception:
            logger.debug("  iflw_channel table not available — systems count set to 0")
        
        total_artifacts = iflow_count + script_count + msg_map_count + val_map_count

        # Environment variable count (files using HC_ vars — matches Environment Variables tab)
        env_var_artifact_count = 0
        try:
            env_var_artifact_count = self.execute_scalar(
                "SELECT COUNT(*) FROM environment_variable_check WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0",
                (self.tenant_id,)
            ) or 0
        except Exception:
            pass

        # Certificate-to-user mapping count (NEO only)
        cert_mapping_count = 0
        if self.subaccount_type == 'NEO':
            try:
                cert_mapping_count = self.execute_scalar(
                    "SELECT COUNT(*) FROM security_certificate_user_mapping WHERE tenant_id = ?",
                    (self.tenant_id,)
                ) or 0
            except Exception:
                pass

        # Points to Note — compute all 5 items with counts
        points_to_note = []

        # 1. Version mismatches (design vs discover)
        version_mismatch_count = 0
        try:
            version_mismatch_count = self.execute_scalar(
                "SELECT COUNT(*) FROM package_discover_version WHERE tenant_id = ? AND CurrentVersion != DiscoverVersion AND DiscoverVersion != 'Manual check needed'",
                (self.tenant_id,)
            ) or 0
        except Exception:
            pass
        points_to_note.append({
            'label': 'Standard packages with version mismatches (Design vs Discover)',
            'count': version_mismatch_count,
            'status': 'warning' if version_mismatch_count > 0 else 'ok'
        })

        # 1b. Standard packages where Discover version could not be validated
        manual_check_count = 0
        try:
            manual_check_count = self.execute_scalar(
                "SELECT COUNT(*) FROM package_discover_version WHERE tenant_id = ? AND DiscoverVersion = 'Manual check needed'",
                (self.tenant_id,)
            ) or 0
        except Exception:
            pass
        points_to_note.append({
            'label': 'Standard packages requiring manual version check',
            'count': manual_check_count,
            'status': 'warning' if manual_check_count > 0 else 'ok'
        })

        # 2. Artifacts in draft status
        draft_count = 0
        try:
            draft_count = self.execute_scalar(
                """SELECT COUNT(*) FROM (
                    SELECT Id FROM iflow WHERE tenant_id = ? AND Version = 'Active'
                    UNION ALL SELECT Id FROM script_collection WHERE tenant_id = ? AND Version = 'Active'
                    UNION ALL SELECT Id FROM message_mapping WHERE tenant_id = ? AND Version = 'Active'
                    UNION ALL SELECT Id FROM value_mapping WHERE tenant_id = ? AND Version = 'Active'
                )""",
                (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id)
            ) or 0
        except Exception:
            pass
        points_to_note.append({
            'label': 'Artifacts in draft status',
            'count': draft_count,
            'status': 'warning' if draft_count > 0 else 'ok'
        })

        # 3. Artifacts not yet deployed
        not_deployed_count = 0
        try:
            not_deployed_count = self.execute_scalar(
                """SELECT COUNT(*) FROM (
                    SELECT i.Id FROM iflow i LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id WHERE i.tenant_id = ? AND r.Id IS NULL
                    UNION ALL SELECT sc.Id FROM script_collection sc LEFT JOIN runtime r ON sc.Id = r.Id AND r.Type = 'SCRIPT_COLLECTION' AND sc.tenant_id = r.tenant_id WHERE sc.tenant_id = ? AND r.Id IS NULL
                    UNION ALL SELECT mm.Id FROM message_mapping mm LEFT JOIN runtime r ON mm.Id = r.Id AND r.Type = 'MESSAGE_MAPPING' AND mm.tenant_id = r.tenant_id WHERE mm.tenant_id = ? AND r.Id IS NULL
                    UNION ALL SELECT vm.Id FROM value_mapping vm LEFT JOIN runtime r ON vm.Id = r.Id AND r.Type = 'VALUE_MAPPING' AND vm.tenant_id = r.tenant_id WHERE vm.tenant_id = ? AND r.Id IS NULL
                )""",
                (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id)
            ) or 0
        except Exception:
            pass
        points_to_note.append({
            'label': 'Artifacts not yet deployed',
            'count': not_deployed_count,
            'status': 'warning' if not_deployed_count > 0 else 'ok'
        })

        # 4. Artifacts with design/runtime version mismatch (out of sync)
        out_of_sync_count = 0
        try:
            out_of_sync_count = self.execute_scalar(
                """SELECT COUNT(*) FROM (
                    SELECT i.Id FROM iflow i INNER JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id WHERE i.tenant_id = ? AND i.Version != r.Version
                    UNION ALL SELECT sc.Id FROM script_collection sc INNER JOIN runtime r ON sc.Id = r.Id AND r.Type = 'SCRIPT_COLLECTION' AND sc.tenant_id = r.tenant_id WHERE sc.tenant_id = ? AND sc.Version != r.Version
                    UNION ALL SELECT mm.Id FROM message_mapping mm INNER JOIN runtime r ON mm.Id = r.Id AND r.Type = 'MESSAGE_MAPPING' AND mm.tenant_id = r.tenant_id WHERE mm.tenant_id = ? AND mm.Version != r.Version
                    UNION ALL SELECT vm.Id FROM value_mapping vm INNER JOIN runtime r ON vm.Id = r.Id AND r.Type = 'VALUE_MAPPING' AND vm.tenant_id = r.tenant_id WHERE vm.tenant_id = ? AND vm.Version != r.Version
                )""",
                (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id)
            ) or 0
        except Exception:
            pass
        points_to_note.append({
            'label': 'Artifacts with version mismatch (Design vs Deployed)',
            'count': out_of_sync_count,
            'status': 'warning' if out_of_sync_count > 0 else 'ok'
        })

        # 5. Expired certificates in keystore (parse OData /Date(timestamp)/ format)
        expired_cert_count = 0
        try:
            import re
            from datetime import datetime as dt
            now = dt.now()
            entries = self.execute_query(
                "SELECT ValidNotAfter FROM security_keystore_entry WHERE tenant_id = ?",
                (self.tenant_id,)
            )
            for entry in entries:
                raw = entry.get('ValidNotAfter', '')
                match = re.search(r'/Date\((\d+)\)/', str(raw))
                if match:
                    ts = int(match.group(1)) / 1000
                    valid_to = dt.fromtimestamp(ts)
                    if valid_to < now:
                        expired_cert_count += 1
        except Exception:
            pass
        points_to_note.append({
            'label': 'Expired certificates in keystore',
            'count': expired_cert_count,
            'status': 'warning' if expired_cert_count > 0 else 'ok'
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

        # Artifact readiness counts for donut chart (same logic as deployment query)
        artifact_readiness = {'green': 0, 'amber': 0, 'red': 0}
        try:
            ar_rows = self.execute_query("""
                SELECT readiness, COUNT(*) as cnt FROM (
                    SELECT CASE
                        WHEN evc.parentName IS NOT NULL THEN 'red'
                        WHEN i.Version = 'Active' THEN 'amber'
                        ELSE 'green'
                    END as readiness
                    FROM iflow i LEFT JOIN (
                        SELECT DISTINCT parentName FROM environment_variable_check
                        WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                    ) evc ON i.Id = evc.parentName WHERE i.tenant_id = ?
                    UNION ALL
                    SELECT CASE
                        WHEN evc.parentName IS NOT NULL THEN 'red'
                        WHEN sc.Version = 'Active' THEN 'amber'
                        ELSE 'green'
                    END FROM script_collection sc LEFT JOIN (
                        SELECT DISTINCT parentName FROM environment_variable_check
                        WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                    ) evc ON sc.Id = evc.parentName WHERE sc.tenant_id = ?
                    UNION ALL
                    SELECT CASE WHEN mm.Version = 'Active' THEN 'amber' ELSE 'green' END
                    FROM message_mapping mm WHERE mm.tenant_id = ?
                    UNION ALL
                    SELECT CASE WHEN vm.Version = 'Active' THEN 'amber' ELSE 'green' END
                    FROM value_mapping vm WHERE vm.tenant_id = ?
                ) GROUP BY readiness""",
                (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id)
            )
            for r in ar_rows:
                artifact_readiness[r['readiness']] = r['cnt']
        except Exception:
            pass
        
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
                'env_var_artifacts': env_var_artifact_count,
                'cert_mappings': cert_mapping_count,
            },
            'package_distribution': package_distribution,
            'artifact_readiness': artifact_readiness,
            'points_to_note': points_to_note,
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

        # Enrich each package with migration_readiness (Green/Amber/Red) and tooltip
        self._compute_package_readiness(packages)

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

    def _compute_package_readiness(self, packages: List[Dict]) -> None:
        """Compute migration readiness for each package in-place.

        Standard packages: check Discover version currency + artifact readiness.
        Custom packages: check artifact readiness + draft status.
        """
        if not packages:
            return

        # 1. Get per-package artifact readiness counts
        #    Reuses the same draft + HC_ env-var logic as the deployment status query.
        artifact_readiness_query = """
        SELECT
            PackageId,
            SUM(CASE WHEN readiness = 'Green' THEN 1 ELSE 0 END) as green_count,
            SUM(CASE WHEN readiness = 'Amber' THEN 1 ELSE 0 END) as amber_count,
            SUM(CASE WHEN readiness = 'Red'   THEN 1 ELSE 0 END) as red_count,
            COUNT(*) as total
        FROM (
            SELECT i.PackageId,
                CASE
                    WHEN evc.parentName IS NOT NULL THEN 'Red'
                    WHEN i.Version = 'Active' THEN 'Amber'
                    ELSE 'Green'
                END as readiness
            FROM iflow i
            LEFT JOIN (
                SELECT parentName FROM environment_variable_check
                WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                GROUP BY parentName
            ) evc ON i.Id = evc.parentName
            WHERE i.tenant_id = ?

            UNION ALL

            SELECT sc.PackageId,
                CASE
                    WHEN evc.parentName IS NOT NULL THEN 'Red'
                    WHEN sc.Version = 'Active' THEN 'Amber'
                    ELSE 'Green'
                END as readiness
            FROM script_collection sc
            LEFT JOIN (
                SELECT parentName FROM environment_variable_check
                WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                GROUP BY parentName
            ) evc ON sc.Id = evc.parentName
            WHERE sc.tenant_id = ?

            UNION ALL

            SELECT mm.PackageId,
                CASE WHEN mm.Version = 'Active' THEN 'Amber' ELSE 'Green' END as readiness
            FROM message_mapping mm WHERE mm.tenant_id = ?

            UNION ALL

            SELECT vm.PackageId,
                CASE WHEN vm.Version = 'Active' THEN 'Amber' ELSE 'Green' END as readiness
            FROM value_mapping vm WHERE vm.tenant_id = ?
        )
        GROUP BY PackageId
        """
        art_rows = self.execute_query(artifact_readiness_query, (
            self.tenant_id, self.tenant_id,
            self.tenant_id, self.tenant_id,
            self.tenant_id,
            self.tenant_id,
        ))
        art_by_pkg = {r['PackageId']: r for r in art_rows}

        # 2. Get Discover version status for standard packages
        discover_status = {}  # package_id -> 'Up-to-date' | 'Update available' | ...
        try:
            dv_rows = self.execute_query(
                """SELECT PackageID,
                          CurrentVersion,
                          DiscoverVersion,
                          CASE
                              WHEN CurrentVersion = DiscoverVersion THEN 'Up-to-date'
                              WHEN DiscoverVersion = 'Manual check needed' THEN 'Manual check needed'
                              ELSE 'Update available'
                          END as status
                   FROM package_discover_version WHERE tenant_id = ?""",
                (self.tenant_id,),
            )
            for row in dv_rows:
                discover_status[row['PackageID']] = row
        except Exception:
            logger.debug("  package_discover_version table not available — skipping discover check")

        # 3. Get artifact-level details for popover: HC_ var artifacts and draft artifacts per package
        hc_artifacts_by_pkg = {}  # package_id -> [{'name': ..., 'type': ...}, ...]
        try:
            hc_art_rows = self.execute_query("""
                SELECT i.PackageId, i.Name as artifact_name, 'Integration Flow' as artifact_type
                FROM iflow i
                INNER JOIN (
                    SELECT DISTINCT parentName FROM environment_variable_check
                    WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                ) evc ON i.Id = evc.parentName
                WHERE i.tenant_id = ?
                UNION ALL
                SELECT sc.PackageId, sc.Name, 'Script Collection'
                FROM script_collection sc
                INNER JOIN (
                    SELECT DISTINCT parentName FROM environment_variable_check
                    WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                ) evc ON sc.Id = evc.parentName
                WHERE sc.tenant_id = ?
            """, (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id))
            for row in hc_art_rows:
                hc_artifacts_by_pkg.setdefault(row['PackageId'], []).append(row)
        except Exception:
            pass

        draft_artifacts_by_pkg = {}  # package_id -> [{'name': ..., 'type': ...}, ...]
        try:
            draft_rows = self.execute_query("""
                SELECT PackageId, Name as artifact_name, 'Integration Flow' as artifact_type
                FROM iflow WHERE tenant_id = ? AND Version = 'Active'
                UNION ALL
                SELECT PackageId, Name, 'Script Collection'
                FROM script_collection WHERE tenant_id = ? AND Version = 'Active'
                UNION ALL
                SELECT PackageId, Name, 'Message Mapping'
                FROM message_mapping WHERE tenant_id = ? AND Version = 'Active'
                UNION ALL
                SELECT PackageId, Name, 'Value Mapping'
                FROM value_mapping WHERE tenant_id = ? AND Version = 'Active'
            """, (self.tenant_id, self.tenant_id, self.tenant_id, self.tenant_id))
            for row in draft_rows:
                draft_artifacts_by_pkg.setdefault(row['PackageId'], []).append(row)
        except Exception:
            pass

        # 4. Assign readiness to each package
        for pkg in packages:
            pid = pkg['package_id']
            ptype = pkg.get('package_type', 'Custom')
            art = art_by_pkg.get(pid, {'green_count': 0, 'amber_count': 0, 'red_count': 0, 'total': 0})
            green = int(art.get('green_count', 0) or 0)
            amber = int(art.get('amber_count', 0) or 0)
            red = int(art.get('red_count', 0) or 0)
            total = int(art.get('total', 0) or 0)
            checks = []
            hc_arts = hc_artifacts_by_pkg.get(pid, [])
            draft_arts = draft_artifacts_by_pkg.get(pid, [])

            if ptype in ('Standard (Editable)', 'Standard (Configure-Only)'):
                dv = discover_status.get(pid)
                version_ok = dv is not None and dv.get('status') == 'Up-to-date'
                version_unknown = dv is None or dv.get('status') == 'Manual check needed'
                all_green = (total == 0 or (amber == 0 and red == 0))

                # Version check
                if version_ok:
                    checks.append({'check': 'Discover Version', 'status': 'Green',
                                   'detail': 'Up-to-date with Discover'})
                elif version_unknown:
                    checks.append({'check': 'Discover Version', 'status': 'Amber',
                                   'detail': 'Discover data unavailable — manual check needed'})
                else:
                    checks.append({'check': 'Discover Version', 'status': 'Red',
                                   'detail': f'Outdated (design: {dv["CurrentVersion"]}, discover: {dv["DiscoverVersion"]})'})

                # Artifact readiness check
                if all_green:
                    checks.append({'check': 'Artifact Readiness', 'status': 'Green',
                                   'detail': f'All {total} artifacts ready' if total else 'No artifacts'})
                else:
                    non_green = amber + red
                    c = {'check': 'Artifact Readiness', 'status': 'Red' if red > 0 else 'Amber',
                         'detail': f'{non_green} of {total} artifacts need attention ({amber} amber, {red} red)'}
                    art_names = []
                    for a in hc_arts:
                        art_names.append(f"{a['artifact_name']} ({a['artifact_type']}) — System (HC_) Variable")
                    for a in draft_arts:
                        if not any(a['artifact_name'] == h['artifact_name'] for h in hc_arts):
                            art_names.append(f"{a['artifact_name']} ({a['artifact_type']}) — Draft")
                    if art_names:
                        c['files'] = art_names
                    checks.append(c)

                if version_ok and all_green:
                    pkg['migration_readiness'] = 'Green'
                elif (not version_ok and not version_unknown) and (red > 0 or amber > 0):
                    pkg['migration_readiness'] = 'Red'
                else:
                    pkg['migration_readiness'] = 'Amber'
            else:
                # Custom package
                # System (HC_) Variable check
                if red > 0:
                    c = {'check': 'System (HC_) Variables', 'status': 'Red',
                         'detail': f'{red} artifact(s) use System (HC_) variables'}
                    c['files'] = [f"{a['artifact_name']} ({a['artifact_type']})" for a in hc_arts]
                    checks.append(c)
                else:
                    checks.append({'check': 'System (HC_) Variables', 'status': 'Green',
                                   'detail': 'No System (HC_) variable issues'})

                # Draft artifacts check
                if amber > 0:
                    c = {'check': 'Draft Artifacts', 'status': 'Amber',
                         'detail': f'{amber} draft artifact(s) — save versioned copies'}
                    c['files'] = [f"{a['artifact_name']} ({a['artifact_type']})" for a in draft_arts]
                    checks.append(c)
                else:
                    checks.append({'check': 'Draft Artifacts', 'status': 'Green',
                                   'detail': 'No draft artifacts'})

                if red > 0:
                    pkg['migration_readiness'] = 'Red'
                elif amber > 0:
                    pkg['migration_readiness'] = 'Amber'
                else:
                    pkg['migration_readiness'] = 'Green'

            pkg['readiness_checks'] = checks
    
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
        # Includes migration_readiness (Green/Amber/Red).
        # HC_ env var check via environment_variable_check table (IFlows & Script Collections only).
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
            i.ModifiedAt as last_modified,
            CASE
                WHEN evc.parentName IS NOT NULL THEN 'Red'
                WHEN i.Version = 'Active' THEN 'Amber'
                ELSE 'Green'
            END as migration_readiness
        FROM iflow i
        INNER JOIN package p ON i.PackageId = p.Id AND i.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id
        LEFT JOIN (
            SELECT parentName, SUM(CAST(envVariableCount AS INTEGER)) as hc_file_count
            FROM environment_variable_check
            WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
            GROUP BY parentName
        ) evc ON i.Id = evc.parentName
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
            NULL as last_modified,
            CASE
                WHEN evc.parentName IS NOT NULL THEN 'Red'
                WHEN sc.Version = 'Active' THEN 'Amber'
                ELSE 'Green'
            END as migration_readiness
        FROM script_collection sc
        INNER JOIN package p ON sc.PackageId = p.Id AND sc.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON sc.Id = r.Id AND r.Type = 'SCRIPT_COLLECTION' AND sc.tenant_id = r.tenant_id
        LEFT JOIN (
            SELECT parentName, SUM(CAST(envVariableCount AS INTEGER)) as hc_file_count
            FROM environment_variable_check
            WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
            GROUP BY parentName
        ) evc ON sc.Id = evc.parentName
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
            NULL as last_modified,
            CASE
                WHEN mm.Version = 'Active' THEN 'Amber'
                ELSE 'Green'
            END as migration_readiness
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
            NULL as last_modified,
            CASE
                WHEN vm.Version = 'Active' THEN 'Amber'
                ELSE 'Green'
            END as migration_readiness
        FROM value_mapping vm
        INNER JOIN package p ON vm.PackageId = p.Id AND vm.tenant_id = p.tenant_id
        LEFT JOIN runtime r ON vm.Id = r.Id AND r.Type = 'VALUE_MAPPING' AND vm.tenant_id = r.tenant_id
        WHERE vm.tenant_id = ?

        ORDER BY deployment_status DESC, package_name, artifact_name
        """
        # 8 params: evc tenant + iflow tenant, evc tenant + sc tenant, mm tenant, vm tenant
        iflow_deployments = self.execute_query(all_artifacts_query, (
            self.tenant_id, self.tenant_id,
            self.tenant_id, self.tenant_id,
            self.tenant_id,
            self.tenant_id
        ))

        # Enrich with structured readiness_checks for popover display.
        # Load HC_ env variable file details for Red artifacts.
        hc_files_by_parent = {}
        try:
            hc_rows = self.execute_query(
                """SELECT parentName, fileName, fileType,
                          CAST(envVariableCount AS INTEGER) as var_count,
                          envVariableList as variables
                   FROM environment_variable_check
                   WHERE tenant_id = ? AND CAST(envVariableCount AS INTEGER) > 0
                   ORDER BY parentName, fileName""",
                (self.tenant_id,),
            )
            for row in hc_rows:
                hc_files_by_parent.setdefault(row['parentName'], []).append(row)
        except Exception:
            logger.debug("  environment_variable_check table not available — skipping HC_ file details")

        for dep in iflow_deployments:
            checks = []
            readiness = dep.get('migration_readiness', 'Green')
            art_type = dep.get('artifact_type', '')
            is_draft = dep.get('design_version') == 'Draft'
            version_display = dep.get('design_version', 'N/A')

            # Version check (applies to all artifact types)
            if is_draft:
                checks.append({'check': 'Version Status', 'status': 'Amber',
                               'detail': f'Draft — save a versioned copy before migration'})
            else:
                checks.append({'check': 'Version Status', 'status': 'Green',
                               'detail': f'Version {version_display} (not draft)'})

            # System (HC_) Variable check (only for IFlows and Script Collections)
            if art_type in ('Integration Flow', 'Script Collection'):
                hc_files = hc_files_by_parent.get(dep.get('artifact_id'), [])
                if hc_files:
                    _ft_label = {'groovyScript': 'Groovy Script', 'javascript': 'JavaScript', 'xslt': 'XSLT'}
                    file_details = [
                        f"{f['fileName']} ({_ft_label.get(f['fileType'], f['fileType'])}, {f['var_count']} vars)"
                        for f in hc_files
                    ]
                    checks.append({'check': 'System (HC_) Variables', 'status': 'Red',
                                   'detail': f'{len(hc_files)} file(s) use System (HC_) variables',
                                   'files': file_details})
                else:
                    checks.append({'check': 'System (HC_) Variables', 'status': 'Green',
                                   'detail': 'No System (HC_) variables found'})

            dep['readiness_checks'] = checks

        # Calculate deployment statistics
        deployment_stats = {
            'synced': len([d for d in iflow_deployments if d['deployment_status'] == 'In Sync']),
            'out_of_sync': len([d for d in iflow_deployments if d['deployment_status'] == 'Out of Sync']),
            'not_deployed': len([d for d in iflow_deployments if d['deployment_status'] == 'Not Deployed']),
            'readiness_green': len([d for d in iflow_deployments if d.get('migration_readiness') == 'Green']),
            'readiness_amber': len([d for d in iflow_deployments if d.get('migration_readiness') == 'Amber']),
            'readiness_red': len([d for d in iflow_deployments if d.get('migration_readiness') == 'Red']),
        }
        
        return {
            'package_versions': package_versions,
            'artifact_deployments': iflow_deployments,
            'deployment_stats': deployment_stats
        }
    
    def _generate_systems_adapters(self) -> Dict[str, Any]:
        """Generate systems and adapter analysis"""

        # Check iflw_channel table exists first
        try:
            self.execute_scalar("SELECT COUNT(*) FROM iflw_channel WHERE tenant_id = ?", (self.tenant_id,))
        except Exception:
            logger.info("  iflw_channel table not available — skipping systems/adapters section")
            return {
                'systems': [],
                'adapters': [],
                'stats': {'unique_systems': 0, 'total_adapters': 0, 'adapter_types': 0}
            }

        # Unique systems with adapter details from iflw_channel table
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
        FROM iflw_channel bc
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
        FROM iflw_channel
        WHERE tenant_id = ?
        AND componentType IS NOT NULL
        GROUP BY componentType
        ORDER BY total_count DESC
        """
        adapters = self.execute_query(adapter_query, (self.tenant_id,))

        # Enrich adapters with IFlow names per direction for drill-down
        adapter_iflow_query = """
        SELECT
            bc.componentType as adapter_type,
            bc.type as channel_type,
            COALESCE(i.Name, bc.iflowId) as iflow_name,
            COALESCE(p.Name, bc.packageId) as package_name
        FROM iflw_channel bc
        LEFT JOIN iflow i ON bc.iflowId = i.Id AND bc.tenant_id = i.tenant_id
        LEFT JOIN package p ON bc.packageId = p.Id AND bc.tenant_id = p.tenant_id
        WHERE bc.tenant_id = ?
        AND bc.componentType IS NOT NULL
        ORDER BY bc.componentType, bc.type, iflow_name
        """
        try:
            iflow_rows = self.execute_query(adapter_iflow_query, (self.tenant_id,))
            # Build lookup: adapter_type -> { 'sender': [...], 'receiver': [...] }
            adapter_iflows = {}
            for row in iflow_rows:
                at = row['adapter_type']
                if at not in adapter_iflows:
                    adapter_iflows[at] = {'sender': [], 'receiver': []}
                entry = f"{row['iflow_name']}|||{row['package_name']}"
                if 'Sender' in (row.get('channel_type') or ''):
                    adapter_iflows[at]['sender'].append(entry)
                else:
                    adapter_iflows[at]['receiver'].append(entry)
            for adapter in adapters:
                at = adapter['adapter_type']
                info = adapter_iflows.get(at, {'sender': [], 'receiver': []})
                adapter['sender_iflows'] = ','.join(info['sender'])
                adapter['receiver_iflows'] = ','.join(info['receiver'])
        except Exception:
            for adapter in adapters:
                adapter['sender_iflows'] = ''
                adapter['receiver_iflows'] = ''
        
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

    def _generate_download_errors(self) -> Dict[str, Any]:
        """Generate download errors summary from download_error table"""
        try:
            self.execute_scalar(
                "SELECT COUNT(*) FROM download_error WHERE tenant_id = ?",
                (self.tenant_id,)
            )
        except Exception:
            logger.info("  download_error table not available — no error data to display")
            return {'errors': [], 'stats': {}, 'available': False}

        errors_query = """
        SELECT
            PackageID as package_id,
            Type as artifact_type,
            ErrorCode as error_code,
            ErrorType as error_type,
            ErrorMessage as error_message,
            Timestamp as timestamp,
            DownloadAttempted as download_path
        FROM download_error
        WHERE tenant_id = ?
        ORDER BY Timestamp DESC
        """
        errors = self.execute_query(errors_query, (self.tenant_id,))

        if not errors:
            return {'errors': [], 'stats': {}, 'available': True}

        # Build stats
        by_type = {}
        by_error_type = {}
        for e in errors:
            at = e.get('artifact_type', 'Unknown')
            et = e.get('error_type', 'Unknown')
            by_type[at] = by_type.get(at, 0) + 1
            by_error_type[et] = by_error_type.get(et, 0) + 1

        stats = {
            'total_errors': len(errors),
            'by_artifact_type': by_type,
            'by_error_type': by_error_type,
        }

        logger.info(f"  Found {len(errors)} download errors")
        return {'errors': errors, 'stats': stats, 'available': True}

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        if not self.report_data:
            self.generate()
        
        dashboard = self.report_data.get('dashboard', {})
        kpis = dashboard.get('kpis', {})
        
        return {
            'total_packages': kpis.get('total_packages', 0),
            'total_artifacts': kpis.get('total_artifacts', 0),
        }
