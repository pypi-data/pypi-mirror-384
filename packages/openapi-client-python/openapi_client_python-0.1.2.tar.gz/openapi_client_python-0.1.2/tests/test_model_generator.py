"""
Unit tests for the model_generator module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from openapi_client_generator.model_generator import ModelGenerator


class TestModelGenerator(unittest.TestCase):
    """Test cases for ModelGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Sample schemas
        self.schemas = {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'email': {'type': 'string'},
                    'active': {'type': 'boolean'}
                },
                'required': ['id', 'name']
            },
            'Product': {
                'type': 'object',
                'properties': {
                    'productId': {'type': 'integer'},
                    'productName': {'type': 'string'},
                    'price': {'type': 'number'},
                    'tags': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                },
                'required': ['productId', 'productName']
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_model_generation(self):
        """Test generating model classes."""
        generator = ModelGenerator(self.schemas, self.temp_dir)
        generator.generate_models()
        
        # Check that models directory was created
        models_dir = self.temp_dir / "models"
        self.assertTrue(models_dir.exists())
        self.assertTrue(models_dir.is_dir())
        
        # Check that model files were created
        user_file = models_dir / "User.py"
        product_file = models_dir / "Product.py"
        init_file = models_dir / "__init__.py"
        
        self.assertTrue(user_file.exists())
        self.assertTrue(product_file.exists())
        self.assertTrue(init_file.exists())
    
    def test_user_model_content(self):
        """Test the content of generated User model."""
        generator = ModelGenerator(self.schemas, self.temp_dir)
        generator.generate_models()
        
        user_file = self.temp_dir / "models" / "User.py"
        with open(user_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for class definition
        self.assertIn('class User:', content)
        
        # Check for imports
        self.assertIn('from __future__ import annotations', content)
        self.assertIn('import json', content)
        self.assertIn('from typing import List, Union, Optional, Dict, Any', content)
        
        # Check for properties
        self.assertIn('def id(self)', content)
        self.assertIn('def name(self)', content)
        self.assertIn('def email(self)', content)
        self.assertIn('def active(self)', content)
        
        # Check for setters
        self.assertIn('@id.setter', content)
        self.assertIn('@name.setter', content)
        
        # Check for utility methods
        self.assertIn('def to_dict(self)', content)
        self.assertIn('def to_json(self)', content)
        self.assertIn('def from_dict(cls', content)
        self.assertIn('def from_json(cls', content)
    
    def test_product_model_content(self):
        """Test the content of generated Product model."""
        generator = ModelGenerator(self.schemas, self.temp_dir)
        generator.generate_models()
        
        product_file = self.temp_dir / "models" / "Product.py"
        with open(product_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for class definition
        self.assertIn('class Product:', content)
        
        # Check for properties with snake_case conversion
        self.assertIn('def product_id(self)', content)
        self.assertIn('def product_name(self)', content)
        self.assertIn('def price(self)', content)
        self.assertIn('def tags(self)', content)
    
    def test_models_init_file(self):
        """Test the content of models __init__.py file."""
        generator = ModelGenerator(self.schemas, self.temp_dir)
        generator.generate_models()
        
        init_file = self.temp_dir / "models" / "__init__.py"
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for imports
        self.assertIn('from .User import User', content)
        self.assertIn('from .Product import Product', content)
        
        # Check for __all__ list
        self.assertIn("__all__ = ['User', 'Product']", content)
    
    def test_empty_schemas(self):
        """Test handling of empty schemas."""
        generator = ModelGenerator({}, self.temp_dir)
        generator.generate_models()
        
        # Check that models directory was created
        models_dir = self.temp_dir / "models"
        self.assertTrue(models_dir.exists())
        
        # Check that __init__.py exists but has minimal content
        init_file = models_dir / "__init__.py"
        self.assertTrue(init_file.exists())
        
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("__all__ = []", content)
    
    def test_model_with_special_characters(self):
        """Test model generation with special characters in name."""
        special_schemas = {
            'User.Model': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'}
                }
            }
        }
        
        generator = ModelGenerator(special_schemas, self.temp_dir)
        generator.generate_models()
        
        # Check that sanitized file was created
        model_file = self.temp_dir / "models" / "User_Model.py"
        self.assertTrue(model_file.exists())
        
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('class User_Model:', content)
    
    def test_property_type_generation(self):
        """Test that property types are correctly generated."""
        generator = ModelGenerator(self.schemas, self.temp_dir)
        generator.generate_models()
        
        user_file = self.temp_dir / "models" / "User.py"
        with open(user_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for correct type annotations
        self.assertIn('-> int:', content)  # id property
        self.assertIn('-> str:', content)  # name property
        self.assertIn('-> bool:', content)  # active property


if __name__ == '__main__':
    unittest.main()