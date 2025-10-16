"""Tests for Azure configuration management module (now in azpaddypy.builder)."""

import pytest
import os
import sys
from unittest.mock import patch, Mock, MagicMock

from azpaddypy.mgmt.logging import AzureLogger
from azpaddypy.mgmt.identity import AzureIdentity
from azpaddypy.resources.keyvault import AzureKeyVault
from azpaddypy.resources.storage import AzureStorage


def create_mock_env_config():
    """Create a mock environment configuration for testing."""
    from azpaddypy.builder import EnvironmentConfiguration
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
        # Note: keyvault and storage fields removed - now handled in service creation
    )


class TestConfigurationLoading:
    """Test configuration loading from environment variables."""

    def setup_method(self):
        """Clean up imports before each test."""
        # Clear azpaddypy modules for clean test isolation
        modules_to_clear = [m for m in sys.modules if m.startswith('azpaddypy')]
        for module in modules_to_clear:
            del sys.modules[module]

    def teardown_method(self):
        """Clean up after each test."""
        # Clear azpaddypy modules for clean test isolation
        modules_to_clear = [m for m in sys.modules if m.startswith('azpaddypy')]
        for module in modules_to_clear:
            del sys.modules[module]

    def test_default_configuration(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            from azpaddypy.builder.directors import ConfigurationSetupDirector

            config = ConfigurationSetupDirector.build_default_config()
            assert isinstance(config.service_name, str)
            assert isinstance(config.service_version, str)
            assert isinstance(config.logger_enable_console, bool)
            assert isinstance(config.identity_enable_token_cache, bool)
            # Note: keyvault/storage fields removed from EnvironmentConfiguration


class TestAzureManagementBuilder:
    """Test Azure management builder."""

    @patch('azpaddypy.mgmt.local_env_manager.create_local_env_manager')
    @patch('azpaddypy.resources.keyvault.create_azure_keyvault')
    @patch('azpaddypy.mgmt.identity.create_azure_identity')
    @patch('azpaddypy.mgmt.logging.create_app_logger')
    def test_management_builder_complete(self, mock_logger, mock_identity, mock_keyvault, mock_env):
        """Test complete management builder flow."""
        from azpaddypy.builder import AzureManagementBuilder

        mock_logger.return_value = Mock(spec=AzureLogger)
        mock_identity.return_value = Mock(spec=AzureIdentity)
        mock_keyvault.return_value = Mock(spec=AzureKeyVault)
        mock_env.return_value = Mock()

        env_config = create_mock_env_config()
        config = (AzureManagementBuilder(env_config)
                  .with_logger()
                  .with_identity()
                  .with_keyvault()
                  .build())

        assert config.logger is not None
        assert config.identity is not None
        assert config.local_env_manager is not None
        assert config.validate()

    def test_management_builder_order_enforcement(self):
        """Test builder enforces initialization order."""
        from azpaddypy.builder import AzureManagementBuilder

        env_config = create_mock_env_config()
        builder = AzureManagementBuilder(env_config)

        # Should fail if identity called before logger
        with pytest.raises(ValueError, match="Identity requires logger"):
            builder.with_identity()

        # Should fail if keyvault called before identity
        with pytest.raises(ValueError, match="Key Vault requires identity"):
            builder.with_keyvault()

    @patch('azpaddypy.mgmt.logging.create_app_logger')
    def test_management_builder_validation(self, mock_logger):
        """Test management configuration validation."""
        from azpaddypy.builder import AzureManagementBuilder

        mock_logger.return_value = Mock(spec=AzureLogger)

        env_config = create_mock_env_config()
        builder = AzureManagementBuilder(env_config).with_logger()

        # Should fail if build called before complete configuration
        with pytest.raises(ValueError, match="Management configuration incomplete"):
            builder.build()


class TestAzureResourceBuilder:
    """Test Azure resource builder."""

    @patch('azpaddypy.builder.configuration.create_azure_storage')
    def test_resource_builder_with_management(self, mock_storage):
        """Test resource builder with management configuration."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration

        mock_storage.return_value = Mock(spec=AzureStorage)

        # Create mock management config
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = Mock(spec=AzureKeyVault)

        env_config = create_mock_env_config()
        config = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_storage()
                  .build())

        assert config.storage_account is not None
        assert config.validate()

    def test_resource_builder_requires_management(self):
        """Test resource builder requires valid management config."""
        from azpaddypy.builder import AzureResourceBuilder

        env_config = create_mock_env_config()
        # Should fail with invalid management config
        with pytest.raises(ValueError, match="Valid management configuration is required"):
            AzureResourceBuilder(None, env_config)

        # Should fail with invalid management config
        invalid_mgmt = Mock()
        invalid_mgmt.validate.return_value = False
        with pytest.raises(ValueError, match="Valid management configuration is required"):
            AzureResourceBuilder(invalid_mgmt, env_config)

    def test_resource_builder_no_resources(self):
        """Test resource builder with no resources."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration

        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)

        env_config = create_mock_env_config()
        config = AzureResourceBuilder(mgmt_config, env_config).build()

        assert config.storage_account is None
        assert config.validate()


class TestMultipleKeyVaults:
    """Test multiple Key Vault functionality."""

    @patch('azpaddypy.mgmt.local_env_manager.create_local_env_manager')
    @patch('azpaddypy.builder.configuration.create_azure_keyvault')
    @patch('azpaddypy.mgmt.identity.create_azure_identity')
    @patch('azpaddypy.mgmt.logging.create_app_logger')
    def test_multiple_keyvaults(self, mock_logger, mock_identity, mock_keyvault, mock_env):
        """Test multiple Key Vaults configuration."""
        from azpaddypy.builder import AzureManagementBuilder

        mock_logger.return_value = Mock(spec=AzureLogger)
        mock_identity.return_value = Mock(spec=AzureIdentity)
        mock_keyvault.return_value = Mock(spec=AzureKeyVault)
        mock_env.return_value = Mock()

        env_config = create_mock_env_config()
        config = (AzureManagementBuilder(env_config)
                  .with_logger()
                  .with_identity()
                  .with_keyvault("default", "https://default.vault.azure.net/")
                  .with_keyvault("prod", "https://prod.vault.azure.net/")
                  .with_keyvault("dev", "https://dev.vault.azure.net/")
                  .build())

        assert len(config.keyvaults) == 3
        assert config.get_keyvault("default") is not None
        assert config.get_keyvault("prod") is not None
        assert config.get_keyvault("dev") is not None
        assert config.get_primary_keyvault() is not None  # Should return default
        assert config.keyvault is not None  # Backward compatibility

        # Verify creation was called for each keyvault
        assert mock_keyvault.call_count == 3

    @patch('azpaddypy.mgmt.local_env_manager.create_local_env_manager')
    @patch('azpaddypy.builder.configuration.create_azure_keyvault')
    @patch('azpaddypy.mgmt.identity.create_azure_identity')
    @patch('azpaddypy.mgmt.logging.create_app_logger')
    def test_named_keyvaults_with_env_config(self, mock_logger, mock_identity, mock_keyvault, mock_env):
        """Test named Key Vaults with environment configuration fallback."""
        from azpaddypy.builder import AzureManagementBuilder, EnvironmentConfiguration
        
        mock_logger.return_value = Mock(spec=AzureLogger)
        mock_identity.return_value = Mock(spec=AzureIdentity)
        mock_keyvault.return_value = Mock(spec=AzureKeyVault)
        mock_env.return_value = Mock()

        # Create custom environment config with keyvault URL
        env_config = EnvironmentConfiguration(
            running_in_docker=False,
            local_settings={},
            local_env_manager=Mock(),  # Add mock local env manager
            service_name="test-service",
            service_version="1.0.0",
            reflection_kind="app",
            logger_enable_console=True,
            logger_connection_string=None,
            logger_instrumentation_options={},
            logger_log_level="INFO",
            identity_enable_token_cache=True,
            identity_allow_unencrypted_storage=True,
            identity_custom_credential_options=None,
            identity_connection_string=None,
            # Note: keyvault and storage fields removed - now handled in service creation
        )

        # Set environment variable for default keyvault (since keyvault config is read directly now)
        with patch.dict(os.environ, {"key_vault_uri": "https://default-env.vault.azure.net/"}, clear=False):
            config = (AzureManagementBuilder(env_config)
                      .with_logger()
                      .with_identity()
                      .with_keyvault("default")  # Should use env var key_vault_uri
                      .with_keyvault("prod", "https://prod.vault.azure.net/")  # Explicit URL
                      .build())

        assert len(config.keyvaults) == 2
        
        # Verify the correct URLs were used
        calls = mock_keyvault.call_args_list
        default_url = calls[0][1]['vault_url']
        prod_url = calls[1][1]['vault_url']
        
        assert default_url == "https://default-env.vault.azure.net/"
        assert prod_url == "https://prod.vault.azure.net/"

    def test_duplicate_keyvault_name_fails(self):
        """Test that duplicate Key Vault names raise an error."""
        from azpaddypy.builder import AzureManagementBuilder

        with patch('azpaddypy.mgmt.logging.create_app_logger') as mock_logger, \
             patch('azpaddypy.mgmt.identity.create_azure_identity') as mock_identity, \
             patch('azpaddypy.mgmt.local_env_manager.create_local_env_manager') as mock_env:
            
            mock_logger.return_value = Mock(spec=AzureLogger)
            mock_identity.return_value = Mock(spec=AzureIdentity)
            mock_env.return_value = Mock()

            env_config = create_mock_env_config()
            builder = (AzureManagementBuilder(env_config)
                      .with_logger()
                      .with_identity()
                      .with_keyvault("default", "https://first.vault.azure.net/"))

            # Should fail on duplicate name
            with pytest.raises(ValueError, match="Key Vault 'default' already configured"):
                builder.with_keyvault("default", "https://second.vault.azure.net/")

    def test_keyvault_backward_compatibility(self):
        """Test backward compatibility properties."""
        from azpaddypy.builder import AzureManagementConfiguration

        config = AzureManagementConfiguration(
            logger=Mock(spec=AzureLogger),
            local_env_manager=Mock(),
            identity=Mock(spec=AzureIdentity),
            keyvaults={}
        )

        # No keyvaults configured
        assert config.keyvault is None
        assert config.get_keyvault("default") is None
        assert config.get_primary_keyvault() is None

        # Add some keyvaults
        default_kv = Mock(spec=AzureKeyVault)
        prod_kv = Mock(spec=AzureKeyVault)
        other_kv = Mock(spec=AzureKeyVault)
        
        config.keyvaults["default"] = default_kv
        config.keyvaults["prod"] = prod_kv
        config.keyvaults["other"] = other_kv

        # Test backward compatibility
        assert config.keyvault is default_kv
        assert config.get_keyvault("default") is default_kv
        assert config.get_keyvault("prod") is prod_kv
        assert config.get_keyvault("other") is other_kv
        assert config.get_primary_keyvault() is default_kv

    def test_get_keyvault_methods(self):
        """Test keyvault access methods."""
        from azpaddypy.builder import AzureManagementConfiguration

        config = AzureManagementConfiguration(
            logger=Mock(spec=AzureLogger),
            local_env_manager=Mock(),
            identity=Mock(spec=AzureIdentity),
            keyvaults={}
        )

        # Test with no default, but has other keyvaults
        prod_kv = Mock(spec=AzureKeyVault)
        dev_kv = Mock(spec=AzureKeyVault)
        
        config.keyvaults["prod"] = prod_kv
        config.keyvaults["dev"] = dev_kv

        # get_primary_keyvault should return first available if no default
        assert config.get_primary_keyvault() in [prod_kv, dev_kv]
        assert config.get_keyvault("nonexistent") is None

    @patch('azpaddypy.mgmt.local_env_manager.create_local_env_manager')
    @patch('azpaddypy.builder.configuration.create_azure_keyvault')
    @patch('azpaddypy.mgmt.identity.create_azure_identity')
    @patch('azpaddypy.mgmt.logging.create_app_logger')
    def test_keyvault_configuration_options(self, mock_logger, mock_identity, mock_keyvault, mock_env):
        """Test Key Vault configuration with different options."""
        from azpaddypy.builder import AzureManagementBuilder

        mock_logger.return_value = Mock(spec=AzureLogger)
        mock_identity.return_value = Mock(spec=AzureIdentity)
        mock_keyvault.return_value = Mock(spec=AzureKeyVault)
        mock_env.return_value = Mock()

        env_config = create_mock_env_config()
        config = (AzureManagementBuilder(env_config)
                  .with_logger()
                  .with_identity()
                  .with_keyvault("secrets-only", "https://secrets.vault.azure.net/", 
                                enable_secrets=True, enable_keys=False, enable_certificates=False)
                  .with_keyvault("keys-only", "https://keys.vault.azure.net/",
                                enable_secrets=False, enable_keys=True, enable_certificates=False)
                  .build())

        assert len(config.keyvaults) == 2
        assert mock_keyvault.call_count == 2

        # Verify configuration options were passed correctly
        calls = mock_keyvault.call_args_list
        
        # First call (secrets-only)
        secrets_call = calls[0][1]
        assert secrets_call['enable_secrets'] is True
        assert secrets_call['enable_keys'] is False
        assert secrets_call['enable_certificates'] is False
        
        # Second call (keys-only)
        keys_call = calls[1][1]
        assert keys_call['enable_secrets'] is False
        assert keys_call['enable_keys'] is True
        assert keys_call['enable_certificates'] is False


class TestCosmosDBBuilder:
    """Test CosmosDB functionality in resource builder."""

    @patch('azpaddypy.builder.configuration.create_azure_cosmosdb')
    def test_resource_builder_with_cosmosdb(self, mock_cosmosdb):
        """Test resource builder with CosmosDB."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration
        from azpaddypy.resources.cosmosdb import AzureCosmosDB

        mock_cosmosdb.return_value = Mock(spec=AzureCosmosDB)

        # Create mock management config
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = None

        env_config = create_mock_env_config()
        
        with patch.dict(os.environ, {"COSMOS_ENDPOINT": "https://test.documents.azure.com:443/"}, clear=False):
            config = (AzureResourceBuilder(mgmt_config, env_config)
                      .with_cosmosdb()
                      .build())

        assert config.cosmosdb_client is not None
        assert config.get_cosmosdb("default") is not None
        assert config.validate()
        mock_cosmosdb.assert_called_once()

    @patch('azpaddypy.builder.configuration.create_azure_cosmosdb')
    def test_multiple_cosmosdb_clients(self, mock_cosmosdb):
        """Test multiple CosmosDB clients configuration."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration
        from azpaddypy.resources.cosmosdb import AzureCosmosDB

        mock_cosmosdb.return_value = Mock(spec=AzureCosmosDB)

        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = None

        env_config = create_mock_env_config()
        config = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_cosmosdb("default", "https://default.documents.azure.com:443/")
                  .with_cosmosdb("prod", "https://prod.documents.azure.com:443/")
                  .with_cosmosdb("dev", "https://dev.documents.azure.com:443/")
                  .build())

        assert len(config.cosmosdb_clients) == 3
        assert config.get_cosmosdb("default") is not None
        assert config.get_cosmosdb("prod") is not None
        assert config.get_cosmosdb("dev") is not None
        assert config.get_primary_cosmosdb() is not None
        assert config.cosmosdb_client is not None  # Backward compatibility

        # Verify creation was called for each cosmosdb
        assert mock_cosmosdb.call_count == 3

    @patch('azpaddypy.builder.configuration.create_azure_cosmosdb')
    def test_cosmosdb_auto_construct_endpoint(self, mock_cosmosdb):
        """Test CosmosDB endpoint auto-construction from KeyVault."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration
        from azpaddypy.resources.cosmosdb import AzureCosmosDB

        mock_cosmosdb.return_value = Mock(spec=AzureCosmosDB)

        # Create mock keyvault with project secrets
        mock_keyvault = Mock()
        mock_keyvault.get_secret.side_effect = lambda key: {
            "project-code": "myproject",
            "resource-group-environment": "dev"
        }.get(key)

        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = mock_keyvault

        env_config = create_mock_env_config()
        config = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_cosmosdb("default")  # Should auto-construct
                  .build())

        # Verify auto-constructed endpoint was used
        call_args = mock_cosmosdb.call_args[1]
        expected_endpoint = "https://coscas-promptmgmt-myproject-dev.documents.azure.com:443/"
        assert call_args['endpoint'] == expected_endpoint

    @patch('azpaddypy.builder.configuration.create_azure_cosmosdb')
    def test_duplicate_cosmosdb_name_fails(self, mock_cosmosdb):
        """Test that duplicate CosmosDB names raise an error."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration
        from azpaddypy.resources.cosmosdb import AzureCosmosDB

        mock_cosmosdb.return_value = Mock(spec=AzureCosmosDB)

        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)

        env_config = create_mock_env_config()
        builder = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_cosmosdb("default", "https://first.documents.azure.com:443/"))

        # Should fail on duplicate name
        with pytest.raises(ValueError, match="CosmosDB client 'default' already configured"):
            builder.with_cosmosdb("default", "https://second.documents.azure.com:443/")

    def test_cosmosdb_backward_compatibility(self):
        """Test backward compatibility properties for CosmosDB."""
        from azpaddypy.builder import AzureResourceConfiguration
        from azpaddypy.resources.cosmosdb import AzureCosmosDB

        config = AzureResourceConfiguration(cosmosdb_clients={})

        # No CosmosDB clients configured
        assert config.cosmosdb_client is None
        assert config.get_cosmosdb("default") is None
        assert config.get_primary_cosmosdb() is None

        # Add some CosmosDB clients
        default_cosmos = Mock(spec=AzureCosmosDB)
        prod_cosmos = Mock(spec=AzureCosmosDB)
        other_cosmos = Mock(spec=AzureCosmosDB)
        
        config.cosmosdb_clients["default"] = default_cosmos
        config.cosmosdb_clients["prod"] = prod_cosmos
        config.cosmosdb_clients["other"] = other_cosmos

        # Test backward compatibility
        assert config.cosmosdb_client is default_cosmos
        assert config.get_cosmosdb("default") is default_cosmos
        assert config.get_cosmosdb("prod") is prod_cosmos
        assert config.get_cosmosdb("other") is other_cosmos
        assert config.get_primary_cosmosdb() is default_cosmos


class TestMultipleStorageAccounts:
    """Test multiple storage account functionality."""

    @patch('azpaddypy.builder.configuration.create_azure_storage')
    def test_multiple_storage_accounts(self, mock_storage):
        """Test multiple storage accounts configuration."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration

        mock_storage.return_value = Mock(spec=AzureStorage)

        # Create mock management config
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = None

        env_config = create_mock_env_config()
        config = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_storage("default", "https://default.blob.core.windows.net/")
                  .with_storage("backup", "https://backup.blob.core.windows.net/")
                  .with_storage("archive", "https://archive.blob.core.windows.net/")
                  .build())

        assert len(config.storage_accounts) == 3
        assert config.get_storage("default") is not None
        assert config.get_storage("backup") is not None
        assert config.get_storage("archive") is not None
        assert config.get_primary_storage() is not None  # Should return default
        assert config.storage_account is not None  # Backward compatibility

        # Verify creation was called for each storage account
        assert mock_storage.call_count == 3

    @patch('azpaddypy.builder.configuration.create_azure_storage')
    def test_named_storage_accounts_with_auto_construct(self, mock_storage):
        """Test named storage accounts with auto-constructed URLs."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration

        mock_storage.return_value = Mock(spec=AzureStorage)

        # Create mock management config with keyvault
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        
        # Mock keyvault with secrets
        mock_keyvault = Mock()
        mock_keyvault.get_secret.side_effect = lambda key: {
            "project-code": "test",
            "resource-group-environment": "dev"
        }[key]
        mgmt_config.keyvault = mock_keyvault

        env_config = create_mock_env_config()
        config = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_storage("default")  # Should use stqueuetestdev
                  .with_storage("backup")   # Should use stbackuptestdev
                  .with_storage("archive")  # Should use starchivetestdev
                  .build())

        assert len(config.storage_accounts) == 3
        
        # Verify the correct URLs were constructed
        calls = mock_storage.call_args_list
        default_url = calls[0][1]['account_url']
        backup_url = calls[1][1]['account_url']
        archive_url = calls[2][1]['account_url']
        
        assert "stqueuetestdev" in default_url
        assert "stbackuptestdev" in backup_url
        assert "starchivetestdev" in archive_url

    def test_duplicate_storage_account_name_fails(self):
        """Test that duplicate storage account names raise an error."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration

        # Create mock management config
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = None

        env_config = create_mock_env_config()
        builder = AzureResourceBuilder(mgmt_config, env_config)
        builder.with_storage("test", "https://test1.blob.core.windows.net/")
        
        # Should fail when trying to add another storage with the same name
        with pytest.raises(ValueError, match="Storage account 'test' already configured"):
            builder.with_storage("test", "https://test2.blob.core.windows.net/")

    def test_storage_account_backward_compatibility(self):
        """Test backward compatibility for single storage account access."""
        from azpaddypy.builder import AzureResourceConfiguration

        # Test with no storage accounts
        config = AzureResourceConfiguration()
        assert config.storage_account is None

        # Test with default storage account
        mock_storage_default = Mock()
        config = AzureResourceConfiguration(storage_accounts={"default": mock_storage_default})
        assert config.storage_account == mock_storage_default

        # Test with multiple storage accounts - should return default
        mock_storage_backup = Mock()
        config = AzureResourceConfiguration(storage_accounts={
            "default": mock_storage_default,
            "backup": mock_storage_backup
        })
        assert config.storage_account == mock_storage_default

        # Test with multiple storage accounts but no default - should return first
        config = AzureResourceConfiguration(storage_accounts={
            "backup": mock_storage_backup,
            "archive": Mock()
        })
        assert config.storage_account == mock_storage_backup

    def test_get_storage_methods(self):
        """Test storage account getter methods."""
        from azpaddypy.builder import AzureResourceConfiguration

        mock_default = Mock()
        mock_backup = Mock()
        mock_archive = Mock()

        config = AzureResourceConfiguration(storage_accounts={
            "default": mock_default,
            "backup": mock_backup,
            "archive": mock_archive
        })

        # Test get_storage method
        assert config.get_storage("default") == mock_default
        assert config.get_storage("backup") == mock_backup
        assert config.get_storage("archive") == mock_archive
        assert config.get_storage("nonexistent") is None

        # Test get_primary_storage method
        assert config.get_primary_storage() == mock_default

        # Test get_primary_storage when no default exists
        config_no_default = AzureResourceConfiguration(storage_accounts={
            "backup": mock_backup,
            "archive": mock_archive
        })
        primary = config_no_default.get_primary_storage()
        assert primary in [mock_backup, mock_archive]

    @patch('azpaddypy.builder.configuration.create_azure_storage')
    def test_storage_account_configuration_options(self, mock_storage):
        """Test storage account configuration with different options."""
        from azpaddypy.builder import AzureResourceBuilder, AzureManagementConfiguration

        mock_storage.return_value = Mock(spec=AzureStorage)

        # Create mock management config
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = None

        env_config = create_mock_env_config()
        config = (AzureResourceBuilder(mgmt_config, env_config)
                  .with_storage("default", "https://default.blob.core.windows.net/",
                               enable_blob=True, enable_file=False, enable_queue=True)
                  .with_storage("backup", "https://backup.blob.core.windows.net/",
                               enable_blob=False, enable_file=True, enable_queue=False)
                  .build())

        assert len(config.storage_accounts) == 2
        
        # Verify storage creation was called with correct parameters
        calls = mock_storage.call_args_list
        
        # Check first storage account (default)
        default_call = calls[0][1]
        assert default_call['enable_blob_storage'] is True
        assert default_call['enable_file_storage'] is False
        assert default_call['enable_queue_storage'] is True
        
        # Check second storage account (backup)
        backup_call = calls[1][1]
        assert backup_call['enable_blob_storage'] is False
        assert backup_call['enable_file_storage'] is True
        assert backup_call['enable_queue_storage'] is False


class TestDirectorPatterns:
    """Test director patterns for common configurations."""

    @patch('azpaddypy.mgmt.local_env_manager.create_local_env_manager')
    @patch('azpaddypy.resources.keyvault.create_azure_keyvault')
    @patch('azpaddypy.mgmt.identity.create_azure_identity')
    @patch('azpaddypy.mgmt.logging.create_app_logger')
    def test_management_director_default(self, mock_logger, mock_identity, mock_keyvault, mock_env):
        """Test default management director."""
        from azpaddypy.builder.directors import AzureManagementDirector, ConfigurationSetupDirector

        mock_logger.return_value = Mock(spec=AzureLogger)
        mock_identity.return_value = Mock(spec=AzureIdentity)
        mock_env.return_value = Mock()

        # Get environment configuration first
        env_config = ConfigurationSetupDirector.build_default_config()
        config = AzureManagementDirector.build_default_config(env_config)

        assert config.logger is not None
        assert config.identity is not None
        assert config.validate()

    def test_configuration_director_default(self):
        """Test default configuration director."""
        from azpaddypy.builder.directors import AzureResourceDirector, ConfigurationSetupDirector, AzureManagementDirector

        # Build the environment configuration
        env_config = ConfigurationSetupDirector.build_default_config()
        
        # Build the management configuration  
        mgmt_config = AzureManagementDirector.build_default_config(env_config)
        
        # Build the combined configuration
        config = AzureResourceDirector.build_default_config(env_config, mgmt_config)

        # Verify the configuration structure is correct
        assert config.management.logger is not None
        assert config.management.identity is not None
        assert config.management.local_env_manager is not None
        assert config.validate()

        # Verify the configuration has both management and resource components
        assert hasattr(config, 'management')
        assert hasattr(config, 'resources')
        
        # Resources may or may not have storage depending on environment
        # but the structure should be valid
        assert hasattr(config.resources, 'storage_account')

    def test_setup_director_patterns(self):
        """Test setup director patterns."""
        from azpaddypy.builder.directors import ConfigurationSetupDirector

        # Test default setup
        default_config = ConfigurationSetupDirector.build_default_config()

        assert isinstance(default_config.service_name, str)
        assert isinstance(default_config.logger_log_level, str)
        assert isinstance(default_config.identity_enable_token_cache, bool)
        assert default_config.local_env_manager is not None




class TestConfigurationValidation:
    """Test configuration validation."""

    def test_management_config_validation(self):
        """Test management configuration validation."""
        from azpaddypy.builder import AzureManagementConfiguration

        # Missing logger
        config = AzureManagementConfiguration(
            logger=None,
            local_env_manager=Mock(),
            identity=Mock(),
        )
        with pytest.raises(ValueError, match="Logger is required"):
            config.validate()

        # Missing identity
        config = AzureManagementConfiguration(
            logger=Mock(),
            local_env_manager=Mock(),
            identity=None,
        )
        with pytest.raises(ValueError, match="Identity is required"):
            config.validate()

        # Missing local env manager
        config = AzureManagementConfiguration(
            logger=Mock(),
            local_env_manager=None,
            identity=Mock(),
        )
        with pytest.raises(ValueError, match="Local env manager is required"):
            config.validate()

    def test_resource_config_validation(self):
        """Test resource configuration validation."""
        from azpaddypy.builder import AzureResourceConfiguration

        # Empty config should be valid
        config = AzureResourceConfiguration()
        assert config.validate()

        # Config with storage should be valid
        config = AzureResourceConfiguration(storage_accounts={"default": Mock()})
        assert config.validate()

        # Test backward compatibility property
        config = AzureResourceConfiguration(storage_accounts={"default": Mock()})
        assert config.storage_account is not None

        # Test multiple storage accounts
        config = AzureResourceConfiguration(storage_accounts={"default": Mock(), "backup": Mock()})
        assert config.validate()
        assert config.get_storage("default") is not None
        assert config.get_storage("backup") is not None
        assert config.get_primary_storage() is not None

        # Test CosmosDB configuration
        config = AzureResourceConfiguration(cosmosdb_clients={"default": Mock()})
        assert config.validate()
        assert config.cosmosdb_client is not None

        # Test multiple CosmosDB clients
        config = AzureResourceConfiguration(cosmosdb_clients={"default": Mock(), "prod": Mock()})
        assert config.validate()
        assert config.get_cosmosdb("default") is not None
        assert config.get_cosmosdb("prod") is not None
        assert config.get_primary_cosmosdb() is not None

        # Test combined storage and CosmosDB configuration
        config = AzureResourceConfiguration(
            storage_accounts={"default": Mock()},
            cosmosdb_clients={"default": Mock()}
        )
        assert config.validate()
        assert config.storage_account is not None
        assert config.cosmosdb_client is not None

    def test_combined_config_validation(self):
        """Test combined configuration validation."""
        from azpaddypy.builder import AzureConfiguration, AzureManagementConfiguration, AzureResourceConfiguration

        mgmt_config = AzureManagementConfiguration(
            logger=Mock(),
            local_env_manager=Mock(),
            identity=Mock()
        )
        resource_config = AzureResourceConfiguration()

        config = AzureConfiguration(management=mgmt_config, resources=resource_config)
        assert config.validate()


class TestDirectImports:
    """Test direct service imports."""

    def setup_method(self):
        """Clean up imports before each test."""
        if 'mgmt_config' in sys.modules:
            del sys.modules['mgmt_config']

    def teardown_method(self):
        """Clean up after each test."""
        if 'mgmt_config' in sys.modules:
            del sys.modules['mgmt_config']

    def test_direct_service_imports_removed(self):
        """Test that direct service imports are no longer available."""
        with patch.dict(os.environ, {}, clear=True):
            import azpaddypy.builder.configuration as mgmt_config

            # These should no longer be available
            assert not hasattr(mgmt_config, 'logger')
            assert not hasattr(mgmt_config, 'identity')
            assert not hasattr(mgmt_config, 'local_env_manager')
            assert not hasattr(mgmt_config, 'keyvault')
            assert not hasattr(mgmt_config, 'storage_account')

    def test_module_exports(self):
        """Test module exports correct symbols."""
        with patch.dict(os.environ, {}, clear=True):
            import azpaddypy.builder as mgmt_config

            expected_exports = [
                # Configuration setup classes
                "ConfigurationSetupBuilder", "EnvironmentConfiguration",
                
                # Builder pattern classes
                "AzureManagementBuilder", "AzureResourceBuilder", 
                "AzureManagementConfiguration", "AzureResourceConfiguration",
                "AzureConfiguration",
                
                # Director pattern classes
                "ConfigurationSetupDirector", "AzureManagementDirector", "AzureResourceDirector"  # Backward compatibility alias
            ]

            assert mgmt_config.__all__ == expected_exports

            # Verify all exported symbols exist
            for symbol in expected_exports:
                assert hasattr(mgmt_config, symbol)


class TestConfigurationSetupBuilder:
    """Test configuration setup builder."""

    def test_setup_builder_complete_flow(self):
        """Test complete setup builder flow."""
        from azpaddypy.builder import ConfigurationSetupBuilder

        config = (ConfigurationSetupBuilder()
                  .with_local_env_management()  # FIRST: Load .env files
                  .with_environment_detection()
                  .with_service_configuration()
                  .with_logging_configuration()
                  .with_identity_configuration()
                  .build())  # keyvault/storage configs removed - handled in service creation

        assert isinstance(config.running_in_docker, bool)
        assert isinstance(config.service_name, str)
        assert isinstance(config.service_version, str)
        assert isinstance(config.logger_log_level, str)
        assert isinstance(config.identity_enable_token_cache, bool)
        # Note: keyvault/storage fields removed from EnvironmentConfiguration

    def test_setup_builder_custom_values(self):
        """Test setup builder with custom values."""
        from azpaddypy.builder import ConfigurationSetupBuilder

        config = (ConfigurationSetupBuilder()
                  .with_local_env_management()  # FIRST: Load .env files
                  .with_environment_detection()
                  .with_service_configuration(service_name="custom-service", service_version="2.0.0")
                  .with_logging_configuration(log_level="DEBUG", enable_console=False)
                  .with_identity_configuration(enable_token_cache=False)
                  .build())  # keyvault/storage configs removed - handled in service creation

        assert config.service_name == "custom-service"
        assert config.service_version == "2.0.0"
        assert config.logger_log_level == "DEBUG"
        assert config.logger_enable_console is False
        assert config.identity_enable_token_cache is False
        # Note: keyvault/storage custom values are now set in with_keyvault() and with_storage() methods

    def test_setup_builder_environment_override(self):
        """Test setup builder with environment variable overrides."""
        from azpaddypy.builder import ConfigurationSetupBuilder

        test_env = {
            'REFLECTION_NAME': 'env-service',
            'SERVICE_VERSION': '3.0.0',
            'LOGGER_LOG_LEVEL': 'WARNING',
            'IDENTITY_ENABLE_TOKEN_CACHE': 'false',
            'key_vault_uri': 'https://test-vault.vault.azure.net/',
            'STORAGE_ACCOUNT_URL': 'https://test-storage.blob.core.windows.net/'
        }

        with patch.dict(os.environ, test_env, clear=True):
            config = (ConfigurationSetupBuilder()
                      .with_local_env_management()  # FIRST: Load .env files
                      .with_environment_detection()
                      .with_service_configuration()
                      .with_logging_configuration()
                      .with_identity_configuration()
                      .build())  # keyvault/storage configs removed - handled in service creation
            assert isinstance(config.service_name, str)
            assert isinstance(config.service_version, str)
            assert isinstance(config.logger_log_level, str)
            assert isinstance(config.identity_enable_token_cache, bool)

            # Note: keyvault_url and storage_url now read directly by with_keyvault() and with_storage()

    def test_setup_director_patterns(self):
        """Test setup director patterns."""
        from azpaddypy.builder.directors import ConfigurationSetupDirector

        # Test default setup
        default_config = ConfigurationSetupDirector.build_default_config()

        assert isinstance(default_config.service_name, str)
        assert isinstance(default_config.logger_log_level, str)
        assert isinstance(default_config.identity_enable_token_cache, bool)
        assert default_config.local_env_manager is not None

    @patch('azpaddypy.builder.configuration.ConfigurationSetupBuilder._is_running_in_docker')
    def test_environment_detection(self, mock_docker_check):
        """Test environment detection for Docker vs local."""
        from azpaddypy.builder import ConfigurationSetupBuilder

        # Test Docker environment
        mock_docker_check.return_value = True
        
        # Set test Azure credentials in environment
        test_env = {
            'AZURE_CLIENT_ID': 'test-client-id',
            'AZURE_TENANT_ID': 'test-tenant-id',
            'AZURE_CLIENT_SECRET': 'test-client-secret'
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            config = (ConfigurationSetupBuilder()
                      .with_local_env_management()  # FIRST: Load .env files
                      .with_environment_detection()
                      .with_environment_variables({
                          'AZURE_CLIENT_ID': 'test-client-id',
                          'AZURE_TENANT_ID': 'test-tenant-id',
                          'AZURE_CLIENT_SECRET': 'test-client-secret'
                      }, in_docker=True, in_machine=True)  # Apply in both environments
                      .with_environment_variables({
                          'AzureWebJobsStorage': 'UseDevelopmentStorage=true'
                      }, in_docker=False, in_machine=True)  # Only on machine
                      .with_service_configuration()
                      .with_logging_configuration()
                      .with_identity_configuration()
                      .build())

            assert config.running_in_docker is True
            assert "AZURE_CLIENT_ID" in config.local_settings
            assert "AzureWebJobsStorage" not in config.local_settings  # Should not be applied in Docker

        # Test local environment
        mock_docker_check.return_value = False
        
        with patch.dict(os.environ, test_env, clear=False):
            config = (ConfigurationSetupBuilder()
                      .with_local_env_management()  # FIRST: Load .env files  
                      .with_environment_detection()
                      .with_environment_variables({
                          'AZURE_CLIENT_ID': 'test-client-id',
                          'AZURE_TENANT_ID': 'test-tenant-id',
                          'AZURE_CLIENT_SECRET': 'test-client-secret'
                      }, in_docker=True, in_machine=True)  # Apply in both environments
                      .with_environment_variables({
                          'AzureWebJobsStorage': 'UseDevelopmentStorage=true'
                      }, in_docker=False, in_machine=True)  # Only on machine
                      .with_service_configuration()
                      .with_logging_configuration()
                      .with_identity_configuration()
                      .build())

            assert config.running_in_docker is False
            assert "AZURE_CLIENT_ID" in config.local_settings
            assert "AzureWebJobsStorage" in config.local_settings  # Should be applied on machine

    def test_management_builder_with_custom_env_config(self):
        """Test management builder with custom environment configuration."""
        from azpaddypy.builder import ConfigurationSetupBuilder, AzureManagementBuilder

        # Create custom environment config
        env_config = (ConfigurationSetupBuilder()
                      .with_local_env_management()  # FIRST: Load .env files
                      .with_environment_detection()
                      .with_service_configuration(service_name="test-service")
                      .with_logging_configuration(log_level="DEBUG")
                      .with_identity_configuration()
                      .build())  # keyvault/storage configs removed - handled in service creation

        # Verify the custom environment config has expected values
        assert env_config.service_name == "test-service"
        assert env_config.logger_log_level == "DEBUG"

        # Test that the builder accepts the custom config without errors
        # and creates a valid configuration object
        builder = AzureManagementBuilder(env_config)
        assert builder._env_config.service_name == "test-service"
        assert builder._env_config.logger_log_level == "DEBUG"

    def test_resource_builder_with_custom_env_config(self):
        """Test resource builder with custom environment configuration."""
        from azpaddypy.builder import ConfigurationSetupBuilder, AzureResourceBuilder, AzureManagementConfiguration

        # Create custom environment config  
        env_config = (ConfigurationSetupBuilder()
                      .with_local_env_management()  # FIRST: Load .env files
                      .with_environment_detection()
                      .with_service_configuration(service_name="test-service")
                      .with_logging_configuration()
                      .with_identity_configuration()
                      .build())  # keyvault/storage configs removed - handled in service creation

        # Verify the custom environment config has expected values
        assert env_config.service_name == "test-service"
        # Note: storage_url is now specified directly in with_storage(account_url="...")

        # Create mock management config
        mgmt_config = Mock(spec=AzureManagementConfiguration)
        mgmt_config.validate.return_value = True
        mgmt_config.logger = Mock(spec=AzureLogger)
        mgmt_config.identity = Mock(spec=AzureIdentity)
        mgmt_config.keyvault = None

        # Test that the resource builder accepts the custom config without errors
        builder = AzureResourceBuilder(mgmt_config, env_config)
        assert builder._env_config.service_name == "test-service"
        # Note: storage_url is now specified directly in with_storage() method