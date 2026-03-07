"""
Parser for Integration Package API responses
Extracts and transforms package data for database storage
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class PackageParser:
    """Parser for integration package data"""
    
    def __init__(self):
        """Initialize parser"""
        pass
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse package API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of parsed package records
        """
        logger.info("Parsing package data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_packages = data['d']['results']
        elif isinstance(data, list):
            raw_packages = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_packages = []
        for pkg in raw_packages:
            parsed_pkg = self._parse_package(pkg)
            parsed_packages.append(parsed_pkg)
        
        logger.info(f"Parsed {len(parsed_packages)} packages")
        return parsed_packages
    
    def _parse_package(self, pkg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse single package record
        
        Args:
            pkg: Raw package data
            
        Returns:
            Parsed package record
        """
        return {
            'Id': pkg.get('Id'),
            'Name': pkg.get('Name'),
            'ResourceId': pkg.get('ResourceId'),
            'Description': pkg.get('Description'),
            'ShortText': pkg.get('ShortText'),
            'Version': pkg.get('Version'),
            'Vendor': pkg.get('Vendor'),
            'PartnerContent': pkg.get('PartnerContent'),
            'UpdateAvailable': pkg.get('UpdateAvailable'),
            'Mode': pkg.get('Mode'),
            'SupportedPlatform': pkg.get('SupportedPlatform'),
            'ModifiedBy': pkg.get('ModifiedBy'),
            'CreationDate': pkg.get('CreationDate'),
            'ModifiedDate': pkg.get('ModifiedDate'),
            'CreatedBy': pkg.get('CreatedBy'),
            'Products': pkg.get('Products'),
            'Keywords': pkg.get('Keywords'),
            'Countries': pkg.get('Countries'),
            'Industries': pkg.get('Industries'),
            'LineOfBusiness': pkg.get('LineOfBusiness'),
            'PackageContent': pkg.get('PackageContent'),
        }