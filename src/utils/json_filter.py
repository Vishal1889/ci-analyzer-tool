"""
JSON filter utility to keep only base-level fields
Removes nested objects and deferred navigation properties
"""

from typing import Dict, List, Any


def filter_base_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter package data to keep only base-level fields
    Removes __metadata and deferred navigation properties
    
    Args:
        data: Raw OData response
        
    Returns:
        Filtered data with only base-level fields
    """
    if 'd' not in data or 'results' not in data['d']:
        return data
    
    filtered_results = []
    for item in data['d']['results']:
        filtered_item = {}
        
        for key, value in item.items():
            # Skip metadata and nested objects
            if key == '__metadata':
                continue
            
            # Skip deferred navigation properties (these are objects with __deferred key)
            if isinstance(value, dict) and '__deferred' in value:
                continue
            
            # Skip other nested objects
            if isinstance(value, dict):
                continue
            
            # Keep simple values (string, number, boolean, null)
            filtered_item[key] = value
        
        filtered_results.append(filtered_item)
    
    return {
        'd': {
            'results': filtered_results
        }
    }


def get_base_level_fields() -> List[str]:
    """
    Get list of expected base-level fields for packages
    Based on reference file structure
    
    Returns:
        List of field names
    """
    return [
        'Id',
        'Name',
        'ResourceId',
        'Description',
        'ShortText',
        'Version',
        'Vendor',
        'PartnerContent',
        'UpdateAvailable',
        'Mode',
        'SupportedPlatform',
        'ModifiedBy',
        'CreationDate',
        'ModifiedDate',
        'CreatedBy',
        'Products',
        'Keywords',
        'Countries',
        'Industries',
        'LineOfBusiness',
        'PackageContent'
    ]