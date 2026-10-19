"""
Artifact ZIP Downloader for SAP Cloud Integration Analyzer Tool
Downloads package and iflow ZIP files
"""

import json
import time
import requests
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
                 parallel_downloads: int = 5, timestamp: str = None,
                 error_collector=None):
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
        self.error_collector = error_collector

        # Track download errors
        self.errors = []

        # Persistent HTTP session — reuses TCP/TLS connections across all ZIP downloads
        self._session = requests.Session()

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
        
        logger.info(f"Artifact ZIP downloads completed. Success: {stats['read_only_packages_downloaded']} packages, {stats['iflows_downloaded']} iflows, {stats['script_collections_downloaded']} script collections, {stats['message_mappings_downloaded']} message mappings, {stats['value_mappings_downloaded']} value mappings")
        
        return stats
    
    def download_read_only_packages(self, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Download ZIP files for READ_ONLY packages in parallel.
        """
        read_only_packages = [pkg for pkg in packages if pkg.get('Mode') == 'READ_ONLY']

        if not read_only_packages:
            logger.info("No READ_ONLY packages to download")
            return {"attempted": 0, "downloaded": 0, "failed": 0}

        logger.info(f"Found {len(read_only_packages)} READ_ONLY packages to download")

        output_dir = self.download_dir / "read-only-packages" / "zip-files"
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = [(pkg.get('Id'), output_dir) for pkg in read_only_packages]
        return self._download_batch(tasks, self._download_package_zip, label="package")
    
    def download_edit_allowed_artifacts(self, packages: List[Dict[str, Any]],
                                       iflows: List[Dict[str, Any]],
                                       script_collections: List[Dict[str, Any]],
                                       message_mappings: List[Dict[str, Any]],
                                       value_mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Download ZIP files for all EDIT_ALLOWED artifacts using a flat thread pool per
        artifact type (all packages submitted together rather than package-by-package).
        """
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

        iflows_dir = self.download_dir / "iflows" / "zip-files"
        iflows_dir.mkdir(parents=True, exist_ok=True)
        script_collections_dir = self.download_dir / "script-collections" / "zip-files"
        script_collections_dir.mkdir(parents=True, exist_ok=True)
        message_mappings_dir = self.download_dir / "message-mappings" / "zip-files"
        message_mappings_dir.mkdir(parents=True, exist_ok=True)
        value_mappings_dir = self.download_dir / "value-mappings" / "zip-files"
        value_mappings_dir.mkdir(parents=True, exist_ok=True)

        edit_pkg_ids = {pkg.get('Id') for pkg in edit_allowed_packages}

        stats = {
            "packages": len(edit_allowed_packages),
            "iflows_attempted": 0, "iflows_downloaded": 0, "iflows_failed": 0,
            "script_collections_attempted": 0, "script_collections_downloaded": 0, "script_collections_failed": 0,
            "message_mappings_attempted": 0, "message_mappings_downloaded": 0, "message_mappings_failed": 0,
            "value_mappings_attempted": 0, "value_mappings_downloaded": 0, "value_mappings_failed": 0
        }

        # 1. Iflows — flat pool across all packages
        iflow_tasks = [
            (iflow.get('Id'), iflow.get('Version'), iflow.get('PackageId'), iflows_dir)
            for iflow in iflows if iflow.get('PackageId') in edit_pkg_ids
        ]
        if iflow_tasks:
            logger.info(f"Downloading {len(iflow_tasks)} iflows across {len(edit_allowed_packages)} packages...")
            pkg_iflow_counts: Dict[str, int] = {}
            for t in iflow_tasks:
                pkg_iflow_counts[t[2]] = pkg_iflow_counts.get(t[2], 0) + 1
            for i, pid in enumerate(sorted(pkg_iflow_counts), 1):
                logger.info(f"  Package {i}/{len(pkg_iflow_counts)} ({pid}): {pkg_iflow_counts[pid]} iflow(s)")
            r = self._download_batch(iflow_tasks, self._download_iflow_zip, label="iflow")
            stats["iflows_attempted"] = r["attempted"]
            stats["iflows_downloaded"] = r["downloaded"]
            stats["iflows_failed"] = r["failed"]

        # 2. Script collections — flat pool
        sc_tasks = [
            (sc.get('Id'), sc.get('Version'), sc.get('PackageId'), script_collections_dir)
            for sc in script_collections if sc.get('PackageId') in edit_pkg_ids
        ]
        if sc_tasks:
            logger.info(f"Downloading {len(sc_tasks)} script collections...")
            r = self._download_batch(sc_tasks, self._download_script_collection_zip, label="script collection")
            stats["script_collections_attempted"] = r["attempted"]
            stats["script_collections_downloaded"] = r["downloaded"]
            stats["script_collections_failed"] = r["failed"]

        # 3. Message mappings — flat pool
        mm_tasks = [
            (mm.get('Id'), mm.get('Version'), mm.get('PackageId'), message_mappings_dir)
            for mm in message_mappings if mm.get('PackageId') in edit_pkg_ids
        ]
        if mm_tasks:
            logger.info(f"Downloading {len(mm_tasks)} message mappings...")
            r = self._download_batch(mm_tasks, self._download_message_mapping_zip, label="message mapping")
            stats["message_mappings_attempted"] = r["attempted"]
            stats["message_mappings_downloaded"] = r["downloaded"]
            stats["message_mappings_failed"] = r["failed"]

        # 4. Value mappings — flat pool
        vm_tasks = [
            (vm.get('Id'), vm.get('Version'), vm.get('PackageId'), value_mappings_dir)
            for vm in value_mappings if vm.get('PackageId') in edit_pkg_ids
        ]
        if vm_tasks:
            logger.info(f"Downloading {len(vm_tasks)} value mappings...")
            r = self._download_batch(vm_tasks, self._download_value_mapping_zip, label="value mapping")
            stats["value_mappings_attempted"] = r["attempted"]
            stats["value_mappings_downloaded"] = r["downloaded"]
            stats["value_mappings_failed"] = r["failed"]

        return stats

    def _download_batch(self, tasks: list, download_fn, label: str = "artifact") -> Dict[str, Any]:
        """
        Submit a list of (arg, ...) tuples to a flat ThreadPoolExecutor and collect results.

        Args:
            tasks: List of argument tuples passed to download_fn via *args.
            download_fn: Callable that returns True on success, False on failure.
            label: Name used in log messages.

        Returns:
            Dict with 'attempted', 'downloaded', 'failed' counts.
        """
        stats = {"attempted": 0, "downloaded": 0, "failed": 0}
        if not tasks:
            return stats

        total = len(tasks)
        completed = 0
        workers = min(self.parallel_downloads, len(tasks))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {executor.submit(download_fn, *t): t for t in tasks}
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                stats["attempted"] += 1
                completed += 1
                try:
                    if future.result():
                        stats["downloaded"] += 1
                        logger.info(f"  [{label} {completed}/{total}] {task[0]}")
                    else:
                        stats["failed"] += 1
                        logger.warning(f"  [{label} {completed}/{total}] FAILED: {task[0]}")
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"  [{label} {completed}/{total}] Exception: {task[0]}: {e}")

        return stats
    
    def _download_package_iflows(self, package_id: str, iflows: List[Dict[str, Any]],
                                 output_dir: Path) -> Dict[str, Any]:
        """Kept for backwards compatibility — delegates to _download_batch."""
        tasks = [(iflow.get('Id'), iflow.get('Version'), package_id, output_dir) for iflow in iflows]
        return self._download_batch(tasks, self._download_iflow_zip, label="iflow")

    def _download_package_script_collections(self, package_id: str,
                                            script_collections: List[Dict[str, Any]],
                                            output_dir: Path) -> Dict[str, Any]:
        """Kept for backwards compatibility — delegates to _download_batch."""
        tasks = [(sc.get('Id'), sc.get('Version'), package_id, output_dir) for sc in script_collections]
        return self._download_batch(tasks, self._download_script_collection_zip, label="script collection")
        
        return stats
    
    def _download_package_zip(self, package_id: str, output_dir: Path) -> bool:
        """Download a single package ZIP."""
        url = f"{self.api_base_url}/IntegrationPackages('{package_id}')/$value"
        output_file = output_dir / f"{package_id}.zip"

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                headers = self.auth_client.get_auth_header()

                logger.debug(f"  GET {url} (attempt {attempt}/{max_retries})")
                response = self._session.get(url, headers=headers, timeout=self.timeout, stream=True)
                
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
        """Download a single iflow ZIP (always uses Version='Active')."""
        logger.debug(f"Downloading IFlow {iflow_id} to directory: {output_dir}")
        url = f"{self.api_base_url}/IntegrationDesigntimeArtifacts(Id='{iflow_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{iflow_id}.zip"

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                headers = self.auth_client.get_auth_header()
                response = self._session.get(url, headers=headers, timeout=self.timeout, stream=True)
                
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
                output_file.unlink(missing_ok=True)
                self._track_error(package_id, iflow_id, version, "IFLOW",
                                None, "CONNECTION_ERROR", str(e), output_file)
                return False
            except Exception as e:
                logger.error(f"  Error downloading iflow {iflow_id}: {e}")
                output_file.unlink(missing_ok=True)
                self._track_error(package_id, iflow_id, version, "IFLOW",
                                None, "UNKNOWN_ERROR", str(e), output_file)
                return False
        
        return False
    
    def _download_script_collection_zip(self, script_id: str, version: str, package_id: str,
                                       output_dir: Path) -> bool:
        """Download a single script collection ZIP (always uses Version='Active')."""
        logger.debug(f"Downloading Script Collection {script_id} to directory: {output_dir}")
        url = f"{self.api_base_url}/ScriptCollectionDesigntimeArtifacts(Id='{script_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{script_id}.zip"

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                headers = self.auth_client.get_auth_header()
                response = self._session.get(url, headers=headers, timeout=self.timeout, stream=True)
                
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
        """Kept for backwards compatibility — delegates to _download_batch."""
        tasks = [(mm.get('Id'), mm.get('Version'), package_id, output_dir) for mm in message_mappings]
        return self._download_batch(tasks, self._download_message_mapping_zip, label="message mapping")

    def _download_message_mapping_zip(self, mapping_id: str, version: str, package_id: str,
                                     output_dir: Path) -> bool:
        """Download a single message mapping ZIP (always uses Version='Active')."""
        logger.debug(f"Downloading Message Mapping {mapping_id} (JSON version: {version}, using 'Active')")
        url = f"{self.api_base_url}/MessageMappingDesigntimeArtifacts(Id='{mapping_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{mapping_id}.zip"

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                headers = self.auth_client.get_auth_header()
                response = self._session.get(url, headers=headers, timeout=self.timeout, stream=True)

                if response.status_code == 200:
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
        """Kept for backwards compatibility — delegates to _download_batch."""
        tasks = [(vm.get('Id'), vm.get('Version'), package_id, output_dir) for vm in value_mappings]
        return self._download_batch(tasks, self._download_value_mapping_zip, label="value mapping")

    def _download_value_mapping_zip(self, mapping_id: str, version: str, package_id: str,
                                   output_dir: Path) -> bool:
        """Download a single value mapping ZIP (always uses Version='Active')."""
        logger.debug(f"Downloading Value Mapping {mapping_id} (JSON version: {version}, using 'Active')")
        url = f"{self.api_base_url}/ValueMappingDesigntimeArtifacts(Id='{mapping_id}',Version='Active')/$value"
        output_file = output_dir / f"{package_id}---{mapping_id}.zip"

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                headers = self.auth_client.get_auth_header()
                response = self._session.get(url, headers=headers, timeout=self.timeout, stream=True)

                if response.status_code == 200:
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
            if attempted_path.is_relative_to(self.download_dir.parent)
            else str(attempted_path),
        }

        if iflow_id:
            error_record["IflowID"] = iflow_id
            error_record["Version"] = version

        self.errors.append(error_record)

        # Forward to centralized error collector
        if self.error_collector:
            self.error_collector.add_error(
                package_id=package_id,
                artifact_type=artifact_type,
                error_code=error_code or 0,
                error_type=error_type,
                error_message=error_message[:500],
                download_path=str(attempted_path.relative_to(self.download_dir.parent)),
                iflow_id=iflow_id or '',
                version=version or ''
            )
    
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