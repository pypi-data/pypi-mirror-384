"""
Command line interface for the OpenAPI client generator.
"""

import argparse
import sys
from .generator import OpenAPIClientGenerator


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='openapi-client-generator',
        description='Generate strongly-typed Python client from OpenAPI/Swagger specification'
    )
    parser.add_argument(
        '--spec', 
        required=True, 
        help='Path to OpenAPI/Swagger specification file'
    )
    parser.add_argument(
        '--output', 
        required=True, 
        help='Output directory for generated client'
    )
    parser.add_argument(
        '--service-name', 
        required=True, 
        help='Service name for the generated client'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
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