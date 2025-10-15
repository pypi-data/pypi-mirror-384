"""
Unit tests for the environment variable interpolation module.

Tests the pycomex.functional.interpolation module which provides utilities
to interpolate environment variables into YAML configuration files using
${VAR} and ${VAR:-default} syntax.
"""

import os
import pytest

from pycomex.functional.utils import (
    ConfigInterpolationError,
    interpolate_env_vars,
    interpolate_string,
    parse_env_var_reference,
)


class TestParseEnvVarReference:
    """Test the parse_env_var_reference function."""

    def test_parse_simple_var(self):
        """Should parse ${VAR} format correctly."""
        var_name, default = parse_env_var_reference("${HOME}")
        assert var_name == "HOME"
        assert default is None

    def test_parse_var_with_default(self):
        """Should parse ${VAR:-default} format correctly."""
        var_name, default = parse_env_var_reference("${PORT:-8080}")
        assert var_name == "PORT"
        assert default == "8080"

    def test_parse_var_with_empty_default(self):
        """Should parse ${VAR:-} format (empty default) correctly."""
        var_name, default = parse_env_var_reference("${VALUE:-}")
        assert var_name == "VALUE"
        assert default == ""

    def test_parse_var_with_complex_default(self):
        """Should parse defaults containing special characters."""
        var_name, default = parse_env_var_reference("${PATH:-/usr/local/bin:/usr/bin}")
        assert var_name == "PATH"
        assert default == "/usr/local/bin:/usr/bin"

    def test_parse_underscore_var(self):
        """Should parse variable names with underscores."""
        var_name, default = parse_env_var_reference("${MY_VAR}")
        assert var_name == "MY_VAR"
        assert default is None

    def test_parse_number_in_var(self):
        """Should parse variable names with numbers."""
        var_name, default = parse_env_var_reference("${VAR_123}")
        assert var_name == "VAR_123"
        assert default is None

    def test_invalid_format_raises_error(self):
        """Should raise error for invalid format."""
        with pytest.raises(ConfigInterpolationError) as exc_info:
            parse_env_var_reference("$HOME")  # Missing braces
        assert "Invalid environment variable reference format" in str(exc_info.value)

    def test_invalid_var_name_raises_error(self):
        """Should raise error for variable names starting with numbers."""
        with pytest.raises(ConfigInterpolationError):
            parse_env_var_reference("${123VAR}")

    def test_empty_var_name_raises_error(self):
        """Should raise error for empty variable name."""
        with pytest.raises(ConfigInterpolationError):
            parse_env_var_reference("${}")


class TestInterpolateString:
    """Test the interpolate_string function."""

    def test_simple_interpolation(self):
        """Should interpolate a single environment variable."""
        os.environ["TEST_VAR"] = "/home/user"
        try:
            result = interpolate_string("Path: ${TEST_VAR}/data")
            assert result == "Path: /home/user/data"
        finally:
            del os.environ["TEST_VAR"]

    def test_multiple_interpolations(self):
        """Should interpolate multiple environment variables."""
        os.environ["HOST"] = "localhost"
        os.environ["PORT"] = "8080"
        try:
            result = interpolate_string("http://${HOST}:${PORT}/api")
            assert result == "http://localhost:8080/api"
        finally:
            del os.environ["HOST"]
            del os.environ["PORT"]

    def test_interpolation_with_default_when_var_set(self):
        """Should use actual value when variable is set."""
        os.environ["PORT"] = "9000"
        try:
            result = interpolate_string("Port: ${PORT:-8080}")
            assert result == "Port: 9000"
        finally:
            del os.environ["PORT"]

    def test_interpolation_with_default_when_var_not_set(self):
        """Should use default value when variable is not set."""
        # Ensure variable is not set
        if "PORT" in os.environ:
            del os.environ["PORT"]

        result = interpolate_string("Port: ${PORT:-8080}")
        assert result == "Port: 8080"

    def test_interpolation_missing_var_raises_error(self):
        """Should raise error when variable not set and no default."""
        # Ensure variable is not set
        if "MISSING_VAR" in os.environ:
            del os.environ["MISSING_VAR"]

        with pytest.raises(ConfigInterpolationError) as exc_info:
            interpolate_string("Value: ${MISSING_VAR}")

        assert "MISSING_VAR" in str(exc_info.value)
        assert "not set" in str(exc_info.value)
        assert ":-default" in str(exc_info.value)  # Should suggest default syntax

    def test_escape_sequence(self):
        """Should handle $$ escape sequence."""
        result = interpolate_string("Price: $$50")
        assert result == "Price: $50"

    def test_multiple_escape_sequences(self):
        """Should handle multiple $$ escape sequences."""
        result = interpolate_string("$$A costs $$50, $$B costs $$75")
        assert result == "$A costs $50, $B costs $75"

    def test_escape_sequence_with_interpolation(self):
        """Should handle both escape sequences and interpolation."""
        os.environ["AMOUNT"] = "100"
        try:
            result = interpolate_string("Price: $$${AMOUNT}")
            assert result == "Price: $100"
        finally:
            del os.environ["AMOUNT"]

    def test_no_interpolation_for_non_string(self):
        """Should return non-string values unchanged."""
        assert interpolate_string(123) == 123
        assert interpolate_string(True) == True
        assert interpolate_string(None) == None
        assert interpolate_string([1, 2, 3]) == [1, 2, 3]

    def test_empty_string(self):
        """Should handle empty strings."""
        assert interpolate_string("") == ""

    def test_string_without_vars(self):
        """Should return string unchanged if no variables."""
        assert interpolate_string("Just a regular string") == "Just a regular string"

    def test_empty_default_value(self):
        """Should handle empty default value."""
        if "EMPTY_VAR" in os.environ:
            del os.environ["EMPTY_VAR"]

        result = interpolate_string("Value: ${EMPTY_VAR:-}")
        assert result == "Value: "


class TestInterpolateEnvVars:
    """Test the interpolate_env_vars function for recursive interpolation."""

    def test_interpolate_dict(self):
        """Should recursively interpolate variables in dictionaries."""
        os.environ["DATA_PATH"] = "/mnt/data"
        os.environ["MODEL_NAME"] = "resnet50"
        try:
            data = {
                "extend": "${DATA_PATH}/experiment.py",
                "parameters": {
                    "MODEL": "${MODEL_NAME}",
                    "EPOCHS": 100,  # Non-string, should be unchanged
                }
            }
            result = interpolate_env_vars(data)

            assert result["extend"] == "/mnt/data/experiment.py"
            assert result["parameters"]["MODEL"] == "resnet50"
            assert result["parameters"]["EPOCHS"] == 100
        finally:
            del os.environ["DATA_PATH"]
            del os.environ["MODEL_NAME"]

    def test_interpolate_list(self):
        """Should recursively interpolate variables in lists."""
        os.environ["HOST"] = "server.com"
        try:
            data = ["${HOST}/api1", "${HOST}/api2", 8080]
            result = interpolate_env_vars(data)

            assert result == ["server.com/api1", "server.com/api2", 8080]
        finally:
            del os.environ["HOST"]

    def test_interpolate_nested_structure(self):
        """Should interpolate deeply nested structures."""
        os.environ["ROOT"] = "/root"
        try:
            data = {
                "level1": {
                    "level2": {
                        "level3": ["${ROOT}/path1", "${ROOT}/path2"]
                    },
                    "other": "${ROOT}/other"
                }
            }
            result = interpolate_env_vars(data)

            assert result["level1"]["level2"]["level3"][0] == "/root/path1"
            assert result["level1"]["level2"]["level3"][1] == "/root/path2"
            assert result["level1"]["other"] == "/root/other"
        finally:
            del os.environ["ROOT"]

    def test_interpolate_preserves_types(self):
        """Should preserve non-string types."""
        data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        result = interpolate_env_vars(data)

        assert result == data
        assert isinstance(result["integer"], int)
        assert isinstance(result["float"], float)
        assert isinstance(result["boolean"], bool)

    def test_interpolate_with_mixed_content(self):
        """Should handle mixed string and non-string content."""
        os.environ["PATH_VAR"] = "/data"
        try:
            data = {
                "path": "${PATH_VAR}/files",
                "count": 10,
                "enabled": True,
                "items": ["${PATH_VAR}/item1", 42, True]
            }
            result = interpolate_env_vars(data)

            assert result["path"] == "/data/files"
            assert result["count"] == 10
            assert result["enabled"] == True
            assert result["items"][0] == "/data/item1"
            assert result["items"][1] == 42
            assert result["items"][2] == True
        finally:
            del os.environ["PATH_VAR"]

    def test_interpolate_empty_dict(self):
        """Should handle empty dictionaries."""
        assert interpolate_env_vars({}) == {}

    def test_interpolate_empty_list(self):
        """Should handle empty lists."""
        assert interpolate_env_vars([]) == []

    def test_interpolate_error_propagates(self):
        """Should propagate ConfigInterpolationError from nested values."""
        if "MISSING" in os.environ:
            del os.environ["MISSING"]

        data = {"nested": {"value": "${MISSING}"}}

        with pytest.raises(ConfigInterpolationError):
            interpolate_env_vars(data)

    def test_realistic_config_example(self):
        """Should handle a realistic configuration example."""
        os.environ["PROJECT_ROOT"] = "/home/user/project"
        os.environ["EXPERIMENT_NAME"] = "my_experiment"
        os.environ["GPU_ID"] = "0"

        try:
            config = {
                "pycomex": True,
                "extend": "${PROJECT_ROOT}/experiments/base.py",
                "name": "${EXPERIMENT_NAME}",
                "base_path": "${PROJECT_ROOT}/results",
                "namespace": "results/${EXPERIMENT_NAME}",
                "description": "Experiment using GPU ${GPU_ID:-none}",
                "parameters": {
                    "DATA_PATH": "${PROJECT_ROOT}/data",
                    "BATCH_SIZE": "${BATCH_SIZE:-32}",
                    "LEARNING_RATE": 0.001,
                    "__DEBUG__": False,
                }
            }

            result = interpolate_env_vars(config)

            assert result["extend"] == "/home/user/project/experiments/base.py"
            assert result["name"] == "my_experiment"
            assert result["base_path"] == "/home/user/project/results"
            assert result["namespace"] == "results/my_experiment"
            assert result["description"] == "Experiment using GPU 0"
            assert result["parameters"]["DATA_PATH"] == "/home/user/project/data"
            assert result["parameters"]["BATCH_SIZE"] == "32"  # Default used
            assert result["parameters"]["LEARNING_RATE"] == 0.001  # Unchanged
            assert result["parameters"]["__DEBUG__"] == False  # Unchanged

        finally:
            del os.environ["PROJECT_ROOT"]
            del os.environ["EXPERIMENT_NAME"]
            del os.environ["GPU_ID"]


class TestConfigInterpolationError:
    """Test the ConfigInterpolationError exception."""

    def test_error_is_exception(self):
        """ConfigInterpolationError should be an Exception."""
        error = ConfigInterpolationError("test message")
        assert isinstance(error, Exception)

    def test_error_message(self):
        """ConfigInterpolationError should preserve message."""
        error = ConfigInterpolationError("custom message")
        assert str(error) == "custom message"
