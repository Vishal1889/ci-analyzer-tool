"""
IFLW Channel Extractor for SAP Cloud Integration Analyzer Tool
Extracts communication channel (message flow) information from IFLW (BPMN XML) files
Includes configuration resolution and property promotion
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from utils.logger import get_logger

logger = get_logger(__name__)

# XML Namespaces for IFLW (BPMN 2.0)
NAMESPACES = {
    'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
}

# Priority-ordered lists for property promotion
# Keys are checked in order - first match wins
ADDRESS_KEYS = [
    # Priority 1-9: Protocol and adapter-specific addresses
    "httpAddressWithoutQuery",      # Priority 1: HTTP address without query parameters
    "receiverAccountName",          # Priority 2: Azure Storage - Receiver account name
    "senderAccountName",            # Priority 3: Azure Storage - Sender account name
    "Address_inbound",              # Priority 4: JMS - Inbound address
    "receipientURL",                # Priority 5: AS2/EDI - Recipient URL (typo preserved for compatibility)
    "destination",                  # Priority 6: JMS - Message destination/broker
    "ldapAddress",                  # Priority 7: LDAP server address
    "edmxPath",                     # Priority 8: OData service metadata path
    "urlPath",                      # Priority 9: REST/HTTP URL path component
    
    # Priority 10-11: Generic address variants
    "Address",                      # Priority 10: Generic address (capital A)
    "address",                      # Priority 11: Generic address (lowercase)
    
    # Priority 12-14: Server/host names (most generic)
    "server",                       # Priority 12: Server hostname (SMTP/Database)
    "hosts",                        # Priority 13: Multiple hosts (database clusters)
    "host",                         # Priority 14: Single host address (SFTP/FTP/Generic)
    
    # Additional variants (checked after standard priority list)
    "mdnTargetURL",                 # MDN target URL for AS2
    "wsdlURL",                      # WSDL URL for SOAP
    "soapWsdlURL",                  # SOAP WSDL URL variant
    "providerUrl"                   # Provider URL
]

RESOURCE_KEYS = [
    # Conditional keys (priority 1-2) - require specific conditions
    "topicSubscriptions---if---consumerMode=DIRECT",    # Solace JMS: Topic subscriptions in direct mode
    "queueName---if---consumerMode=GUARANTEED",         # Solace JMS: Queue name in guaranteed mode
    
    # Simple keys (priority 3-18) - direct property name match
    "resourcePathForOdatav4",       # OData v4 resource path
    "receiverContainerName",        # Azure Storage: Container when receiving
    "senderContainerName",          # Azure Storage: Container when sending
    "QueueName_outbound",           # JMS: Outbound queue name
    "QueueName_inbound",            # JMS: Inbound queue name
    "destinationName",              # Generic destination name
    "operationName",                # SOAP operation or REST method name
    "ldapOperation",                # LDAP operation (search, add, modify, delete)
    "resourcePath",                 # REST/HTTP resource path
    "storageName",                  # Cloud storage name
    "queueName",                    # Generic queue name
    "entitySet",                    # OData entity set name
    "folder",                       # File/FTP folder path
    "entity",                       # OData/REST entity name
    "topic",                        # Kafka topic name
    "path"                          # Generic path (most generic, checked last)
]

CREDENTIAL_NAME_KEYS = [
    # Priority 1-2: Role-based authentication
    "userRole---if---senderAuthType=RoleBased",                             # Priority 1: Role-based authentication
    "userRole---if---authentication=basic",                                 # Priority 2: Basic auth with roles
    
    # Priority 3-4: OAuth2 authentication
    "oauth2ClientCredentialsCredentialName---if---authenticationType=OAUTH2---and---oauthCredentialType=OAUTH2_CLIENT_CREDENTIALS",  # Priority 3: OAuth2 client credentials
    "oauth2AuthorizationCodeCredentialName---if---authenticationType=OAUTH2---and---oauthCredentialType=OAUTH2_AUTHORIZATION_CODE",  # Priority 4: OAuth2 authorization code
    
    # Priority 5-7: Component-specific authentication
    "alias---if---authenticationMethod=Basic---and---ComponentType=HCIOData",  # Priority 5: HCI OData basic auth
    "alias---if---ComponentType=SuccessFactors---and---MessageProtocol=SOAP",  # Priority 6: SuccessFactors SOAP
    "alias---if---ComponentType=SuccessFactors---and---MessageProtocol=OData V2",  # Priority 7: SuccessFactors OData V2
    
    # Priority 8-11: Standard authentication methods
    "credentialName---if---authenticationMethod=OAuth2 Client Credentials", # Priority 8: OAuth2 client credentials (generic)
    "credentialName---if---authenticationMethod=Basic",                     # Priority 9: Basic authentication
    "credentialName---if---authentication=Basic",                           # Priority 10: Basic authentication (lowercase)
    "credentialName---if---authentication=SASL",                            # Priority 11: SASL authentication (Kafka, AMQP)
    
    # Priority 12-13: FTP authentication
    "credential_name---if---authentication=user_password",                  # Priority 12: FTP user/password
    "credential_name---if---ComponentType=FTP",                             # Priority 13: Generic FTP credentials
    
    # Priority 14-16: Basic authentication variants
    "BasicAuthCredentialName---if---AuthenticationType=BasicAuthentication", # Priority 14: Basic auth (capitalized)
    "username---if---authenticationType=BASIC",                             # Priority 15: Basic auth username
    "userCredentialAlias---if---authenticationType=BasicAuthentication",    # Priority 16: User credential alias
    
    # Priority 17-19: Other authentication methods
    "user---if---auth=loginPlain",                                          # Priority 17: Plain login
    "credentialName---if---authentication=Transport_OAuth2",                # Priority 18: Transport OAuth2
    "ldapCredentialName---if---ldapAuthentication=ldapAuthenticationSimple", # Priority 19: LDAP simple bind
    
    # Priority 20-23: Azure Storage authentication
    "accessKey---if---receiverAuthorization=SharedAccesskey",               # Priority 20: Azure receiver access key
    "accessKey---if---senderAuthorization=SharedAccesskey",                 # Priority 21: Azure sender access key
    "sasToken---if---receiverAuthorization=SASTOKEN",                       # Priority 22: Azure receiver SAS token
    "sasToken---if---senderAuthorization=SASTOKEN",                         # Priority 23: Azure sender SAS token
    
    # Priority 24-25: Token credentials
    "tokenCredential---if---auth=oauth",                                    # Priority 24: OAuth token credential
    "tokenCredential---if---auth=loginEncrypted",                           # Priority 25: Encrypted login token
    
    # Additional simple keys (checked after all conditional keys)
    #"credentialName",               # Generic credential name (fallback)
    #"credential_name",              # Snake case credential name variant
   # "clientSecurityArtifactValue",  # Client security artifact
    #"BasicAuthCredentialName",      # Basic authentication credential (simple)
   # "UserNameTokenCredentialName",  # Username token credential (SOAP)
   # "WsdlUserNameTokenCredentialName",  # WSDL username token credential
   # "userCredentialAlias",          # User credential alias (simple)
  #  "mdnUserCredentialAlias",       # MDN user credential alias (AS2)
   # "credential",                   # Generic credential
   # "accountName",                  # Account name
   # "alias",                        # Generic alias (fallback)
   # "username",                     # Username (simple)
   # "user",                         # User (simple)
   # "UserName"                      # Username (capital case)
]

AUTHENTICATION_METHOD_KEYS = [
    # Priority 1-2: Azure Storage specific (highest priority)
    "receiverAuthorization",        # Priority 1: Azure receiver authorization method
    "senderAuthorization",          # Priority 2: Azure sender authorization method
    
    # Priority 3: Standard authentication method (most common)
    "authenticationMethod",         # Priority 3: Generic authentication method
    
    # Priority 4-5: Authentication type variants
    "authenticationType",           # Priority 4: Authentication type (lowercase)
    "AuthenticationType",           # Priority 5: Authentication type (capital case)
    
    # Priority 6: LDAP specific
    "ldapAuthentication",           # Priority 6: LDAP-specific authentication
    
    # Priority 7: Sender authentication type
    "senderAuthType",               # Priority 7: Sender authentication type
    
    # Priority 8: Generic authentication
    "authentication",               # Priority 8: Generic authentication (lowercase)
    
    # Priority 9: Short form (most generic)
    "auth",                         # Priority 9: Auth (shortest form)
    
    # Additional variant (checked after standard priority list)
    "mdnAuthenticationType"         # MDN authentication type (AS2)
]

KEY_ALIAS_KEYS = [
    # Priority 1: Client certificates with generic condition
    "clientCertificates---if---authentication=Client Certificate",         # Priority 1: Generic client cert
    
    # Priority 2-5: Private key alias with multiple conditions
    "privateKeyAlias---if---authentication=Client Certificate",            # Priority 2: Generic private key
    "privateKeyAlias---if---authenticationMethod=Client Certificate",      # Priority 3: Standard auth private key
    "privateKeyAlias---if---authentication=public_key",                    # Priority 4: SFTP SSH key
    "privateKeyAlias---if---authenticationType=ClientCertificate",         # Priority 5: Alternative client cert
    
    # Priority 6: Client certificates with sender-specific condition
    "clientCertificates---if---senderAuthType=ClientCertificate",          # Priority 6: Sender client cert
    
    # Additional variants (checked after standard priority list)
   # "privateKeyAlias",              # Generic private key alias (simple)
    "privateKeyAliasForSigning",    # Private key for signing
    "privateKeyAliasForDecryption", # Private key for decryption
    "privateKeyAliasForMDNSigning", # Private key for MDN signing (AS2)
    "PrivateKeyAliasSigning",       # Private key signing (capital case)
    "PrivateKeyAliasResponseSigning", # Private key for response signing
    "mdnPrivateKeyAlias",           # MDN private key alias (AS2)
    "odataCertAuthPrivateKeyAlias", # OData certificate authentication private key
    "keyAlias",                     # Generic key alias
    "alias"                         # Generic alias (fallback)
]

LOCATION_ID_KEYS = [
    # Priority 1-2: Adapter-specific location IDs (highest priority)
    "ldapLocationID",               # Priority 1: LDAP-specific location ID
    "mdnLocationID",                # Priority 2: AS2/MDN-specific location ID
    
    # Priority 3: Cloud Connector specific
    "scc_location_id",              # Priority 3: SAP Cloud Connector location ID (underscore)
    
    # Priority 4-5: Standard variants (capitalized)
    "locationID",                   # Priority 4: Standard location ID (capital D)
    "locationId",                   # Priority 5: Standard location ID (lowercase d)
    
    # Priority 6: Generic (lowercase with underscore)
    "location_id"                   # Priority 6: Generic location ID (underscore)
]


@dataclass
class IflwChannel:
    """Represents an IFLW channel (message flow) with promoted properties"""
    # Basic identification
    id: str
    name: str
    type: str
    participant_id: str
    participant_name: str
    iflow_id: str
    package_id: str
    
    # Promoted fields (all optional)
    component_type: Optional[str] = None
    message_protocol: Optional[str] = None
    transport_protocol: Optional[str] = None
    message_protocol_version: Optional[str] = None
    transport_protocol_version: Optional[str] = None
    system: Optional[str] = None
    address: Optional[str] = None
    address_key: Optional[str] = None
    resource: Optional[str] = None
    resource_key: Optional[str] = None
    authentication_method: Optional[str] = None
    authentication_method_key: Optional[str] = None
    credential_name: Optional[str] = None
    credential_name_key: Optional[str] = None
    key_alias: Optional[str] = None
    key_alias_key: Optional[str] = None
    location_id: Optional[str] = None
    location_id_key: Optional[str] = None
    
    def to_camel_case_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'participantId': self.participant_id,
            'participantName': self.participant_name,
            'iflowId': self.iflow_id,
            'packageId': self.package_id,
            'componentType': self.component_type,
            'messageProtocol': self.message_protocol,
            'transportProtocol': self.transport_protocol,
            'messageProtocolVersion': self.message_protocol_version,
            'transportProtocolVersion': self.transport_protocol_version,
            'system': self.system,
            'address': self.address,
            'addressKey': self.address_key,
            'resource': self.resource,
            'resourceKey': self.resource_key,
            'authenticationMethod': self.authentication_method,
            'authenticationMethodKey': self.authentication_method_key,
            'credentialName': self.credential_name,
            'credentialNameKey': self.credential_name_key,
            'keyAlias': self.key_alias,
            'keyAliasKey': self.key_alias_key,
            'locationId': self.location_id,
            'locationIdKey': self.location_id_key
        }


@dataclass
class IflwChannelProperty:
    """Represents a property of an IFLW channel"""
    package_id: str
    iflow_id: str
    participant_id: str
    participant_name: str
    channel_id: str
    channel_name: str
    key: str
    raw_value: str
    resolved_value: Optional[str] = None
    
    def to_camel_case_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys"""
        return {
            'packageId': self.package_id,
            'iflowId': self.iflow_id,
            'participantId': self.participant_id,
            'participantName': self.participant_name,
            'channelId': self.channel_id,
            'channelName': self.channel_name,
            'key': self.key,
            'rawValue': self.raw_value,
            'resolvedValue': self.resolved_value
        }


@dataclass
class PromotedValue:
    """Helper class for promoted property values"""
    key: str
    value: str


class IflwParticipantChannelAnalyzer:
    """Analyzes IFLW XML to extract channel information for a participant"""
    
    @staticmethod
    def analyze(root: ET.Element, participant_id: str, participant_name: str,
                participant_type: str, iflow_id: str, package_id: str) -> Tuple[List[IflwChannel], List[IflwChannelProperty]]:
        """
        Analyze IFLW XML to extract channels for a specific participant
        
        Args:
            root: XML root element
            participant_id: Participant ID to analyze
            participant_name: Participant name
            participant_type: Participant type (EndpointSender/EndpointReceiver/etc)
            iflow_id: Integration Flow ID
            package_id: Package ID
            
        Returns:
            Tuple of (channels list, properties list)
        """
        channels = []
        properties = []
        
        # Find collaboration element
        collaboration = root.find('.//bpmn2:collaboration', NAMESPACES)
        if collaboration is None:
            logger.debug(f"  No collaboration element found for participant {participant_id}")
            return channels, properties
        
        # Find all message flows
        message_flows = collaboration.findall('bpmn2:messageFlow', NAMESPACES)
        
        # Filter message flows based on participant type
        channels_found = []
        
        # Normalize type (handle SAP typo)
        normalized_type = "EndpointReceiver" if participant_type == "EndpointRecevier" else participant_type
        
        if normalized_type in ["EndpointReceiver"]:
            # For receivers: find flows where targetRef = participant_id
            # Message flows TO receivers can come from process elements (EndEvent, ServiceTask, etc.)
            channels_found = [
                mf for mf in message_flows
                if mf.get('targetRef') == participant_id
            ]
        elif normalized_type == "EndpointSender":
            # For senders: find flows where sourceRef = participant_id
            # Message flows FROM senders go TO process elements (StartEvent, etc.)
            channels_found = [
                mf for mf in message_flows
                if mf.get('sourceRef') == participant_id
            ]
        
        logger.trace(f"    Found {len(channels_found)} channels for participant {participant_id}")
        
        # Extract channel and property information
        for channel_xml in channels_found:
            channel_id = channel_xml.get('id', '')
            channel_name = channel_xml.get('name', '')
            
            # Extract properties from extension elements
            raw_props = IflwParticipantChannelAnalyzer._extract_properties(channel_xml)
            
            # Create channel object (without promoted fields yet)
            channel = IflwChannel(
                id=channel_id,
                name=channel_name,
                type=participant_type,  # Keep original type
                participant_id=participant_id,
                participant_name=participant_name,
                iflow_id=iflow_id,
                package_id=package_id
            )
            channels.append(channel)
            
            # Create property objects
            for key, value in raw_props.items():
                prop = IflwChannelProperty(
                    package_id=package_id,
                    iflow_id=iflow_id,
                    participant_id=participant_id,
                    participant_name=participant_name,
                    channel_id=channel_id,
                    channel_name=channel_name,
                    key=key,
                    raw_value=value,
                    resolved_value=None  # Will be filled by resolver
                )
                properties.append(prop)
            
            logger.trace(f"      Channel {channel_id}: {len(raw_props)} properties")
        
        return channels, properties
    
    @staticmethod
    def _extract_properties(channel_xml: ET.Element) -> Dict[str, str]:
        """
        Extract properties from bpmn2:extensionElements/ifl:property
        
        Args:
            channel_xml: Message flow XML element
            
        Returns:
            Dictionary of property key-value pairs
        """
        props = {}
        
        extension_elements = channel_xml.findall('bpmn2:extensionElements', NAMESPACES)
        
        for ext in extension_elements:
            ifl_properties = ext.findall('ifl:property', NAMESPACES)
            
            for p in ifl_properties:
                # Properties are stored as child elements, not attributes
                key_elem = p.find('key')
                value_elem = p.find('value')
                
                if key_elem is not None and key_elem.text:
                    key = key_elem.text
                    value = value_elem.text if value_elem is not None else ''
                    props[key] = value if value else ''
        
        return props


class IflwParticipantChannelResolver:
    """Resolves configuration placeholders and promotes common properties"""
    
    @staticmethod
    def resolve_config_to_properties(properties: List[IflwChannelProperty],
                                     config: Dict[str, str]):
        """
        Resolve {{placeholder}} values in properties using configuration
        
        Args:
            properties: List of channel properties to resolve
            config: Configuration dictionary {key: value} for the iflow
        """
        if not properties:
            return
        
        if config is None:
            config = {}
        
        for prop in properties:
            prop.resolved_value = IflwParticipantChannelResolver._resolve_one_pass(
                prop.raw_value, config
            )
    
    @staticmethod
    def _resolve_one_pass(input_str: str, config: Dict[str, str]) -> str:
        """
        Replace {{key}} placeholders with values from config dictionary
        
        Args:
            input_str: String potentially containing {{key}} placeholders
            config: Configuration dictionary
            
        Returns:
            String with placeholders replaced (or kept if no value found)
        """
        if not input_str or '{{' not in input_str:
            return input_str
        
        result = []
        i = 0
        
        while i < len(input_str):
            start = input_str.find('{{', i)
            
            if start < 0:
                # No more placeholders
                result.append(input_str[i:])
                break
            
            # Append text before placeholder
            result.append(input_str[i:start])
            
            # Find end of placeholder
            end = input_str.find('}}', start + 2)
            
            if end < 0:
                # Malformed placeholder, keep rest as-is
                result.append(input_str[start:])
                break
            
            # Extract key and lookup value
            key = input_str[start + 2:end]
            value = config.get(key)
            
            if value:
                result.append(value)
            else:
                # Keep placeholder if no value found
                result.append(input_str[start:end + 2])
            
            i = end + 2
        
        return ''.join(result)
    
    @staticmethod
    def promote_common_properties(channels: List[IflwChannel],
                                  properties: List[IflwChannelProperty]):
        """
        Promote common properties to channel-level fields
        
        Args:
            channels: List of channels to populate
            properties: List of properties to promote from
        """
        # Group properties by channel ID
        props_by_channel = {}
        for prop in properties:
            if prop.channel_id not in props_by_channel:
                props_by_channel[prop.channel_id] = []
            props_by_channel[prop.channel_id].append(prop)
        
        # For each channel, promote properties
        for channel in channels:
            props = props_by_channel.get(channel.id, [])
            if not props:
                continue
            
            # Promote simple fields (direct lookup)
            channel.component_type = IflwParticipantChannelResolver._find_value(props, "ComponentType")
            channel.transport_protocol = IflwParticipantChannelResolver._find_value(props, "TransportProtocol")
            channel.message_protocol = IflwParticipantChannelResolver._find_value(props, "MessageProtocol")
            channel.message_protocol_version = IflwParticipantChannelResolver._find_value(props, "MessageProtocolVersion")
            channel.transport_protocol_version = IflwParticipantChannelResolver._find_value(props, "TransportProtocolVersion")
            channel.system = IflwParticipantChannelResolver._find_value(props, "system")
            
            # Promote complex fields (with conditional logic and priority)
            address_pv = IflwParticipantChannelResolver._find_first_promoted(props, ADDRESS_KEYS)
            channel.address = address_pv.value if address_pv else None
            channel.address_key = address_pv.key if address_pv else None
            
            resource_pv = IflwParticipantChannelResolver._find_first_promoted(props, RESOURCE_KEYS)
            channel.resource = resource_pv.value if resource_pv else None
            channel.resource_key = resource_pv.key if resource_pv else None
            
            auth_method_pv = IflwParticipantChannelResolver._find_first_promoted(props, AUTHENTICATION_METHOD_KEYS)
            channel.authentication_method = auth_method_pv.value if auth_method_pv else None
            channel.authentication_method_key = auth_method_pv.key if auth_method_pv else None
            
            credential_pv = IflwParticipantChannelResolver._find_first_promoted(props, CREDENTIAL_NAME_KEYS)
            channel.credential_name = credential_pv.value if credential_pv else None
            channel.credential_name_key = credential_pv.key if credential_pv else None
            
            key_alias_pv = IflwParticipantChannelResolver._find_first_promoted(props, KEY_ALIAS_KEYS)
            channel.key_alias = key_alias_pv.value if key_alias_pv else None
            channel.key_alias_key = key_alias_pv.key if key_alias_pv else None
            
            location_pv = IflwParticipantChannelResolver._find_first_promoted(props, LOCATION_ID_KEYS)
            channel.location_id = location_pv.value if location_pv else None
            channel.location_id_key = location_pv.key if location_pv else None
    
    @staticmethod
    def _find_value(props: List[IflwChannelProperty], key: str) -> Optional[str]:
        """Find property by exact key match"""
        prop = next((p for p in props if p.key == key), None)
        if not prop:
            return None
        return prop.resolved_value or prop.raw_value
    
    @staticmethod
    def _find_first_promoted(props: List[IflwChannelProperty],
                            keys_in_order: List[str]) -> Optional[PromotedValue]:
        """
        Find first matching property from priority list, handling conditional rules
        
        Args:
            props: List of properties to search
            keys_in_order: Priority-ordered list of keys (may include conditions)
            
        Returns:
            PromotedValue with key and value, or None if no match
        """
        for rule in keys_in_order:
            if '---if---' in rule:
                # Conditional rule: "targetKey---if---condKey1=condVal1---and---condKey2=condVal2"
                parts = rule.split('---if---', 1)
                target_key = parts[0]
                cond_part = parts[1]
                conditions = cond_part.split('---and---')
                
                # Check all conditions
                all_matched = True
                for cond in conditions:
                    eq_idx = cond.find('=')
                    if eq_idx <= 0:
                        all_matched = False
                        break
                    
                    cond_key = cond[:eq_idx]
                    cond_val = cond[eq_idx + 1:]
                    
                    # Find the condition property
                    cond_prop = next((p for p in props if p.key == cond_key), None)
                    if not cond_prop:
                        all_matched = False
                        break
                    
                    actual_val = cond_prop.resolved_value or cond_prop.raw_value
                    if actual_val != cond_val:
                        all_matched = False
                        break
                
                if not all_matched:
                    continue
                
                # All conditions matched, find target property
                target_prop = next((p for p in props if p.key == target_key), None)
                if target_prop:
                    value = target_prop.resolved_value or target_prop.raw_value
                    if value is not None:  # Return even if empty string
                        return PromotedValue(key=target_key, value=value)
            else:
                # Simple rule (no conditions)
                prop = next((p for p in props if p.key == rule), None)
                if prop:
                    value = prop.resolved_value or prop.raw_value
                    if value is not None:  # Return even if empty string
                        return PromotedValue(key=rule, value=value)
        
        return None


class IflwChannelExtractor:
    """Main extractor for IFLW channels across all IFLW files"""
    
    def __init__(self, iflw_files_dir: Path, participants_file: Path,
                 configurations_file: Path, output_dir: Path, timestamp: str = None):
        """
        Initialize IFLW Channel Extractor

        Args:
            iflw_files_dir: Directory containing IFLW files
            participants_file: Path to iflw-participants.json
            configurations_file: Path to configurations.json
            output_dir: Directory for output JSON files
            timestamp: Optional timestamp for organized output
        """
        self.iflw_files_dir = Path(iflw_files_dir)
        self.participants_file = Path(participants_file)
        self.configurations_file = Path(configurations_file)
        self.output_dir = Path(output_dir)
        self.timestamp = timestamp
        
        # Track errors
        self.errors = []
        
        logger.info("IflwChannelExtractor initialized")
        logger.info(f"  IFLW files: {self.iflw_files_dir}")
        logger.info(f"  Participants: {self.participants_file}")
        logger.info(f"  Configurations: {self.configurations_file}")
        logger.info(f"  Output: {self.output_dir}")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract channels from all IFLW files
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting IFLW channel extraction...")
        
        stats = {
            "iflw_files_attempted": 0,
            "iflw_files_processed": 0,
            "iflw_files_failed": 0,
            "total_channels_extracted": 0,
            "total_properties_extracted": 0,
            "channels_by_type": {
                "EndpointSender": 0,
                "EndpointReceiver": 0,
                "EndpointRecevier": 0
            }
        }
        
        # Load participants
        participants = self._load_participants()
        if not participants:
            logger.warning("No participants found, cannot extract channels")
            self._save_output([], [])
            return stats
        
        logger.info(f"Loaded {len(participants)} participants")
        
        # Load configurations
        configurations = self._load_configurations()
        logger.info(f"Loaded configurations for {len(configurations)} iflows")
        
        # Check if IFLW directory exists
        if not self.iflw_files_dir.exists():
            logger.warning(f"IFLW files directory not found: {self.iflw_files_dir}")
            self._save_output([], [])
            return stats
        
        # Group participants by iflow_id
        participants_by_iflow = {}
        for p in participants:
            iflow_id = p.get('iflowId', '')
            if iflow_id not in participants_by_iflow:
                participants_by_iflow[iflow_id] = []
            participants_by_iflow[iflow_id].append(p)
        
        logger.info(f"Participants grouped into {len(participants_by_iflow)} iflows")
        
        # Get all IFLW files
        iflw_files = list(self.iflw_files_dir.glob("*.iflw"))
        
        if not iflw_files:
            logger.info("No IFLW files found")
            self._save_output([], [])
            return stats
        
        logger.info(f"Found {len(iflw_files)} IFLW files to process")
        
        # Collect all channels and properties
        all_channels = []
        all_properties = []
        
        # Process each IFLW file
        for idx, iflw_path in enumerate(iflw_files, 1):
            stats["iflw_files_attempted"] += 1
            
            try:
                logger.debug(f"Processing {idx}/{len(iflw_files)}: {iflw_path.name}")
                
                # Extract IDs from filename
                package_id, iflow_id = self._extract_ids_from_filename(iflw_path.name)
                
                # Get participants for this iflow
                iflow_participants = participants_by_iflow.get(iflow_id, [])
                
                if not iflow_participants:
                    logger.debug(f"  No participants found for iflow {iflow_id}")
                    stats["iflw_files_processed"] += 1
                    continue
                
                # Parse XML
                tree = ET.parse(iflw_path)
                root = tree.getroot()
                
                # Get configuration for this iflow
                iflow_config = configurations.get(iflow_id, {})
                
                # Extract channels for each participant
                for participant in iflow_participants:
                    channels, properties = IflwParticipantChannelAnalyzer.analyze(
                        root=root,
                        participant_id=participant['id'],
                        participant_name=participant['name'],
                        participant_type=participant['type'],
                        iflow_id=iflow_id,
                        package_id=package_id
                    )
                    
                    # Resolve configurations
                    IflwParticipantChannelResolver.resolve_config_to_properties(
                        properties, iflow_config
                    )
                    
                    # Promote common properties
                    IflwParticipantChannelResolver.promote_common_properties(
                        channels, properties
                    )
                    
                    # Add to master lists
                    all_channels.extend(channels)
                    all_properties.extend(properties)
                    
                    # Update statistics
                    stats["total_channels_extracted"] += len(channels)
                    stats["total_properties_extracted"] += len(properties)
                    
                    for channel in channels:
                        channel_type = channel.type
                        if channel_type in stats["channels_by_type"]:
                            stats["channels_by_type"][channel_type] += 1
                
                stats["iflw_files_processed"] += 1
                
                if len(all_channels) > 0:
                    logger.debug(f"  Extracted {len([c for c in all_channels if c.iflow_id == iflow_id])} channels")
                
            except Exception as e:
                stats["iflw_files_failed"] += 1
                logger.error(f"  Failed to process {iflw_path.name}: {e}")
                self._track_error(iflw_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save output
        self._save_output(all_channels, all_properties)
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"IFLW channel extraction completed. Processed {stats['iflw_files_processed']}/{stats['iflw_files_attempted']}")
        logger.info(f"Total channels extracted: {stats['total_channels_extracted']}")
        logger.info(f"Total properties extracted: {stats['total_properties_extracted']}")
        
        return stats
    
    def _load_participants(self) -> List[Dict]:
        """Load participants from JSON file"""
        if not self.participants_file.exists():
            logger.warning(f"Participants file not found: {self.participants_file}")
            return []
        
        try:
            with open(self.participants_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load participants: {e}")
            return []
    
    def _load_configurations(self) -> Dict[str, Dict[str, str]]:
        """
        Load configurations from JSON file and build nested dictionary
        
        Returns:
            Dictionary {iflow_id: {param_key: param_value}}
        """
        if not self.configurations_file.exists():
            logger.warning(f"Configurations file not found: {self.configurations_file}")
            return {}
        
        try:
            with open(self.configurations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract results array
            results = data.get('d', {}).get('results', [])
            
            # Build nested dictionary
            config_dict = {}
            for item in results:
                iflow_id = item.get('IflowId', '')
                param_key = item.get('ParameterKey', '')
                param_value = item.get('ParameterValue', '')
                
                if iflow_id and param_key:
                    if iflow_id not in config_dict:
                        config_dict[iflow_id] = {}
                    config_dict[iflow_id][param_key] = param_value
            
            return config_dict
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            return {}
    
    def _extract_ids_from_filename(self, filename: str) -> Tuple[str, str]:
        """Extract package ID and iflow ID from filename"""
        name_without_ext = filename.rsplit('.iflw', 1)[0]
        
        if '---' in name_without_ext:
            parts = name_without_ext.split('---', 1)
            package_id = parts[0].strip()
            iflow_id = parts[1].strip()
        else:
            logger.warning(f"Filename doesn't match expected format: {filename}")
            package_id = ""
            iflow_id = name_without_ext
        
        return package_id, iflow_id
    
    def _save_output(self, channels: List[IflwChannel], properties: List[IflwChannelProperty]):
        """Save channels and properties to JSON files with camelCase keys"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save channels with camelCase keys
        channels_file = self.output_dir / "iflw-channels.json"
        with open(channels_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_camel_case_dict() for c in channels], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(channels)} channels to {channels_file}")
        
        # Save properties with camelCase keys
        properties_file = self.output_dir / "iflw-channels-properties.json"
        with open(properties_file, 'w', encoding='utf-8') as f:
            json.dump([p.to_camel_case_dict() for p in properties], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(properties)} properties to {properties_file}")
    
    def _track_error(self, iflw_name: str, error_type: str, error_message: str):
        """Track extraction error"""
        self.errors.append({
            "IflowFile": iflw_name,
            "ErrorType": error_type,
            "ErrorMessage": error_message[:500],
            "Timestamp": datetime.now().isoformat()
        })
    
    def _save_error_log(self):
        """Save error log to JSON file"""
        output_file = self.output_dir / "iflw-channel-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log: iflw-channel-extraction-errors.json")