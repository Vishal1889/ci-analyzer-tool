"""
BPMN Process Activity Resolver for SAP Cloud Integration Analyzer Tool
Resolves configuration placeholders in BPMN activity properties
"""

import re
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BpmnProcessActivityResolver:
    """
    Resolves configuration placeholders in strings.
    Placeholder format: {{key}}
    """
    
    # Regex pattern to find {{placeholder}} patterns
    PLACEHOLDER_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    @staticmethod
    def resolveOnePass(input_str: Optional[str], cfg: Dict[str, str]) -> Optional[str]:
        """
        Resolve configuration placeholders in a string (single pass).
        
        Resolution rules:
        1. If input is None → return None
        2. If input contains no "{{" → return input unchanged
        3. For each {{key}} placeholder:
           - If cfg[key] exists and is non-empty → replace with cfg[key]
           - Otherwise → keep {{key}} unchanged
        4. Return resolved string
        
        Args:
            input_str: Input string that may contain {{placeholder}} patterns
            cfg: Configuration dictionary with key-value pairs
            
        Returns:
            Resolved string with placeholders replaced where possible, or None if input was None
            
        Examples:
            >>> resolveOnePass(None, {}) 
            None
            
            >>> resolveOnePass("", {})
            ""
            
            >>> resolveOnePass("no placeholders", {})
            "no placeholders"
            
            >>> resolveOnePass("{{key}}", {"key": "value"})
            "value"
            
            >>> resolveOnePass("{{key}}", {"key": ""})
            "{{key}}"
            
            >>> resolveOnePass("{{key}}", {})
            "{{key}}"
            
            >>> resolveOnePass("prefix {{key}} suffix", {"key": "value"})
            "prefix value suffix"
        """
        # Rule 1: If input is None, return None
        if input_str is None:
            return None
        
        # Rule 2: If no placeholders, return unchanged
        if '{{' not in input_str:
            return input_str
        
        # Rule 3: Process each placeholder
        def replace_placeholder(match):
            key = match.group(1).strip()  # Extract key from {{key}}
            
            # Check if config has the key and value is non-empty
            if key in cfg and cfg[key]:
                replacement = cfg[key]
                logger.trace(f"Resolved placeholder {{{{{{key}}}}}} → '{replacement}'")
                return replacement
            else:
                # Keep placeholder unchanged
                logger.trace(f"Placeholder {{{{{{key}}}}}} not resolved (key not found or empty)")
                return match.group(0)  # Return original {{key}}
        
        # Replace all placeholders
        resolved = BpmnProcessActivityResolver.PLACEHOLDER_PATTERN.sub(
            replace_placeholder, 
            input_str
        )
        
        return resolved
    
    @staticmethod
    def resolveConfigToProperties(items: list, cfg: Dict[str, str], 
                                  value_field: str = 'rowValue',
                                  default_field: str = 'rowDefault') -> list:
        """
        Resolve configuration placeholders for a list of items.
        
        For each item, resolves:
        - item[value_field] → item[value_field + 'Resolved']
        - item[default_field] → item[default_field + 'Resolved']
        
        Args:
            items: List of items (dicts or objects) to resolve
            cfg: Configuration dictionary
            value_field: Name of the value field to resolve
            default_field: Name of the default field to resolve
            
        Returns:
            The same list with resolved fields added
        """
        for item in items:
            # Handle both dict and object attribute access
            if isinstance(item, dict):
                value = item.get(value_field)
                default = item.get(default_field)
                
                item[value_field + 'Resolved'] = BpmnProcessActivityResolver.resolveOnePass(value, cfg)
                item[default_field + 'Resolved'] = BpmnProcessActivityResolver.resolveOnePass(default, cfg)
            else:
                # Object attribute access
                value = getattr(item, value_field, None)
                default = getattr(item, default_field, None)
                
                setattr(item, value_field + '_resolved', 
                       BpmnProcessActivityResolver.resolveOnePass(value, cfg))
                setattr(item, default_field + '_resolved',
                       BpmnProcessActivityResolver.resolveOnePass(default, cfg))
        
        return items