"""
Unit tests for the utils module.
"""

import pytest
from openapi_client_generator.utils import (
    sanitize_python_identifier, sanitize_model_name, to_snake_case, 
    to_pascal_case, get_python_type
)
def test_sanitize_python_identifier():
    """Test sanitizing Python identifiers."""
    # Test Python keywords
    assert sanitize_python_identifier('class') == 'class_'
    assert sanitize_python_identifier('if') == 'if_'
    assert sanitize_python_identifier('for') == 'for_'
    
    # Test identifiers starting with digits
    assert sanitize_python_identifier('123abc') == '_123abc'
    assert sanitize_python_identifier('9test') == '_9test'
    
    # Test valid identifiers
    assert sanitize_python_identifier('valid_name') == 'valid_name'
    assert sanitize_python_identifier('ValidName') == 'ValidName'
    
    # Test empty string
    assert sanitize_python_identifier('') == ''

def test_sanitize_model_name():
    """Test sanitizing model names."""
    # Test names with dots and spaces
    assert sanitize_model_name('User.Data') == 'User_Data'
    assert sanitize_model_name('User Data') == 'User_Data'
    
    # Test names with special characters
    assert sanitize_model_name('User-Model') == 'User_Model'
    assert sanitize_model_name('User@Model') == 'User_Model'
    
    # Test names starting with digits
    assert sanitize_model_name('123Model') == 'Model_123Model'
    
    # Test multiple underscores
    assert sanitize_model_name('User___Model') == 'User_Model'
    
    # Test trailing underscores
    assert sanitize_model_name('User_Model_') == 'User_Model'

def test_to_snake_case():
    """Test converting strings to snake_case."""
    # Test PascalCase
    assert to_snake_case('UserModel') == 'user_model'
    assert to_snake_case('APIClient') == 'api_client'
    
    # Test camelCase
    assert to_snake_case('userModel') == 'user_model'
    assert to_snake_case('apiClient') == 'api_client'
    
    # Test with numbers
    assert to_snake_case('User2Model') == 'user2_model'
    assert to_snake_case('APIv2Client') == 'ap_iv2_client'
    
    # Test with special characters
    assert to_snake_case('user-model') == 'user_model'
    assert to_snake_case('user.model') == 'user_model'
    
    # Test version placeholders
    assert to_snake_case('user{id}model') == 'user_id_model'
    
    # Test empty and invalid names
    assert to_snake_case('') == 'operation'
    assert to_snake_case('123') == 'op_123'

def test_to_pascal_case():
    """Test converting strings to PascalCase."""
    # Test snake_case
    assert to_pascal_case('user_model') == 'UserModel'
    assert to_pascal_case('api_client') == 'ApiClient'
    
    # Test with hyphens
    assert to_pascal_case('user-model') == 'UserModel'
    
    # Test single words
    assert to_pascal_case('user') == 'User'
    assert to_pascal_case('api') == 'Api'
    
    # Test already PascalCase
    assert to_pascal_case('UserModel') == 'Usermodel'

def test_get_python_type():
    """Test getting Python types from OpenAPI/Swagger type definitions."""
    # Test basic types
    assert get_python_type({'type': 'string'}) == 'str'
    assert get_python_type({'type': 'integer'}) == 'int'
    assert get_python_type({'type': 'number'}) == 'float'
    assert get_python_type({'type': 'boolean'}) == 'bool'
    assert get_python_type({'type': 'object'}) == 'Dict[str, Any]'
    
    # Test array types
    assert get_python_type({
        'type': 'array',
        'items': {'type': 'string'}
    }) == 'List[str]'
    assert get_python_type({
        'type': 'array',
        'items': {'type': 'integer'}
    }) == 'List[int]'
    
    # Test nested arrays
    assert get_python_type({
        'type': 'array',
        'items': {
            'type': 'array',
            'items': {'type': 'string'}
        }
    }) == 'List[List[str]]'
    
    # Test unknown types
    assert get_python_type({'type': 'unknown'}) == 'Any'
    
    # Test missing type
    assert get_python_type({}) == 'str'
    
    # Test type with no type field but default
    assert get_python_type({'description': 'Some field'}) == 'str'