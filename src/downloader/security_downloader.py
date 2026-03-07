"""
Security & Runtime Downloaders for SAP Cloud Integration
Downloads security artifacts and runtime data from various endpoints
"""

from typing import Dict, Any
from pathlib import Path
from .base_downloader import BaseDownloader
from utils.logger import get_logger

logger = get_logger(__name__)


class SecurityDownloader(BaseDownloader):
    """Base downloader for security and runtime artifacts (non-nested, paginated APIs)"""
    
    def __init__(self, oauth_client, api_base_url: str, download_dir: Path, 
                 timeout: int = 30, timestamp: str = None):
        """
        Initialize Security downloader
        
        Args:
            oauth_client: OAuth client for authentication
            api_base_url: Base URL for the API
            download_dir: Directory to save downloaded files
            timeout: Request timeout in seconds
            timestamp: Optional timestamp for organized downloads
        """
        super().__init__(oauth_client, api_base_url, download_dir, timeout, timestamp)
        logger.info("SecurityDownloader initialized")
    
    def download_endpoint(self, endpoint: str, filename: str, description: str) -> Dict[str, Any]:
        """
        Download data from a non-paginated endpoint
        
        Args:
            endpoint: API endpoint (e.g., 'UserCredentials')
            filename: Output filename (e.g., 'security-user-credentials.json')
            description: Human-readable description for logging
            
        Returns:
            Dictionary with 'count' and 'items'
        """
        logger.info(f"Starting {description} download...")
        
        # Build URL (no pagination for security APIs)
        url = f"{self.api_base_url}/{endpoint}"
        
        logger.info(f"Fetching {description}...")
        
        # Make request
        data = self._make_request(url)
        
        if data is None:
            logger.warning(f"No data received for {description}")
            all_items = []
        elif 'd' in data and 'results' in data['d']:
            # Extract items from OData response
            all_items = data['d']['results']
            logger.info(f"Retrieved {len(all_items)} items")
        else:
            logger.warning(f"Unexpected response structure for {description}")
            all_items = []
        
        # Filter to keep only base-level fields and flatten SecurityArtifactDescriptor
        logger.info("Filtering response and flattening SecurityArtifactDescriptor...")
        filtered_items = []
        for item in all_items:
            filtered_item = {}
            for key, value in item.items():
                # Skip metadata
                if key == '__metadata':
                    continue
                # Skip deferred links
                if isinstance(value, dict) and '__deferred' in value:
                    continue
                # Flatten SecurityArtifactDescriptor to top level
                if key == 'SecurityArtifactDescriptor' and isinstance(value, dict):
                    for desc_key, desc_value in value.items():
                        if desc_key != '__metadata':
                            filtered_item[desc_key] = desc_value
                    continue
                # Skip other nested objects
                if isinstance(value, dict):
                    continue
                # Keep simple values
                filtered_item[key] = value
            filtered_items.append(filtered_item)
        
        # Save to file
        output_data = {
            "d": {
                "results": filtered_items
            }
        }
        
        self._save_json(output_data, filename)
        
        logger.info(f"{description} download completed. Retrieved {len(filtered_items)} items (filtered)")
        
        return {
            "count": len(filtered_items),
            "items": filtered_items
        }


class UserCredentialsDownloader(SecurityDownloader):
    """Downloads User Credentials from Security Material API"""
    
    def download(self) -> Dict[str, Any]:
        """Download user credentials"""
        return self.download_endpoint(
            endpoint='UserCredentials',
            filename='security-user-credentials.json',
            description='User Credentials'
        )


class OAuth2ClientCredentialsDownloader(SecurityDownloader):
    """Downloads OAuth2 Client Credentials from Security Material API"""
    
    def download(self) -> Dict[str, Any]:
        """Download OAuth2 client credentials"""
        return self.download_endpoint(
            endpoint='OAuth2ClientCredentials',
            filename='security-oauth2-client-credentials.json',
            description='OAuth2 Client Credentials'
        )


class SecureParametersDownloader(SecurityDownloader):
    """Downloads Secure Parameters from Security Material API"""
    
    def download(self) -> Dict[str, Any]:
        """Download secure parameters"""
        return self.download_endpoint(
            endpoint='SecureParameters',
            filename='security-secure-parameters.json',
            description='Secure Parameters'
        )


class KeystoreEntriesDownloader(SecurityDownloader):
    """Downloads Keystore Entries from Security Material API"""
    
    def download(self) -> Dict[str, Any]:
        """Download keystore entries"""
        return self.download_endpoint(
            endpoint='KeystoreEntries',
            filename='security-keystore-entries.json',
            description='Keystore Entries'
        )


class RuntimeArtifactsDownloader(SecurityDownloader):
    """Downloads Runtime Artifacts from Runtime API"""
    
    def download(self) -> Dict[str, Any]:
        """Download runtime artifacts"""
        return self.download_endpoint(
            endpoint='IntegrationRuntimeArtifacts',
            filename='runtimes.json',
            description='Runtime Artifacts'
        )


class CertificateUserMappingsDownloader(SecurityDownloader):
    """Downloads Certificate-to-User Mappings (NEO only) with certificate parsing"""
    
    def download(self) -> Dict[str, Any]:
        """
        Download certificate-to-user mappings and parse certificates
        Extracts: MappingId, User, SerialNumber, IssuedTo, IssuedBy, ValidFrom, ValidTo
        """
        logger.info("Starting Certificate-to-User Mappings download...")
        
        # Build URL with $select to get only needed fields
        url = f"{self.api_base_url}/CertificateUserMappings?$select=Id,User,Certificate"
        
        logger.info("Fetching Certificate-to-User Mappings...")
        
        # Make request
        data = self._make_request(url)
        
        if data is None:
            logger.warning("No data received for Certificate-to-User Mappings")
            all_items = []
        elif 'd' in data and 'results' in data['d']:
            all_items = data['d']['results']
            logger.info(f"Retrieved {len(all_items)} certificate mappings")
        else:
            logger.warning("Unexpected response structure for Certificate-to-User Mappings")
            all_items = []
        
        # Parse certificates and flatten structure
        logger.info("Parsing certificates and extracting fields...")
        parsed_items = []
        
        for item in all_items:
            mapping_id = item.get('Id')
            user = item.get('User')
            cert_base64 = item.get('Certificate')
            
            # Parse certificate
            if cert_base64:
                cert_info = self._parse_certificate(cert_base64)
            else:
                cert_info = {
                    'SerialNumber': None,
                    'IssuedTo': None,
                    'IssuedBy': None,
                    'ValidFrom': None,
                    'ValidTo': None
                }
            
            # Create flattened record
            parsed_record = {
                'MappingId': mapping_id,
                'User': user,
                'SerialNumber': cert_info['SerialNumber'],
                'IssuedTo': cert_info['IssuedTo'],
                'IssuedBy': cert_info['IssuedBy'],
                'ValidFrom': cert_info['ValidFrom'],
                'ValidTo': cert_info['ValidTo']
            }
            
            parsed_items.append(parsed_record)
        
        # Save parsed data
        output_data = {
            "d": {
                "results": parsed_items
            }
        }
        
        self._save_json(output_data, 'security-certificate-user-mappings.json')
        
        logger.info(f"Certificate-to-User Mappings download completed. Retrieved and parsed {len(parsed_items)} mappings")
        
        return {
            "count": len(parsed_items),
            "items": parsed_items
        }
    
    def _parse_certificate(self, base64_cert: str) -> dict:
        """
        Parse X.509 certificate from base64 string
        Uses the exact algorithm specified by user for SAP NEO certificates
        
        Algorithm:
        1. Perform base64 decode
        2. Check if contents start with '-----BEGIN CERTIFICATE-----'
           - If YES: Extract content between headers and perform second base64 decode
           - If NO: Directly use the decoded bytes as DER certificate
        
        Args:
            base64_cert: Base64-encoded certificate from API
            
        Returns:
            Dictionary with certificate fields
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            import base64
            import re
            
            # Clean the base64 string (remove whitespace, newlines)
            clean_cert = re.sub(r'\s+', '', base64_cert)
            
            # Step 1: Perform first base64 decode
            first_decode_bytes = base64.b64decode(clean_cert)
            
            # Try to decode as UTF-8 to check for PEM headers
            try:
                first_decode_str = first_decode_bytes.decode('utf-8')
                
                # Step 2: Check if contents start with PEM header
                if first_decode_str.startswith('-----BEGIN CERTIFICATE-----'):
                    logger.debug("Detected PEM format after first decode (double base64-encoded PEM)")
                    
                    # Extract content between headers
                    # Remove PEM headers and get just the base64 content
                    pem_content = first_decode_str.replace('-----BEGIN CERTIFICATE-----', '')
                    pem_content = pem_content.replace('-----END CERTIFICATE-----', '')
                    pem_content = pem_content.replace('\n', '').replace('\r', '').strip()
                    
                    # Step 3: Perform second base64 decode to get DER binary
                    cert_bytes = base64.b64decode(pem_content)
                    
                else:
                    # No PEM headers - directly perform second base64 decode
                    logger.debug("No PEM headers found, performing second base64 decode")
                    cert_bytes = base64.b64decode(first_decode_str)
                
                # Parse as DER certificate
                cert = x509.load_der_x509_certificate(cert_bytes, default_backend())
                logger.debug("Successfully parsed certificate")
                
                return {
                    'SerialNumber': str(cert.serial_number),
                    'IssuedTo': cert.subject.rfc4514_string(),
                    'IssuedBy': cert.issuer.rfc4514_string(),
                    'ValidFrom': cert.not_valid_before_utc.isoformat(),
                    'ValidTo': cert.not_valid_after_utc.isoformat()
                }
                    
            except UnicodeDecodeError:
                # Not a UTF-8 string, so it's already binary DER data after first decode
                # This shouldn't happen based on user's algorithm, but handle it anyway
                logger.debug("Binary data after first decode, parsing as DER")
                cert = x509.load_der_x509_certificate(first_decode_bytes, default_backend())
                logger.debug("Successfully parsed certificate from binary")
            
            return {
                'SerialNumber': str(cert.serial_number),
                'IssuedTo': cert.subject.rfc4514_string(),
                'IssuedBy': cert.issuer.rfc4514_string(),
                'ValidFrom': cert.not_valid_before_utc.isoformat(),
                'ValidTo': cert.not_valid_after_utc.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse certificate: {e}")
            return {
                'SerialNumber': None,
                'IssuedTo': None,
                'IssuedBy': None,
                'ValidFrom': None,
                'ValidTo': None
            }


class AccessPoliciesDownloader(SecurityDownloader):
    """Downloads Access Policies with normalized ArtifactReferences"""
    
    def download(self) -> Dict[str, Any]:
        """
        Download access policies and normalize ArtifactReferences
        Creates one record per ArtifactReference with parent policy info
        """
        logger.info("Starting Access Policies download...")
        
        # Build URL with $expand to get ArtifactReferences in one call
        url = f"{self.api_base_url}/AccessPolicies?$expand=ArtifactReferences"
        
        logger.info("Fetching Access Policies with ArtifactReferences...")
        
        # Make request
        data = self._make_request(url)
        
        if data is None:
            logger.warning("No data received for Access Policies")
            all_items = []
        elif 'd' in data and 'results' in data['d']:
            all_items = data['d']['results']
            logger.info(f"Retrieved {len(all_items)} access policies")
        else:
            logger.warning("Unexpected response structure for Access Policies")
            all_items = []
        
        # Normalize: flatten one-to-many relationship
        logger.info("Normalizing Access Policies with ArtifactReferences...")
        normalized_items = []
        
        for policy in all_items:
            # Extract base policy fields
            policy_id = policy.get('Id')
            policy_name = policy.get('RoleName')
            policy_description = policy.get('Description', '')
            
            # Check if policy has ArtifactReferences
            artifact_refs = policy.get('ArtifactReferences', {})
            if isinstance(artifact_refs, dict) and 'results' in artifact_refs:
                refs_list = artifact_refs['results']
                
                if len(refs_list) > 0:
                    # Create one normalized record per ArtifactReference
                    for ref in refs_list:
                        normalized_record = {
                            'AccessPolicyID': policy_id,
                            'AccessPolicyName': policy_name,
                            'AccessPolicyDescription': policy_description,
                            'ReferenceId': ref.get('Id'),
                            'ReferenceName': ref.get('Name'),
                            'ReferenceDescription': ref.get('Description', ''),
                            'ObjectType': ref.get('Type'),
                            'ConditionAttribute': ref.get('ConditionAttribute'),
                            'ConditionValue': ref.get('ConditionValue'),
                            'ConditionType': ref.get('ConditionType')
                        }
                        normalized_items.append(normalized_record)
                else:
                    # Policy has no ArtifactReferences - create record with null references
                    normalized_record = {
                        'AccessPolicyID': policy_id,
                        'AccessPolicyName': policy_name,
                        'AccessPolicyDescription': policy_description,
                        'ReferenceId': None,
                        'ReferenceName': None,
                        'ReferenceDescription': None,
                        'ObjectType': None,
                        'ConditionAttribute': None,
                        'ConditionValue': None,
                        'ConditionType': None
                    }
                    normalized_items.append(normalized_record)
            else:
                # No ArtifactReferences structure - create record with null references
                normalized_record = {
                    'AccessPolicyID': policy_id,
                    'AccessPolicyName': policy_name,
                    'AccessPolicyDescription': policy_description,
                    'ReferenceId': None,
                    'ReferenceName': None,
                    'ReferenceDescription': None,
                    'ObjectType': None,
                    'ConditionAttribute': None,
                    'ConditionValue': None,
                    'ConditionType': None
                }
                normalized_items.append(normalized_record)
        
        # Save normalized data
        output_data = {
            "d": {
                "results": normalized_items
            }
        }
        
        self._save_json(output_data, 'access-policies.json')
        
        logger.info(f"Access Policies download completed. Retrieved {len(all_items)} policies, normalized to {len(normalized_items)} records")
        
        return {
            "count": len(normalized_items),
            "items": normalized_items,
            "original_policy_count": len(all_items)
        }
