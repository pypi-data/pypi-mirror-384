"""
OpenAPI Python Client Generator with Strong Typing

Generates strongly-typed Python clients from OpenAPI 3.0 or Swagger 2.0 specifications.
"""

from .generator import OpenAPIClientGenerator
from .spec_loader import SpecLoader
from .model_generator import ModelGenerator
from .base_api_generator import BaseAPIGenerator
from .swagger20_api_generator import Swagger20APIGenerator
from .openapi30_api_generator import OpenAPI30APIGenerator

__version__ = "0.1.0"
__all__ = [
    'OpenAPIClientGenerator', 
    'SpecLoader', 
    'ModelGenerator', 
    'BaseAPIGenerator',
    'Swagger20APIGenerator',
    'OpenAPI30APIGenerator'
]