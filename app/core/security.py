import re
from typing import Optional

def sanitize_text(text: Optional[str], max_length: int = 1000) -> str:
    """
    Sanitize user-provided text to prevent injection attacks.
    
    Args:
        text: The input text to sanitize.
        max_length: The maximum allowed length for the text.
        
    Returns:
        A sanitized string.
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^<]+?>', '', text)
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Truncate to max_length
    return text[:max_length]

def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe and doesn't contain path traversal characters.
    
    Args:
        filename: The filename to check.
        
    Returns:
        True if the filename is safe, False otherwise.
    """
    if not filename:
        return False
    
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
        
    return True
