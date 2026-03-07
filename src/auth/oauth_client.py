"""
OAuth 2.0 Client for SAP Cloud Integration API authentication
"""

import time
from typing import Optional, Dict
import requests
from requests.auth import HTTPBasicAuth

from utils.logger import get_logger

logger = get_logger(__name__)


class OAuthClient:
    """OAuth 2.0 client for SAP Cloud Integration authentication"""
    
    def __init__(self, token_url: str, client_id: str, client_secret: str, 
                 timeout: int = 30):
        """
        Initialize OAuth client
        
        Args:
            token_url: OAuth token endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            timeout: Request timeout in seconds
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        
        # Token management
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._token_buffer: int = 300  # Refresh 5 minutes before expiry
        
        logger.debug(f"OAuth client initialized for {token_url}")
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get valid access token (refreshes if expired)
        
        Args:
            force_refresh: Force token refresh even if not expired
            
        Returns:
            Valid access token
            
        Raises:
            requests.RequestException: If token acquisition fails
        """
        # Check if we need to refresh
        current_time = time.time()
        
        if force_refresh or not self._access_token or current_time >= self._token_expiry:
            logger.info("Acquiring new OAuth access token...")
            self._refresh_token()
        else:
            logger.debug("Using cached OAuth token")
        
        return self._access_token
    
    def _refresh_token(self):
        """
        Refresh OAuth access token using client credentials flow
        
        Raises:
            requests.RequestException: If token refresh fails
        """
        try:
            logger.debug(f"Requesting token from {self.token_url}")
            
            # Prepare token request
            data = {
                'grant_type': 'client_credentials'
            }
            
            auth = HTTPBasicAuth(self.client_id, self.client_secret)
            
            # Make token request
            start_time = time.time()
            response = requests.post(
                self.token_url,
                data=data,
                auth=auth,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            
            elapsed = time.time() - start_time
            
            # Check response
            response.raise_for_status()
            
            # Parse token response
            token_data = response.json()
            
            self._access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            
            # Calculate token expiry with buffer
            self._token_expiry = time.time() + expires_in - self._token_buffer
            
            logger.info(
                f"OAuth token acquired successfully "
                f"(expires in {expires_in}s, response time: {elapsed:.2f}s)"
            )
            logger.debug(f"Token type: {token_data.get('token_type', 'Bearer')}")
            
        except requests.RequestException as e:
            logger.error(f"Failed to acquire OAuth token: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_auth_header(self) -> Dict[str, str]:
        """
        Get authorization header with valid token
        
        Returns:
            Dictionary with Authorization header
        """
        token = self.get_access_token()
        return {'Authorization': f'Bearer {token}'}
    
    def invalidate_token(self):
        """Invalidate current token (force refresh on next request)"""
        logger.debug("Invalidating OAuth token")
        self._access_token = None
        self._token_expiry = 0
    
    def is_token_valid(self) -> bool:
        """
        Check if current token is still valid
        
        Returns:
            True if token exists and not expired
        """
        if not self._access_token:
            return False
        
        return time.time() < self._token_expiry
    
    def __repr__(self) -> str:
        """String representation"""
        status = "valid" if self.is_token_valid() else "expired/missing"
        return f"OAuthClient(token_url='{self.token_url}', token_status='{status}')"