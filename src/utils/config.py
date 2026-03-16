"""
Configuration management for SAP Cloud Integration Analyzer Tool
Loads and validates configuration from environment variables
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration manager"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            env_file: Path to .env file (default: .env in project root)
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in current directory or parent
            env_path = Path(".env")
            if env_path.exists():
                load_dotenv(env_path)
            else:
                parent_env = Path("../.env")
                if parent_env.exists():
                    load_dotenv(parent_env)
        
        # Tenant Configuration
        self.tenant_id = self._get_required("SAP_TENANT_ID")
        self.tenant_short_name = self._get_required("SAP_TENANT_SHORT_NAME")
        
        # Subaccount and Authentication Type Configuration
        self.subaccount_type = self._get_optional("SAP_SUBACCOUNT_TYPE", "CF").upper()
        self.auth_type = self._get_optional("SAP_AUTH_TYPE", "OAUTH").upper()
        
        # OAuth Configuration (required for OAuth auth)
        self.oauth_token_url = self._get_optional("SAP_OAUTH_TOKEN_URL", "")
        self.client_id = self._get_optional("SAP_CLIENT_ID", "")
        self.client_secret = self._get_optional("SAP_CLIENT_SECRET", "")
        
        # Basic Authentication Configuration (required for Basic auth)
        self.basic_auth_username = self._get_optional("SAP_BASIC_AUTH_USERNAME", "")
        self.basic_auth_password = self._get_optional("SAP_BASIC_AUTH_PASSWORD", "")
        
        # API Configuration
        self.api_base_url = self._get_required("SAP_API_BASE_URL")
        self.api_timeout = int(self._get_optional("API_TIMEOUT", "30"))
        self.api_retry_count = int(self._get_optional("API_RETRY_COUNT", "3"))
        self.api_page_size = int(self._get_optional("API_PAGE_SIZE", "50"))
        
        # Parallel download configuration (min: 1, max: 10)
        parallel_downloads = int(self._get_optional("PARALLEL_DOWNLOADS", "1"))
        self.parallel_downloads = max(1, min(10, parallel_downloads))
        
        # Run Organization Configuration
        self.runs_dir = Path(self._get_optional("RUNS_DIR", "./runs"))
        
        # Logging Configuration
        self.log_level = self._get_optional("LOG_LEVEL", "INFO").upper()
        self.trace_api_calls = self._get_optional("TRACE_API_CALLS", "false").lower() == "true"
        
        # =============================================================================
        # EXECUTION MODE - Simplified configuration
        # =============================================================================
        self.execution_mode = self._get_optional("EXECUTION_MODE", "FULL").upper()
        self.report_db_path = self._get_optional("REPORT_DB_PATH", "").strip()
        
        # For FULL mode, everything is enabled (hardcoded to TRUE)
        if self.execution_mode == "FULL":
            self.download_runtime_artifacts = True
            self.download_packages = True
            self.download_iflows = True
            self.download_resources = True
            self.download_configurations = True
            self.download_message_mappings = True
            self.download_value_mappings = True
            self.download_script_collections = True
            self.download_security_apis = True
            self.download_partner_directory = True
            self.download_discover_versions = True
            self.download_artifact_zips = True
            self.extract_readonly_packages = True
            self.extract_iflow_content = True
            self.extract_script_collection_content = True
            self.extract_message_mapping_content = True
            self.extract_value_mapping_content = True
            self.parse_iflw_content = True
        else:
            # For REPORT_ONLY mode, all downloads/parsing disabled
            self.download_runtime_artifacts = False
            self.download_packages = False
            self.download_iflows = False
            self.download_resources = False
            self.download_configurations = False
            self.download_message_mappings = False
            self.download_value_mappings = False
            self.download_script_collections = False
            self.download_security_apis = False
            self.download_partner_directory = False
            self.download_discover_versions = False
            self.download_artifact_zips = False
            self.extract_readonly_packages = False
            self.extract_iflow_content = False
            self.extract_script_collection_content = False
            self.extract_message_mapping_content = False
            self.extract_value_mapping_content = False
            self.parse_iflw_content = False
        
        # Legacy flag support (with deprecation warnings)
        self._check_legacy_flags()
        
        # Additional Configuration
        self.max_artifact_size_mb = int(self._get_optional("MAX_ARTIFACT_SIZE_MB", "50"))

        # Report Selection (applies to both FULL and REPORT_ONLY modes)
        self.report_neo_to_cf = self._get_bool('REPORT_NEO_TO_CF', 'true')
        
        # Optional Discover Tenant Configuration
        self.discover_base_url = self._get_optional("DISCOVER_BASE_URL", "").strip()
        self.discover_client_id = self._get_optional("DISCOVER_OAUTH_CLIENT_ID", "").strip()
        self.discover_client_secret = self._get_optional("DISCOVER_OAUTH_CLIENT_SECRET", "").strip()
        self.discover_token_url = self._get_optional("DISCOVER_OAUTH_TOKEN_URL", "").strip()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _check_legacy_flags(self):
        """Check for legacy configuration flags and log warnings"""
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
        
        legacy_flags = {
            'DOWNLOAD_ONLY': 'Use EXECUTION_MODE=FULL instead',
            'ANALYZE_EXISTING': 'Use EXECUTION_MODE=REPORT_ONLY with REPORT_DB_PATH',
            'ANALYZE_RUN_TIMESTAMP': 'Use REPORT_DB_PATH instead',
            'DOWNLOAD_PACKAGES': 'FULL mode downloads everything automatically',
            'DOWNLOAD_IFLOWS': 'FULL mode downloads everything automatically',
            'EXTRACT_IFLOW_CONTENT': 'FULL mode extracts everything automatically',
            'PARSE_IFLW_CONTENT': 'FULL mode parses everything automatically',
            'KEEP_RUNS': 'Removed - manage runs manually'
        }
        
        for flag, message in legacy_flags.items():
            if os.getenv(flag):
                logger.warning(f"⚠️  {flag} is deprecated. {message}")
    
    def _get_required(self, key: str) -> str:
        """
        Get required environment variable
        
        Args:
            key: Environment variable name
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable '{key}' is not set. "
                f"Please check your .env file."
            )
        return value
    
    def _get_optional(self, key: str, default: str) -> str:
        """
        Get optional environment variable with default
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    def _get_bool(self, key: str, default: str) -> bool:
        """
        Get boolean environment variable
        
        Args:
            key: Environment variable name
            default: Default value ("true" or "false")
            
        Returns:
            Boolean value
        """
        value = self._get_optional(key, default).lower()
        return value in ("true", "1", "yes", "on")
    
    def _ensure_directories(self):
        """Create required directories if they don't exist"""
        # Only create the base runs directory
        # Individual run directories will be created as needed
        self.runs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_run_dir(self, timestamp: str) -> Path:
        """
        Get run directory for a specific timestamp
        
        Args:
            timestamp: Timestamp string in format YYYYMMDD_HHMMSS
            
        Returns:
            Path to run directory: runs/{tenant_id}/{timestamp}/
        """
        run_dir = self.runs_dir / self.tenant_id / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    
    def get_database_path(self, timestamp: str) -> Path:
        """
        Get database path for a specific run
        
        Args:
            timestamp: Timestamp string in format YYYYMMDD_HHMMSS
            
        Returns:
            Path to database: runs/{tenant_id}/{timestamp}/ci_analyzer_{tenant_short_name}_{timestamp}.db
        """
        db_filename = f"ci_analyzer_{self.tenant_short_name}_{timestamp}.db"
        return self.get_run_dir(timestamp) / db_filename
    
    def get_log_file(self, timestamp: str) -> Path:
        """
        Get log file path for a specific run
        
        Args:
            timestamp: Timestamp string in format YYYYMMDD_HHMMSS
            
        Returns:
            Path to log file: runs/{tenant_id}/{timestamp}/ci_analyzer_{tenant_short_name}_{timestamp}.log
        """
        log_filename = f"ci_analyzer_{self.tenant_short_name}_{timestamp}.log"
        return self.get_run_dir(timestamp) / log_filename
    
    def get_download_path(self, timestamp: str) -> str:
        """
        Get download path for a specific run
        
        Args:
            timestamp: Timestamp string in format YYYYMMDD_HHMMSS
            
        Returns:
            Path to downloads directory: runs/{tenant_id}/{timestamp}/downloads/
        """
        path = self.get_run_dir(timestamp) / "downloads"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    def get_reports_dir(self, timestamp: str) -> Path:
        """
        Get reports directory for a specific run
        
        Args:
            timestamp: Timestamp string in format YYYYMMDD_HHMMSS
            
        Returns:
            Path to reports directory: runs/{tenant_id}/{timestamp}/reports/
        """
        path = self.get_run_dir(timestamp) / "reports"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def has_discover_config(self) -> bool:
        """
        Check if Discover tenant configuration is available
        
        Returns:
            True if all Discover config values are set
        """
        return all([
            self.discover_base_url,
            self.discover_client_id,
            self.discover_client_secret,
            self.discover_token_url
        ])
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate subaccount type
        if self.subaccount_type not in ["CF", "NEO"]:
            raise ValueError(
                f"Invalid subaccount type '{self.subaccount_type}'. "
                f"Must be 'CF' (Cloud Foundry) or 'NEO'"
            )
        
        # Validate authentication type
        if self.auth_type not in ["OAUTH", "BASIC"]:
            raise ValueError(
                f"Invalid authentication type '{self.auth_type}'. "
                f"Must be 'OAUTH' or 'BASIC'"
            )
        
        # Validate authentication configuration
        self._validate_auth_configuration()
        
        # Validate execution mode
        if self.execution_mode not in ["FULL", "REPORT_ONLY"]:
            raise ValueError(
                f"Invalid execution mode '{self.execution_mode}'. "
                f"Must be 'FULL' or 'REPORT_ONLY'"
            )
        
        # Validate REPORT_ONLY mode requirements
        if self.execution_mode == "REPORT_ONLY":
            if not self.report_db_path:
                raise ValueError(
                    "REPORT_ONLY mode requires REPORT_DB_PATH to be set. "
                    "Example: runs/Trial/20260307_164253/ci_analyzer_Trial_20260307_164253.db"
                )
            
            db_path = Path(self.report_db_path)
            if not db_path.exists():
                raise ValueError(
                    f"Database file not found: {self.report_db_path}\n"
                    f"Please verify the path is correct and the database exists."
                )
            
            if not db_path.is_file():
                raise ValueError(
                    f"REPORT_DB_PATH must point to a file, not a directory: {self.report_db_path}"
                )
        
        # Validate log level
        valid_log_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"]
        if self.log_level not in valid_log_levels:
            raise ValueError(
                f"Invalid log level '{self.log_level}'. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Validate API base URL
        if not self.api_base_url.startswith("https://"):
            raise ValueError("API base URL must start with https://")
        
        # Validate numeric values
        if self.api_timeout <= 0:
            raise ValueError("API timeout must be positive")
        
        if self.api_retry_count < 0:
            raise ValueError("API retry count cannot be negative")
        
        if self.api_page_size <= 0 or self.api_page_size > 1000:
            raise ValueError("API page size must be between 1 and 1000")
        
        # Check URL patterns and provide warnings
        self._check_url_patterns()
        
        return True
    
    def _validate_auth_configuration(self):
        """
        Validate authentication configuration based on subaccount type and auth method
        
        Raises:
            ValueError: If authentication configuration is invalid
        """
        # Rule 1: Cloud Foundry + Basic Auth = NOT ALLOWED
        if self.subaccount_type == "CF" and self.auth_type == "BASIC":
            raise ValueError(
                "❌ Basic Authentication is not supported for Cloud Foundry subaccounts.\n"
                "   Please use OAuth (SAP_AUTH_TYPE=OAUTH) or switch to Neo (SAP_SUBACCOUNT_TYPE=NEO)"
            )
        
        # Rule 2: OAuth requires OAuth credentials
        if self.auth_type == "OAUTH":
            if not self.oauth_token_url:
                raise ValueError(
                    "❌ OAuth Authentication requires SAP_OAUTH_TOKEN_URL to be set in .env file"
                )
            if not self.oauth_token_url.startswith("https://"):
                raise ValueError("OAuth token URL must start with https://")
            if not self.client_id:
                raise ValueError(
                    "❌ OAuth Authentication requires SAP_CLIENT_ID to be set in .env file"
                )
            if not self.client_secret:
                raise ValueError(
                    "❌ OAuth Authentication requires SAP_CLIENT_SECRET to be set in .env file"
                )
        
        # Rule 3: Basic Auth requires username and password
        if self.auth_type == "BASIC":
            if not self.basic_auth_username:
                raise ValueError(
                    "❌ Basic Authentication requires SAP_BASIC_AUTH_USERNAME to be set in .env file"
                )
            if not self.basic_auth_password:
                raise ValueError(
                    "❌ Basic Authentication requires SAP_BASIC_AUTH_PASSWORD to be set in .env file"
                )
    
    def _check_url_patterns(self):
        """
        Check URL patterns and log warnings if they don't match subaccount type
        """
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
        except ImportError:
            # Fallback for direct imports (e.g., when testing config directly)
            import logging
            logger = logging.getLogger(__name__)
        
        api_url_lower = self.api_base_url.lower()
        
        # Check for CF URL pattern with Neo subaccount type
        if self.subaccount_type == "NEO" and "cfapps" in api_url_lower:
            logger.warning(
                "⚠️  Subaccount type is set to NEO but API URL contains 'cfapps' (typical for Cloud Foundry).\n"
                "   Please verify your configuration. API URL: %s", self.api_base_url
            )
        
        # Check for Neo URL pattern with CF subaccount type
        if self.subaccount_type == "CF" and ".hci." in api_url_lower:
            logger.warning(
                "⚠️  Subaccount type is set to CF but API URL contains '.hci.' (typical for Neo).\n"
                "   Please verify your configuration. API URL: %s", self.api_base_url
            )
    
    def __repr__(self) -> str:
        """String representation (excluding sensitive data)"""
        return (
            f"Config(tenant_id='{self.tenant_id}', "
            f"execution_mode='{self.execution_mode}', "
            f"api_base_url='{self.api_base_url}', "
            f"log_level='{self.log_level}')"
        )


# Singleton instance
_config_instance: Optional[Config] = None


def get_config(env_file: Optional[str] = None, reload: bool = False) -> Config:
    """
    Get configuration singleton instance
    
    Args:
        env_file: Path to .env file (only used on first call)
        reload: Force reload of configuration
        
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = Config(env_file)
        _config_instance.validate()
    
    return _config_instance