"""
Unit tests for the CLI module.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from openapi_client_generator.cli import main


@pytest.fixture
def temp_spec_file():
    """Create a temporary OpenAPI spec file."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "getTest",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(spec, f)
        return f.name


@pytest.fixture 
def temp_output_dir():
    """Create a temporary output directory."""
    return tempfile.mkdtemp()


def test_cli_help():
    """Test CLI help output."""
    with patch('sys.argv', ['openapi-client-generator', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_version():
    """Test CLI version output."""
    with patch('sys.argv', ['openapi-client-generator', '--version']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_missing_required_args():
    """Test CLI with missing required arguments."""
    with patch('sys.argv', ['openapi-client-generator']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0


@patch('builtins.print')
def test_cli_successful_generation(mock_print, temp_spec_file, temp_output_dir):
    """Test successful client generation via CLI."""
    args = [
        'openapi-client-generator',
        '--spec', temp_spec_file,
        '--output', temp_output_dir,
        '--service-name', 'test_service'
    ]
    
    with patch('sys.argv', args):
        with patch('openapi_client_generator.cli.OpenAPIClientGenerator') as mock_generator:
            mock_instance = MagicMock()
            mock_generator.return_value = mock_instance
            
            main()
            
            # Verify generator was called correctly
            mock_generator.assert_called_once_with(temp_spec_file, temp_output_dir, 'test_service')
            mock_instance.generate_client.assert_called_once()
            
            # Verify success message was printed
            mock_print.assert_called_with("✅ Strongly-typed client generation completed successfully!")


@patch('builtins.print')
@patch('sys.exit')
def test_cli_generation_failure(mock_exit, mock_print, temp_spec_file, temp_output_dir):
    """Test CLI handling of generation failure."""
    args = [
        'openapi-client-generator',
        '--spec', temp_spec_file,
        '--output', temp_output_dir,
        '--service-name', 'test_service'
    ]
    
    with patch('sys.argv', args):
        with patch('openapi_client_generator.cli.OpenAPIClientGenerator') as mock_generator:
            mock_generator.side_effect = Exception("Test error")
            
            main()
            
            # Verify error message was printed
            mock_print.assert_called_with("❌ Error generating client: Test error")
            # Verify exit was called with error code
            mock_exit.assert_called_with(1)


def test_cli_all_arguments(temp_spec_file, temp_output_dir):
    """Test CLI with all arguments provided."""
    args = [
        'openapi-client-generator',
        '--spec', temp_spec_file,
        '--output', temp_output_dir,
        '--service-name', 'test_service'
    ]
    
    with patch('sys.argv', args):
        with patch('openapi_client_generator.cli.OpenAPIClientGenerator') as mock_generator:
            mock_instance = MagicMock()
            mock_generator.return_value = mock_instance
            
            main()
            
            # Verify all arguments were passed correctly
            mock_generator.assert_called_once_with(temp_spec_file, temp_output_dir, 'test_service')


def test_cli_invalid_spec_file():
    """Test CLI with invalid spec file."""
    args = [
        'openapi-client-generator',
        '--spec', '/nonexistent/file.json',
        '--output', '/tmp/test',
        '--service-name', 'test_service'
    ]
    
    with patch('sys.argv', args):
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                main()
                
                # Should print error and exit with code 1
                assert mock_print.called
                mock_exit.assert_called_with(1)