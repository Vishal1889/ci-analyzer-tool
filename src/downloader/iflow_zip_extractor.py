"""
IFlow ZIP Content Extractor for SAP Cloud Integration Analyzer Tool
Extracts specific file types from IFlow ZIP archives and organizes them into dedicated directories
"""

import json
from typing import Dict, Any, Tuple, List
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from datetime import datetime
from utils.logger import get_logger
from utils.filename_sanitizer import sanitize_chars, sanitize_source_name

logger = get_logger(__name__)


class IFlowZipExtractor:
    """Extracts content files (IFLW, scripts, mappings, schemas, archives) from IFlow ZIP archives"""
    
    def __init__(self, download_dir: Path, timestamp: str = None, error_collector=None):
        """
        Initialize IFlow ZIP Content Extractor
        
        Args:
            download_dir: Base download directory (e.g., downloads/)
            timestamp: Optional timestamp for organized extraction
        """
        self.download_dir = Path(download_dir)
        self.timestamp = timestamp
        self.error_collector = error_collector
        
        # Source directory containing IFlow ZIPs
        self.iflows_zip_dir = self.download_dir / "iflows" / "zip-files"
        
        # Define all target directories
        self.target_dirs = {
            'iflw': self.download_dir / "iflows" / "iflw-files",
            'groovy': self.download_dir / "iflows" / "groovy-scripts",
            'javascript': self.download_dir / "iflows" / "java-scripts",
            'mmap': self.download_dir / "iflows" / "message-mappings",
            'xslt': self.download_dir / "iflows" / "xslts",
            'other_mappings': self.download_dir / "iflows" / "other-mappings",
            'edmx': self.download_dir / "iflows" / "schemas" / "edmx",
            'xsd': self.download_dir / "iflows" / "schemas" / "xsd",
            'wsdl': self.download_dir / "iflows" / "schemas" / "wsdl",
            'json_schema': self.download_dir / "iflows" / "schemas" / "json",
            'archives': self.download_dir / "iflows" / "archives"
        }
        
        # Track extraction errors
        self.errors = []
        
        logger.info("IFlowZipExtractor initialized")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract content files from all IFlow ZIP archives
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting IFlow ZIP content extraction...")
        
        stats = {
            "iflow_zips_attempted": 0,
            "iflow_zips_processed": 0,
            "iflow_zips_failed": 0,
            "iflw_files": 0,
            "groovy_scripts": 0,
            "javascript_files": 0,
            "message_mappings": 0,
            "xslt_mappings": 0,
            "other_mappings": 0,
            "edmx_schemas": 0,
            "xsd_schemas": 0,
            "wsdl_schemas": 0,
            "json_schemas": 0,
            "archive_files": 0,
            "total_files_extracted": 0
        }
        
        # Check if source directory exists
        if not self.iflows_zip_dir.exists():
            logger.warning(f"IFlow ZIP directory not found: {self.iflows_zip_dir}")
            return stats
        
        # Get all IFlow ZIP files
        iflow_zips = list(self.iflows_zip_dir.glob("*.zip"))
        
        if not iflow_zips:
            logger.info("No IFlow ZIP files found to extract")
            return stats
        
        logger.info(f"Found {len(iflow_zips)} IFlow ZIP files to process")
        
        # Create all target directories
        self._create_target_directories()
        
        # Process each IFlow ZIP
        for idx, zip_path in enumerate(iflow_zips, 1):
            stats["iflow_zips_attempted"] += 1
            
            try:
                # Parse package and iflow IDs from filename
                package_id, iflow_id = self._parse_zip_filename(zip_path)
                
                logger.info(f"Processing ZIP {idx}/{len(iflow_zips)}: {package_id}---{iflow_id}")
                
                # Extract content from this ZIP
                zip_stats = self._extract_iflow_zip(zip_path, package_id, iflow_id)
                
                # Aggregate statistics
                stats["iflow_zips_processed"] += 1
                stats["iflw_files"] += zip_stats["iflw"]
                stats["groovy_scripts"] += zip_stats["groovy"]
                stats["javascript_files"] += zip_stats["javascript"]
                stats["message_mappings"] += zip_stats["mmap"]
                stats["xslt_mappings"] += zip_stats["xslt"]
                stats["other_mappings"] += zip_stats["other_mappings"]
                stats["edmx_schemas"] += zip_stats["edmx"]
                stats["xsd_schemas"] += zip_stats["xsd"]
                stats["wsdl_schemas"] += zip_stats["wsdl"]
                stats["json_schemas"] += zip_stats["json_schema"]
                stats["archive_files"] += zip_stats["archives"]
                stats["total_files_extracted"] += zip_stats["total"]
                
            except Exception as e:
                stats["iflow_zips_failed"] += 1
                logger.error(f"  Failed to process {zip_path.name}: {e}")
                self._track_error(zip_path.name, "ZIP_PROCESSING", str(e))
        
        logger.info(f"Extraction completed. Processed {stats['iflow_zips_processed']}/{stats['iflow_zips_attempted']} ZIPs")
        logger.info(f"  Total files extracted: {stats['total_files_extracted']}")
        
        return stats
    
    def _create_target_directories(self):
        """Create all target directories if they don't exist"""
        for dir_name, dir_path in self.target_dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")
    
    def _parse_zip_filename(self, zip_path: Path) -> Tuple[str, str]:
        """
        Parse PackageID and IflowID from ZIP filename
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            Tuple of (package_id, iflow_id)
        """
        # Filename format: PackageID---IflowID.zip
        filename = zip_path.stem  # Remove .zip extension
        
        if '---' in filename:
            parts = filename.split('---', 1)  # Split on first occurrence only
            return parts[0], parts[1]
        else:
            # Fallback if format is unexpected
            logger.warning(f"Unexpected filename format: {filename}")
            return "Unknown", filename
    
    def _extract_iflow_zip(self, zip_path: Path, package_id: str, iflow_id: str) -> Dict[str, int]:
        """
        Extract content files from a single IFlow ZIP
        
        Args:
            zip_path: Path to the IFlow ZIP file
            package_id: Package ID
            iflow_id: IFlow ID
            
        Returns:
            Dictionary with extraction counts per category
        """
        stats = {
            "iflw": 0,
            "groovy": 0,
            "javascript": 0,
            "mmap": 0,
            "xslt": 0,
            "other_mappings": 0,
            "edmx": 0,
            "xsd": 0,
            "wsdl": 0,
            "json_schema": 0,
            "archives": 0,
            "total": 0
        }
        
        try:
            with ZipFile(zip_path, 'r') as zip_file:
                # Extract each category
                stats["iflw"] = self._extract_iflw(zip_file, package_id, iflow_id)
                stats["groovy"], stats["javascript"] = self._extract_scripts(zip_file, iflow_id)
                stats["mmap"], stats["xslt"], stats["other_mappings"] = self._extract_mappings(zip_file, iflow_id)
                stats["edmx"], stats["xsd"], stats["wsdl"], stats["json_schema"] = self._extract_schemas(zip_file, iflow_id)
                stats["archives"] = self._extract_archives(zip_file, iflow_id)
                
                # Calculate total
                stats["total"] = sum(v for k, v in stats.items() if k != "total")
                
                if stats["total"] > 0:
                    logger.info(f"  Extracted {stats['total']} files from {package_id}---{iflow_id}")
                
        except BadZipFile as e:
            logger.error(f"  Corrupt ZIP file: {zip_path.name}")
            self._track_error(zip_path.name, "BAD_ZIP", str(e))
            raise
        except Exception as e:
            logger.error(f"  Error extracting from {zip_path.name}: {e}")
            self._track_error(zip_path.name, "EXTRACTION_ERROR", str(e))
            raise
        
        return stats
    
    def _extract_iflw(self, zip_file: ZipFile, package_id: str, iflow_id: str) -> int:
        """
        Extract IFLW file from ZIP
        
        Args:
            zip_file: Open ZipFile object
            package_id: Package ID
            iflow_id: IFlow ID
            
        Returns:
            Number of files extracted
        """
        count = 0
        target_dir = self.target_dirs['iflw']
        
        # Look for IFLW file in scenarioflows/integrationflow/
        prefix = "src/main/resources/scenarioflows/integrationflow/"
        
        for file_info in zip_file.filelist:
            if file_info.filename.startswith(prefix) and file_info.filename.endswith('.iflw'):
                # Extract IFLW file
                try:
                    content = zip_file.read(file_info.filename)
                    
                    # Target filename: PackageID---IflowID.iflw
                    output_filename = f"{package_id}---{iflow_id}.iflw"
                    output_path = target_dir / output_filename
                    
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    count += 1
                    logger.debug(f"    Extracted IFLW: {output_filename}")
                    break  # Only one IFLW file expected
                    
                except Exception as e:
                    logger.error(f"    Failed to extract IFLW {file_info.filename}: {e}")
        
        return count
    
    def _extract_scripts(self, zip_file: ZipFile, iflow_id: str) -> Tuple[int, int]:
        """
        Extract script files (groovy, gsh, js) from ZIP
        
        Args:
            zip_file: Open ZipFile object
            iflow_id: IFlow ID
            
        Returns:
            Tuple of (groovy_count, javascript_count)
        """
        groovy_count = 0
        js_count = 0
        
        groovy_dir = self.target_dirs['groovy']
        js_dir = self.target_dirs['javascript']
        
        # Look for scripts in src/main/resources/script/
        prefix = "src/main/resources/script/"
        
        for file_info in zip_file.filelist:
            if file_info.filename.startswith(prefix) and not file_info.is_dir():
                try:
                    # Get source filename
                    source_name = Path(file_info.filename).name
                    
                    # Check file extension
                    if source_name.endswith(('.groovy', '.gsh')):
                        # Groovy script
                        content = zip_file.read(file_info.filename)
                        output_filename = f"{iflow_id}---{sanitize_chars(source_name)}"
                        output_path = groovy_dir / output_filename
                        
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        groovy_count += 1
                        logger.debug(f"    Extracted Groovy script: {output_filename}")
                    
                    elif source_name.endswith('.js'):
                        # JavaScript
                        content = zip_file.read(file_info.filename)
                        output_filename = f"{iflow_id}---{sanitize_chars(source_name)}"
                        output_path = js_dir / output_filename
                        
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        js_count += 1
                        logger.debug(f"    Extracted JavaScript: {output_filename}")
                
                except Exception as e:
                    logger.error(f"    Failed to extract script {file_info.filename}: {e}")
        
        return groovy_count, js_count
    
    def _extract_mappings(self, zip_file: ZipFile, iflow_id: str) -> Tuple[int, int, int]:
        """
        Extract mapping files (mmap, xslt, xsl, others) from ZIP
        Skips .info files as they are not required for analysis
        
        Args:
            zip_file: Open ZipFile object
            iflow_id: IFlow ID
            
        Returns:
            Tuple of (mmap_count, xslt_count, other_count)
        """
        mmap_count = 0
        xslt_count = 0
        other_count = 0
        
        mmap_dir = self.target_dirs['mmap']
        xslt_dir = self.target_dirs['xslt']
        other_dir = self.target_dirs['other_mappings']
        
        # Look for mappings in src/main/resources/mapping/
        prefix = "src/main/resources/mapping/"
        
        for file_info in zip_file.filelist:
            if file_info.filename.startswith(prefix) and not file_info.is_dir():
                try:
                    # Get source filename
                    source_name = Path(file_info.filename).name
                    
                    # Skip .info files - not required for analysis
                    if source_name.endswith('.info'):
                        logger.debug(f"    Skipped .info file: {source_name}")
                        continue
                    
                    content = zip_file.read(file_info.filename)
                    
                    # Determine target directory based on extension
                    if source_name.endswith('.mmap'):
                        # Message mapping
                        output_filename = f"{iflow_id}---{sanitize_source_name(source_name)}"
                        output_path = mmap_dir / output_filename
                        mmap_count += 1
                        logger.debug(f"    Extracted message mapping: {output_filename}")
                    
                    elif source_name.endswith(('.xslt', '.xsl')):
                        # XSLT mapping
                        output_filename = f"{iflow_id}---{sanitize_chars(source_name)}"
                        output_path = xslt_dir / output_filename
                        xslt_count += 1
                        logger.debug(f"    Extracted XSLT: {output_filename}")
                    
                    else:
                        # Other mapping types
                        output_filename = f"{iflow_id}---{sanitize_source_name(source_name)}"
                        output_path = other_dir / output_filename
                        other_count += 1
                        logger.debug(f"    Extracted other mapping: {output_filename}")
                    
                    with open(output_path, 'wb') as f:
                        f.write(content)
                
                except Exception as e:
                    logger.error(f"    Failed to extract mapping {file_info.filename}: {e}")
        
        return mmap_count, xslt_count, other_count
    
    def _extract_schemas(self, zip_file: ZipFile, iflow_id: str) -> Tuple[int, int, int, int]:
        """
        Extract schema files (edmx, xsd, wsdl, json) from ZIP
        
        Args:
            zip_file: Open ZipFile object
            iflow_id: IFlow ID
            
        Returns:
            Tuple of (edmx_count, xsd_count, wsdl_count, json_count)
        """
        edmx_count = 0
        xsd_count = 0
        wsdl_count = 0
        json_count = 0
        
        # Define schema paths and their target directories
        schema_configs = [
            ("src/main/resources/edmx/", self.target_dirs['edmx'], 'edmx'),
            ("src/main/resources/xsd/", self.target_dirs['xsd'], 'xsd'),
            ("src/main/resources/wsdl/", self.target_dirs['wsdl'], 'wsdl'),
            ("src/main/resources/json/", self.target_dirs['json_schema'], 'json')
        ]
        
        for prefix, target_dir, schema_type in schema_configs:
            for file_info in zip_file.filelist:
                if file_info.filename.startswith(prefix) and not file_info.is_dir():
                    try:
                        # Get source filename
                        source_name = Path(file_info.filename).name
                        content = zip_file.read(file_info.filename)
                        
                        # Create output filename
                        output_filename = f"{iflow_id}---{sanitize_source_name(source_name)}"
                        output_path = target_dir / output_filename

                        with open(output_path, 'wb') as f:
                            f.write(content)

                        # Increment appropriate counter
                        if schema_type == 'edmx':
                            edmx_count += 1
                        elif schema_type == 'xsd':
                            xsd_count += 1
                        elif schema_type == 'wsdl':
                            wsdl_count += 1
                        elif schema_type == 'json':
                            json_count += 1
                        
                        logger.debug(f"    Extracted {schema_type.upper()} schema: {output_filename}")
                    
                    except Exception as e:
                        logger.error(f"    Failed to extract {schema_type} schema {file_info.filename}: {e}")
        
        return edmx_count, xsd_count, wsdl_count, json_count
    
    def _extract_archives(self, zip_file: ZipFile, iflow_id: str) -> int:
        """
        Extract archive/library files from ZIP
        
        Args:
            zip_file: Open ZipFile object
            iflow_id: IFlow ID
            
        Returns:
            Number of files extracted
        """
        count = 0
        target_dir = self.target_dirs['archives']
        
        # Look for libraries in src/main/resources/lib/
        prefix = "src/main/resources/lib/"
        
        for file_info in zip_file.filelist:
            if file_info.filename.startswith(prefix) and not file_info.is_dir():
                try:
                    # Get source filename
                    source_name = Path(file_info.filename).name
                    content = zip_file.read(file_info.filename)
                    
                    # Create output filename
                    output_filename = f"{iflow_id}---{sanitize_source_name(source_name)}"
                    output_path = target_dir / output_filename

                    with open(output_path, 'wb') as f:
                        f.write(content)

                    count += 1
                    logger.debug(f"    Extracted archive: {output_filename}")
                
                except Exception as e:
                    logger.error(f"    Failed to extract archive {file_info.filename}: {e}")
        
        return count
    
    def _track_error(self, zip_name: str, error_type: str, error_message: str):
        """Track extraction error for later reporting"""
        error_record = {
            "ZipFile": zip_name,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],  # Limit message length
            "Timestamp": datetime.now().isoformat()
        }

        self.errors.append(error_record)

        # Forward to centralized error collector
        if self.error_collector:
            # Parse package_id and iflow_id from zip_name (format: PackageID---IflowID.zip)
            stem = zip_name.rsplit('.', 1)[0] if '.' in zip_name else zip_name
            if '---' in stem:
                package_id, iflow_id = stem.split('---', 1)
            else:
                package_id, iflow_id = stem, ''
            self.error_collector.add_error(
                package_id=package_id,
                artifact_type='IFLOW_EXTRACTION',
                error_code=0,
                error_type=error_type,
                error_message=error_message[:500],
                iflow_id=iflow_id
            )
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        output_file = self.download_dir / "iflow-content-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log with {len(self.errors)} errors: iflow-content-extraction-errors.json")