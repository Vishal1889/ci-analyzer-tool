"""
Value Mapping Parser for SAP Cloud Integration
Parses value mapping artifact data from API responses
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class ValueMappingParser:
    """Parses value mapping artifact data"""
    
    def parse(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse value mapping response data
        
        Args:
            response: API response containing value mapping data
            
        Returns:
            List of parsed value mapping dictionaries
        """
        logger.info("Parsing Value Mapping data...")
        
        results = response.get('d', {}).get('results', [])
        parsed_mappings = []
        
        for mapping in results:
            parsed_mapping = {
                'Id': mapping.get('Id'),
                'Version': mapping.get('Version'),
                'PackageId': mapping.get('PackageId'),
                'Name': mapping.get('Name'),
                'Description': mapping.get('Description'),
                'ArtifactContent': mapping.get('ArtifactContent')
            }
            parsed_mappings.append(parsed_mapping)
        
        logger.info(f"Parsed {len(parsed_mappings)} value mappings")
        return parsed_mappings