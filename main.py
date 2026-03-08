#!/usr/bin/env python3
"""
SAP Cloud Integration Analyzer Tool
Main entry point for the application
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="SAP Cloud Integration Analyzer Tool - Extract and analyze CI data"
    )
    
    parser.add_argument(
        "--api",
        type=str,
        choices=["packages", "iflows", "configurations", "runtime", "security"],
        help="Specific API to call (default: all)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--save-only",
        action="store_true",
        help="Only download and save JSON responses, don't parse or store in DB"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="CI Analyzer Tool v0.1.0"
    )
    
    return parser.parse_args()


def main():
    """Main application entry point"""
    print("=" * 70)
    print("SAP Cloud Integration Analyzer Tool")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    args = parse_arguments()
    
    # Generate run timestamp once at start
    run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Import modules (config first to catch validation errors early)
        from utils.config import get_config
        
        # Load and validate configuration
        print("[INFO] Loading configuration...")
        try:
            config = get_config()
        except ValueError as e:
            # Configuration validation error - display cleanly without traceback
            print()
            print("=" * 70)
            print("[ERROR] Configuration Validation Failed")
            print("=" * 70)
            print(str(e))
            print("=" * 70)
            print()
            print("Please fix the configuration errors in your .env file and try again.")
            return 1
        
        from utils.logger import setup_logging
        from auth.auth_factory import create_auth_client, create_discover_auth_client
        from database.db_manager import DynamicDatabaseManager
        from downloader.package_downloader import PackageDownloader
        from downloader.iflow_downloader import IFlowDownloader
        from downloader.resource_downloader import ResourceDownloader
        from downloader.configuration_downloader import ConfigurationDownloader
        from downloader.message_mapping_downloader import MessageMappingDownloader
        from downloader.value_mapping_downloader import ValueMappingDownloader
        from downloader.script_collection_downloader import ScriptCollectionDownloader
        from downloader.security_downloader import (
            UserCredentialsDownloader,
            OAuth2ClientCredentialsDownloader,
            SecureParametersDownloader,
            KeystoreEntriesDownloader,
            RuntimeArtifactsDownloader,
            CertificateUserMappingsDownloader,
            AccessPoliciesDownloader
        )
        from downloader.partner_directory_downloader import PartnerDirectoryDownloader
        from downloader.discover_version_checker import DiscoverVersionChecker
        from downloader.artifact_zip_downloader import ArtifactZipDownloader
        from downloader.readonly_package_extractor import ReadOnlyPackageExtractor
        from parsers.package_parser import PackageParser
        from parsers.iflow_parser import IFlowParser
        from parsers.resource_parser import ResourceParser
        from parsers.configuration_parser import ConfigurationParser
        from parsers.message_mapping_parser import MessageMappingParser
        from parsers.value_mapping_parser import ValueMappingParser
        from parsers.script_collection_parser import ScriptCollectionParser
        import json
        
        # Configuration already loaded and validated above
        print(f"[INFO] Tenant: {config.tenant_id}")
        print(f"[INFO] API Base URL: {config.api_base_url}")
        print(f"[INFO] Run directory: {config.get_run_dir(run_timestamp)}")
        
        # Setup logging with run-specific log file
        print(f"[INFO] Setting up logging (level: {args.log_level})...")
        log_setup = setup_logging(
            config.tenant_id,
            config.get_log_file(run_timestamp),
            args.log_level,
            config.trace_api_calls
        )
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        logger.info("Application started")
        logger.info(f"Configuration loaded: {config}")
        logger.info(f"Run timestamp: {run_timestamp}")
        logger.info(f"Run directory: {config.get_run_dir(run_timestamp)}")
        
        # Note: Database initialization moved to after BPMN extraction (PHASE 2)
        
        # Log authentication configuration
        logger.info("=" * 70)
        logger.info("Authentication Configuration")
        logger.info("=" * 70)
        logger.info(f"Subaccount Type: {config.subaccount_type}")
        logger.info(f"Authentication Method: {config.auth_type}")
        if config.auth_type == "BASIC":
            masked_username = config.basic_auth_username[:3] + '*' * (len(config.basic_auth_username) - 3) \
                             if len(config.basic_auth_username) > 3 else '***'
            logger.info(f"Username: {masked_username}")
        logger.info(f"API Base URL: {config.api_base_url}")
        logger.info("=" * 70)
        
        # Create authentication client using factory
        logger.info("Setting up authentication...")
        auth_client = create_auth_client(config)
        
        # Test authentication
        logger.info("Testing authentication...")
        auth_client.get_access_token()
        logger.info("Authentication successful!")
        
        # Use run-specific download path
        download_path = config.get_download_path(run_timestamp)
        logger.info(f"Download directory: {download_path}")
        
        # Track download results for batch parsing
        download_results = {}
        
        # Check execution mode
        if config.execution_mode == "REPORT_ONLY":
            logger.info("=" * 70)
            logger.info("REPORT_ONLY MODE - Generating reports only")
            logger.info("=" * 70)
            logger.info(f"Using database: {config.report_db_path}")
            logger.info("")
            
            # Generate reports from existing database
            try:
                logger.info("Generating reports...")
                logger.info("-" * 70)
                
                from report_generators.report_types import (
                    PackageVersionComparisonReport,
                    EnvironmentVariablesReport,
                    PackageStatisticsReport
                )
                
                # Extract tenant info from database path
                db_path = Path(config.report_db_path)
                
                # Create reports directory next to database
                reports_dir = db_path.parent / "reports"
                reports_dir.mkdir(exist_ok=True)
                
                # Generate each report
                reports_generated = []
                
                # Package Version Comparison
                try:
                    report = PackageVersionComparisonReport(db_path, config.tenant_id, datetime.now().isoformat())
                    data = report.generate()
                    
                    # Save report to JSON file
                    report_file = reports_dir / f"{report.get_report_name()}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    reports_generated.append(report.get_report_name())
                    logger.info(f"✓ Generated {report.get_report_title()}")
                    logger.info(f"  Saved to: {report_file}")
                except Exception as e:
                    logger.warning(f"Could not generate Package Version Comparison: {e}")
                
                # Environment Variables
                try:
                    report = EnvironmentVariablesReport(db_path, config.tenant_id, datetime.now().isoformat())
                    data = report.generate()
                    
                    # Save report to JSON file
                    report_file = reports_dir / f"{report.get_report_name()}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    reports_generated.append(report.get_report_name())
                    logger.info(f"✓ Generated {report.get_report_title()}")
                    logger.info(f"  Saved to: {report_file}")
                except Exception as e:
                    logger.warning(f"Could not generate Environment Variables report: {e}")
                
                # Package Statistics
                try:
                    report = PackageStatisticsReport(db_path, config.tenant_id, datetime.now().isoformat())
                    data = report.generate()
                    
                    # Save report to JSON file
                    report_file = reports_dir / f"{report.get_report_name()}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    reports_generated.append(report.get_report_name())
                    logger.info(f"✓ Generated {report.get_report_title()}")
                    logger.info(f"  Saved to: {report_file}")
                except Exception as e:
                    logger.warning(f"Could not generate Package Statistics report: {e}")
                
                logger.info("")
                logger.info("=" * 70)
                logger.info(f"Report generation completed! ({len(reports_generated)} reports)")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Note: HTML/Excel output formatting not yet implemented")
                logger.info("Report data has been generated and validated from database")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                raise
            
        elif config.execution_mode == "FULL":
            # PHASE 1: DOWNLOAD ALL APIs
            logger.info("=" * 70)
            logger.info("PHASE 1: DOWNLOADING DATA")
            logger.info("=" * 70)
            
            # Download Runtime Artifacts (independent) - FIRST!
            if args.api == 'runtime' or not args.api:
                logger.info("")
                logger.info("Downloading Runtime Artifacts...")
                logger.info("-" * 70)
                
                downloader = RuntimeArtifactsDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['runtime_artifacts'] = downloader.download()
                logger.info(f"Downloaded {download_results['runtime_artifacts']['count']} runtime artifacts")
        
            # Download Packages
            if args.api == 'packages' or not args.api:
                logger.info("")
                logger.info("Downloading Packages...")
                logger.info("-" * 70)
                
                downloader = PackageDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                
                download_results['packages'] = downloader.download()
                logger.info(f"✓ Downloaded {download_results['packages']['count']} packages")
                
                # Check Discover versions (if configured)
                if config.download_discover_versions and config.has_discover_config():
                    logger.info("")
                    logger.info("Checking Discover versions for SAP/Partner packages...")
                    logger.info("-" * 70)
                    
                    try:
                        # Create OAuth client for Discover tenant (always uses OAuth)
                        discover_oauth_client = create_discover_auth_client(config)
                        
                        # Test Discover authentication
                        discover_oauth_client.get_access_token()
                        logger.info("Discover tenant authentication successful!")
                        
                        # Run version checker
                        checker = DiscoverVersionChecker(
                            discover_oauth_client,
                            config.discover_base_url,
                            Path(download_path),
                            config.api_timeout,
                            timestamp=run_timestamp
                        )
                        
                        discover_results = checker.check_versions(download_results['packages']['items'])
                        logger.info(f"Checked {discover_results['count']} SAP/Partner packages")
                        
                    except Exception as e:
                        logger.error(f"Discover version check failed: {e}")
                        logger.warning("Continuing without Discover version information...")
                elif not config.download_discover_versions:
                    logger.info("")
                    logger.info("Discover version check disabled (DOWNLOAD_DISCOVER_VERSIONS=false)")
                else:
                    logger.info("")
                    logger.info("Discover version check skipped (no Discover tenant configuration provided)")
        
            # Download IFlows (depends on packages)
            if (args.api == 'iflows' or not args.api) and 'packages' in download_results:
                logger.info("")
                logger.info("Downloading IFlows...")
                logger.info("-" * 70)
                
                downloader = IFlowDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    parallel_downloads=config.parallel_downloads,
                    timestamp=run_timestamp
                )
                
                download_results['iflows'] = downloader.download()
                logger.info(f"Downloaded {download_results['iflows']['count']} iflows")
        
            # Download Resources (depends on iflows)
            if not args.api and 'iflows' in download_results:
                logger.info("")
                logger.info("Downloading Resources...")
                logger.info("-" * 70)
                
                downloader = ResourceDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    parallel_downloads=config.parallel_downloads,
                    timestamp=run_timestamp
                )
                
                download_results['resources'] = downloader.download()
                logger.info(f"Downloaded {download_results['resources']['count']} resources")
        
            # Download Configurations (depends on iflows)
            if not args.api and 'iflows' in download_results:
                logger.info("")
                logger.info("Downloading Configurations...")
                logger.info("-" * 70)
                
                downloader = ConfigurationDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    parallel_downloads=config.parallel_downloads,
                    timestamp=run_timestamp
                )
                
                download_results['configurations'] = downloader.download()
                logger.info(f"Downloaded {download_results['configurations']['count']} configurations")
        
            # Download Message Mappings (independent, after packages)
            if not args.api and 'packages' in download_results:
                logger.info("")
                logger.info("Downloading Message Mappings...")
                logger.info("-" * 70)
                
                downloader = MessageMappingDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                
                download_results['message_mappings'] = downloader.download()
                logger.info(f"Downloaded {download_results['message_mappings']['count']} message mappings")
        
            # Download Value Mappings (independent, after packages)
            if not args.api and 'packages' in download_results:
                logger.info("")
                logger.info("Downloading Value Mappings...")
                logger.info("-" * 70)
                
                downloader = ValueMappingDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                
                download_results['value_mappings'] = downloader.download()
                logger.info(f"Downloaded {download_results['value_mappings']['count']} value mappings")
        
            # Download Script Collections (nested, depends on packages)
            if not args.api and 'packages' in download_results:
                logger.info("")
                logger.info("Downloading Script Collections...")
                logger.info("-" * 70)
                
                downloader = ScriptCollectionDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    parallel_downloads=config.parallel_downloads,
                    timestamp=run_timestamp
                )
                
                download_results['script_collections'] = downloader.download()
                logger.info(f"Downloaded {download_results['script_collections']['count']} script collections")
        
            # Download Security & Runtime APIs (independent, no dependencies)
            if args.api == 'security' or not args.api:
                logger.info("")
                logger.info("Downloading Security & Runtime Data...")
                logger.info("-" * 70)
                
                # User Credentials
                logger.info("Downloading User Credentials...")
                downloader = UserCredentialsDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['user_credentials'] = downloader.download()
                logger.info(f"Downloaded {download_results['user_credentials']['count']} user credentials")
                
                # OAuth2 Client Credentials
                logger.info("Downloading OAuth2 Client Credentials...")
                downloader = OAuth2ClientCredentialsDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['oauth2_credentials'] = downloader.download()
                logger.info(f"Downloaded {download_results['oauth2_credentials']['count']} OAuth2 client credentials")
                
                # Secure Parameters
                logger.info("Downloading Secure Parameters...")
                downloader = SecureParametersDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['secure_parameters'] = downloader.download()
                logger.info(f"Downloaded {download_results['secure_parameters']['count']} secure parameters")
                
                # Keystore Entries
                logger.info("Downloading Keystore Entries...")
                downloader = KeystoreEntriesDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['keystore_entries'] = downloader.download()
                logger.info(f"Downloaded {download_results['keystore_entries']['count']} keystore entries")
                
                # Certificate-to-User Mappings (NEO only)
                if config.subaccount_type == 'NEO':
                    logger.info("Downloading Certificate-to-User Mappings (NEO)...")
                    downloader = CertificateUserMappingsDownloader(
                        auth_client,
                        config.api_base_url,
                        Path(download_path),
                        config.api_timeout,
                        timestamp=run_timestamp
                    )
                    download_results['certificate_user_mappings'] = downloader.download()
                    logger.info(f"Downloaded {download_results['certificate_user_mappings']['count']} certificate-to-user mappings")
                else:
                    logger.info("Certificate-to-User Mappings skipped (only available for NEO subaccounts)")
                
                # Access Policies (with normalized ArtifactReferences)
                logger.info("Downloading Access Policies...")
                downloader = AccessPoliciesDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['access_policies'] = downloader.download()
                logger.info(f"Downloaded {download_results['access_policies']['count']} access policy records ({download_results['access_policies']['original_policy_count']} policies)")
            
            # Download Partner Directory Binary Parameters (independent)
            if not args.api:
                logger.info("")
                logger.info("Downloading Partner Directory Binary Parameters...")
                logger.info("-" * 70)
                
                downloader = PartnerDirectoryDownloader(
                    auth_client,
                    config.api_base_url,
                    Path(download_path),
                    config.api_timeout,
                    timestamp=run_timestamp
                )
                download_results['partner_directory'] = downloader.download()
                logger.info(f"Downloaded {download_results['partner_directory']['count']} binary parameters")
                logger.info(f"  Files extracted: {download_results['partner_directory']['files_extracted']}")
                logger.info(f"  Files skipped (empty): {download_results['partner_directory']['files_skipped']}")
                
                # Show breakdown by content type
                if download_results['partner_directory']['extraction_stats']:
                    logger.info("  Extraction by type:")
                    for content_type, count in sorted(download_results['partner_directory']['extraction_stats'].items()):
                        logger.info(f"    {content_type}: {count}")
        
            logger.info("")
            logger.info("=" * 70)
            logger.info("All JSON downloads completed successfully!")
            logger.info("=" * 70)
        
            # PHASE 1.5: DOWNLOAD ARTIFACT ZIPS (if packages and iflows are available)
            if config.download_artifact_zips and 'packages' in download_results and 'iflows' in download_results:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.5: DOWNLOADING ARTIFACT ZIPS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Downloading artifact ZIP files...")
                logger.info("-" * 70)
                
                try:
                    zip_downloader = ArtifactZipDownloader(
                        auth_client,
                        config.api_base_url,
                        Path(download_path),
                        config.api_timeout,
                        parallel_downloads=config.parallel_downloads,
                        timestamp=run_timestamp
                    )
                    
                    # Get message mappings and value mappings (use empty lists if not available)
                    message_mappings = download_results.get('message_mappings', {}).get('items', [])
                    value_mappings = download_results.get('value_mappings', {}).get('items', [])
                    
                    zip_stats = zip_downloader.download_all(
                        download_results['packages']['items'],
                        download_results['iflows']['items'],
                        download_results['script_collections']['items'],
                        message_mappings,
                        value_mappings
                    )
                    
                    logger.info("")
                    logger.info("Artifact ZIP download summary:")
                    logger.info(f"  READ_ONLY packages: {zip_stats['read_only_packages_downloaded']}/{zip_stats['read_only_packages_attempted']} downloaded")
                    logger.info(f"  EDIT_ALLOWED iflows: {zip_stats['iflows_downloaded']}/{zip_stats['iflows_attempted']} downloaded")
                    logger.info(f"  Script collections: {zip_stats['script_collections_downloaded']}/{zip_stats['script_collections_attempted']} downloaded")
                    logger.info(f"  Message mappings: {zip_stats['message_mappings_downloaded']}/{zip_stats['message_mappings_attempted']} downloaded")
                    logger.info(f"  Value mappings: {zip_stats['value_mappings_downloaded']}/{zip_stats['value_mappings_attempted']} downloaded")
                    
                    failed_count = (zip_stats['read_only_packages_failed'] + zip_stats['iflows_failed'] + 
                                  zip_stats['script_collections_failed'] + zip_stats['message_mappings_failed'] + 
                                  zip_stats['value_mappings_failed'])
                    
                    if failed_count > 0:
                        logger.warning(f"  Failed downloads: {zip_stats['read_only_packages_failed']} packages, {zip_stats['iflows_failed']} iflows, {zip_stats['script_collections_failed']} script collections, {zip_stats['message_mappings_failed']} message mappings, {zip_stats['value_mappings_failed']} value mappings")
                        logger.warning("  Check download-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("Artifact ZIP downloads completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"Artifact ZIP download failed: {e}")
                    logger.warning("Continuing without artifact ZIPs...")
            else:
                logger.info("")
                logger.info("Skipping artifact ZIP downloads (packages or iflows not downloaded)")
        
            # PHASE 1.6: EXTRACT READ_ONLY PACKAGE ARTIFACTS
            if config.extract_readonly_packages and 'packages' in download_results:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.6: EXTRACTING READ_ONLY PACKAGE ARTIFACTS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting artifacts from READ_ONLY package ZIPs...")
                logger.info("-" * 70)
                
                try:
                    extractor = ReadOnlyPackageExtractor(
                        Path(download_path),
                        timestamp=run_timestamp
                    )
                    
                    extraction_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("READ_ONLY package extraction summary:")
                    logger.info(f"  Packages processed: {extraction_stats['packages_processed']}/{extraction_stats['packages_attempted']}")
                    logger.info(f"  IFlows extracted: {extraction_stats['iflows_extracted']}")
                    logger.info(f"  Script collections extracted: {extraction_stats['script_collections_extracted']}")
                    logger.info(f"  Message mappings extracted: {extraction_stats['message_mappings_extracted']}")
                    logger.info(f"  Value mappings extracted: {extraction_stats['value_mappings_extracted']}")
                    logger.info(f"  Total artifacts extracted: {extraction_stats['total_artifacts']}")
                    
                    if extraction_stats['packages_failed'] > 0:
                        logger.warning(f"  Failed to process {extraction_stats['packages_failed']} packages")
                        logger.warning("  Check readonly-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("READ_ONLY package extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"READ_ONLY package extraction failed: {e}")
                    logger.warning("Continuing without READ_ONLY package extraction...")
            elif not config.extract_readonly_packages:
                logger.info("")
                logger.info("READ_ONLY package extraction disabled (EXTRACT_READONLY_PACKAGES=false)")
            else:
                logger.info("")
                logger.info("Skipping READ_ONLY package extraction (packages not downloaded)")
        
            # PHASE 1.7: EXTRACT IFLOW CONTENT FILES
            if config.extract_iflow_content and config.download_artifact_zips:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.7: EXTRACTING IFLOW CONTENT FILES")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting content files from IFlow ZIPs...")
                logger.info("(IFLW, scripts, mappings, schemas, archives)")
                logger.info("-" * 70)
                
                try:
                    from downloader.iflow_zip_extractor import IFlowZipExtractor
                    
                    extractor = IFlowZipExtractor(
                        Path(download_path),
                        timestamp=run_timestamp
                    )
                    
                    extraction_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("IFlow content extraction summary:")
                    logger.info(f"  IFlow ZIPs processed: {extraction_stats['iflow_zips_processed']}/{extraction_stats['iflow_zips_attempted']}")
                    logger.info(f"  IFLW files: {extraction_stats['iflw_files']}")
                    logger.info(f"  Groovy scripts: {extraction_stats['groovy_scripts']}")
                    logger.info(f"  JavaScript files: {extraction_stats['javascript_files']}")
                    logger.info(f"  Message mappings: {extraction_stats['message_mappings']}")
                    logger.info(f"  XSLT mappings: {extraction_stats['xslt_mappings']}")
                    logger.info(f"  Other mappings: {extraction_stats['other_mappings']}")
                    logger.info(f"  EDMX schemas: {extraction_stats['edmx_schemas']}")
                    logger.info(f"  XSD schemas: {extraction_stats['xsd_schemas']}")
                    logger.info(f"  WSDL schemas: {extraction_stats['wsdl_schemas']}")
                    logger.info(f"  JSON schemas: {extraction_stats['json_schemas']}")
                    logger.info(f"  Archive files: {extraction_stats['archive_files']}")
                    logger.info(f"  Total files extracted: {extraction_stats['total_files_extracted']}")
                    
                    if extraction_stats['iflow_zips_failed'] > 0:
                        logger.warning(f"  Failed to process {extraction_stats['iflow_zips_failed']} IFlow ZIPs")
                        logger.warning("  Check iflow-content-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("IFlow content extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"IFlow content extraction failed: {e}")
                    logger.warning("Continuing without IFlow content extraction...")
            elif not config.extract_iflow_content:
                logger.info("")
                logger.info("IFlow content extraction disabled (EXTRACT_IFLOW_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping IFlow content extraction (Artifact ZIPs not downloaded)")
            
            # PHASE 1.8: EXTRACT ARTIFACT CONTENT FILES
            if config.download_artifact_zips and (config.extract_script_collection_content or 
                                                   config.extract_message_mapping_content or 
                                                   config.extract_value_mapping_content):
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.8: EXTRACTING ARTIFACT CONTENT FILES")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting content files from artifact ZIPs...")
                logger.info("(Script Collections, Message Mappings, Value Mappings)")
                logger.info("-" * 70)
                
                try:
                    from downloader.artifact_content_extractor import (
                        ScriptCollectionExtractor,
                        MessageMappingExtractor,
                        ValueMappingExtractor
                    )
                    
                    total_extracted = 0
                    
                    # Extract Script Collection content
                    if config.extract_script_collection_content:
                        logger.info("")
                        logger.info("Extracting Script Collection content...")
                        extractor = ScriptCollectionExtractor(
                            Path(download_path),
                            timestamp=run_timestamp
                        )
                        sc_stats = extractor.extract_all()
                        total_extracted += sc_stats['total_files_extracted']
                        
                        logger.info(f"  Script Collections processed: {sc_stats['script_collections_processed']}/{sc_stats['script_collections_attempted']}")
                        logger.info(f"  Groovy scripts: {sc_stats['groovy_scripts_extracted']}")
                        logger.info(f"  JavaScript files: {sc_stats['java_scripts_extracted']}")
                        logger.info(f"  Library files: {sc_stats['libraries_extracted']}")
                        logger.info(f"  Total files extracted: {sc_stats['total_files_extracted']}")
                        
                        if sc_stats['script_collections_failed'] > 0:
                            logger.warning(f"  Failed: {sc_stats['script_collections_failed']} script collections")
                    
                    # Extract Message Mapping content
                    if config.extract_message_mapping_content:
                        logger.info("")
                        logger.info("Extracting Message Mapping content...")
                        extractor = MessageMappingExtractor(
                            Path(download_path),
                            timestamp=run_timestamp
                        )
                        mm_stats = extractor.extract_all()
                        total_extracted += mm_stats['mapping_files_extracted']
                        
                        logger.info(f"  Message Mappings processed: {mm_stats['message_mappings_processed']}/{mm_stats['message_mappings_attempted']}")
                        logger.info(f"  Mapping files extracted: {mm_stats['mapping_files_extracted']}")
                        
                        if mm_stats['message_mappings_failed'] > 0:
                            logger.warning(f"  Failed: {mm_stats['message_mappings_failed']} message mappings")
                    
                    # Extract Value Mapping content
                    if config.extract_value_mapping_content:
                        logger.info("")
                        logger.info("Extracting Value Mapping content...")
                        extractor = ValueMappingExtractor(
                            Path(download_path),
                            timestamp=run_timestamp
                        )
                        vm_stats = extractor.extract_all()
                        total_extracted += vm_stats['xml_files_extracted']
                        
                        logger.info(f"  Value Mappings processed: {vm_stats['value_mappings_processed']}/{vm_stats['value_mappings_attempted']}")
                        logger.info(f"  XML files extracted: {vm_stats['xml_files_extracted']}")
                        
                        if vm_stats['value_mappings_failed'] > 0:
                            logger.warning(f"  Failed: {vm_stats['value_mappings_failed']} value mappings")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info(f"Total files extracted from artifacts: {total_extracted}")
                    logger.info("Artifact content extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"Artifact content extraction failed: {e}")
                    logger.warning("Continuing without artifact content extraction...")
            elif not config.download_artifact_zips:
                logger.info("")
                logger.info("Skipping artifact content extraction (Artifact ZIPs not downloaded)")
            else:
                logger.info("")
                logger.info("Artifact content extraction disabled (all extractors set to false)")
            
            # PHASE 1.9.1: EXTRACT BPMN PARTICIPANTS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.1: EXTRACTING BPMN PARTICIPANTS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting participant information from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_participant_extractor import BpmnParticipantExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    extractor = BpmnParticipantExtractor(
                        iflw_files_dir=iflw_dir,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    participant_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("BPMN participant extraction summary:")
                    logger.info(f"  IFLW files processed: {participant_stats['iflw_files_processed']}/{participant_stats['iflw_files_attempted']}")
                    logger.info(f"  Total participants extracted: {participant_stats['total_participants_extracted']}")
                    logger.info(f"  Participants by type:")
                    logger.info(f"    EndpointSender: {participant_stats['participants_by_type']['EndpointSender']}")
                    logger.info(f"    EndpointReceiver: {participant_stats['participants_by_type']['EndpointReceiver']}")
                    logger.info(f"    IntegrationProcess: {participant_stats['participants_by_type']['IntegrationProcess']}")
                    logger.info(f"    Unknown: {participant_stats['participants_by_type']['Unknown']}")
                    
                    if participant_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {participant_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-participant-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN participant extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN participant extraction failed: {e}")
                    logger.warning("Continuing without BPMN participant extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN participant extraction (IFlow content not extracted)")
            
            # PHASE 1.9.2: EXTRACT BPMN CHANNELS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.2: EXTRACTING BPMN CHANNELS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting communication channels from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_channel_extractor import BpmnChannelExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    participants_file = Path(download_path) / "iflows" / "bpmn-json-files" / "bpmn-participants.json"
                    configurations_file = Path(download_path) / "json-files" / "configurations.json"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    extractor = BpmnChannelExtractor(
                        iflw_files_dir=iflw_dir,
                        participants_file=participants_file,
                        configurations_file=configurations_file,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    channel_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("BPMN channel extraction summary:")
                    logger.info(f"  IFLW files processed: {channel_stats['iflw_files_processed']}/{channel_stats['iflw_files_attempted']}")
                    logger.info(f"  Total channels extracted: {channel_stats['total_channels_extracted']}")
                    logger.info(f"  Total properties extracted: {channel_stats['total_properties_extracted']}")
                    logger.info(f"  Channels by type:")
                    logger.info(f"    EndpointSender: {channel_stats['channels_by_type']['EndpointSender']}")
                    logger.info(f"    EndpointReceiver: {channel_stats['channels_by_type']['EndpointReceiver']}")
                    
                    if channel_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {channel_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-channel-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN channel extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN channel extraction failed: {e}")
                    logger.warning("Continuing without BPMN channel extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN channel extraction (IFlow content not extracted)")
            
            # PHASE 1.9.3: EXTRACT BPMN ACTIVITIES
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.3: EXTRACTING BPMN ACTIVITIES")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting process activities from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_activity_extractor import BpmnActivityExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    configurations_file = Path(download_path) / "json-files" / "configurations.json"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    extractor = BpmnActivityExtractor(
                        iflw_files_dir=iflw_dir,
                        configurations_file=configurations_file,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    activity_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("BPMN activity extraction summary:")
                    logger.info(f"  IFLW files processed: {activity_stats['iflw_files_processed']}/{activity_stats['iflw_files_attempted']}")
                    logger.info(f"  Total activities extracted: {activity_stats['total_activities_extracted']}")
                    logger.info(f"  Total properties extracted: {activity_stats['total_properties_extracted']}")
                    
                    if activity_stats['activities_by_type']:
                        logger.info(f"  Activities by type:")
                        for activity_type, count in sorted(activity_stats['activities_by_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
                            logger.info(f"    {activity_type}: {count}")
                        if len(activity_stats['activities_by_type']) > 10:
                            logger.info(f"    ... and {len(activity_stats['activities_by_type']) - 10} more types")
                    
                    if activity_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {activity_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-activity-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN activity extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN activity extraction failed: {e}")
                    logger.warning("Continuing without BPMN activity extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN activity analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN activity extraction (IFlow content not extracted)")
            
            # PHASE 1.9.4: EXTRACT GROOVY SCRIPTS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.4: EXTRACTING GROOVY SCRIPTS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting Groovy script activities from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_script_extractor import BpmnScriptExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    extractor = BpmnScriptExtractor(
                        iflw_files_dir=iflw_dir,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    script_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("BPMN Groovy script extraction summary:")
                    logger.info(f"  IFLW files processed: {script_stats['iflw_files_processed']}/{script_stats['iflw_files_attempted']}")
                    logger.info(f"  Total Groovy scripts extracted: {script_stats['total_scripts_extracted']}")
                    logger.info(f"    Inline scripts: {script_stats['inline_scripts']}")
                    logger.info(f"    Bundle scripts: {script_stats['bundle_scripts']}")
                    
                    if script_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {script_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-script-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN Groovy script extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN Groovy script extraction failed: {e}")
                    logger.warning("Continuing without BPMN Groovy script extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN script analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN Groovy script extraction (IFlow content not extracted)")
            
            # PHASE 1.9.5: EXTRACT MESSAGE MAPPINGS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.5: EXTRACTING MESSAGE MAPPINGS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting message mapping activities from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_message_mapping_extractor import BpmnMessageMappingExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    extractor = BpmnMessageMappingExtractor(
                        iflw_files_dir=iflw_dir,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    mapping_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("BPMN message mapping extraction summary:")
                    logger.info(f"  IFLW files processed: {mapping_stats['iflw_files_processed']}/{mapping_stats['iflw_files_attempted']}")
                    logger.info(f"  Total message mappings extracted: {mapping_stats['total_mappings_extracted']}")
                    
                    if mapping_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {mapping_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-message-mapping-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN message mapping extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN message mapping extraction failed: {e}")
                    logger.warning("Continuing without BPMN message mapping extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN message mapping analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN message mapping extraction (IFlow content not extracted)")
            
            # PHASE 1.9.6: EXTRACT XSLT MAPPINGS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.6: EXTRACTING XSLT MAPPINGS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting XSLT mapping activities from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_xslt_mapping_extractor import BpmnXSLTMappingExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    extractor = BpmnXSLTMappingExtractor(
                        iflw_files_dir=iflw_dir,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    xslt_stats = extractor.extract_all()
                    
                    logger.info("")
                    logger.info("BPMN XSLT mapping extraction summary:")
                    logger.info(f"  IFLW files processed: {xslt_stats['iflw_files_processed']}/{xslt_stats['iflw_files_attempted']}")
                    logger.info(f"  Total XSLT mappings extracted: {xslt_stats['total_mappings_extracted']}")
                    
                    if xslt_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {xslt_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-xslt-mapping-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN XSLT mapping extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN XSLT mapping extraction failed: {e}")
                    logger.warning("Continuing without BPMN XSLT mapping extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN XSLT mapping analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN XSLT mapping extraction (IFlow content not extracted)")
            
            # PHASE 1.9.7: EXTRACT CONTENT MODIFIERS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.7: EXTRACTING CONTENT MODIFIERS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting content modifier (enricher) activities from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_content_modifier_extractor import BpmnContentModifierExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    # Load configurations for placeholder resolution
                    configurations = None
                    config_file = Path(download_path) / "json-files" / "configurations.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config_data = json.load(f)
                            
                            # Build configuration dictionary: iflow_id -> {key: value}
                            configurations = {}
                            results = config_data.get('d', {}).get('results', [])
                            for cfg in results:
                                iflow_id = cfg.get('IflowId')  # Use IflowId not ArtifactSymbolicName
                                param_key = cfg.get('ParameterKey')
                                param_value = cfg.get('ParameterValue')
                                
                                if iflow_id and param_key:
                                    if iflow_id not in configurations:
                                        configurations[iflow_id] = {}
                                    configurations[iflow_id][param_key] = param_value or ''
                            
                            logger.info(f'Loaded configurations for {len(configurations)} iflows')
                        except Exception as e:
                            logger.warning(f'Failed to load configurations: {e}')
                            configurations = None
                    
                    extractor = BpmnContentModifierExtractor(
                        iflw_files_dir=iflw_dir,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    cm_stats = extractor.extract_all(configurations)
                    
                    logger.info("")
                    logger.info("BPMN content modifier extraction summary:")
                    logger.info(f"  IFLW files processed: {cm_stats['iflw_files_processed']}/{cm_stats['iflw_files_attempted']}")
                    logger.info(f"  Total content modifier rows extracted: {cm_stats['total_modifiers_extracted']}")
                    
                    if cm_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {cm_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-content-modifier-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN content modifier extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN content modifier extraction failed: {e}")
                    logger.warning("Continuing without BPMN content modifier extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN content modifier analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN content modifier extraction (IFlow content not extracted)")
            
            # PHASE 1.9.8: EXTRACT TIMERS
            if config.parse_bpmn_content and config.extract_iflow_content:
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.9.8: EXTRACTING TIMERS")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Extracting timer configurations from IFLW files...")
                logger.info("-" * 70)
                
                try:
                    from analysers.bpmn_timer_extractor import BpmnTimerExtractor
                    
                    iflw_dir = Path(download_path) / "iflows" / "iflw-files"
                    output_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                    
                    # Load configurations for placeholder resolution
                    configurations = None
                    config_file = Path(download_path) / "json-files" / "configurations.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config_data = json.load(f)
                            
                            # Build configuration dictionary: iflow_id -> {key: value}
                            configurations = {}
                            results = config_data.get('d', {}).get('results', [])
                            for cfg in results:
                                iflow_id = cfg.get('IflowId')
                                param_key = cfg.get('ParameterKey')
                                param_value = cfg.get('ParameterValue')
                                
                                if iflow_id and param_key:
                                    if iflow_id not in configurations:
                                        configurations[iflow_id] = {}
                                    configurations[iflow_id][param_key] = param_value or ''
                            
                            logger.info(f'Loaded configurations for {len(configurations)} iflows')
                        except Exception as e:
                            logger.warning(f'Failed to load configurations: {e}')
                            configurations = None
                    
                    extractor = BpmnTimerExtractor(
                        iflw_files_dir=iflw_dir,
                        output_dir=output_dir,
                        timestamp=run_timestamp
                    )
                    
                    timer_stats = extractor.extract_all(configurations)
                    
                    logger.info("")
                    logger.info("BPMN timer extraction summary:")
                    logger.info(f"  IFLW files processed: {timer_stats['iflw_files_processed']}/{timer_stats['iflw_files_attempted']}")
                    logger.info(f"  Total timers extracted: {timer_stats['total_timers_extracted']}")
                    logger.info(f"    Event timers: {timer_stats['event_timers']}")
                    logger.info(f"    Channel timers: {timer_stats['channel_timers']}")
                    
                    if timer_stats['iflw_files_failed'] > 0:
                        logger.warning(f"  Failed to process {timer_stats['iflw_files_failed']} IFLW files")
                        logger.warning("  Check bpmn-timer-extraction-errors.json for details")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("BPMN timer extraction completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"BPMN timer extraction failed: {e}")
                    logger.warning("Continuing without BPMN timer extraction...")
            elif not config.parse_bpmn_content:
                logger.info("")
                logger.info("BPMN timer analysis disabled (PARSE_BPMN_CONTENT=false)")
            else:
                logger.info("")
                logger.info("Skipping BPMN timer extraction (IFlow content not extracted)")
            
            # PHASE 1.10: ENVIRONMENT VARIABLE SCANNING
            if (config.parse_bpmn_content or config.extract_iflow_content or 
                config.extract_script_collection_content or config.download_partner_directory):
                logger.info("")
                logger.info("=" * 70)
                logger.info("PHASE 1.10: SCANNING FOR ENVIRONMENT VARIABLES")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Scanning for HC_ environment variables in scripts and XSLTs...")
                logger.info("-" * 70)
                
                try:
                    from analysers.environment_variable_scanner import EnvironmentVariableScanner
                    
                    scanner = EnvironmentVariableScanner(
                        Path(download_path),
                        timestamp=run_timestamp
                    )
                    
                    env_var_stats = scanner.scan_all()
                    
                    logger.info("")
                    logger.info("Environment variable scan summary:")
                    logger.info(f"  Files scanned: {env_var_stats['files_scanned']}")
                    logger.info(f"  Files with HC_ variables: {env_var_stats['files_with_vars']}")
                    logger.info(f"  Unique HC_ variables found: {env_var_stats['unique_vars']}")
                    
                    if env_var_stats['by_file_type']:
                        logger.info(f"  By file type:")
                        for file_type, count in sorted(env_var_stats['by_file_type'].items()):
                            logger.info(f"    {file_type}: {count} files")
                    
                    if env_var_stats['by_parent_type']:
                        logger.info(f"  By parent type:")
                        for parent_type, count in sorted(env_var_stats['by_parent_type'].items()):
                            logger.info(f"    {parent_type}: {count} files")
                    
                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("Environment variable scanning completed!")
                    logger.info("=" * 70)
                    
                except Exception as e:
                    logger.error(f"Environment variable scanning failed: {e}")
                    logger.warning("Continuing without environment variable scan...")
            else:
                logger.info("")
                logger.info("Environment variable scanning skipped (no script files extracted)")
        
        # PHASE 2: DATABASE OPERATIONS (only in FULL mode, unless --save-only)
        if config.execution_mode == "FULL" and not args.save_only:
            logger.info("")
            logger.info("=" * 70)
            logger.info("PHASE 2: DATABASE OPERATIONS")
            logger.info("=" * 70)
            
            # Generate ISO 8601 timestamp with timezone for captured_at
            timestamp_iso = datetime.now().astimezone().isoformat()
            
            # PHASE 2.1: CREATE DATABASE SCHEMA FROM JSON FILES
            logger.info("")
            logger.info("PHASE 2.1: CREATING DATABASE SCHEMA FROM JSON FILES")
            logger.info("-" * 70)
            
            try:
                db_manager = DynamicDatabaseManager(
                    db_path=str(config.get_database_path(run_timestamp)),
                    tenant_id=config.tenant_id,
                    captured_at=timestamp_iso
                )
                
                # Define paths
                json_files_dir = Path(download_path) / "json-files"
                bpmn_json_files_dir = Path(download_path) / "iflows" / "bpmn-json-files"
                
                # Create schema from JSON files
                db_manager.create_tables_from_json_dirs(
                    odata_dir=json_files_dir,
                    bpmn_dir=bpmn_json_files_dir
                )
                
                logger.info("")
                logger.info("=" * 70)
                logger.info("Database schema creation completed!")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error(f"Database schema creation failed: {e}")
                raise
            
            # PHASE 2.2: IMPORT JSON DATA TO DATABASE
            logger.info("")
            logger.info("PHASE 2.2: IMPORTING JSON DATA TO DATABASE")
            logger.info("-" * 70)
            
            try:
                db_manager.import_all_json_files(
                    odata_dir=json_files_dir,
                    bpmn_dir=bpmn_json_files_dir
                )
                
                logger.info("")
                logger.info("=" * 70)
                logger.info("Database import completed!")
                logger.info("=" * 70)
                
                # Show database statistics
                logger.info("")
                logger.info("Database Statistics:")
                logger.info("-" * 70)
                
                tables = db_manager.list_tables()
                logger.info(f"Total tables created: {len(tables)}")
                
                # Show row counts for key tables
                for table_name in ['package', 'iflow', 'configuration', 'bpmn_activity', 'bpmn_channel']:
                    try:
                        count = db_manager.get_table_count(table_name)
                        logger.info(f"  {table_name}: {count} rows")
                    except:
                        pass  # Table might not exist
                
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error(f"Database import failed: {e}")
                raise
            
            # PHASE 3: GENERATE REPORTS (only in FULL mode)
            logger.info("")
            logger.info("=" * 70)
            logger.info("PHASE 3: REPORT GENERATION")
            logger.info("=" * 70)
            logger.info("")
            
            try:
                logger.info("Generating reports...")
                logger.info("-" * 70)
                
                from report_generators.report_types import (
                    PackageVersionComparisonReport,
                    EnvironmentVariablesReport,
                    PackageStatisticsReport
                )
                
                db_path = config.get_database_path(run_timestamp)
                reports_generated = []
                
                # Create reports directory
                reports_dir = config.get_run_dir(run_timestamp) / "reports"
                reports_dir.mkdir(exist_ok=True)
                
                # Package Version Comparison
                try:
                    report = PackageVersionComparisonReport(db_path, config.tenant_id, timestamp_iso)
                    data = report.generate()
                    
                    # Save report to JSON file
                    report_file = reports_dir / f"{report.get_report_name()}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    reports_generated.append(report.get_report_name())
                    logger.info(f"✓ Generated {report.get_report_title()}")
                    logger.info(f"  Saved to: {report_file}")
                except Exception as e:
                    logger.warning(f"Could not generate Package Version Comparison: {e}")
                
                # Environment Variables
                try:
                    report = EnvironmentVariablesReport(db_path, config.tenant_id, timestamp_iso)
                    data = report.generate()
                    
                    # Save report to JSON file
                    report_file = reports_dir / f"{report.get_report_name()}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    reports_generated.append(report.get_report_name())
                    logger.info(f"✓ Generated {report.get_report_title()}")
                    logger.info(f"  Saved to: {report_file}")
                except Exception as e:
                    logger.warning(f"Could not generate Environment Variables report: {e}")
                
                # Package Statistics
                try:
                    report = PackageStatisticsReport(db_path, config.tenant_id, timestamp_iso)
                    data = report.generate()
                    
                    # Save report to JSON file
                    report_file = reports_dir / f"{report.get_report_name()}.json"
                    with open(report_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    reports_generated.append(report.get_report_name())
                    logger.info(f"✓ Generated {report.get_report_title()}")
                    logger.info(f"  Saved to: {report_file}")
                except Exception as e:
                    logger.warning(f"Could not generate Package Statistics report: {e}")
                
                logger.info("")
                logger.info("=" * 70)
                logger.info(f"Report generation completed! ({len(reports_generated)} reports)")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Note: HTML/Excel output formatting not yet implemented")
                logger.info("Report data has been generated and validated from database")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                logger.warning("Continuing despite report generation failure...")
        
        logger.info("=" * 70)
        logger.info("Analysis completed successfully!")
        logger.info(f"Log file: {log_setup.log_file}")
        logger.info("=" * 70)
        
        print()
        print("=" * 70)
        print("[SUCCESS] Analysis completed successfully!")
        print(f"Run directory: {config.get_run_dir(run_timestamp)}")
        print(f"Log file: {log_setup.log_file}")
        print(f"Database: {config.get_database_path(run_timestamp)}")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n[WARNING] Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())