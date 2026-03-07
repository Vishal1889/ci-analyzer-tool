"""
BPMN Message Mapping Extractor for SAP Cloud Integration Analyzer Tool
Extracts message mapping activities from IFLW (BPMN XML) files
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

# XML Namespaces for BPMN 2.0
NAMESPACES = {
    'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
}


@dataclass
class BpmnActivityMessageMapping:
    """Represents a BPMN message mapping activity"""
    # Base activity fields
    id: str
    name: str
    process_id: str
    process_name: str
    iflow_id: str
    package_id: str
    activity_type: str
    sub_activity_type: Optional[str]
    component_version: Optional[str]
    
    # Message mapping-specific fields
    mapping_id: Optional[str]                    # Message mapping resource ID (mappinguri)
    mapping_name: Optional[str]                  # Mapping name
    mapping_path: Optional[str]                  # Mapping path
    mapping_reference: Optional[str]             # Mapping reference (static/dynamic)
    mapping_source_value: Optional[str]          # Mapping source value
    mapping_type: Optional[str]                  # Mapping type
    message_mapping_bundle_id: Optional[str]     # Message mapping bundle ID
    source_message: Optional[str]                # Source message type
    target_message: Optional[str]                # Target message type
    
    def to_camel_case_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys - matching exact base structure"""
        return {
            'activityType': self.activity_type,
            'componentVersion': self.component_version,
            'id': self.id,
            'iflowId': self.iflow_id,
            'mappingname': self.mapping_name,
            'mappingpath': self.mapping_path,
            'mappingReference': self.mapping_reference,
            'mappingSourceValue': self.mapping_source_value,
            'mappingType': self.mapping_type,
            'mappinguri': self.mapping_id,
            'messageMappingBundleId': self.message_mapping_bundle_id,
            'name': self.name,
            'packageId': self.package_id,
            'processId': self.process_id,
            'processName': self.process_name,
            'subActivityType': self.sub_activity_type
        }


class BpmnActivityMessageMappingAnalyzer:
    """Analyzes BPMN XML to extract message mapping activities"""
    
    @staticmethod
    def analyze(root: ET.Element, iflow_id: str, package_id: str) -> List[BpmnActivityMessageMapping]:
        """
        Extract message mapping activities from BPMN XML
        
        Args:
            root: XML root element
            iflow_id: Integration Flow ID
            package_id: Package ID
            
        Returns:
            List of BpmnActivityMessageMapping objects
        """
        mappings = []
        
        # Find all processes and subprocesses
        processes = root.findall('.//bpmn2:process', NAMESPACES)
        subprocesses = root.findall('.//bpmn2:subProcess', NAMESPACES)
        all_processes = processes + subprocesses
        
        logger.debug(f"  Found {len(processes)} processes and {len(subprocesses)} subprocesses")
        
        # Process each process/subprocess
        for proc in all_processes:
            process_id = proc.get('id', '')
            process_name = proc.get('name', '')
            
            # Only process callActivity elements
            call_activities = proc.findall('bpmn2:callActivity', NAMESPACES)
            
            logger.trace(f"    Process {process_id}: {len(call_activities)} callActivities")
            
            for activity in call_activities:
                activity_id = activity.get('id', '')
                activity_name = activity.get('name', '')
                
                # Extract properties
                props = BpmnActivityMessageMappingAnalyzer._extract_properties(activity)
                
                activity_type = props.get('activityType')
                sub_activity_type = props.get('subActivityType')
                mapping_type = props.get('mappingType')
                
                # Filter: Only Message Mappings
                # activityType == "Mapping" 
                # AND mappingType != "XSLTMapping" 
                # AND subActivityType != "XSLTMapping"
                if (BpmnActivityMessageMappingAnalyzer._equals_ignore_case(activity_type, 'Mapping') and 
                    not BpmnActivityMessageMappingAnalyzer._equals_ignore_case(mapping_type, 'XSLTMapping') and
                    not BpmnActivityMessageMappingAnalyzer._equals_ignore_case(sub_activity_type, 'XSLTMapping')):
                    
                    # Extract component version and sub activity type
                    component_version = props.get('componentVersion')
                    sub_activity_type = props.get('subActivityType')
                    
                    # Create message mapping object
                    mapping = BpmnActivityMessageMapping(
                        id=activity_id,
                        name=activity_name,
                        process_id=process_id,
                        process_name=process_name,
                        iflow_id=iflow_id,
                        package_id=package_id,
                        activity_type=activity_type or 'Mapping',
                        sub_activity_type=sub_activity_type,
                        component_version=component_version,
                        mapping_id=props.get('mappinguri'),
                        mapping_name=props.get('mappingname'),
                        mapping_path=props.get('mappingpath'),
                        mapping_reference=props.get('mappingReference'),
                        mapping_source_value=props.get('mappingSourceValue'),
                        mapping_type=props.get('mappingType'),
                        message_mapping_bundle_id=props.get('messageMappingBundleId'),
                        source_message=props.get('messagemappingSourcemessage'),
                        target_message=props.get('messagemappingTargetmessage')
                    )
                    
                    mappings.append(mapping)
                    logger.trace(f"      Extracted message mapping: {activity_id}")
        
        return mappings
    
    @staticmethod
    def _extract_properties(activity_xml: ET.Element) -> Dict[str, Optional[str]]:
        """
        Extract properties from bpmn2:extensionElements/ifl:property
        
        Args:
            activity_xml: Activity XML element
            
        Returns:
            Dictionary of property key-value pairs (value can be None if missing/empty)
        """
        props = {}
        
        extension_elements = activity_xml.findall('bpmn2:extensionElements', NAMESPACES)
        
        for ext in extension_elements:
            ifl_properties = ext.findall('ifl:property', NAMESPACES)
            
            for p in ifl_properties:
                # Properties are stored as child elements
                key_elem = p.find('key')
                value_elem = p.find('value')
                
                if key_elem is not None and key_elem.text:
                    key = key_elem.text.strip()
                    
                    # Get value - None if element missing or text is None/empty
                    if value_elem is not None and value_elem.text:
                        value = value_elem.text.strip()
                        value = value if value else None
                    else:
                        value = None
                    
                    if key:
                        props[key] = value
        
        return props
    
    @staticmethod
    def _equals_ignore_case(str1: Optional[str], str2: str) -> bool:
        """Case-insensitive string comparison"""
        if str1 is None:
            return False
        return str1.lower() == str2.lower()


class BpmnMessageMappingExtractor:
    """Main extractor for BPMN message mappings across all IFLW files"""
    
    def __init__(self, iflw_files_dir: Path, output_dir: Path, timestamp: str = None):
        """
        Initialize BPMN Message Mapping Extractor
        
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
        
        logger.info("BpmnMessageMappingExtractor initialized")
        logger.info(f"  IFLW files: {self.iflw_files_dir}")
        logger.info(f"  Output: {self.output_dir}")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract message mappings from all IFLW files
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting BPMN message mapping extraction...")
        
        stats = {
            "iflw_files_attempted": 0,
            "iflw_files_processed": 0,
            "iflw_files_failed": 0,
            "total_mappings_extracted": 0
        }
        
        # Check if IFLW directory exists
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
        
        # Collect all message mappings
        all_mappings = []
        
        # Process each IFLW file
        for idx, iflw_path in enumerate(iflw_files, 1):
            stats["iflw_files_attempted"] += 1
            
            try:
                logger.debug(f"Processing {idx}/{len(iflw_files)}: {iflw_path.name}")
                
                # Extract IDs from filename
                package_id, iflow_id = self._extract_ids_from_filename(iflw_path.name)
                
                # Parse XML
                tree = ET.parse(iflw_path)
                root = tree.getroot()
                
                # Extract message mappings
                mappings = BpmnActivityMessageMappingAnalyzer.analyze(
                    root=root,
                    iflow_id=iflow_id,
                    package_id=package_id
                )
                
                # Add to master list
                all_mappings.extend(mappings)
                
                # Update statistics
                stats["total_mappings_extracted"] += len(mappings)
                
                stats["iflw_files_processed"] += 1
                
                if len(mappings) > 0:
                    logger.debug(f"  Extracted {len(mappings)} message mappings")
                
            except Exception as e:
                stats["iflw_files_failed"] += 1
                logger.error(f"  Failed to process {iflw_path.name}: {e}")
                self._track_error(iflw_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save output
        self._save_output(all_mappings)
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"BPMN message mapping extraction completed. Processed {stats['iflw_files_processed']}/{stats['iflw_files_attempted']}")
        logger.info(f"Total message mappings extracted: {stats['total_mappings_extracted']}")
        
        return stats
    
    def _extract_ids_from_filename(self, filename: str) -> tuple:
        """Extract package ID and iflow ID from filename"""
        name_without_ext = filename.rsplit('.iflw', 1)[0]
        
        if '---' in name_without_ext:
            parts = name_without_ext.split('---', 1)
            package_id = parts[0].strip()
            iflow_id = parts[1].strip()
        else:
            logger.warning(f"Filename doesn't match expected format: {filename}")
            package_id = ""
            iflow_id = name_without_ext
        
        return package_id, iflow_id
    
    def _save_output(self, mappings: List[BpmnActivityMessageMapping]):
        """Save message mappings to JSON file with camelCase keys"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save mappings with camelCase keys
        mappings_file = self.output_dir / "bpmn-message-mappings.json"
        with open(mappings_file, 'w', encoding='utf-8') as f:
            json.dump([m.to_camel_case_dict() for m in mappings], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(mappings)} message mappings to {mappings_file}")
    
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
        output_file = self.output_dir / "bpmn-message-mapping-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved message mapping extraction error log: bpmn-message-mapping-extraction-errors.json")