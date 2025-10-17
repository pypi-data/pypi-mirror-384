"""
Unit tests for the spec_loader module.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from openapi_client_generator.spec_loader import SpecLoader


class TestSpecLoader(unittest.TestCase):
    """Test cases for SpecLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample OpenAPI 3.0 specification
        self.openapi3_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users"
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"}
                        }
                    }
                }
            },
            "servers": [
                {"url": "https://api.example.com"}
            ]
        }
        
        # Sample Swagger 2.0 specification
        self.swagger2_spec = {
            "swagger": "2.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "basePath": "/api/v1",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users"
                    }
                }
            },
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
    
    def test_load_openapi3_spec(self):
        """Test loading OpenAPI 3.0 specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.openapi3_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            self.assertTrue(loader.is_openapi3)
            self.assertEqual(loader.spec_data['openapi'], '3.0.0')
        finally:
            os.unlink(temp_file)
    
    def test_load_swagger2_spec(self):
        """Test loading Swagger 2.0 specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.swagger2_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            self.assertFalse(loader.is_openapi3)
            self.assertEqual(loader.spec_data['swagger'], '2.0')
        finally:
            os.unlink(temp_file)
    
    def test_invalid_spec_file(self):
        """Test handling of invalid specification file."""
        with self.assertRaises(ValueError):
            SpecLoader('/nonexistent/file.json')
    
    def test_invalid_spec_format(self):
        """Test handling of invalid specification format."""
        invalid_spec = {"title": "Invalid"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_spec, f)
            temp_file = f.name
        
        try:
            with self.assertRaises(ValueError):
                SpecLoader(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_get_schemas_openapi3(self):
        """Test getting schemas from OpenAPI 3.0 spec."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.openapi3_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            schemas = loader.get_schemas()
            self.assertIn('User', schemas)
            self.assertEqual(schemas['User']['type'], 'object')
        finally:
            os.unlink(temp_file)
    
    def test_get_schemas_swagger2(self):
        """Test getting schemas from Swagger 2.0 spec."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.swagger2_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            schemas = loader.get_schemas()
            self.assertIn('User', schemas)
            self.assertEqual(schemas['User']['type'], 'object')
        finally:
            os.unlink(temp_file)
    
    def test_get_paths(self):
        """Test getting paths from specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.openapi3_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            paths = loader.get_paths()
            self.assertIn('/users', paths)
        finally:
            os.unlink(temp_file)
    
    def test_get_info(self):
        """Test getting API info from specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.openapi3_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            info = loader.get_info()
            self.assertEqual(info['title'], 'Test API')
            self.assertEqual(info['version'], '1.0.0')
        finally:
            os.unlink(temp_file)
    
    def test_get_servers_openapi3(self):
        """Test getting servers from OpenAPI 3.0 spec."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.openapi3_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            servers = loader.get_servers()
            self.assertEqual(len(servers), 1)
            self.assertEqual(servers[0]['url'], 'https://api.example.com')
        finally:
            os.unlink(temp_file)
    
    def test_get_servers_swagger2(self):
        """Test getting servers from Swagger 2.0 spec (should return empty list)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.swagger2_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            servers = loader.get_servers()
            self.assertEqual(len(servers), 0)
        finally:
            os.unlink(temp_file)
    
    def test_get_base_path_swagger2(self):
        """Test getting base path from Swagger 2.0 spec."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.swagger2_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            base_path = loader.get_base_path()
            self.assertEqual(base_path, '/api/v1')
        finally:
            os.unlink(temp_file)
    
    def test_get_base_path_openapi3(self):
        """Test getting base path from OpenAPI 3.0 spec (should return empty string)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.openapi3_spec, f)
            temp_file = f.name
        
        try:
            loader = SpecLoader(temp_file)
            base_path = loader.get_base_path()
            self.assertEqual(base_path, '')
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()