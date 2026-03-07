"""
BPMN Process Activity Extractor for SAP Cloud Integration Analyzer Tool
Extracts process activities (integration flow steps/components) from IFLW (BPMN XML) files
Includes configuration resolution for activity properties
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple, Optional
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

# Metadata fields that should be promoted to activity-level fields
METADATA_KEYS = {
    'activityType',
    'subActivityType',
    'componentVersion',
    'cmdVariantUri'
}


@dataclass
class BpmnProcessActivity:
    """Represents a BPMN process activity (integration flow step/component)"""
    # Identification
    id: str
    name: str
    process_id: str
    process_name: str
    iflow_id: str
    package_id: str
    
    # Activity metadata (promoted from properties)
    # Can be None if value is blank in XML, or '' if key is missing
    activity_type: Optional[str]
    sub_activity_type: Optional[str]
    component_version: Optional[str]
    cmd_variant_uri: Optional[str] = None
    
    def to_camel_case_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys"""
        return {
            'id': self.id,
            'name': self.name,
            'processId': self.process_id,
            'processName': self.process_name,
            'iflowId': self.iflow_id,
            'packageId': self.package_id,
            'activityType': self.activity_type,
            'subActivityType': self.sub_activity_type,
            'componentVersion': self.component_version,
            'cmdVariantUri': self.cmd_variant_uri
        }


@dataclass
class BpmnProcessActivityProperty:
    """Represents a property of a BPMN process activity"""
    package_id: str
    iflow_id: str
    process_id: str
    process_name: str
    activity_id: str
    activity_name: str
    activity_type: Optional[str]  # Can be None if blank in XML
    sub_activity_type: Optional[str]  # Can be None if blank in XML
    component_version: Optional[str]  # Can be None if blank in XML
    key: str
    raw_value: Optional[str]  # Can be None for blank XML values
    resolved_value: Optional[str] = None
    
    def to_camel_case_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys"""
        return {
            'packageId': self.package_id,
            'iflowId': self.iflow_id,
            'processId': self.process_id,
            'processName': self.process_name,
            'activityId': self.activity_id,
            'activityName': self.activity_name,
            'activityType': self.activity_type,
            'subActivityType': self.sub_activity_type,
            'componentVersion': self.component_version,
            'key': self.key,
            'rawValue': self.raw_value,
            'resolvedValue': self.resolved_value
        }


class BpmnProcessActivityAnalyzer:
    """Analyzes BPMN XML to extract process activities"""
    
    @staticmethod
    def analyze(root: ET.Element, iflow_id: str, package_id: str) -> Tuple[List[BpmnProcessActivity], List[BpmnProcessActivityProperty]]:
        """
        Analyze BPMN XML to extract all process activities
        
        Args:
            root: XML root element
            iflow_id: Integration Flow ID
            package_id: Package ID
            
        Returns:
            Tuple of (activities list, properties list)
        """
        activities = []
        properties = []
        
        # Find all processes and subprocesses
        processes = root.findall('.//bpmn2:process', NAMESPACES)
        subprocesses = root.findall('.//bpmn2:subProcess', NAMESPACES)
        all_processes = processes + subprocesses
        
        logger.debug(f"  Found {len(processes)} processes and {len(subprocesses)} subprocesses")
        
        # Process each process/subprocess
        for proc in all_processes:
            process_id = proc.get('id', '')
            process_name = proc.get('name', '')
            
            # Find all activity types
            call_activities = proc.findall('bpmn2:callActivity', NAMESPACES)
            exclusive_gateways = proc.findall('bpmn2:exclusiveGateway', NAMESPACES)
            parallel_gateways = proc.findall('bpmn2:parallelGateway', NAMESPACES)
            
            all_activities = call_activities + exclusive_gateways + parallel_gateways
            
            logger.trace(f"    Process {process_id}: {len(call_activities)} callActivities, "
                        f"{len(exclusive_gateways)} exclusiveGateways, {len(parallel_gateways)} parallelGateways")
            
            # Process each activity
            for activity_xml in all_activities:
                activity_id = activity_xml.get('id', '')
                activity_name = activity_xml.get('name', '')
                
                # Extract properties from extension elements
                props = BpmnProcessActivityAnalyzer._extract_properties(activity_xml)
                
                # Extract metadata from properties
                # Preserve None for both missing keys and blank values (both → null in JSON)
                activity_type = props.get('activityType')
                sub_activity_type = props.get('subActivityType')
                component_version = props.get('componentVersion')
                cmd_variant_uri = props.get('cmdVariantUri')
                
                # Create activity object
                activity = BpmnProcessActivity(
                    id=activity_id,
                    name=activity_name,
                    process_id=process_id,
                    process_name=process_name,
                    iflow_id=iflow_id,
                    package_id=package_id,
                    activity_type=activity_type,
                    sub_activity_type=sub_activity_type,
                    component_version=component_version,
                    cmd_variant_uri=cmd_variant_uri
                )
                activities.append(activity)
                
                # Create property objects (exclude metadata fields)
                for key, value in props.items():
                    if key not in METADATA_KEYS:
                        prop = BpmnProcessActivityProperty(
                            package_id=package_id,
                            iflow_id=iflow_id,
                            process_id=process_id,
                            process_name=process_name,
                            activity_id=activity_id,
                            activity_name=activity_name,
                            activity_type=activity_type,
                            sub_activity_type=sub_activity_type,
                            component_version=component_version,
                            key=key,
                            raw_value=value,  # Keep None as-is (will be null in JSON)
                            resolved_value=None  # Will be filled by resolver
                        )
                        properties.append(prop)
                
                logger.trace(f"      Activity {activity_id}: {len(props)} properties ({len([k for k in props.keys() if k not in METADATA_KEYS])} non-metadata)")
        
        return activities, properties
    
    @staticmethod
    def _extract_properties(activity_xml: ET.Element) -> Dict[str, Optional[str]]:
        """
        Extract properties from bpmn2:extensionElements/ifl:property
        
        Note: Activity properties use CHILD ELEMENTS (like channels)
        not attributes as originally documented
        
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
                # Properties are stored as child elements, not attributes
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
    def _normalize(s: Optional[str]) -> Optional[str]:
        """Trim whitespace and return None if empty (deprecated - kept for compatibility)"""
        if not s:
            return None
        s = s.strip()
        return s if s else None


class BpmnProcessActivityResolver:
    """Resolves configuration placeholders in activity properties"""
    
    @staticmethod
    def resolve_config_to_properties(properties: List[BpmnProcessActivityProperty],
                                     config: Dict[str, str]):
        """
        Resolve {{placeholder}} values in properties using configuration
        
        Args:
            properties: List of activity properties to resolve
            config: Configuration dictionary {key: value} for the iflow
        """
        if not properties:
            return
        
        if config is None:
            config = {}
        
        for prop in properties:
            prop.resolved_value = BpmnProcessActivityResolver._resolve_one_pass(
                prop.raw_value, config
            )
    
    @staticmethod
    def _resolve_one_pass(input_str: Optional[str], config: Dict[str, str]) -> Optional[str]:
        """
        Replace {{key}} placeholders with values from config dictionary
        
        Args:
            input_str: String potentially containing {{key}} placeholders (can be None)
            config: Configuration dictionary
            
        Returns:
            String with placeholders replaced (or kept if no value found), or None if input was None
        """
        if not input_str or '{{' not in input_str:
            return input_str  # Returns None if input_str is None
        
        result = []
        i = 0
        
        while i < len(input_str):
            start = input_str.find('{{', i)
            
            if start < 0:
                # No more placeholders
                result.append(input_str[i:])
                break
            
            # Append text before placeholder
            result.append(input_str[i:start])
            
            # Find end of placeholder
            end = input_str.find('}}', start + 2)
            
            if end < 0:
                # Malformed placeholder, keep rest as-is
                result.append(input_str[start:])
                break
            
            # Extract key and lookup value
            key = input_str[start + 2:end]
            value = config.get(key)
            
            if value:
                result.append(value)
            else:
                # Keep placeholder if no value found
                result.append(input_str[start:end + 2])
            
            i = end + 2
        
        return ''.join(result)


class BpmnActivityExtractor:
    """Main extractor for BPMN process activities across all IFLW files"""
    
    def __init__(self, iflw_files_dir: Path, configurations_file: Path,
                 output_dir: Path, timestamp: str = None):
        """
        Initialize BPMN Activity Extractor
        
        Args:
            iflw_files_dir: Directory containing IFLW files
            configurations_file: Path to configurations.json
            output_dir: Directory for output JSON files
            timestamp: Optional timestamp for organized output
        """
        self.iflw_files_dir = Path(iflw_files_dir)
        self.configurations_file = Path(configurations_file)
        self.output_dir = Path(output_dir)
        self.timestamp = timestamp
        
        # Track errors
        self.errors = []
        
        logger.info("BpmnActivityExtractor initialized")
        logger.info(f"  IFLW files: {self.iflw_files_dir}")
        logger.info(f"  Configurations: {self.configurations_file}")
        logger.info(f"  Output: {self.output_dir}")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract activities from all IFLW files
        
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting BPMN activity extraction...")
        
        stats = {
            "iflw_files_attempted": 0,
            "iflw_files_processed": 0,
            "iflw_files_failed": 0,
            "total_activities_extracted": 0,
            "total_properties_extracted": 0,
            "activities_by_type": {}
        }
        
        # Load configurations
        configurations = self._load_configurations()
        logger.info(f"Loaded configurations for {len(configurations)} iflows")
        
        # Check if IFLW directory exists
        if not self.iflw_files_dir.exists():
            logger.warning(f"IFLW files directory not found: {self.iflw_files_dir}")
            self._save_output([], [])
            return stats
        
        # Get all IFLW files
        iflw_files = list(self.iflw_files_dir.glob("*.iflw"))
        
        if not iflw_files:
            logger.info("No IFLW files found")
            self._save_output([], [])
            return stats
        
        logger.info(f"Found {len(iflw_files)} IFLW files to process")
        
        # Collect all activities and properties
        all_activities = []
        all_properties = []
        
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
                
                # Get configuration for this iflow
                iflow_config = configurations.get(iflow_id, {})
                
                # Extract activities
                activities, properties = BpmnProcessActivityAnalyzer.analyze(
                    root=root,
                    iflow_id=iflow_id,
                    package_id=package_id
                )
                
                # Resolve configurations
                BpmnProcessActivityResolver.resolve_config_to_properties(
                    properties, iflow_config
                )
                
                # Add to master lists
                all_activities.extend(activities)
                all_properties.extend(properties)
                
                # Update statistics
                stats["total_activities_extracted"] += len(activities)
                stats["total_properties_extracted"] += len(properties)
                
                # Track activity types
                for activity in activities:
                    activity_type = activity.activity_type
                    if activity_type:
                        if activity_type not in stats["activities_by_type"]:
                            stats["activities_by_type"][activity_type] = 0
                        stats["activities_by_type"][activity_type] += 1
                
                stats["iflw_files_processed"] += 1
                
                if len(activities) > 0:
                    logger.debug(f"  Extracted {len(activities)} activities, {len(properties)} properties")
                
            except Exception as e:
                stats["iflw_files_failed"] += 1
                logger.error(f"  Failed to process {iflw_path.name}: {e}")
                self._track_error(iflw_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save output
        self._save_output(all_activities, all_properties)
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"BPMN activity extraction completed. Processed {stats['iflw_files_processed']}/{stats['iflw_files_attempted']}")
        logger.info(f"Total activities extracted: {stats['total_activities_extracted']}")
        logger.info(f"Total properties extracted: {stats['total_properties_extracted']}")
        
        if stats["activities_by_type"]:
            logger.info("Activities by type:")
            for activity_type, count in sorted(stats["activities_by_type"].items()):
                logger.info(f"  {activity_type}: {count}")
        
        return stats
    
    def _load_configurations(self) -> Dict[str, Dict[str, str]]:
        """
        Load configurations from JSON file and build nested dictionary
        
        Returns:
            Dictionary {iflow_id: {param_key: param_value}}
        """
        if not self.configurations_file.exists():
            logger.warning(f"Configurations file not found: {self.configurations_file}")
            return {}
        
        try:
            with open(self.configurations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract results array
            results = data.get('d', {}).get('results', [])
            
            # Build nested dictionary
            config_dict = {}
            for item in results:
                iflow_id = item.get('IflowId', '')
                param_key = item.get('ParameterKey', '')
                param_value = item.get('ParameterValue', '')
                
                if iflow_id and param_key:
                    if iflow_id not in config_dict:
                        config_dict[iflow_id] = {}
                    config_dict[iflow_id][param_key] = param_value
            
            return config_dict
            
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            return {}
    
    def _extract_ids_from_filename(self, filename: str) -> Tuple[str, str]:
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
    
    def _save_output(self, activities: List[BpmnProcessActivity],
                     properties: List[BpmnProcessActivityProperty]):
        """Save activities and properties to JSON files with camelCase keys"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save activities with camelCase keys
        activities_file = self.output_dir / "bpmn-activities.json"
        with open(activities_file, 'w', encoding='utf-8') as f:
            json.dump([a.to_camel_case_dict() for a in activities], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(activities)} activities to {activities_file}")
        
        # Save properties with camelCase keys
        properties_file = self.output_dir / "bpmn-activities-properties.json"
        with open(properties_file, 'w', encoding='utf-8') as f:
            json.dump([p.to_camel_case_dict() for p in properties], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(properties)} properties to {properties_file}")
    
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
        output_file = self.output_dir / "bpmn-activity-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved extraction error log: bpmn-activity-extraction-errors.json")