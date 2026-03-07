"""
Basic Authentication Client for SAP Cloud Integration API
Used primarily for Neo subaccounts
"""

import base64
from typing import Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class BasicAuthClient:
    """Basic Authentication client for SAP Cloud Integration"""
    
    def __init__(self, username: str, password: str):
        """
        Initialize Basic Auth client
        
        Args:
            username: Basic auth username (S-user, P-user, or technical user)
            password: Basic auth password
        """
        self.username = username
        self.password = password
        
        # Pre-compute base64 encoded credentials
        credentials = f"{username}:{password}"
        self._encoded_credentials = base64.b64encode(
            credentials.encode('utf-8')
        ).decode('utf-8')
        
        # Mask username for logging (show first 3 chars only)
        masked_username = username[:3] + '*' * (len(username) - 3) if len(username) > 3 else '***'
        logger.debug(f"Basic Auth client initialized for user {masked_username}")
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get access token (not applicable for Basic auth, returns empty string)
        
        This method exists for interface compatibility with OAuthClient.
        Basic authentication doesn't use tokens - credentials are sent with each request.
        
        Args:
            force_refresh: Ignored for Basic auth
            
        Returns:
            Empty string (Basic auth doesn't use tokens)
        """
        return ""
    
    def get_auth_header(self) -> Dict[str, str]:
        """
        Get authorization header with Basic auth credentials
        
        Returns:
            Dictionary with Authorization header
        """
        return {
            'Authorization': f'Basic {self._encoded_credentials}'
        }
    
    def invalidate_token(self):
        """
        Invalidate token (not applicable for Basic auth)
        
        This method exists for interface compatibility with OAuthClient.
        Basic auth doesn't maintain tokens, so this is a no-op.
        """
        logger.debug("Token invalidation called on BasicAuthClient (no-op)")
        pass
    
    def is_token_valid(self) -> bool:
        """
        Check if credentials are valid
        
        For Basic auth, credentials are always "valid" in the sense that
        they're available. Actual validation happens on the server side.
        
        Returns:
            True (credentials are always present)
        """
        return True
    
    def __repr__(self) -> str:
        """String representation (without exposing credentials)"""
        masked_username = self.username[:3] + '*' * (len(self.username) - 3) if len(self.username) > 3 else '***'
        return f"BasicAuthClient(username='{masked_username}')"