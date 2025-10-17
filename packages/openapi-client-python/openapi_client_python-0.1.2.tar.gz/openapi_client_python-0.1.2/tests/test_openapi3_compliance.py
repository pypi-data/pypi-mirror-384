"""
Enhanced OpenAPI 3.0 compliance tests and integration tests.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from openapi_client_generator import OpenAPIClientGenerator


@pytest.fixture
def temp_dir():
    """Fixture to create and clean up a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def comprehensive_openapi3_spec():
    """Comprehensive OpenAPI 3.0 specification for testing compliance."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Comprehensive API",
            "version": "1.0.0",
            "description": "A comprehensive test API",
            "termsOfService": "https://example.com/terms",
            "contact": {
                "name": "API Support",
                "url": "https://example.com/support",
                "email": "support@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.example.com/v1",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.example.com/v1",
                "description": "Staging server"
            }
        ],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "summary": "List users",
                    "description": "Get a list of all users",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Maximum number of users to return",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 20
                            }
                        },
                        {
                            "name": "X-Request-ID",
                            "in": "header",
                            "description": "Request ID for tracking",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "format": "uuid"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "headers": {
                                "X-Total-Count": {
                                    "description": "Total number of users",
                                    "schema": {
                                        "type": "integer"
                                    }
                                }
                            },
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/User"
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Error"
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create user",
                    "description": "Create a new user",
                    "tags": ["users"],
                    "requestBody": {
                        "description": "User to create",
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserInput"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            }
                        },
                        "422": {
                            "description": "Validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ValidationError"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/users/{userId}": {
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "description": "User ID",
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "format": "int64"
                        }
                    }
                ],
                "get": {
                    "operationId": "getUserById",
                    "summary": "Get user",
                    "description": "Get a user by ID",
                    "tags": ["users"],
                    "responses": {
                        "200": {
                            "description": "User found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "User not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Error"
                                    }
                                }
                            }
                        }
                    }
                },
                "put": {
                    "operationId": "updateUser",
                    "summary": "Update user",
                    "description": "Update an existing user",
                    "tags": ["users"],
                    "requestBody": {
                        "description": "Updated user data",
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserInput"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User updated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "User not found"
                        }
                    }
                },
                "delete": {
                    "operationId": "deleteUser",
                    "summary": "Delete user",
                    "description": "Delete a user",
                    "tags": ["users"],
                    "responses": {
                        "204": {
                            "description": "User deleted successfully"
                        },
                        "404": {
                            "description": "User not found"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["id", "email", "firstName", "lastName"],
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int64",
                            "description": "User ID",
                            "example": 123
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "User email address",
                            "example": "user@example.com"
                        },
                        "firstName": {
                            "type": "string",
                            "description": "User first name",
                            "example": "John"
                        },
                        "lastName": {
                            "type": "string",
                            "description": "User last name",
                            "example": "Doe"
                        },
                        "age": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 120,
                            "description": "User age",
                            "example": 30
                        },
                        "active": {
                            "type": "boolean",
                            "description": "Whether the user is active",
                            "default": True
                        },
                        "createdAt": {
                            "type": "string",
                            "format": "date-time",
                            "description": "User creation timestamp",
                            "readOnly": True
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "User tags"
                        },
                        "metadata": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": "Additional user metadata"
                        }
                    }
                },
                "UserInput": {
                    "type": "object",
                    "required": ["email", "firstName", "lastName"],
                    "properties": {
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "User email address"
                        },
                        "firstName": {
                            "type": "string",
                            "description": "User first name"
                        },
                        "lastName": {
                            "type": "string",
                            "description": "User last name"
                        },
                        "age": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 120,
                            "description": "User age"
                        },
                        "active": {
                            "type": "boolean",
                            "description": "Whether the user is active",
                            "default": True
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "User tags"
                        },
                        "metadata": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": "Additional user metadata"
                        }
                    }
                },
                "Error": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {
                            "type": "integer",
                            "description": "Error code"
                        },
                        "message": {
                            "type": "string",
                            "description": "Error message"
                        },
                        "details": {
                            "type": "string",
                            "description": "Additional error details"
                        }
                    }
                },
                "ValidationError": {
                    "type": "object",
                    "required": ["message", "errors"],
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Validation error message"
                        },
                        "errors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {
                                        "type": "string"
                                    },
                                    "message": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "parameters": {
                "LimitParam": {
                    "name": "limit",
                    "in": "query",
                    "description": "Maximum number of items to return",
                    "required": False,
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20
                    }
                }
            },
            "responses": {
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/Error"
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "users",
                "description": "User management operations"
            }
        ]
    }


def test_comprehensive_openapi3_compliance(temp_dir, comprehensive_openapi3_spec):
    """Test comprehensive OpenAPI 3.0 compliance with a full spec."""
    # Create temp spec file
    spec_file = temp_dir / "comprehensive_spec.json"
    with open(spec_file, 'w') as f:
        json.dump(comprehensive_openapi3_spec, f)
    
    output_dir = temp_dir / "output"
    
    # Generate client
    generator = OpenAPIClientGenerator(str(spec_file), str(output_dir), "comprehensive")
    generator.generate_client()
    
    # Verify structure was created
    service_dir = output_dir / "comprehensive"
    assert service_dir.exists()
    
    # Check for main API file
    api_file = service_dir / "ComprehensiveAPIs.py"
    assert api_file.exists()
    
    # Check for models directory
    models_dir = service_dir / "models"
    assert models_dir.exists()
    
    # Check for model files
    user_model = models_dir / "User.py"
    user_input_model = models_dir / "UserInput.py"
    error_model = models_dir / "Error.py"
    validation_error_model = models_dir / "ValidationError.py"
    
    assert user_model.exists()
    assert user_input_model.exists()
    assert error_model.exists()
    assert validation_error_model.exists()


def test_openapi3_required_fields(temp_dir):
    """Test that required OpenAPI 3.0 fields are properly handled."""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Required Fields Test",
            "version": "1.0.0"
        },
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        }
    }
    
    spec_file = temp_dir / "required_spec.json"
    with open(spec_file, 'w') as f:
        json.dump(spec, f)
    
    output_dir = temp_dir / "output"
    
    # Should not raise an error with minimal required fields
    generator = OpenAPIClientGenerator(str(spec_file), str(output_dir), "required_test")
    generator.generate_client()
    
    assert (output_dir / "required_test").exists()


def test_openapi3_parameter_types(temp_dir):
    """Test OpenAPI 3.0 parameter type handling."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Parameter Types Test", "version": "1.0.0"},
        "paths": {
            "/test/{id}": {
                "get": {
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "format": "int64"}
                        },
                        {
                            "name": "filter",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["active", "inactive"]}
                        },
                        {
                            "name": "X-API-Key",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    }
    
    spec_file = temp_dir / "param_types_spec.json"
    with open(spec_file, 'w') as f:
        json.dump(spec, f)
    
    output_dir = temp_dir / "output"
    
    generator = OpenAPIClientGenerator(str(spec_file), str(output_dir), "param_test")
    generator.generate_client()
    
    # Check that API file was generated with proper parameter handling
    api_file = output_dir / "param_test" / "ParamTestAPIs.py"
    assert api_file.exists()
    
    with open(api_file, 'r') as f:
        content = f.read()
        # Should have proper parameter types
        assert 'id: int' in content
        assert 'filter: str' in content or 'filter: Optional[str]' in content
        assert 'x_api_key: str' in content


def test_openapi3_content_types(temp_dir):
    """Test OpenAPI 3.0 content type handling."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Content Types Test", "version": "1.0.0"},
        "paths": {
            "/upload": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"}
                                    }
                                }
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    }
    
    spec_file = temp_dir / "content_types_spec.json"
    with open(spec_file, 'w') as f:
        json.dump(spec, f)
    
    output_dir = temp_dir / "output"
    
    generator = OpenAPIClientGenerator(str(spec_file), str(output_dir), "content_test")
    generator.generate_client()
    
    assert (output_dir / "content_test").exists()


def test_openapi3_components_schemas(temp_dir):
    """Test OpenAPI 3.0 components/schemas handling."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Components Test", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Item"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Item": {
                    "type": "object",
                    "required": ["id", "name"],
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "price": {"type": "number", "format": "float"},
                        "available": {"type": "boolean", "default": True}
                    }
                }
            }
        }
    }
    
    spec_file = temp_dir / "components_spec.json"
    with open(spec_file, 'w') as f:
        json.dump(spec, f)
    
    output_dir = temp_dir / "output"
    
    generator = OpenAPIClientGenerator(str(spec_file), str(output_dir), "components_test")
    generator.generate_client()
    
    # Check that model was generated
    item_model = output_dir / "components_test" / "models" / "Item.py"
    assert item_model.exists()
    
    with open(item_model, 'r') as f:
        content = f.read()
        # Should have all properties
        assert 'def id(self)' in content
        assert 'def name(self)' in content
        assert 'def description(self)' in content
        assert 'def price(self)' in content
        assert 'def available(self)' in content