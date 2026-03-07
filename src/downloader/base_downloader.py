"""
Base downloader for SAP Cloud Integration OData APIs
Provides common functionality for all API downloaders
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

from auth.oauth_client import OAuthClient
from utils.logger import get_api_logger

logger = get_api_logger(__name__)


class BaseDownloader:
    """Base class for API downloaders"""
    
    def __init__(self, oauth_client: OAuthClient, api_base_url: str, 
                 downloads_dir: Path, timeout: int = 30, timestamp: str = None):
        """
        Initialize base downloader
        
        Args:
            oauth_client: OAuth client for authentication
            api_base_url: Base URL for API calls
            downloads_dir: Directory to save downloaded data
            timeout: Request timeout in seconds
            timestamp: Timestamp for organized downloads (format: YYYYMMDD_HHMMSS)
        """
        self.oauth_client = oauth_client
        self.api_base_url = api_base_url.rstrip('/')
        self.timeout = timeout
        self.timestamp = timestamp
        
        # Set download directory (organized by timestamp if provided)
        self.downloads_dir = Path(downloads_dir)
        
        # JSON files subdirectory
        self.json_dir = self.downloads_dir / "json-files"
        
        # Ensure directories exist
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        
        logger.logger.debug(f"Downloader initialized with base URL: {api_base_url}")
        logger.logger.debug(f"Downloads directory: {self.downloads_dir}")
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Full URL
        """
        endpoint = endpoint.lstrip('/')
        return f"{self.api_base_url}/{endpoint}"
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make authenticated API request
        
        Args:
            url: Full URL
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: If request fails
        """
        # Get authentication headers
        headers = self.oauth_client.get_auth_header()
        headers['Accept'] = 'application/json'
        
        # Log request
        logger.log_request('GET', url, headers, params)
        
        # Make request
        start_time = time.time()
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            
            # Log response
            logger.log_response(
                response.status_code,
                elapsed,
                len(response.content) if response.content else 0
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse JSON
            data = response.json()
            
            # Log response data at trace level
            logger.log_response_data(data)
            
            return data
            
        except requests.RequestException as e:
            logger.log_error(e, f"Request to {url}")
            raise
    
    def _fetch_all_pages(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch all pages from paginated API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        url = self._build_url(endpoint)
        
        if params is None:
            params = {}
        
        # OData pagination parameters
        skip = 0
        top = params.get('$top', 50)
        params['$top'] = top
        
        page = 1
        while True:
            params['$skip'] = skip
            
            logger.logger.info(f"Fetching page {page} (skip={skip}, top={top})")
            
            try:
                data = self._make_request(url, params)
                
                # Extract items from OData response
                if 'd' in data and 'results' in data['d']:
                    items = data['d']['results']
                    item_count = len(items)
                    
                    if item_count == 0:
                        logger.logger.info(f"No more items found. Total pages: {page-1}")
                        break
                    
                    all_items.extend(items)
                    logger.logger.info(f"Retrieved {item_count} items. Total so far: {len(all_items)}")
                    
                    # Check if we got fewer items than requested (last page)
                    if item_count < top:
                        logger.logger.info(f"Last page reached. Total items: {len(all_items)}")
                        break
                    
                    skip += top
                    page += 1
                else:
                    logger.logger.warning(f"Unexpected response structure: {list(data.keys())}")
                    break
                    
            except requests.RequestException as e:
                logger.logger.error(f"Error fetching page {page}: {e}")
                break
        
        return all_items
    
    def _save_json(self, data: Any, filename: str):
        """
        Save data to JSON file in json-files subdirectory
        
        Args:
            data: Data to save
            filename: Output filename
        """
        filepath = self.json_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.logger.info(f"Saved {filename} ({self._get_file_size(filepath)})")
    
    def _get_file_size(self, filepath: Path) -> str:
        """
        Get human-readable file size
        
        Args:
            filepath: Path to file
            
        Returns:
            File size string (e.g., "1.5 MB")
        """
        size_bytes = filepath.stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"
    
    def download(self) -> Dict[str, Any]:
        """
        Download data (to be implemented by subclasses)
        
        Returns:
            Dictionary with download results
        """
        raise NotImplementedError("Subclasses must implement download()")