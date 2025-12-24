"""Input validation utilities."""

import re
from typing import Dict, Any, Optional, Tuple


def validate_email(email: str) -> bool:
    """
    Basic email format validation.
    
    Args:
        email: Email string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets requirements (min 6 characters).
    
    Args:
        password: Password string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, None


def validate_note_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate note creation/update data.
    
    Args:
        data: Note data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Title is required
    if 'title' not in data or not data['title']:
        return False, "Title is required"
    
    if not isinstance(data['title'], str):
        return False, "Title must be a string"
    
    # Content is optional, but if provided must be string
    if 'content' in data and data['content'] is not None:
        if not isinstance(data['content'], str):
            return False, "Content must be a string"
    
    # Note date is required and must be a number (timestamp)
    if 'note_date' not in data:
        return False, "note_date is required"
    
    if not isinstance(data['note_date'], (int, float)):
        return False, "note_date must be a number (timestamp)"
    
    # Attachment key is optional, but if provided must be string
    if 'attachment_key' in data and data['attachment_key'] is not None:
        if not isinstance(data['attachment_key'], str):
            return False, "attachment_key must be a string"
    
    return True, None


def validate_timestamp(timestamp: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate timestamp is a valid number.
    
    Args:
        timestamp: Timestamp value to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if timestamp is None:
        return False, "Timestamp is required"
    
    if not isinstance(timestamp, (int, float)):
        return False, "Timestamp must be a number"
    
    # Check if timestamp is reasonable (not negative, not too large)
    if timestamp < 0:
        return False, "Timestamp cannot be negative"
    
    # Check if timestamp is not too far in the future (e.g., year 2100)
    max_timestamp = 4102444800  # Jan 1, 2100
    if timestamp > max_timestamp:
        return False, "Timestamp is too far in the future"
    
    return True, None


def validate_file_type(content_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file type is an image.
    
    Args:
        content_type: MIME content type string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content_type or not isinstance(content_type, str):
        return False, "Content type is required"
    
    # Check if content type starts with 'image/'
    if not content_type.startswith('image/'):
        return False, "Only image files are allowed"
    
    # Common image MIME types
    allowed_types = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/bmp',
        'image/svg+xml'
    ]
    
    if content_type.lower() not in [t.lower() for t in allowed_types]:
        return False, f"Image type {content_type} is not supported"
    
    return True, None


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename is safe and has valid extension.
    
    Args:
        filename: Filename string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename or not isinstance(filename, str):
        return False, "Filename is required"
    
    # Check for valid image extensions
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    filename_lower = filename.lower()
    
    has_valid_extension = any(filename_lower.endswith(ext) for ext in valid_extensions)
    
    if not has_valid_extension:
        return False, "Filename must have a valid image extension (.jpg, .jpeg, .png, .gif, .webp, .bmp, .svg)"
    
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00']
    if any(char in filename for char in dangerous_chars):
        return False, "Filename contains invalid characters"
    
    return True, None

