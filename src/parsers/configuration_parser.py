"""
Configuration parser for SAP Cloud Integration
Parses configuration data from the OData API response
"""

from typing import Dict, Any, List
from utils.logger import get_api_logger

logger = get_api_logger(__name__)


class ConfigurationParser:
    """Parser for Configuration API responses"""
    
    def parse(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse configuration data from API response
        
        Args:
            response_data: Raw API response data
            
        Returns:
            List of parsed configuration dictionaries
        """
        logger.logger.info("Parsing Configuration data...")
        
        configurations = []
        
        if 'd' in response_data and 'results' in response_data['d']:
            for config in response_data['d']['results']:
                parsed_config = self._parse_configuration(config)
                if parsed_config:
                    configurations.append(parsed_config)
        
        logger.logger.info(f"Parsed {len(configurations)} configurations")
        return configurations
    
    def _parse_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse individual configuration entry
        
        Args:
            config: Raw configuration data
            
        Returns:
            Parsed configuration dictionary
        """
        try:
            return {
                'parameter_key': config.get('ParameterKey'),
                'parameter_value': config.get('ParameterValue'),
                'data_type': config.get('DataType'),
                'description': config.get('Description'),
                'iflow_id': config.get('IflowId'),
                'package_id': config.get('PackageId')
            }
        except Exception as e:
            logger.logger.error(f"Error parsing configuration: {e}")
            return None