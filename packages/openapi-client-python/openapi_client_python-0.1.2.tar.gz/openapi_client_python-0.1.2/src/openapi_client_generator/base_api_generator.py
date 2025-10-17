"""
Base API generator with common functionality for both Swagger 2.0 and OpenAPI 3.0.
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .utils import sanitize_model_name, to_snake_case, to_pascal_case, get_python_type


class BaseAPIGenerator(ABC):
    """Base class for generating strongly-typed API client classes."""
    
    def __init__(self, paths: Dict[str, Any], schemas: Dict[str, Any], 
                 service_name: str, output_dir: Path):
        """Initialize the base API generator."""
        self.paths = paths
        self.schemas = schemas
        self.service_name = service_name
        self.output_dir = output_dir
        
    def generate_api_client(self):
        """Generate the main API client class."""
        class_name = f"{to_pascal_case(self.service_name)}APIs"
        file_path = self.output_dir / f"{class_name}.py"
        
        # Extract operations from spec
        operations = self._extract_operations()
        
        content = self._generate_apis_content(class_name, operations)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _extract_operations(self) -> List[Dict[str, Any]]:
        """Extract API operations from the specification."""
        operations = []
        
        for path, path_item in self.paths.items():
            for method, operation in path_item.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    operations.append({
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId', f"{method}_{path.replace('/', '_')}"),
                        'parameters': operation.get('parameters', []),
                        'operation': operation,
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                    })
        
        return operations
    
    @abstractmethod
    def _get_request_body_info(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get request body information (version-specific)."""
        pass
    
    @abstractmethod
    def _get_response_model(self, operation: Dict[str, Any]) -> Optional[str]:
        """Get response model type (version-specific)."""
        pass
    
    @abstractmethod
    def _get_content_types(self, operation: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Get consumes and produces content types (version-specific)."""
        pass
    
    def _generate_apis_content(self, class_name: str, operations: List[Dict[str, Any]]) -> str:
        """Generate the complete API client class content."""
        imports = self._generate_imports()
        class_definition = self._generate_class_definition(class_name)
        init_method = self._generate_init_method()
        utility_methods = self._generate_utility_methods()
        api_methods = []
        
        for operation in operations:
            api_methods.append(self._generate_api_method(operation))
        
        content = f"""{imports}

{class_definition}
{init_method}
{utility_methods}

{chr(10).join(api_methods)}"""
        
        return content
    
    def _generate_imports(self) -> str:
        """Generate import statements."""
        model_imports = self._generate_model_imports()
        base_imports = """import requests
import logging
from typing import Optional, Dict, Any, Union, List"""
        
        if model_imports:
            return f"{base_imports}\n{model_imports}"
        return base_imports
    
    def _generate_model_imports(self) -> str:
        """Generate model import statements."""
        if not self.schemas:
            return ""
        
        imports = []
        for model_name in self.schemas.keys():
            clean_name = sanitize_model_name(model_name)
            imports.append(f"from .models.{clean_name} import {clean_name}")
        
        return '\n'.join(imports)
    
    def _generate_class_definition(self, class_name: str) -> str:
        """Generate class definition with docstring."""
        return f'''class {class_name}:
    """
    Strongly-typed API client for {self.service_name}
    
    This class provides methods to interact with the {self.service_name} API endpoints.
    All methods are strongly-typed with automatic model serialization/deserialization.
    """'''
    
    def _generate_init_method(self) -> str:
        """Generate the __init__ method."""
        return '''    
    def __init__(self, base_url: str = None, auth_token: str = None, tenant: str = None):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the API service
            auth_token: Authentication token for API requests
            tenant: Tenant ID for multi-tenant APIs
        """
        self.logger = logging.getLogger(__name__)
        self._tenant = tenant or ""
        self._base_url = base_url or ""
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": f"GeneratedApiClient/{self.service_name}",
        }
        
        if auth_token:
            self.set_auth_token(auth_token)'''
    
    def _generate_utility_methods(self) -> str:
        """Generate utility methods for the API client."""
        return '''    
    def set_base_url(self, base_url: str):
        """Set the base URL for API requests"""
        self._base_url = base_url.rstrip('/')
        self.logger.info(f"Base URL set to: {self._base_url}")
    
    def set_tenant(self, tenant: str):
        """Set the tenant ID"""
        self._tenant = tenant
        self.logger.info(f"Tenant set to: {tenant}")
    
    def get_tenant(self) -> str:
        """Get the current tenant ID"""
        return self._tenant
    
    def set_auth_token(self, token: str):
        """Set the authentication token"""
        self._headers["Authorization"] = f"Bearer {token}"
        self.logger.info("Authentication token updated")
    
    def get_headers(self) -> Dict[str, str]:
        """Get the current headers"""
        return self._headers.copy()
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with error handling and logging
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response: The response object
            
        Raises:
            requests.exceptions.RequestException: For request errors
        """
        try:
            self.logger.debug(f"Making {method} request to: {url}")
            
            # Ensure headers are included
            if 'headers' not in kwargs:
                kwargs['headers'] = self.get_headers()
            
            response = requests.request(method, url, **kwargs)
            
            # Log response details
            self.logger.debug(f"Response status: {response.status_code}")
            
            if not response.ok:
                self.logger.error(f"Request failed: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise'''
    
    def _generate_method_name(self, operation: Dict[str, Any]) -> str:
        """Generate a method name for the operation."""
        operation_id = operation.get('operation_id', '')
        path = operation.get('path', '')
        method = operation.get('method', '').lower()
        
        if operation_id:
            method_name = to_snake_case(operation_id)
        else:
            # Generate from path and method
            path_parts = [part for part in path.split('/') if part and not part.startswith('{')]
            if len(path_parts) == 1:
                method_name = f"{method}_{path_parts[0]}"
            else:
                method_name = f"{method}_" + "_".join(path_parts)
        
        return to_snake_case(method_name)
    
    def _generate_api_method(self, operation: Dict[str, Any]) -> str:
        """Generate a single strongly-typed API method."""
        method_name = self._generate_method_name(operation)
        path = operation['path']
        http_method = operation['method']
        parameters = operation['parameters']
        operation_data = operation['operation']
        
        # Extract different parameter types
        path_params = [p for p in parameters if p.get('in') == 'path']
        query_params = [p for p in parameters if p.get('in') == 'query']
        header_params = [p for p in parameters if p.get('in') == 'header']
        cookie_params = [p for p in parameters if p.get('in') == 'cookie']
        
        # Get request body information
        request_body_info = self._get_request_body_info(operation_data)
        
        # Get response model
        response_model = self._get_response_model(operation_data)
        
        # Generate method signature
        signature_parts = [f"self"]
        
        # Add path parameters
        for param in path_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            signature_parts.append(f"{param_name}: {param_type}")
        
        # Add header parameters
        for param in header_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required = param.get('required', False)
            if required:
                signature_parts.append(f"{param_name}: {param_type}")
            else:
                signature_parts.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Add query parameters
        for param in query_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required = param.get('required', False)
            if required:
                signature_parts.append(f"{param_name}: {param_type}")
            else:
                signature_parts.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Add cookie parameters
        for param in cookie_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required = param.get('required', False)
            if required:
                signature_parts.append(f"{param_name}: {param_type}")
            else:
                signature_parts.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Add request body parameter
        if request_body_info:
            body_type = request_body_info.get('type', 'Any')
            body_required = request_body_info.get('required', True)
            if body_required:
                signature_parts.append(f"payload: {body_type}")
            else:
                signature_parts.append(f"payload: {body_type} = None")
        
        # Determine return type
        return_type = response_model if response_model else "requests.Response"
        
        signature = f"def {method_name}({', '.join(signature_parts)}) -> {return_type}:"
        
        # Generate method body
        operation_summary = operation_data.get('summary', f"{operation_data.get('operationId', method_name)} operation")
        
        # Replace path parameters with snake_case variables
        formatted_path = path
        for param in path_params:
            original_name = param['name']
            snake_case_name = to_snake_case(original_name)
            formatted_path = formatted_path.replace(f'{{{original_name}}}', f'{{{snake_case_name}}}')
        
        url_line = f'url = f"{{self._base_url}}{formatted_path}"'
        
        body_lines = [
            f'        """{operation_summary}"""',
            f"        {url_line}"
        ]
        
        # Generate query parameters handling
        if query_params:
            body_lines.append("        params = {}")
            for param in query_params:
                param_name = to_snake_case(param['name'])
                original_name = param['name']
                required = param.get('required', False)
                if required:
                    body_lines.append(f'        params["{original_name}"] = {param_name}')
                else:
                    body_lines.append(f'        if {param_name} is not None:')
                    body_lines.append(f'            params["{original_name}"] = {param_name}')
        
        # Generate headers handling
        headers_lines = []
        if header_params:
            headers_lines.append("        headers = self.get_headers()")
            for param in header_params:
                param_name = to_snake_case(param['name'])
                original_name = param['name']
                required = param.get('required', False)
                if required:
                    headers_lines.append(f'        headers["{original_name}"] = {param_name}')
                else:
                    headers_lines.append(f'        if {param_name} is not None:')
                    headers_lines.append(f'            headers["{original_name}"] = {param_name}')
        
        # Generate cookies handling
        cookies_lines = []
        if cookie_params:
            cookies_lines.append("        cookies = {}")
            for param in cookie_params:
                param_name = to_snake_case(param['name'])
                original_name = param['name']
                required = param.get('required', False)
                if required:
                    cookies_lines.append(f'        cookies["{original_name}"] = {param_name}')
                else:
                    cookies_lines.append(f'        if {param_name} is not None:')
                    cookies_lines.append(f'            cookies["{original_name}"] = {param_name}')
        
        # Add generated lines to body
        body_lines.extend(headers_lines)
        body_lines.extend(cookies_lines)
        
        # Generate request call
        request_args = ['"' + http_method + '"', 'url']
        
        if query_params:
            request_args.append('params=params if params else None')
        if header_params:
            request_args.append('headers=headers')
        elif not header_params:
            # Always pass headers for consistency
            request_args.append('headers=self.get_headers()')
        if cookie_params:
            request_args.append('cookies=cookies if cookies else None')
        if request_body_info:
            if request_body_info.get('is_json', True):
                request_args.append('json=payload')
            else:
                request_args.append('data=payload')
        
        # Generate return logic with strong typing
        if response_model and response_model != "requests.Response":
            # Strong typed response - convert response to model
            body_lines.append(f"        response = self._make_request({', '.join(request_args)})")
            
            if response_model.startswith('List[') and response_model.endswith(']'):
                # Handle array responses
                model_name = response_model[5:-1]  # Remove 'List[' and ']'
                body_lines.append(f"        return [{model_name}.from_dict(item) for item in response.json()]")
            elif response_model in ['str', 'int', 'float', 'bool', 'Dict[str, Any]']:
                # Handle primitive types and Dict - return JSON directly
                if response_model == 'str':
                    body_lines.append(f"        return response.text")
                elif response_model == 'Dict[str, Any]':
                    body_lines.append(f"        return response.json()")
                else:
                    body_lines.append(f"        return response.json()")
            else:
                # Handle single model responses
                body_lines.append(f"        return {response_model}.from_dict(response.json())")
        else:
            # Raw response
            return_line = f"        return self._make_request({', '.join(request_args)})"
            body_lines.append(return_line)
        
        method_body = '\n'.join(body_lines)
        
        return f"""
    {signature}
{method_body}"""
    
    def _get_parameter_type(self, param: Dict[str, Any]) -> str:
        """Get the Python type for a parameter."""
        # This method needs to be implemented differently for each version
        # but provides a common interface
        param_type = param.get('type', 'string')
        param_format = param.get('format')
        
        # Handle array types
        if param_type == 'array':
            items = param.get('items', {})
            item_type = items.get('type', 'string')
            return f"List[{get_python_type(item_type, items.get('format'))}]"
        
        return get_python_type(param_type, param_format)
    
    def _find_body_parameter(self, parameters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the body parameter in the parameters list (for Swagger 2.0)."""
        for param in parameters:
            if param.get('in') == 'body':
                return param
        return None