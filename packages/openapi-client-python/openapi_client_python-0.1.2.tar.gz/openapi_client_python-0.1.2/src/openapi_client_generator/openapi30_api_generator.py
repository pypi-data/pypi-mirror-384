"""
OpenAPI 3.0+ specific API generator.
Supports OpenAPI 3.0.x, 3.1.x, and 3.2.x specifications.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .base_api_generator import BaseAPIGenerator
from .utils import get_python_type, sanitize_model_name


class OpenAPI30APIGenerator(BaseAPIGenerator):
    """Generates strongly-typed API client classes from OpenAPI 3.0+ specifications."""
    
    def __init__(self, paths: Dict[str, Any], schemas: Dict[str, Any], 
                 service_name: str, output_dir: Path, spec_data: Dict[str, Any]):
        """Initialize the OpenAPI 3.0+ API generator."""
        super().__init__(paths, schemas, service_name, output_dir)
        self.spec_data = spec_data
        self.version_info = None  # Will be set by the main generator
        
    def _supports_feature(self, feature: str) -> bool:
        """Check if the current OpenAPI version supports a specific feature."""
        if not self.version_info:
            return False
            
        feature_support = {
            'webhooks': self.version_info.get('supports_webhooks', False),
            'json_schema_draft_2020_12': self.version_info.get('supports_json_schema_draft_2020_12', False),
            'discriminator_mapping': self.version_info.get('supports_discriminator_mapping', False),
            'const_keyword': self.version_info.get('version_family') in ['openapi31', 'openapi32'],
            'unevaluated_properties': self.version_info.get('version_family') in ['openapi31', 'openapi32']
        }
        
        return feature_support.get(feature, False)
        
    def _get_request_body_info(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get request body information for OpenAPI 3.0."""
        request_body = operation.get('requestBody')
        if not request_body:
            return None
        
        required = request_body.get('required', False)
        content = request_body.get('content', {})
        
        # Try to get JSON content first, then fallback to others
        content_type_keys = list(content.keys())
        preferred_content_types = ['application/json', 'application/xml', 'text/plain']
        
        schema = None
        is_json = True
        
        # Look for preferred content types first
        for content_type in preferred_content_types:
            if content_type in content:
                schema = content[content_type].get('schema')
                is_json = content_type == 'application/json'
                break
        
        # If no preferred type found, use the first available
        if not schema and content_type_keys:
            first_content_type = content_type_keys[0]
            schema = content[first_content_type].get('schema')
            is_json = 'json' in first_content_type.lower()
        
        if not schema:
            return {
                'type': 'Any',
                'required': required,
                'is_json': is_json
            }
        
        # Determine the type from schema
        type_name = self._resolve_schema_type(schema)
        
        return {
            'type': type_name,
            'required': required,
            'is_json': is_json
        }
    
    def _get_response_model(self, operation: Dict[str, Any]) -> Optional[str]:
        """Get response model type for OpenAPI 3.0."""
        responses = operation.get('responses', {})
        
        # Look for successful response (200, 201, etc.)
        success_response = None
        for status_code, response in responses.items():
            if isinstance(status_code, str) and status_code.startswith('2'):
                success_response = response
                break
            elif isinstance(status_code, int) and 200 <= status_code < 300:
                success_response = response
                break
        
        if not success_response:
            return None
        
        content = success_response.get('content', {})
        if not content:
            return None
        
        # Try to get JSON content first, then others
        schema = None
        content_type_keys = list(content.keys())
        preferred_content_types = ['application/json', 'application/xml', 'text/plain']
        
        for content_type in preferred_content_types:
            if content_type in content:
                schema = content[content_type].get('schema')
                break
        
        if not schema and content_type_keys:
            first_content_type = content_type_keys[0]
            schema = content[first_content_type].get('schema')
        
        if not schema:
            return None
        
        return self._resolve_schema_type(schema)
    
    def _resolve_schema_type(self, schema: Dict[str, Any]) -> str:
        """Resolve schema to Python type for OpenAPI 3.0+."""
        # Handle $ref
        if '$ref' in schema:
            ref_path = schema['$ref']
            if ref_path.startswith('#/components/schemas/'):
                model_name = ref_path.split('/')[-1]
                return sanitize_model_name(model_name)
            else:
                return 'Any'
        
        # Handle const keyword (OpenAPI 3.1+)
        if 'const' in schema and self._supports_feature('const_keyword'):
            const_value = schema['const']
            if isinstance(const_value, str):
                return 'str'
            elif isinstance(const_value, (int, float)):
                return 'Union[int, float]'
            elif isinstance(const_value, bool):
                return 'bool'
            else:
                return 'Any'
        
        # Handle array type
        if schema.get('type') == 'array':
            items = schema.get('items', {})
            item_type = self._resolve_schema_type(items)
            return f'List[{item_type}]'
        
        # Handle object with properties (inline schema)
        if schema.get('type') == 'object' and 'properties' in schema:
            return 'Dict[str, Any]'
        
        # Handle oneOf, anyOf, allOf with enhanced support
        if 'oneOf' in schema or 'anyOf' in schema:
            # For union types, we could be more sophisticated in OpenAPI 3.1+
            if self._supports_feature('json_schema_draft_2020_12'):
                # Could implement more advanced union type detection
                return 'Any'
            return 'Any'
        
        if 'allOf' in schema:
            # For allOf, try to resolve the first schema that has a $ref
            for sub_schema in schema['allOf']:
                if '$ref' in sub_schema:
                    return self._resolve_schema_type(sub_schema)
            return 'Any'
        
        # Handle simple types
        schema_type = schema.get('type', 'object')
        schema_format = schema.get('format')
        
        return get_python_type(schema_type, schema_format)
    
    def _get_content_types(self, operation: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Get consumes and produces content types for OpenAPI 3.0."""
        consumes = []
        produces = []
        
        # Extract from requestBody
        request_body = operation.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            consumes = list(content.keys())
        
        # Extract from responses
        responses = operation.get('responses', {})
        for response in responses.values():
            if isinstance(response, dict):
                content = response.get('content', {})
                produces.extend(content.keys())
        
        # Remove duplicates while preserving order
        produces = list(dict.fromkeys(produces))
        
        return consumes, produces
    
    def _get_parameter_type(self, param: Dict[str, Any]) -> str:
        """Get the Python type for an OpenAPI 3.0 parameter."""
        schema = param.get('schema', {})
        
        # Handle array types
        if schema.get('type') == 'array':
            items = schema.get('items', {})
            item_type = self._resolve_schema_type(items)
            return f"List[{item_type}]"
        
        return self._resolve_schema_type(schema)
    
    def _generate_imports(self) -> str:
        """Generate import statements for OpenAPI 3.0."""
        model_imports = self._generate_model_imports()
        base_imports = """import requests
import logging
from typing import Optional, Dict, Any, Union, List"""
        
        if model_imports:
            return f"{base_imports}\n{model_imports}"
        return base_imports
    
    def _generate_init_method(self) -> str:
        """Generate the __init__ method for OpenAPI 3.0 client."""
        # Get base URL from servers if available
        servers = self.spec_data.get('servers', [])
        default_url = ""
        if servers:
            default_url = servers[0].get('url', '')
        
        return f'''    
    def __init__(self, base_url: str = None, auth_token: str = None, tenant: str = None):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the API service (default: {default_url or "not specified"})
            auth_token: Authentication token for API requests
            tenant: Tenant ID for multi-tenant APIs
        """
        self.logger = logging.getLogger(__name__)
        self._tenant = tenant or ""
        self._base_url = base_url or "{default_url}"
        self._headers = {{
            "Content-Type": "application/json",
            "User-Agent": f"GeneratedApiClient/{self.service_name}",
        }}
        
        if auth_token:
            self.set_auth_token(auth_token)'''