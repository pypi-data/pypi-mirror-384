# OpenAPI Python Client Generator

A powerful tool that generates strongly-typed Python clients from OpenAPI 3.0 and Swagger 2.0 specifications. This generator creates clean, maintainable code with full type annotations, automatic model serialization, and comprehensive error handling.

## Features

- **Strong Typing**: Full type annotations for all generated code
- **OpenAPI 3.0 & Swagger 2.0 Support**: Works with both specification formats
- **Model Generation**: Automatically generates data models with properties and validation
- **API Client Generation**: Creates method stubs for all API endpoints
- **Serialization Support**: Built-in JSON serialization/deserialization
- **Error Handling**: Robust error handling with logging
- **Clean Code**: Well-structured, readable generated code
- **Test Coverage**: Comprehensive unit tests

## Installation

### From PyPI (Recommended)

```bash
pip install openapi-client-python
```

### From Source

```bash
git clone https://github.com/autoocto/openapi-client-python.git
cd openapi-client-python
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

Generate a client from an OpenAPI specification:

```bash
openapi-client-python --spec samples/pet_store.json --output ./generated --service-name petstore
```

### Command Line Options

- `--spec`: Path to your OpenAPI/Swagger specification file (JSON format)
- `--output`: Output directory for the generated client
- `--service-name`: Name for your service (used for class and directory names)

### Getting Help

To see all available options:

```bash
openapi-client-python --help
```

### Example

```bash
# Generate from the included Pet Store example
openapi-client-python --spec samples/pet_store.json --output ./my_clients --service-name pet_store

# This creates:
# ./my_clients/pet_store/
#   ├── __init__.py
#   ├── PetStoreAPIs.py
#   └── models/
#       ├── __init__.py
#       ├── Pet.py
#       ├── User.py
#       └── Order.py
```

## Using the Generated Client

Once generated, you can use your client like this:

```python
from my_clients.pet_store import PetStoreAPIs
from my_clients.pet_store.models.Pet import Pet

# Initialize the client
client = PetStoreAPIs(
    base_url="https://petstore.swagger.io/v2",
    auth_token="your-api-token"
)

# Create a new pet
new_pet = Pet({
    "id": 123,
    "name": "Fluffy",
    "status": "available"
})

# Use the API
created_pet = client.post_pet(payload=new_pet)
print(f"Created pet: {created_pet.name}")

# Get pets by status
available_pets = client.get_pets_find_by_status(status="available")
for pet in available_pets:
    print(f"Pet: {pet.name} (ID: {pet.id})")
```

## Generated Code Structure

The generator creates a well-organized structure:

```
your_service/
├── __init__.py                 # Main package exports
├── YourServiceAPIs.py          # Main API client class
└── models/                     # Data models
    ├── __init__.py             # Model exports
    ├── ModelName.py            # Individual model classes
    └── ...
```

### API Client Features

The generated API client includes:

- **Authentication Support**: Bearer token authentication
- **Base URL Management**: Configurable base URL
- **Request/Response Handling**: Automatic serialization/deserialization
- **Error Handling**: Comprehensive error handling with logging
- **Type Safety**: Full type annotations for all methods

### Model Features

Generated models include:

- **Property Access**: Clean property getters/setters
- **Type Annotations**: Full typing support
- **Serialization**: `to_dict()`, `to_json()`, `from_dict()`, `from_json()` methods
- **Validation**: Basic type validation

## Development

### Project Structure

```
openapi-client-python/
├── src/
│   ├── main.py                           # CLI entry point
│   └── openapi_client_generator/         # Main package
│       ├── __init__.py                   # Package exports
│       ├── generator.py                  # Main orchestrator
│       ├── spec_loader.py                # Specification loader
│       ├── model_generator.py            # Model generation
│       ├── api_generator.py              # API client generation
│       └── utils.py                      # Utility functions
├── tests/                                # Unit tests
│   ├── __init__.py                       # Test runner
│   ├── test_spec_loader.py               # Spec loader tests
│   ├── test_model_generator.py           # Model generator tests
│   ├── test_api_generator.py             # API generator tests
│   ├── test_generator.py                 # Main generator tests
│   └── test_utils.py                     # Utility tests
├── samples/                              # Example specifications
├── requirements.txt                      # Dependencies
└── README.md                             # This file
```

### Running Tests

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/openapi_client_generator

# Run specific test module
python -m pytest tests/test_generator.py -v
```

### Dependencies

- `requests`: HTTP client library
- Standard library modules: `json`, `pathlib`, `typing`, `re`, `argparse`

## Supported Specifications

### OpenAPI 3.0
- ✅ Path operations (GET, POST, PUT, DELETE, PATCH)
- ✅ Request/response models
- ✅ Path parameters
- ✅ Query parameters
- ✅ Request bodies
- ✅ Schema references (`#/components/schemas/`)
- ✅ Array responses
- ✅ Nested models

### Swagger 2.0
- ✅ Path operations
- ✅ Model definitions
- ✅ Path parameters
- ✅ Query parameters
- ✅ Body parameters
- ✅ Schema references (`#/definitions/`)
- ✅ Array responses

## Examples

Check the `samples/` directory for example specifications:

- `pet_store.json`: OpenAPI 3.0 Pet Store example
- `pet_store_swagger.json`: Swagger 2.0 Pet Store example
- `simple_api_overview.json`: Simple API example

### Generate from Pet Store

```bash
# OpenAPI 3.0 version
openapi-client-python --spec samples/pet_store.json --output ./clients --service-name petstore

# Swagger 2.0 version
openapi-client-python --spec samples/pet_store_swagger.json --output ./clients --service-name petstore_v2
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python -m pytest tests/`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0
- Initial release
- OpenAPI 3.0 and Swagger 2.0 support
- Strongly-typed model generation
- API client generation
- Comprehensive test suite
- Clean, maintainable code structure
