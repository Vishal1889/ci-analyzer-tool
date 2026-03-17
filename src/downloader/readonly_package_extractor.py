"""
READ_ONLY Package Artifact Extractor for SAP Cloud Integration Analyzer Tool
Extracts artifacts (IFlows, ScriptCollections, MessageMappings, ValueMappings) from READ_ONLY package ZIPs
"""

import json
import base64
from typing import Dict, Any, List
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ReadOnlyPackageExtractor:
    """Extracts artifacts from READ_ONLY package ZIP files"""
    
    def __init__(self, download_dir: Path, timestamp: str = None, error_collector=None):
        """
        Initialize READ_ONLY Package Extractor
        
        Args:
            download_dir: Base download directory (e.g., downloads/64ff97e3trial/20260228_212202)
            timestamp: Optional timestamp for organized extraction
        """
        self.download_dir = Path(download_dir)
        self.timestamp = timestamp
        self.error_collector = error_collector

        # Define source and destination directories
        self.readonly_packages_dir = self.download_dir / "read-only-packages" / "zip-files"
        self.iflows_dir = self.download_dir / "iflows" / "zip-files"
        self.script_collections_dir = self.download_dir / "script-collections" / "zip-files"
        self.message_mappings_dir = self.download_dir / "message-mappings" / "zip-files"
        self.value_mappings_dir = self.download_dir / "value-mappings" / "zip-files"
        
        # Track extraction errors
        self.errors = []
        
        logger.info("ReadOnlyPackageExtractor initialized")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all artifacts from READ_ONLY package ZIPs
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting READ_ONLY package artifact extraction...")
        
        stats = {
            "packages_attempted": 0,
            "packages_processed": 0,
            "packages_failed": 0,
            "iflows_extracted": 0,
            "script_collections_extracted": 0,
            "message_mappings_extracted": 0,
            "value_mappings_extracted": 0,
            "total_artifacts": 0
        }
        
        # Check if read-only-packages directory exists
        if not self.readonly_packages_dir.exists():
            logger.warning(f"READ_ONLY packages directory not found: {self.readonly_packages_dir}")
            return stats
        
        # Get all package ZIP files
        package_zips = list(self.readonly_packages_dir.glob("*.zip"))
        
        if not package_zips:
            logger.info("No READ_ONLY package ZIPs found to extract")
            return stats
        
        logger.info(f"Found {len(package_zips)} READ_ONLY package ZIPs to process")
        
        # Process each package ZIP
        for idx, package_zip_path in enumerate(package_zips, 1):
            package_id = package_zip_path.stem  # Filename without .zip
            logger.info(f"Processing package {idx}/{len(package_zips)}: {package_id}")
            
            stats["packages_attempted"] += 1
            
            try:
                package_stats = self._extract_package(package_zip_path, package_id)
                
                stats["packages_processed"] += 1
                stats["iflows_extracted"] += package_stats["iflows"]
                stats["script_collections_extracted"] += package_stats["script_collections"]
                stats["message_mappings_extracted"] += package_stats["message_mappings"]
                stats["value_mappings_extracted"] += package_stats["value_mappings"]
                stats["total_artifacts"] += package_stats["total"]
                
                logger.info(f"  Extracted {package_stats['total']} artifacts from {package_id}")
                
            except Exception as e:
                stats["packages_failed"] += 1
                logger.error(f"  Failed to process package {package_id}: {e}")
                self._track_error(package_id, None, None, "PACKAGE_PROCESSING", str(e))
        
        logger.info(f"Extraction completed. Processed {stats['packages_processed']}/{stats['packages_attempted']} packages")
        logger.info(f"  Extracted: {stats['iflows_extracted']} iflows, "
                   f"{stats['script_collections_extracted']} script collections, "
                   f"{stats['message_mappings_extracted']} message mappings, "
                   f"{stats['value_mappings_extracted']} value mappings")
        
        return stats
    
    def _extract_package(self, package_zip_path: Path, package_id: str) -> Dict[str, int]:
        """
        Extract artifacts from a single READ_ONLY package ZIP
        
        Args:
            package_zip_path: Path to the package ZIP file
            package_id: Package ID (filename without extension)
            
        Returns:
            Dictionary with extraction counts per artifact type
        """
        stats = {
            "iflows": 0,
            "script_collections": 0,
            "message_mappings": 0,
            "value_mappings": 0,
            "total": 0
        }
        
        try:
            with ZipFile(package_zip_path, 'r') as zip_file:
                # Step 1: Decode resources.cnt
                resources_data = self._decode_resources_cnt(zip_file, package_id)
                
                if not resources_data:
                    logger.warning(f"  Could not decode resources.cnt for {package_id}")
                    return stats
                
                # Step 2: Extract artifacts from resources
                resources = resources_data.get('resources', [])
                
                if not resources:
                    logger.warning(f"  No resources found in {package_id}")
                    return stats
                
                logger.info(f"  Found {len(resources)} resources in metadata")
                
                # Step 3: Process each resource
                for resource in resources:
                    resource_type = resource.get('resourceType')
                    
                    # Skip ContentPackage entries
                    if resource_type == 'ContentPackage':
                        continue
                    
                    # Skip unsupported types
                    if resource_type not in ['IFlow', 'ScriptCollection', 'MessageMapping', 'ValueMapping']:
                        logger.debug(f"  Skipping unsupported resource type: {resource_type}")
                        continue
                    
                    artifact_id = resource.get('id')
                    unique_id = resource.get('uniqueId')
                    
                    if not artifact_id or not unique_id:
                        logger.warning(f"  Missing id or uniqueId for resource in {package_id}")
                        continue
                    
                    # Extract the artifact
                    success = self._extract_artifact(zip_file, artifact_id, unique_id, 
                                                    resource_type, package_id)
                    
                    if success:
                        # Update statistics
                        if resource_type == 'IFlow':
                            stats["iflows"] += 1
                        elif resource_type == 'ScriptCollection':
                            stats["script_collections"] += 1
                        elif resource_type == 'MessageMapping':
                            stats["message_mappings"] += 1
                        elif resource_type == 'ValueMapping':
                            stats["value_mappings"] += 1
                        
                        stats["total"] += 1
                
        except Exception as e:
            logger.error(f"  Error processing package ZIP {package_id}: {e}")
            self._track_error(package_id, None, None, "ZIP_PROCESSING", str(e))
            raise
        
        return stats
    
    def _decode_resources_cnt(self, zip_file: ZipFile, package_id: str) -> Dict[str, Any]:
        """
        Decode resources.cnt file from package ZIP
        
        Args:
            zip_file: Open ZipFile object
            package_id: Package ID for error tracking
            
        Returns:
            Decoded JSON data or None if failed
        """
        try:
            # Check if resources.cnt exists
            if 'resources.cnt' not in zip_file.namelist():
                logger.warning(f"  resources.cnt not found in {package_id}")
                self._track_error(package_id, None, None, "MISSING_RESOURCES_CNT", 
                                "resources.cnt file not found in package ZIP")
                return None
            
            # Read resources.cnt
            resources_cnt_data = zip_file.read('resources.cnt')
            
            # Decode base64
            try:
                decoded_data = base64.b64decode(resources_cnt_data)
            except Exception as e:
                logger.error(f"  Failed to decode base64 in {package_id}: {e}")
                self._track_error(package_id, None, None, "BASE64_DECODE_ERROR", str(e))
                return None
            
            # Parse JSON
            try:
                json_data = json.loads(decoded_data.decode('utf-8'))
                return json_data
            except Exception as e:
                logger.error(f"  Failed to parse JSON in {package_id}: {e}")
                self._track_error(package_id, None, None, "JSON_PARSE_ERROR", str(e))
                return None
                
        except Exception as e:
            logger.error(f"  Error reading resources.cnt from {package_id}: {e}")
            self._track_error(package_id, None, None, "RESOURCES_CNT_READ_ERROR", str(e))
            return None
    
    def _extract_artifact(self, zip_file: ZipFile, artifact_id: str, unique_id: str,
                         resource_type: str, package_id: str) -> bool:
        """
        Extract a single artifact content file from package ZIP
        
        Args:
            zip_file: Open ZipFile object
            artifact_id: Artifact ID (used to find content file)
            unique_id: Unique ID (used in output filename)
            resource_type: Type of artifact (IFlow, ScriptCollection, etc.)
            package_id: Package ID
            
        Returns:
            True if successful, False otherwise
        """
        # Determine content filename
        content_filename = f"{artifact_id}_content"
        
        # Check if content file exists in ZIP
        if content_filename not in zip_file.namelist():
            logger.warning(f"  Content file not found: {content_filename} for {unique_id}")
            self._track_error(package_id, artifact_id, unique_id, "MISSING_CONTENT_FILE",
                            f"Content file {content_filename} not found in package ZIP")
            return False
        
        # Determine destination directory
        if resource_type == 'IFlow':
            dest_dir = self.iflows_dir
        elif resource_type == 'ScriptCollection':
            dest_dir = self.script_collections_dir
        elif resource_type == 'MessageMapping':
            dest_dir = self.message_mappings_dir
        elif resource_type == 'ValueMapping':
            dest_dir = self.value_mappings_dir
        else:
            logger.warning(f"  Unknown resource type: {resource_type}")
            return False
        
        # Create destination directory if it doesn't exist
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output filename
        output_filename = f"{package_id}---{unique_id}.zip"
        output_path = dest_dir / output_filename
        
        try:
            # Extract content file
            content_data = zip_file.read(content_filename)
            
            # Write to destination
            with open(output_path, 'wb') as f:
                f.write(content_data)
            
            file_size = output_path.stat().st_size
            logger.debug(f"    Extracted: {output_filename} ({file_size / 1024:.1f} KB)")
            
            return True
            
        except Exception as e:
            logger.error(f"  Failed to extract {content_filename}: {e}")
            self._track_error(package_id, artifact_id, unique_id, "EXTRACTION_ERROR", str(e))
            return False
    
    def _track_error(self, package_id: str, artifact_id: str, unique_id: str,
                    error_type: str, error_message: str):
        """Track extraction error for later reporting"""
        error_record = {
            "PackageID": package_id,
            "ArtifactID": artifact_id,
            "UniqueID": unique_id,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],  # Limit message length
            "Timestamp": datetime.now().isoformat()
        }

        self.errors.append(error_record)

        # Forward to centralized error collector
        if self.error_collector:
            self.error_collector.add_error(
                package_id=package_id,
                artifact_type='READ_ONLY_PACKAGE',
                error_code=0,
                error_type=error_type,
                error_message=error_message[:500],
                iflow_id=artifact_id or '',
                version=unique_id or ''
            )
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        output_file = self.download_dir / "readonly-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log with {len(self.errors)} errors: readonly-extraction-errors.json")