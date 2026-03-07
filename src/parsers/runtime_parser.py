"""
Parser for Runtime Artifact API responses
Extracts and transforms runtime data for database storage
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class RuntimeArtifactParser:
    """Parser for Runtime Artifact data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Runtime Artifact API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of parsed runtime artifact records
        """
        logger.info("Parsing runtime artifact data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_artifacts = data['d']['results']
        elif isinstance(data, list):
            raw_artifacts = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_artifacts = []
        for artifact in raw_artifacts:
            parsed_artifact = self._parse_artifact(artifact)
            parsed_artifacts.append(parsed_artifact)
        
        logger.info(f"Parsed {len(parsed_artifacts)} runtime artifacts")
        return parsed_artifacts
    
    def _parse_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single runtime artifact record"""
        return {
            'Id': artifact.get('Id'),
            'Version': artifact.get('Version'),
            'Name': artifact.get('Name'),
            'Type': artifact.get('Type'),
            'DeployedBy': artifact.get('DeployedBy'),
            'DeployedOn': artifact.get('DeployedOn'),
            'Status': artifact.get('Status'),
        }