"""
Swagger 2.0 specific API generator.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .base_api_generator import BaseAPIGenerator
from .utils import get_python_type, sanitize_model_name


class Swagger20APIGenerator(BaseAPIGenerator):
    """Generates strongly-typed API client classes from Swagger 2.0 specifications."""
    
    def __init__(self, paths: Dict[str, Any], schemas: Dict[str, Any], 
                 service_name: str, output_dir: Path, spec_data: Dict[str, Any]):
        """Initialize the Swagger 2.0 API generator."""
        super().__init__(paths, schemas, service_name, output_dir)
        self.spec_data = spec_data
        
    def _get_request_body_info(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get request body information for Swagger 2.0."""
        parameters = operation.get('parameters', [])
        body_param = self._find_body_parameter(parameters)
        
        if not body_param:
            return None
        
        schema = body_param.get('schema', {})
        required = body_param.get('required', False)
        
        # Determine the type from schema
        if '$ref' in schema:
            # Extract model name from $ref
            ref_path = schema['$ref']
            if ref_path.startswith('#/definitions/'):
                model_name = ref_path.split('/')[-1]
                type_name = sanitize_model_name(model_name)
            else:
                type_name = 'Any'
        elif schema.get('type') == 'array':
            # Handle array type
            items = schema.get('items', {})
            if '$ref' in items:
                item_ref = items['$ref']
                if item_ref.startswith('#/definitions/'):
                    item_model = item_ref.split('/')[-1]
                    item_type = sanitize_model_name(item_model)
                    type_name = f'List[{item_type}]'
                else:
                    type_name = 'List[Any]'
            else:
                item_type = get_python_type(items.get('type', 'string'), items.get('format'))
                type_name = f'List[{item_type}]'
        else:
            # Simple type
            type_name = get_python_type(schema.get('type', 'object'), schema.get('format'))
        
        return {
            'type': type_name,
            'required': required,
            'is_json': True  # Swagger 2.0 typically uses JSON for body
        }
    
    def _get_response_model(self, operation: Dict[str, Any]) -> Optional[str]:
        """Get response model type for Swagger 2.0."""
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
        
        schema = success_response.get('schema')
        if not schema:
            return None
        
        # Handle different schema types
        if '$ref' in schema:
            # Direct model reference
            ref_path = schema['$ref']
            if ref_path.startswith('#/definitions/'):
                model_name = ref_path.split('/')[-1]
                return sanitize_model_name(model_name)
        elif schema.get('type') == 'array':
            # Array response
            items = schema.get('items', {})
            if '$ref' in items:
                item_ref = items['$ref']
                if item_ref.startswith('#/definitions/'):
                    item_model = item_ref.split('/')[-1]
                    item_type = sanitize_model_name(item_model)
                    return f'List[{item_type}]'
                else:
                    return 'List[Any]'
            else:
                item_type = get_python_type(items.get('type', 'string'), items.get('format'))
                return f'List[{item_type}]'
        elif schema.get('type'):
            # Simple type response
            return get_python_type(schema.get('type'), schema.get('format'))
        
        return None
    
    def _get_content_types(self, operation: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Get consumes and produces content types for Swagger 2.0."""
        # In Swagger 2.0, consumes and produces can be at operation level or global level
        consumes = operation.get('consumes', self.spec_data.get('consumes', []))
        produces = operation.get('produces', self.spec_data.get('produces', []))
        
        return consumes, produces
    
    def _get_parameter_type(self, param: Dict[str, Any]) -> str:
        """Get the Python type for a Swagger 2.0 parameter."""
        param_type = param.get('type', 'string')
        param_format = param.get('format')
        
        # Handle array types
        if param_type == 'array':
            items = param.get('items', {})
            item_type = items.get('type', 'string')
            item_format = items.get('format')
            return f"List[{get_python_type(item_type, item_format)}]"
        
        # Handle file type (specific to Swagger 2.0)
        if param_type == 'file':
            return 'Any'  # File uploads are typically handled as binary data
        
        return get_python_type(param_type, param_format)
    
    def _generate_imports(self) -> str:
        """Generate import statements for Swagger 2.0."""
        model_imports = self._generate_model_imports()
        base_imports = """import requests
import logging
from typing import Optional, Dict, Any, Union, List"""
        
        if model_imports:
            return f"{base_imports}\n{model_imports}"
        return base_imports
    
    def _generate_init_method(self) -> str:
        """Generate the __init__ method for Swagger 2.0 client."""
        # Get base URL from spec if available
        host = self.spec_data.get('host', '')
        base_path = self.spec_data.get('basePath', '')
        schemes = self.spec_data.get('schemes', ['https'])
        
        default_url = ""
        if host:
            scheme = schemes[0] if schemes else 'https'
            default_url = f"{scheme}://{host}{base_path}"
        
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