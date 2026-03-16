"""
Artifact ZIP Downloader for SAP Cloud Integration Analyzer Tool
Downloads package and iflow ZIP files
"""

import json
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from auth.oauth_client import OAuthClient
from auth.basic_auth_client import BasicAuthClient
from utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactZipDownloader:
    """Downloads artifact ZIP files for packages and iflows"""
    
    def __init__(self, auth_client: Union[OAuthClient, BasicAuthClient], api_base_url: str, 
                 download_dir: Path, timeout: int = 30, 
                 parallel_downloads: int = 5, timestamp: str = None):
        """
        Initialize Artifact ZIP Downloader
        
        Args:
            auth_client: Authentication client (OAuth or Basic Auth)
            api_base_url: Base URL for the API
            download_dir: Directory to save downloaded files
            timeout: Request timeout in seconds
            parallel_downloads: Number of concurrent downloads
            timestamp: Optional timestamp for organized downloads
        """
        self.auth_client = auth_client
        self.api_base_url = api_base_url.rstrip('/')
        self.download_dir = Path(download_dir)
        self.timeout = timeout
        self.parallel_downloads = parallel_downloads
        self.timestamp = timestamp
        
        # Track download errors
        self.errors = []
        
        logger.info("ArtifactZipDownloader initialized")
    
    def download_all(self, packages: List[Dict[str, Any]], iflows: List[Dict[str, Any]], 
                     script_collections: List[Dict[str, Any]], message_mappings: List[Dict[str, Any]],
                     value_mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Download all artifact ZIPs (READ_ONLY packages and EDIT_ALLOWED iflows + script collections + message mappings + value mappings)
        
        Args:
            packages: List of package dictionaries
            iflows: List of iflow dictionaries
            script_collections: List of script collection dictionaries
            message_mappings: List of message mapping dictionaries
            value_mappings: List of value mapping dictionaries
            
        Returns:
            Dictionary with download statistics
        """
        logger.info("Starting artifact ZIP downloads...")
        
        stats = {
            "read_only_packages_attempted": 0,
            "read_only_packages_downloaded": 0,
            "read_only_packages_failed": 0,
            "edit_allowed_packages": 0,
            "iflows_attempted": 0,
            "iflows_downloaded": 0,
            "iflows_failed": 0,
            "script_collections_attempted": 0,
            "script_collections_downloaded": 0,
            "script_collections_failed": 0,
            "message_mappings_attempted": 0,
            "message_mappings_downloaded": 0,
            "message_mappings_failed": 0,
            "value_mappings_attempted": 0,
            "value_mappings_downloaded": 0,
            "value_mappings_failed": 0
        }
        
        # Download READ_ONLY packages
        read_only_stats = self.download_read_only_packages(packages)
        stats["read_only_packages_attempted"] = read_only_stats["attempted"]
        stats["read_only_packages_downloaded"] = read_only_stats["downloaded"]
        stats["read_only_packages_failed"] = read_only_stats["failed"]
        
        # Download EDIT_ALLOWED iflows, script collections, message mappings, and value mappings (package-by-package)
        edit_allowed_stats = self.download_edit_allowed_artifacts(packages, iflows, script_collections, 
                                                                  message_mappings, value_mappings)
        stats["edit_allowed_packages"] = edit_allowed_stats["packages"]
        stats["iflows_attempted"] = edit_allowed_stats["iflows_attempted"]
        stats["iflows_downloaded"] = edit_allowed_stats["iflows_downloaded"]
        stats["iflows_failed"] = edit_allowed_stats["iflows_failed"]
        stats["script_collections_attempted"] = edit_allowed_stats["script_collections_attempted"]
        stats["script_collections_downloaded"] = edit_allowed_stats["script_collections_downloaded"]
        stats["script_collections_failed"] = edit_allowed_stats["script_collections_failed"]
        stats["message_mappings_attempted"] = edit_allowed_stats["message_mappings_attempted"]
        stats["message_mappings_downloaded"] = edit_allowed_stats["message_mappings_downloaded"]
        stats["message_mappings_failed"] = edit_allowed_stats["message_mappings_failed"]
        stats["value_mappings_attempted"] = edit_allowed_stats["value_mappings_attempted"]
        stats["value_mappings_downloaded"] = edit_allowed_stats["value_mappings_downloaded"]
        stats["value_mappings_failed"] = edit_allowed_stats["value_mappings_failed"]
        
        # Save error log if there are any errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"Artifact ZIP downloads completed. Success: {stats['read_only_packages_downloaded']} packages, {stats['iflows_downloaded']} iflows, {stats['script_collections_downloaded']} script collections, {stats['message_mappings_downloaded']} message mappings, {stats['value_mappings_downloaded']} value mappings")
        
        return stats
    
    def download_read_only_packages(self, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Download ZIP files for READ_ONLY packages
        
        Args:
            packages: List of package dictionaries
            
        Returns:
            Dictionary with download statistics
        """
        # Filter READ_ONLY packages
        read_only_packages = [pkg for pkg in packages if pkg.get('Mode') == 'READ_ONLY']
        
        if not read_only_packages:
            logger.info("No READ_ONLY packages to download")
            return {"attempted": 0, "downloaded": 0, "failed": 0}
        
        logger.info(f"Found {len(read_only_packages)} READ_ONLY packages to download")
        
        # Create directory with zip-files subdirectory
        output_dir = self.download_dir / "read-only-packages" / "zip-files"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {"attempted": 0, "downloaded": 0, "failed": 0}
        
        for idx, package in enumerate(read_only_packages, 1):
            package_id = package.get('Id')
            logger.info(f"Downloading package {idx}/{len(read_only_packages)}: {package_id}")
            
            stats["attempted"] += 1
            success = self._download_package_zip(package_id, output_dir)
            
            if success:
                stats["downloaded"] += 1
            else:
                stats["failed"] += 1
        
        return stats
    
    def download_edit_allowed_artifacts(self, packages: List[Dict[str, Any]], 
                                       iflows: List[Dict[str, Any]],
                                       script_collections: List[Dict[str, Any]],
                                       message_mappings: List[Dict[str, Any]],
                                       value_mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Download ZIP files for iflows, script collections, message mappings, and value mappings in EDIT_ALLOWED packages
        Process package-by-package: iflows → script collections → message mappings → value mappings
        
        Args:
            packages: List of package dictionaries
            iflows: List of iflow dictionaries
            script_collections: List of script collection dictionaries
            message_mappings: List of message mapping dictionaries
            value_mappings: List of value mapping dictionaries
            
        Returns:
            Dictionary with download statistics
        """
        # Filter EDIT_ALLOWED packages
        edit_allowed_packages = [pkg for pkg in packages if pkg.get('Mode') == 'EDIT_ALLOWED']
        
        if not edit_allowed_packages:
            logger.info("No EDIT_ALLOWED packages to download")
            return {
                "packages": 0, 
                "iflows_attempted": 0, "iflows_downloaded": 0, "iflows_failed": 0,
                "script_collections_attempted": 0, "script_collections_downloaded": 0, "script_collections_failed": 0,
                "message_mappings_attempted": 0, "message_mappings_downloaded": 0, "message_mappings_failed": 0,
                "value_mappings_attempted": 0, "value_mappings_downloaded": 0, "value_mappings_failed": 0
            }
        
        logger.info(f"Found {len(edit_allowed_packages)} EDIT_ALLOWED packages")
        
        # Create directories with zip-files subdirectories
        iflows_dir = self.download_dir / "iflows" / "zip-files"
        iflows_dir.mkdir(parents=True, exist_ok=True)
        
        script_collections_dir = self.download_dir / "script-collections" / "zip-files"
        script_collections_dir.mkdir(parents=True, exist_ok=True)
        
        message_mappings_dir = self.download_dir / "message-mappings" / "zip-files"
        message_mappings_dir.mkdir(parents=True, exist_ok=True)
        
        value_mappings_dir = self.download_dir / "value-mappings" / "zip-files"
        value_mappings_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "packages": len(edit_allowed_packages),
            "iflows_attempted": 0, "iflows_downloaded": 0, "iflows_failed": 0,
            "script_collections_attempted": 0, "script_collections_downloaded": 0, "script_collections_failed": 0,
            "message_mappings_attempted": 0, "message_mappings_downloaded": 0, "message_mappings_failed": 0,
            "value_mappings_attempted": 0, "value_mappings_downloaded": 0, "value_mappings_failed": 0
        }
        
        # Process each package sequentially
        for idx, package in enumerate(edit_allowed_packages, 1):
            package_id = package.get('Id')
            logger.info(f"Processing package {idx}/{len(edit_allowed_packages)}: {package_id}")
            
            # 1. Download iflows for this package
            package_iflows = [iflow for iflow in iflows if iflow.get('PackageId') == package_id]
            if package_iflows:
                logger.info(f"  Downloading {len(package_iflows)} iflows for {package_id}")
                iflow_stats = self._download_package_iflows(package_id, package_iflows, iflows_dir)
                stats["iflows_attempted"] += iflow_stats["attempted"]
                stats["iflows_downloaded"] += iflow_stats["downloaded"]
                stats["iflows_failed"] += iflow_stats["failed"]
            
            # 2. Download script collections for this package
            package_scripts = [sc for sc in script_collections if sc.get('PackageId') == package_id]
            if package_scripts:
                logger.info(f"  Downloading {len(package_scripts)} script collections for {package_id}")
                script_stats = self._download_package_script_collections(package_id, package_scripts, script_collections_dir)
                stats["script_collections_attempted"] += script_stats["attempted"]
                stats["script_collections_downloaded"] += script_stats["downloaded"]
                stats["script_collections_failed"] += script_stats["failed"]
            
            # 3. Download message mappings for this package
            package_message_mappings = [mm for mm in message_mappings if mm.get('PackageId') == package_id]
            if package_message_mappings:
                logger.info(f"  Downloading {len(package_message_mappings)} message mappings for {package_id}")
                mm_stats = self._download_package_message_mappings(package_id, package_message_mappings, message_mappings_dir)
                stats["message_mappings_attempted"] += mm_stats["attempted"]
                stats["message_mappings_downloaded"] += mm_stats["downloaded"]
                stats["message_mappings_failed"] += mm_stats["failed"]
            
            # 4. Download value mappings for this package
            package_value_mappings = [vm for vm in value_mappings if vm.get('PackageId') == package_id]
            if package_value_mappings:
                logger.info(f"  Downloading {len(package_value_mappings)} value mappings for {package_id}")
                vm_stats = self._download_package_value_mappings(package_id, package_value_mappings, value_mappings_dir)
                stats["value_mappings_attempted"] += vm_stats["attempted"]
                stats["value_mappings_downloaded"] += vm_stats["downloaded"]
                stats["value_mappings_failed"] += vm_stats["failed"]
        
        return stats
    
    def _download_package_iflows(self, package_id: str, iflows: List[Dict[str, Any]], 
                                 output_dir: Path) -> Dict[str, Any]:
        """
        Download iflow ZIPs for a single package (parallel)
        
        Args:
            package_id: Package ID
            iflows: List of iflow dicts for this package
            output_dir: Output directory (iflows/)
            
        Returns:
            Dict with download stats
        """
        stats = {"attempted": 0, "downloaded": 0, "failed": 0}
        
        if not iflows:
            return stats
        
        # Determine actual parallelism
        actual_workers = min(self.parallel_downloads, len(iflows))
        
        # Download iflows in parallel
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_iflow = {
                executor.submit(self._download_iflow_zip, 
                              iflow.get('Id'), iflow.get('Version'), 
                              package_id, output_dir): iflow
                for iflow in iflows
            }
            
            for future in as_completed(future_to_iflow):
                iflow_info = future_to_iflow[future]
                stats["attempted"] += 1
                
                try:
                    success = future.result()
                    if success:
                        stats["downloaded"] += 1
                        logger.info(f"    Downloaded: {package_id}---{iflow_info.get('Id')}.zip")
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"    Exception downloading {iflow_info.get('Id')}: {e}")
        
        return stats
    
    def _download_package_script_collections(self, package_id: str, 
                                            script_collections: List[Dict[str, Any]],
                                            output_dir: Path) -> Dict[str, Any]:
        """
        Download script collection ZIPs for a single package (parallel)
        
        Args:
            package_id: Package ID
            script_collections: List of script collection dicts for this package
            output_dir: Output directory (script-collections/)
            
        Returns:
            Dict with download stats
        """
        stats = {"attempted": 0, "downloaded": 0, "failed": 0}
        
        if not script_collections:
            return stats
        
        # Determine actual parallelism
        actual_workers = min(self.parallel_downloads, len(script_collections))
        
        # Download script collections in parallel
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_script = {
                executor.submit(self._download_script_collection_zip,
                              sc.get('Id'), sc.get('Version'),
                              package_id, output_dir): sc
                for sc in script_collections
            }
            
            for future in as_completed(future_to_script):
                script_info = future_to_script[future]
                stats["attempted"] += 1
                
                try:
                    success = future.result()
                    if success:
                        stats["downloaded"] += 1
                        logger.info(f"    Downloaded: {package_id}---{script_info.get('Id')}.zip")
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"    Exception downloading {script_info.get('Id')}: {e}")
        
        return stats
    
    def _download_package_zip(self, package_id: str, output_dir: Path) -> bool:
        """
        Download a single package ZIP
        
        Args:
            package_id: Package ID
            output_dir: Output directory
            
        Returns:
            True if successful, False otherwise
        """
        import requests
        
        url = f"{self.api_base_url}/IntegrationPackages('{package_id}')/$value"
        output_file = output_dir / f"{package_id}.zip"
        
        # Retry logic
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Use generic auth header (works with OAuth or Basic Auth)
                headers = self.auth_client.get_auth_header()
                
                logger.debug(f"  GET {url} (attempt {attempt}/{max_retries})")
                response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
                
                if response.status_code == 200:
                    # Save ZIP file
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_size = output_file.stat().st_size
                    logger.info(f"  Downloaded: {package_id}.zip ({file_size / 1024:.1f} KB)")
                    return True
                
                elif response.status_code == 403:
                    # Proprietary content - log and skip
                    error_msg = 'Forbidden'
                    try:
                        # Try JSON first
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', {}).get('value', 'Forbidden')
                    except:
                        # Try XML parsing
                        try:
                            import xml.etree.ElementTree as ET
                            root = ET.fromstring(response.text)
                            # Find message element (handle namespace)
                            message_elem = root.find('.//{*}message')
                            if message_elem is not None and message_elem.text:
                                error_msg = message_elem.text
                            else:
                                error_msg = response.text[:500] if response.text else 'Forbidden'
                        except:
                            error_msg = response.text[:500] if response.text else 'Forbidden'
                    
                    logger.warning(f"  403 Forbidden: {error_msg}")
                    self._track_error(package_id, None, None, "READ_ONLY_PACKAGE", 
                                    403, "PROPRIETARY_CONTENT", error_msg, output_file)
                    return False
                
                elif response.status_code in [401, 404]:
                    # Auth or Not Found - log and retry
                    logger.warning(f"  {response.status_code} error for {package_id}")
                    
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        # Track error only after all retries exhausted
                        self._track_error(package_id, None, None, "READ_ONLY_PACKAGE",
                                        response.status_code, f"HTTP_{response.status_code}", 
                                        response.text, output_file)
                    return False
                
                else:
                    logger.error(f"  Unexpected status {response.status_code}: {response.text}")
                    self._track_error(package_id, None, None, "READ_ONLY_PACKAGE",
                                    response.status_code, f"HTTP_{response.status_code}",
                                    response.text, output_file)
                    return False
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.warning(f"  Connection/Timeout error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                self._track_error(package_id, None, None, "READ_ONLY_PACKAGE",
                                None, "CONNECTION_ERROR", str(e), output_file)
                return False
            except Exception as e:
                logger.error(f"  Error downloading package {package_id}: {e}")
                self._track_error(package_id, None, None, "READ_ONLY_PACKAGE",
                                None, "UNKNOWN_ERROR", str(e), output_file)
                return False
        
        return False
    
    def _download_iflow_zip(self, iflow_id: str, version: str, package_id: str, 
                           output_dir: Path) -> bool:
        """
        Download a single iflow ZIP
        
        Args:
            iflow_id: IFlow ID
            version: IFlow version (from JSON, for logging only)
            package_id: Package ID (for filename)
            output_dir: Output directory (should be iflows/zip-files/)
            
        Returns:
            True if successful, False otherwise
        """
        import requests
        
        # Always use 'Active' to get the latest/active version, regardless of JSON version
        logger.debug(f"Downloading IFlow {iflow_id} to directory: {output_dir}")
        url = f"{self.api_base_url}/IntegrationDesigntimeArtifacts(Id='{iflow_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{iflow_id}.zip"
        
        # Retry logic
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Use generic auth header (works with OAuth or Basic Auth)
                headers = self.auth_client.get_auth_header()
                
                response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
                
                if response.status_code == 200:
                    # Save ZIP file
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                
                elif response.status_code in [401, 403, 404]:
                    logger.warning(f"  {response.status_code} error for {iflow_id}")
                    
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        # Track error only after all retries exhausted
                        self._track_error(package_id, iflow_id, version, "IFLOW",
                                        response.status_code, f"HTTP_{response.status_code}",
                                        response.text, output_file)
                    return False
                
                else:
                    logger.error(f"  Unexpected status {response.status_code} for {iflow_id}")
                    self._track_error(package_id, iflow_id, version, "IFLOW",
                                    response.status_code, f"HTTP_{response.status_code}",
                                    response.text, output_file)
                    return False
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                self._track_error(package_id, iflow_id, version, "IFLOW",
                                None, "CONNECTION_ERROR", str(e), output_file)
                return False
            except Exception as e:
                logger.error(f"  Error downloading iflow {iflow_id}: {e}")
                self._track_error(package_id, iflow_id, version, "IFLOW",
                                None, "UNKNOWN_ERROR", str(e), output_file)
                return False
        
        return False
    
    def _download_script_collection_zip(self, script_id: str, version: str, package_id: str,
                                       output_dir: Path) -> bool:
        """
        Download a single script collection ZIP
        
        Args:
            script_id: Script collection ID
            version: Script collection version (from JSON, for logging only)
            package_id: Package ID (for filename)
            output_dir: Output directory (should be script-collections/zip-files/)
            
        Returns:
            True if successful, False otherwise
        """
        import requests
        
        # Always use 'Active' to get the latest/active version, regardless of JSON version
        logger.debug(f"Downloading Script Collection {script_id} to directory: {output_dir}")
        url = f"{self.api_base_url}/ScriptCollectionDesigntimeArtifacts(Id='{script_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{script_id}.zip"
        
        # Retry logic
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Use generic auth header (works with OAuth or Basic Auth)
                headers = self.auth_client.get_auth_header()
                
                response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
                
                if response.status_code == 200:
                    # Save ZIP file
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                
                elif response.status_code in [401, 403, 404]:
                    logger.warning(f"  {response.status_code} error for script collection {script_id}")
                    
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        # Track error only after all retries exhausted
                        self._track_error(package_id, script_id, version, "SCRIPT_COLLECTION",
                                        response.status_code, f"HTTP_{response.status_code}",
                                        response.text, output_file)
                    return False
                
                else:
                    logger.error(f"  Unexpected status {response.status_code} for script collection {script_id}")
                    self._track_error(package_id, script_id, version, "SCRIPT_COLLECTION",
                                    response.status_code, f"HTTP_{response.status_code}",
                                    response.text, output_file)
                    return False
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                self._track_error(package_id, script_id, version, "SCRIPT_COLLECTION",
                                None, "CONNECTION_ERROR", str(e), output_file)
                return False
            except Exception as e:
                logger.error(f"  Error downloading script collection {script_id}: {e}")
                self._track_error(package_id, script_id, version, "SCRIPT_COLLECTION",
                                None, "UNKNOWN_ERROR", str(e), output_file)
                return False
        
        return False
    
    def _download_package_message_mappings(self, package_id: str, 
                                          message_mappings: List[Dict[str, Any]],
                                          output_dir: Path) -> Dict[str, Any]:
        """
        Download message mapping ZIPs for a single package (parallel)
        
        Args:
            package_id: Package ID
            message_mappings: List of message mapping dicts for this package
            output_dir: Output directory (message-mappings/)
            
        Returns:
            Dict with download stats
        """
        stats = {"attempted": 0, "downloaded": 0, "failed": 0}
        
        if not message_mappings:
            return stats
        
        # Determine actual parallelism
        actual_workers = min(self.parallel_downloads, len(message_mappings))
        
        # Download message mappings in parallel
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_mapping = {
                executor.submit(self._download_message_mapping_zip,
                              mm.get('Id'), mm.get('Version'),
                              package_id, output_dir): mm
                for mm in message_mappings
            }
            
            for future in as_completed(future_to_mapping):
                mapping_info = future_to_mapping[future]
                stats["attempted"] += 1
                
                try:
                    success = future.result()
                    if success:
                        stats["downloaded"] += 1
                        logger.info(f"    Downloaded: {package_id}---{mapping_info.get('Id')}.zip")
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"    Exception downloading message mapping {mapping_info.get('Id')}: {e}")
        
        return stats
    
    def _download_message_mapping_zip(self, mapping_id: str, version: str, package_id: str,
                                     output_dir: Path) -> bool:
        """
        Download a single message mapping ZIP
        
        Args:
            mapping_id: Message mapping ID
            version: Message mapping version (from JSON, for logging only)
            package_id: Package ID (for filename)
            output_dir: Output directory
            
        Returns:
            True if successful, False otherwise
        """
        import requests
        
        # Always use 'Active' to get the latest/active version, regardless of JSON version
        logger.debug(f"Downloading Message Mapping {mapping_id} (JSON version: {version}, using 'Active')")
        url = f"{self.api_base_url}/MessageMappingDesigntimeArtifacts(Id='{mapping_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{mapping_id}.zip"
        
        # Retry logic
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Use generic auth header (works with OAuth or Basic Auth)
                headers = self.auth_client.get_auth_header()
                
                response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
                
                if response.status_code == 200:
                    # Save ZIP file
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                
                elif response.status_code in [401, 403, 404]:
                    logger.warning(f"  {response.status_code} error for message mapping {mapping_id}")
                    
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        # Track error only after all retries exhausted
                        self._track_error(package_id, mapping_id, version, "MESSAGE_MAPPING",
                                        response.status_code, f"HTTP_{response.status_code}",
                                        response.text, output_file)
                    return False
                
                else:
                    logger.error(f"  Unexpected status {response.status_code} for message mapping {mapping_id}")
                    self._track_error(package_id, mapping_id, version, "MESSAGE_MAPPING",
                                    response.status_code, f"HTTP_{response.status_code}",
                                    response.text, output_file)
                    return False
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                self._track_error(package_id, mapping_id, version, "MESSAGE_MAPPING",
                                None, "CONNECTION_ERROR", str(e), output_file)
                return False
            except Exception as e:
                logger.error(f"  Error downloading message mapping {mapping_id}: {e}")
                self._track_error(package_id, mapping_id, version, "MESSAGE_MAPPING",
                                None, "UNKNOWN_ERROR", str(e), output_file)
                return False
        
        return False
    
    def _download_package_value_mappings(self, package_id: str, 
                                        value_mappings: List[Dict[str, Any]],
                                        output_dir: Path) -> Dict[str, Any]:
        """
        Download value mapping ZIPs for a single package (parallel)
        
        Args:
            package_id: Package ID
            value_mappings: List of value mapping dicts for this package
            output_dir: Output directory (value-mappings/)
            
        Returns:
            Dict with download stats
        """
        stats = {"attempted": 0, "downloaded": 0, "failed": 0}
        
        if not value_mappings:
            return stats
        
        # Determine actual parallelism
        actual_workers = min(self.parallel_downloads, len(value_mappings))
        
        # Download value mappings in parallel
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_mapping = {
                executor.submit(self._download_value_mapping_zip,
                              vm.get('Id'), vm.get('Version'),
                              package_id, output_dir): vm
                for vm in value_mappings
            }
            
            for future in as_completed(future_to_mapping):
                mapping_info = future_to_mapping[future]
                stats["attempted"] += 1
                
                try:
                    success = future.result()
                    if success:
                        stats["downloaded"] += 1
                        logger.info(f"    Downloaded: {package_id}---{mapping_info.get('Id')}.zip")
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"    Exception downloading value mapping {mapping_info.get('Id')}: {e}")
        
        return stats
    
    def _download_value_mapping_zip(self, mapping_id: str, version: str, package_id: str,
                                   output_dir: Path) -> bool:
        """
        Download a single value mapping ZIP
        
        Args:
            mapping_id: Value mapping ID
            version: Value mapping version (from JSON, for logging only)
            package_id: Package ID (for filename)
            output_dir: Output directory
            
        Returns:
            True if successful, False otherwise
        """
        import requests
        
        # Always use 'Active' to get the latest/active version, regardless of JSON version
        logger.debug(f"Downloading Value Mapping {mapping_id} (JSON version: {version}, using 'Active')")
        url = f"{self.api_base_url}/ValueMappingDesigntimeArtifacts(Id='{mapping_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{mapping_id}.zip"
        
        # Retry logic
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Use generic auth header (works with OAuth or Basic Auth)
                headers = self.auth_client.get_auth_header()
                
                response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
                
                if response.status_code == 200:
                    # Save ZIP file
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                
                elif response.status_code in [401, 403, 404]:
                    logger.warning(f"  {response.status_code} error for value mapping {mapping_id}")
                    
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        # Track error only after all retries exhausted
                        self._track_error(package_id, mapping_id, version, "VALUE_MAPPING",
                                        response.status_code, f"HTTP_{response.status_code}",
                                        response.text, output_file)
                    return False
                
                else:
                    logger.error(f"  Unexpected status {response.status_code} for value mapping {mapping_id}")
                    self._track_error(package_id, mapping_id, version, "VALUE_MAPPING",
                                    response.status_code, f"HTTP_{response.status_code}",
                                    response.text, output_file)
                    return False
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                self._track_error(package_id, mapping_id, version, "VALUE_MAPPING",
                                None, "CONNECTION_ERROR", str(e), output_file)
                return False
            except Exception as e:
                logger.error(f"  Error downloading value mapping {mapping_id}: {e}")
                self._track_error(package_id, mapping_id, version, "VALUE_MAPPING",
                                None, "UNKNOWN_ERROR", str(e), output_file)
                return False
        
        return False
    
    def _track_error(self, package_id: str, iflow_id: Optional[str], version: Optional[str],
                    artifact_type: str, error_code: Optional[int], error_type: str,
                    error_message: str, attempted_path: Path):
        """Track download error for later reporting"""
        error_record = {
            "PackageID": package_id,
            "Type": artifact_type,
            "ErrorCode": error_code,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],  # Limit message length
            "Timestamp": datetime.now().isoformat(),
            "DownloadAttempted": str(attempted_path.relative_to(self.download_dir.parent))
        }
        
        if iflow_id:
            error_record["IflowID"] = iflow_id
            error_record["Version"] = version
        
        self.errors.append(error_record)
    
    def _save_error_log(self):
        """Save error log to JSON file (in json-files/ so it gets imported to DB)"""
        json_files_dir = self.download_dir / "json-files"
        json_files_dir.mkdir(parents=True, exist_ok=True)
        output_file = json_files_dir / "download-errors.json"
        
        output_data = {
            "d": {
                "results": self.errors
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved download error log with {len(self.errors)} errors: download-errors.json")