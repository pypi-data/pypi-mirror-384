"""
Specification loader for OpenAPI/Swagger files.
"""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
import re


class SpecLoader:
    """Loads and validates OpenAPI/Swagger specifications."""
    
    # Version compatibility mapping
    VERSION_COMPATIBILITY = {
        '2.0': 'swagger2',
        '3.0.0': 'openapi3',
        '3.0.1': 'openapi3',
        '3.0.2': 'openapi3',
        '3.0.3': 'openapi3',
        '3.0.4': 'openapi3',
        '3.1.0': 'openapi31',
        '3.1.1': 'openapi31',
        '3.1.2': 'openapi31',
        '3.2.0': 'openapi32'
    }
    
    def __init__(self, spec_file: str):
        """Initialize with specification file path."""
        self.spec_file = spec_file
        self.spec_data = self._load_spec()
        self.version, self.version_family = self._detect_spec_version()
        # Legacy compatibility property
        self.is_openapi3 = self.version_family.startswith('openapi')
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load and parse the OpenAPI/Swagger specification."""
        try:
            with open(self.spec_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load spec file {self.spec_file}: {e}")
    
    def _detect_spec_version(self) -> Tuple[str, str]:
        """Detect the exact OpenAPI/Swagger version and determine compatibility family.
        
        Returns:
            Tuple of (exact_version, version_family)
            version_family is one of: 'swagger2', 'openapi3', 'openapi31', 'openapi32'
        """
        if 'openapi' in self.spec_data:
            version_str = str(self.spec_data['openapi'])
            # Normalize version string (handle cases like "3.0" vs "3.0.0")
            if re.match(r'^3\.[0-4]$', version_str):
                version_str += '.0'
            
            if version_str in self.VERSION_COMPATIBILITY:
                return version_str, self.VERSION_COMPATIBILITY[version_str]
            else:
                # Default to closest supported version
                if version_str.startswith('3.2'):
                    return version_str, 'openapi32'
                elif version_str.startswith('3.1'):
                    return version_str, 'openapi31'
                elif version_str.startswith('3.0'):
                    return version_str, 'openapi3'
                else:
                    raise ValueError(f"Unsupported OpenAPI version: {version_str}")
        elif 'swagger' in self.spec_data:
            version_str = str(self.spec_data['swagger'])
            if version_str == '2.0':
                return version_str, 'swagger2'
            else:
                raise ValueError(f"Unsupported Swagger version: {version_str}")
        else:
            raise ValueError("Invalid specification: missing 'openapi' or 'swagger' field")
    
    def get_version_info(self) -> Dict[str, str]:
        """Get detailed version information."""
        return {
            'exact_version': self.version,
            'version_family': self.version_family,
            'is_swagger2': self.version_family == 'swagger2',
            'is_openapi3': self.version_family == 'openapi3',
            'is_openapi31': self.version_family == 'openapi31',
            'is_openapi32': self.version_family == 'openapi32',
            'supports_webhooks': self.version_family in ['openapi31', 'openapi32'],
            'supports_json_schema_draft_2020_12': self.version_family in ['openapi31', 'openapi32'],
            'supports_discriminator_mapping': self.version_family != 'swagger2'
        }
    
    def get_schemas(self) -> Dict[str, Any]:
        """Get schema definitions from the specification."""
        if self.is_openapi3:
            return self.spec_data.get('components', {}).get('schemas', {})
        else:
            return self.spec_data.get('definitions', {})
    
    def get_paths(self) -> Dict[str, Any]:
        """Get path definitions from the specification."""
        return self.spec_data.get('paths', {})
    
    def get_info(self) -> Dict[str, Any]:
        """Get API info from the specification."""
        return self.spec_data.get('info', {})
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """Get server definitions."""
        if self.is_openapi3:
            return self.spec_data.get('servers', [])
        else:
            # Convert Swagger 2.0 host/basePath to server format
            host = self.spec_data.get('host', '')
            base_path = self.spec_data.get('basePath', '')
            schemes = self.spec_data.get('schemes', ['https'])
            
            if host:
                servers = []
                for scheme in schemes:
                    url = f"{scheme}://{host}{base_path}"
                    servers.append({'url': url})
                return servers
            return []
    
    def get_base_path(self) -> str:
        """Get base path (Swagger 2.0 only)."""
        if not self.is_openapi3:
            return self.spec_data.get('basePath', '')
        return ''