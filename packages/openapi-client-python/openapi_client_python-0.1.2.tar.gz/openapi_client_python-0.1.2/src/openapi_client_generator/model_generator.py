"""
Model generator for OpenAPI/Swagger specifications.
"""

from typing import Dict, Any, List
from pathlib import Path
from .utils import sanitize_model_name, sanitize_python_identifier, to_snake_case, get_python_type


class ModelGenerator:
    """Generates strongly-typed model classes from schema definitions."""
    
    def __init__(self, schemas: Dict[str, Any], output_dir: Path):
        """Initialize the model generator."""
        self.schemas = schemas
        self.models_dir = output_dir / "models"
        
    def generate_models(self):
        """Generate all model classes."""
        # Create models directory
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate each model
        for model_name, model_def in self.schemas.items():
            self._generate_model_class(model_name, model_def)
        
        # Generate models __init__.py
        self._generate_models_init()
    
    def _generate_model_class(self, model_name: str, model_def: Dict[str, Any]):
        """Generate a single strongly-typed model class."""
        # Sanitize model name for file and class names
        sanitized_name = sanitize_model_name(model_name)
        file_path = self.models_dir / f"{sanitized_name}.py"
        
        # Extract properties
        properties = model_def.get('properties', {})
        required = model_def.get('required', [])
        
        content = self._generate_model_content(sanitized_name, model_name, properties, required)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_model_content(self, class_name: str, original_name: str, 
                               properties: Dict[str, Any], required: List[str]) -> str:
        """Generate the content for a model class."""
        imports = """from __future__ import annotations

import json
from typing import List, Union, Optional, Dict, Any"""
        
        class_definition = f"""


class {class_name}:
    \"\"\"
    Strongly-typed model class for {original_name}
    
    Generated from OpenAPI/Swagger specification
    \"\"\"

    def __init__(self, data: Union[Dict[str, Any], None] = None):
        self._data = data or {{}}

{self._generate_model_properties(properties, required)}

    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert model to dictionary with nested object support\"\"\"
        result = {{}}
        for key, value in self._data.items():
            if hasattr(value, 'to_dict'):
                # Handle nested model objects
                result[key] = value.to_dict()
            elif isinstance(value, list):
                # Handle lists that might contain model objects
                result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
            else:
                result[key] = value
        return result

    def to_json(self) -> str:
        \"\"\"Convert model to JSON string\"\"\"
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> {class_name}:
        \"\"\"Create model from dictionary\"\"\"
        return cls(data)

    @classmethod
    def from_json(cls, json_str: str) -> {class_name}:
        \"\"\"Create model from JSON string\"\"\"
        return cls(json.loads(json_str))"""
        
        return imports + class_definition
    
    def _generate_model_properties(self, properties: Dict[str, Any], required: List[str]) -> str:
        """Generate property getters and setters for a model."""
        prop_code = []
        
        for prop_name, prop_def in properties.items():
            prop_type = get_python_type(prop_def)
            is_required = prop_name in required
            
            # Sanitize property name to avoid Python keywords
            python_prop_name = sanitize_python_identifier(to_snake_case(prop_name))
            
            # Property getter
            prop_code.append(f"""    @property
    def {python_prop_name}(self) -> {prop_type}:
        \"\"\"Get {prop_name}\"\"\"
        return self._data.get("{prop_name}")""")
            
            # Property setter
            prop_code.append(f"""    @{python_prop_name}.setter
    def {python_prop_name}(self, value: {prop_type}):
        \"\"\"Set {prop_name}\"\"\"
        self._data["{prop_name}"] = value""")
            
            prop_code.append("")
        
        return "\n".join(prop_code)
    
    def _generate_models_init(self):
        """Generate __init__.py file for models package."""
        init_content = "# Generated strongly-typed model classes\n\n"
        
        # Import all models
        for model_name in self.schemas.keys():
            sanitized_name = sanitize_model_name(model_name)
            init_content += f"from .{sanitized_name} import {sanitized_name}\n"
        
        # Add __all__ list
        model_names = [sanitize_model_name(name) for name in self.schemas.keys()]
        init_content += f"\n__all__ = {model_names}\n"
        
        models_init = self.models_dir / "__init__.py"
        with open(models_init, 'w', encoding='utf-8') as f:
            f.write(init_content)