"""
Artifact Content Extractor for SAP Cloud Integration Analyzer Tool
Extracts content files from Script Collection, Message Mapping, and Value Mapping ZIP archives
"""

import json
from typing import Dict, Any, Tuple
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ScriptCollectionExtractor:
    """Extracts script files from Script Collection ZIP archives"""
    
    def __init__(self, download_dir: Path, timestamp: str = None):
        """
        Initialize Script Collection Extractor
        
        Args:
            download_dir: Base download directory
            timestamp: Optional timestamp for organized extraction
        """
        self.download_dir = Path(download_dir)
        self.timestamp = timestamp
        
        # Source directory
        self.zip_dir = self.download_dir / "script-collections" / "zip-files"
        
        # Target directories for different file types
        self.base_target_dir = self.download_dir / "script-collections" / "extracted-files"
        self.groovy_dir = self.base_target_dir / "groovy-scripts"
        self.js_dir = self.base_target_dir / "java-scripts"
        self.lib_dir = self.base_target_dir / "libraries"
        
        # Track errors
        self.errors = []
        
        logger.info("ScriptCollectionExtractor initialized")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract script files from all Script Collection ZIPs
        Extracts to three separate directories:
        - groovy-scripts: .groovy and .gsh files from src/main/resources/script/
        - java-scripts: .js files from src/main/resources/script/
        - libraries: all files from src/main/resources/lib/
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting Script Collection content extraction...")
        
        stats = {
            "script_collections_attempted": 0,
            "script_collections_processed": 0,
            "script_collections_failed": 0,
            "groovy_scripts_extracted": 0,
            "java_scripts_extracted": 0,
            "libraries_extracted": 0,
            "total_files_extracted": 0
        }
        
        # Check if source directory exists
        if not self.zip_dir.exists():
            logger.warning(f"Script Collection ZIP directory not found: {self.zip_dir}")
            return stats
        
        # Get all ZIP files
        zip_files = list(self.zip_dir.glob("*.zip"))
        
        if not zip_files:
            logger.info("No Script Collection ZIP files found")
            return stats
        
        logger.info(f"Found {len(zip_files)} Script Collection ZIP files to process")
        
        # Create target directories
        self.groovy_dir.mkdir(parents=True, exist_ok=True)
        self.js_dir.mkdir(parents=True, exist_ok=True)
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each ZIP
        for idx, zip_path in enumerate(zip_files, 1):
            stats["script_collections_attempted"] += 1
            
            try:
                # Parse artifact ID from filename: PackageID---ScriptCollectionID.zip
                artifact_id = self._parse_artifact_id(zip_path)
                
                logger.info(f"Processing {idx}/{len(zip_files)}: {artifact_id}")
                
                # Extract content
                groovy_count, js_count, lib_count = self._extract_scripts(zip_path, artifact_id)
                
                stats["script_collections_processed"] += 1
                stats["groovy_scripts_extracted"] += groovy_count
                stats["java_scripts_extracted"] += js_count
                stats["libraries_extracted"] += lib_count
                stats["total_files_extracted"] += groovy_count + js_count + lib_count
                
                if groovy_count + js_count + lib_count > 0:
                    logger.info(f"  Extracted {groovy_count} Groovy, {js_count} JavaScript, {lib_count} library files")
                
            except Exception as e:
                stats["script_collections_failed"] += 1
                logger.error(f"  Failed to process {zip_path.name}: {e}")
                self._track_error(zip_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"Script Collection extraction completed. Processed {stats['script_collections_processed']}/{stats['script_collections_attempted']}")
        logger.info(f"  Groovy scripts: {stats['groovy_scripts_extracted']}, JavaScript: {stats['java_scripts_extracted']}, Libraries: {stats['libraries_extracted']}")
        
        return stats
    
    def _parse_artifact_id(self, zip_path: Path) -> str:
        """Extract artifact ID from filename"""
        filename = zip_path.stem
        if '---' in filename:
            return filename.split('---', 1)[1]
        return filename
    
    def _extract_scripts(self, zip_path: Path, artifact_id: str) -> Tuple[int, int, int]:
        """
        Extract script files from ZIP into three separate directories
        
        Args:
            zip_path: Path to ZIP file
            artifact_id: Script Collection ID
            
        Returns:
            Tuple of (groovy_count, js_count, lib_count)
        """
        groovy_count = 0
        js_count = 0
        lib_count = 0
        
        script_prefix = "src/main/resources/script/"
        lib_prefix = "src/main/resources/lib/"
        
        try:
            with ZipFile(zip_path, 'r') as zip_file:
                for file_info in zip_file.filelist:
                    if file_info.is_dir():
                        continue
                    
                    file_path = file_info.filename
                    source_name = Path(file_path).name
                    
                    try:
                        # Check if it's a Groovy script (.groovy or .gsh)
                        if file_path.startswith(script_prefix) and (source_name.endswith('.groovy') or source_name.endswith('.gsh')):
                            content = zip_file.read(file_info.filename)
                            output_filename = f"{artifact_id}---{source_name}"
                            output_path = self.groovy_dir / output_filename
                            
                            with open(output_path, 'wb') as f:
                                f.write(content)
                            
                            groovy_count += 1
                            logger.debug(f"    Extracted Groovy script: {output_filename}")
                        
                        # Check if it's a JavaScript file (.js)
                        elif file_path.startswith(script_prefix) and source_name.endswith('.js'):
                            content = zip_file.read(file_info.filename)
                            output_filename = f"{artifact_id}---{source_name}"
                            output_path = self.js_dir / output_filename
                            
                            with open(output_path, 'wb') as f:
                                f.write(content)
                            
                            js_count += 1
                            logger.debug(f"    Extracted JavaScript: {output_filename}")
                        
                        # Check if it's a library file (any extension in lib directory)
                        elif file_path.startswith(lib_prefix):
                            content = zip_file.read(file_info.filename)
                            output_filename = f"{artifact_id}---{source_name}"
                            output_path = self.lib_dir / output_filename
                            
                            with open(output_path, 'wb') as f:
                                f.write(content)
                            
                            lib_count += 1
                            logger.debug(f"    Extracted library: {output_filename}")
                    
                    except Exception as e:
                        logger.error(f"    Failed to extract {file_info.filename}: {e}")
        
        except BadZipFile as e:
            logger.error(f"  Corrupt ZIP file: {zip_path.name}")
            self._track_error(zip_path.name, "BAD_ZIP", str(e))
            raise
        
        return groovy_count, js_count, lib_count
    
    def _track_error(self, zip_name: str, error_type: str, error_message: str):
        """Track extraction error"""
        self.errors.append({
            "ZipFile": zip_name,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],
            "Timestamp": datetime.now().isoformat()
        })
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        output_file = self.download_dir / "script-collection-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log: script-collection-extraction-errors.json")


class MessageMappingExtractor:
    """Extracts mapping files from Message Mapping ZIP archives"""
    
    def __init__(self, download_dir: Path, timestamp: str = None):
        """
        Initialize Message Mapping Extractor
        
        Args:
            download_dir: Base download directory
            timestamp: Optional timestamp for organized extraction
        """
        self.download_dir = Path(download_dir)
        self.timestamp = timestamp
        
        # Source and target directories
        self.zip_dir = self.download_dir / "message-mappings" / "zip-files"
        self.target_dir = self.download_dir / "message-mappings" / "extracted-files"
        
        # Track errors
        self.errors = []
        
        logger.info("MessageMappingExtractor initialized")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract mapping files from all Message Mapping ZIPs
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting Message Mapping content extraction...")
        
        stats = {
            "message_mappings_attempted": 0,
            "message_mappings_processed": 0,
            "message_mappings_failed": 0,
            "mapping_files_extracted": 0
        }
        
        # Check if source directory exists
        if not self.zip_dir.exists():
            logger.warning(f"Message Mapping ZIP directory not found: {self.zip_dir}")
            return stats
        
        # Get all ZIP files
        zip_files = list(self.zip_dir.glob("*.zip"))
        
        if not zip_files:
            logger.info("No Message Mapping ZIP files found")
            return stats
        
        logger.info(f"Found {len(zip_files)} Message Mapping ZIP files to process")
        
        # Create target directory
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each ZIP
        for idx, zip_path in enumerate(zip_files, 1):
            stats["message_mappings_attempted"] += 1
            
            try:
                # Parse artifact ID from filename: PackageID---MessageMappingID.zip
                artifact_id = self._parse_artifact_id(zip_path)
                
                logger.info(f"Processing {idx}/{len(zip_files)}: {artifact_id}")
                
                # Extract content
                count = self._extract_mappings(zip_path, artifact_id)
                
                stats["message_mappings_processed"] += 1
                stats["mapping_files_extracted"] += count
                
                if count > 0:
                    logger.info(f"  Extracted {count} mapping files")
                
            except Exception as e:
                stats["message_mappings_failed"] += 1
                logger.error(f"  Failed to process {zip_path.name}: {e}")
                self._track_error(zip_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"Message Mapping extraction completed. Processed {stats['message_mappings_processed']}/{stats['message_mappings_attempted']}")
        
        return stats
    
    def _parse_artifact_id(self, zip_path: Path) -> str:
        """Extract artifact ID from filename"""
        filename = zip_path.stem
        if '---' in filename:
            return filename.split('---', 1)[1]
        return filename
    
    def _extract_mappings(self, zip_path: Path, artifact_id: str) -> int:
        """Extract mapping files from ZIP"""
        count = 0
        prefix = "src/main/resources/mapping/"
        
        try:
            with ZipFile(zip_path, 'r') as zip_file:
                for file_info in zip_file.filelist:
                    if file_info.filename.startswith(prefix) and not file_info.is_dir():
                        try:
                            # Get source filename
                            source_name = Path(file_info.filename).name
                            content = zip_file.read(file_info.filename)
                            
                            # Create output filename: MessageMappingID---FileName.ext
                            output_filename = f"{artifact_id}---{source_name}"
                            output_path = self.target_dir / output_filename
                            
                            with open(output_path, 'wb') as f:
                                f.write(content)
                            
                            count += 1
                            logger.debug(f"    Extracted mapping file: {output_filename}")
                        
                        except Exception as e:
                            logger.error(f"    Failed to extract {file_info.filename}: {e}")
        
        except BadZipFile as e:
            logger.error(f"  Corrupt ZIP file: {zip_path.name}")
            self._track_error(zip_path.name, "BAD_ZIP", str(e))
            raise
        
        return count
    
    def _track_error(self, zip_name: str, error_type: str, error_message: str):
        """Track extraction error"""
        self.errors.append({
            "ZipFile": zip_name,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],
            "Timestamp": datetime.now().isoformat()
        })
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        output_file = self.download_dir / "message-mapping-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log: message-mapping-extraction-errors.json")


class ValueMappingExtractor:
    """Extracts XML files from Value Mapping ZIP archives"""
    
    def __init__(self, download_dir: Path, timestamp: str = None):
        """
        Initialize Value Mapping Extractor
        
        Args:
            download_dir: Base download directory
            timestamp: Optional timestamp for organized extraction
        """
        self.download_dir = Path(download_dir)
        self.timestamp = timestamp
        
        # Source and target directories
        self.zip_dir = self.download_dir / "value-mappings" / "zip-files"
        self.target_dir = self.download_dir / "value-mappings" / "extracted-files"
        
        # Track errors
        self.errors = []
        
        logger.info("ValueMappingExtractor initialized")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract XML files from all Value Mapping ZIPs
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting Value Mapping content extraction...")
        
        stats = {
            "value_mappings_attempted": 0,
            "value_mappings_processed": 0,
            "value_mappings_failed": 0,
            "xml_files_extracted": 0
        }
        
        # Check if source directory exists
        if not self.zip_dir.exists():
            logger.warning(f"Value Mapping ZIP directory not found: {self.zip_dir}")
            return stats
        
        # Get all ZIP files
        zip_files = list(self.zip_dir.glob("*.zip"))
        
        if not zip_files:
            logger.info("No Value Mapping ZIP files found")
            return stats
        
        logger.info(f"Found {len(zip_files)} Value Mapping ZIP files to process")
        
        # Create target directory
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each ZIP
        for idx, zip_path in enumerate(zip_files, 1):
            stats["value_mappings_attempted"] += 1
            
            try:
                # Parse artifact ID from filename: PackageID---ValueMappingID.zip
                artifact_id = self._parse_artifact_id(zip_path)
                
                logger.info(f"Processing {idx}/{len(zip_files)}: {artifact_id}")
                
                # Extract content
                count = self._extract_xml_files(zip_path, artifact_id)
                
                stats["value_mappings_processed"] += 1
                stats["xml_files_extracted"] += count
                
                if count > 0:
                    logger.info(f"  Extracted {count} XML files")
                
            except Exception as e:
                stats["value_mappings_failed"] += 1
                logger.error(f"  Failed to process {zip_path.name}: {e}")
                self._track_error(zip_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"Value Mapping extraction completed. Processed {stats['value_mappings_processed']}/{stats['value_mappings_attempted']}")
        
        return stats
    
    def _parse_artifact_id(self, zip_path: Path) -> str:
        """Extract artifact ID from filename"""
        filename = zip_path.stem
        if '---' in filename:
            return filename.split('---', 1)[1]
        return filename
    
    def _extract_xml_files(self, zip_path: Path, artifact_id: str) -> int:
        """Extract XML files from ZIP root"""
        count = 0
        
        try:
            with ZipFile(zip_path, 'r') as zip_file:
                for file_info in zip_file.filelist:
                    # Check if file is at root level (no directory separators) and is XML
                    if '/' not in file_info.filename and file_info.filename.endswith('.xml') and not file_info.is_dir():
                        try:
                            # Get source filename
                            source_name = file_info.filename
                            content = zip_file.read(file_info.filename)
                            
                            # Create output filename: ValueMappingID---FileName.xml
                            output_filename = f"{artifact_id}---{source_name}"
                            output_path = self.target_dir / output_filename
                            
                            with open(output_path, 'wb') as f:
                                f.write(content)
                            
                            count += 1
                            logger.debug(f"    Extracted XML file: {output_filename}")
                        
                        except Exception as e:
                            logger.error(f"    Failed to extract {file_info.filename}: {e}")
        
        except BadZipFile as e:
            logger.error(f"  Corrupt ZIP file: {zip_path.name}")
            self._track_error(zip_path.name, "BAD_ZIP", str(e))
            raise
        
        return count
    
    def _track_error(self, zip_name: str, error_type: str, error_message: str):
        """Track extraction error"""
        self.errors.append({
            "ZipFile": zip_name,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],
            "Timestamp": datetime.now().isoformat()
        })
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        output_file = self.download_dir / "value-mapping-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log: value-mapping-extraction-errors.json")