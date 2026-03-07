"""
BPMN Participant Extractor for SAP Cloud Integration Analyzer Tool
Extracts participant information from IFLW (BPMN XML) files
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

# XML Namespaces for BPMN 2.0
NAMESPACES = {
    'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
}

# Type normalization mapping (handles SAP typo)
TYPE_MAPPING = {
    "EndpointSender": "EndpointSender",
    "EndpointReceiver": "EndpointReceiver",
    "EndpointRecevier": "EndpointReceiver",  # Handle SAP typo
    "IntegrationProcess": "IntegrationProcess"
}


class BpmnParticipantExtractor:
    """Extracts participant information from BPMN XML files (.iflw)"""
    
    def __init__(self, iflw_files_dir: Path, output_dir: Path, timestamp: str = None):
        """
        Initialize BPMN Participant Extractor
        
        Args:
            iflw_files_dir: Directory containing IFLW files
            output_dir: Directory for output JSON files
            timestamp: Optional timestamp for organized output
        """
        self.iflw_files_dir = Path(iflw_files_dir)
        self.output_dir = Path(output_dir)
        self.timestamp = timestamp
        
        # Track errors
        self.errors = []
        
        logger.info("BpmnParticipantExtractor initialized")
        logger.info(f"  Source: {self.iflw_files_dir}")
        logger.info(f"  Output: {self.output_dir}")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract participants from all IFLW files and generate consolidated JSON
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting BPMN participant extraction...")
        
        stats = {
            "iflw_files_attempted": 0,
            "iflw_files_processed": 0,
            "iflw_files_failed": 0,
            "total_participants_extracted": 0,
            "participants_by_type": {
                "EndpointSender": 0,
                "EndpointReceiver": 0,
                "IntegrationProcess": 0,
                "Unknown": 0
            }
        }
        
        # Check if source directory exists
        if not self.iflw_files_dir.exists():
            logger.warning(f"IFLW files directory not found: {self.iflw_files_dir}")
            self._save_output([])
            return stats
        
        # Get all IFLW files
        iflw_files = list(self.iflw_files_dir.glob("*.iflw"))
        
        if not iflw_files:
            logger.info("No IFLW files found")
            self._save_output([])
            return stats
        
        logger.info(f"Found {len(iflw_files)} IFLW files to process")
        
        # Collect all participants from all files
        all_participants = []
        
        # Process each IFLW file
        for idx, iflw_path in enumerate(iflw_files, 1):
            stats["iflw_files_attempted"] += 1
            
            try:
                logger.debug(f"Processing {idx}/{len(iflw_files)}: {iflw_path.name}")
                
                # Extract package ID and iflow ID from filename
                package_id, iflow_id = self._extract_ids_from_filename(iflw_path.name)
                
                # Parse IFLW file and extract participants
                participants = self._parse_iflw_file(iflw_path, package_id, iflow_id)
                
                # Add to consolidated list
                all_participants.extend(participants)
                
                # Update statistics
                stats["iflw_files_processed"] += 1
                stats["total_participants_extracted"] += len(participants)
                
                # Count by type
                for participant in participants:
                    participant_type = participant["type"]
                    if participant_type in stats["participants_by_type"]:
                        stats["participants_by_type"][participant_type] += 1
                
                if len(participants) > 0:
                    logger.debug(f"  Extracted {len(participants)} participants")
                
            except Exception as e:
                stats["iflw_files_failed"] += 1
                logger.error(f"  Failed to process {iflw_path.name}: {e}")
                self._track_error(iflw_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save consolidated output
        self._save_output(all_participants)
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"BPMN participant extraction completed. Processed {stats['iflw_files_processed']}/{stats['iflw_files_attempted']}")
        logger.info(f"Total participants extracted: {stats['total_participants_extracted']}")
        
        return stats
    
    def _extract_ids_from_filename(self, filename: str) -> Tuple[str, str]:
        """
        Extract package ID and iflow ID from filename
        
        Filename format: "{PackageID}---{IflowID}.iflw"
        Example: "Pack2---Group_XSLT.iflw" -> ("Pack2", "Group_XSLT")
        
        Args:
            filename: IFLW filename
            
        Returns:
            Tuple of (package_id, iflow_id)
        """
        # Remove .iflw extension
        name_without_ext = filename.rsplit('.iflw', 1)[0]
        
        # Split on "---" separator (3 dashes, no spaces)
        if '---' in name_without_ext:
            parts = name_without_ext.split('---', 1)
            package_id = parts[0].strip()
            iflow_id = parts[1].strip()
        else:
            # Fallback: use entire name as iflow_id, empty package_id
            logger.warning(f"Filename doesn't match expected format: {filename}")
            package_id = ""
            iflow_id = name_without_ext
        
        return package_id, iflow_id
    
    def _parse_iflw_file(self, iflw_path: Path, package_id: str, iflow_id: str) -> List[Dict[str, str]]:
        """
        Parse IFLW file and extract participant information
        
        Args:
            iflw_path: Path to IFLW file
            package_id: Package identifier
            iflow_id: IFlow identifier
            
        Returns:
            List of participant dictionaries
        """
        participants = []
        
        try:
            # Parse XML
            tree = ET.parse(iflw_path)
            root = tree.getroot()
            
            # Find collaboration element
            collaboration = root.find('.//bpmn2:collaboration', NAMESPACES)
            
            if collaboration is None:
                logger.debug(f"  No collaboration element found in {iflw_path.name}")
                return []
            
            # Find all participant elements
            participant_elements = collaboration.findall('bpmn2:participant', NAMESPACES)
            
            for participant_elem in participant_elements:
                # Extract attributes
                participant_id = participant_elem.get('id', '')
                participant_name = participant_elem.get('name', '')
                ifl_type_raw = participant_elem.get('{http:///com.sap.ifl.model/Ifl.xsd}type', '')
                
                # Normalize type
                participant_type = self._normalize_type(ifl_type_raw)
                
                # Create participant dictionary (use camelCase for JSON output)
                participant = {
                    "id": participant_id,
                    "name": participant_name,
                    "type": participant_type,
                    "iflowId": iflow_id,
                    "packageId": package_id
                }
                
                participants.append(participant)
                
                logger.trace(f"    Participant: id={participant_id}, name={participant_name}, type={participant_type}")
        
        except ET.ParseError as e:
            logger.error(f"  XML parse error in {iflw_path.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"  Error parsing {iflw_path.name}: {e}")
            raise
        
        return participants
    
    def _normalize_type(self, ifl_type: str) -> str:
        """
        Normalize participant type value
        
        Handles the SAP typo "EndpointRecevier" -> "EndpointReceiver"
        
        Args:
            ifl_type: Raw ifl:type attribute value
            
        Returns:
            Normalized type string
        """
        if not ifl_type:
            return "Unknown"
        
        return TYPE_MAPPING.get(ifl_type, "Unknown")
    
    def _save_output(self, participants: List[Dict[str, str]]):
        """
        Save consolidated participants to JSON file
        
        Args:
            participants: List of all participants from all IFLW files
        """
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Output file path
        output_file = self.output_dir / "bpmn-participants.json"
        
        # Write JSON (with nice formatting)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(participants, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved {len(participants)} participants to {output_file}")
    
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
        output_file = self.output_dir / "bpmn-participant-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log: bpmn-participant-extraction-errors.json")