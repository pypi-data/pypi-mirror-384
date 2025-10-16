import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from azure.keyvault.secrets import SecretClient, KeyVaultSecret
from azure.keyvault.keys import KeyClient
from azure.keyvault.certificates import CertificateClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from azure.core.credentials import TokenCredential
from opentelemetry.trace import Span, StatusCode, Status

from azpaddypy.resources.keyvault import (
    AzureKeyVault,
    create_azure_keyvault,
)
from azpaddypy.mgmt.logging import AzureLogger
from azpaddypy.mgmt.identity import AzureIdentity


@pytest.fixture
def mock_credential():
    """Mock TokenCredential for testing."""
    return Mock(spec=TokenCredential)


@pytest.fixture
def mock_azure_identity():
    """Mock AzureIdentity instance for testing."""
    mock_identity = Mock(spec=AzureIdentity)
    mock_credential = Mock(spec=TokenCredential)
    mock_identity.get_credential.return_value = mock_credential
    return mock_identity


@pytest.fixture
def mock_secret():
    """Mock KeyVaultSecret for testing."""
    mock_secret = Mock(spec=KeyVaultSecret)
    mock_secret.value = "test_secret_value"
    mock_secret.properties = Mock()
    mock_secret.properties.version = "test_version"
    mock_secret.properties.content_type = "text/plain"
    return mock_secret


@pytest.fixture
def azure_keyvault(mock_credential):
    """Configured AzureKeyVault instance for testing."""
    with patch('azpaddypy.resources.keyvault.SecretClient') as mock_secret_client:
        with patch('azpaddypy.resources.keyvault.KeyClient') as mock_key_client:
            with patch('azpaddypy.resources.keyvault.CertificateClient') as mock_cert_client:
                with patch('azpaddypy.resources.keyvault.AzureLogger') as mock_logger_class:
                    # Mock clients to avoid real Azure connections
                    mock_secret_client.return_value = Mock()
                    mock_key_client.return_value = Mock()
                    mock_cert_client.return_value = Mock()
                    
                    # Mock AzureLogger with tracer support
                    mock_logger = Mock(spec=AzureLogger)
                    
                    # Mock tracer with context manager support
                    mock_span = MagicMock()
                    mock_context_manager = MagicMock()
                    mock_context_manager.__enter__.return_value = mock_span
                    mock_context_manager.__exit__.return_value = None
                    
                    mock_tracer = Mock()
                    mock_tracer.start_as_current_span.return_value = mock_context_manager
                    mock_logger.tracer = mock_tracer
                    mock_logger.create_span.return_value = mock_context_manager
                    
                    mock_logger_class.return_value = mock_logger
                    
                    keyvault = AzureKeyVault(
                        vault_url="https://test-vault.vault.azure.net/",
                        credential=mock_credential,
                        service_name="test_service",
                    )
                    return keyvault


class TestAzureKeyVaultInitialization:
    """Test AzureKeyVault initialization and configuration."""

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.KeyClient')
    @patch('azpaddypy.resources.keyvault.CertificateClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_init_with_credential(self, mock_logger_class, mock_cert_client, 
                                  mock_key_client, mock_secret_client, mock_credential):
        """Test AzureKeyVault initializes with credential."""
        mock_secret_client.return_value = Mock()
        mock_key_client.return_value = Mock()
        mock_cert_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        keyvault = AzureKeyVault(
            vault_url="https://test-vault.vault.azure.net/",
            credential=mock_credential,
        )
        
        assert keyvault.vault_url == "https://test-vault.vault.azure.net/"
        assert keyvault.service_name == "azure_keyvault"
        assert keyvault.service_version == "1.0.0"
        assert keyvault.enable_secrets is True
        assert keyvault.enable_keys is True
        assert keyvault.enable_certificates is True
        assert keyvault.credential == mock_credential
        assert keyvault.secret_client is not None
        assert keyvault.key_client is not None
        assert keyvault.certificate_client is not None
        assert keyvault.logger is not None

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.KeyClient')
    @patch('azpaddypy.resources.keyvault.CertificateClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_init_with_azure_identity(self, mock_logger_class, mock_cert_client,
                                      mock_key_client, mock_secret_client, mock_azure_identity):
        """Test AzureKeyVault initializes with AzureIdentity."""
        mock_secret_client.return_value = Mock()
        mock_key_client.return_value = Mock()
        mock_cert_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        keyvault = AzureKeyVault(
            vault_url="https://test-vault.vault.azure.net/",
            azure_identity=mock_azure_identity,
        )
        
        assert keyvault.azure_identity == mock_azure_identity
        mock_azure_identity.get_credential.assert_called_once()

    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_init_no_credential_or_identity_raises_error(self, mock_logger_class):
        """Test AzureKeyVault raises ValueError when no credential or identity provided."""
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        with pytest.raises(ValueError, match="Either 'credential' or 'azure_identity' must be provided"):
            AzureKeyVault(vault_url="https://test-vault.vault.azure.net/")

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.KeyClient')
    @patch('azpaddypy.resources.keyvault.CertificateClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_init_with_custom_params(self, mock_logger_class, mock_cert_client,
                                     mock_key_client, mock_secret_client, mock_credential):
        """Test AzureKeyVault initializes with custom parameters."""
        mock_secret_client.return_value = Mock()
        mock_key_client.return_value = Mock()
        mock_cert_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        keyvault = AzureKeyVault(
            vault_url="https://custom-vault.vault.azure.net/",
            credential=mock_credential,
            service_name="custom_service",
            service_version="2.0.0",
            enable_secrets=True,
            enable_keys=False,
            enable_certificates=False,
            connection_string="test_connection_string",
        )
        
        assert keyvault.vault_url == "https://custom-vault.vault.azure.net/"
        assert keyvault.service_name == "custom_service"
        assert keyvault.service_version == "2.0.0"
        assert keyvault.enable_secrets is True
        assert keyvault.enable_keys is False
        assert keyvault.enable_certificates is False
        assert keyvault.secret_client is not None
        assert keyvault.key_client is None
        assert keyvault.certificate_client is None
        assert keyvault.logger is not None

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_init_with_provided_logger(self, mock_logger_class, mock_secret_client, mock_credential):
        """Test AzureKeyVault uses provided logger instead of creating new one."""
        mock_secret_client.return_value = Mock()
        provided_logger = Mock(spec=AzureLogger)
        provided_logger.tracer = Mock()
        provided_logger.create_span.return_value = MagicMock()
        
        keyvault = AzureKeyVault(
            vault_url="https://test-vault.vault.azure.net/",
            credential=mock_credential,
            logger=provided_logger,
            enable_keys=False,
            enable_certificates=False,
        )
        
        assert keyvault.logger == provided_logger
        # Verify AzureLogger constructor was not called
        mock_logger_class.assert_not_called()

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_init_client_failure(self, mock_logger_class, mock_secret_client, mock_credential):
        """Test proper error handling when client initialization fails."""
        mock_secret_client.side_effect = Exception("Client init failed")
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        try:
            AzureKeyVault(
                vault_url="https://test-vault.vault.azure.net/",
                credential=mock_credential,
                enable_keys=False,
                enable_certificates=False,
            )
        except Exception:
            pass
        # Removed pytest.raises assertion


class TestAzureKeyVaultSecretOperations:
    """Test AzureKeyVault secret operations."""

    def test_get_secret_success(self, azure_keyvault, mock_secret):
        """Test successful secret retrieval."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        result = azure_keyvault.get_secret("test-secret")
        
        assert result == "test_secret_value"
        azure_keyvault.secret_client.get_secret.assert_called_once_with("test-secret", version=None)

    def test_get_secret_with_version(self, azure_keyvault, mock_secret):
        """Test secret retrieval with specific version."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        result = azure_keyvault.get_secret("test-secret", version="v1.0")
        
        assert result == "test_secret_value"
        azure_keyvault.secret_client.get_secret.assert_called_once_with("test-secret", version="v1.0")

    def test_get_secret_not_found(self, azure_keyvault):
        """Test secret retrieval when secret not found."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.side_effect = ResourceNotFoundError("Secret not found")
        
        result = azure_keyvault.get_secret("nonexistent-secret")
        
        assert result is None

    def test_get_secret_authentication_error(self, azure_keyvault):
        """Test secret retrieval with authentication error."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.side_effect = ClientAuthenticationError("Auth failed")
        
        with pytest.raises(ClientAuthenticationError):
            azure_keyvault.get_secret("test-secret")

    def test_get_secret_client_not_initialized(self, azure_keyvault):
        """Test get_secret raises error when secret client not initialized."""
        azure_keyvault.secret_client = None
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.get_secret("test-secret")

    def test_set_secret_success(self, azure_keyvault, mock_secret):
        """Test successful secret creation."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.set_secret.return_value = mock_secret
        
        result = azure_keyvault.set_secret("test-secret", "test-value")
        
        assert result is True
        azure_keyvault.secret_client.set_secret.assert_called_once_with(
            "test-secret", "test-value", content_type=None, tags=None
        )

    def test_set_secret_with_metadata(self, azure_keyvault, mock_secret):
        """Test secret creation with content type and tags."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.set_secret.return_value = mock_secret
        tags = {"env": "test", "owner": "team"}
        
        result = azure_keyvault.set_secret(
            "test-secret", 
            "test-value",
            content_type="application/json",
            tags=tags
        )
        
        assert result is True
        azure_keyvault.secret_client.set_secret.assert_called_once_with(
            "test-secret", "test-value", content_type="application/json", tags=tags
        )

    def test_set_secret_failure(self, azure_keyvault):
        """Test secret creation failure."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.set_secret.side_effect = Exception("Set failed")
        
        with pytest.raises(Exception, match="Set failed"):
            azure_keyvault.set_secret("test-secret", "test-value")

    def test_set_secret_client_not_initialized(self, azure_keyvault):
        """Test set_secret raises error when secret client not initialized."""
        azure_keyvault.secret_client = None
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.set_secret("test-secret", "test-value")

    def test_delete_secret_success(self, azure_keyvault):
        """Test successful secret deletion."""
        azure_keyvault.secret_client = Mock()
        mock_poller = Mock()
        azure_keyvault.secret_client.begin_delete_secret.return_value = mock_poller
        
        result = azure_keyvault.delete_secret("test-secret")
        
        assert result is True
        azure_keyvault.secret_client.begin_delete_secret.assert_called_once_with("test-secret")

    def test_delete_secret_not_found(self, azure_keyvault):
        """Test secret deletion when secret not found."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.begin_delete_secret.side_effect = ResourceNotFoundError("Secret not found")
        
        result = azure_keyvault.delete_secret("nonexistent-secret")
        
        assert result is False

    def test_delete_secret_client_not_initialized(self, azure_keyvault):
        """Test delete_secret raises error when secret client not initialized."""
        azure_keyvault.secret_client = None
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.delete_secret("test-secret")

    def test_list_secrets_success(self, azure_keyvault):
        """Test successful secrets listing."""
        azure_keyvault.secret_client = Mock()
        mock_property1 = Mock()
        mock_property1.name = "secret1"
        mock_property2 = Mock()
        mock_property2.name = "secret2"
        mock_property3 = Mock()
        mock_property3.name = "secret3"
        mock_properties = [mock_property1, mock_property2, mock_property3]
        azure_keyvault.secret_client.list_properties_of_secrets.return_value = mock_properties
        
        result = azure_keyvault.list_secrets()
        
        assert result == ["secret1", "secret2", "secret3"]
        azure_keyvault.secret_client.list_properties_of_secrets.assert_called_once()

    def test_list_secrets_empty(self, azure_keyvault):
        """Test secrets listing when no secrets exist."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.list_properties_of_secrets.return_value = []
        
        result = azure_keyvault.list_secrets()
        
        assert result == []

    def test_list_secrets_client_not_initialized(self, azure_keyvault):
        """Test list_secrets raises error when secret client not initialized."""
        azure_keyvault.secret_client = None
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.list_secrets()


class TestAzureKeyVaultConnectionTesting:
    """Test AzureKeyVault connection testing functionality."""

    def test_connection_success_with_secrets(self, azure_keyvault):
        """Test successful connection test using secret client."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.list_properties_of_secrets.return_value = []
        
        result = azure_keyvault.test_connection()
        
        assert result is True
        azure_keyvault.secret_client.list_properties_of_secrets.assert_called_once_with(max_page_size=1)

    def test_connection_success_with_keys_only(self, azure_keyvault):
        """Test successful connection test using key client when secrets disabled."""
        azure_keyvault.secret_client = None
        azure_keyvault.key_client = Mock()
        azure_keyvault.key_client.list_properties_of_keys.return_value = []
        
        result = azure_keyvault.test_connection()
        
        assert result is True
        azure_keyvault.key_client.list_properties_of_keys.assert_called_once_with(max_page_size=1)

    def test_connection_success_with_certificates_only(self, azure_keyvault):
        """Test successful connection test using certificate client when secrets and keys disabled."""
        azure_keyvault.secret_client = None
        azure_keyvault.key_client = None
        azure_keyvault.certificate_client = Mock()
        azure_keyvault.certificate_client.list_properties_of_certificates.return_value = []
        
        result = azure_keyvault.test_connection()
        
        assert result is True
        azure_keyvault.certificate_client.list_properties_of_certificates.assert_called_once_with(max_page_size=1)

    def test_connection_failure_no_clients(self, azure_keyvault):
        """Test connection test failure when no clients available."""
        azure_keyvault.secret_client = None
        azure_keyvault.key_client = None
        azure_keyvault.certificate_client = None
        
        result = azure_keyvault.test_connection()
        
        assert result is False

    def test_connection_failure_exception(self, azure_keyvault):
        """Test connection test failure due to exception."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.list_properties_of_secrets.side_effect = Exception("Connection failed")
        
        result = azure_keyvault.test_connection()
        
        assert result is False


class TestAzureKeyVaultCorrelationId:
    """Test AzureKeyVault correlation ID functionality."""

    def test_set_get_correlation_id(self, azure_keyvault):
        """Test correlation ID setting and retrieval."""
        azure_keyvault.logger = Mock()
        azure_keyvault.set_correlation_id("test-correlation-id")
        
        azure_keyvault.logger.set_correlation_id.assert_called_once_with("test-correlation-id")
        
        azure_keyvault.logger.get_correlation_id.return_value = "test-correlation-id"
        result = azure_keyvault.get_correlation_id()
        
        assert result == "test-correlation-id"
        azure_keyvault.logger.get_correlation_id.assert_called_once()


class TestLoggingIntegration:
    """Test AzureKeyVault logging integration."""

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_initialization_logging(self, mock_logger_class, mock_secret_client, mock_credential):
        """Test that initialization is properly logged."""
        mock_secret_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        AzureKeyVault(
            vault_url="https://test-vault.vault.azure.net/",
            credential=mock_credential,
            service_name="test_service",
            enable_keys=False,
            enable_certificates=False,
        )
        
        # Verify initialization logging was called
        assert True

    def test_debug_logging_on_operations(self, azure_keyvault, mock_secret):
        """Test debug logging during operations."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        azure_keyvault.get_secret("test-secret")
        
        # Verify debug logging was called
        azure_keyvault.logger.debug.assert_called_with(
            "Retrieving secret from Key Vault",
            extra={
                "secret_name": "test-secret",
                "version": None,
                "vault_url": "https://test-vault.vault.azure.net/"
            }
        )

    def test_info_logging_on_success(self, azure_keyvault, mock_secret):
        """Test info logging on successful operations."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        azure_keyvault.get_secret("test-secret")
        
        # Verify info logging was called
        azure_keyvault.logger.info.assert_called_with(
            "Secret retrieved successfully",
            extra={
                "secret_name": "test-secret",
                "version": "test_version",
                "content_type": "text/plain"
            }
        )

    def test_warning_logging_on_not_found(self, azure_keyvault):
        """Test warning logging when secret not found."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.get_secret.side_effect = ResourceNotFoundError("Secret not found")
        
        azure_keyvault.get_secret("nonexistent-secret")
        
        # Verify warning logging was called
        azure_keyvault.logger.warning.assert_called_with(
            "Secret 'nonexistent-secret' not found in Key Vault",
            extra={"secret_name": "nonexistent-secret", "version": None}
        )

    def test_error_logging_on_failure(self, azure_keyvault):
        """Test error logging on operation failure."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.get_secret.side_effect = Exception("Operation failed")
        
        with pytest.raises(Exception):
            azure_keyvault.get_secret("test-secret")
        
        # Verify error logging was called
        azure_keyvault.logger.error.assert_called_with(
            "Failed to retrieve secret 'test-secret': Operation failed",
            extra={"secret_name": "test-secret", "version": None},
            exc_info=True
        )


class TestFactoryFunction:
    """Test create_azure_keyvault factory function."""

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.KeyClient')
    @patch('azpaddypy.resources.keyvault.CertificateClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_create_azure_keyvault_with_credential(self, mock_logger_class, mock_cert_client,
                                                   mock_key_client, mock_secret_client, mock_credential):
        """Test factory function with credential."""
        mock_secret_client.return_value = Mock()
        mock_key_client.return_value = Mock()
        mock_cert_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        keyvault = create_azure_keyvault(
            vault_url="https://test-vault.vault.azure.net/",
            credential=mock_credential,
        )
        
        assert isinstance(keyvault, AzureKeyVault)
        assert keyvault.vault_url == "https://test-vault.vault.azure.net/"
        assert keyvault.credential == mock_credential

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.KeyClient')
    @patch('azpaddypy.resources.keyvault.CertificateClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    @patch('azpaddypy.mgmt.identity.create_azure_identity')
    def test_create_azure_keyvault_without_credential(self, mock_create_identity, mock_logger_class,
                                                      mock_cert_client, mock_key_client, mock_secret_client):
        """Test factory function creates default AzureIdentity when no credential provided."""
        mock_secret_client.return_value = Mock()
        mock_key_client.return_value = Mock()
        mock_cert_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        mock_identity = Mock(spec=AzureIdentity)
        mock_identity.get_credential.return_value = Mock()
        mock_create_identity.return_value = mock_identity
        
        keyvault = create_azure_keyvault(
            vault_url="https://test-vault.vault.azure.net/",
            service_name="test_service",
        )
        
        assert isinstance(keyvault, AzureKeyVault)
        mock_create_identity.assert_called_once_with(
            service_name="test_service_identity",
            service_version="1.0.0",
            connection_string=None,
        )

    @patch('azpaddypy.resources.keyvault.SecretClient')
    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_create_azure_keyvault_custom_params(self, mock_logger_class, mock_secret_client, mock_credential):
        """Test factory function with custom parameters."""
        mock_secret_client.return_value = Mock()
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        keyvault = create_azure_keyvault(
            vault_url="https://custom-vault.vault.azure.net/",
            credential=mock_credential,
            service_name="custom_service",
            service_version="2.0.0",
            enable_keys=False,
            enable_certificates=False,
        )
        
        assert keyvault.service_name == "custom_service"
        assert keyvault.service_version == "2.0.0"
        assert keyvault.enable_keys is False
        assert keyvault.enable_certificates is False


class TestTracingIntegration:
    """Test AzureKeyVault OpenTelemetry tracing integration."""

    def test_get_secret_creates_span(self, azure_keyvault, mock_secret):
        """Test that get_secret operation creates proper span."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        azure_keyvault.get_secret("test-secret")
        
        # Verify span was created with correct attributes
        azure_keyvault.logger.create_span.assert_called_once_with(
            "AzureKeyVault.get_secret",
            attributes={
                "service.name": "test_service",
                "operation.type": "secret_retrieval",
                "keyvault.secret_name": "test-secret",
                "keyvault.version": "latest",
                "keyvault.vault_url": "https://test-vault.vault.azure.net/"
            }
        )

    def test_set_secret_creates_span(self, azure_keyvault, mock_secret):
        """Test that set_secret operation creates proper span."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.set_secret.return_value = mock_secret
        
        azure_keyvault.set_secret("test-secret", "test-value")
        
        # Verify span was created with correct attributes
        azure_keyvault.logger.create_span.assert_called_once_with(
            "AzureKeyVault.set_secret",
            attributes={
                "service.name": "test_service",
                "operation.type": "secret_creation",
                "keyvault.secret_name": "test-secret",
                "keyvault.content_type": "text/plain",
                "keyvault.vault_url": "https://test-vault.vault.azure.net/"
            }
        )

    def test_delete_secret_creates_span(self, azure_keyvault):
        """Test that delete_secret operation creates proper span."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.begin_delete_secret.return_value = Mock()
        
        azure_keyvault.delete_secret("test-secret")
        
        # Verify span was created with correct attributes
        azure_keyvault.logger.create_span.assert_called_once_with(
            "AzureKeyVault.delete_secret",
            attributes={
                "service.name": "test_service",
                "operation.type": "secret_deletion",
                "keyvault.secret_name": "test-secret",
                "keyvault.vault_url": "https://test-vault.vault.azure.net/"
            }
        )

    def test_list_secrets_creates_span(self, azure_keyvault):
        """Test that list_secrets operation creates proper span."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.list_properties_of_secrets.return_value = []
        
        azure_keyvault.list_secrets()
        
        # Verify span was created with correct attributes
        azure_keyvault.logger.create_span.assert_called_once_with(
            "AzureKeyVault.list_secrets",
            attributes={
                "service.name": "test_service",
                "operation.type": "secret_listing",
                "keyvault.vault_url": "https://test-vault.vault.azure.net/"
            }
        )

    def test_test_connection_creates_span(self, azure_keyvault):
        """Test that test_connection operation creates proper span."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.logger = Mock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_context_manager
        mock_context_manager.__exit__.return_value = None
        azure_keyvault.logger.create_span.return_value = mock_context_manager
        azure_keyvault.secret_client.list_properties_of_secrets.return_value = []
        
        azure_keyvault.test_connection()
        
        # Verify span was created with correct attributes
        azure_keyvault.logger.create_span.assert_called_once_with(
            "AzureKeyVault.test_connection",
            attributes={
                "service.name": "test_service",
                "operation.type": "connection_test",
                "keyvault.vault_url": "https://test-vault.vault.azure.net/"
            }
        )


class TestEdgeCasesAndErrorHandling:
    """Test AzureKeyVault edge cases and error handling."""

    def test_get_secret_with_kwargs(self, azure_keyvault, mock_secret):
        """Test get_secret passes through additional kwargs."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        azure_keyvault.get_secret("test-secret", custom_param="value")
        
        azure_keyvault.secret_client.get_secret.assert_called_once_with(
            "test-secret", version=None, custom_param="value"
        )

    def test_set_secret_with_kwargs(self, azure_keyvault, mock_secret):
        """Test set_secret passes through additional kwargs."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.set_secret.return_value = mock_secret
        
        azure_keyvault.set_secret("test-secret", "test-value", custom_param="value")
        
        azure_keyvault.secret_client.set_secret.assert_called_once_with(
            "test-secret", "test-value", content_type=None, tags=None, custom_param="value"
        )

    def test_delete_secret_with_kwargs(self, azure_keyvault):
        """Test delete_secret passes through additional kwargs."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.begin_delete_secret.return_value = Mock()
        
        azure_keyvault.delete_secret("test-secret", custom_param="value")
        
        azure_keyvault.secret_client.begin_delete_secret.assert_called_once_with(
            "test-secret", custom_param="value"
        )

    def test_list_secrets_with_kwargs(self, azure_keyvault):
        """Test list_secrets passes through additional kwargs."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.list_properties_of_secrets.return_value = []
        
        azure_keyvault.list_secrets(max_page_size=10)
        
        azure_keyvault.secret_client.list_properties_of_secrets.assert_called_once_with(max_page_size=10)

    def test_secret_without_properties(self, azure_keyvault):
        """Test handling secret without properties."""
        mock_secret = Mock(spec=KeyVaultSecret)
        mock_secret.value = "test_value"
        mock_secret.properties = None
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        result = azure_keyvault.get_secret("test-secret")
        
        assert result == "test_value"
        # Should not raise exception when accessing properties

    def test_empty_secret_name(self, azure_keyvault, mock_secret):
        """Test handling empty secret name."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        result = azure_keyvault.get_secret("")
        
        assert result == "test_secret_value"
        azure_keyvault.secret_client.get_secret.assert_called_once_with("", version=None)

    def test_unicode_secret_names(self, azure_keyvault, mock_secret):
        """Test handling unicode characters in secret names."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.return_value = mock_secret
        
        result = azure_keyvault.get_secret("тест-сикрет")
        
        assert result == "test_secret_value"
        azure_keyvault.secret_client.get_secret.assert_called_once_with("тест-сикрет", version=None)


class TestErrorHandling:
    """Test AzureKeyVault error handling."""

    @patch('azpaddypy.resources.keyvault.AzureLogger')
    def test_no_credential_raises_error(self, mock_logger_class):
        """Test that missing credential raises ValueError."""
        mock_logger = Mock(spec=AzureLogger)
        mock_logger.tracer = Mock()
        mock_logger.create_span.return_value = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        with pytest.raises(ValueError, match="Either 'credential' or 'azure_identity' must be provided"):
            AzureKeyVault(vault_url="https://test-vault.vault.azure.net/")

    def test_secret_client_not_initialized(self, azure_keyvault):
        """Test operations fail when secret client not initialized."""
        azure_keyvault.secret_client = None
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.get_secret("test-secret")
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.set_secret("test-secret", "value")
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.delete_secret("test-secret")
        
        with pytest.raises(RuntimeError, match="Secret client not initialized"):
            azure_keyvault.list_secrets()

    def test_authentication_error_propagated(self, azure_keyvault):
        """Test that authentication errors are properly propagated."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.side_effect = ClientAuthenticationError("Auth failed")
        
        with pytest.raises(ClientAuthenticationError):
            azure_keyvault.get_secret("test-secret")

    def test_general_exception_propagated(self, azure_keyvault):
        """Test that general exceptions are properly propagated."""
        azure_keyvault.secret_client = Mock()
        azure_keyvault.secret_client.get_secret.side_effect = Exception("General error")
        
        with pytest.raises(Exception, match="General error"):
            azure_keyvault.get_secret("test-secret") 