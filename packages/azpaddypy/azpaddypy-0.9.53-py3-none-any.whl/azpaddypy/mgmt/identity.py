from typing import Optional, Dict, Any, Union
from azure.identity import (
    TokenCachePersistenceOptions,
    get_bearer_token_provider,
    DefaultAzureCredential
)
from azure.core.credentials import AccessToken, TokenCredential
from .logging import AzureLogger


class AzureIdentity:
    """Azure identity management with token caching and distributed tracing.

    Provides standardized Azure authentication using DefaultAzureCredential
    with integrated logging, caching, and OpenTelemetry tracing support.
    Prioritizes Managed Identity, then Environment variables per Azure SDK
    best practices.

    Attributes:
        service_name: Service identifier for logging and tracing
        service_version: Service version for context
        enable_token_cache: Whether token caching is enabled
        allow_unencrypted_storage: Whether to allow unencrypted token storage
        logger: AzureLogger instance for structured logging
    """

    def __init__(
        self,
        service_name: str = "azure_identity",
        service_version: str = "1.0.0",
        enable_token_cache: bool = True,
        allow_unencrypted_storage: bool = True,
        custom_credential_options: Optional[Dict[str, Any]] = None,
        logger: Optional[AzureLogger] = None,
        connection_string: Optional[str] = None,
    ):
        """Initialize Azure Identity with comprehensive configuration.

        Args:
            service_name: Service name for tracing context
            service_version: Service version for metadata
            enable_token_cache: Enable in-memory token persistence
            allow_unencrypted_storage: Allow unencrypted token storage
            custom_credential_options: Additional DefaultAzureCredential options
            logger: Optional AzureLogger instance
            connection_string: Application Insights connection string
        """
        self.service_name = service_name
        self.service_version = service_version
        self.enable_token_cache = enable_token_cache
        self.allow_unencrypted_storage = allow_unencrypted_storage

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

        self._credential = None
        self._setup_credential(custom_credential_options)

        self.logger.info(
            f"Azure Identity initialized for service '{service_name}' v{service_version}"
        )

    def _setup_credential(self, custom_options: Optional[Dict[str, Any]] = None):
        """Configure DefaultAzureCredential with appropriate settings.

        Args:
            custom_options: Additional options for DefaultAzureCredential

        Raises:
            Exception: If credential initialization fails
        """
        try:
            credential_options = {}

            # Add token cache configuration if enabled
            if self.enable_token_cache:
                token_cache_options = TokenCachePersistenceOptions(
                    allow_unencrypted_storage=self.allow_unencrypted_storage
                )
                credential_options["token_cache_persistence_options"] = token_cache_options

            # Merge custom options
            if custom_options:
                credential_options.update(custom_options)

            self._credential = DefaultAzureCredential(**credential_options)
            
            self.logger.debug(
                "DefaultAzureCredential configured successfully",
                extra={
                    "token_cache_enabled": self.enable_token_cache,
                    "unencrypted_storage": self.allow_unencrypted_storage,
                }
            )

        except Exception as e:
            self.logger.error(
                f"Failed to initialize DefaultAzureCredential: {e}",
                exc_info=True
            )
            raise

    def get_credential(self) -> TokenCredential:
        """Get the configured DefaultAzureCredential instance.

        Returns:
            Configured TokenCredential instance

        Raises:
            RuntimeError: If credential is not initialized
        """
        with self.logger.create_span(
            "AzureIdentity.get_credential",
            attributes={
                "service.name": self.service_name,
                "operation.type": "credential_retrieval"
            }
        ):
            if self._credential is None:
                error_msg = "Credential not initialized"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            self.logger.debug("Retrieving DefaultAzureCredential instance")
            return self._credential

    def get_token(
        self, 
        scopes: Union[str, list],
        **kwargs
    ) -> AccessToken:
        """Acquire an access token for specified scopes.

        Args:
            scopes: Target scope(s) for token request
            **kwargs: Additional token request parameters

        Returns:
            AccessToken with token and expiration information

        Raises:
            RuntimeError: If credential is not initialized
            Exception: If token acquisition fails
        """
        # Normalize to list format
        if isinstance(scopes, str):
            scopes = [scopes]

        with self.logger.create_span(
            "AzureIdentity.get_token",
            attributes={
                "service.name": self.service_name,
                "operation.type": "token_acquisition",
                "token.scopes": ", ".join(scopes),
                "token.scope_count": len(scopes)
            }
        ):
            if self._credential is None:
                raise RuntimeError("Credential not initialized")

            self.logger.debug(
                "Acquiring access token",
                extra={
                    "scopes": scopes,
                    "scope_count": len(scopes)
                }
            )

            token = self._credential.get_token(*scopes, **kwargs)
            
            self.logger.info(
                "Access token acquired successfully",
                extra={
                    "scopes": scopes,
                    "expires_on": token.expires_on if hasattr(token, 'expires_on') else None
                }
            )
            
            return token

    def get_token_provider(
        self, 
        scopes: Union[str, list],
        **kwargs
    ) -> callable:
        """Create a bearer token provider for specified scopes.

        Useful for Azure SDK clients that accept token providers.

        Args:
            scopes: Target scope(s) for the token provider
            **kwargs: Additional token provider parameters

        Returns:
            Callable that returns bearer tokens

        Raises:
            RuntimeError: If credential is not initialized
            Exception: If token provider creation fails
        """
        # Normalize to list format
        if isinstance(scopes, str):
            scopes = [scopes]

        with self.logger.create_span(
            "AzureIdentity.get_token_provider",
            attributes={
                "service.name": self.service_name,
                "operation.type": "token_provider_creation",
                "token.scopes": ", ".join(scopes),
                "token.scope_count": len(scopes)
            }
        ):
            if self._credential is None:
                raise RuntimeError("Credential not initialized")

            self.logger.debug(
                "Creating bearer token provider",
                extra={
                    "scopes": scopes,
                    "scope_count": len(scopes)
                }
            )

            provider = get_bearer_token_provider(self._credential, *scopes, **kwargs)
            
            self.logger.info(
                "Bearer token provider created successfully",
                extra={
                    "scopes": scopes
                }
            )
            
            return provider

    def test_credential(self, test_scopes: Optional[Union[str, list]] = None) -> bool:
        """Test credential by attempting token acquisition.

        Args:
            test_scopes: Scopes to test with (defaults to Azure Management API)

        Returns:
            True if credential works, False otherwise
        """
        if test_scopes is None:
            test_scopes = ["https://management.azure.com/.default"]
        elif isinstance(test_scopes, str):
            test_scopes = [test_scopes]

        with self.logger.create_span(
            "AzureIdentity.test_credential",
            attributes={
                "service.name": self.service_name,
                "operation.type": "credential_test",
                "test.scopes": ", ".join(test_scopes)
            }
        ):
            try:
                self.logger.info("Testing credential authentication")
                token = self.get_token(test_scopes)
                
                if token and hasattr(token, 'token') and token.token:
                    self.logger.info("Credential test successful")
                    return True
                else:
                    self.logger.warning("Credential test returned empty token")
                    return False

            except Exception as e:
                self.logger.warning(
                    f"Credential test failed: {e}",
                    extra={"test_scopes": test_scopes}
                )
                return False

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for tracking identity operations.
        
        Args:
            correlation_id: Unique identifier for transaction tracking
        """
        self.logger.set_correlation_id(correlation_id)

    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID.
        
        Returns:
            Current correlation ID if set, otherwise None
        """
        return self.logger.get_correlation_id()


def create_azure_identity(
    service_name: str = "azure_identity",
    service_version: str = "1.0.0",
    enable_token_cache: bool = True,
    allow_unencrypted_storage: bool = True,
    custom_credential_options: Optional[Dict[str, Any]] = None,
    logger: Optional[AzureLogger] = None,
    connection_string: Optional[str] = None,
) -> AzureIdentity:
    """Create a configured AzureIdentity instance.

    Factory function providing convenient AzureIdentity instantiation with
    commonly used settings.

    Args:
        service_name: Service name for tracing context
        service_version: Service version for metadata
        enable_token_cache: Enable in-memory token persistence
        allow_unencrypted_storage: Allow unencrypted token storage
        custom_credential_options: Additional DefaultAzureCredential options
        logger: Optional AzureLogger instance
        connection_string: Application Insights connection string

    Returns:
        Configured AzureIdentity instance
    """
    return AzureIdentity(
        service_name=service_name,
        service_version=service_version,
        enable_token_cache=enable_token_cache,
        allow_unencrypted_storage=allow_unencrypted_storage,
        custom_credential_options=custom_credential_options,
        logger=logger,
        connection_string=connection_string,
    )
