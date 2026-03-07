"""
Resource parser for SAP Cloud Integration
Parses resource metadata from OData API responses
"""

from typing import Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class ResourceParser:
    """Parser for Resource data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Resource data from OData response
        
        Args:
            data: OData response containing resource data
            
        Returns:
            List of parsed resource dictionaries
        """
        logger.info("Parsing Resource data...")
        
        resources = []
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_resources = data['d']['results']
            
            for raw_resource in raw_resources:
                parsed_resource = self._parse_resource(raw_resource)
                if parsed_resource:
                    resources.append(parsed_resource)
        
        logger.info(f"Parsed {len(resources)} resources")
        return resources
    
    def _parse_resource(self, raw_resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single resource record
        
        Args:
            raw_resource: Raw resource data from API
            
        Returns:
            Parsed resource dictionary
        """
        try:
            return {
                'Name': raw_resource.get('Name'),
                'ResourceType': raw_resource.get('ResourceType'),
                'ReferencedResourceType': raw_resource.get('ReferencedResourceType'),
                'ResourceSize': raw_resource.get('ResourceSize'),
                'ResourceSizeUnit': raw_resource.get('ResourceSizeUnit'),
                'ResourceContent': raw_resource.get('ResourceContent'),
                'IflowId': raw_resource.get('IflowId'),
                'PackageId': raw_resource.get('PackageId')
            }
        except Exception as e:
            logger.error(f"Error parsing resource {raw_resource.get('Name', 'unknown')}: {e}")
            return None