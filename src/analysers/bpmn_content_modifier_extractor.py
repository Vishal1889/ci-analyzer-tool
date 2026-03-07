"""
BPMN Content Modifier (Enricher) Extractor for SAP Cloud Integration Analyzer Tool
Extracts content modifier activities that modify message headers or properties
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from utils.logger import get_logger
from analysers.bpmn_process_activity_resolver import BpmnProcessActivityResolver

logger = get_logger(__name__)

# XML Namespaces for BPMN 2.0
NAMESPACES = {
    'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
}


@dataclass
class BpmnActivityEnricher:
    """Represents a BPMN content modifier (enricher) row"""
    # Row-specific fields (9 fields)
    row_table: str                          # "header" or "property"
    row_action: Optional[str]               # Action (e.g., "Create", "Delete")
    row_type: Optional[str]                 # Type (e.g., "expression")
    row_name: Optional[str]                 # Name of header/property
    row_datatype: Optional[str]             # Data type
    row_value: Optional[str]                # Raw value (may contain {{placeholder}})
    row_value_resolved: Optional[str]       # Resolved value
    row_default: Optional[str]              # Default value (may contain {{placeholder}})
    row_default_resolved: Optional[str]     # Resolved default
    
    # Common activity fields (9 fields)
    activity_type: str                      # Always "Enricher"
    component_version: Optional[str]        # Component version
    id: str                                 # Activity ID
    iflow_id: str                          # IFlow ID
    name: str                              # Activity name
    package_id: str                        # Package ID
    process_id: str                        # Process ID
    process_name: str                      # Process name
    sub_activity_type: Optional[str]       # Sub activity type (usually null)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with exact field order from specification"""
        return {
            # Row-specific fields (1-9)
            'rowTable': self.row_table,
            'rowAction': self.row_action,
            'rowType': self.row_type,
            'rowName': self.row_name,
            'rowDatatype': self.row_datatype,
            'rowValue': self.row_value,
            'rowValueResolved': self.row_value_resolved,
            'rowDefault': self.row_default,
            'rowDefaultResolved': self.row_default_resolved,
            
            # Common activity fields (10-18)
            'activityType': self.activity_type,
            'componentVersion': self.component_version,
            'id': self.id,
            'iflowId': self.iflow_id,
            'name': self.name,
            'packageId': self.package_id,
            'processId': self.process_id,
            'processName': self.process_name,
            'subActivityType': self.sub_activity_type
        }


class BpmnActivityEnricherAnalyzer:
    """Analyzes BPMN XML to extract content modifier (enricher) activities"""
    
    @staticmethod
    def analyze(root: ET.Element, iflow_id: str, package_id: str) -> List[BpmnActivityEnricher]:
        """
        Extract content modifier activities from BPMN XML
        
        Args:
            root: XML root element
            iflow_id: Integration Flow ID
            package_id: Package ID
            
        Returns:
            List of BpmnActivityEnricher objects (one per header/property row)
        """
        enrichers = []
        
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
                props = BpmnActivityEnricherAnalyzer._extract_properties(activity)
                
                activity_type = props.get('activityType')
                
                # Filter: Only Enricher activities
                if not BpmnActivityEnricherAnalyzer._equals_ignore_case(activity_type, 'Enricher'):
                    continue
                
                component_version = props.get('componentVersion')
                sub_activity_type = props.get('subActivityType')
                
                logger.trace(f"      Found Enricher: {activity_id} (version {component_version})")
                
                # Parse based on component version
                rows = []
                
                if component_version == '1.1':
                    # Version 1.1: Legacy text format
                    rows = BpmnActivityEnricherAnalyzer._parse_version_1_1(props)
                else:
                    # Other versions: XML format
                    rows = BpmnActivityEnricherAnalyzer._parse_xml_format(props)
                
                # Create BpmnActivityEnricher object for each row
                for row in rows:
                    enricher = BpmnActivityEnricher(
                        # Row-specific fields
                        row_table=row['table'],
                        row_action=row.get('Action'),
                        row_type=row.get('Type'),
                        row_name=row.get('Name'),
                        row_datatype=row.get('Datatype'),
                        row_value=row.get('Value'),
                        row_value_resolved=None,  # Will be resolved later
                        row_default=row.get('Default'),
                        row_default_resolved=None,  # Will be resolved later
                        
                        # Common activity fields
                        activity_type='Enricher',
                        component_version=component_version,
                        id=activity_id,
                        iflow_id=iflow_id,
                        name=activity_name,
                        package_id=package_id,
                        process_id=process_id,
                        process_name=process_name,
                        sub_activity_type=sub_activity_type
                    )
                    
                    enrichers.append(enricher)
                
                if len(rows) > 0:
                    logger.trace(f"        Extracted {len(rows)} content modifier rows")
        
        return enrichers
    
    @staticmethod
    def _parse_version_1_1(props: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
        """
        Parse version 1.1 text format properties
        
        Format: PREFIX_Key:=:Value:;PREFIX_Key2:=:Value2:;...
        - Between cells: :; (colon-semicolon)
        - Within cell: :=: (colon-equals-colon)
        - Prefixes: HEADER_ for headers, property_ for properties
        
        Args:
            props: Property dictionary
            
        Returns:
            List of row dictionaries with 'table' and field data
        """
        rows = []
        
        # Process header table
        header_rows = BpmnActivityEnricherAnalyzer._parse_text_table(props, 'HEADER_', 'header')
        rows.extend(header_rows)
        
        # Process property table
        property_rows = BpmnActivityEnricherAnalyzer._parse_text_table(props, 'property_', 'property')
        rows.extend(property_rows)
        
        return rows
    
    @staticmethod
    def _parse_text_table(props: Dict[str, Optional[str]], prefix: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Parse a single table from text format properties
        
        Args:
            props: Property dictionary
            prefix: Property prefix (e.g., "HEADER_" or "property_")
            table_name: Table name ("header" or "property")
            
        Returns:
            List of row dictionaries
        """
        rows = []
        
        # Collect all properties with this prefix
        cells_by_field = {}  # field_name -> list of values
        
        for key, value in props.items():
            if key.startswith(prefix):
                # Extract field name (e.g., "HEADER_Action" -> "Action")
                field_name = key[len(prefix):]
                
                if value:
                    # Parse delimited string: "val1:;val2:;val3"
                    # Split by :; to get individual cell values
                    cell_values = value.split(':;')
                    
                    # Clean up values (remove :=: if present and trailing colons)
                    cleaned_values = []
                    for cv in cell_values:
                        # Remove :=: delimiter if present
                        if ':=:' in cv:
                            parts = cv.split(':=:', 1)
                            cleaned = parts[1] if len(parts) > 1 else parts[0]
                        else:
                            cleaned = cv
                        
                        # Remove trailing colon
                        cleaned = cleaned.rstrip(':')
                        cleaned_values.append(cleaned if cleaned else None)
                    
                    cells_by_field[field_name] = cleaned_values
        
        if not cells_by_field:
            return rows
        
        # Determine number of rows (max length of any field)
        max_rows = max(len(values) for values in cells_by_field.values())
        
        # Build rows
        for i in range(max_rows):
            row = {'table': table_name}
            
            for field_name, values in cells_by_field.items():
                if i < len(values):
                    row[field_name] = values[i]
                else:
                    row[field_name] = None
            
            rows.append(row)
        
        return rows
    
    @staticmethod
    def _parse_xml_format(props: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
        """
        Parse XML format properties
        
        Format: <rows><row><cell id="Action">value</cell>...</row></rows>
        
        Args:
            props: Property dictionary
            
        Returns:
            List of row dictionaries with 'table' and field data
        """
        rows = []
        
        # Process header table
        header_xml = props.get('headerTable')
        if header_xml:
            header_rows = BpmnActivityEnricherAnalyzer._parse_xml_table(header_xml, 'header')
            rows.extend(header_rows)
        
        # Process property table
        property_xml = props.get('propertyTable')
        if property_xml:
            property_rows = BpmnActivityEnricherAnalyzer._parse_xml_table(property_xml, 'property')
            rows.extend(property_rows)
        
        return rows
    
    @staticmethod
    def _parse_xml_table(xml_str: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Parse XML table string into row dictionaries
        
        Args:
            xml_str: XML string containing rows
            table_name: Table name ("header" or "property")
            
        Returns:
            List of row dictionaries
        """
        rows = []
        
        try:
            # XML might not have a single root element, so wrap it
            if not xml_str.strip().startswith('<rows>'):
                xml_str = f'<rows>{xml_str}</rows>'
            
            # Parse XML
            root = ET.fromstring(xml_str)
            
            # Find all row elements
            row_elements = root.findall('.//row')
            
            for row_elem in row_elements:
                row = {'table': table_name}
                
                # Extract all cell elements
                cells = row_elem.findall('cell')
                
                for cell in cells:
                    cell_id = cell.get('id')
                    cell_value = cell.text
                    
                    if cell_id:
                        # Use empty string for empty cells, None for missing
                        row[cell_id] = cell_value if cell_value is not None else ''
                
                rows.append(row)
        
        except ET.ParseError as e:
            logger.warning(f"Failed to parse XML table: {e}")
        
        return rows
    
    @staticmethod
    def _extract_properties(activity_xml: ET.Element) -> Dict[str, Optional[str]]:
        """Extract properties from bpmn2:extensionElements/ifl:property"""
        props = {}
        
        extension_elements = activity_xml.findall('bpmn2:extensionElements', NAMESPACES)
        
        for ext in extension_elements:
            ifl_properties = ext.findall('ifl:property', NAMESPACES)
            
            for p in ifl_properties:
                key_elem = p.find('key')
                value_elem = p.find('value')
                
                if key_elem is not None and key_elem.text:
                    key = key_elem.text.strip()
                    
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


class BpmnContentModifierExtractor:
    """Main extractor for BPMN content modifiers across all IFLW files"""
    
    def __init__(self, iflw_files_dir: Path, output_dir: Path, timestamp: str = None):
        """
        Initialize BPMN Content Modifier Extractor
        
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
        
        logger.info("BpmnContentModifierExtractor initialized")
        logger.info(f"  IFLW files: {self.iflw_files_dir}")
        logger.info(f"  Output: {self.output_dir}")
    
    def extract_all(self, configurations: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Extract content modifiers from all IFLW files and resolve configurations
        
        Args:
            configurations: Dictionary mapping iflow_id to configuration dict
            
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting BPMN content modifier extraction...")
        
        stats = {
            "iflw_files_attempted": 0,
            "iflw_files_processed": 0,
            "iflw_files_failed": 0,
            "total_modifiers_extracted": 0
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
        
        # Collect all content modifiers
        all_modifiers = []
        
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
                
                # Extract content modifiers
                modifiers = BpmnActivityEnricherAnalyzer.analyze(
                    root=root,
                    iflow_id=iflow_id,
                    package_id=package_id
                )
                
                # Resolve configurations if provided
                if configurations and iflow_id in configurations:
                    cfg = configurations[iflow_id]
                    for modifier in modifiers:
                        modifier.row_value_resolved = BpmnProcessActivityResolver.resolveOnePass(
                            modifier.row_value, cfg
                        )
                        modifier.row_default_resolved = BpmnProcessActivityResolver.resolveOnePass(
                            modifier.row_default, cfg
                        )
                else:
                    # No config available - resolved values same as raw values
                    for modifier in modifiers:
                        modifier.row_value_resolved = modifier.row_value
                        modifier.row_default_resolved = modifier.row_default
                
                # Add to master list
                all_modifiers.extend(modifiers)
                
                # Update statistics
                stats["total_modifiers_extracted"] += len(modifiers)
                stats["iflw_files_processed"] += 1
                
                if len(modifiers) > 0:
                    logger.debug(f"  Extracted {len(modifiers)} content modifier rows")
                
            except Exception as e:
                stats["iflw_files_failed"] += 1
                logger.error(f"  Failed to process {iflw_path.name}: {e}")
                self._track_error(iflw_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save output
        self._save_output(all_modifiers)
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"BPMN content modifier extraction completed. Processed {stats['iflw_files_processed']}/{stats['iflw_files_attempted']}")
        logger.info(f"Total content modifier rows extracted: {stats['total_modifiers_extracted']}")
        
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
    
    def _save_output(self, modifiers: List[BpmnActivityEnricher]):
        """Save content modifiers to JSON file"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save modifiers
        output_file = self.output_dir / "bpmn-content-modifiers.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([m.to_dict() for m in modifiers], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(modifiers)} content modifier rows to {output_file}")
    
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
        output_file = self.output_dir / "bpmn-content-modifier-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved content modifier extraction error log: bpmn-content-modifier-extraction-errors.json")