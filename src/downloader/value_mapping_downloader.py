"""
Value Mapping Downloader for SAP Cloud Integration
Downloads value mapping artifacts from the Integration Content API
"""

from pathlib import Path
from typing import Dict, Any, List
from .base_downloader import BaseDownloader
from utils.logger import get_logger

logger = get_logger(__name__)


class ValueMappingDownloader(BaseDownloader):
    """Downloads Value Mapping artifacts"""
    
    def __init__(self, oauth_client, api_base_url: str, download_dir: Path, 
                 timeout: int = 30, timestamp: str = None):
        """
        Initialize Value Mapping downloader
        
        Args:
            oauth_client: OAuth client for authentication
            api_base_url: Base URL for the API
            download_dir: Directory to save downloaded files
            timeout: Request timeout in seconds
            timestamp: Optional timestamp for organized downloads
        """
        super().__init__(oauth_client, api_base_url, download_dir, timeout, timestamp)
        logger.info("ValueMappingDownloader initialized")
    
    def download(self) -> Dict[str, Any]:
        """
        Download all value mapping artifacts
        
        Returns:
            Dictionary with 'count' and 'items' (filtered)
        """
        logger.info("Starting value mapping download...")
        
        endpoint = "ValueMappingDesigntimeArtifacts"
        all_items = []
        skip = 0
        top = 50
        
        while True:
            # Construct URL with pagination
            url = f"{self.api_base_url}/{endpoint}?$skip={skip}&$top={top}"
            
            logger.info(f"Fetching page {(skip // top) + 1} (skip={skip}, top={top})")
            
            # Make API request
            response = self._make_request(url)
            
            if response is None:
                logger.error("Failed to fetch value mappings")
                break
            
            # Extract results
            results = response.get('d', {}).get('results', [])
            
            if not results:
                logger.info("Last page reached. Total items: {}".format(len(all_items)))
                break
            
            all_items.extend(results)
            logger.info(f"Retrieved {len(results)} items. Total so far: {len(all_items)}")
            
            # Check if there are more pages
            if len(results) < top:
                logger.info("Last page reached. Total items: {}".format(len(all_items)))
                break
            
            skip += top
        
        # Filter to keep only base-level fields
        logger.info("Filtering response to keep only base-level fields...")
        filtered_items = []
        for item in all_items:
            filtered_item = {}
            for key, value in item.items():
                # Skip metadata and nested objects
                if key == '__metadata':
                    continue
                if isinstance(value, dict) and '__deferred' in value:
                    continue
                if isinstance(value, dict):
                    continue
                # Keep simple values
                filtered_item[key] = value
            filtered_items.append(filtered_item)
        
        # Save to file
        output_data = {
            "d": {
                "results": filtered_items
            }
        }
        
        filename = "value-mappings.json"
        self._save_json(output_data, filename)
        
        logger.info(f"Value mapping download completed. Retrieved {len(filtered_items)} value mappings (filtered)")
        
        return {
            "count": len(filtered_items),
            "items": filtered_items
        }