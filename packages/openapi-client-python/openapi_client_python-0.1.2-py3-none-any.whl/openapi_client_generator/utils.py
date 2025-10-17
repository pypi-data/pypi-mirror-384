"""
Utility functions for the OpenAPI client generator.
"""

import re
import keyword
from typing import Dict, Any


def sanitize_python_identifier(name: str) -> str:
    """Sanitize identifier to avoid Python keywords and invalid names."""
    # If it's a Python keyword, append underscore
    if keyword.iskeyword(name):
        return f"{name}_"
    
    # If it starts with a digit, prepend underscore
    if name and name[0].isdigit():
        return f"_{name}"
    
    return name


def sanitize_model_name(model_name: str) -> str:
    """Sanitize model name to be a valid Python identifier."""
    # Replace dots, spaces, and other invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', model_name)
    # Ensure it doesn't start with a digit
    if sanitized[0].isdigit():
        sanitized = f"Model_{sanitized}"
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def to_snake_case(name: str) -> str:
    """Convert string to snake_case."""
    # Sanitize invalid characters
    sanitized = re.sub(r'[^a-zA-Z0-9_{}]', '_', name)
    
    # Convert version placeholders {id} to _id_
    sanitized = re.sub(r'\{([^}]+)\}', r'_\1_', sanitized)
    
    # Clean up patterns
    sanitized = re.sub(r'_api_v\d*_', '_', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    
    # Handle camelCase and PascalCase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', sanitized)
    result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    # Final cleanup
    result = re.sub(r'_+', '_', result).strip('_')
    
    # Ensure valid identifier
    if result and result[0].isdigit():
        result = f"op_{result}"
    
    if not result:
        result = "operation"
        
    return result


def to_pascal_case(name: str) -> str:
    """Convert string to PascalCase."""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


def get_python_type(type_def, format_str=None) -> str:
    """Convert OpenAPI/Swagger type to Python type."""
    # Handle backward compatibility - if called with (type_str, format_str)
    if isinstance(type_def, str):
        type_str = type_def
        format_val = format_str
        type_def_dict = {'type': type_str, 'format': format_val}
    else:
        # Original behavior - type_def is a dictionary
        type_def_dict = type_def
        type_str = type_def.get('type')
        format_val = type_def.get('format')
    
    type_mapping = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'array': 'List',
        'object': 'Dict[str, Any]',
        'file': 'Any'  # For Swagger 2.0 file type
    }
    
    if type_str == 'array':
        items = type_def_dict.get('items', {})
        item_type = get_python_type(items)
        return f"List[{item_type}]"
    elif type_str in type_mapping:
        return type_mapping[type_str]
    elif type_str is None:
        return 'str'  # Default to str when no type is specified
    else:
        return 'Any'