"""
Filename sanitizer utility for safe file creation on Windows/macOS/Linux.
Handles illegal characters and path length limits.
"""

import hashlib
import re
from pathlib import Path

# Characters illegal in Windows filenames
_ILLEGAL_CHARS = re.compile(r'[\\/:*?"<>|;&]')


def sanitize_chars(name: str) -> str:
    """Replace illegal Windows filename characters with underscore.

    Safe for all file types — only replaces characters, never truncates.
    """
    return _ILLEGAL_CHARS.sub('_', name)


def sanitize_source_name(name: str, max_length: int = 80) -> str:
    """Sanitize the source_name portion of an extracted filename.

    - Replaces illegal Windows characters with _
    - Truncates to max_length, preserving the file extension
    - Appends a short hash when truncated for uniqueness

    Use this ONLY for schema/mapping files (.edmx, .wsdl, .xsd, .mmap, .xml, .json)
    that are NOT parsed downstream.

    For script files (.groovy, .js, .xsl) use sanitize_chars() instead
    since the environment variable scanner stores the filename in output.
    """
    # Replace illegal characters first
    sanitized = _ILLEGAL_CHARS.sub('_', name)

    if len(sanitized) <= max_length:
        return sanitized

    # Truncate preserving extension + append short hash for uniqueness
    ext = Path(sanitized).suffix  # e.g., '.edmx'
    name_hash = hashlib.md5(name.encode()).hexdigest()[:6]
    max_stem = max_length - len(ext) - 1 - len(name_hash)  # -1 for underscore
    stem = Path(sanitized).stem[:max_stem]

    return f"{stem}_{name_hash}{ext}"
