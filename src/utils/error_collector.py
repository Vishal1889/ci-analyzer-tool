"""
Centralized error collector for all download and extraction phases.
Collects errors from all phases and saves to a single download-errors.json
in the json-files/ directory for DB import.
"""

import json
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class ErrorCollector:
    """Collects errors from all download/extraction phases into a single file."""

    def __init__(self):
        self.errors = []

    def add_error(self, package_id: str, artifact_type: str, error_code: int,
                  error_type: str, error_message: str, download_path: str = '',
                  iflow_id: str = '', version: str = ''):
        """Add an error record.

        Args:
            package_id: Package or artifact identifier
            artifact_type: e.g., 'READ_ONLY_PACKAGE', 'IFLOW', 'SCRIPT_COLLECTION', etc.
            error_code: HTTP status code or OS errno
            error_type: Category e.g., 'PROPRIETARY_CONTENT', 'PATH_TOO_LONG', 'EXTRACTION_ERROR'
            error_message: Human-readable error description
            download_path: The file path that was attempted
            iflow_id: Optional IFlow ID (for artifact-level errors)
            version: Optional version string
        """
        record = {
            'PackageID': package_id,
            'Type': artifact_type,
            'ErrorCode': error_code,
            'ErrorType': error_type,
            'ErrorMessage': error_message,
            'Timestamp': datetime.now().isoformat(),
            'DownloadAttempted': download_path,
        }
        if iflow_id:
            record['IflowID'] = iflow_id
            record['Version'] = version

        self.errors.append(record)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def save(self, json_files_dir: Path):
        """Save all collected errors to json-files/download-errors.json.

        Uses OData format for DB import compatibility.
        """
        json_files_dir = Path(json_files_dir)
        json_files_dir.mkdir(parents=True, exist_ok=True)
        output_file = json_files_dir / 'download-errors.json'

        output_data = {
            'd': {
                'results': self.errors
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        if self.errors:
            logger.info(f"Saved {len(self.errors)} errors to download-errors.json")
        else:
            logger.info("No download/extraction errors to save")
