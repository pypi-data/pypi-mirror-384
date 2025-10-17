"""
Main OpenAPI client generator orchestrator.
"""

from pathlib import Path
from .spec_loader import SpecLoader
from .model_generator import ModelGenerator
from .swagger20_api_generator import Swagger20APIGenerator
from .openapi30_api_generator import OpenAPI30APIGenerator


class OpenAPIClientGenerator:
    """Generator for strongly-typed Python clients from OpenAPI/Swagger specs."""
    
    def __init__(self, spec_file: str, output_dir: str, service_name: str):
        """Initialize the generator."""
        self.spec_file = spec_file
        self.output_dir = Path(output_dir)
        self.service_name = service_name
        
        # Load and parse specification
        self.spec_loader = SpecLoader(spec_file)
        
        # Create output directories
        self.service_dir = self.output_dir / service_name
        
    def _select_api_generator(self, paths: dict, schemas: dict):
        """Select the appropriate API generator based on specification version."""
        version_info = self.spec_loader.get_version_info()
        
        print(f"Detected OpenAPI version: {version_info['exact_version']} (family: {version_info['version_family']})")
        
        # Map version families to generators
        if version_info['version_family'] == 'swagger2':
            return Swagger20APIGenerator(
                paths, schemas, self.service_name, self.service_dir, self.spec_loader.spec_data
            )
        elif version_info['version_family'] in ['openapi3', 'openapi31', 'openapi32']:
            # All OpenAPI 3.x versions use the same generator with version-aware features
            generator = OpenAPI30APIGenerator(
                paths, schemas, self.service_name, self.service_dir, self.spec_loader.spec_data
            )
            # Pass version info to generator for version-specific handling
            generator.version_info = version_info
            return generator
        else:
            raise ValueError(f"Unsupported specification version family: {version_info['version_family']}")
        
    def generate_client(self):
        """Generate the strongly-typed Python client."""
        version_info = self.spec_loader.get_version_info()
        print(f"Generating strongly-typed Python client for {self.service_name}...")
        print(f"OpenAPI version: {version_info['exact_version']} (family: {version_info['version_family']})")
        
        # Create directory structure
        self._create_directories()
        
        # Generate models
        schemas = self.spec_loader.get_schemas()
        if schemas:
            model_generator = ModelGenerator(schemas, self.service_dir)
            model_generator.generate_models()
        
        # Generate API client using version-specific generator
        paths = self.spec_loader.get_paths()
        api_generator = self._select_api_generator(paths, schemas)
        api_generator.generate_api_client()
        
        # Generate main package __init__.py
        self._generate_main_init()
        
        print(f"✅ Client generated successfully in {self.service_dir}")
        
    def _create_directories(self):
        """Create necessary directory structure."""
        self.service_dir.mkdir(parents=True, exist_ok=True)
        (self.service_dir / "models").mkdir(exist_ok=True)
    
    def _generate_main_init(self):
        """Generate main package __init__.py file."""
        from .utils import to_pascal_case
        
        class_name = f"{to_pascal_case(self.service_name)}APIs"
        
        init_content = f'''"""
{self.service_name} API Client

Auto-generated strongly-typed Python client for {self.service_name}.
"""

from .{class_name} import {class_name}

__all__ = ['{class_name}']
__version__ = '1.0.0'
'''
        
        init_file = self.service_dir / "__init__.py"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)