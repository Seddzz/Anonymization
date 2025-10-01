"""
Generic helper functions for the anonymization system.
"""

import os
import re
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime


def generate_unique_id() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def hash_string(text: str) -> str:
    """Create a hash of a string for consistent anonymization."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for file systems."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    # Ensure it's not empty
    if not filename:
        filename = f"file_{generate_unique_id()[:8]}"
    return filename


def ensure_directory(path: str) -> None:
    """Ensure a directory exists, create if it doesn't."""
    os.makedirs(path, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return os.path.splitext(filename)[1].lower()


def is_text_file(filename: str) -> bool:
    """Check if a file is a text file based on extension."""
    text_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm'}
    return get_file_extension(filename) in text_extensions


def is_document_file(filename: str) -> bool:
    """Check if a file is a document file that can be processed."""
    doc_extensions = {'.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt'}
    return get_file_extension(filename) in doc_extensions


def format_bytes(size: int) -> str:
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing."""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    return text.strip()


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text."""
    # Simple phone number patterns
    phone_patterns = [
        r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # (123) 456-7890
        r'\b\d{3}\.\d{3}\.\d{4}\b',  # 123.456.7890
        r'\b\d{10}\b'  # 1234567890
    ]
    
    phone_numbers = []
    for pattern in phone_patterns:
        phone_numbers.extend(re.findall(pattern, text))
    
    return phone_numbers


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """Validate that a configuration dictionary has all required keys."""
    return all(key in config for key in required_keys)


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, with dict2 values taking precedence."""
    result = dict1.copy()
    result.update(dict2)
    return result


def timestamp() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary with a default."""
    return dictionary.get(key, default)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """Flatten a nested list into a single list."""
    return [item for sublist in nested_list for item in sublist]


def extract_valid_entities(parsed_entities: List[Dict], entity_types: List[str] = None) -> List[Dict]:
    """
    Extract and validate entities against allowed types.
    
    Args:
        parsed_entities: Raw parsed entities
        entity_types: Valid entity types. If None, uses default entity types.
    
    Returns:
        List of validated entities
    """
    # Ensure all entities are dictionaries
    if not all(isinstance(entity, dict) for entity in parsed_entities):
        print(f"[ERROR] Invalid entities detected: {parsed_entities}")
        parsed_entities = [entity for entity in parsed_entities if isinstance(entity, dict)]

    if entity_types is None:
        entity_types = ['PERSON', 'ORG', 'GPE', 'LOC', 'MISC', 'NORP', 'FAC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']
    
    valid_labels = entity_types + ['ORG']  # ORG is alias for ORGANIZATION
    valid_entities = []
    
    for entity in parsed_entities:
        raw_label = entity.get("label", "").strip()
        text = entity.get("text", "").strip()
        
        # Handle multi-labels (e.g., "PERSON|AGE")
        labels = [lbl for lbl in raw_label.split("|") if lbl in valid_labels]
        
        if not labels:
            print(f"❌ Invalid label: {raw_label}")
            continue
        
        # Create entity for each valid label
        for label in labels:
            valid_entity = {"text": text, "label": label}
            
            # Preserve position info if present
            if "start" in entity:
                valid_entity["start"] = entity["start"]
            if "end" in entity:
                valid_entity["end"] = entity["end"]
            
            valid_entities.append(valid_entity)
    
    return valid_entities