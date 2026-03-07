"""
IFlow parser for SAP Cloud Integration
Parses integration flow data from OData API responses
"""

from typing import Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class IFlowParser:
    """Parser for Integration Flow data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse IFlow data from OData response
        
        Args:
            data: OData response containing iflow data
            
        Returns:
            List of parsed iflow dictionaries
        """
        logger.info("Parsing IFlow data...")
        
        iflows = []
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_iflows = data['d']['results']
            
            for raw_iflow in raw_iflows:
                parsed_iflow = self._parse_iflow(raw_iflow)
                if parsed_iflow:
                    iflows.append(parsed_iflow)
        
        logger.info(f"Parsed {len(iflows)} iflows")
        return iflows
    
    def _parse_iflow(self, raw_iflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single iflow record
        
        Args:
            raw_iflow: Raw iflow data from API
            
        Returns:
            Parsed iflow dictionary
        """
        try:
            return {
                'Id': raw_iflow.get('Id'),
                'Version': raw_iflow.get('Version'),
                'PackageId': raw_iflow.get('PackageId'),
                'Name': raw_iflow.get('Name'),
                'Description': raw_iflow.get('Description'),
                'Sender': raw_iflow.get('Sender'),
                'Receiver': raw_iflow.get('Receiver'),
                'CreatedBy': raw_iflow.get('CreatedBy'),
                'CreatedAt': raw_iflow.get('CreatedAt'),
                'ModifiedBy': raw_iflow.get('ModifiedBy'),
                'ModifiedAt': raw_iflow.get('ModifiedAt'),
                'ArtifactContent': raw_iflow.get('ArtifactContent')
            }
        except Exception as e:
            logger.error(f"Error parsing iflow {raw_iflow.get('Id', 'unknown')}: {e}")
            return None