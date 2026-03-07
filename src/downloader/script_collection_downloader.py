"""
Script Collection Downloader for SAP Cloud Integration
Downloads script collection artifacts from the Integration Content API with parallel processing
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from .base_downloader import BaseDownloader
from utils.logger import get_logger

logger = get_logger(__name__)


class ScriptCollectionDownloader(BaseDownloader):
    """Downloads Script Collection artifacts with parallel processing"""
    
    def __init__(self, oauth_client, api_base_url: str, download_dir: Path, 
                 timeout: int = 30, parallel_downloads: int = 1, timestamp: str = None):
        """
        Initialize Script Collection downloader
        
        Args:
            oauth_client: OAuth client for authentication
            api_base_url: Base URL for the API
            download_dir: Directory to save downloaded files
            timeout: Request timeout in seconds
            parallel_downloads: Number of concurrent package downloads (1-10)
            timestamp: Optional timestamp for organized downloads
        """
        super().__init__(oauth_client, api_base_url, download_dir, timeout, timestamp)
        self.parallel_downloads = max(1, min(10, parallel_downloads))
        self.result_lock = Lock()  # Thread-safe result aggregation
        logger.info("ScriptCollectionDownloader initialized")
    
    def download(self) -> Dict[str, Any]:
        """
        Download all script collections from all packages
        
        Returns:
            Dictionary with 'count' and 'items' (filtered)
        """
        logger.info("Starting script collection download...")
        logger.info(f"Parallel downloads: {self.parallel_downloads}")
        
        # Load packages to get Package IDs
        package_ids = self._load_package_ids()
        
        if not package_ids:
            logger.warning("No packages found. Cannot download script collections.")
            return {
                'items': [],
                'count': 0
            }
        
        logger.info(f"Found {len(package_ids)} packages to process")
        
        # Download script collections with parallel processing
        all_collections = self._download_collections_parallel(package_ids)
        
        # Filter to keep only base-level fields
        logger.info("Filtering response to keep only base-level fields...")
        filtered_collections = []
        for collection in all_collections:
            filtered_collection = {}
            for key, value in collection.items():
                # Skip metadata and nested objects
                if key == '__metadata':
                    continue
                if isinstance(value, dict) and '__deferred' in value:
                    continue
                if isinstance(value, dict):
                    continue
                # Keep simple values
                filtered_collection[key] = value
            filtered_collections.append(filtered_collection)
        
        # Save to file
        output_data = {
            "d": {
                "results": filtered_collections
            }
        }
        
        filename = "script-collections.json"
        self._save_json(output_data, filename)
        
        logger.info(f"Script collection download completed. Retrieved {len(filtered_collections)} script collections (filtered)")
        
        return {
            "count": len(filtered_collections),
            "items": filtered_collections
        }
    
    def _load_package_ids(self) -> List[str]:
        """
        Load Package IDs from packages.json
        
        Returns:
            List of Package IDs
        """
        packages_file = self.json_dir / 'packages.json'
        
        if not packages_file.exists():
            logger.error(f"packages.json not found at {packages_file}")
            return []
        
        try:
            with open(packages_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract Package IDs
            package_ids = []
            if 'd' in data and 'results' in data['d']:
                for pkg in data['d']['results']:
                    if 'Id' in pkg:
                        package_ids.append(pkg['Id'])
            
            logger.info(f"Loaded {len(package_ids)} Package IDs from packages.json")
            return package_ids
            
        except Exception as e:
            logger.error(f"Error loading packages.json: {e}")
            return []
    
    def _download_collections_parallel(self, package_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Download script collections for all packages using parallel processing
        
        Args:
            package_ids: List of Package IDs
            
        Returns:
            Consolidated list of all script collections
        """
        all_collections = []
        
        if self.parallel_downloads == 1:
            # Sequential processing
            logger.info("Using sequential download (parallel_downloads=1)")
            for i, package_id in enumerate(package_ids, 1):
                logger.info(f"Processing package {i}/{len(package_ids)}: {package_id}")
                collections = self._fetch_collections_for_package(package_id)
                all_collections.extend(collections)
        else:
            # Parallel processing
            logger.info(f"Using parallel download with {self.parallel_downloads} workers")
            
            with ThreadPoolExecutor(max_workers=self.parallel_downloads) as executor:
                # Submit all tasks
                future_to_package = {
                    executor.submit(self._fetch_collections_for_package, pkg_id): pkg_id 
                    for pkg_id in package_ids
                }
                
                # Process completed tasks
                completed = 0
                for future in as_completed(future_to_package):
                    package_id = future_to_package[future]
                    completed += 1
                    
                    try:
                        collections = future.result()
                        
                        # Thread-safe aggregation
                        with self.result_lock:
                            all_collections.extend(collections)
                        
                        logger.info(
                            f"Completed {completed}/{len(package_ids)}: "
                            f"{package_id} ({len(collections)} script collections)"
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing package {package_id}: {e}")
        
        return all_collections
    
    def _fetch_collections_for_package(self, package_id: str) -> List[Dict[str, Any]]:
        """
        Fetch script collections for a single package
        
        Args:
            package_id: Package ID
            
        Returns:
            List of script collections for this package
        """
        # Build endpoint
        endpoint = f"IntegrationPackages('{package_id}')/ScriptCollectionDesigntimeArtifacts"
        
        try:
            # Build URL
            url = f"{self.api_base_url}/{endpoint}"
            
            # Make request
            logger.debug(f"Fetching script collections for package: {package_id}")
            data = self._make_request(url)
            
            if data is None:
                return []
            
            # Extract items from OData response
            if 'd' in data and 'results' in data['d']:
                collections = data['d']['results']
                logger.debug(f"Retrieved {len(collections)} script collections from package {package_id}")
                return collections
            else:
                logger.warning(f"Unexpected response structure for package {package_id}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch script collections for package {package_id}: {e}")
            return []