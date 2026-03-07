"""
IFlow API downloader for SAP Cloud Integration
Downloads integration flow data from the OData API with parallel processing support
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from .base_downloader import BaseDownloader
from utils.logger import get_api_logger
from utils.json_filter import filter_base_fields

logger = get_api_logger(__name__)


class IFlowDownloader(BaseDownloader):
    """Downloader for Integration Flow API with parallel processing"""
    
    def __init__(self, *args, parallel_downloads: int = 1, **kwargs):
        """
        Initialize IFlow downloader
        
        Args:
            parallel_downloads: Number of concurrent package downloads (1-10)
        """
        super().__init__(*args, **kwargs)
        self.parallel_downloads = max(1, min(10, parallel_downloads))
        self.result_lock = Lock()  # Thread-safe result aggregation
        
    def download(self) -> Dict[str, Any]:
        """
        Download all integration flows from all packages
        
        Returns:
            Dictionary with download results including:
            - items: List of iflow data
            - count: Number of iflows downloaded
            - filename: Saved file name
        """
        logger.logger.info("Starting IFlow download...")
        logger.logger.info(f"Parallel downloads: {self.parallel_downloads}")
        
        # Load packages to get Package IDs
        package_ids = self._load_package_ids()
        
        if not package_ids:
            logger.logger.warning("No packages found. Cannot download IFlows.")
            return {
                'items': [],
                'count': 0,
                'filename': 'iflows.json'
            }
        
        logger.logger.info(f"Found {len(package_ids)} packages to process")
        
        # Download IFlows with parallel processing
        all_iflows = self._download_iflows_parallel(package_ids)
        
        # Create response structure
        response_data = {
            'd': {
                'results': all_iflows
            }
        }
        
        # Filter to keep only base-level fields
        logger.logger.info("Filtering response to keep only base-level fields...")
        filtered_data = filter_base_fields(response_data)
        
        # Save filtered data to JSON file
        filename = 'iflows.json'
        self._save_json(filtered_data, filename)
        
        result = {
            'items': filtered_data['d']['results'],
            'count': len(filtered_data['d']['results']),
            'filename': filename
        }
        
        logger.logger.info(f"IFlow download completed. Retrieved {len(all_iflows)} iflows (filtered)")
        
        return result
    
    def _load_package_ids(self) -> List[str]:
        """
        Load Package IDs from packages.json
        
        Returns:
            List of Package IDs
        """
        packages_file = self.json_dir / 'packages.json'
        
        if not packages_file.exists():
            logger.logger.error(f"packages.json not found at {packages_file}")
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
            
            logger.logger.info(f"Loaded {len(package_ids)} Package IDs from packages.json")
            return package_ids
            
        except Exception as e:
            logger.logger.error(f"Error loading packages.json: {e}")
            return []
    
    def _download_iflows_parallel(self, package_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Download IFlows for all packages using parallel processing
        
        Args:
            package_ids: List of Package IDs
            
        Returns:
            Consolidated list of all IFlows
        """
        all_iflows = []
        
        if self.parallel_downloads == 1:
            # Sequential processing
            logger.logger.info("Using sequential download (parallel_downloads=1)")
            for i, package_id in enumerate(package_ids, 1):
                logger.logger.info(f"Processing package {i}/{len(package_ids)}: {package_id}")
                iflows = self._fetch_iflows_for_package(package_id)
                all_iflows.extend(iflows)
        else:
            # Parallel processing
            logger.logger.info(f"Using parallel download with {self.parallel_downloads} workers")
            
            with ThreadPoolExecutor(max_workers=self.parallel_downloads) as executor:
                # Submit all tasks
                future_to_package = {
                    executor.submit(self._fetch_iflows_for_package, pkg_id): pkg_id 
                    for pkg_id in package_ids
                }
                
                # Process completed tasks
                completed = 0
                for future in as_completed(future_to_package):
                    package_id = future_to_package[future]
                    completed += 1
                    
                    try:
                        iflows = future.result()
                        
                        # Thread-safe aggregation
                        with self.result_lock:
                            all_iflows.extend(iflows)
                        
                        logger.logger.info(
                            f"Completed {completed}/{len(package_ids)}: "
                            f"{package_id} ({len(iflows)} iflows)"
                        )
                        
                    except Exception as e:
                        logger.logger.error(f"Error processing package {package_id}: {e}")
        
        return all_iflows
    
    def _fetch_iflows_for_package(self, package_id: str) -> List[Dict[str, Any]]:
        """
        Fetch IFlows for a single package
        
        Args:
            package_id: Package ID
            
        Returns:
            List of IFlows for this package
        """
        # Build endpoint with proper escaping
        endpoint = f"IntegrationPackages('{package_id}')/IntegrationDesigntimeArtifacts"
        
        try:
            # Build URL
            url = self._build_url(endpoint)
            
            # Make request (no pagination needed for single package)
            logger.logger.debug(f"Fetching IFlows for package: {package_id}")
            data = self._make_request(url)
            
            # Extract items from OData response
            if 'd' in data and 'results' in data['d']:
                iflows = data['d']['results']
                logger.logger.debug(f"Retrieved {len(iflows)} iflows from package {package_id}")
                return iflows
            else:
                logger.logger.warning(f"Unexpected response structure for package {package_id}")
                return []
                
        except Exception as e:
            logger.logger.error(f"Failed to fetch IFlows for package {package_id}: {e}")
            return []