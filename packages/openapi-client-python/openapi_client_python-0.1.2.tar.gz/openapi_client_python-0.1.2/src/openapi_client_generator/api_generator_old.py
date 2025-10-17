"""
API generator for OpenAPI/Swagger specifications.
"""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from .utils import sanitize_model_name, to_snake_case, to_pascal_case, get_python_type


class APIGenerator:
    """Generates strongly-typed API client classes from path definitions."""
    
    def __init__(self, paths: Dict[str, Any], schemas: Dict[str, Any], 
                 service_name: str, output_dir: Path, is_openapi3: bool):
        """Initialize the API generator."""
        self.paths = paths
        self.schemas = schemas
        self.service_name = service_name
        self.output_dir = output_dir
        self.is_openapi3 = is_openapi3
        
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
                        'request_body': operation.get('requestBody') if self.is_openapi3 else None,
                        'body_param': self._find_body_parameter(operation.get('parameters', [])) if not self.is_openapi3 else None,
                        'responses': operation.get('responses', {}),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', '')
                    })
        
        return operations
    
    def _find_body_parameter(self, parameters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find body parameter in Swagger 2.0 parameters."""
        for param in parameters:
            if param.get('in') == 'body':
                return param
        return None
    
    def _generate_apis_content(self, class_name: str, operations: List[Dict[str, Any]]) -> str:
        """Generate the APIs class content with strong typing."""
        # Generate model imports
        model_imports = self._generate_model_imports()
        
        imports = f'''import requests
import logging
from typing import Optional, Dict, Any, Union, List
{model_imports}


class {class_name}:
    """
    Strongly-typed API client for {self.service_name}
    
    This class provides methods to interact with the {self.service_name} API endpoints.
    All methods are strongly-typed with automatic model serialization/deserialization.
    """
    
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
        self._headers = {{
            "Content-Type": "application/json",
            "User-Agent": "GeneratedApiClient/{self.service_name}",
        }}
        
        if auth_token:
            self.set_auth_token(auth_token)
    
    def set_base_url(self, base_url: str):
        """Set the base URL for API requests"""
        self._base_url = base_url.rstrip('/')
        self.logger.info(f"Base URL set to: {{self._base_url}}")
    
    def set_tenant(self, tenant: str):
        """Set the tenant ID"""
        self._tenant = tenant
        self.logger.info(f"Tenant set to: {{tenant}}")
    
    def get_tenant(self) -> str:
        """Get the current tenant ID"""
        return self._tenant
    
    def set_auth_token(self, token: str):
        """Set the authentication token"""
        self._headers["Authorization"] = f"Bearer {{token}}"
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
            self.logger.debug(f"Making {{method}} request to: {{url}}")
            
            # Ensure headers are included
            if 'headers' not in kwargs:
                kwargs['headers'] = self.get_headers()
            
            response = requests.request(method, url, **kwargs)
            
            # Log response details
            self.logger.debug(f"Response status: {{response.status_code}}")
            
            if not response.ok:
                self.logger.error(f"Request failed: {{response.status_code}} - {{response.text}}")
                response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {{e}}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {{e}}")
            raise'''
        
        methods = []
        for op in operations:
            method_code = self._generate_api_method(op)
            methods.append(method_code)
        
        return imports + "\n\n" + "\n\n".join(methods)
    
    def _generate_model_imports(self) -> str:
        """Generate import statements for model classes."""
        if not self.schemas:
            return ""
        
        imports = []
        for model_name in self.schemas.keys():
            # Sanitize model name for Python imports
            sanitized_name = sanitize_model_name(model_name)
            imports.append(f"from .models.{sanitized_name} import {sanitized_name}")
        
        return "\n".join(imports)
    
    def _get_response_model(self, operation: Dict[str, Any]) -> Optional[str]:
        """Determine the response model for an operation."""
        responses = operation.get('responses', {})
        
        # Check 200 response first
        success_response = responses.get('200') or responses.get('201') or responses.get('202')
        if not success_response:
            return None
        
        if self.is_openapi3:
            content = success_response.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
        else:
            schema = success_response.get('schema', {})
        
        # Check if it references a model
        if '$ref' in schema:
            ref = schema['$ref']
            if self.is_openapi3:
                # OpenAPI 3.0: #/components/schemas/ModelName
                if ref.startswith('#/components/schemas/'):
                    model_name = ref.split('/')[-1]
                    return sanitize_model_name(model_name)
            else:
                # Swagger 2.0: #/definitions/ModelName
                if ref.startswith('#/definitions/'):
                    model_name = ref.split('/')[-1]
                    return sanitize_model_name(model_name)
        
        # Handle array responses
        elif schema.get('type') == 'array' and 'items' in schema:
            items_schema = schema['items']
            if '$ref' in items_schema:
                ref = items_schema['$ref']
                if self.is_openapi3:
                    if ref.startswith('#/components/schemas/'):
                        model_name = ref.split('/')[-1]
                        return f"List[{sanitize_model_name(model_name)}]"
                else:
                    if ref.startswith('#/definitions/'):
                        model_name = ref.split('/')[-1]
                        return f"List[{sanitize_model_name(model_name)}]"
        
        return None
    
    def _get_request_body_model(self, operation: Dict[str, Any]) -> Optional[str]:
        """Determine the request body model for an operation."""
        # Handle Swagger 2.0 body parameter
        body_param = operation.get('body_param')
        if body_param and 'schema' in body_param:
            schema = body_param['schema']
            if '$ref' in schema:
                ref = schema['$ref']
                if ref.startswith('#/definitions/'):
                    model_name = ref.split('/')[-1]
                    return sanitize_model_name(model_name)
            # Handle arrays of models
            elif schema.get('type') == 'array' and 'items' in schema:
                items_schema = schema['items']
                if '$ref' in items_schema:
                    ref = items_schema['$ref']
                    if ref.startswith('#/definitions/'):
                        model_name = ref.split('/')[-1]
                        return f"List[{sanitize_model_name(model_name)}]"
        
        # Handle OpenAPI 3.0 request body
        if self.is_openapi3 and operation.get('request_body'):
            request_body = operation['request_body']
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
            
            if '$ref' in schema:
                ref = schema['$ref']
                if ref.startswith('#/components/schemas/'):
                    model_name = ref.split('/')[-1]
                    return sanitize_model_name(model_name)
            # Handle arrays of models
            elif schema.get('type') == 'array' and 'items' in schema:
                items_schema = schema['items']
                if '$ref' in items_schema:
                    ref = items_schema['$ref']
                    if ref.startswith('#/components/schemas/'):
                        model_name = ref.split('/')[-1]
                        return f"List[{sanitize_model_name(model_name)}]"
        
        return None
    
    def _generate_method_name(self, operation: Dict[str, Any]) -> str:
        """Generate a clean method name from operation details."""
        operation_id = operation.get('operation_id', '')
        path = operation['path']
        http_method = operation['method'].lower()
        
        # Clean up the path to create a meaningful method name
        clean_path = re.sub(r'/api/v\d+/', '', path)
        clean_path = re.sub(r'\{[^}]+\}', '_by_id', clean_path)
        clean_path = clean_path.strip('/')
        
        # Convert path to method name
        path_parts = [part for part in clean_path.split('/') if part]
        
        if path_parts:
            if len(path_parts) == 1:
                method_name = f"{http_method}_{path_parts[0]}"
            else:
                method_name = f"{http_method}_" + "_".join(path_parts)
        else:
            method_name = to_snake_case(operation_id)
        
        return to_snake_case(method_name)
    
    def _generate_api_method(self, operation: Dict[str, Any]) -> str:
        """Generate a single strongly-typed API method."""
        method_name = self._generate_method_name(operation)
        path = operation['path']
        http_method = operation['method'].lower()
        parameters = operation['parameters']
        
        # Extract parameters by location
        path_params = [p for p in parameters if p.get('in') == 'path']
        query_params = [p for p in parameters if p.get('in') == 'query']
        header_params = [p for p in parameters if p.get('in') == 'header']
        cookie_params = [p for p in parameters if p.get('in') == 'cookie']
        body_param = operation.get('body_param')
        
        # Generate method signature with strong typing
        required_params = []
        optional_params = []
        
        # Path parameters are always required
        for param in path_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required_params.append(f"{param_name}: {param_type}")
        
        # Query parameters can be required or optional
        for param in query_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required = param.get('required', False)
            if required:
                required_params.append(f"{param_name}: {param_type}")
            else:
                optional_params.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Header parameters can be required or optional
        for param in header_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required = param.get('required', False)
            if required:
                required_params.append(f"{param_name}: {param_type}")
            else:
                optional_params.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Cookie parameters can be required or optional
        for param in cookie_params:
            param_name = to_snake_case(param['name'])
            param_type = self._get_parameter_type(param)
            required = param.get('required', False)
            if required:
                required_params.append(f"{param_name}: {param_type}")
            else:
                optional_params.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Body parameter with strong typing
        if body_param or (self.is_openapi3 and operation.get('request_body')):
            request_model = self._get_request_body_model(operation)
            if request_model:
                optional_params.append(f"payload: {request_model} = None")
            else:
                optional_params.append("payload: dict = None")
        
        # Determine return type
        response_model = self._get_response_model(operation)
        return_type = f" -> {response_model}" if response_model else " -> requests.Response"
        
        # Combine parameters: required first, then optional
        all_params = required_params + optional_params
        signature = f"def {method_name}(self" + (", " + ", ".join(all_params) if all_params else "") + ")" + return_type + ":"
        
        # Generate docstring
        description = operation.get('description') or operation.get('summary') or f"{operation['operation_id']} operation"
        docstring = f'        """{description}"""'
        
        # Generate URL construction
        url_template = path
        for param in path_params:
            param_name = to_snake_case(param['name'])
            if param_name == 'tenant':
                url_template = url_template.replace(f"{{{param['name']}}}", "{self._tenant}")
            else:
                url_template = url_template.replace(f"{{{param['name']}}}", f"{{{param_name}}}")
        
        # Handle tenant parameter specially
        if '{tenant}' in url_template:
            url_template = url_template.replace('{tenant}', '{self._tenant}')
        
        url_line = f'        url = f"{{self._base_url}}{url_template}"'
        
        # Generate parameters handling
        params_lines = []
        if query_params:
            params_lines.append("        params = {}")
            for param in query_params:
                param_name = to_snake_case(param['name'])
                original_name = param['name']
                required = param.get('required', False)
                if required:
                    params_lines.append(f'        params["{original_name}"] = {param_name}')
                else:
                    params_lines.append(f'        if {param_name} is not None:')
                    params_lines.append(f'            params["{original_name}"] = {param_name}')
        
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
        
        # Generate request call with strong typing
        request_kwargs = []
        if query_params:
            request_kwargs.append("params=params if params else None")
        if header_params:
            request_kwargs.append("headers=headers")
        if cookie_params:
            request_kwargs.append("cookies=cookies if cookies else None")
        if body_param or (self.is_openapi3 and operation.get('request_body')):
            request_model = self._get_request_body_model(operation)
            if request_model:
                if request_model.startswith('List['):
                    request_kwargs.append("json=[item.to_dict() for item in payload] if payload else None")
                else:
                    request_kwargs.append("json=payload.to_dict() if payload else None")
            else:
                request_kwargs.append("json=payload")
        
        kwargs_str = ", " + ", ".join(request_kwargs) if request_kwargs else ""
        
        # Generate return statement with model conversion
        response_model = self._get_response_model(operation)
        if response_model:
            request_line = f'        response = self._make_request("{http_method.upper()}", url{kwargs_str})'
            
            # Handle List responses differently from single model responses
            if response_model.startswith('List[') and response_model.endswith(']'):
                model_name = response_model[5:-1]  # Remove 'List[' and ']'
                conversion_line = f'        return [{model_name}.from_dict(item) for item in response.json()]'
            else:
                conversion_line = f'        return {response_model}.from_dict(response.json())'
            
            request_line = request_line + "\n" + conversion_line
        else:
            request_line = f'        return self._make_request("{http_method.upper()}", url{kwargs_str})'
        
        # Combine all parts
        method_parts = [f"    {signature}", docstring, url_line]
        method_parts.extend(params_lines)
        method_parts.extend(headers_lines)
        method_parts.extend(cookies_lines)
        method_parts.append(request_line)
        
        return "\n".join(method_parts)
    
    def _get_parameter_type(self, param: Dict[str, Any]) -> str:
        """Get Python type for a parameter."""
        if self.is_openapi3:
            schema = param.get('schema', {})
            return get_python_type(schema)
        else:
            return get_python_type(param)