"""
Unit tests for the main generator module.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from openapi_client_generator import OpenAPIClientGenerator


class TestOpenAPIClientGenerator(unittest.TestCase):
    """Test cases for OpenAPIClientGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Sample OpenAPI 3.0 specification
        self.sample_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "Get all users",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create a user",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["id", "name"]
                    }
                }
            }
        }
        
        # Create temporary spec file
        self.spec_file = self.temp_dir / "test_spec.json"
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_spec, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(self.spec_file), 
            str(output_dir), 
            "test_service"
        )
        
        self.assertEqual(generator.spec_file, str(self.spec_file))
        self.assertEqual(generator.output_dir, output_dir)
        self.assertEqual(generator.service_name, "test_service")
        self.assertTrue(generator.spec_loader.is_openapi3)
    
    def test_full_client_generation(self):
        """Test complete client generation process."""
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(self.spec_file), 
            str(output_dir), 
            "test_service"
        )
        
        generator.generate_client()
        
        # Check that service directory was created
        service_dir = output_dir / "test_service"
        self.assertTrue(service_dir.exists())
        self.assertTrue(service_dir.is_dir())
        
        # Check that main package __init__.py was created
        main_init = service_dir / "__init__.py"
        self.assertTrue(main_init.exists())
        
        # Check that API client file was created
        api_file = service_dir / "TestServiceAPIs.py"
        self.assertTrue(api_file.exists())
        
        # Check that models directory was created
        models_dir = service_dir / "models"
        self.assertTrue(models_dir.exists())
        
        # Check that model files were created
        user_model = models_dir / "User.py"
        models_init = models_dir / "__init__.py"
        self.assertTrue(user_model.exists())
        self.assertTrue(models_init.exists())
    
    def test_main_init_content(self):
        """Test the content of main package __init__.py."""
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(self.spec_file), 
            str(output_dir), 
            "test_service"
        )
        
        generator.generate_client()
        
        main_init = output_dir / "test_service" / "__init__.py"
        with open(main_init, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper imports and exports
        self.assertIn('from .TestServiceAPIs import TestServiceAPIs', content)
        self.assertIn('__version__ = \'1.0.0\'', content)
        self.assertIn('__all__ = [\'TestServiceAPIs\']', content)
    
    def test_api_client_content(self):
        """Test the content of generated API client."""
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(self.spec_file), 
            str(output_dir), 
            "test_service"
        )
        
        generator.generate_client()
        
        api_file = output_dir / "test_service" / "TestServiceAPIs.py"
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for class and methods
        self.assertIn('class TestServiceAPIs:', content)
        self.assertIn('def get_users(self', content)
        self.assertIn('def create_user(self', content)  # Updated to match operationId "createUser"
        
        # Check for proper model imports
        self.assertIn('from .models.User import User', content)
        
        # Check for proper typing
        self.assertIn('-> List[User]:', content)  # getUsers return type
        self.assertIn('-> User:', content)  # createUser return type
    
    def test_user_model_content(self):
        """Test the content of generated User model."""
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(self.spec_file), 
            str(output_dir), 
            "test_service"
        )
        
        generator.generate_client()
        
        user_file = output_dir / "test_service" / "models" / "User.py"
        with open(user_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for class definition
        self.assertIn('class User:', content)
        
        # Check for properties
        self.assertIn('def id(self)', content)
        self.assertIn('def name(self)', content)
        self.assertIn('def email(self)', content)
        
        # Check for utility methods
        self.assertIn('def to_dict(self)', content)
        self.assertIn('def from_dict(cls', content)
    
    def test_invalid_spec_file(self):
        """Test handling of invalid spec file."""
        output_dir = self.temp_dir / "output"
        
        with self.assertRaises(ValueError):
            OpenAPIClientGenerator(
                "/nonexistent/file.json", 
                str(output_dir), 
                "test_service"
            )
    
    def test_empty_specification(self):
        """Test handling of specification with no schemas or paths."""
        empty_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Empty API",
                "version": "1.0.0"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Create temporary empty spec file
        empty_spec_file = self.temp_dir / "empty_spec.json"
        with open(empty_spec_file, 'w', encoding='utf-8') as f:
            json.dump(empty_spec, f)
        
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(empty_spec_file), 
            str(output_dir), 
            "empty_service"
        )
        
        generator.generate_client()
        
        # Check that service directory was still created
        service_dir = output_dir / "empty_service"
        self.assertTrue(service_dir.exists())
        
        # Check that API file was created (even if empty)
        api_file = service_dir / "EmptyServiceAPIs.py"
        self.assertTrue(api_file.exists())
    
    def test_service_name_with_special_characters(self):
        """Test service name with special characters."""
        output_dir = self.temp_dir / "output"
        generator = OpenAPIClientGenerator(
            str(self.spec_file), 
            str(output_dir), 
            "test-service_v2"
        )
        
        generator.generate_client()
        
        # Check that service directory was created with original name
        service_dir = output_dir / "test-service_v2"
        self.assertTrue(service_dir.exists())
        
        # Check that API class name was sanitized
        api_file = service_dir / "TestServiceV2APIs.py"
        self.assertTrue(api_file.exists())
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('class TestServiceV2APIs:', content)


if __name__ == '__main__':
    unittest.main()