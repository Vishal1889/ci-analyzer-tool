"""
Discover Version Checker for SAP Cloud Integration Analyzer Tool
Checks latest package versions available in SAP Discover tenant
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from auth.oauth_client import OAuthClient
from utils.logger import get_logger

logger = get_logger(__name__)


class DiscoverVersionChecker:
    """Checks latest package versions from Discover tenant"""
    
    def __init__(self, oauth_client: OAuthClient, discover_base_url: str, 
                 download_dir: Path, timeout: int = 30, timestamp: str = None):
        """
        Initialize Discover Version Checker
        
        Args:
            oauth_client: OAuth client for Discover tenant authentication
            discover_base_url: Base URL for Discover tenant API
            download_dir: Directory to save results
            timeout: Request timeout in seconds
            timestamp: Optional timestamp for organized downloads
        """
        self.oauth_client = oauth_client
        self.discover_base_url = discover_base_url.rstrip('/')
        self.download_dir = Path(download_dir)
        self.timeout = timeout
        self.timestamp = timestamp
        
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("DiscoverVersionChecker initialized")
    
    def check_versions(self, packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check Discover versions for SAP and Partner packages
        
        Args:
            packages: List of package dictionaries from packages.json
            
        Returns:
            Dictionary with count and results list
        """
        logger.info("Starting Discover version check...")
        
        # Filter packages: Vendor="SAP" OR PartnerContent=true
        sap_partner_packages = [
            pkg for pkg in packages 
            if pkg.get('Vendor') == 'SAP' or pkg.get('PartnerContent') == True
        ]
        
        logger.info(f"Found {len(sap_partner_packages)} SAP/Partner packages to check")
        
        results = []
        
        for idx, package in enumerate(sap_partner_packages, 1):
            package_id = package.get('Id')
            package_name = package.get('Name', 'Unknown')
            
            logger.info(f"Checking {idx}/{len(sap_partner_packages)}: {package_id}")
            
            discover_version = self._check_package_version(package_id)
            
            results.append({
                "PackageID": package_id,
                "PackageName": package_name,
                "CurrentVersion": package.get('Version'),
                "DiscoverVersion": discover_version
            })
            
            logger.info(f"  Result: {discover_version}")
        
        # Save results
        output_data = {
            "d": {
                "results": results
            }
        }
        
        output_file = self.download_dir / "discover-versions.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        file_size = output_file.stat().st_size
        if file_size >= 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} B"
        
        logger.info(f"Saved discover-versions.json ({size_str})")
        logger.info(f"Discover version check completed. Checked {len(results)} packages")
        
        return {
            "count": len(results),
            "results": results
        }
    
    def _check_package_version(self, package_id: str) -> str:
        """
        Check Discover version for a single package
        
        Args:
            package_id: Package ID to check
            
        Returns:
            Version string or "Manual check needed"
        """
        # First attempt: Try with full package ID
        version = self._try_copy_package(package_id)
        
        if version:
            return version
        
        # First attempt failed (404) - package likely has suffix
        # Split on first dot and retry with base ID
        if '.' in package_id:
            base_id = package_id.split('.', 1)[0]
            logger.info(f"  Retrying with base ID: {base_id}")
            
            version = self._try_copy_package(base_id)
            
            if version:
                return version
        
        # Both attempts failed
        logger.warning(f"  Could not determine Discover version for {package_id}")
        return "Manual check needed"
    
    def _try_copy_package(self, package_id: str) -> str:
        """
        Try to copy package and extract version
        
        Args:
            package_id: Package ID to copy
            
        Returns:
            Version string if successful, None if failed
        """
        import requests
        
        try:
            # POST to copy package with suffix
            url = f"{self.discover_base_url}/CopyIntegrationPackage"
            params = {
                'Id': f"'{package_id}'",
                'ImportMode': "'CREATE_COPY'",
                'Suffix': "'MADELETE'"
            }
            
            # Get access token
            token = self.oauth_client.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            logger.debug(f"  POST {url}")
            response = requests.post(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check for 404 - package has suffix or doesn't exist
            if response.status_code == 404:
                logger.debug(f"  404 Not Found - package may have suffix")
                return None
            
            # Check for success (201 Created)
            if response.status_code != 201:
                logger.warning(f"  Unexpected status {response.status_code}: {response.text}")
                return None
            
            # Extract version and created package ID from response
            data = response.json()
            version = data.get('d', {}).get('Version')
            created_package_id = data.get('d', {}).get('Id')
            
            if not version:
                logger.warning(f"  Version not found in response")
                return None
            
            logger.info(f"  Found version: {version}")
            
            # Delete the created package
            if created_package_id:
                self._delete_package(created_package_id)
            
            return version
            
        except requests.exceptions.Timeout:
            logger.error(f"  Timeout while copying package {package_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request error while copying package {package_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"  Unexpected error while copying package {package_id}: {e}")
            return None
    
    def _delete_package(self, package_id: str) -> bool:
        """
        Delete a package from Discover tenant
        
        Args:
            package_id: Package ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        import requests
        
        try:
            url = f"{self.discover_base_url}/IntegrationPackages('{package_id}')"
            
            # Get access token
            token = self.oauth_client.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            logger.debug(f"  DELETE {url}")
            response = requests.delete(
                url,
                headers=headers,
                timeout=self.timeout
            )
            
            # 202 Accepted is the expected success response
            if response.status_code == 202:
                logger.debug(f"  Package {package_id} deleted successfully")
                return True
            else:
                logger.warning(f"  Delete returned status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"  Timeout while deleting package {package_id}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"  Request error while deleting package {package_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"  Unexpected error while deleting package {package_id}: {e}")
            return False