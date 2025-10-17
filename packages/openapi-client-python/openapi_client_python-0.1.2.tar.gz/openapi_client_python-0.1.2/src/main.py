#!/usr/bin/env python3
"""
OpenAPI Python Client Generator with Strong Typing

Generates strongly-typed Python clients from OpenAPI 3.0 or Swagger 2.0 specifications.

Usage:
    python main.py --spec <spec_file> --output <output_dir> --service-name <name>
"""

import argparse
import sys
from openapi_client_generator import OpenAPIClientGenerator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate strongly-typed Python client from OpenAPI/Swagger specification'
    )
    parser.add_argument('--spec', required=True, help='Path to OpenAPI/Swagger specification file')
    parser.add_argument('--output', required=True, help='Output directory for generated client')
    parser.add_argument('--service-name', required=True, help='Service name for the generated client')
    
    args = parser.parse_args()
    
    try:
        generator = OpenAPIClientGenerator(args.spec, args.output, args.service_name)
        generator.generate_client()
        print("✅ Strongly-typed client generation completed successfully!")
    except Exception as e:
        print(f"❌ Error generating client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()