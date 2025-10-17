import pytest
import os
import yaml

from dictconf.lib import (
    Config,
    ConfigLoader,
    load_config,
    ConfigFileNotFoundError,
    InvalidOverrideError,
    InterpolationError,
    ConfigError
)

# ==============================================================================
# Tests for the Config object itself
# ==============================================================================
class TestConfig:
    """Tests the functionality of the dot-notation Config object."""

    def test_attribute_access(self):
        """
        Tests basic access to top-level keys as attributes.
        """
        # Arrange
        data = {"host": "localhost", "port": 8000}

        # Act
        conf = Config(data)

        # Assert
        assert conf.host == "localhost"
        assert conf.port == 8000

    def test_nested_attribute_access(self):
        """
        Tests access to nested keys as attributes.
        """
        # Arrange
        data = {"server": {"host": "example.com", "port": 443}}

        # Act
        conf = Config(data)

        # Assert
        assert conf.server.host == "example.com"
        assert conf.server.port == 443

    def test_attribute_assignment(self):
        """
        Tests setting a value via attribute assignment.
        """
        # Arrange
        conf = Config({"key": "initial_value"})

        # Act
        conf.key = "new_value"
        conf.new_key = 123

        # Assert
        assert conf.key == "new_value"
        assert conf["key"] == "new_value"
        assert conf.new_key == 123

    def test_attribute_access_raises_attribute_error(self):
        """
        Tests that accessing a non-existent key raises an AttributeError.
        """
        # Arrange
        conf = Config({"existing_key": "value"})

        # Act & Assert
        with pytest.raises(AttributeError, match="'Config' object has no attribute 'missing_key'"):
            _ = conf.missing_key


# ==============================================================================
# Tests for the ConfigLoader class
# ==============================================================================
class TestConfigLoader:
    """Tests the core logic of loading, merging, and processing."""

    def test_loader_init_raises_for_bad_directory(self):
        """
        Tests that the loader raises an error if the config directory doesn't exist.
        """
        # Arrange
        bad_path = "/path/that/does/not/exist"

        # Act & Assert
        with pytest.raises(ConfigFileNotFoundError, match=f"Configuration directory not found: {bad_path}"):
            _ = ConfigLoader(bad_path)

    def test_legacy_load_with_typed_overrides(self, config_dir):
        """
        Tests that non-composed loading correctly casts override types.
        """
        # Arrange
        loader = ConfigLoader(config_dir)
        overrides = [
            "service.retries=5",
            "service.enabled=true",
            "service.timeout=1.5",
            "service.user=null"
        ]

        # Act
        conf = loader.load("legacy.yaml", cli_args=overrides)

        # Assert
        assert conf.service.retries == 5
        assert conf.service.enabled is True
        assert conf.service.timeout == 1.5
        assert conf.service.user is None

    def test_composed_load_default(self, config_dir):
        """
        Tests loading a composed config with its specified default component.
        """
        # Arrange
        loader = ConfigLoader(config_dir)

        # Act
        conf = loader.load("config.yaml")

        # Assert
        assert conf.db.driver == "sqlite"
        assert conf.db.path == "/var/data/app.db"
        assert conf.server.host == "127.0.0.1"

    def test_composed_load_with_component_swap(self, config_dir):
        """
        Tests swapping a default component via a CLI argument.
        """
        # Arrange
        loader = ConfigLoader(config_dir)
        cli_args = ["db=mysql"]

        # Act
        conf = loader.load("config.yaml", cli_args=cli_args)

        # Assert
        assert conf.db.driver == "mysql"
        assert conf.db.user == "root"
        assert "path" not in conf.db  # Ensure sqlite config was not merged

    def test_composed_load_swap_and_value_override(self, config_dir):
        """
        Tests both swapping a component and overriding a value in it.
        """
        # Arrange
        loader = ConfigLoader(config_dir)
        cli_args = ["db=mysql", "db.user=admin", "db.host=db.test.local"]

        # Act
        conf = loader.load("config.yaml", cli_args=cli_args)

        # Assert
        assert conf.db.driver == "mysql"
        assert conf.db.user == "admin"
        assert conf.db.host == "db.test.local"
        assert conf.db.password == "changeme"  # Unchanged value

    def test_interpolation_resolves_correctly(self, config_dir):
        """
        Tests that variable interpolation works as expected.
        """
        # Arrange
        loader = ConfigLoader(config_dir)
        cli_args = ["server.port=443", "server.host=example.com"]

        # Act
        conf = loader.load("config.yaml", cli_args=cli_args)

        # Assert
        assert conf.server.url == "http://example.com:443"

    def test_interpolation_preserves_type(self, config_dir):
        """
        Tests that full-string replacement preserves the original type.
        """
        # Arrange
        # Add a config file with an interpolation target that is an integer
        int_interp_config = {
            "app": {
                "port": 9090,
                "port_reference": "${app.port}"
            }
        }
        with open(os.path.join(config_dir, "interp.yaml"), "w") as f:
            yaml.dump(int_interp_config, f)
        
        loader = ConfigLoader(config_dir)

        # Act
        conf = loader.load("interp.yaml")

        # Assert
        assert conf.app.port_reference == 9090
        assert isinstance(conf.app.port_reference, int)

    def test_interpolation_circular_reference_raises_error(self, config_dir):
        """
        Tests that a circular variable reference raises an InterpolationError.
        """
        # Arrange
        circular_ref_config = {
            "a": "${b}",
            "b": "${a}"
        }
        with open(os.path.join(config_dir, "circular.yaml"), "w") as f:
            yaml.dump(circular_ref_config, f)

        loader = ConfigLoader(config_dir)
        
        # Act & Assert
        with pytest.raises(InterpolationError, match="Max interpolation depth reached"):
            loader.load("circular.yaml")

    def test_load_missing_component_raises_error(self, config_dir):
        """
        Tests that a missing component file raises ConfigFileNotFoundError.
        """
        # Arrange
        loader = ConfigLoader(config_dir)
        cli_args = ["db=postgres"]  # postgres.yaml does not exist

        # Act & Assert
        with pytest.raises(ConfigFileNotFoundError, match="postgres.yaml"):
            loader.load("config.yaml", cli_args=cli_args)

    def test_invalid_override_format_raises_error(self, config_dir):
        """
        Tests that a malformed CLI value override raises InvalidOverrideError.
        """
        # Arrange
        loader = ConfigLoader(config_dir)
        # Missing '='
        cli_args = ["db.useradmin"]

        # Act & Assert
        with pytest.raises(InvalidOverrideError, match="Invalid override format: 'db.useradmin'"):
            loader.load("legacy.yaml", cli_args=cli_args)

    def test_malformed_yaml_raises_error(self, config_dir):
        """
        Tests that a syntactically incorrect YAML file raises a ConfigError.
        """
        # Arrange
        with open(os.path.join(config_dir, "malformed.yaml"), "w") as f:
            f.write("server: {host: 'localhost', port: 8080") # Missing closing brace
        
        loader = ConfigLoader(config_dir)

        # Act & Assert
        with pytest.raises(ConfigError, match="Error parsing YAML file"):
            loader.load("malformed.yaml")


# ==============================================================================
# Tests for the load_config wrapper function
# ==============================================================================
class TestLoadConfigWrapper:
    """Tests the public API wrapper function `load_config`."""

    def test_load_config_wrapper_with_file_path(self, config_dir):
        """
        Tests that the wrapper works correctly when given a direct file path.
        """
        # Arrange
        file_path = os.path.join(config_dir, "config.yaml")

        # Act
        conf = load_config(file_path, cli_args=["db=mysql"])

        # Assert
        assert conf.db.driver == "mysql"
        assert conf.server.host == "127.0.0.1"

    def test_load_config_wrapper_with_dir_path(self, config_dir):
        """
        Tests that the wrapper works when given a directory path,
        assuming a 'config.yaml' exists.
        """
        # Arrange
        # config_dir fixture is already the path to the directory

        # Act
        conf = load_config(config_dir)

        # Assert
        assert conf.db.driver == "sqlite"
        assert conf.server.host == "127.0.0.1"
