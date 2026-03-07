"""
Environment Variable Scanner for SAP Cloud Integration Analyzer
Scans Groovy scripts, JavaScript files, and XSLTs for HC_ environment variables
"""

import json
import re
from typing import Dict, Any, List, Set, Tuple
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class EnvironmentVariableScanner:
    """Scans script files for HC_ environment variable usage"""
    
    # File extension to type mapping
    FILE_TYPE_MAP = {
        '.groovy': 'groovyScript',
        '.gsh': 'groovyScript',
        '.js': 'javascript',
        '.xsl': 'xslt',
        '.xslt': 'xslt'
    }
    
    def __init__(self, download_dir: Path, timestamp: str = None):
        """
        Initialize Environment Variable Scanner
        
        Args:
            download_dir: Base download directory
            timestamp: Optional timestamp for organized output
        """
        self.download_dir = Path(download_dir)
        self.timestamp = timestamp
        
        # Define scan directories
        self.iflow_groovy_dir = self.download_dir / "iflows" / "groovy-scripts"
        self.iflow_js_dir = self.download_dir / "iflows" / "java-scripts"
        self.iflow_xslt_dir = self.download_dir / "iflows" / "xslts"
        
        self.sc_groovy_dir = self.download_dir / "script-collections" / "extracted-files" / "groovy-scripts"
        self.sc_js_dir = self.download_dir / "script-collections" / "extracted-files" / "java-scripts"
        
        self.pd_xsl_dir = self.download_dir / "partner-directory" / "xsl"
        
        # Package lookup cache
        self.package_lookup = {}
        
        # Track errors
        self.errors = []
        
        logger.info("EnvironmentVariableScanner initialized")
    
    def scan_all(self) -> Dict[str, Any]:
        """
        Scan all script files for HC_ environment variables
        
        Returns:
            Dictionary with scanning statistics
        """
        logger.info("Starting environment variable scan...")
        
        # Load package lookup data
        self._load_package_lookup()
        
        results = []
        stats = {
            'files_scanned': 0,
            'files_with_vars': 0,
            'unique_vars': set(),
            'by_file_type': {},
            'by_parent_type': {}
        }
        
        # Scan IFlow files
        logger.info("Scanning IFlow files...")
        iflow_results = self._scan_iflow_files()
        results.extend(iflow_results)
        
        # Scan Script Collection files
        logger.info("Scanning Script Collection files...")
        sc_results = self._scan_script_collection_files()
        results.extend(sc_results)
        
        # Scan Partner Directory files
        logger.info("Scanning Partner Directory files...")
        pd_results = self._scan_partner_directory_files()
        results.extend(pd_results)
        
        # Calculate statistics
        for result in results:
            stats['files_scanned'] += 1
            
            if result['envVariableCount'] > 0:
                stats['files_with_vars'] += 1
                
                # Add unique variables
                var_list = result['envVariableList'].split('|') if result['envVariableList'] else []
                stats['unique_vars'].update(var_list)
                
                # Track by file type
                file_type = result['fileType']
                stats['by_file_type'][file_type] = stats['by_file_type'].get(file_type, 0) + 1
                
                # Track by parent type
                parent_type = result['parentType']
                stats['by_parent_type'][parent_type] = stats['by_parent_type'].get(parent_type, 0) + 1
        
        # Convert set to count
        stats['unique_vars'] = len(stats['unique_vars'])
        
        # Save results to JSON
        output_data = {
            "d": {
                "results": results
            }
        }
        
        output_file = self.download_dir / "json-files" / "environment-variable-check.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved environment variable scan results: {output_file.name}")
        logger.info(f"  Files scanned: {stats['files_scanned']}")
        logger.info(f"  Files with HC_ variables: {stats['files_with_vars']}")
        logger.info(f"  Unique variables found: {stats['unique_vars']}")
        
        return stats
    
    def _load_package_lookup(self):
        """Load package lookup data from iflows.json and script-collections.json"""
        
        # Load IFlows lookup (Id -> PackageId)
        iflows_file = self.download_dir / "json-files" / "iflows.json"
        if iflows_file.exists():
            try:
                with open(iflows_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                iflows = data.get('d', {}).get('results', [])
                iflow_count = 0
                for iflow in iflows:
                    iflow_id = iflow.get('Id')
                    package_id = iflow.get('PackageId')
                    if iflow_id and package_id:
                        self.package_lookup[iflow_id] = package_id
                        iflow_count += 1
                
                logger.info(f"Loaded {iflow_count} IFlow package mappings")
            except Exception as e:
                logger.error(f"Failed to load iflows.json: {e}")
        else:
            logger.warning("iflows.json not found")
        
        # Load Script Collections lookup (Id -> PackageId)
        sc_file = self.download_dir / "json-files" / "script-collections.json"
        if sc_file.exists():
            try:
                with open(sc_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                script_collections = data.get('d', {}).get('results', [])
                sc_count = 0
                for sc in script_collections:
                    sc_id = sc.get('Id')
                    package_id = sc.get('PackageId')
                    if sc_id and package_id:
                        self.package_lookup[sc_id] = package_id
                        sc_count += 1
                
                logger.info(f"Loaded {sc_count} Script Collection package mappings")
            except Exception as e:
                logger.error(f"Failed to load script-collections.json: {e}")
        else:
            logger.warning("script-collections.json not found")
        
        logger.info(f"Total package lookup entries: {len(self.package_lookup)}")
    
    def _scan_iflow_files(self) -> List[Dict[str, Any]]:
        """Scan IFlow script files"""
        results = []
        
        # Scan Groovy scripts
        if self.iflow_groovy_dir.exists():
            for file_path in self.iflow_groovy_dir.glob("*.groovy"):
                result = self._scan_single_file(file_path, "Iflow")
                if result:
                    results.append(result)
            
            for file_path in self.iflow_groovy_dir.glob("*.gsh"):
                result = self._scan_single_file(file_path, "Iflow")
                if result:
                    results.append(result)
        
        # Scan JavaScript files
        if self.iflow_js_dir.exists():
            for file_path in self.iflow_js_dir.glob("*.js"):
                result = self._scan_single_file(file_path, "Iflow")
                if result:
                    results.append(result)
        
        # Scan XSLT files
        if self.iflow_xslt_dir.exists():
            for file_path in self.iflow_xslt_dir.glob("*.xsl"):
                result = self._scan_single_file(file_path, "Iflow")
                if result:
                    results.append(result)
            
            for file_path in self.iflow_xslt_dir.glob("*.xslt"):
                result = self._scan_single_file(file_path, "Iflow")
                if result:
                    results.append(result)
        
        return results
    
    def _scan_script_collection_files(self) -> List[Dict[str, Any]]:
        """Scan Script Collection files"""
        results = []
        
        # Scan Groovy scripts
        if self.sc_groovy_dir.exists():
            for file_path in self.sc_groovy_dir.glob("*.groovy"):
                result = self._scan_single_file(file_path, "ScriptCollection")
                if result:
                    results.append(result)
            
            for file_path in self.sc_groovy_dir.glob("*.gsh"):
                result = self._scan_single_file(file_path, "ScriptCollection")
                if result:
                    results.append(result)
        
        # Scan JavaScript files
        if self.sc_js_dir.exists():
            for file_path in self.sc_js_dir.glob("*.js"):
                result = self._scan_single_file(file_path, "ScriptCollection")
                if result:
                    results.append(result)
        
        return results
    
    def _scan_partner_directory_files(self) -> List[Dict[str, Any]]:
        """Scan Partner Directory XSL files"""
        results = []
        
        if self.pd_xsl_dir.exists():
            for file_path in self.pd_xsl_dir.glob("*.xsl"):
                result = self._scan_single_file(file_path, "PartnerDirectory")
                if result:
                    results.append(result)
        
        return results
    
    def _scan_single_file(self, file_path: Path, parent_type: str) -> Dict[str, Any]:
        """
        Scan a single file for HC_ environment variables
        
        Args:
            file_path: Path to the file
            parent_type: Type of parent (Iflow, ScriptCollection, PartnerDirectory)
            
        Returns:
            Dictionary with scan result
        """
        try:
            # Parse filename to get parent name
            parent_name, extension = self._parse_filename(file_path.name)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove comments based on file type
            content_no_comments = self._remove_comments(content, extension)
            
            # Extract HC_ variables
            hc_variables = self._extract_hc_variables(content_no_comments)
            
            # Only return result if HC_ variables found
            if len(hc_variables) == 0:
                logger.debug(f"Scanned {file_path.name}: No HC_ variables found")
                return None
            
            # Get package ID
            package_id = None
            if parent_type in ["Iflow", "ScriptCollection"]:
                package_id = self.package_lookup.get(parent_name)
            
            # Determine file type
            file_type = self.FILE_TYPE_MAP.get(extension, 'unknown')
            
            # Extract actual script name (part after '---')
            script_name = file_path.name.split('---', 1)[1] if '---' in file_path.name else file_path.name
            
            # Build result
            result = {
                'packageId': package_id,
                'parentType': parent_type,
                'parentName': parent_name,
                'fileName': script_name,
                'fileType': file_type,
                'envVariableCount': len(hc_variables),
                'envVariableList': '|'.join(sorted(hc_variables))
            }
            
            logger.debug(f"Scanned {file_path.name}: {len(hc_variables)} HC_ variables found")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to scan {file_path.name}: {e}")
            self._track_error(file_path.name, str(e))
            return None
    
    def _parse_filename(self, filename: str) -> Tuple[str, str]:
        """
        Parse filename to extract parent name and extension
        
        Args:
            filename: Filename in format ParentID---scriptname.ext
            
        Returns:
            Tuple of (parent_name, extension)
        """
        # Split on first '---'
        if '---' in filename:
            parent_name = filename.split('---', 1)[0]
        else:
            parent_name = Path(filename).stem
        
        # Get extension
        extension = Path(filename).suffix
        
        return parent_name, extension
    
    def _remove_comments(self, content: str, extension: str) -> str:
        """
        Remove comments from content based on file type
        
        Args:
            content: File content
            extension: File extension
            
        Returns:
            Content with comments removed
        """
        if extension in ['.groovy', '.gsh', '.js']:
            # Remove single-line comments: //
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            
            # Remove multi-line comments: /* ... */
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        elif extension in ['.xsl', '.xslt']:
            # Remove XML/XSLT comments: <!-- ... -->
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        return content
    
    def _extract_hc_variables(self, content: str) -> Set[str]:
        """
        Extract HC_ environment variables from content
        
        Args:
            content: File content (with comments removed)
            
        Returns:
            Set of unique HC_ variable names
        """
        # Pattern to match HC_ followed by uppercase letters, numbers, and underscores
        pattern = r'\bHC_[A-Z0-9_]+\b'
        
        matches = re.findall(pattern, content)
        
        return set(matches)
    
    def _track_error(self, filename: str, error_message: str):
        """Track scanning error"""
        error_record = {
            "FileName": filename,
            "ErrorMessage": error_message[:500],
            "Timestamp": datetime.now().isoformat()
        }
        
        self.errors.append(error_record)
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        if not self.errors:
            return
        
        output_file = self.download_dir / "environment-variable-scan-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved error log with {len(self.errors)} errors")