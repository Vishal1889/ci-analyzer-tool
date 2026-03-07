"""
Parsers for Security Artifact API responses
Extracts and transforms security data for database storage
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class UserCredentialParser:
    """Parser for User Credential data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse User Credential API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of parsed user credential records
        """
        logger.info("Parsing user credential data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_credentials = data['d']['results']
        elif isinstance(data, list):
            raw_credentials = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_credentials = []
        for cred in raw_credentials:
            parsed_cred = self._parse_credential(cred)
            parsed_credentials.append(parsed_cred)
        
        logger.info(f"Parsed {len(parsed_credentials)} user credentials")
        return parsed_credentials
    
    def _parse_credential(self, cred: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single user credential record"""
        return {
            'Name': cred.get('Name'),
            'Kind': cred.get('Kind'),
            'Description': cred.get('Description'),
            'User': cred.get('User'),
            'Password': cred.get('Password'),
            'CompanyId': cred.get('CompanyId'),
            'Type': cred.get('Type'),
            'DeployedBy': cred.get('DeployedBy'),
            'DeployedOn': cred.get('DeployedOn'),
            'Status': cred.get('Status'),
        }


class OAuth2ClientCredentialParser:
    """Parser for OAuth2 Client Credential data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse OAuth2 Client Credential API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of parsed OAuth2 client credential records
        """
        logger.info("Parsing OAuth2 client credential data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_credentials = data['d']['results']
        elif isinstance(data, list):
            raw_credentials = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_credentials = []
        for cred in raw_credentials:
            parsed_cred = self._parse_credential(cred)
            parsed_credentials.append(parsed_cred)
        
        logger.info(f"Parsed {len(parsed_credentials)} OAuth2 client credentials")
        return parsed_credentials
    
    def _parse_credential(self, cred: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single OAuth2 client credential record"""
        return {
            'Name': cred.get('Name'),
            'Description': cred.get('Description'),
            'TokenServiceUrl': cred.get('TokenServiceUrl'),
            'ClientId': cred.get('ClientId'),
            'ClientSecret': cred.get('ClientSecret'),
            'ClientAuthentication': cred.get('ClientAuthentication'),
            'Scope': cred.get('Scope'),
            'ScopeContentType': cred.get('ScopeContentType'),
            'Resource': cred.get('Resource'),
            'Audience': cred.get('Audience'),
            'Type': cred.get('Type'),
            'DeployedBy': cred.get('DeployedBy'),
            'DeployedOn': cred.get('DeployedOn'),
            'Status': cred.get('Status'),
        }


class SecureParameterParser:
    """Parser for Secure Parameter data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Secure Parameter API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of parsed secure parameter records
        """
        logger.info("Parsing secure parameter data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_parameters = data['d']['results']
        elif isinstance(data, list):
            raw_parameters = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_parameters = []
        for param in raw_parameters:
            parsed_param = self._parse_parameter(param)
            parsed_parameters.append(parsed_param)
        
        logger.info(f"Parsed {len(parsed_parameters)} secure parameters")
        return parsed_parameters
    
    def _parse_parameter(self, param: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single secure parameter record"""
        return {
            'Name': param.get('Name'),
            'Description': param.get('Description'),
            'SecureParam': param.get('SecureParam'),
            'DeployedBy': param.get('DeployedBy'),
            'DeployedOn': param.get('DeployedOn'),
            'Status': param.get('Status'),
        }


class KeystoreEntryParser:
    """Parser for Keystore Entry data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Keystore Entry API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of parsed keystore entry records
        """
        logger.info("Parsing keystore entry data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_entries = data['d']['results']
        elif isinstance(data, list):
            raw_entries = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_entries = []
        for entry in raw_entries:
            parsed_entry = self._parse_entry(entry)
            parsed_entries.append(parsed_entry)
        
        logger.info(f"Parsed {len(parsed_entries)} keystore entries")
        return parsed_entries
    
    def _parse_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single keystore entry record"""
        return {
            'Hexalias': entry.get('Hexalias'),
            'Alias': entry.get('Alias'),
            'KeyType': entry.get('KeyType'),
            'KeySize': entry.get('KeySize'),
            'ValidNotBefore': entry.get('ValidNotBefore'),
            'ValidNotAfter': entry.get('ValidNotAfter'),
            'SerialNumber': entry.get('SerialNumber'),
            'SignatureAlgorithm': entry.get('SignatureAlgorithm'),
            'EllipticCurve': entry.get('EllipticCurve'),
            'Validity': entry.get('Validity'),
            'SubjectDN': entry.get('SubjectDN'),
            'IssuerDN': entry.get('IssuerDN'),
            'Version': entry.get('Version'),
            'FingerprintSha1': entry.get('FingerprintSha1'),
            'FingerprintSha256': entry.get('FingerprintSha256'),
            'FingerprintSha512': entry.get('FingerprintSha512'),
            'Type': entry.get('Type'),
            'Owner': entry.get('Owner'),
            'LastModifiedBy': entry.get('LastModifiedBy'),
            'LastModifiedTime': entry.get('LastModifiedTime'),
            'CreatedBy': entry.get('CreatedBy'),
            'CreatedTime': entry.get('CreatedTime'),
            'Status': entry.get('Status'),
        }


class AccessPolicyParser:
    """Parser for Access Policy data"""
    
    def parse(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Access Policy API response
        
        Args:
            data: Raw API response data (already normalized by downloader)
            
        Returns:
            List of parsed access policy records
        """
        logger.info("Parsing access policy data...")
        
        # Extract results from OData structure
        if 'd' in data and 'results' in data['d']:
            raw_policies = data['d']['results']
        elif isinstance(data, list):
            raw_policies = data
        else:
            logger.warning(f"Unexpected data structure: {list(data.keys())}")
            return []
        
        parsed_policies = []
        for policy in raw_policies:
            parsed_policy = self._parse_policy(policy)
            parsed_policies.append(parsed_policy)
        
        logger.info(f"Parsed {len(parsed_policies)} access policy records")
        return parsed_policies
    
    def _parse_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single access policy record"""
        return {
            'AccessPolicyID': policy.get('AccessPolicyID'),
            'AccessPolicyName': policy.get('AccessPolicyName'),
            'AccessPolicyDescription': policy.get('AccessPolicyDescription'),
            'ReferenceId': policy.get('ReferenceId'),
            'ReferenceName': policy.get('ReferenceName'),
            'ReferenceDescription': policy.get('ReferenceDescription'),
            'ObjectType': policy.get('ObjectType'),
            'ConditionAttribute': policy.get('ConditionAttribute'),
            'ConditionValue': policy.get('ConditionValue'),
            'ConditionType': policy.get('ConditionType'),
        }
