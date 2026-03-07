"""
Configuration API downloader for SAP Cloud Integration
Downloads configuration metadata from the OData API with parallel processing support
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


class ConfigurationDownloader(BaseDownloader):
    """Downloader for Integration Flow Configurations API with parallel processing"""
    
    def __init__(self, *args, parallel_downloads: int = 1, **kwargs):
        """
        Initialize Configuration downloader
        
        Args:
            parallel_downloads: Number of concurrent IFlow configuration downloads (1-10)
        """
        super().__init__(*args, **kwargs)
        self.parallel_downloads = max(1, min(10, parallel_downloads))
        self.result_lock = Lock()  # Thread-safe result aggregation
        
    def download(self) -> Dict[str, Any]:
        """
        Download all configurations from all integration flows
        
        Returns:
            Dictionary with download results including:
            - items: List of configuration data
            - count: Number of configurations downloaded
            - filename: Saved file name
        """
        logger.logger.info("Starting Configuration download...")
        logger.logger.info(f"Parallel downloads: {self.parallel_downloads}")
        
        # Load IFlows to get IFlow IDs
        iflow_ids = self._load_iflow_ids()
        
        if not iflow_ids:
            logger.logger.warning("No IFlows found. Cannot download Configurations.")
            return {
                'items': [],
                'count': 0,
                'filename': 'configurations.json'
            }
        
        logger.logger.info(f"Found {len(iflow_ids)} IFlows to process")
        
        # Download Configurations with parallel processing
        all_configurations = self._download_configurations_parallel(iflow_ids)
        
        # Create response structure
        response_data = {
            'd': {
                'results': all_configurations
            }
        }
        
        # Filter to keep only base-level fields
        logger.logger.info("Filtering response to keep only base-level fields...")
        filtered_data = filter_base_fields(response_data)
        
        # Save filtered data to JSON file
        filename = 'configurations.json'
        self._save_json(filtered_data, filename)
        
        result = {
            'items': filtered_data['d']['results'],
            'count': len(filtered_data['d']['results']),
            'filename': filename
        }
        
        logger.logger.info(f"Configuration download completed. Retrieved {len(all_configurations)} configurations (filtered)")
        
        return result
    
    def _load_iflow_ids(self) -> List[str]:
        """
        Load IFlow IDs from iflows.json
        
        Returns:
            List of IFlow IDs
        """
        iflows_file = self.json_dir / 'iflows.json'
        
        if not iflows_file.exists():
            logger.logger.error(f"iflows.json not found at {iflows_file}")
            return []
        
        try:
            with open(iflows_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract IFlow IDs
            iflow_ids = []
            if 'd' in data and 'results' in data['d']:
                for iflow in data['d']['results']:
                    if 'Id' in iflow:
                        iflow_ids.append(iflow['Id'])
            
            logger.logger.info(f"Loaded {len(iflow_ids)} IFlow IDs from iflows.json")
            return iflow_ids
            
        except Exception as e:
            logger.logger.error(f"Error loading iflows.json: {e}")
            return []
    
    def _download_configurations_parallel(self, iflow_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Download Configurations for all IFlows using parallel processing
        
        Args:
            iflow_ids: List of IFlow IDs
            
        Returns:
            Consolidated list of all Configurations
        """
        all_configurations = []
        
        if self.parallel_downloads == 1:
            # Sequential processing
            logger.logger.info("Using sequential download (parallel_downloads=1)")
            for i, iflow_id in enumerate(iflow_ids, 1):
                logger.logger.info(f"Processing IFlow {i}/{len(iflow_ids)}: {iflow_id}")
                configurations = self._fetch_configurations_for_iflow(iflow_id)
                all_configurations.extend(configurations)
        else:
            # Parallel processing
            logger.logger.info(f"Using parallel download with {self.parallel_downloads} workers")
            
            with ThreadPoolExecutor(max_workers=self.parallel_downloads) as executor:
                # Submit all tasks
                future_to_iflow = {
                    executor.submit(self._fetch_configurations_for_iflow, iflow_id): iflow_id 
                    for iflow_id in iflow_ids
                }
                
                # Process completed tasks
                completed = 0
                for future in as_completed(future_to_iflow):
                    iflow_id = future_to_iflow[future]
                    completed += 1
                    
                    try:
                        configurations = future.result()
                        
                        # Thread-safe aggregation
                        with self.result_lock:
                            all_configurations.extend(configurations)
                        
                        logger.logger.info(
                            f"Completed {completed}/{len(iflow_ids)}: "
                            f"{iflow_id} ({len(configurations)} configurations)"
                        )
                        
                    except Exception as e:
                        logger.logger.error(f"Error processing IFlow {iflow_id}: {e}")
        
        return all_configurations
    
    def _fetch_configurations_for_iflow(self, iflow_id: str) -> List[Dict[str, Any]]:
        """
        Fetch Configurations for a single IFlow and enrich with IflowId and PackageId
        
        Args:
            iflow_id: IFlow ID
            
        Returns:
            List of Configurations for this IFlow (enriched with IflowId and PackageId)
        """
        # Build endpoint with proper escaping - use Version='Active'
        endpoint = f"IntegrationDesigntimeArtifacts(Id='{iflow_id}',Version='Active')/Configurations"
        
        try:
            # Build URL
            url = self._build_url(endpoint)
            
            # Make request (no pagination needed for single IFlow)
            logger.logger.debug(f"Fetching Configurations for IFlow: {iflow_id}")
            data = self._make_request(url)
            
            # Extract items from OData response and enrich with IflowId and PackageId
            if 'd' in data and 'results' in data['d']:
                configurations = data['d']['results']
                
                # Get PackageId for this IFlow from iflows.json
                package_id = self._get_package_id_for_iflow(iflow_id)
                
                # Filter out SAP_ProfileId and enrich each configuration with IflowId and PackageId
                enriched_configurations = []
                for configuration in configurations:
                    # Filter out SAP_ProfileId parameter (case-insensitive)
                    param_key = configuration.get('ParameterKey', '')
                    if param_key and param_key.lower() == 'sap_profileid':
                        logger.logger.trace(f"Filtering out SAP_ProfileId parameter from IFlow {iflow_id}")
                        continue
                    
                    configuration['IflowId'] = iflow_id
                    configuration['PackageId'] = package_id
                    enriched_configurations.append(configuration)
                
                logger.logger.debug(f"Retrieved {len(enriched_configurations)} configurations from IFlow {iflow_id} (after filtering)")
                return enriched_configurations
            else:
                logger.logger.warning(f"Unexpected response structure for IFlow {iflow_id}")
                return []
                
        except Exception as e:
            logger.logger.error(f"Failed to fetch Configurations for IFlow {iflow_id}: {e}")
            return []
    
    def _get_package_id_for_iflow(self, iflow_id: str) -> str:
        """
        Get PackageId for a given IFlow ID by reading from iflows.json
        
        Args:
            iflow_id: IFlow ID
            
        Returns:
            PackageId for the IFlow, or None if not found
        """
        iflows_file = self.json_dir / 'iflows.json'
        
        try:
            with open(iflows_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find the IFlow and return its PackageId
            if 'd' in data and 'results' in data['d']:
                for iflow in data['d']['results']:
                    if iflow.get('Id') == iflow_id:
                        return iflow.get('PackageId')
            
            return None
            
        except Exception as e:
            logger.logger.error(f"Error getting PackageId for IFlow {iflow_id}: {e}")
            return None