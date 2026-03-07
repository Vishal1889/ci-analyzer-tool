"""
Script Collection Parser for SAP Cloud Integration
Parses script collection artifact data from API responses
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class ScriptCollectionParser:
    """Parses script collection artifact data"""
    
    def parse(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse script collection response data
        
        Args:
            response: API response containing script collection data
            
        Returns:
            List of parsed script collection dictionaries
        """
        logger.info("Parsing Script Collection data...")
        
        results = response.get('d', {}).get('results', [])
        parsed_collections = []
        
        for collection in results:
            parsed_collection = {
                'Id': collection.get('Id'),
                'Version': collection.get('Version'),
                'PackageId': collection.get('PackageId'),
                'Name': collection.get('Name'),
                'Description': collection.get('Description'),
                'ArtifactContent': collection.get('ArtifactContent')
            }
            parsed_collections.append(parsed_collection)
        
        logger.info(f"Parsed {len(parsed_collections)} script collections")
        return parsed_collections