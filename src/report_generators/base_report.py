"""
Base Report Generator Class
Provides common functionality for all report generators
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import sqlite3
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseReport(ABC):
    """Abstract base class for all report generators"""
    
    def __init__(self, db_path: Path, tenant_id: str, captured_at: str):
        """
        Initialize base report
        
        Args:
            db_path: Path to SQLite database
            tenant_id: Tenant identifier
            captured_at: Capture timestamp
        """
        self.db_path = db_path
        self.tenant_id = tenant_id
        self.captured_at = captured_at
        self.report_data = {}
        
        logger.debug(f"Initialized {self.__class__.__name__} for tenant {tenant_id}")
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries with query results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                # Convert rows to dictionaries
                columns = [description[0] for description in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def execute_scalar(self, query: str, params: tuple = ()) -> Any:
        """
        Execute query and return single scalar value
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Single value result
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Scalar query execution failed: {e}")
            raise
    
    @abstractmethod
    def generate(self) -> Dict[str, Any]:
        """
        Generate report data
        
        Must be implemented by subclasses
        
        Returns:
            Dictionary with report data
        """
        pass
    
    @abstractmethod
    def get_report_name(self) -> str:
        """
        Get report name
        
        Returns:
            Report name string
        """
        pass
    
    @abstractmethod
    def get_report_title(self) -> str:
        """
        Get report title for display
        
        Returns:
            Report title string
        """
        pass
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """
        Get summary metrics for executive summary
        
        Returns:
            Dictionary with key metrics
        """
        return {}
    
    def get_chart_data(self) -> List[Dict[str, Any]]:
        """
        Get data for charts/visualizations
        
        Returns:
            List of chart configurations
        """
        return []
    
    def format_date(self, timestamp: str) -> str:
        """
        Format timestamp for display
        
        Args:
            timestamp: ISO format timestamp
            
        Returns:
            Formatted date string
        """
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        return timestamp or 'N/A'
    
    def safe_int(self, value: Any) -> int:
        """Safely convert value to integer"""
        try:
            return int(value) if value is not None else 0
        except:
            return 0
    
    def safe_float(self, value: Any) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if value is not None else 0.0
        except:
            return 0.0