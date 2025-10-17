from typing import Optional, Dict, Any, Union, List
from azure.keyvault.secrets import SecretClient
from azure.keyvault.keys import KeyClient
from azure.keyvault.certificates import CertificateClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from azure.core.credentials import TokenCredential
from ..mgmt.logging import AzureLogger
from ..mgmt.identity import AzureIdentity


# KeyVault instance caching
_keyvault_instances: Dict[Any, "AzureKeyVault"] = {}


class AzureKeyVault:
    """Azure Key Vault management with comprehensive secret, key, and certificate operations.

    Provides standardized Azure Key Vault operations using Azure SDK clients
    with integrated logging, error handling, and OpenTelemetry tracing support.
    Supports operations for secrets, keys, and certificates with proper
    authentication and authorization handling.

    Attributes:
        vault_url: Azure Key Vault URL
        service_name: Service identifier for logging and tracing
        service_version: Service version for context
        logger: AzureLogger instance for structured logging
        credential: Azure credential for authentication
        secret_client: Azure Key Vault SecretClient instance
        key_client: Azure Key Vault KeyClient instance
        certificate_client: Azure Key Vault CertificateClient instance
    """

    def __init__(
        self,
        vault_url: str,
        credential: Optional[TokenCredential] = None,
        azure_identity: Optional[AzureIdentity] = None,
        service_name: str = "azure_keyvault",
        service_version: str = "1.0.0",
        logger: Optional[AzureLogger] = None,
        connection_string: Optional[str] = None,
        enable_secrets: bool = True,
        enable_keys: bool = True,
        enable_certificates: bool = True,
    ):
        """Initialize Azure Key Vault with comprehensive configuration.

        Args:
            vault_url: Azure Key Vault URL (e.g., https://vault.vault.azure.net/)
            credential: Azure credential for authentication
            azure_identity: AzureIdentity instance for credential management
            service_name: Service name for tracing context
            service_version: Service version for metadata
            logger: Optional AzureLogger instance
            connection_string: Application Insights connection string
            enable_secrets: Enable secret operations client
            enable_keys: Enable key operations client
            enable_certificates: Enable certificate operations client

        Raises:
            ValueError: If neither credential nor azure_identity is provided
            Exception: If client initialization fails
        """
        self.vault_url = vault_url
        self.service_name = service_name
        self.service_version = service_version
        self.enable_secrets = enable_secrets
        self.enable_keys = enable_keys
        self.enable_certificates = enable_certificates

        # Initialize logger - use provided instance or create new one
        if logger is not None:
            self.logger = logger
        else:
            self.logger = AzureLogger(
                service_name=service_name,
                service_version=service_version,
                connection_string=connection_string,
                enable_console_logging=True,
            )

        # Setup credential
        if azure_identity is not None:
            self.credential = azure_identity.get_credential()
            self.azure_identity = azure_identity
        elif credential is not None:
            self.credential = credential
            self.azure_identity = None
        else:
            raise ValueError("Either 'credential' or 'azure_identity' must be provided")

        # Initialize clients
        self.secret_client = None
        self.key_client = None
        self.certificate_client = None
        
        self._setup_clients()

        self.logger.info(
            f"Azure Key Vault initialized for service '{service_name}' v{service_version}",
            extra={
                "vault_url": vault_url,
                "secrets_enabled": enable_secrets,
                "keys_enabled": enable_keys,
                "certificates_enabled": enable_certificates,
            }
        )

    def _setup_clients(self):
        """Initialize Key Vault clients based on enabled features.

        Raises:
            Exception: If client initialization fails
        """
        try:
            if self.enable_secrets:
                self.secret_client = SecretClient(
                    vault_url=self.vault_url,
                    credential=self.credential
                )
                self.logger.debug("SecretClient initialized successfully")

            if self.enable_keys:
                self.key_client = KeyClient(
                    vault_url=self.vault_url,
                    credential=self.credential
                )
                self.logger.debug("KeyClient initialized successfully")

            if self.enable_certificates:
                self.certificate_client = CertificateClient(
                    vault_url=self.vault_url,
                    credential=self.credential
                )
                self.logger.debug("CertificateClient initialized successfully")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize Key Vault clients: {e}",
                exc_info=True
            )
            raise

    # Secret Operations
    def get_secret(
        self,
        secret_name: str,
        version: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Retrieve a secret from Azure Key Vault.

        Args:
            secret_name: Name of the secret
            version: Optional specific version of the secret
            **kwargs: Additional parameters for the secret retrieval

        Returns:
            Secret value if found, None if not found

        Raises:
            RuntimeError: If secret client is not initialized
            Exception: If secret retrieval fails for reasons other than not found
        """
        with self.logger.create_span(
            "AzureKeyVault.get_secret",
            attributes={
                "service.name": self.service_name,
                "operation.type": "secret_retrieval",
                "keyvault.secret_name": secret_name,
                "keyvault.version": version or "latest",
                "keyvault.vault_url": self.vault_url
            }
        ):
            if self.secret_client is None:
                error_msg = "Secret client not initialized. Enable secrets during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Retrieving secret from Key Vault",
                    extra={
                        "secret_name": secret_name,
                        "version": version,
                        "vault_url": self.vault_url
                    }
                )

                secret = self.secret_client.get_secret(secret_name, version=version, **kwargs)
                
                self.logger.info(
                    "Secret retrieved successfully",
                    extra={
                        "secret_name": secret_name,
                        "version": secret.properties.version if secret.properties else None,
                        "content_type": secret.properties.content_type if secret.properties else None
                    }
                )
                
                return secret.value

            except ResourceNotFoundError:
                self.logger.warning(
                    f"Secret '{secret_name}' not found in Key Vault",
                    extra={"secret_name": secret_name, "version": version}
                )
                return None
            except ClientAuthenticationError as e:
                self.logger.error(
                    f"Authentication failed for secret '{secret_name}': {e}",
                    extra={"secret_name": secret_name},
                    exc_info=True
                )
                raise
            except Exception as e:
                self.logger.error(
                    f"Failed to retrieve secret '{secret_name}': {e}",
                    extra={"secret_name": secret_name, "version": version},
                    exc_info=True
                )
                raise

    def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        content_type: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> bool:
        """Set a secret in Azure Key Vault.

        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret
            content_type: Optional content type for the secret
            tags: Optional tags for the secret
            **kwargs: Additional parameters for secret creation

        Returns:
            True if secret was set successfully

        Raises:
            RuntimeError: If secret client is not initialized
            Exception: If secret creation fails
        """
        with self.logger.create_span(
            "AzureKeyVault.set_secret",
            attributes={
                "service.name": self.service_name,
                "operation.type": "secret_creation",
                "keyvault.secret_name": secret_name,
                "keyvault.content_type": content_type or "text/plain",
                "keyvault.vault_url": self.vault_url
            }
        ):
            if self.secret_client is None:
                error_msg = "Secret client not initialized. Enable secrets during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Setting secret in Key Vault",
                    extra={
                        "secret_name": secret_name,
                        "content_type": content_type,
                        "has_tags": tags is not None,
                        "vault_url": self.vault_url
                    }
                )

                secret = self.secret_client.set_secret(
                    secret_name,
                    secret_value,
                    content_type=content_type,
                    tags=tags,
                    **kwargs
                )
                
                self.logger.info(
                    "Secret set successfully",
                    extra={
                        "secret_name": secret_name,
                        "version": secret.properties.version if secret.properties else None,
                        "content_type": secret.properties.content_type if secret.properties else None
                    }
                )
                
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to set secret '{secret_name}': {e}",
                    extra={"secret_name": secret_name, "content_type": content_type},
                    exc_info=True
                )
                raise

    def delete_secret(self, secret_name: str, **kwargs) -> bool:
        """Delete a secret from Azure Key Vault.

        Args:
            secret_name: Name of the secret to delete
            **kwargs: Additional parameters for secret deletion

        Returns:
            True if secret was deleted successfully

        Raises:
            RuntimeError: If secret client is not initialized
            Exception: If secret deletion fails
        """
        with self.logger.create_span(
            "AzureKeyVault.delete_secret",
            attributes={
                "service.name": self.service_name,
                "operation.type": "secret_deletion",
                "keyvault.secret_name": secret_name,
                "keyvault.vault_url": self.vault_url
            }
        ):
            if self.secret_client is None:
                error_msg = "Secret client not initialized. Enable secrets during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Deleting secret from Key Vault",
                    extra={"secret_name": secret_name, "vault_url": self.vault_url}
                )

                self.secret_client.begin_delete_secret(secret_name, **kwargs)
                
                self.logger.info(
                    "Secret deletion initiated successfully",
                    extra={"secret_name": secret_name}
                )
                
                return True

            except ResourceNotFoundError:
                self.logger.warning(
                    f"Secret '{secret_name}' not found for deletion",
                    extra={"secret_name": secret_name}
                )
                return False
            except Exception as e:
                self.logger.error(
                    f"Failed to delete secret '{secret_name}': {e}",
                    extra={"secret_name": secret_name},
                    exc_info=True
                )
                raise

    def list_secrets(self, **kwargs) -> List[str]:
        """List all secrets in the Key Vault.

        Args:
            **kwargs: Additional parameters for listing secrets

        Returns:
            List of secret names

        Raises:
            RuntimeError: If secret client is not initialized
            Exception: If listing secrets fails
        """
        with self.logger.create_span(
            "AzureKeyVault.list_secrets",
            attributes={
                "service.name": self.service_name,
                "operation.type": "secret_listing",
                "keyvault.vault_url": self.vault_url
            }
        ):
            if self.secret_client is None:
                error_msg = "Secret client not initialized. Enable secrets during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Listing secrets from Key Vault",
                    extra={"vault_url": self.vault_url}
                )

                secret_names = []
                for secret_property in self.secret_client.list_properties_of_secrets(**kwargs):
                    secret_names.append(secret_property.name)
                
                self.logger.info(
                    "Secrets listed successfully",
                    extra={"secret_count": len(secret_names)}
                )
                
                return secret_names

            except Exception as e:
                self.logger.error(
                    f"Failed to list secrets: {e}",
                    exc_info=True
                )
                raise

    def test_connection(self) -> bool:
        """Test connection to Key Vault by attempting to list secrets.

        Returns:
            True if connection is successful, False otherwise
        """
        with self.logger.create_span(
            "AzureKeyVault.test_connection",
            attributes={
                "service.name": self.service_name,
                "operation.type": "connection_test",
                "keyvault.vault_url": self.vault_url
            }
        ):
            try:
                self.logger.debug(
                    "Testing Key Vault connection",
                    extra={"vault_url": self.vault_url}
                )

                if self.secret_client is not None:
                    # Try to list secrets (limited to 1) to test connection
                    list(self.secret_client.list_properties_of_secrets(max_page_size=1))
                elif self.key_client is not None:
                    # Try to list keys if secrets are disabled
                    list(self.key_client.list_properties_of_keys(max_page_size=1))
                elif self.certificate_client is not None:
                    # Try to list certificates if keys are disabled
                    list(self.certificate_client.list_properties_of_certificates(max_page_size=1))
                else:
                    self.logger.error("No clients available for connection testing")
                    return False

                self.logger.info("Key Vault connection test successful")
                return True

            except Exception as e:
                self.logger.warning(
                    f"Key Vault connection test failed: {e}",
                    extra={"vault_url": self.vault_url}
                )
                return False

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request/transaction tracking.

        Args:
            correlation_id: Unique identifier for transaction correlation
        """
        self.logger.set_correlation_id(correlation_id)

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID.

        Returns:
            Current correlation ID if set, otherwise None
        """
        return self.logger.get_correlation_id()


def create_azure_keyvault(
    vault_url: str,
    credential: Optional[TokenCredential] = None,
    azure_identity: Optional[AzureIdentity] = None,
    service_name: str = "azure_keyvault",
    service_version: str = "1.0.0",
    logger: Optional[AzureLogger] = None,
    connection_string: Optional[str] = None,
    enable_secrets: bool = True,
    enable_keys: bool = True,
    enable_certificates: bool = True,
) -> AzureKeyVault:
    """Factory function to create cached AzureKeyVault instance.

    Returns existing KeyVault instance if one with same configuration exists.
    Provides a convenient way to create an AzureKeyVault instance with
    common configuration patterns. If no credential or azure_identity
    is provided, creates a default AzureIdentity instance.

    Args:
        vault_url: Azure Key Vault URL
        credential: Azure credential for authentication
        azure_identity: AzureIdentity instance for credential management
        service_name: Service name for tracing context
        service_version: Service version for metadata
        logger: Optional AzureLogger instance
        connection_string: Application Insights connection string
        enable_secrets: Enable secret operations client
        enable_keys: Enable key operations client
        enable_certificates: Enable certificate operations client

    Returns:
        Configured AzureKeyVault instance (cached if available)

    Example:
        # Basic usage with default credential
        kv = create_azure_keyvault("https://vault.vault.azure.net/")
        
        # With custom service name and specific features
        kv = create_azure_keyvault(
            "https://vault.vault.azure.net/",
            service_name="my_app",
            enable_keys=False,
            enable_certificates=False
        )
    """
    # Handle default credential creation before caching
    if credential is None and azure_identity is None:
        # Create default AzureIdentity instance
        from ..mgmt.identity import create_azure_identity
        azure_identity = create_azure_identity(
            service_name=f"{service_name}_identity",
            service_version=service_version,
            connection_string=connection_string,
        )

    # Create cache key from configuration parameters
    # Use object identity for credential objects since they may not be hashable
    cache_key = (
        vault_url,
        id(credential) if credential else None,
        id(azure_identity) if azure_identity else None,
        service_name,
        service_version,
        id(logger) if logger else None,
        connection_string,
        enable_secrets,
        enable_keys,
        enable_certificates,
    )

    # Return cached instance if available
    if cache_key in _keyvault_instances:
        return _keyvault_instances[cache_key]

    # Create new instance and cache it
    keyvault_instance = AzureKeyVault(
        vault_url=vault_url,
        credential=credential,
        azure_identity=azure_identity,
        service_name=service_name,
        service_version=service_version,
        logger=logger,
        connection_string=connection_string,
        enable_secrets=enable_secrets,
        enable_keys=enable_keys,
        enable_certificates=enable_certificates,
    )
    
    _keyvault_instances[cache_key] = keyvault_instance
    return keyvault_instance
