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
        self.keep_runs = int(self._get_optional("KEEP_RUNS", "5"))
        
        # Logging Configuration
        self.log_level = self._get_optional("LOG_LEVEL", "INFO").upper()
        self.trace_api_calls = self._get_optional("TRACE_API_CALLS", "false").lower() == "true"
        
        # Download Control Configuration
        self.download_runtime_artifacts = self._get_bool("DOWNLOAD_RUNTIME_ARTIFACTS", "true")
        self.download_packages = self._get_bool("DOWNLOAD_PACKAGES", "true")
        self.download_iflows = self._get_bool("DOWNLOAD_IFLOWS", "true")
        self.download_resources = self._get_bool("DOWNLOAD_RESOURCES", "true")
        self.download_configurations = self._get_bool("DOWNLOAD_CONFIGURATIONS", "true")
        self.download_message_mappings = self._get_bool("DOWNLOAD_MESSAGE_MAPPINGS", "true")
        self.download_value_mappings = self._get_bool("DOWNLOAD_VALUE_MAPPINGS", "true")
        self.download_script_collections = self._get_bool("DOWNLOAD_SCRIPT_COLLECTIONS", "true")
        self.download_security_apis = self._get_bool("DOWNLOAD_SECURITY_APIS", "true")
        self.download_partner_directory = self._get_bool("DOWNLOAD_PARTNER_DIRECTORY", "true")
        self.download_discover_versions = self._get_bool("DOWNLOAD_DISCOVER_VERSIONS", "true")
        self.download_artifact_zips = self._get_bool("DOWNLOAD_ARTIFACT_ZIPS", "true")
        self.extract_readonly_packages = self._get_bool("EXTRACT_READONLY_PACKAGES", "true")
        
        # IFlow content extraction (IFLW, scripts, mappings, schemas, archives)
        self.extract_iflow_content = self._get_bool("EXTRACT_IFLOW_CONTENT", "true")
        
        # Artifact content extraction (Script Collections, Message Mappings, Value Mappings)
        self.extract_script_collection_content = self._get_bool("EXTRACT_SCRIPT_COLLECTION_CONTENT", "true")
        self.extract_message_mapping_content = self._get_bool("EXTRACT_MESSAGE_MAPPING_CONTENT", "true")
        self.extract_value_mapping_content = self._get_bool("EXTRACT_VALUE_MAPPING_CONTENT", "true")
        
        # BPMN Analysis (unified flag for all BPMN parsers)
        self.parse_bpmn_content = self._get_bool("PARSE_BPMN_CONTENT", "true")
        
        # Execution Mode Configuration
        self.download_only = self._get_bool("DOWNLOAD_ONLY", "false")
        self.analyze_existing = self._get_bool("ANALYZE_EXISTING", "false")
        self.analyze_run_timestamp = self._get_optional("ANALYZE_RUN_TIMESTAMP", "").strip()
        
        # Additional Configuration
        self.max_artifact_size_mb = int(self._get_optional("MAX_ARTIFACT_SIZE_MB", "50"))
        
        # Optional Discover Tenant Configuration
        self.discover_base_url = self._get_optional("DISCOVER_BASE_URL", "").strip()
        self.discover_client_id = self._get_optional("DISCOVER_OAUTH_CLIENT_ID", "").strip()
        self.discover_client_secret = self._get_optional("DISCOVER_OAUTH_CLIENT_SECRET", "").strip()
        self.discover_token_url = self._get_optional("DISCOVER_OAUTH_TOKEN_URL", "").strip()
        
        # Ensure directories exist
        self._ensure_directories()
    
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
    
    def cleanup_old_runs(self, keep_last: int):
        """
        Delete old runs beyond retention limit
        
        Args:
            keep_last: Number of most recent runs to keep (0 = keep all)
        """
        if keep_last <= 0:
            return  # Keep all runs
        
        tenant_dir = self.runs_dir / self.tenant_id
        
        if not tenant_dir.exists():
            return
        
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
        
        # Get all run directories (sorted by name = timestamp)
        run_dirs = sorted(
            [d for d in tenant_dir.iterdir() if d.is_dir()],
            reverse=True  # Newest first
        )
        
        # Delete old runs
        import shutil
        for old_run in run_dirs[keep_last:]:
            try:
                logger.info(f"Cleaning up old run: {old_run.name}")
                shutil.rmtree(old_run)
            except Exception as e:
                logger.warning(f"Failed to delete old run {old_run.name}: {e}")
    
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
        
        # Validate download dependencies
        self.validate_download_dependencies()
        
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
    
    def validate_download_dependencies(self):
        """
        Validate API download dependencies
        Only validates when downloads are explicitly enabled
        
        Raises:
            ValueError: If download dependencies are not met
        """
        errors = []
        
        # Only validate dependencies if the dependent download is enabled
        
        # IFlows depend on Packages
        if self.download_iflows and not self.download_packages:
            errors.append("❌ IFlows require Packages (set DOWNLOAD_PACKAGES=true or DOWNLOAD_IFLOWS=false)")
        
        # Resources depend on IFlows (but only validate if Resources is enabled)
        if self.download_resources and not self.download_iflows:
            errors.append("❌ Resources require IFlows (set DOWNLOAD_IFLOWS=true or DOWNLOAD_RESOURCES=false)")
        
        # Configurations depend on IFlows (but only validate if Configurations is enabled)
        if self.download_configurations and not self.download_iflows:
            errors.append("❌ Configurations require IFlows (set DOWNLOAD_IFLOWS=true or DOWNLOAD_CONFIGURATIONS=false)")
        
        # Script Collections depend on Packages
        if self.download_script_collections and not self.download_packages:
            errors.append("❌ Script Collections require Packages (set DOWNLOAD_PACKAGES=true or DOWNLOAD_SCRIPT_COLLECTIONS=false)")
        
        # Message Mappings depend on Packages
        if self.download_message_mappings and not self.download_packages:
            errors.append("❌ Message Mappings require Packages (set DOWNLOAD_PACKAGES=true or DOWNLOAD_MESSAGE_MAPPINGS=false)")
        
        # Value Mappings depend on Packages
        if self.download_value_mappings and not self.download_packages:
            errors.append("❌ Value Mappings require Packages (set DOWNLOAD_PACKAGES=true or DOWNLOAD_VALUE_MAPPINGS=false)")
        
        # Artifact ZIPs depend on Packages
        if self.download_artifact_zips and not self.download_packages:
            errors.append("❌ Artifact ZIPs require Packages (set DOWNLOAD_PACKAGES=true or DOWNLOAD_ARTIFACT_ZIPS=false)")
        
        # READ_ONLY extraction depends on Artifact ZIPs
        if self.extract_readonly_packages and not self.download_artifact_zips:
            errors.append("❌ READ_ONLY extraction requires Artifact ZIPs (set DOWNLOAD_ARTIFACT_ZIPS=true or EXTRACT_READONLY_PACKAGES=false)")
        
        # IFlow content extraction depends on Artifact ZIPs
        if self.extract_iflow_content and not self.download_artifact_zips:
            errors.append("❌ IFlow content extraction requires Artifact ZIPs (set DOWNLOAD_ARTIFACT_ZIPS=true or EXTRACT_IFLOW_CONTENT=false)")
        
        # Analyze existing requires timestamp
        if self.analyze_existing and not self.analyze_run_timestamp:
            errors.append("❌ ANALYZE_EXISTING=true requires ANALYZE_RUN_TIMESTAMP to be set")
        
        # Cannot have both modes
        if self.analyze_existing and self.download_only:
            errors.append("❌ Cannot set both ANALYZE_EXISTING=true and DOWNLOAD_ONLY=true")
        
        # Discover versions requires packages
        if self.download_discover_versions and not self.download_packages:
            errors.append("❌ Discover version check requires Packages (set DOWNLOAD_PACKAGES=true or DOWNLOAD_DISCOVER_VERSIONS=false)")
        
        if errors:
            raise ValueError("Download configuration validation failed:\n" + "\n".join(errors))
    
    def __repr__(self) -> str:
        """String representation (excluding sensitive data)"""
        return (
            f"Config(tenant_id='{self.tenant_id}', "
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