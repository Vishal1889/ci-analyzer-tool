"""
Authentication Factory for SAP Cloud Integration Analyzer Tool
Creates appropriate authentication client based on configuration
"""

from typing import Union
from auth.oauth_client import OAuthClient
from auth.basic_auth_client import BasicAuthClient
from utils.logger import get_logger

logger = get_logger(__name__)


def create_auth_client(config) -> Union[OAuthClient, BasicAuthClient]:
    """
    Create appropriate authentication client based on configuration
    
    Args:
        config: Application configuration object
        
    Returns:
        OAuthClient or BasicAuthClient instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    auth_type = config.auth_type.upper()
    subaccount_type = config.subaccount_type.upper()
    
    logger.info(f"Creating authentication client: {auth_type} for {subaccount_type} subaccount")
    
    if auth_type == "OAUTH":
        # Create OAuth client
        logger.debug(f"Initializing OAuth client with token URL: {config.oauth_token_url}")
        return OAuthClient(
            token_url=config.oauth_token_url,
            client_id=config.client_id,
            client_secret=config.client_secret,
            timeout=config.api_timeout
        )
    
    elif auth_type == "BASIC":
        # Create Basic Auth client
        masked_username = config.basic_auth_username[:3] + '*' * (len(config.basic_auth_username) - 3) \
                         if len(config.basic_auth_username) > 3 else '***'
        logger.debug(f"Initializing Basic Auth client for user: {masked_username}")
        
        return BasicAuthClient(
            username=config.basic_auth_username,
            password=config.basic_auth_password
        )
    
    else:
        raise ValueError(f"Unknown authentication type: {auth_type}")


def create_discover_auth_client(config) -> OAuthClient:
    """
    Create OAuth authentication client for Discover tenant
    
    Discover tenant always uses OAuth authentication regardless of
    the main tenant's authentication method.
    
    Args:
        config: Application configuration object
        
    Returns:
        OAuthClient instance for Discover tenant
        
    Raises:
        ValueError: If Discover configuration is incomplete
    """
    if not config.has_discover_config():
        raise ValueError(
            "Incomplete Discover configuration. Please ensure all Discover "
            "OAuth parameters are set in .env file."
        )
    
    logger.info("Creating OAuth client for Discover tenant")
    logger.debug(f"Discover token URL: {config.discover_token_url}")
    
    return OAuthClient(
        token_url=config.discover_token_url,
        client_id=config.discover_client_id,
        client_secret=config.discover_client_secret,
        timeout=config.api_timeout
    )