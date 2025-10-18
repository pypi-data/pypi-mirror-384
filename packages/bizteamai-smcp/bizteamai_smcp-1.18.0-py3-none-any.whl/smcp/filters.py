"""
Input filtering and sanitization for prompts and parameters.
"""

import re
from typing import Any, Dict, Union


class InputValidationError(Exception):
    """Raised when input fails validation."""
    pass


def sanitize_prompt(prompt: str, cfg: Dict[str, Union[str, int]]) -> None:
    """
    Sanitize and validate prompt input against configured rules.
    
    Args:
        prompt: The prompt text to validate
        cfg: Configuration dictionary containing validation rules
        
    Raises:
        InputValidationError: If the prompt fails validation
    """
    # Length validation
    max_len = cfg.get("MAX_LEN")
    if max_len and len(prompt) > max_len:
        raise InputValidationError(f"Prompt exceeds maximum length of {max_len}")
    
    # Pattern validation
    safe_re = cfg.get("SAFE_RE")
    if safe_re:
        if not re.match(safe_re, prompt, re.DOTALL):
            raise InputValidationError("Prompt contains invalid characters or patterns")
    
    # Blocked patterns check
    blocked_patterns = cfg.get("BLOCKED_PATTERNS", [])
    for pattern in blocked_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise InputValidationError(f"Prompt contains blocked pattern")


def sanitize_parameter(param_name: str, param_value: Any, cfg: Dict[str, Any]) -> Any:
    """
    Sanitize and validate a function parameter.
    
    Args:
        param_name: Name of the parameter
        param_value: Value of the parameter
        cfg: Configuration dictionary containing validation rules
        
    Returns:
        Sanitized parameter value
        
    Raises:
        InputValidationError: If the parameter fails validation
    """
    # String parameter validation
    if isinstance(param_value, str):
        _validate_string_parameter(param_name, param_value, cfg)
    
    # Numeric parameter validation
    elif isinstance(param_value, (int, float)):
        _validate_numeric_parameter(param_name, param_value, cfg)
    
    # List parameter validation
    elif isinstance(param_value, list):
        _validate_list_parameter(param_name, param_value, cfg)
    
    return param_value


def _validate_string_parameter(param_name: str, value: str, cfg: Dict[str, Any]) -> None:
    """Validate string parameters."""
    param_rules = cfg.get("PARAM_RULES", {}).get(param_name, {})
    
    # Length validation
    max_len = param_rules.get("max_length", cfg.get("MAX_PARAM_LEN"))
    if max_len and len(value) > max_len:
        raise InputValidationError(f"Parameter '{param_name}' exceeds maximum length")
    
    # Pattern validation
    pattern = param_rules.get("pattern", cfg.get("PARAM_SAFE_RE"))
    if pattern and not re.match(pattern, value):
        raise InputValidationError(f"Parameter '{param_name}' contains invalid characters")
    
    # Blocked content check
    blocked = param_rules.get("blocked", cfg.get("BLOCKED_PARAM_PATTERNS", []))
    for block_pattern in blocked:
        if re.search(block_pattern, value, re.IGNORECASE):
            raise InputValidationError(f"Parameter '{param_name}' contains blocked content")


def _validate_numeric_parameter(param_name: str, value: Union[int, float], cfg: Dict[str, Any]) -> None:
    """Validate numeric parameters."""
    param_rules = cfg.get("PARAM_RULES", {}).get(param_name, {})
    
    # Range validation
    min_val = param_rules.get("min_value")
    max_val = param_rules.get("max_value")
    
    if min_val is not None and value < min_val:
        raise InputValidationError(f"Parameter '{param_name}' below minimum value {min_val}")
    
    if max_val is not None and value > max_val:
        raise InputValidationError(f"Parameter '{param_name}' exceeds maximum value {max_val}")


def _validate_list_parameter(param_name: str, value: list, cfg: Dict[str, Any]) -> None:
    """Validate list parameters."""
    param_rules = cfg.get("PARAM_RULES", {}).get(param_name, {})
    
    # Length validation
    max_items = param_rules.get("max_items", cfg.get("MAX_LIST_ITEMS"))
    if max_items and len(value) > max_items:
        raise InputValidationError(f"Parameter '{param_name}' has too many items")
    
    # Validate each item in the list
    for i, item in enumerate(value):
        try:
            if isinstance(item, str):
                _validate_string_parameter(f"{param_name}[{i}]", item, cfg)
            elif isinstance(item, (int, float)):
                _validate_numeric_parameter(f"{param_name}[{i}]", item, cfg)
        except InputValidationError as e:
            raise InputValidationError(f"List item validation failed: {e}")


def create_safe_regex(allowed_chars: str = None) -> str:
    """
    Create a safe regex pattern for input validation.
    
    Args:
        allowed_chars: Additional characters to allow beyond basic alphanumeric
        
    Returns:
        Regex pattern string for safe input validation
    """
    base_chars = r"\w\s"  # alphanumeric and whitespace
    
    if allowed_chars:
        # Escape special regex characters
        escaped_chars = re.escape(allowed_chars)
        base_chars += escaped_chars
    
    return f"^[{base_chars}]*$"


def strip_dangerous_content(text: str, cfg: Dict[str, Any]) -> str:
    """
    Strip potentially dangerous content from text.
    
    Args:
        text: Text to sanitize
        cfg: Configuration dictionary
        
    Returns:
        Sanitized text with dangerous content removed
    """
    # Remove common injection patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'data:',                     # Data URLs
        r'vbscript:',                 # VBScript URLs
    ]
    
    # Add custom dangerous patterns from config
    custom_patterns = cfg.get("DANGEROUS_PATTERNS", [])
    dangerous_patterns.extend(custom_patterns)
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized
