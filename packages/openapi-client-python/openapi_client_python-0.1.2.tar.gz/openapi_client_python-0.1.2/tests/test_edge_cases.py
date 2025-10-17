"""
Tests for edge cases and missing coverage scenarios.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator
from openapi_client_generator.swagger20_api_generator import Swagger20APIGenerator


class TestEdgeCases:
    """Test class for edge cases to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.schemas = {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'}
                }
            }
        }
    
    def test_operation_with_all_parameter_types(self):
        """Test operation with path, query, header, and cookie parameters."""
        paths = {
            '/test/{id}': {
                'get': {
                    'operationId': 'testOperation',
                    'parameters': [
                        {
                            'name': 'id',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'string'}
                        },
                        {
                            'name': 'query_param',
                            'in': 'query',
                            'required': False,
                            'schema': {'type': 'string'}
                        },
                        {
                            'name': 'X-Custom-Header',
                            'in': 'header',
                            'required': True,
                            'schema': {'type': 'string'}
                        },
                        {
                            'name': 'session_id',
                            'in': 'cookie',
                            'required': False,
                            'schema': {'type': 'string'}
                        }
                    ],
                    'responses': {
                        '200': {
                            'description': 'Success',
                            'content': {
                                'application/json': {
                                    'schema': {'type': 'object'}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify all parameter types are included
        assert 'id: str' in content
        assert 'query_param: Optional[str] = None' in content
        assert 'x_custom_header: str' in content
        assert 'session_id: Optional[str] = None' in content
        
        # Verify headers and cookies handling
        assert 'headers = self.get_headers()' in content
        assert 'cookies = {}' in content
        assert 'headers["X-Custom-Header"] = x_custom_header' in content
        assert 'if session_id is not None:' in content
        assert 'cookies["session_id"] = session_id' in content

    def test_operation_without_operation_id_single_path_part(self):
        """Test operation without operationId and single path part."""
        paths = {
            '/users': {
                'get': {
                    'responses': {
                        '200': {
                            'description': 'Success'
                        }
                    }
                }
            }
        }
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should generate method name from path
        assert 'def get_users(' in content

    def test_operation_without_operation_id_multiple_path_parts(self):
        """Test operation without operationId and multiple path parts."""
        paths = {
            '/users/profiles/settings': {
                'post': {
                    'responses': {
                        '200': {
                            'description': 'Success'
                        }
                    }
                }
            }
        }
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should generate method name from path parts
        assert 'def post_users_profiles_settings(' in content

    def test_request_body_with_different_content_types(self):
        """Test request body with various content types."""
        paths = {
            '/upload': {
                'post': {
                    'operationId': 'uploadFile',
                    'requestBody': {
                        'required': True,
                        'content': {
                            'multipart/form-data': {
                                'schema': {'type': 'object'}
                            },
                            'application/octet-stream': {
                                'schema': {'type': 'string', 'format': 'binary'}
                            }
                        }
                    },
                    'responses': {
                        '200': {
                            'description': 'Success'
                        }
                    }
                }
            }
        }
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should handle different content types
        assert 'def upload_file(' in content
        assert 'payload: Dict[str, Any]' in content

    def test_response_without_success_status(self):
        """Test response handling when no 2xx status code is present."""
        paths = {
            '/error': {
                'get': {
                    'operationId': 'getError',
                    'responses': {
                        '400': {
                            'description': 'Bad Request'
                        },
                        '500': {
                            'description': 'Internal Server Error'
                        }
                    }
                }
            }
        }
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should still generate method but return requests.Response
        assert 'def get_error(' in content
        assert '-> requests.Response:' in content

    def test_api_with_no_paths(self):
        """Test API spec with no paths defined."""
        paths = {}
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should generate basic class structure
        assert 'class TestServiceAPIs:' in content
        assert 'def __init__(self, base_url: str = None, auth_token: str = None, tenant: str = None):' in content
        
    def test_cookie_parameter_required(self):
        """Test required cookie parameter handling."""
        paths = {
            '/secure': {
                'get': {
                    'operationId': 'getSecure',
                    'parameters': [
                        {
                            'name': 'auth_token',
                            'in': 'cookie',
                            'required': True,
                            'schema': {'type': 'string'}
                        }
                    ],
                    'responses': {
                        '200': {
                            'description': 'Success'
                        }
                    }
                }
            }
        }
        
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}

        
        generator = OpenAPI30APIGenerator(paths, self.schemas, 'test_service', self.temp_dir, spec_data)
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Required cookie parameter should not have Optional in method signature
        assert 'def get_secure(self, auth_token: str)' in content
        assert 'cookies["auth_token"] = auth_token' in content
        # The method parameter should be required (not Optional)
        assert 'auth_token: Optional[str]' not in 'def get_secure(self, auth_token: str)'