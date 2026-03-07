"""
Package API downloader for SAP Cloud Integration
Downloads integration package data from the OData API
"""

from typing import Dict, Any
from .base_downloader import BaseDownloader
from utils.logger import get_api_logger
from utils.json_filter import filter_base_fields

logger = get_api_logger(__name__)


class PackageDownloader(BaseDownloader):
    """Downloader for Integration Package API"""
    
    def __init__(self, *args, **kwargs):
        """Initialize package downloader"""
        super().__init__(*args, **kwargs)
        self.endpoint = 'IntegrationPackages'
    
    def download(self) -> Dict[str, Any]:
        """
        Download all integration packages
        
        Returns:
            Dictionary with download results including:
            - items: List of package data
            - count: Number of packages downloaded
            - filename: Saved file name
        """
        logger.logger.info("Starting package download...")
        
        # Fetch all packages with pagination
        packages = self._fetch_all_pages(self.endpoint)
        
        # Create response structure
        response_data = {
            'd': {
                'results': packages
            }
        }
        
        # Filter to keep only base-level fields
        logger.logger.info("Filtering response to keep only base-level fields...")
        filtered_data = filter_base_fields(response_data)
        
        # Save filtered data to JSON file
        filename = 'packages.json'
        self._save_json(filtered_data, filename)
        
        result = {
            'items': filtered_data['d']['results'],
            'count': len(filtered_data['d']['results']),
            'filename': filename
        }
        
        logger.logger.info(f"Package download completed. Retrieved {len(packages)} packages (filtered)")
        
        return result
