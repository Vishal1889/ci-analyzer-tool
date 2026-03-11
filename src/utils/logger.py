"""
Logging infrastructure for SAP Cloud Integration Analyzer Tool
Supports TRACE, DEBUG, INFO, WARNING, ERROR levels
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Define custom TRACE level (between DEBUG and NOTSET)
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


class TraceLogger(logging.Logger):
    """Extended logger with TRACE level support"""
    
    def trace(self, message, *args, **kwargs):
        """Log message at TRACE level"""
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, message, args, **kwargs)


# Set custom logger class
logging.setLoggerClass(TraceLogger)


class LoggerSetup:
    """Setup and configure logging for the application"""
    
    def __init__(self, tenant_id: str, log_file: Path, log_level: str = "INFO", 
                 trace_api_calls: bool = False):
        """
        Initialize logger setup
        
        Args:
            tenant_id: Tenant identifier for logging context
            log_file: Full path to log file (including filename)
            log_level: Logging level (TRACE, DEBUG, INFO, WARNING, ERROR)
            trace_api_calls: Enable detailed API call tracing
        """
        self.tenant_id = tenant_id
        self.log_file = Path(log_file)
        self.log_level = log_level
        self.trace_api_calls = trace_api_calls
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with file and console handlers"""
        # Convert log level string to numeric level
        numeric_level = self._get_numeric_level(self.log_level)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(TRACE_LEVEL)  # Set to lowest level to capture all
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler - logs everything at configured level
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(TRACE_LEVEL)  # File gets all logs
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Ensure stdout uses UTF-8 on Windows to handle Unicode characters (e.g. ✓)
        # cp1252 (the default Windows console codec) cannot encode many Unicode symbols
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

        # Console handler - logs INFO and above (or configured level if higher)
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = max(numeric_level, logging.INFO)  # At least INFO for console
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info("=" * 70)
        logger.info("Logging initialized")
        logger.info(f"Log file: {self.log_file}")
        logger.info(f"Log level: {self.log_level} (File: ALL, Console: {logging.getLevelName(console_level)})")
        logger.info(f"Trace API calls: {self.trace_api_calls}")
        logger.info("=" * 70)
    
    def _get_numeric_level(self, level_name: str) -> int:
        """
        Convert level name to numeric level
        
        Args:
            level_name: Level name (TRACE, DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Numeric log level
        """
        level_map = {
            "TRACE": TRACE_LEVEL,
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        return level_map.get(level_name.upper(), logging.INFO)
    
    def get_logger(self, name: str) -> TraceLogger:
        """
        Get a logger instance
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance with TRACE support
        """
        return logging.getLogger(name)


class APILogger:
    """Specialized logger for API calls with TRACE level support"""
    
    def __init__(self, logger: logging.Logger, trace_enabled: bool = False):
        """
        Initialize API logger
        
        Args:
            logger: Base logger instance
            trace_enabled: Enable TRACE level API logging
        """
        self.logger = logger
        self.trace_enabled = trace_enabled
    
    def log_request(self, method: str, url: str, headers: Optional[dict] = None, 
                   params: Optional[dict] = None):
        """
        Log API request
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers (Authorization will be masked)
            params: Request parameters
        """
        self.logger.info(f"API Request: {method} {url}")
        
        if self.trace_enabled:
            if params:
                self.logger.trace(f"  Parameters: {params}")
            
            if headers:
                # Mask sensitive headers
                safe_headers = self._mask_sensitive_headers(headers)
                self.logger.trace(f"  Headers: {safe_headers}")
    
    def log_response(self, status_code: int, response_time: float, 
                    response_size: Optional[int] = None):
        """
        Log API response
        
        Args:
            status_code: HTTP status code
            response_time: Response time in seconds
            response_size: Response size in bytes
        """
        self.logger.info(
            f"API Response: Status={status_code}, Time={response_time:.2f}s"
            + (f", Size={response_size} bytes" if response_size else "")
        )
    
    def log_response_data(self, data: dict):
        """
        Log response data at TRACE level
        
        Args:
            data: Response data dictionary
        """
        if self.trace_enabled:
            # Log basic structure info
            if isinstance(data, dict):
                if 'd' in data and 'results' in data['d']:
                    count = len(data['d']['results'])
                    self.logger.trace(f"  Response contains {count} items")
                self.logger.trace(f"  Response keys: {list(data.keys())}")
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """
        Log API error
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        error_msg = f"API Error: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        self.logger.error(error_msg)
        
        if self.trace_enabled:
            import traceback
            self.logger.trace(f"  Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def _mask_sensitive_headers(headers: dict) -> dict:
        """
        Mask sensitive header values
        
        Args:
            headers: Original headers
            
        Returns:
            Headers with masked sensitive values
        """
        sensitive_keys = ['authorization', 'api-key', 'x-api-key', 'password']
        masked = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                masked[key] = '***MASKED***'
            else:
                masked[key] = value
        
        return masked


# Global logger setup instance
_logger_setup: Optional[LoggerSetup] = None


def setup_logging(tenant_id: str, log_file: Path, log_level: str = "INFO",
                 trace_api_calls: bool = False) -> LoggerSetup:
    """
    Setup global logging configuration
    
    Args:
        tenant_id: Tenant identifier
        log_file: Full path to log file
        log_level: Logging level
        trace_api_calls: Enable API call tracing
        
    Returns:
        LoggerSetup instance
    """
    global _logger_setup
    _logger_setup = LoggerSetup(tenant_id, log_file, log_level, trace_api_calls)
    return _logger_setup


def get_logger(name: str) -> TraceLogger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if _logger_setup:
        return _logger_setup.get_logger(name)
    else:
        # Fallback to basic logging if not setup
        return logging.getLogger(name)


def get_api_logger(name: str) -> APILogger:
    """
    Get an API logger instance
    
    Args:
        name: Logger name
        
    Returns:
        API logger instance
    """
    logger = get_logger(name)
    trace_enabled = _logger_setup.trace_api_calls if _logger_setup else False
    return APILogger(logger, trace_enabled)