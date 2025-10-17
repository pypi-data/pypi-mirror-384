"""
Unit tests for the api_generator module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator
from openapi_client_generator.swagger20_api_generator import Swagger20APIGenerator


class TestAPIGenerator(unittest.TestCase):
    """Test cases for APIGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Sample paths for OpenAPI 3.0
        self.openapi3_paths = {
            '/users': {
                'get': {
                    'operationId': 'getUsers',
                    'summary': 'Get all users',
                    'parameters': [
                        {
                            'name': 'limit',
                            'in': 'query',
                            'required': False,
                            'schema': {'type': 'integer'}
                        }
                    ],
                    'responses': {
                        '200': {
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'array',
                                        'items': {'$ref': '#/components/schemas/User'}
                                    }
                                }
                            }
                        }
                    }
                },
                'post': {
                    'operationId': 'createUser',
                    'summary': 'Create a user',
                    'requestBody': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/User'}
                            }
                        }
                    },
                    'responses': {
                        '201': {
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/User'}
                                }
                            }
                        }
                    }
                }
            },
            '/users/{id}': {
                'get': {
                    'operationId': 'getUserById',
                    'summary': 'Get user by ID',
                    'parameters': [
                        {
                            'name': 'id',
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'integer'}
                        }
                    ],
                    'responses': {
                        '200': {
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/User'}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Sample schemas
        self.schemas = {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'}
                }
            }
        }
        
        # Sample Swagger 2.0 paths
        self.swagger2_paths = {
            '/users': {
                'get': {
                    'operationId': 'getUsers',
                    'summary': 'Get all users',
                    'parameters': [
                        {
                            'name': 'limit',
                            'in': 'query',
                            'required': False,
                            'type': 'integer'
                        }
                    ],
                    'responses': {
                        '200': {
                            'schema': {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/User'}
                            }
                        }
                    }
                },
                'post': {
                    'operationId': 'createUser',
                    'summary': 'Create a user',
                    'parameters': [
                        {
                            'name': 'user',
                            'in': 'body',
                            'required': True,
                            'schema': {'$ref': '#/definitions/User'}
                        }
                    ],
                    'responses': {
                        '201': {
                            'schema': {'$ref': '#/definitions/User'}
                        }
                    }
                }
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_api_generation_openapi3(self):
        """Test generating API client for OpenAPI 3.0."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        generator.generate_api_client()
        
        # Check that API file was created
        api_file = self.temp_dir / "TestServiceAPIs.py"
        self.assertTrue(api_file.exists())
    
    def test_api_generation_swagger2(self):
        """Test generating API client for Swagger 2.0."""
        spec_data = {'swagger': '2.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = Swagger20APIGenerator(
            self.swagger2_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        generator.generate_api_client()
        
        # Check that API file was created
        api_file = self.temp_dir / "TestServiceAPIs.py"
        self.assertTrue(api_file.exists())
    
    def test_api_content_openapi3(self):
        """Test the content of generated API client for OpenAPI 3.0."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for class definition
        self.assertIn('class TestServiceAPIs:', content)
        
        # Check for imports
        self.assertIn('import requests', content)
        self.assertIn('import logging', content)
        self.assertIn('from typing import Optional, Dict, Any, Union, List', content)
        self.assertIn('from .models.User import User', content)
        
        # Check for initialization method
        self.assertIn('def __init__(self, base_url: str = None', content)
        
        # Check for utility methods
        self.assertIn('def set_base_url(self, base_url: str)', content)
        self.assertIn('def set_auth_token(self, token: str)', content)
        self.assertIn('def _make_request(self, method: str, url: str', content)
        
        # Check for generated API methods
        self.assertIn('def get_users(self', content)
        self.assertIn('def create_user(self', content)
        self.assertIn('def get_user_by_id(self', content)
    
    def test_method_signatures(self):
        """Test that method signatures are correctly generated."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        generator.generate_api_client()
        
        api_file = self.temp_dir / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check method signatures with proper typing
        self.assertIn('def get_users(self, limit: Optional[int] = None) -> List[User]:', content)
        self.assertIn('def create_user(self, payload: User = None) -> User:', content)
        self.assertIn('def get_user_by_id(self, id: int) -> User:', content)
    
    def test_extract_operations(self):
        """Test extracting operations from paths."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        
        operations = generator._extract_operations()
        
        # Should have 3 operations
        self.assertEqual(len(operations), 3)
        
        # Check operation details
        get_users = next(op for op in operations if op['operation_id'] == 'getUsers')
        self.assertEqual(get_users['method'], 'GET')
        self.assertEqual(get_users['path'], '/users')
        
        create_user = next(op for op in operations if op['operation_id'] == 'createUser')
        self.assertEqual(create_user['method'], 'POST')
        self.assertEqual(create_user['path'], '/users')
        
        get_user_by_id = next(op for op in operations if op['operation_id'] == 'getUserById')
        self.assertEqual(get_user_by_id['method'], 'GET')
        self.assertEqual(get_user_by_id['path'], '/users/{id}')
    
    def test_response_model_detection_openapi3(self):
        """Test response model detection for OpenAPI 3.0."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        
        # Test single model response
        operation = {
            'responses': {
                '200': {
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/User'}
                        }
                    }
                }
            }
        }
        response_model = generator._get_response_model(operation)
        self.assertEqual(response_model, 'User')
        
        # Test array response
        operation = {
            'responses': {
                '200': {
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'array',
                                'items': {'$ref': '#/components/schemas/User'}
                            }
                        }
                    }
                }
            }
        }
        response_model = generator._get_response_model(operation)
        self.assertEqual(response_model, 'List[User]')
    
    def test_request_body_model_detection_openapi3(self):
        """Test request body model detection for OpenAPI 3.0."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        
        # Test single model request body
        operation = {
            'requestBody': {
                'content': {
                    'application/json': {
                        'schema': {'$ref': '#/components/schemas/User'}
                    }
                }
            }
        }
        request_info = generator._get_request_body_info(operation)
        self.assertIsNotNone(request_info)
        self.assertEqual(request_info['type'], 'User')
    
    def test_method_name_generation(self):
        """Test method name generation."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        
        # Test simple path
        operation = {
            'operation_id': 'getUsers',
            'path': '/users',
            'method': 'GET'
        }
        method_name = generator._generate_method_name(operation)
        self.assertEqual(method_name, 'get_users')
        
        # Test path with parameter
        operation = {
            'operation_id': 'getUserById',
            'path': '/users/{id}',
            'method': 'GET'
        }
        method_name = generator._generate_method_name(operation)
        self.assertEqual(method_name, 'get_user_by_id')
    
    def test_model_imports_generation(self):
        """Test model imports generation."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            self.openapi3_paths, 
            self.schemas, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        
        imports = generator._generate_model_imports()
        self.assertIn('from .models.User import User', imports)
    
    def test_empty_paths(self):
        """Test handling of empty paths."""
        spec_data = {'openapi': '3.0.0', 'info': {'title': 'Test API', 'version': '1.0.0'}}
        generator = OpenAPI30APIGenerator(
            {}, 
            {}, 
            'test_service', 
            self.temp_dir,
            spec_data
        )
        generator.generate_api_client()
        
        # Check that API file was created even with no operations
        api_file = self.temp_dir / "TestServiceAPIs.py"
        self.assertTrue(api_file.exists())
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should still have the class structure
        self.assertIn('class TestServiceAPIs:', content)
        self.assertIn('def __init__(self', content)


if __name__ == '__main__':
    unittest.main()