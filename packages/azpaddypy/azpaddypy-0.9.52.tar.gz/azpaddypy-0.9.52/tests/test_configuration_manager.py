"""
Pytest tests for the Configuration Manager tool.

Tests cover configuration loading, access tracking, reporting,
health checks, and error handling scenarios.
"""

import pytest
import os
import json
import tempfile
import pathlib
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from azpaddypy.tools.configuration_manager import (
    ConfigurationManager,
    create_configuration_manager,
    ConfigSource,
    ConfigEntry,
    LogExecution
)
from azpaddypy.mgmt.logging import AzureLogger
from azpaddypy.builder.configuration import EnvironmentConfiguration


class TestConfigEntry:
    """Test the ConfigEntry dataclass."""

    def test_config_entry_creation(self):
        """Test ConfigEntry creation with defaults."""
        entry = ConfigEntry(
            key="test_key",
            value="test_value",
            source=ConfigSource.ENVIRONMENT,
            source_detail="Environment Variable"
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.source == ConfigSource.ENVIRONMENT
        assert entry.source_detail == "Environment Variable"
        assert entry.access_count == 0
        assert isinstance(entry.loaded_at, float)
        assert isinstance(entry.last_accessed, float)

    def test_mark_accessed(self):
        """Test access tracking functionality."""
        entry = ConfigEntry(
            key="test_key",
            value="test_value",
            source=ConfigSource.ENVIRONMENT,
            source_detail="Environment Variable"
        )
        
        initial_access_time = entry.last_accessed
        initial_count = entry.access_count
        
        time.sleep(0.1)  # Small delay to ensure time difference
        entry.mark_accessed()
        
        assert entry.access_count == initial_count + 1
        assert entry.last_accessed > initial_access_time

    def test_human_readable_timestamps(self):
        """Test human readable timestamp formatting."""
        entry = ConfigEntry(
            key="test_key",
            value="test_value", 
            source=ConfigSource.ENVIRONMENT,
            source_detail="Environment Variable"
        )
        
        # Test loaded time format
        loaded_str = entry.get_human_readable_loaded_at()
        assert isinstance(loaded_str, str)
        assert len(loaded_str) == 19  # YYYY-MM-DD HH:MM:SS format
        
        # Test last access time format
        access_str = entry.get_human_readable_last_access()
        assert isinstance(access_str, str)
        assert len(access_str) == 19  # YYYY-MM-DD HH:MM:SS format


class TestConfigurationManager:
    """Test the ConfigurationManager class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with test config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = pathlib.Path(temp_dir) / "configs"
            config_dir.mkdir()
            
            # Create test JSON files
            database_config = {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "testdb"
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600
                }
            }
            
            features_config = {
                "features": {
                    "new_ui": {"enabled": True},
                    "beta_mode": {"enabled": False}
                }
            }
            
            # Write config files
            with open(config_dir / "database.json", "w") as f:
                json.dump(database_config, f)
                
            with open(config_dir / "features.json", "w") as f:
                json.dump(features_config, f)
            
            # Create invalid JSON file
            with open(config_dir / "invalid.json", "w") as f:
                f.write("{ invalid json }")
            
            yield str(config_dir)

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = Mock(spec=AzureLogger)
        logger.create_span = MagicMock()
        logger.create_span.return_value.__enter__ = Mock()
        logger.create_span.return_value.__exit__ = Mock()
        return logger

    @pytest.fixture
    def mock_environment_config(self):
        """Create a mock EnvironmentConfiguration for testing."""
        return EnvironmentConfiguration(
            running_in_docker=False,
            local_settings={},
            local_env_manager=Mock(),
            service_name="test_service",
            service_version="1.0.0",
            reflection_kind="test",
            logger_enable_console=True,
            logger_connection_string=None,
            logger_instrumentation_options={},
            logger_log_level="INFO",
            identity_enable_token_cache=True,
            identity_allow_unencrypted_storage=True,
            identity_custom_credential_options=None,
            identity_connection_string=None,
        )

    @pytest.fixture
    def config_manager(self, temp_config_dir, mock_logger, mock_environment_config):
        """Create a ConfigurationManager for testing."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value", "APP_CONFIG": "app_value"}):
            return ConfigurationManager(
                environment_configuration=mock_environment_config,
                configs_dir=temp_config_dir,
                auto_reload=False,
                include_env_vars=True,
                env_var_prefix="TEST_",
                logger=mock_logger
            )

    def test_initialization(self, config_manager, mock_logger):
        """Test ConfigurationManager initialization."""
        assert config_manager.service_name == "test_service"
        assert config_manager.service_version == "1.0.0"
        assert config_manager.logger == mock_logger
        assert config_manager.auto_reload is False
        assert config_manager.include_env_vars is True
        assert config_manager.env_var_prefix == "TEST_"
        assert len(config_manager._config_entries) > 0

    def test_environment_variable_loading(self, temp_config_dir, mock_logger, mock_environment_config):
        """Test loading environment variables with prefix filtering."""
        with patch.dict(os.environ, {"TEST_VAR1": "value1", "TEST_VAR2": "value2", "OTHER_VAR": "other"}):
            manager = ConfigurationManager(
                environment_configuration=mock_environment_config,
                configs_dir=temp_config_dir,
                env_var_prefix="TEST_",
                logger=mock_logger
            )
            
            # Should load TEST_ prefixed vars
            assert manager.get_config("TEST_VAR1") == "value1"
            assert manager.get_config("TEST_VAR2") == "value2"
            
            # Should not load non-prefixed vars
            assert manager.get_config("OTHER_VAR") is None

    def test_json_config_loading(self, config_manager):
        """Test loading JSON configuration files."""
        # Test flattened JSON access
        assert config_manager.get_config("database.host") == "localhost"
        assert config_manager.get_config("database.port") == 5432
        assert config_manager.get_config("cache.enabled") is True
        assert config_manager.get_config("features.new_ui.enabled") is True
        assert config_manager.get_config("features.beta_mode.enabled") is False

    def test_get_config_with_defaults(self, config_manager):
        """Test getting configuration with default values."""
        # Existing key
        assert config_manager.get_config("database.host", "default") == "localhost"
        
        # Non-existing key with default
        assert config_manager.get_config("nonexistent.key", "default_value") == "default_value"
        
        # Non-existing key without default
        assert config_manager.get_config("nonexistent.key") is None

    def test_access_tracking(self, config_manager):
        """Test configuration access tracking."""
        key = "database.host"
        
        # Get initial access count
        entry = config_manager._config_entries[key]
        initial_count = entry.access_count
        initial_time = entry.last_accessed
        
        time.sleep(0.1)  # Small delay
        
        # Access the configuration
        value = config_manager.get_config(key)
        
        # Verify access tracking
        assert value == "localhost"
        assert entry.access_count == initial_count + 1
        assert entry.last_accessed > initial_time

    def test_has_config(self, config_manager):
        """Test configuration existence checking."""
        assert config_manager.has_config("database.host") is True
        assert config_manager.has_config("nonexistent.key") is False

    def test_get_all_configs(self, config_manager):
        """Test getting all configurations."""
        all_configs = config_manager.get_all_configs()
        
        assert isinstance(all_configs, dict)
        assert "database.host" in all_configs
        assert "features.new_ui.enabled" in all_configs
        assert all_configs["database.host"] == "localhost"

    def test_repr_method(self, config_manager):
        """Test the __repr__ method for generating reports."""
        report = repr(config_manager)
        assert isinstance(report, str)
        assert "Configuration Manager Report" in report
        assert "test_service" in report
        assert "database.host" in report
        assert "[HIDDEN]" not in report  # No sensitive keys in this test

    def test_get_filtered_report(self, config_manager):
        """Test generating a filtered configuration report."""
        # Filter by prefix
        report = config_manager.get_filtered_report(filter_prefix="database.")
        assert "database.host" in report
        assert "features.new_ui.enabled" not in report
        
        # Test with hidden values
        report_hidden = config_manager.get_filtered_report(show_values=False)
        assert "[HIDDEN]" in report_hidden

    def test_get_access_stats(self, config_manager):
        """Test getting configuration access statistics."""
        # Access a key to generate stats
        config_manager.get_config("database.host")
        
        stats = config_manager.get_access_stats()
        
        assert isinstance(stats, dict)
        assert "total_accesses" in stats
        assert stats["total_accesses"] > 0
        assert stats["most_accessed_key"] == "database.host"

    def test_health_check(self, config_manager):
        """Test the health check functionality."""
        health = config_manager.health_check()
        
        assert isinstance(health, dict)
        assert health["status"] == "healthy"
        assert "configs_directory" in health["checks"]
        assert health["checks"]["configs_directory"]["status"] == "healthy"

    def test_reload_configs(self, config_manager, temp_config_dir):
        """Test manually reloading configuration files."""
        # Modify a config file
        new_port = 9999
        config_file = pathlib.Path(temp_config_dir) / "database.json"
        
        with open(config_file, "r") as f:
            data = json.load(f)
        
        data["database"]["port"] = new_port
        
        with open(config_file, "w") as f:
            json.dump(data, f)
            
        # Reload and verify
        config_manager.reload_configs()
        assert config_manager.get_config("database.port") == new_port

    def test_auto_reload(self, temp_config_dir, mock_logger, mock_environment_config):
        """Test automatic reloading of configurations on change."""
        manager = ConfigurationManager(
            environment_configuration=mock_environment_config,
            configs_dir=temp_config_dir,
            auto_reload=True,
            logger=mock_logger
        )
        
        # Modify a file
        config_file = pathlib.Path(temp_config_dir) / "features.json"
        time.sleep(0.1)  # Ensure modification time is different
        with open(config_file, "r+") as f:
            data = json.load(f)
            data["features"]["beta_mode"]["enabled"] = True
            f.seek(0)
            json.dump(data, f)
            f.truncate()
        
        # Access a key to trigger reload
        assert manager.get_config("features.beta_mode.enabled") is True

    def test_missing_configs_directory(self, mock_logger, mock_environment_config):
        """Test handling of a missing configs directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_dir = os.path.join(temp_dir, "nonexistent")
            manager = ConfigurationManager(
                environment_configuration=mock_environment_config,
                configs_dir=missing_dir,
                logger=mock_logger,
                include_env_vars=False
            )
            assert len(manager._config_entries) == 0  # No file-based configs

    def test_invalid_json_handling(self, temp_config_dir, mock_logger, mock_environment_config):
        """Test that invalid JSON files are handled gracefully."""
        manager = ConfigurationManager(
            environment_configuration=mock_environment_config,
            configs_dir=temp_config_dir,
            logger=mock_logger
        )
        # Should log an error but not raise an exception
        assert mock_logger.error.called
        # Check that valid files were still loaded
        assert manager.has_config("database.host")

    def test_no_environment_variables(self, temp_config_dir, mock_logger, mock_environment_config):
        """Test initialization without including environment variables."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            manager = ConfigurationManager(
                environment_configuration=mock_environment_config,
                configs_dir=temp_config_dir,
                include_env_vars=False,
                logger=mock_logger
            )
            assert manager.get_config("TEST_VAR") is None
            assert manager.has_config("TEST_VAR") is False

    def test_json_flattening(self, config_manager):
        """Test nested JSON flattening logic."""
        # Nested keys from test files
        assert config_manager.get_config("database.host") == "localhost"
        assert config_manager.get_config("features.new_ui.enabled") is True
        
        # Manually check a non-existent deep key
        assert config_manager.get_config("database.connection.pool.size") is None

    def test_set_config_runtime(self, config_manager):
        """Test setting a configuration value at runtime."""
        key = "runtime.key"
        value = "runtime_value"

        # Key should not exist initially
        assert not config_manager.has_config(key)

        # Set the config
        config_manager.set_config(key, value)

        # Verify the config is set correctly
        assert config_manager.has_config(key)
        assert config_manager.get_config(key) == value
        
        entry = config_manager._config_entries[key]
        assert entry.source == ConfigSource.RUNTIME

    def test_set_config_with_env(self, config_manager):
        """Test setting a config value and also as an environment variable."""
        key = "RUNTIME_ENV_VAR"
        value = "runtime_env_value"

        with patch.dict(os.environ) as mock_env:
            # Set the config with env=True
            config_manager.set_config(key, value, env=True)

            # Verify the config is set
            assert config_manager.get_config(key) == value
            
            # Verify the environment variable is set
            assert key in mock_env
            assert mock_env[key] == str(value)


class TestConfigurationManagerFactory:
    """Test the create_configuration_manager factory function."""

    def test_factory_function(self):
        """Test configuration manager creation via factory function."""
        # Create mock environment config for factory test
        mock_env_config = EnvironmentConfiguration(
            running_in_docker=False,
            local_settings={},
            local_env_manager=Mock(),
            service_name="test_factory",
            service_version="2.0.0",
            reflection_kind="test",
            logger_enable_console=True,
            logger_connection_string=None,
            logger_instrumentation_options={},
            logger_log_level="INFO",
            identity_enable_token_cache=True,
            identity_allow_unencrypted_storage=True,
            identity_custom_credential_options=None,
            identity_connection_string=None,
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = create_configuration_manager(
                environment_configuration=mock_env_config,
                configs_dir=temp_dir,
                auto_reload=True,
                include_env_vars=False,
                env_var_prefix="FACTORY_"
            )
            
            assert isinstance(manager, ConfigurationManager)
            assert manager.service_name == "test_factory"
            assert manager.service_version == "2.0.0"
            assert manager.auto_reload is True
            assert manager.include_env_vars is False
            assert manager.env_var_prefix == "FACTORY_"

    def test_factory_with_custom_logger(self):
        """Test factory function with custom logger."""
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.create_span = MagicMock()
        mock_logger.create_span.return_value.__enter__ = Mock()
        mock_logger.create_span.return_value.__exit__ = Mock()
        
        # Create mock environment config
        mock_env_config = EnvironmentConfiguration(
            running_in_docker=False,
            local_settings={},
            local_env_manager=Mock(),
            service_name="test_service",
            service_version="1.0.0",
            reflection_kind="test",
            logger_enable_console=True,
            logger_connection_string=None,
            logger_instrumentation_options={},
            logger_log_level="INFO",
            identity_enable_token_cache=True,
            identity_allow_unencrypted_storage=True,
            identity_custom_credential_options=None,
            identity_connection_string=None,
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = create_configuration_manager(
                environment_configuration=mock_env_config,
                configs_dir=temp_dir,
                logger=mock_logger
            )
            
            assert manager.logger == mock_logger


class TestConfigurationManagerIntegration:
    """Integration tests for ConfigurationManager."""

    def test_realistic_scenario(self):
        """Test a realistic configuration management scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = pathlib.Path(temp_dir) / "configs"
            config_dir.mkdir()
            
            # Create realistic config files
            app_config = {
                "app": {
                    "name": "MyApp",
                    "version": "1.0.0",
                    "debug": False
                },
                "database": {
                    "host": "prod-db.example.com",
                    "port": 5432,
                    "ssl": True
                },
                "features": {
                    "analytics": {"enabled": True},
                    "beta_ui": {"enabled": False}
                }
            }
            
            limits_config = {
                "limits": {
                    "max_requests_per_minute": 1000,
                    "max_upload_size_mb": 100,
                    "session_timeout_minutes": 30
                }
            }
            
            with open(config_dir / "app.json", "w") as f:
                json.dump(app_config, f)
            with open(config_dir / "limits.json", "w") as f:
                json.dump(limits_config, f)
            
            # Set environment variables
            env_vars = {
                "APP_ENV": "production",
                "APP_DEBUG": "false",
                "DATABASE_PASSWORD": "secret123"
            }
            
            with patch.dict(os.environ, env_vars):
                # Create mock environment config for integration test
                integration_env_config = EnvironmentConfiguration(
                    running_in_docker=False,
                    local_settings={},
                    local_env_manager=Mock(),
                    service_name="integration_test",
                    service_version="1.0.0",
                    reflection_kind="test",
                    logger_enable_console=True,
                    logger_connection_string=None,
                    logger_instrumentation_options={},
                    logger_log_level="INFO",
                    identity_enable_token_cache=True,
                    identity_allow_unencrypted_storage=True,
                    identity_custom_credential_options=None,
                    identity_connection_string=None,
                )
                
                manager = create_configuration_manager(
                    environment_configuration=integration_env_config,
                    configs_dir=str(config_dir),
                    auto_reload=True,
                    include_env_vars=True,
                    env_var_prefix="APP_"
                )
                
                # Test various configuration access patterns
                assert manager.get_config("app.name") == "MyApp"
                assert manager.get_config("database.host") == "prod-db.example.com"
                assert manager.get_config("features.analytics.enabled") is True
                assert manager.get_config("limits.max_requests_per_minute") == 1000
                assert manager.get_config("APP_ENV") == "production"
                
                # Test defaults
                assert manager.get_config("nonexistent.key", "default") == "default"
                
                # Test health check
                health = manager.health_check()
                assert health["status"] == "healthy"
                
                # Test repr output
                repr_output = repr(manager)
                assert "integration_test" in repr_output
                assert "app.name" in repr_output
                
                # Test access statistics
                stats = manager.get_access_stats()
                assert stats["total_accesses"] >= 5
                
                # Test filtered reporting
                app_report = manager.get_filtered_report(filter_prefix="app")
                assert "app.name" in app_report
                assert "database.host" not in app_report 


class TestKeyVaultIntegration:
    """Tests for Azure Key Vault integration in ConfigurationManager."""

    @pytest.fixture
    def mock_kv_client(self):
        """Create a mock Key Vault client."""
        kv_client = Mock()
        kv_client.get_secret.return_value = "my_super_secret_value"
        return kv_client

    @pytest.fixture
    def mock_environment_config(self):
        """Create a mock EnvironmentConfiguration for testing."""
        return EnvironmentConfiguration(
            running_in_docker=False,
            local_settings={},
            local_env_manager=Mock(),
            service_name="kv_test_service",
            service_version="1.0.0",
            reflection_kind="test",
            logger_enable_console=True,
            logger_connection_string=None,
            logger_instrumentation_options={},
            logger_log_level="INFO",
            identity_enable_token_cache=True,
            identity_allow_unencrypted_storage=True,
            identity_custom_credential_options=None,
            identity_connection_string=None,
        )

    @pytest.fixture
    def config_manager_with_kv(self, mock_environment_config, mock_kv_client):
        """Create a ConfigurationManager with a mocked Key Vault client."""
        return ConfigurationManager(
            environment_configuration=mock_environment_config,
            keyvault_clients={"my_kv": mock_kv_client}
        )

    def test_get_keyvault_secret_success(self, config_manager_with_kv, mock_kv_client):
        """Test successfully fetching a secret from Key Vault."""
        secret_value = config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret")
        assert secret_value == "my_super_secret_value"
        mock_kv_client.get_secret.assert_called_once_with(secret_name="test-secret")
        
        # Verify it's now in the internal config
        assert config_manager_with_kv.has_config("keyvault.my_kv.test-secret")

    def test_get_keyvault_secret_with_ttl_cached(self, config_manager_with_kv, mock_kv_client):
        """Test that a secret is retrieved from cache if within TTL."""
        # First call fetches from KV
        config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret", ttl=10)
        mock_kv_client.get_secret.assert_called_once_with(secret_name="test-secret")
        
        # Second call should hit the cache
        secret_value = config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret", ttl=10)
        assert secret_value == "my_super_secret_value"
        
        # Assert get_secret was not called again
        mock_kv_client.get_secret.assert_called_once()

    def test_get_keyvault_secret_with_ttl_expired(self, config_manager_with_kv, mock_kv_client):
        """Test that a secret is re-fetched when TTL expires."""
        # First call fetches from KV
        config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret", ttl=1) # 1 minute TTL
        
        # Manually expire the cache entry
        entry = config_manager_with_kv._config_entries["keyvault.my_kv.test-secret"]
        entry.loaded_at = time.time() - 70  # 70 seconds ago, > 1 min
        
        # Second call should re-fetch from KV
        config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret", ttl=1)
        
        assert mock_kv_client.get_secret.call_count == 2
        
    def test_get_keyvault_secret_no_ttl(self, config_manager_with_kv, mock_kv_client):
        """Test that a secret is always fetched when no TTL is provided."""
        config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret", ttl=None)
        config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret", ttl=0)
        config_manager_with_kv.get_keyvault_secret("my_kv", "test-secret")
        
        assert mock_kv_client.get_secret.call_count == 3

    def test_get_keyvault_secret_invalid_client(self, config_manager_with_kv):
        """Test getting a secret from a non-existent Key Vault client."""
        secret_value = config_manager_with_kv.get_keyvault_secret("invalid_kv", "test-secret")
        assert secret_value is None

    def test_get_keyvault_secret_not_found(self, config_manager_with_kv, mock_kv_client):
        """Test getting a non-existent secret from Key Vault."""
        mock_kv_client.get_secret.side_effect = Exception("Secret not found")
        
        secret_value = config_manager_with_kv.get_keyvault_secret("my_kv", "nonexistent-secret")
        
        assert secret_value is None
        mock_kv_client.get_secret.assert_called_once_with(secret_name="nonexistent-secret")

    def test_set_keyvault_secret_remote_only(self, config_manager_with_kv, mock_kv_client):
        """Test setting a secret in Key Vault only."""
        secret_name = "new-secret"
        secret_value = "new-value"

        config_manager_with_kv.set_keyvault_secret("my_kv", secret_name, secret_value)

        # Verify the secret was sent to KV
        mock_kv_client.set_secret.assert_called_once_with(secret_name, str(secret_value))

        # Verify it was not stored locally
        config_key = f"keyvault.my_kv.{secret_name}"
        assert not config_manager_with_kv.has_config(config_key)

    def test_set_keyvault_secret_with_local_cache(self, config_manager_with_kv, mock_kv_client):
        """Test setting a secret and caching it locally."""
        secret_name = "local-secret"
        secret_value = "local-value"

        config_manager_with_kv.set_keyvault_secret("my_kv", secret_name, secret_value, local=True)

        # Verify KV call
        mock_kv_client.set_secret.assert_called_once_with(secret_name, str(secret_value))

        # Verify local cache
        config_key = f"keyvault.my_kv.{secret_name}"
        assert config_manager_with_kv.has_config(config_key)
        assert config_manager_with_kv.get_config(config_key) == secret_value

    def test_set_keyvault_secret_with_local_cache_and_env(self, config_manager_with_kv, mock_kv_client):
        """Test setting a secret, caching it, and setting an env var."""
        secret_name = "env-secret"
        secret_value = "env-value"
        config_key = f"keyvault.my_kv.{secret_name}"

        with patch.dict(os.environ) as mock_env:
            config_manager_with_kv.set_keyvault_secret(
                "my_kv", secret_name, secret_value, local=True, env=True
            )

            # Verify KV call
            mock_kv_client.set_secret.assert_called_once_with(secret_name, str(secret_value))

            # Verify local cache
            assert config_manager_with_kv.get_config(config_key) == secret_value

            # Verify environment variable
            assert config_key in mock_env
            assert mock_env[config_key] == str(secret_value)


class TestLogExecution:
    """Test the LogExecution dataclass functionality."""

    def test_log_execution_creation(self):
        """Test LogExecution dataclass creation with all parameters."""
        log_config = LogExecution(
            log_execution=True,
            log_args=False,
            log_result=True
        )

        assert log_config.log_execution is True
        assert log_config.log_args is False
        assert log_config.log_result is True

    def test_from_config_manager_with_defaults(self):
        """Test LogExecution creation from config manager with default values."""
        mock_config_manager = Mock()
        mock_config_manager.get_config.side_effect = lambda key, default: default

        log_config = LogExecution.from_config_manager(mock_config_manager)

        # Verify config manager was called with correct keys and defaults
        assert mock_config_manager.get_config.call_count == 3

        # Check individual calls
        calls = mock_config_manager.get_config.call_args_list
        assert calls[0] == ((), {"key": "log_execution", "default": True})
        assert calls[1] == ((), {"key": "log_args", "default": False})
        assert calls[2] == ((), {"key": "log_result", "default": False})

        # Verify default values
        assert log_config.log_execution is True
        assert log_config.log_args is False
        assert log_config.log_result is False

    def test_from_config_manager_with_custom_values(self):
        """Test LogExecution creation from config manager with custom configuration values."""
        mock_config_manager = Mock()
        config_values = {
            "log_execution": False,
            "log_args": True,
            "log_result": True
        }
        mock_config_manager.get_config.side_effect = lambda key, default: config_values.get(key, default)

        log_config = LogExecution.from_config_manager(mock_config_manager)

        # Verify custom values are used
        assert log_config.log_execution is False
        assert log_config.log_args is True
        assert log_config.log_result is True

    def test_to_dict_conversion(self):
        """Test LogExecution to_dict method returns correct dictionary structure."""
        log_config = LogExecution(
            log_execution=True,
            log_args=False,
            log_result=True
        )

        result_dict = log_config.to_dict()

        expected_dict = {
            "log_execution": True,
            "log_args": False,
            "log_result": True
        }

        assert result_dict == expected_dict
        assert isinstance(result_dict, dict)
        assert all(isinstance(key, str) for key in result_dict.keys())
        assert all(isinstance(value, bool) for value in result_dict.values())

    def test_integration_with_mock_config_manager(self):
        """Test LogExecution integration with realistic ConfigurationManager behavior."""
        # Mock a ConfigurationManager that returns varied config values
        mock_config_manager = Mock()
        config_responses = {
            "log_execution": "false",  # String from environment variable
            "log_args": True,          # Boolean from JSON config
            "log_result": "enabled"    # String value
        }

        def mock_get_config(key, default):
            return config_responses.get(key, default)

        mock_config_manager.get_config.side_effect = mock_get_config

        log_config = LogExecution.from_config_manager(mock_config_manager)

        # Verify values are retrieved correctly from different sources
        assert log_config.log_execution == "false"    # String from env var
        assert log_config.log_args is True            # Boolean from JSON
        assert log_config.log_result == "enabled"     # String value

        # Test to_dict with mixed value types
        result_dict = log_config.to_dict()
        expected_dict = {
            "log_execution": "false",
            "log_args": True,
            "log_result": "enabled"
        }
        assert result_dict == expected_dict

        # Verify the config manager was called with correct parameters
        assert mock_config_manager.get_config.call_count == 3


class TestLogExecutionWithLoggingDecorator:
    """Test LogExecution dataclass integration with logging decorator functionality."""

    @pytest.fixture
    def mock_azure_logger(self):
        """Create a mock AzureLogger for decorator testing."""
        from azpaddypy.mgmt.logging import AzureLogger
        from unittest.mock import Mock, MagicMock
        import functools
        import asyncio

        logger = Mock(spec=AzureLogger)

        # Mock the tracer and span creation
        mock_tracer = Mock()
        mock_span = Mock()
        mock_span.__enter__ = Mock(return_value=mock_span)
        mock_span.__exit__ = Mock(return_value=None)

        mock_tracer.start_as_current_span = Mock(return_value=mock_span)
        logger.tracer = mock_tracer
        logger._correlation_id = None

        # Mock logging methods
        logger.debug = Mock()
        logger.info = Mock()
        logger.error = Mock()
        logger.log_function_execution = Mock()

        # Create a working trace_function decorator that tracks calls but preserves function behavior
        def mock_trace_function(function_name=None, log_execution=True, log_args=True, log_result=False):
            def decorator(func):
                # Determine if the function is async at decoration time
                is_async = asyncio.iscoroutinefunction(func)

                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    span_name = function_name or f"{func.__module__}.{func.__name__}"
                    with mock_tracer.start_as_current_span(span_name) as span:
                        # Set span attributes to mimic real decorator behavior
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.is_async", True)
                        span.set_attribute("function.decorator.log_args", log_args)
                        span.set_attribute("function.decorator.log_result", log_result)
                        span.set_attribute("function.decorator.log_execution", log_execution)

                        if log_args and args:
                            span.set_attribute("function.args_count", len(args))
                            for i, arg in enumerate(args):
                                span.set_attribute(f"function.arg.arg_{i}", str(arg))

                        if log_args and kwargs:
                            span.set_attribute("function.kwargs_count", len(kwargs))
                            for key, value in kwargs.items():
                                span.set_attribute(f"function.kwarg.{key}", str(value))

                        # Call the actual function
                        result = await func(*args, **kwargs)

                        if log_result and result is not None:
                            span.set_attribute("function.has_result", True)
                            span.set_attribute("function.result_type", type(result).__name__)
                            span.set_attribute("function.result", str(result))

                        if log_execution:
                            logger.log_function_execution(func.__name__, 100.0, True, {})

                        # Set success status
                        from opentelemetry.trace import Status, StatusCode
                        span.set_status(Status(StatusCode.OK))

                        return result

                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    span_name = function_name or f"{func.__module__}.{func.__name__}"
                    with mock_tracer.start_as_current_span(span_name) as span:
                        # Set span attributes to mimic real decorator behavior
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.is_async", False)
                        span.set_attribute("function.decorator.log_args", log_args)
                        span.set_attribute("function.decorator.log_result", log_result)
                        span.set_attribute("function.decorator.log_execution", log_execution)

                        if log_args and args:
                            span.set_attribute("function.args_count", len(args))
                            # Mock parameter inspection for sync functions
                            import inspect
                            try:
                                sig = inspect.signature(func)
                                param_names = list(sig.parameters.keys())
                                for i, arg_value in enumerate(args):
                                    param_name = param_names[i] if i < len(param_names) else f"arg_{i}"
                                    span.set_attribute(f"function.arg.{param_name}", str(arg_value))
                            except Exception:
                                for i, arg in enumerate(args):
                                    span.set_attribute(f"function.arg.arg_{i}", str(arg))

                        if log_args and kwargs:
                            span.set_attribute("function.kwargs_count", len(kwargs))
                            for key, value in kwargs.items():
                                span.set_attribute(f"function.kwarg.{key}", str(value))

                        # Call the actual function
                        result = func(*args, **kwargs)

                        if log_result and result is not None:
                            span.set_attribute("function.has_result", True)
                            span.set_attribute("function.result_type", type(result).__name__)
                            span.set_attribute("function.result", str(result))

                        if log_execution:
                            logger.log_function_execution(func.__name__, 100.0, True, {})

                        # Set success status
                        from opentelemetry.trace import Status, StatusCode
                        span.set_status(Status(StatusCode.OK))

                        return result

                # Return appropriate wrapper based on function type
                if is_async:
                    return async_wrapper
                return sync_wrapper

            return decorator

        logger.trace_function = mock_trace_function

        return logger, mock_span

    def test_sync_function_with_log_execution_config(self, mock_azure_logger):
        """Test synchronous function decorated with LogExecution config parameters."""
        logger, mock_span = mock_azure_logger

        # Create LogExecution config for comprehensive logging
        log_config = LogExecution(
            log_execution=True,
            log_args=True,
            log_result=True
        )

        # Apply decorator with LogExecution config
        @logger.trace_function(**log_config.to_dict())
        def process_data(user_id: int, action: str = "default") -> dict:
            """Sample synchronous function to test decorator integration."""
            return {"user_id": user_id, "action": action, "status": "completed"}

        # Execute the decorated function
        result = process_data(12345, action="update")

        # Verify the function executed correctly
        assert result == {"user_id": 12345, "action": "update", "status": "completed"}

        # Verify tracer was called with function name
        logger.tracer.start_as_current_span.assert_called_once()
        span_name = logger.tracer.start_as_current_span.call_args[0][0]
        assert "process_data" in span_name

        # Verify span attributes were set based on LogExecution config
        span_calls = mock_span.set_attribute.call_args_list
        span_attributes = {call[0][0]: call[0][1] for call in span_calls}

        # Check logging configuration attributes
        assert span_attributes.get("function.decorator.log_args") is True
        assert span_attributes.get("function.decorator.log_result") is True
        assert span_attributes.get("function.decorator.log_execution") is True

        # Check function metadata attributes
        assert span_attributes.get("function.name") == "process_data"
        assert span_attributes.get("function.is_async") is False

        # Check that arguments were logged (log_args=True)
        assert span_attributes.get("function.args_count") == 1
        assert span_attributes.get("function.kwargs_count") == 1
        assert span_attributes.get("function.arg.user_id") == "12345"
        assert span_attributes.get("function.kwarg.action") == "update"

        # Check that result was logged (log_result=True)
        assert span_attributes.get("function.has_result") is True
        assert span_attributes.get("function.result_type") == "dict"

        # Verify function execution logging was called (log_execution=True)
        logger.log_function_execution.assert_called_once()
        exec_call = logger.log_function_execution.call_args
        assert exec_call[0][0] == "process_data"  # function name
        assert exec_call[0][2] is True  # success flag

    def test_async_function_with_minimal_log_config(self, mock_azure_logger):
        """Test asynchronous function with minimal LogExecution configuration."""
        import asyncio

        logger, mock_span = mock_azure_logger

        # Create LogExecution config with minimal logging
        log_config = LogExecution(
            log_execution=False,  # Disable execution logging
            log_args=False,       # Disable argument logging
            log_result=False      # Disable result logging
        )

        # Apply decorator with minimal LogExecution config
        @logger.trace_function(**log_config.to_dict())
        async def async_process_task(task_id: str, priority: int = 1) -> bool:
            """Sample asynchronous function to test decorator integration."""
            await asyncio.sleep(0.001)  # Simulate async work
            return True

        # Execute the decorated async function
        async def run_test():
            result = await async_process_task("task-123", priority=5)
            assert result is True

            # Verify tracer was called
            logger.tracer.start_as_current_span.assert_called_once()

            # Verify span attributes reflect minimal logging config
            span_calls = mock_span.set_attribute.call_args_list
            span_attributes = {call[0][0]: call[0][1] for call in span_calls}

            # Check logging configuration attributes match our config
            assert span_attributes.get("function.decorator.log_args") is False
            assert span_attributes.get("function.decorator.log_result") is False
            assert span_attributes.get("function.decorator.log_execution") is False

            # Check basic function metadata is still present
            assert span_attributes.get("function.name") == "async_process_task"
            assert span_attributes.get("function.is_async") is True

            # Verify arguments were NOT logged (log_args=False)
            assert "function.arg.task_id" not in span_attributes
            assert "function.kwarg.priority" not in span_attributes

            # Verify result was NOT logged (log_result=False)
            assert "function.result" not in span_attributes

            # Verify function execution logging was NOT called (log_execution=False)
            logger.log_function_execution.assert_not_called()

        # Run the async test
        asyncio.run(run_test())

    def test_function_with_dynamic_log_config_from_config_manager(self, mock_azure_logger):
        """Test function decorated with LogExecution config loaded dynamically from ConfigurationManager."""
        logger, mock_span = mock_azure_logger

        # Mock ConfigurationManager with specific logging configuration
        mock_config_manager = Mock()
        config_values = {
            "log_execution": True,
            "log_args": False,     # Don't log sensitive arguments
            "log_result": True     # Log results for debugging
        }
        mock_config_manager.get_config.side_effect = lambda key, default: config_values.get(key, default)

        # Create LogExecution from ConfigurationManager (simulating real usage)
        log_config = LogExecution.from_config_manager(mock_config_manager)

        # Define a function that processes sensitive data
        @logger.trace_function(**log_config.to_dict())
        def process_payment(card_number: str, amount: float, currency: str = "USD") -> dict:
            """Function that processes sensitive payment data."""
            # Simulate payment processing
            processed_amount = amount * 1.0  # No fees for test
            return {
                "transaction_id": "txn_12345",
                "amount": processed_amount,
                "currency": currency,
                "status": "processed"
            }

        # Execute function with sensitive data
        result = process_payment("4111-1111-1111-1111", 99.99, currency="EUR")

        # Verify function executed correctly
        expected_result = {
            "transaction_id": "txn_12345",
            "amount": 99.99,
            "currency": "EUR",
            "status": "processed"
        }
        assert result == expected_result

        # Verify configuration was loaded from ConfigurationManager
        assert mock_config_manager.get_config.call_count == 3

        # Verify tracer interaction
        logger.tracer.start_as_current_span.assert_called_once()

        # Verify span attributes reflect our security-conscious configuration
        span_calls = mock_span.set_attribute.call_args_list
        span_attributes = {call[0][0]: call[0][1] for call in span_calls}

        # Check configuration was applied correctly
        assert span_attributes.get("function.decorator.log_args") is False    # Sensitive data protection
        assert span_attributes.get("function.decorator.log_result") is True   # Results are safe to log
        assert span_attributes.get("function.decorator.log_execution") is True # Performance monitoring

        # Verify sensitive arguments were NOT logged (log_args=False)
        assert "function.arg.card_number" not in span_attributes
        assert "function.kwarg.amount" not in span_attributes
        assert "function.kwarg.currency" not in span_attributes

        # Verify result WAS logged (log_result=True)
        assert span_attributes.get("function.has_result") is True
        assert span_attributes.get("function.result_type") == "dict"
        result_logged = span_attributes.get("function.result")
        assert "transaction_id" in result_logged
        assert "status" in result_logged

        # Verify execution logging was called (log_execution=True)
        logger.log_function_execution.assert_called_once()
        exec_call = logger.log_function_execution.call_args
        assert exec_call[0][0] == "process_payment"
        assert exec_call[0][2] is True  # success flag

        # Verify span status was set to success
        mock_span.set_status.assert_called()
        status_call = mock_span.set_status.call_args[0][0]
        assert hasattr(status_call, 'status_code')