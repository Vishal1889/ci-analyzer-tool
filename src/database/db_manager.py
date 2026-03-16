"""
Dynamic Database Manager for SAP Cloud Integration Analyzer
Automatically generates schema from JSON files and handles bulk imports
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import time

from utils.logger import get_logger

logger = get_logger(__name__)


class DynamicDatabaseManager:
    """Manages SQLite database with dynamic schema generation from JSON files"""
    
    # Mapping from JSON filename to table name
    TABLE_NAME_MAP = {
        # OData tables
        'runtimes.json': 'runtime',
        'packages.json': 'package',
        'iflows.json': 'iflow',
        'resources.json': 'resource',
        'configurations.json': 'configuration',
        'message-mappings.json': 'message_mapping',
        'value-mappings.json': 'value_mapping',
        'script-collections.json': 'script_collection',
        'security-user-credentials.json': 'security_user_credential',
        'security-oauth2-client-credentials.json': 'security_oauth2_client_credential',
        'security-secure-parameters.json': 'security_secure_parameter',
        'security-keystore-entries.json': 'security_keystore_entry',
        'security-certificate-user-mappings.json': 'security_certificate_user_mapping',
        'access-policies.json': 'security_access_policy',
        'partner-directory-binary.json': 'partner_directory_binary_parameter',
        'environment-variable-check.json': 'environment_variable_check',
        'package-discover-versions.json': 'package_discover_version',
        'download-errors.json': 'download_error',
        # IFLW tables
        'iflw-participants.json': 'iflw_participant',
        'iflw-channels.json': 'iflw_channel',
        'iflw-channels-properties.json': 'iflw_channel_property',
        'iflw-activities.json': 'iflw_activity',
        'iflw-activities-properties.json': 'iflw_activity_property',
        'iflw-groovy-scripts.json': 'iflw_groovy_script',
        'iflw-message-mappings.json': 'iflw_message_mapping',
        'iflw-xslt-mappings.json': 'iflw_xslt_mapping',
        'iflw-content-modifiers.json': 'iflw_content_modifier',
        'iflw-timers.json': 'iflw_timer'
    }
    
    # Fields to exclude from database (per table)
    EXCLUDED_FIELDS = {
        'partner_directory_binary_parameter': ['Value']  # Exclude Value field to prevent DB bloat
    }
    
    def __init__(self, db_path: str, tenant_id: str, captured_at: str):
        """
        Initialize dynamic database manager
        
        Args:
            db_path: Path to SQLite database file
            tenant_id: Tenant identifier for data isolation
            captured_at: Timestamp in ISO 8601 format (e.g., 2026-03-04T18:17:09.606037+05:30)
        """
        self.db_path = Path(db_path)
        self.tenant_id = tenant_id
        self.captured_at = captured_at
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Database manager initialized: {self.db_path}")
        logger.info(f"  Tenant ID: {self.tenant_id}")
        logger.info(f"  Captured At: {self.captured_at}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        
        Yields:
            sqlite3.Connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _extract_rows_from_json(self, data: Any, origin: str) -> List[Dict[str, Any]]:
        """
        Extract rows from JSON data based on origin
        
        Args:
            data: Parsed JSON data
            origin: 'odata' or 'iflw'
            
        Returns:
            List of row dictionaries
        """
        if origin == 'odata':
            # OData format: { "d": { "results": [...] } }
            if isinstance(data, dict) and 'd' in data and 'results' in data['d']:
                return data['d']['results']
            else:
                logger.warning(f"OData format not found, returning empty array")
                return []
        elif origin == 'iflw':
            # IFLW format: direct array [...]
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"IFLW format not found (expected array), returning empty array")
                return []
        else:
            raise ValueError(f"Unknown origin: {origin}")
    
    def _infer_columns_from_rows(self, rows: List[Dict[str, Any]], table_name: str = None) -> List[str]:
        """
        Infer column names from JSON rows
        
        Args:
            rows: List of row dictionaries
            table_name: Optional table name to apply field exclusions
            
        Returns:
            List of column names (preserving JSON field names)
        """
        if not rows:
            return []
        
        # Get all unique keys from all rows (some rows may have different fields)
        all_keys = set()
        for row in rows:
            if isinstance(row, dict):
                all_keys.update(row.keys())
        
        # Apply field exclusions if table has any
        if table_name and table_name in self.EXCLUDED_FIELDS:
            excluded = set(self.EXCLUDED_FIELDS[table_name])
            all_keys = all_keys - excluded
            if excluded:
                logger.debug(f"  Excluded fields for {table_name}: {', '.join(excluded)}")
        
        # Return sorted list for consistency
        return sorted(list(all_keys))
    
    def create_table(self, json_file: Path, origin: str) -> str:
        """
        Create table from JSON file structure
        
        Args:
            json_file: Path to JSON file
            origin: 'odata' or 'iflw'
            
        Returns:
            Table name created
        """
        # Get table name
        filename = json_file.name
        table_name = self.TABLE_NAME_MAP.get(filename)
        
        if not table_name:
            logger.error(f"No table mapping found for {filename}")
            raise ValueError(f"Unknown JSON file: {filename}")
        
        # Load JSON data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {json_file}: {e}")
            raise
        
        # Extract rows
        rows = self._extract_rows_from_json(data, origin)
        
        # Infer columns (with table-specific exclusions)
        json_columns = self._infer_columns_from_rows(rows, table_name)
        
        # Build CREATE TABLE statement
        # All columns as TEXT, system columns first
        columns = ['tenant_id TEXT', 'captured_at TEXT']
        columns.extend([f'"{col}" TEXT' for col in json_columns])
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    "
        create_sql += ",\n    ".join(columns)
        create_sql += "\n)"
        
        # Execute CREATE TABLE
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_sql)
        
        logger.info(f"Created table '{table_name}' with {len(json_columns)} columns (+ 2 system columns)")
        logger.debug(f"  Columns: tenant_id, captured_at, {', '.join(json_columns[:5])}{'...' if len(json_columns) > 5 else ''}")
        
        return table_name
    
    def insert_from_json(self, table_name: str, json_file: Path, origin: str, 
                        progress_interval: int = 5000) -> int:
        """
        Bulk insert data from JSON file
        
        Args:
            table_name: Target table name
            json_file: Path to JSON file
            origin: 'odata' or 'iflw'
            progress_interval: Log progress every N rows
            
        Returns:
            Number of rows inserted
        """
        start_time = time.time()
        
        # Load JSON data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {json_file}: {e}")
            raise
        
        # Extract rows
        rows = self._extract_rows_from_json(data, origin)
        
        if not rows:
            logger.info(f"  No rows to insert for {table_name}")
            return 0
        
        # Get column names from first row (with table-specific exclusions)
        json_columns = self._infer_columns_from_rows(rows, table_name)
        
        # Build INSERT statement
        all_columns = ['tenant_id', 'captured_at'] + json_columns
        placeholders = ','.join(['?' for _ in all_columns])
        insert_sql = f"INSERT INTO {table_name} ({','.join(all_columns)}) VALUES ({placeholders})"
        
        # Prepare data for bulk insert
        insert_data = []
        for row in rows:
            # System columns
            row_values = [self.tenant_id, self.captured_at]
            
            # JSON columns (handle null/missing/nested)
            for col in json_columns:
                value = row.get(col)
                if value is None:
                    row_values.append(None)
                elif isinstance(value, (dict, list)):
                    # Stringify nested objects/arrays
                    row_values.append(json.dumps(value, ensure_ascii=False))
                else:
                    # Convert to string
                    row_values.append(str(value) if value != '' else '')
            
            insert_data.append(tuple(row_values))
        
        # Bulk insert with transaction
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for i, row_data in enumerate(insert_data, 1):
                cursor.execute(insert_sql, row_data)
                
                # Progress logging
                if i % progress_interval == 0:
                    logger.debug(f"  Inserted {i}/{len(insert_data)} rows...")
        
        duration = time.time() - start_time
        logger.info(f"  Inserted {len(insert_data)} rows into {table_name} in {duration:.2f}s")
        
        return len(insert_data)
    
    def create_tables_from_json_dirs(self, odata_dir: Path, iflw_dir: Path):
        """
        Create all tables from JSON directories
        
        Args:
            odata_dir: Directory containing OData JSON files
            iflw_dir: Directory containing IFLW JSON files
        """
        logger.info("Creating database schema from JSON files...")
        
        total_tables = 0
        
        # Process OData files
        odata_dir = Path(odata_dir)
        if odata_dir.exists():
            odata_files = sorted(odata_dir.glob('*.json'))
            logger.info(f"  Processing {len(odata_files)} OData JSON files...")
            
            for json_file in odata_files:
                try:
                    self.create_table(json_file, origin='odata')
                    total_tables += 1
                except Exception as e:
                    logger.error(f"  Failed to create table from {json_file.name}: {e}")
        else:
            logger.warning(f"OData directory not found: {odata_dir}")
        
        # Process IFLW files
        iflw_dir = Path(iflw_dir)
        if iflw_dir.exists():
            iflw_files = sorted(iflw_dir.glob('*.json'))
            logger.info(f"  Processing {len(iflw_files)} IFLW JSON files...")

            for json_file in iflw_files:
                try:
                    self.create_table(json_file, origin='iflw')
                    total_tables += 1
                except Exception as e:
                    logger.error(f"  Failed to create table from {json_file.name}: {e}")
        else:
            logger.warning(f"IFLW directory not found: {iflw_dir}")
        
        logger.info(f"Database schema created: {total_tables} tables")
    
    def import_all_json_files(self, odata_dir: Path, iflw_dir: Path):
        """
        Import all JSON files to database
        
        Args:
            odata_dir: Directory containing OData JSON files
            iflw_dir: Directory containing IFLW JSON files
        """
        logger.info("Importing JSON data to database...")
        
        total_rows = 0
        total_files = 0
        
        # Import OData files
        odata_dir = Path(odata_dir)
        if odata_dir.exists():
            odata_files = sorted(odata_dir.glob('*.json'))
            logger.info(f"  Importing {len(odata_files)} OData JSON files...")
            
            for json_file in odata_files:
                table_name = self.TABLE_NAME_MAP.get(json_file.name)
                if table_name:
                    try:
                        rows_inserted = self.insert_from_json(table_name, json_file, origin='odata')
                        total_rows += rows_inserted
                        total_files += 1
                    except Exception as e:
                        logger.error(f"  Failed to import {json_file.name}: {e}")
                else:
                    logger.warning(f"  No table mapping for {json_file.name}, skipping")
        
        # Import IFLW files
        iflw_dir = Path(iflw_dir)
        if iflw_dir.exists():
            iflw_files = sorted(iflw_dir.glob('*.json'))
            logger.info(f"  Importing {len(iflw_files)} IFLW JSON files...")

            for json_file in iflw_files:
                table_name = self.TABLE_NAME_MAP.get(json_file.name)
                if table_name:
                    try:
                        rows_inserted = self.insert_from_json(table_name, json_file, origin='iflw')
                        total_rows += rows_inserted
                        total_files += 1
                    except Exception as e:
                        logger.error(f"  Failed to import {json_file.name}: {e}")
                else:
                    logger.warning(f"  No table mapping for {json_file.name}, skipping")
        
        logger.info(f"Data import completed: {total_files} files, {total_rows} total rows")
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id = ?", (self.tenant_id,))
            return cursor.fetchone()[0]
    
    def list_tables(self) -> List[str]:
        """Get list of all tables in database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in cursor.fetchall()]