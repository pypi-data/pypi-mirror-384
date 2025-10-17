"""
API generator for OpenAPI/Swagger specifications.
Compatibility wrapper that delegates to version-specific generators.
"""

from typing import Dict, Any
from pathlib import Path
from .openapi30_api_generator import OpenAPI30APIGenerator
from .swagger20_api_generator import Swagger20APIGenerator


class APIGenerator:
    """
    Compatibility wrapper for the old APIGenerator interface.
    Delegates to the appropriate version-specific generator.
    """
    
    def __init__(self, paths: Dict[str, Any], schemas: Dict[str, Any], 
                 service_name: str, output_dir: Path, is_openapi3: bool):
        """Initialize the API generator."""
        self.paths = paths
        self.schemas = schemas
        self.service_name = service_name
        self.output_dir = output_dir
        self.is_openapi3 = is_openapi3
        
        # Create minimal spec_data for the generators
        self.spec_data = {
            'paths': paths,
            'components': {'schemas': schemas} if is_openapi3 else None,
            'definitions': schemas if not is_openapi3 else None,
            'info': {'title': service_name, 'version': '1.0.0'},
            'openapi': '3.0.0' if is_openapi3 else None,
            'swagger': '2.0' if not is_openapi3 else None
        }
        
        # Initialize the appropriate generator
        if is_openapi3:
            self.generator = OpenAPI30APIGenerator(paths, schemas, service_name, output_dir, self.spec_data)
        else:
            self.generator = Swagger20APIGenerator(paths, schemas, service_name, output_dir, self.spec_data)
        
    def generate_api_client(self):
        """Generate the main API client class."""
        return self.generator.generate_api_client()