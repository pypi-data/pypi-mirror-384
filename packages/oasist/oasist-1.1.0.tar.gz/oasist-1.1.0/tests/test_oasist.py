"""
Comprehensive tests for OASist package
Tests all functionality, edge cases, error handling, and integrations.
"""
import pytest
import sys
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, Mock, call
from io import StringIO
import requests

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from oasist.oasist import (
    substitute_env_vars, substitute_recursive, temp_file,
    ServiceConfig, SchemaProcessor, ClientGenerator,
    ConfigLoader, parse_args, main,
    EXIT_SUCCESS, EXIT_ERROR,
    JSONParser, YAMLParser, GeneratorRunner, CodeFormatter,
    ListCommand, GenerateCommand, GenerateAllCommand, InfoCommand,
    CommandRegistry, HelpDisplay, HTTP_TIMEOUT
)


# ============================================================================
# Test Environment Variable Substitution
# ============================================================================
class TestEnvSubstitution:
    """Tests for environment variable substitution."""
    
    def test_substitute_env_vars_with_existing_var(self, monkeypatch):
        """Test substitution with existing environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = substitute_env_vars("URL is ${TEST_VAR}")
        assert result == "URL is test_value"
    
    def test_substitute_env_vars_with_default(self):
        """Test substitution with default value."""
        result = substitute_env_vars("URL is ${NONEXISTENT:default_value}")
        assert result == "URL is default_value"
    
    def test_substitute_env_vars_missing_no_default(self):
        """Test substitution with missing var and no default."""
        result = substitute_env_vars("URL is ${NONEXISTENT_VAR}")
        assert result == "URL is ${NONEXISTENT_VAR}"
    
    def test_substitute_recursive_dict(self, monkeypatch):
        """Test recursive substitution in dictionaries."""
        monkeypatch.setenv("HOST", "localhost")
        data = {"url": "http://${HOST}/api", "port": 8080}
        result = substitute_recursive(data)
        assert result["url"] == "http://localhost/api"
        assert result["port"] == 8080
    
    def test_substitute_recursive_list(self, monkeypatch):
        """Test recursive substitution in lists."""
        monkeypatch.setenv("ENV", "prod")
        data = ["${ENV}", "test", {"env": "${ENV}"}]
        result = substitute_recursive(data)
        assert result[0] == "prod"
        assert result[2]["env"] == "prod"


# ============================================================================
# Test Temporary File Management
# ============================================================================
class TestTempFile:
    """Tests for temporary file context manager."""
    
    def test_temp_file_json(self):
        """Test creating temporary JSON file."""
        data = {"key": "value", "number": 123}
        with temp_file(data, as_json=True) as path:
            assert path.exists()
            assert path.suffix == '.json'
            content = json.loads(path.read_text())
            assert content == data
        assert not path.exists()  # Should be cleaned up
    
    def test_temp_file_yaml(self):
        """Test creating temporary YAML file."""
        data = {"key": "value", "list": [1, 2, 3]}
        with temp_file(data, as_json=False) as path:
            assert path.exists()
            assert path.suffix == '.yaml'
            content = path.read_text()
            assert "key: value" in content
        assert not path.exists()  # Should be cleaned up
    
    def test_temp_file_cleanup_on_exception(self):
        """Test temp file cleanup when exception occurs."""
        data = {"test": "data"}
        path_ref = None
        try:
            with temp_file(data) as path:
                path_ref = path
                raise ValueError("Test exception")
        except ValueError:
            pass
        if path_ref:
            assert not path_ref.exists()  # Should still be cleaned up


# ============================================================================
# Test Service Configuration
# ============================================================================
class TestServiceConfig:
    """Tests for ServiceConfig dataclass."""
    
    def test_valid_config(self):
        """Test creating valid service configuration."""
        config = ServiceConfig(
            name="Test Service",
            schema_url="http://example.com/openapi.json",
            output_dir="test_client"
        )
        assert config.name == "Test Service"
        assert config.package_name == "test_service"
        assert config.base_url == "http://example.com"
    
    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Service name cannot be empty"):
            ServiceConfig(name="", schema_url="http://test.com/api", output_dir="out")
    
    def test_empty_schema_url_raises_error(self):
        """Test that empty schema URL raises ValueError."""
        with pytest.raises(ValueError, match="Schema URL cannot be empty"):
            ServiceConfig(name="Test", schema_url="", output_dir="out")
    
    def test_invalid_url_format_raises_error(self):
        """Test that invalid URL format raises ValueError."""
        with pytest.raises(ValueError, match="must start with http"):
            ServiceConfig(name="Test", schema_url="ftp://test.com", output_dir="out")
    
    def test_path_traversal_protection(self):
        """Test that path traversal is blocked."""
        with pytest.raises(ValueError, match="cannot contain '..'"):
            ServiceConfig(
                name="Test",
                schema_url="http://test.com/api",
                output_dir="../etc/passwd"
            )
    
    def test_absolute_path_protection(self):
        """Test that absolute paths are blocked."""
        with pytest.raises(ValueError, match="must be relative"):
            ServiceConfig(
                name="Test",
                schema_url="http://test.com/api",
                output_dir="/etc/passwd"
            )
    
    def test_base_url_detection_with_api_pattern(self):
        """Test automatic base URL detection with /api/ pattern."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://example.com/api/v1/openapi.json",
            output_dir="test"
        )
        assert config.base_url == "http://example.com"


# ============================================================================
# Test Schema Processor
# ============================================================================
class TestSchemaProcessor:
    """Tests for SchemaProcessor."""
    
    def test_sanitize_security_with_dict(self):
        """Test sanitizing invalid dict security definitions."""
        schema = {
            "paths": {
                "/test": {
                    "get": {
                        "security": {"bearer": {}, "api_key": {}}
                    }
                }
            }
        }
        result = SchemaProcessor.sanitize_security(schema)
        assert isinstance(result["paths"]["/test"]["get"]["security"], list)
        assert len(result["paths"]["/test"]["get"]["security"]) == 2
    
    def test_sanitize_security_preserves_valid_format(self):
        """Test that valid security format is preserved."""
        schema = {
            "paths": {
                "/test": {
                    "get": {
                        "security": [{"bearer": []}]
                    }
                }
            }
        }
        result = SchemaProcessor.sanitize_security(schema)
        assert result["paths"]["/test"]["get"]["security"] == [{"bearer": []}]


# ============================================================================
# Test Client Generator
# ============================================================================
class TestClientGenerator:
    """Tests for ClientGenerator."""
    
    def test_add_service(self):
        """Test adding a service."""
        generator = ClientGenerator()
        config = ServiceConfig(
            name="Test",
            schema_url="http://test.com/api",
            output_dir="test"
        )
        generator.add_service("test", config)
        assert "test" in generator.services
    
    def test_generate_nonexistent_service(self):
        """Test generating nonexistent service returns False."""
        generator = ClientGenerator()
        result = generator.generate("nonexistent")
        assert result is False
    
    def test_list_services_empty(self, capsys):
        """Test listing services when none configured."""
        generator = ClientGenerator()
        generator.list_services()
        captured = capsys.readouterr()
        # Should show "No services configured" message


# ============================================================================
# Test Config Loader
# ============================================================================
class TestConfigLoader:
    """Tests for ConfigLoader."""
    
    def test_load_missing_file(self):
        """Test loading from missing file."""
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, "nonexistent.json")
        assert result is False
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{invalid json}")
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        assert result is False
    
    def test_load_valid_projects_format(self, tmp_path):
        """Test loading valid projects format."""
        config_data = {
            "output_dir": "./test_clients",
            "projects": {
                "test_api": {
                    "input": {"target": "https://t.forbiz.ir//openapi.json"},
                    "output": {
                        "dir": "test_api",
                        "name": "Test API"
                    }
                }
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        assert result is True
        assert "test_api" in generator.services


# ============================================================================
# Test Argument Parsing
# ============================================================================
class TestArgumentParsing:
    """Tests for command line argument parsing."""
    
    def test_parse_args_default(self):
        """Test parsing with default arguments."""
        config, verbose, args = parse_args(["list"])
        assert config == "oasist_config.json"
        assert verbose is False
        assert args == ["list"]
    
    def test_parse_args_with_config(self):
        """Test parsing with config file flag."""
        config, verbose, args = parse_args(["-c", "custom.json", "list"])
        assert config == "custom.json"
        assert args == ["list"]
    
    def test_parse_args_with_verbose(self):
        """Test parsing with verbose flag."""
        config, verbose, args = parse_args(["-v", "generate", "api"])
        assert verbose is True
        assert args == ["generate", "api"]
    
    def test_parse_args_combined_flags(self):
        """Test parsing with multiple flags."""
        config, verbose, args = parse_args(["-v", "-c", "prod.json", "generate-all", "--force"])
        assert verbose is True
        assert config == "prod.json"
        assert args == ["generate-all", "--force"]


# ============================================================================
# Test Main Entry Point
# ============================================================================
class TestMain:
    """Tests for main() entry point."""
    
    @patch('sys.argv', ['oasist', '--version'])
    def test_main_version(self, capsys):
        """Test --version flag."""
        result = main()
        assert result == EXIT_SUCCESS
    
    @patch('sys.argv', ['oasist', '--help'])
    def test_main_help(self):
        """Test --help flag."""
        result = main()
        assert result == EXIT_SUCCESS
    
    @patch('sys.argv', ['oasist'])
    def test_main_no_args(self):
        """Test running without arguments."""
        result = main()
        assert result == EXIT_SUCCESS


# ============================================================================
# Test Package Import
# ============================================================================
class TestPackageImport:
    """Tests for package import functionality."""
    
    def test_import_package(self):
        """Test that the package can be imported."""
        import oasist
        assert hasattr(oasist, 'oasist')

    def test_version_exists(self):
        """Test that version is accessible."""
        from oasist import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_exported_classes(self):
        """Test that main classes are exported."""
        from oasist import ClientGenerator, ServiceConfig
        assert ClientGenerator is not None
        assert ServiceConfig is not None


# ============================================================================
# Test Schema Parsers
# ============================================================================
class TestParsers:
    """Tests for JSON and YAML parsers."""
    
    def test_json_parser_valid(self):
        """Test JSON parser with valid input."""
        parser = JSONParser()
        result = parser.parse('{"key": "value", "number": 42}')
        assert result == {"key": "value", "number": 42}
    
    def test_json_parser_invalid(self):
        """Test JSON parser with invalid input."""
        parser = JSONParser()
        with pytest.raises(json.JSONDecodeError):
            parser.parse('{invalid json}')
    
    def test_yaml_parser_valid(self):
        """Test YAML parser with valid input."""
        parser = YAMLParser()
        result = parser.parse('key: value\nnumber: 42')
        assert result == {"key": "value", "number": 42}
    
    def test_yaml_parser_list(self):
        """Test YAML parser with list."""
        parser = YAMLParser()
        result = parser.parse('- item1\n- item2\n- item3')
        assert result == ["item1", "item2", "item3"]


# ============================================================================
# Test ServiceConfig Advanced
# ============================================================================
class TestServiceConfigAdvanced:
    """Advanced tests for ServiceConfig."""
    
    def test_config_with_custom_package_name(self):
        """Test config with custom package name."""
        config = ServiceConfig(
            name="My Service",
            schema_url="http://test.com/api",
            output_dir="output",
            package_name="custom_pkg"
        )
        assert config.package_name == "custom_pkg"
    
    def test_config_auto_package_name(self):
        """Test automatic package name generation."""
        config = ServiceConfig(
            name="My-Test Service",
            schema_url="http://test.com/api",
            output_dir="output"
        )
        assert config.package_name == "my_test_service"
    
    def test_config_base_url_with_openapi_pattern(self):
        """Test base URL detection with /openapi pattern."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://example.com/openapi/schema.json",
            output_dir="output"
        )
        assert config.base_url == "http://example.com"
    
    def test_config_base_url_with_swagger_pattern(self):
        """Test base URL detection with /swagger pattern."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://example.com/swagger.json",
            output_dir="output"
        )
        assert config.base_url == "http://example.com"
    
    def test_config_custom_base_url(self):
        """Test config with custom base URL."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://schema.com/api",
            output_dir="output",
            base_url="http://custom.com"
        )
        assert config.base_url == "http://custom.com"
        assert config.original_base_url == "http://custom.com"
    
    def test_config_request_params(self):
        """Test config with request parameters."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://test.com/api",
            output_dir="output",
            request_params={"format": "json", "version": "v1"}
        )
        assert config.request_params == {"format": "json", "version": "v1"}
    
    def test_config_request_headers(self):
        """Test config with custom headers."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://test.com/api",
            output_dir="output",
            request_headers={"Authorization": "Bearer token"}
        )
        assert config.request_headers == {"Authorization": "Bearer token"}
    
    def test_config_env_vars_in_headers(self, monkeypatch):
        """Test environment variable substitution in headers."""
        monkeypatch.setenv("API_TOKEN", "secret123")
        config = ServiceConfig(
            name="Test",
            schema_url="http://test.com/api",
            output_dir="output",
            request_headers={"Authorization": "Bearer ${API_TOKEN}"}
        )
        assert config.request_headers["Authorization"] == "Bearer secret123"
    
    def test_config_whitespace_name(self):
        """Test that whitespace-only name raises error."""
        with pytest.raises(ValueError, match="Service name cannot be empty"):
            ServiceConfig(name="   ", schema_url="http://test.com/api", output_dir="out")
    
    def test_config_https_url(self):
        """Test that HTTPS URLs are accepted."""
        config = ServiceConfig(
            name="Test",
            schema_url="https://secure.com/api",
            output_dir="output"
        )
        assert config.schema_url == "https://secure.com/api"
    
    def test_config_format_with_black_default(self):
        """Test that format_with_black defaults to True."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://test.com/api",
            output_dir="output"
        )
        assert config.format_with_black is True
    
    def test_config_format_with_black_disabled(self):
        """Test disabling Black formatting."""
        config = ServiceConfig(
            name="Test",
            schema_url="http://test.com/api",
            output_dir="output",
            format_with_black=False
        )
        assert config.format_with_black is False


# ============================================================================
# Test SchemaProcessor Advanced
# ============================================================================
class TestSchemaProcessorAdvanced:
    """Advanced tests for SchemaProcessor."""
    
    @patch('requests.get')
    def test_fetch_success_json(self, mock_get):
        """Test successful schema fetch as JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"openapi": "3.0.0", "paths": {}}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True)
        assert schema is not None
        assert schema.get("openapi") == "3.0.0"
    
    @patch('requests.get')
    def test_fetch_success_yaml(self, mock_get):
        """Test successful schema fetch as YAML."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'openapi: 3.0.0\npaths: {}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, False)
        assert schema is not None
        assert schema.get("openapi") == "3.0.0"
    
    @patch('requests.get')
    def test_fetch_empty_response(self, mock_get):
        """Test fetch with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True)
        assert schema is None
    
    @patch('requests.get')
    def test_fetch_timeout(self, mock_get):
        """Test fetch with timeout error."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True)
        assert schema is None
    
    @patch('requests.get')
    def test_fetch_connection_error(self, mock_get):
        """Test fetch with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True)
        assert schema is None
    
    @patch('requests.get')
    def test_fetch_http_error(self, mock_get):
        """Test fetch with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True)
        assert schema is None
    
    @patch('requests.get')
    def test_fetch_with_custom_headers(self, mock_get):
        """Test fetch with custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"openapi": "3.0.0", "paths": {}}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        custom_headers = {"Authorization": "Bearer token"}
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True, custom_headers)
        
        assert schema is not None
        # Verify custom headers were passed
        call_args = mock_get.call_args
        assert "Authorization" in call_args[1]["headers"]
    
    @patch('requests.get')
    def test_fetch_json_fallback_to_yaml(self, mock_get):
        """Test JSON fetch falling back to YAML parsing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'openapi: 3.0.0\npaths: {}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Request JSON but get YAML response
        schema = SchemaProcessor.fetch("http://test.com/openapi.json", {}, True)
        assert schema is not None
        assert schema.get("openapi") == "3.0.0"
    
    @patch('requests.get')
    def test_fetch_invalid_schema_structure(self, mock_get):
        """Test fetch with invalid schema structure."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"invalid": "schema"}'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        schema = SchemaProcessor.fetch("http://test.com/api", {}, True)
        assert schema is not None  # Returns schema but logs warnings
    
    def test_sanitize_security_nested(self):
        """Test sanitizing nested security definitions."""
        schema = {
            "paths": {
                "/test1": {
                    "get": {"security": {"bearer": {}}},
                    "post": {"security": [{"api_key": []}]}
                },
                "/test2": {
                    "delete": {"security": {"oauth2": {}}}
                }
            }
        }
        result = SchemaProcessor.sanitize_security(schema)
        assert isinstance(result["paths"]["/test1"]["get"]["security"], list)
        assert isinstance(result["paths"]["/test1"]["post"]["security"], list)
        assert isinstance(result["paths"]["/test2"]["delete"]["security"], list)
    
    def test_sanitize_security_empty_dict(self):
        """Test sanitizing empty security dict."""
        schema = {
            "paths": {
                "/test": {
                    "get": {"security": {}}
                }
            }
        }
        result = SchemaProcessor.sanitize_security(schema)
        assert result["paths"]["/test"]["get"]["security"] == []
    
    def test_sanitize_security_no_paths(self):
        """Test sanitizing schema without paths."""
        schema = {"openapi": "3.0.0"}
        result = SchemaProcessor.sanitize_security(schema)
        assert result == schema


# ============================================================================
# Test CodeFormatter
# ============================================================================
class TestCodeFormatter:
    """Tests for CodeFormatter."""
    
    def test_is_black_available(self):
        """Test checking if Black is available."""
        # This test will pass or fail based on whether Black is installed
        result = CodeFormatter.is_black_available()
        assert isinstance(result, bool)
    
    @patch('subprocess.run')
    def test_is_black_available_mock(self, mock_run):
        """Test Black availability check with mock."""
        mock_run.return_value = Mock(returncode=0)
        assert CodeFormatter.is_black_available() is True
        
        mock_run.return_value = Mock(returncode=1)
        assert CodeFormatter.is_black_available() is False
    
    @patch('subprocess.run')
    def test_format_directory_success(self, mock_run, tmp_path):
        """Test successful directory formatting."""
        # Mock Black availability check
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")
        
        test_dir = tmp_path / "test_code"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("def   foo( ):pass")
        
        result = CodeFormatter.format_directory(test_dir)
        assert result is True
    
    @patch.object(CodeFormatter, 'is_black_available', return_value=False)
    def test_format_directory_black_not_available(self, mock_black, tmp_path):
        """Test formatting when Black is not installed."""
        test_dir = tmp_path / "test_code"
        test_dir.mkdir()
        
        result = CodeFormatter.format_directory(test_dir)
        assert result is True  # Should return True (skip formatting, not an error)
    
    def test_format_directory_nonexistent(self):
        """Test formatting nonexistent directory."""
        result = CodeFormatter.format_directory(Path("/nonexistent/path"))
        assert result is False
    
    @patch('subprocess.run')
    @patch.object(CodeFormatter, 'is_black_available', return_value=True)
    def test_format_directory_timeout(self, mock_black, mock_run, tmp_path):
        """Test formatting with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=['black'], timeout=60)
        
        test_dir = tmp_path / "test_code"
        test_dir.mkdir()
        
        result = CodeFormatter.format_directory(test_dir)
        assert result is False


# ============================================================================
# Test GeneratorRunner
# ============================================================================
class TestGeneratorRunner:
    """Tests for GeneratorRunner."""
    
    @patch('subprocess.run')
    def test_run_success(self, mock_run, tmp_path):
        """Test successful generator run."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="Success")
        
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output"
        
        result = GeneratorRunner.run(schema_path, output_path, False)
        assert result is True
    
    @patch('subprocess.run')
    def test_run_with_hooks_disabled(self, mock_run, tmp_path):
        """Test generator run with hooks disabled."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")
        
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output"
        
        result = GeneratorRunner.run(schema_path, output_path, True)
        assert result is True
    
    @patch('subprocess.run')
    def test_run_with_hooks_disabled_simple(self, mock_run, tmp_path):
        """Test running with hooks disabled (simplified approach)."""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="Success")
        
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output"
        
        result = GeneratorRunner.run(schema_path, output_path, True)
        assert result is True
        assert mock_run.call_count == 1
    
    @patch('subprocess.run')
    def test_run_retry_on_ruff_failure(self, mock_run, tmp_path):
        """Test retry when ruff fails."""
        mock_run.side_effect = [
            Mock(returncode=1, stderr="ruff failed", stdout=""),
            Mock(returncode=0, stderr="", stdout="Success")
        ]
        
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output"
        
        result = GeneratorRunner.run(schema_path, output_path, False)
        assert result is True
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_run_failure(self, mock_run, tmp_path):
        """Test generator failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Error occurred", stdout="")
        
        schema_path = tmp_path / "schema.json"
        output_path = tmp_path / "output"
        
        result = GeneratorRunner.run(schema_path, output_path, False)
        assert result is False


# ============================================================================
# Test ClientGenerator Advanced
# ============================================================================
class TestClientGeneratorAdvanced:
    """Advanced tests for ClientGenerator."""
    
    def test_add_multiple_services(self):
        """Test adding multiple services."""
        generator = ClientGenerator()
        config1 = ServiceConfig("Service1", "http://test1.com/api", "out1")
        config2 = ServiceConfig("Service2", "http://test2.com/api", "out2")
        
        generator.add_service("svc1", config1)
        generator.add_service("svc2", config2)
        
        assert len(generator.services) == 2
        assert "svc1" in generator.services
        assert "svc2" in generator.services
    
    @patch.object(SchemaProcessor, 'fetch', return_value={"openapi": "3.0.0", "paths": {}})
    @patch.object(SchemaProcessor, 'sanitize_security')
    @patch.object(GeneratorRunner, 'run', return_value=True)
    def test_generate_success(self, mock_run, mock_sanitize, mock_fetch, tmp_path):
        """Test successful client generation."""
        mock_sanitize.side_effect = lambda x: x
        
        generator = ClientGenerator(output_base=tmp_path)
        config = ServiceConfig("Test", "http://test.com/api", "test_output")
        generator.add_service("test", config)
        
        result = generator.generate("test", force=False)
        assert result is True
    
    @patch.object(SchemaProcessor, 'fetch', return_value=None)
    def test_generate_schema_fetch_failure(self, mock_fetch, tmp_path):
        """Test generation with schema fetch failure."""
        generator = ClientGenerator(output_base=tmp_path)
        config = ServiceConfig("Test", "http://test.com/api", "test_output")
        generator.add_service("test", config)
        
        result = generator.generate("test")
        assert result is False
    
    @patch.object(SchemaProcessor, 'fetch', return_value={"openapi": "3.0.0", "paths": {}})
    @patch.object(SchemaProcessor, 'sanitize_security')
    @patch.object(GeneratorRunner, 'run', return_value=False)
    def test_generate_runner_failure(self, mock_run, mock_sanitize, mock_fetch, tmp_path):
        """Test generation with runner failure."""
        mock_sanitize.side_effect = lambda x: x
        
        generator = ClientGenerator(output_base=tmp_path)
        config = ServiceConfig("Test", "http://test.com/api", "test_output")
        generator.add_service("test", config)
        
        result = generator.generate("test")
        assert result is False
    
    def test_generate_existing_without_force(self, tmp_path):
        """Test generation with existing client without force flag."""
        generator = ClientGenerator(output_base=tmp_path)
        config = ServiceConfig("Test", "http://test.com/api", "test_output")
        generator.add_service("test", config)
        
        # Create existing output directory
        output_dir = tmp_path / "test_output"
        output_dir.mkdir(parents=True)
        
        result = generator.generate("test", force=False)
        assert result is False
    
    @patch.object(SchemaProcessor, 'fetch', return_value={"openapi": "3.0.0", "paths": {}})
    @patch.object(SchemaProcessor, 'sanitize_security')
    @patch.object(GeneratorRunner, 'run', return_value=True)
    def test_generate_existing_with_force(self, mock_run, mock_sanitize, mock_fetch, tmp_path):
        """Test generation with existing client and force flag."""
        mock_sanitize.side_effect = lambda x: x
        
        generator = ClientGenerator(output_base=tmp_path)
        config = ServiceConfig("Test", "http://test.com/api", "test_output")
        generator.add_service("test", config)
        
        # Create existing output directory
        output_dir = tmp_path / "test_output"
        output_dir.mkdir(parents=True)
        (output_dir / "old_file.py").touch()
        
        result = generator.generate("test", force=True)
        assert result is True
    
    def test_generate_path_traversal_protection(self, tmp_path):
        """Test path traversal protection in generate."""
        generator = ClientGenerator(output_base=tmp_path)
        # This should fail during ServiceConfig creation
        with pytest.raises(ValueError):
            config = ServiceConfig("Test", "http://test.com/api", "../evil")
    
    @patch.object(SchemaProcessor, 'fetch', return_value={"openapi": "3.0.0", "paths": {}})
    @patch.object(SchemaProcessor, 'sanitize_security')
    @patch.object(GeneratorRunner, 'run', return_value=True)
    def test_generate_all_success(self, mock_run, mock_sanitize, mock_fetch, tmp_path):
        """Test generate_all with multiple services."""
        mock_sanitize.side_effect = lambda x: x
        
        generator = ClientGenerator(output_base=tmp_path)
        generator.add_service("svc1", ServiceConfig("Svc1", "http://test1.com/api", "out1"))
        generator.add_service("svc2", ServiceConfig("Svc2", "http://test2.com/api", "out2"))
        
        count = generator.generate_all(force=False)
        assert count == 2
    
    def test_generate_all_empty(self):
        """Test generate_all with no services."""
        generator = ClientGenerator()
        count = generator.generate_all()
        assert count == 0
    
    @patch.object(SchemaProcessor, 'fetch')
    @patch.object(SchemaProcessor, 'sanitize_security')
    @patch.object(GeneratorRunner, 'run')
    def test_generate_all_partial_success(self, mock_run, mock_sanitize, mock_fetch, tmp_path):
        """Test generate_all with some failures."""
        mock_sanitize.side_effect = lambda x: x
        # First succeeds, second fails
        mock_fetch.side_effect = [{"openapi": "3.0.0", "paths": {}}, None]
        mock_run.return_value = True
        
        generator = ClientGenerator(output_base=tmp_path)
        generator.add_service("svc1", ServiceConfig("Svc1", "http://test1.com/api", "out1"))
        generator.add_service("svc2", ServiceConfig("Svc2", "http://test2.com/api", "out2"))
        
        count = generator.generate_all(force=False)
        assert count == 1
    
    def test_list_services_with_services(self, capsys):
        """Test listing services when configured."""
        generator = ClientGenerator()
        generator.add_service("test", ServiceConfig("Test", "http://test.com/api", "test_out"))
        
        generator.list_services()
        captured = capsys.readouterr()
        assert "test" in captured.out
    
    def test_info_existing_service(self, capsys):
        """Test info for existing service."""
        generator = ClientGenerator()
        generator.add_service("test", ServiceConfig("Test", "http://test.com/api", "test_out"))
        
        generator.info("test")
        captured = capsys.readouterr()
        assert "test" in captured.out.lower()
    
    def test_info_nonexistent_service(self, capsys):
        """Test info for nonexistent service."""
        generator = ClientGenerator()
        generator.info("nonexistent")
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


# ============================================================================
# Test ConfigLoader Advanced
# ============================================================================
class TestConfigLoaderAdvanced:
    """Advanced tests for ConfigLoader."""
    
    def test_load_projects_format(self, tmp_path):
        """Test loading projects format config."""
        config_data = {
            "output_dir": str(tmp_path / "clients"),
            "projects": {
                "api1": {
                    "input": {"target": "http://api1.com/openapi.json"},
                    "output": {"dir": "api1", "name": "API 1"}
                },
                "api2": {
                    "input": {"target": "http://api2.com/swagger.yaml"},
                    "output": {"dir": "api2", "name": "API 2"}
                }
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        assert len(generator.services) == 2
        assert "api1" in generator.services
        assert "api2" in generator.services
    
    def test_load_services_format(self, tmp_path):
        """Test loading legacy services format."""
        config_data = {
            "services": [
                {
                    "key": "svc1",
                    "name": "Service 1",
                    "schema_url": "http://svc1.com/api",
                    "output_dir": "svc1"
                },
                {
                    "key": "svc2",
                    "name": "Service 2",
                    "schema_url": "http://svc2.com/api",
                    "output_dir": "svc2"
                }
            ]
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        assert len(generator.services) == 2
    
    def test_load_mixed_format(self, tmp_path):
        """Test loading config with both projects and services."""
        config_data = {
            "projects": {
                "proj1": {
                    "input": {"target": "http://proj1.com/api"},
                    "output": {"dir": "proj1", "name": "Project 1"}
                }
            },
            "services": [
                {
                    "key": "svc1",
                    "name": "Service 1",
                    "schema_url": "http://svc1.com/api",
                    "output_dir": "svc1"
                }
            ]
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        assert len(generator.services) == 2
    
    def test_load_service_without_key(self, tmp_path):
        """Test loading service without key field."""
        config_data = {
            "services": [
                {
                    "name": "No Key Service",
                    "schema_url": "http://test.com/api",
                    "output_dir": "output"
                }
            ]
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is False
    
    def test_load_invalid_service_config(self, tmp_path):
        """Test loading config with invalid service."""
        config_data = {
            "services": [
                {
                    "key": "invalid",
                    "name": "",  # Invalid: empty name
                    "schema_url": "http://test.com/api",
                    "output_dir": "output"
                }
            ]
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is False
    
    def test_load_empty_config(self, tmp_path):
        """Test loading empty config."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{}')
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is False
    
    def test_load_permission_denied(self, tmp_path):
        """Test loading config with permission denied."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{}')
        
        generator = ClientGenerator()
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = ConfigLoader.load(generator, str(config_file))
            assert result is False
    
    def test_load_unicode_error(self, tmp_path):
        """Test loading config with unicode error."""
        config_file = tmp_path / "config.json"
        config_file.write_bytes(b'\xff\xfe')  # Invalid UTF-8
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is False


# ============================================================================
# Test Command Classes
# ============================================================================
class TestCommands:
    """Tests for command classes."""
    
    def test_list_command(self):
        """Test ListCommand execution."""
        generator = Mock()
        cmd = ListCommand()
        cmd.execute(generator, ["list"])
        generator.list_services.assert_called_once()
    
    def test_generate_command_success(self):
        """Test GenerateCommand with service name."""
        generator = Mock()
        cmd = GenerateCommand()
        cmd.execute(generator, ["generate", "myapi"])
        generator.generate.assert_called_once_with("myapi", False)
    
    def test_generate_command_with_force(self):
        """Test GenerateCommand with force flag."""
        generator = Mock()
        cmd = GenerateCommand()
        cmd.execute(generator, ["generate", "myapi", "--force"])
        generator.generate.assert_called_once_with("myapi", True)
    
    def test_generate_command_missing_service(self, capsys):
        """Test GenerateCommand without service name."""
        generator = Mock()
        cmd = GenerateCommand()
        cmd.execute(generator, ["generate"])
        captured = capsys.readouterr()
        assert "missing" in captured.out.lower()
    
    def test_generate_all_command(self):
        """Test GenerateAllCommand execution."""
        generator = Mock()
        cmd = GenerateAllCommand()
        cmd.execute(generator, ["generate-all"])
        generator.generate_all.assert_called_once_with(False)
    
    def test_generate_all_command_with_force(self):
        """Test GenerateAllCommand with force flag."""
        generator = Mock()
        cmd = GenerateAllCommand()
        cmd.execute(generator, ["generate-all", "--force"])
        generator.generate_all.assert_called_once_with(True)
    
    def test_info_command_success(self):
        """Test InfoCommand with service name."""
        generator = Mock()
        cmd = InfoCommand()
        cmd.execute(generator, ["info", "myapi"])
        generator.info.assert_called_once_with("myapi")
    
    def test_info_command_missing_service(self, capsys):
        """Test InfoCommand without service name."""
        generator = Mock()
        cmd = InfoCommand()
        cmd.execute(generator, ["info"])
        captured = capsys.readouterr()
        assert "missing" in captured.out.lower()
    
    def test_command_registry_execute(self):
        """Test CommandRegistry execution."""
        generator = Mock()
        result = CommandRegistry.execute("list", generator, ["list"])
        assert result is True
    
    def test_command_registry_invalid_command(self):
        """Test CommandRegistry with invalid command."""
        generator = Mock()
        result = CommandRegistry.execute("invalid_cmd", generator, [])
        assert result is False


# ============================================================================
# Test Help Display
# ============================================================================
class TestHelpDisplay:
    """Tests for HelpDisplay."""
    
    def test_show_main_help(self, capsys):
        """Test showing main help."""
        HelpDisplay.show_main()
        captured = capsys.readouterr()
        assert "oasist" in captured.out.lower()
        assert "usage" in captured.out.lower()
    
    def test_show_command_help_list(self, capsys):
        """Test showing help for list command."""
        HelpDisplay.show_command("list")
        captured = capsys.readouterr()
        assert "list" in captured.out.lower()
    
    def test_show_command_help_generate(self, capsys):
        """Test showing help for generate command."""
        HelpDisplay.show_command("generate")
        captured = capsys.readouterr()
        assert "generate" in captured.out.lower()
        assert "force" in captured.out.lower()
    
    def test_show_command_help_invalid(self, capsys):
        """Test showing help for invalid command."""
        HelpDisplay.show_command("invalid")
        captured = capsys.readouterr()
        assert "oasist" in captured.out.lower()


# ============================================================================
# Test Argument Parsing Advanced
# ============================================================================
class TestArgumentParsingAdvanced:
    """Advanced tests for argument parsing."""
    
    def test_parse_empty_args(self):
        """Test parsing empty argument list."""
        config, verbose, args = parse_args([])
        assert config == "oasist_config.json"
        assert verbose is False
        assert args == []
    
    def test_parse_config_long_form(self):
        """Test parsing config with long form flag."""
        config, verbose, args = parse_args(["--config", "prod.json", "list"])
        assert config == "prod.json"
    
    def test_parse_verbose_long_form(self):
        """Test parsing verbose with long form flag."""
        config, verbose, args = parse_args(["--verbose", "list"])
        assert verbose is True
    
    def test_parse_multiple_commands(self):
        """Test parsing multiple command arguments."""
        config, verbose, args = parse_args(["generate", "api1", "--force"])
        assert args == ["generate", "api1", "--force"]
    
    def test_parse_config_at_end(self):
        """Test parsing with config flag at end."""
        config, verbose, args = parse_args(["list", "-c", "custom.json"])
        assert config == "custom.json"
        assert args == ["list"]


# ============================================================================
# Test Main Entry Point Advanced
# ============================================================================
class TestMainAdvanced:
    """Advanced tests for main() function."""
    
    @patch('sys.argv', ['oasist', '-V'])
    def test_main_version_short(self, capsys):
        """Test -V flag for version."""
        result = main()
        assert result == EXIT_SUCCESS
        captured = capsys.readouterr()
        assert "oasist" in captured.out
    
    @patch('sys.argv', ['oasist', 'help'])
    def test_main_help_command(self):
        """Test help command."""
        result = main()
        assert result == EXIT_SUCCESS
    
    @patch('sys.argv', ['oasist', 'help', 'generate'])
    def test_main_help_for_command(self):
        """Test help for specific command."""
        result = main()
        assert result == EXIT_SUCCESS
    
    @patch('sys.argv', ['oasist', '-h'])
    def test_main_help_flag_short(self):
        """Test -h flag."""
        result = main()
        assert result == EXIT_SUCCESS
    
    @patch('sys.argv', ['oasist', 'list'])
    @patch.object(ConfigLoader, 'load', return_value=True)
    @patch.object(CommandRegistry, 'execute', return_value=True)
    def test_main_list_command(self, mock_execute, mock_load):
        """Test main with list command."""
        result = main()
        assert result == EXIT_SUCCESS
    
    @patch('sys.argv', ['oasist', 'invalid_command'])
    @patch.object(ConfigLoader, 'load', return_value=True)
    def test_main_invalid_command(self, mock_load):
        """Test main with invalid command."""
        result = main()
        assert result == EXIT_ERROR
    
    @patch('sys.argv', ['oasist', 'list'])
    @patch.object(ConfigLoader, 'load', return_value=False)
    def test_main_config_load_failure(self, mock_load):
        """Test main with config load failure."""
        result = main()
        assert result == EXIT_ERROR
    
    @patch('sys.argv', ['oasist', '-v', 'list'])
    @patch.object(ConfigLoader, 'load', return_value=True)
    @patch.object(CommandRegistry, 'execute', return_value=True)
    def test_main_verbose_mode(self, mock_execute, mock_load):
        """Test main with verbose mode."""
        result = main()
        assert result == EXIT_SUCCESS


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================
class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_substitute_env_vars_non_string(self):
        """Test env substitution with non-string input."""
        result = substitute_env_vars(123)
        assert result == 123
    
    def test_substitute_env_vars_nested_braces(self):
        """Test env substitution with nested patterns."""
        result = substitute_env_vars("${VAR1}${VAR2}")
        assert "${VAR1}" in result or "${VAR2}" in result
    
    def test_substitute_recursive_none(self):
        """Test recursive substitution with None."""
        result = substitute_recursive(None)
        assert result is None
    
    def test_substitute_recursive_integer(self):
        """Test recursive substitution with integer."""
        result = substitute_recursive(42)
        assert result == 42
    
    def test_substitute_recursive_mixed_types(self, monkeypatch):
        """Test recursive substitution with mixed types."""
        monkeypatch.setenv("TEST", "value")
        data = {
            "string": "${TEST}",
            "number": 123,
            "list": ["${TEST}", 456],
            "nested": {"key": "${TEST}"}
        }
        result = substitute_recursive(data)
        assert result["string"] == "value"
        assert result["number"] == 123
        assert result["list"][0] == "value"
        assert result["nested"]["key"] == "value"
    
    def test_temp_file_io_error(self):
        """Test temp_file with IO error during write."""
        with patch('tempfile.NamedTemporaryFile', side_effect=IOError("Disk full")):
            with pytest.raises(IOError):
                with temp_file({"test": "data"}):
                    pass
    
    def test_service_config_url_with_port(self):
        """Test service config with URL containing port."""
        config = ServiceConfig(
            name="Test",
            schema_url="https://t.forbiz.ir//api/openapi.json",
            output_dir="output"
        )
        assert config.base_url == "https://t.forbiz.ir/"
    
    def test_sanitize_security_non_dict_paths(self):
        """Test sanitize with non-dict paths."""
        schema = {"paths": "invalid"}
        result = SchemaProcessor.sanitize_security(schema)
        assert result == schema
    
    def test_sanitize_security_non_dict_path_item(self):
        """Test sanitize with non-dict path item."""
        schema = {"paths": {"/test": "invalid"}}
        result = SchemaProcessor.sanitize_security(schema)
        assert result == schema
    
    def test_sanitize_security_non_dict_operation(self):
        """Test sanitize with non-dict operation."""
        schema = {"paths": {"/test": {"get": "invalid"}}}
        result = SchemaProcessor.sanitize_security(schema)
        assert result == schema


# ============================================================================
# Test Integration Scenarios
# ============================================================================
class TestIntegration:
    """Integration tests for complete workflows."""
    
    @patch.object(SchemaProcessor, 'fetch')
    @patch.object(GeneratorRunner, 'run')
    def test_full_generate_workflow(self, mock_run, mock_fetch, tmp_path):
        """Test complete generation workflow."""
        # Setup
        mock_fetch.return_value = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {"security": {"bearer": {}}}
                }
            }
        }
        mock_run.return_value = True
        
        config_data = {
            "output_dir": str(tmp_path),
            "projects": {
                "test_api": {
                    "input": {"target": "http://test.com/openapi.json"},
                    "output": {"dir": "test_api", "name": "Test API"}
                }
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Execute
        generator = ClientGenerator()
        ConfigLoader.load(generator, str(config_file))
        result = generator.generate("test_api", force=True)
        
        # Verify
        assert result is True
        assert mock_fetch.called
        assert mock_run.called
    
    def test_config_with_env_vars(self, tmp_path, monkeypatch):
        """Test config loading with environment variables."""
        monkeypatch.setenv("API_URL", "http://production.com")
        monkeypatch.setenv("API_TOKEN", "secret123")
        
        config_data = {
            "projects": {
                "prod_api": {
                    "input": {
                        "target": "${API_URL}/openapi.json",
                        "headers": {"Authorization": "Bearer ${API_TOKEN}"}
                    },
                    "output": {"dir": "prod_api", "name": "Production API"}
                }
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        service_config = generator.services["prod_api"]
        assert "production.com" in service_config.schema_url
        assert service_config.request_headers["Authorization"] == "Bearer secret123"


# ============================================================================
# Test Real API Endpoints (Optional - requires network)
# ============================================================================
class TestRealAPIs:
    """Tests against real API endpoints (can be skipped if APIs unavailable)."""
    
    @pytest.mark.skip(reason="Real API test - enable manually for integration testing")
    def test_fetch_fastapi_telegram_bot_schema(self):
        """Test fetching real FastAPI OpenAPI schema (JSON).
        
        API: Telegram Bot API at https://t.forbiz.ir/openapi.json
        Framework: FastAPI
        Format: JSON
        """
        schema = SchemaProcessor.fetch(
            "https://t.forbiz.ir/openapi.json",
            params={},
            prefer_json=True
        )
        
        assert schema is not None
        assert "openapi" in schema or "swagger" in schema
        assert "paths" in schema
        assert schema.get("info", {}).get("title") is not None
        
        # Verify it's the Telegram Bot API
        assert "Telegram" in schema.get("info", {}).get("title", "")
    
    @pytest.mark.skip(reason="Real API test - enable manually for integration testing")
    def test_fetch_django_drf_schema_json(self):
        """Test fetching Django DRF Spectacular schema (JSON).
        
        API: Django DRF at http://localhost:8004/api/schema/
        Framework: Django REST Framework with drf-spectacular
        Format: JSON
        """
        try:
            schema = SchemaProcessor.fetch(
                "http://localhost:8004/api/schema/",
                params={"format": "json"},
                prefer_json=True
            )
            
            if schema is not None:
                assert "openapi" in schema or "swagger" in schema
                assert "paths" in schema
        except Exception:
            pytest.skip("Django API not available at localhost:8004")
    
    @pytest.mark.skip(reason="Real API test - enable manually for integration testing")
    def test_fetch_django_drf_schema_yaml(self):
        """Test fetching Django DRF Spectacular schema (YAML).
        
        API: Django DRF at http://localhost:8004/api/schema/
        Framework: Django REST Framework with drf-spectacular
        Format: YAML
        """
        try:
            schema = SchemaProcessor.fetch(
                "http://localhost:8004/api/schema/",
                params={"format": "yaml"},
                prefer_json=False
            )
            
            if schema is not None:
                assert "openapi" in schema or "swagger" in schema
                assert "paths" in schema
        except Exception:
            pytest.skip("Django API not available at localhost:8004")
    
    @pytest.mark.skip(reason="Real API test - enable manually for integration testing")
    def test_telegram_bot_api_security_sanitization(self):
        """Test that Telegram Bot API security is properly sanitized.
        
        Tests the security field sanitization on real API data.
        """
        schema = SchemaProcessor.fetch(
            "https://t.forbiz.ir/openapi.json",
            params={},
            prefer_json=True
        )
        
        if schema is not None:
            sanitized = SchemaProcessor.sanitize_security(schema)
            
            # Check that all security fields are properly formatted as lists
            for path, path_item in sanitized.get("paths", {}).items():
                for method, operation in path_item.items():
                    if method in SchemaProcessor.HTTP_METHODS and isinstance(operation, dict):
                        security = operation.get("security")
                        if security is not None:
                            assert isinstance(security, list), \
                                f"Security in {path}.{method} should be a list"
    
    @pytest.mark.skip(reason="Real API test - enable manually for integration testing") 
    def test_generate_client_from_telegram_api(self, tmp_path):
        """Test full client generation from Telegram Bot API.
        
        Integration test that generates a complete Python client from real API.
        """
        generator = ClientGenerator(output_base=tmp_path)
        config = ServiceConfig(
            name="Telegram Bot API",
            schema_url="https://t.forbiz.ir/openapi.json",
            output_dir="telegram_bot_client",
            prefer_json=True
        )
        generator.add_service("telegram_bot", config)
        
        result = generator.generate("telegram_bot", force=True)
        
        if result:
            output_dir = tmp_path / "telegram_bot_client"
            assert output_dir.exists()
            assert (output_dir / "telegram_bot_api").exists()
            # Check that client module was generated
            assert any(output_dir.rglob("*.py"))


# ============================================================================
# Test Performance and Stress
# ============================================================================
class TestPerformance:
    """Performance and stress tests."""
    
    def test_substitute_recursive_large_structure(self, monkeypatch):
        """Test recursive substitution on large data structure."""
        monkeypatch.setenv("TEST", "value")
        
        # Create a large nested structure
        large_data = {
            f"key_{i}": {
                "nested": "${TEST}",
                "list": ["${TEST}"] * 10
            } for i in range(100)
        }
        
        result = substitute_recursive(large_data)
        
        # Verify all substitutions occurred
        assert result["key_0"]["nested"] == "value"
        assert all(v == "value" for v in result["key_0"]["list"])
    
    def test_sanitize_large_schema(self):
        """Test sanitizing large schema with many paths."""
        # Create schema with many paths
        schema = {
            "paths": {
                f"/endpoint_{i}": {
                    "get": {"security": {"bearer": {}}},
                    "post": {"security": {"api_key": {}}}
                } for i in range(100)
            }
        }
        
        result = SchemaProcessor.sanitize_security(schema)
        
        # Verify all paths were processed
        assert len(result["paths"]) == 100
        for path_item in result["paths"].values():
            assert isinstance(path_item["get"]["security"], list)
            assert isinstance(path_item["post"]["security"], list)
    
    def test_multiple_generators_isolated(self, tmp_path):
        """Test that multiple generators don't interfere with each other."""
        gen1 = ClientGenerator(output_base=tmp_path / "gen1")
        gen2 = ClientGenerator(output_base=tmp_path / "gen2")
        
        config1 = ServiceConfig("API1", "http://api1.com/openapi.json", "client1")
        config2 = ServiceConfig("API2", "http://api2.com/openapi.json", "client2")
        
        gen1.add_service("api1", config1)
        gen2.add_service("api2", config2)
        
        assert "api1" in gen1.services
        assert "api1" not in gen2.services
        assert "api2" in gen2.services
        assert "api2" not in gen1.services


# ============================================================================
# Test Backwards Compatibility
# ============================================================================
class TestBackwardsCompatibility:
    """Tests for backwards compatibility with older configurations."""
    
    def test_legacy_config_without_prefer_json(self, tmp_path):
        """Test loading config without prefer_json field."""
        config_data = {
            "services": [
                {
                    "key": "old_api",
                    "name": "Old API",
                    "schema_url": "http://old.com/api",
                    "output_dir": "old_api"
                }
            ]
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        assert generator.services["old_api"].prefer_json is False
    
    def test_legacy_config_without_disable_post_hooks(self, tmp_path):
        """Test loading config without disable_post_hooks field."""
        config_data = {
            "projects": {
                "legacy": {
                    "input": {"target": "http://legacy.com/api"},
                    "output": {"dir": "legacy"}
                }
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        assert generator.services["legacy"].disable_post_hooks is True
    
    def test_config_with_format_with_black(self, tmp_path):
        """Test loading config with format_with_black option."""
        config_data = {
            "projects": {
                "formatted": {
                    "input": {"target": "http://test.com/api"},
                    "output": {"dir": "formatted", "format_with_black": True}
                },
                "unformatted": {
                    "input": {"target": "http://test.com/api"},
                    "output": {"dir": "unformatted", "format_with_black": False}
                }
            }
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        generator = ClientGenerator()
        result = ConfigLoader.load(generator, str(config_file))
        
        assert result is True
        assert generator.services["formatted"].format_with_black is True
        assert generator.services["unformatted"].format_with_black is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
