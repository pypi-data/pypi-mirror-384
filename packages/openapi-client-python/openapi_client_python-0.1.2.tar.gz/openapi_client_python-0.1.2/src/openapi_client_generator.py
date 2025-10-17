#!/usr/bin/env python3
"""
OpenAPI Python Client Generator with Strong Typing (DEPRECATED)

⚠️ DEPRECATED: This monolithic file has been refactored into smaller, maintainable modules.
Use the new modular structure in the `openapi_client_generator` package instead.

For CLI usage, use: python src/main.py
For programmatic usage, import from: openapi_client_generator

This file is kept for backward compatibility but will be removed in a future version.
"""

import warnings
from openapi_client_generator import OpenAPIClientGenerator

# Issue deprecation warning
warnings.warn(
    "The monolithic openapi_client_generator.py file is deprecated. "
    "Please use the new modular structure: `from openapi_client_generator import OpenAPIClientGenerator`",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
__all__ = ["OpenAPIClientGenerator"]


def main():
    """Deprecated main function - use src/main.py instead."""
    warnings.warn(
        "Direct execution of this file is deprecated. Use: python src/main.py",
        DeprecationWarning,
        stacklevel=2
    )
    
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Generate strongly-typed Python client from OpenAPI/Swagger specification')
    parser.add_argument('--spec', required=True, help='Path to OpenAPI/Swagger specification file')
    parser.add_argument('--output', required=True, help='Output directory for generated client')
    parser.add_argument('--service-name', required=True, help='Service name for the generated client')
    
    args = parser.parse_args()
    
    try:
        generator = OpenAPIClientGenerator(args.spec, args.output, args.service_name)
        generator.generate_client()
        print("✅ Strongly-typed client generation completed successfully!")
        print("⚠️  Note: Please migrate to using 'python src/main.py' instead of this deprecated file.")
    except Exception as e:
        print(f"❌ Error generating client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()