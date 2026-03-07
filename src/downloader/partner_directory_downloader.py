"""
Partner Directory Downloader for SAP Cloud Integration
Downloads binary parameters from Partner Directory and extracts content
"""

import json
import base64
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from .base_downloader import BaseDownloader
from utils.logger import get_logger

logger = get_logger(__name__)


class PartnerDirectoryDownloader(BaseDownloader):
    """Downloads Partner Directory Binary Parameters and extracts binary content"""
    
    # ContentType to file extension mapping
    CONTENT_TYPE_EXTENSIONS = {
        'xml': '.xml',
        'xsl': '.xsl',
        'xsd': '.xsd',
        'json': '.json',
        'text': '.txt',
        'zip': '.zip',
        'gz': '.gz',
        'zlib': '.zlib',
        'crt': '.crt'
    }
    
    def __init__(self, oauth_client, api_base_url: str, download_dir: Path, 
                 timeout: int = 30, timestamp: str = None):
        """
        Initialize Partner Directory downloader
        
        Args:
            oauth_client: OAuth client for authentication
            api_base_url: Base URL for the API
            download_dir: Directory to save downloaded files
            timeout: Request timeout in seconds
            timestamp: Optional timestamp for organized downloads
        """
        super().__init__(oauth_client, api_base_url, download_dir, timeout, timestamp)
        
        # Target directory for binary files
        self.binary_dir = self.downloads_dir / "partner-directory"
        
        # Track extraction errors
        self.extraction_errors = []
        
        logger.info("PartnerDirectoryDownloader initialized")
    
    def download(self) -> Dict[str, Any]:
        """
        Download Partner Directory Binary Parameters
        
        Returns:
            Dictionary with download and extraction statistics
        """
        logger.info("Starting Partner Directory Binary Parameters download...")
        
        # Build URL
        url = f"{self.api_base_url}/BinaryParameters"
        
        logger.info("Fetching Binary Parameters...")
        
        # Make request
        data = self._make_request(url)
        
        if data is None:
            logger.warning("No data received for Binary Parameters")
            return {
                "count": 0,
                "items": [],
                "files_extracted": 0,
                "files_skipped": 0,
                "extraction_stats": {}
            }
        
        # Extract items from OData response
        if 'd' in data and 'results' in data['d']:
            all_items = data['d']['results']
            logger.info(f"Retrieved {len(all_items)} binary parameters")
        else:
            logger.warning("Unexpected response structure for Binary Parameters")
            all_items = []
        
        # Normalize response - keep only required fields
        logger.info("Normalizing response...")
        normalized_items = self._normalize_response(all_items)
        
        # Save normalized JSON (with Value field for extraction)
        output_data = {
            "d": {
                "results": normalized_items
            }
        }
        
        self._save_json(output_data, 'partner-directory-binary.json')
        
        logger.info(f"Saved normalized JSON with {len(normalized_items)} entries")
        
        # Extract binary files
        logger.info("Extracting binary files...")
        extraction_stats = self._extract_binary_files(normalized_items)
        
        logger.info(f"Binary Parameters download completed. Retrieved {len(normalized_items)} parameters")
        logger.info(f"  Files extracted: {extraction_stats['total_extracted']}")
        logger.info(f"  Files skipped (empty value): {extraction_stats['skipped']}")
        
        return {
            "count": len(normalized_items),
            "items": normalized_items,
            "files_extracted": extraction_stats['total_extracted'],
            "files_skipped": extraction_stats['skipped'],
            "extraction_stats": extraction_stats['by_type']
        }
    
    def _normalize_response(self, items: list) -> list:
        """
        Normalize response to keep only required fields
        
        Args:
            items: List of binary parameter items
            
        Returns:
            List of normalized items
        """
        normalized = []
        
        for item in items:
            normalized_item = {
                'Pid': item.get('Pid'),
                'Id': item.get('Id'),
                'LastModifiedBy': item.get('LastModifiedBy'),
                'LastModifiedTime': item.get('LastModifiedTime'),
                'CreatedBy': item.get('CreatedBy'),
                'CreatedTime': item.get('CreatedTime'),
                'ContentType': item.get('ContentType'),
                'Value': item.get('Value')  # Keep for extraction, will be excluded from DB
            }
            normalized.append(normalized_item)
        
        return normalized
    
    def _extract_binary_files(self, items: list) -> Dict[str, Any]:
        """
        Extract binary files from normalized items
        
        Args:
            items: List of normalized binary parameter items
            
        Returns:
            Dictionary with extraction statistics
        """
        stats = {
            'total_extracted': 0,
            'skipped': 0,
            'by_type': {}
        }
        
        for item in items:
            pid = item.get('Pid')
            item_id = item.get('Id')
            content_type = item.get('ContentType', 'unknown')
            value = item.get('Value')
            
            # Skip if value is empty or None
            if not value:
                stats['skipped'] += 1
                logger.debug(f"Skipped {pid}---{item_id} (empty value)")
                continue
            
            try:
                # Decode base64 content
                decoded_content = base64.b64decode(value)
                
                # Get file extension
                extension = self._get_file_extension(content_type)
                
                # Create target directory for this content type
                target_dir = self.binary_dir / content_type
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Create filename: {PID}---{ID}.{extension}
                filename = f"{pid}---{item_id}{extension}"
                output_path = target_dir / filename
                
                # Write binary content
                with open(output_path, 'wb') as f:
                    f.write(decoded_content)
                
                # Update statistics
                stats['total_extracted'] += 1
                stats['by_type'][content_type] = stats['by_type'].get(content_type, 0) + 1
                
                logger.debug(f"Extracted: {filename} to {content_type}/")
                
            except Exception as e:
                logger.error(f"Failed to extract {pid}---{item_id}: {e}")
                self._track_extraction_error(pid, item_id, content_type, str(e))
        
        # Save extraction error log if there are errors
        if self.extraction_errors:
            self._save_extraction_error_log()
        
        return stats
    
    def _get_file_extension(self, content_type: str) -> str:
        """
        Get file extension for content type
        
        Args:
            content_type: Content type string
            
        Returns:
            File extension with dot (e.g., '.xml')
        """
        # Return mapped extension or use content_type as-is with dot
        return self.CONTENT_TYPE_EXTENSIONS.get(content_type.lower(), f'.{content_type.lower()}')
    
    def _track_extraction_error(self, pid: str, item_id: str, content_type: str, error_message: str):
        """Track extraction error for later reporting"""
        error_record = {
            "Pid": pid,
            "Id": item_id,
            "ContentType": content_type,
            "ErrorMessage": error_message[:500],
            "Timestamp": datetime.now().isoformat()
        }
        
        self.extraction_errors.append(error_record)
    
    def _save_extraction_error_log(self):
        """Save extraction error log to JSON file"""
        output_file = self.downloads_dir / "partner-directory-extraction-errors.json"
        
        output_data = {
            "errors": self.extraction_errors,
            "total_errors": len(self.extraction_errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log with {len(self.extraction_errors)} errors")