"""
IFLW Timer Extractor for SAP Cloud Integration Analyzer Tool
Extracts timer configurations from Timer Start Events and Scheduled Channels
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from utils.logger import get_logger
from analysers.iflw_process_activity_resolver import IflwProcessActivityResolver

logger = get_logger(__name__)

# XML Namespaces for BPMN 2.0
NAMESPACES = {
    'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
}


@dataclass
class IflwTimer:
    """Represents an IFLW timer configuration"""
    package_id: str
    iflow_id: str
    type: str  # "Event" or "Channel"
    owner_type: str
    owner_id: str
    owner_name: str
    trigger_id: str
    trigger_name: str
    component_version: Optional[str]
    schedule_key: Optional[str]
    schedule_key_resolved: Optional[str]
    cron_expression: Optional[str]
    time_zone: Optional[str]
    cron_description: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with exact field order from specification"""
        return {
            'packageId': self.package_id,
            'iflowId': self.iflow_id,
            'type': self.type,
            'ownerType': self.owner_type,
            'ownerId': self.owner_id,
            'ownerName': self.owner_name,
            'triggerId': self.trigger_id,
            'triggerName': self.trigger_name,
            'componentVersion': self.component_version,
            'scheduleKey': self.schedule_key,
            'scheduleKeyResolved': self.schedule_key_resolved,
            'cronExpression': self.cron_expression,
            'timeZone': self.time_zone,
            'cronDescription': self.cron_description
        }


class IflwTimerAnalyzer:
    """Analyzes IFLW XML to extract timer configurations"""
    
    @staticmethod
    def analyze(root: ET.Element, iflow_id: str, package_id: str, configurations: Dict[str, str] = None) -> List[IflwTimer]:
        """
        Extract timer configurations from IFLW XML
        
        Args:
            root: XML root element
            iflow_id: Integration Flow ID
            package_id: Package ID
            configurations: Configuration dictionary for placeholder resolution
            
        Returns:
            List of IflwTimer objects
        """
        timers = []
        
        # Extract Timer Start Events (type="Event")
        event_timers = IflwTimerAnalyzer._extract_timer_events(root, iflow_id, package_id, configurations)
        timers.extend(event_timers)
        
        # Extract Scheduled Channels (type="Channel")
        channel_timers = IflwTimerAnalyzer._extract_scheduled_channels(root, iflow_id, package_id, configurations)
        timers.extend(channel_timers)
        
        return timers
    
    @staticmethod
    def _extract_timer_events(root: ET.Element, iflow_id: str, package_id: str, configurations: Dict[str, str] = None) -> List[IflwTimer]:
        """Extract Timer Start Events from processes"""
        timers = []
        
        # Find all processes and subprocesses
        processes = root.findall('.//bpmn2:process', NAMESPACES)
        subprocesses = root.findall('.//bpmn2:subProcess', NAMESPACES)
        all_processes = processes + subprocesses
        
        for process in all_processes:
            process_id = process.get('id', '')
            process_name = process.get('name', '')
            
            # Find all start events with timer definitions
            start_events = process.findall('bpmn2:startEvent', NAMESPACES)
            
            for start_event in start_events:
                # Check if it has a timer definition
                timer_def = start_event.find('bpmn2:timerEventDefinition', NAMESPACES)
                if timer_def is None:
                    continue
                
                event_id = start_event.get('id', '')
                event_name = start_event.get('name', '')
                
                # Extract properties from timerEventDefinition (not from startEvent!)
                props = IflwTimerAnalyzer._extract_properties(timer_def)
                
                # Check if this is a StartTimerEvent (filter condition from Java code)
                activity_type = props.get('activityType')
                if activity_type and not IflwTimerAnalyzer._equals_ignore_case(activity_type, 'StartTimerEvent'):
                    continue
                
                # Use activityType if present, otherwise default to StartTimerEvent
                activity_type = activity_type or 'StartTimerEvent'
                
                component_version = props.get('componentVersion')
                schedule_key = props.get('scheduleKey')
                
                # Resolve configuration
                schedule_key_resolved = IflwProcessActivityResolver.resolveOnePass(
                    schedule_key, configurations
                ) if configurations else schedule_key
                
                # Parse cron expression
                cron_expression, time_zone, cron_description = IflwTimerAnalyzer._analyze_cron_expression(
                    schedule_key_resolved
                )
                
                timer = IflwTimer(
                    package_id=package_id,
                    iflow_id=iflow_id,
                    type='Event',
                    owner_type=activity_type or 'StartTimerEvent',
                    owner_id=process_id,
                    owner_name=process_name,
                    trigger_id=event_id,
                    trigger_name=event_name,
                    component_version=component_version,
                    schedule_key=schedule_key,
                    schedule_key_resolved=schedule_key_resolved,
                    cron_expression=cron_expression,
                    time_zone=time_zone,
                    cron_description=cron_description
                )
                
                timers.append(timer)
                logger.trace(f"      Found Timer Event: {event_id} in process {process_id}")
        
        return timers
    
    @staticmethod
    def _extract_scheduled_channels(root: ET.Element, iflow_id: str, package_id: str, configurations: Dict[str, str] = None) -> List[IflwTimer]:
        """Extract Scheduled Channels from message flows"""
        timers = []
        
        # Build participant lookup
        participants = {}
        collaborations = root.findall('.//bpmn2:collaboration', NAMESPACES)
        for collab in collaborations:
            for participant in collab.findall('bpmn2:participant', NAMESPACES):
                p_id = participant.get('id')
                p_name = participant.get('name')
                if p_id:
                    participants[p_id] = p_name or ''
        
        # Find all message flows with scheduleKey
        for collab in collaborations:
            message_flows = collab.findall('bpmn2:messageFlow', NAMESPACES)
            
            for msg_flow in message_flows:
                flow_id = msg_flow.get('id', '')
                flow_name = msg_flow.get('name', '')
                source_ref = msg_flow.get('sourceRef', '')
                
                # Extract properties
                props = IflwTimerAnalyzer._extract_properties(msg_flow)
                
                schedule_key = props.get('scheduleKey')
                
                # Skip if no schedule key
                if not schedule_key:
                    continue
                
                component_type = props.get('ComponentType')
                component_version = props.get('componentVersion')
                
                # Look up participant name
                participant_name = participants.get(source_ref, '')
                
                # Resolve configuration
                schedule_key_resolved = IflwProcessActivityResolver.resolveOnePass(
                    schedule_key, configurations
                ) if configurations else schedule_key
                
                # Parse cron expression
                cron_expression, time_zone, cron_description = IflwTimerAnalyzer._analyze_cron_expression(
                    schedule_key_resolved
                )
                
                timer = IflwTimer(
                    package_id=package_id,
                    iflow_id=iflow_id,
                    type='Channel',
                    owner_type=component_type or '',
                    owner_id=source_ref,
                    owner_name=participant_name,
                    trigger_id=flow_id,
                    trigger_name=flow_name,
                    component_version=component_version,
                    schedule_key=schedule_key,
                    schedule_key_resolved=schedule_key_resolved,
                    cron_expression=cron_expression,
                    time_zone=time_zone,
                    cron_description=cron_description
                )
                
                timers.append(timer)
                logger.trace(f"      Found Scheduled Channel: {flow_id} ({component_type})")
        
        return timers
    
    @staticmethod
    def _analyze_cron_expression(schedule_key_resolved: Optional[str]) -> tuple:
        """
        Parse cron expression from resolved schedule key
        
        Returns:
            Tuple of (cron_expression, time_zone, cron_description)
        """
        if not schedule_key_resolved:
            return None, None, None
        
        # Special case: fireNow=true
        if schedule_key_resolved == 'fireNow=true':
            return 'fireNow=true', None, 'fireNow=true'
        
        cron_expression = None
        time_zone = None
        
        # Detect format: XML vs Text
        if schedule_key_resolved.strip().startswith('<row>'):
            # XML format
            cron_expression, time_zone = IflwTimerAnalyzer._parse_xml_schedule(schedule_key_resolved)
        else:
            # Text format
            cron_expression, time_zone = IflwTimerAnalyzer._parse_text_schedule(schedule_key_resolved)
        
        # Generate description
        cron_description = IflwTimerAnalyzer._generate_cron_description(cron_expression)
        
        return cron_expression, time_zone, cron_description
    
    @staticmethod
    def _parse_xml_schedule(xml_str: str) -> tuple:
        """
        Parse XML format schedule
        
        Returns:
            Tuple of (cron_expression, time_zone)
        """
        try:
            # Wrap in <rows> tag
            if not xml_str.strip().startswith('<rows>'):
                xml_str = f'<rows>{xml_str}</rows>'
            
            root = ET.fromstring(xml_str)
            
            # Find row with cell[0] == "schedule1"
            rows = root.findall('.//row')
            for row in rows:
                cells = row.findall('cell')
                if len(cells) >= 2:
                    first_cell = cells[0].text or ''
                    if first_cell.strip() == 'schedule1':
                        # Found schedule1 row
                        schedule_value = cells[1].text or ''
                        
                        # Special case for fireNow
                        if schedule_value == 'fireNow=true':
                            return 'fireNow=true', None
                        
                        # Replace + with space
                        schedule_value = schedule_value.replace('+', ' ')
                        
                        # Split by &trigger.timeZone= or &amp;trigger.timeZone=
                        if '&trigger.timeZone=' in schedule_value:
                            parts = schedule_value.split('&trigger.timeZone=', 1)
                        elif '&amp;trigger.timeZone=' in schedule_value:
                            parts = schedule_value.split('&amp;trigger.timeZone=', 1)
                        else:
                            parts = [schedule_value]
                        
                        cron_expr = parts[0].strip()
                        tz = parts[1].strip() if len(parts) > 1 else None
                        
                        return cron_expr, tz
            
            return None, None
            
        except ET.ParseError as e:
            logger.warning(f"Failed to parse XML schedule: {e}")
            return None, None
    
    @staticmethod
    def _parse_text_schedule(text: str) -> tuple:
        """
        Parse text format schedule
        
        Returns:
            Tuple of (cron_expression, time_zone)
        """
        # Split by --tz=
        if '--tz=' in text:
            parts = text.split('--tz=', 1)
            cron_expr = parts[0].strip()
            tz = parts[1].strip() if len(parts) > 1 else None
            return cron_expr, tz
        else:
            return text.strip(), None
    
    @staticmethod
    def _generate_cron_description(cron_expression: Optional[str]) -> Optional[str]:
        """
        Generate human-readable description of cron expression
        
        Args:
            cron_expression: Cron expression string
            
        Returns:
            Human-readable description or the expression itself if invalid
        """
        if not cron_expression:
            return None
        
        # Special case for fireNow
        if cron_expression == 'fireNow=true':
            return 'fireNow=true'
        
        try:
            # Try using cron-descriptor library
            from cron_descriptor import get_description
            
            # cron-descriptor expects standard cron format (5-7 fields)
            # Try to parse and generate description
            description = get_description(cron_expression)
            return description
            
        except ImportError:
            # Library not installed, return expression as-is
            logger.warning("cron-descriptor library not installed, using expression as description")
            return cron_expression
        except Exception as e:
            # Invalid cron expression or parsing error
            logger.trace(f"Failed to parse cron expression '{cron_expression}': {e}")
            return cron_expression
    
    @staticmethod
    def _extract_properties(element: ET.Element) -> Dict[str, Optional[str]]:
        """Extract properties from bpmn2:extensionElements/ifl:property"""
        props = {}
        
        extension_elements = element.findall('bpmn2:extensionElements', NAMESPACES)
        
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


class IflwTimerExtractor:
    """Main extractor for IFLW timers across all IFLW files"""
    
    def __init__(self, iflw_files_dir: Path, output_dir: Path, timestamp: str = None):
        """
        Initialize IFLW Timer Extractor
        
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
        
        logger.info("IflwTimerExtractor initialized")
        logger.info(f"  IFLW files: {self.iflw_files_dir}")
        logger.info(f"  Output: {self.output_dir}")
    
    def extract_all(self, configurations: Dict[str, Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Extract timers from all IFLW files and resolve configurations
        
        Args:
            configurations: Dictionary mapping iflow_id to configuration dict
            
        Returns:
            Dictionary with extraction statistics
        """
        logger.info("Starting IFLW timer extraction...")
        
        stats = {
            "iflw_files_attempted": 0,
            "iflw_files_processed": 0,
            "iflw_files_failed": 0,
            "total_timers_extracted": 0,
            "event_timers": 0,
            "channel_timers": 0
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
        
        # Collect all timers
        all_timers = []
        
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
                
                # Get configurations for this iflow
                iflow_config = configurations.get(iflow_id) if configurations else None
                
                # Extract timers
                timers = IflwTimerAnalyzer.analyze(
                    root=root,
                    iflow_id=iflow_id,
                    package_id=package_id,
                    configurations=iflow_config
                )
                
                # Add to master list
                all_timers.extend(timers)
                
                # Update statistics
                for timer in timers:
                    if timer.type == 'Event':
                        stats["event_timers"] += 1
                    elif timer.type == 'Channel':
                        stats["channel_timers"] += 1
                
                stats["total_timers_extracted"] += len(timers)
                stats["iflw_files_processed"] += 1
                
                if len(timers) > 0:
                    logger.debug(f"  Extracted {len(timers)} timers")
                
            except Exception as e:
                stats["iflw_files_failed"] += 1
                logger.error(f"  Failed to process {iflw_path.name}: {e}")
                self._track_error(iflw_path.name, "EXTRACTION_ERROR", str(e))
        
        # Save output
        self._save_output(all_timers)
        
        # Save error log if there are errors
        if self.errors:
            self._save_error_log()
        
        logger.info(f"IFLW timer extraction completed. Processed {stats['iflw_files_processed']}/{stats['iflw_files_attempted']}")
        logger.info(f"Total timers extracted: {stats['total_timers_extracted']} (Events: {stats['event_timers']}, Channels: {stats['channel_timers']})")
        
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
    
    def _save_output(self, timers: List[IflwTimer]):
        """Save timers to JSON file"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save timers
        output_file = self.output_dir / "iflw-timers.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in timers], f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(timers)} timers to {output_file}")
    
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
        output_file = self.output_dir / "iflw-timer-extraction-errors.json"
        
        output_data = {
            "errors": self.errors,
            "total_errors": len(self.errors)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved timer extraction error log: iflw-timer-extraction-errors.json")