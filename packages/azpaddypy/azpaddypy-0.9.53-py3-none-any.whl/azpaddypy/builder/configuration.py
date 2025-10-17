"""Azure configuration management with builder patterns.

Provides standardized Azure service configuration through environment variables
and builder patterns. Supports both direct service imports and flexible builders.

Usage Examples:
    # Builder pattern (recommended)
    from azpaddypy.builder import AzureManagementBuilder, AzureResourceBuilder
    from azpaddypy.builder.directors import ConfigurationSetupDirector
    
    env_config = ConfigurationSetupDirector.build_default_setup()
    mgmt = AzureManagementBuilder(env_config).with_logger().with_identity().with_keyvault().build()
    resources = AzureResourceBuilder(mgmt, env_config).with_storage().build()
    
    # Custom configuration (local env management is FIRST step)
    env_config = (ConfigurationSetupBuilder()
                  .with_local_env_management()  # FIRST: Load .env files
                  .with_environment_detection()
                  .with_environment_variables({"CUSTOM_VAR": "value"}, in_docker=True)
                  .with_service_configuration()
                  .with_logging_configuration()  # Complex configuration kept
                  .with_identity_configuration()  # Complex configuration kept
                  .build())  # keyvault/storage configs removed for simplicity

Environment Variables:
    # Core service configuration
    REFLECTION_NAME: Service name
    REFLECTION_KIND: Service type (app, functionapp)
    
    # Logging configuration
    LOGGER_LOG_LEVEL: Log level (default: INFO)
    APPLICATIONINSIGHTS_CONNECTION_STRING: App Insights connection
    
    # Identity configuration
    IDENTITY_ENABLE_TOKEN_CACHE: Enable token cache (default: true)
    IDENTITY_ALLOW_UNENCRYPTED_STORAGE: Allow unencrypted cache (default: true)
    
    # KeyVault configuration (read directly by with_keyvault)
    key_vault_uri: Primary Key Vault URL
    KEYVAULT_ENABLE_SECRETS: Enable secrets access (default: true)
    KEYVAULT_ENABLE_KEYS: Enable keys access (default: false)
    KEYVAULT_ENABLE_CERTIFICATES: Enable certificates access (default: false)
    
    # Storage configuration (read directly by with_storage)
    STORAGE_ACCOUNT_URL: Storage Account URL
    STORAGE_ENABLE_BLOB: Enable blob storage (default: true)
    STORAGE_ENABLE_FILE: Enable file storage (default: true)
    STORAGE_ENABLE_QUEUE: Enable queue storage (default: true)

Configuration Flow:
    1. with_local_env_management() - Load .env files and environment variables (FIRST)
    2. with_environment_detection() - Detect Docker vs local environment
    3. with_environment_variables() - Set conditional environment variables
    4. with_service_configuration() - Parse service settings
    5. with_logging_configuration() - Complex logging configuration
    6. with_identity_configuration() - Complex identity configuration
    Note: KeyVault and Storage read environment variables directly in service methods
"""

from __future__ import annotations
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import IntEnum

from ..mgmt.identity import create_azure_identity
from ..mgmt.local_env_manager import create_local_env_manager
from ..mgmt.logging import create_app_logger, create_function_logger
from ..resources.keyvault import create_azure_keyvault
from ..resources.storage import create_azure_storage
from ..resources.cosmosdb import create_azure_cosmosdb


@dataclass
class EnvironmentConfiguration:
    """Complete environment configuration."""
    # Environment detection
    running_in_docker: bool
    local_settings: Dict[str, str]
    
    # Local environment management
    local_env_manager: Any
    
    # Service configuration
    service_name: str
    service_version: str
    reflection_kind: str
    
    # Logging configuration
    logger_enable_console: bool
    logger_connection_string: Optional[str]
    logger_instrumentation_options: Dict[str, Dict[str, bool]]
    logger_log_level: str
    
    # Identity configuration
    identity_enable_token_cache: bool
    identity_allow_unencrypted_storage: bool
    identity_custom_credential_options: Optional[Dict[str, Any]]
    identity_connection_string: Optional[str]
    
    # Note: KeyVault and Storage configurations are now handled directly 
    # in their respective service creation methods for API simplicity


class ConfigurationSetupBuilder:
    """Builder for environment configuration setup."""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> 'ConfigurationSetupBuilder':
        """Reset builder to initial state."""
        self._config = None
        self._local_settings = {}
        self._local_env_manager = None
        return self
    
    def with_local_env_management(self, file_path: str = ".env", 
                                 settings: Optional[Dict[str, str]] = None,
                                 override_json: bool = True,
                                 override_dotenv: bool = True, 
                                 override_settings: bool = True) -> 'ConfigurationSetupBuilder':
        """Initialize local environment management (FIRST STEP).
        
        Loads environment variables from .env files and other sources.
        This should be called first as all subsequent steps depend on environment variables.
        
        Args:
            file_path: Path to .env file (default: ".env")
            settings: Additional settings to apply
            override_json: Whether to override with JSON settings
            override_dotenv: Whether to override with .env file settings
            override_settings: Whether to override with provided settings
        """
        from ..mgmt.local_env_manager import create_local_env_manager
        
        actual_settings = settings or {}
        
        self._local_env_manager = create_local_env_manager(
            file_path=file_path,
            settings=actual_settings,
            override_json=override_json,
            override_dotenv=override_dotenv,
            override_settings=override_settings,
        )
        
        # Update local settings for tracking
        self._local_settings.update(actual_settings)
        
        return self
    
    def with_environment_detection(self) -> 'ConfigurationSetupBuilder':
        """Detect environment (Docker vs local)."""
        running_in_docker = self._is_running_in_docker()
        os.environ["running_in_docker"] = str(running_in_docker)
        
        self._running_in_docker = running_in_docker
 
        print(f"is_running_in_docker: {running_in_docker}")
        return self
    
    def with_service_configuration(self, service_name: Optional[str] = None, 
                                  service_version: Optional[str] = None,
                                  reflection_kind: Optional[str] = None) -> 'ConfigurationSetupBuilder':
        """Parse service configuration."""
        reflection_name = service_name or os.getenv("REFLECTION_NAME")
        actual_reflection_kind = reflection_kind or os.getenv("REFLECTION_KIND", "").replace(",", "-")
        actual_service_name = reflection_name or str(__name__)
        actual_service_version = service_version or os.getenv("SERVICE_VERSION", "1.0.0")
        
        self._service_name = actual_service_name
        self._service_version = actual_service_version
        self._reflection_kind = actual_reflection_kind
        
        return self
    
    def with_logging_configuration(self, log_level: Optional[str] = None,
                                  enable_console: Optional[bool] = None,
                                  connection_string: Optional[str] = None) -> 'ConfigurationSetupBuilder':
        """Parse logging configuration."""
        actual_enable_console = enable_console if enable_console is not None else os.getenv("LOGGER_ENABLE_CONSOLE", "true").lower() == "true"
        actual_connection_string = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        actual_log_level = log_level or os.getenv("LOGGER_LOG_LEVEL", "INFO")
        
        instrumentation_options = {
            "azure_sdk": {"enabled": True},
            "django": {"enabled": False},
            "fastapi": {"enabled": False},
            "flask": {"enabled": True},
            "psycopg2": {"enabled": True},
            "requests": {"enabled": True},
            "urllib": {"enabled": True},
            "urllib3": {"enabled": True},
        }
        
        self._logger_enable_console = actual_enable_console
        self._logger_connection_string = actual_connection_string
        self._logger_instrumentation_options = instrumentation_options
        self._logger_log_level = actual_log_level
        
        return self
    
    def with_identity_configuration(self, enable_token_cache: Optional[bool] = None,
                                   allow_unencrypted_storage: Optional[bool] = None,
                                   custom_options: Optional[Dict[str, Any]] = None) -> 'ConfigurationSetupBuilder':
        """Parse identity configuration."""
        actual_token_cache = enable_token_cache if enable_token_cache is not None else os.getenv("IDENTITY_ENABLE_TOKEN_CACHE", "true").lower() == "true"
        actual_unencrypted = allow_unencrypted_storage if allow_unencrypted_storage is not None else os.getenv("IDENTITY_ALLOW_UNENCRYPTED_STORAGE", "true").lower() == "true"
        actual_custom_options = custom_options  # Reserved for future custom credential configuration
        actual_connection_string = self._logger_connection_string  # Share with logger by default
        
        self._identity_enable_token_cache = actual_token_cache
        self._identity_allow_unencrypted_storage = actual_unencrypted
        self._identity_custom_credential_options = actual_custom_options
        self._identity_connection_string = actual_connection_string
        
        return self
    
    # Note: KeyVault and Storage configuration methods have been removed.
    # These services now read environment variables directly in their
    # respective with_keyvault() and with_storage() methods for API simplicity.
    
    def with_environment_variables(self, 
                                  env_vars: Dict[str, str],
                                  in_docker: bool = True, 
                                  in_machine: bool = True) -> 'ConfigurationSetupBuilder':
        """Set environment variables conditionally based on runtime environment.
        
        This method can be called multiple times to build up different sets of environment variables.
        Variables are applied to os.environ based on the current runtime environment and the specified conditions.
        
        Args:
            env_vars: Dictionary of environment variable key-value pairs to set
            in_docker: If True, apply these variables when running in Docker (default: True)
            in_machine: If True, apply these variables when running on native machine (default: True)
            
        Returns:
            Self for method chaining
            
        Example:
            builder = (ConfigurationSetupBuilder()
                      .with_environment_detection()
                      .with_environment_variables({
                          "AZURE_CLIENT_ID": "app-id",
                          "AZURE_TENANT_ID": "tenant-id"
                      }, in_docker=True, in_machine=True)  # Apply in both environments
                      .with_environment_variables({
                          "AzureWebJobsStorage": "UseDevelopmentStorage=true"
                      }, in_docker=False, in_machine=True)  # Only on native machine
                      .build())
        """
        # Ensure environment detection has been called first
        if not hasattr(self, '_running_in_docker'):
            raise ValueError("with_environment_detection() must be called before with_environment_variables()")
        
        # Ensure local_settings exists
        if not hasattr(self, '_local_settings'):
            self._local_settings = {}
        
        # Check if we should apply these variables based on current environment
        should_apply = False
        if self._running_in_docker and in_docker:
            should_apply = True
        elif not self._running_in_docker and in_machine:
            should_apply = True
        
        if should_apply:
            # Add to local settings for the configuration
            self._local_settings.update(env_vars)
            
            # Also set in os.environ immediately for runtime use
            itter = 0
            for key, value in env_vars.items():
                os.environ[key] = value
                print(f"{itter} Loaded for override: {key}={str(value)[:8]}...")
                itter += 1
                
            print(f"Applied {len(env_vars)} environment variables for {'Docker' if self._running_in_docker else 'machine'} environment")
        else:
            print(f"Skipped {len(env_vars)} environment variables (not applicable for current environment)")
        
        return self
    
    def build(self) -> EnvironmentConfiguration:
        """Build complete environment configuration."""
        return EnvironmentConfiguration(
            # Environment detection
            running_in_docker=self._running_in_docker,
            local_settings=self._local_settings,
            
            # Local environment management
            local_env_manager=self._local_env_manager,
            
            # Service configuration
            service_name=self._service_name,
            service_version=self._service_version,
            reflection_kind=self._reflection_kind,
            
            # Logging configuration
            logger_enable_console=self._logger_enable_console,
            logger_connection_string=self._logger_connection_string,
            logger_instrumentation_options=self._logger_instrumentation_options,
            logger_log_level=self._logger_log_level,
            
            # Identity configuration
            identity_enable_token_cache=self._identity_enable_token_cache,
            identity_allow_unencrypted_storage=self._identity_allow_unencrypted_storage,
            identity_custom_credential_options=self._identity_custom_credential_options,
            identity_connection_string=self._identity_connection_string,
        )
    
    @staticmethod
    def _is_running_in_docker() -> bool:
        """Check if running inside a Docker container."""
        if os.path.exists('/.dockerenv'):
            return True
        try:
            with open('/proc/1/cgroup', 'rt', encoding='utf-8') as f:
                content = f.read()
                return any(indicator in content for indicator in ['docker', 'kubepods', 'containerd'])
        except (FileNotFoundError, PermissionError, OSError):
            pass
        return False




# Note: Environment configuration is now required to be explicitly provided
# Use ConfigurationSetupDirector.build_default_setup() for default configuration


class ManagementInitializationStage(IntEnum):
    """Management layer initialization stages."""
    NOT_STARTED = 0
    LOGGER_READY = 1
    IDENTITY_READY = 2
    KEYVAULT_READY = 3
    COMPLETE = 4


class ResourceInitializationStage(IntEnum):
    """Resource layer initialization stages."""
    NOT_STARTED = 0
    STORAGE_READY = 1
    COMPLETE = 2


@dataclass
class AzureManagementConfiguration:
    """Management services configuration."""
    logger: Any
    local_env_manager: Any
    identity: Any
    keyvaults: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize keyvaults as empty dict if None."""
        if self.keyvaults is None:
            self.keyvaults = {}
    
    def validate(self) -> bool:
        """Validate required services are initialized."""
        if not self.logger:
            raise ValueError("Logger is required")
        if not self.identity:
            raise ValueError("Identity is required")
        if not self.local_env_manager:
            raise ValueError("Local env manager is required")
        return True
    
    def get_keyvault(self, name: str = "default") -> Optional[Any]:
        """Get keyvault by name."""
        return self.keyvaults.get(name)
    
    def get_primary_keyvault(self) -> Optional[Any]:
        """Get the primary/default keyvault."""
        return self.get_keyvault("default") or next(iter(self.keyvaults.values()), None)
    
    @property
    def keyvault(self) -> Optional[Any]:
        """Backward compatibility property for single keyvault access."""
        return self.get_primary_keyvault()
    



@dataclass
class AzureResourceConfiguration:
    """Resource services configuration."""
    storage_accounts: Dict[str, Any] = None
    cosmosdb_clients: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize storage_accounts and cosmosdb_clients as empty dicts if None."""
        if self.storage_accounts is None:
            self.storage_accounts = {}
        if self.cosmosdb_clients is None:
            self.cosmosdb_clients = {}
    
    def validate(self) -> bool:
        """Validate resource configuration."""
        return True
    
    def get_storage(self, name: str = "default") -> Optional[Any]:
        """Get storage account by name."""
        return self.storage_accounts.get(name)
    
    def get_primary_storage(self) -> Optional[Any]:
        """Get the primary/default storage account."""
        return self.get_storage("default") or next(iter(self.storage_accounts.values()), None)
    
    @property
    def storage_account(self) -> Optional[Any]:
        """Backward compatibility property for single storage account access."""
        return self.get_primary_storage()
    
    def get_cosmosdb(self, name: str = "default") -> Optional[Any]:
        """Get CosmosDB client by name."""
        return self.cosmosdb_clients.get(name)
    
    def get_primary_cosmosdb(self) -> Optional[Any]:
        """Get the primary/default CosmosDB client."""
        return self.get_cosmosdb("default") or next(iter(self.cosmosdb_clients.values()), None)
    
    @property
    def cosmosdb_client(self) -> Optional[Any]:
        """Backward compatibility property for single CosmosDB client access."""
        return self.get_primary_cosmosdb()


@dataclass
class AzureConfiguration:
    """Combined management and resource configuration."""
    management: AzureManagementConfiguration
    resources: AzureResourceConfiguration
    
    def validate(self) -> bool:
        """Validate all services are initialized."""
        return self.management.validate() and self.resources.validate()


class AzureManagementBuilder:
    """Builder for Azure management services."""
    
    def __init__(self, env_config: EnvironmentConfiguration):
        """Initialize with required environment configuration.
        
        Args:
            env_config: Environment configuration (use ConfigurationSetupDirector.build_default_setup() for defaults)
        """
        if not env_config:
            raise ValueError("Environment configuration is required")
        self._env_config = env_config
        self.reset()
    
    def reset(self) -> 'AzureManagementBuilder':
        """Reset builder to initial state."""
        self._logger = None
        self._local_env_manager = None
        self._identity = None
        self._keyvaults: Dict[str, Any] = {}
        self._stage = ManagementInitializationStage.NOT_STARTED
        return self
    
    def with_logger(self, log_level: Optional[str] = None, enable_console: Optional[bool] = None) -> 'AzureManagementBuilder':
        """Initialize logger."""
        if self._stage != ManagementInitializationStage.NOT_STARTED:
            raise ValueError(f"Logger must be created first. Current stage: {self._stage}")
        
        # Use provided values or fall back to environment configuration
        actual_log_level = log_level or self._env_config.logger_log_level
        actual_enable_console = enable_console if enable_console is not None else self._env_config.logger_enable_console
        
        if "functionapp" in self._env_config.reflection_kind:
            self._logger = create_function_logger(
                function_app_name=self._env_config.service_name,
                function_name=self._env_config.reflection_kind,
                service_version=self._env_config.service_version,
                connection_string=self._env_config.logger_connection_string,
                log_level=actual_log_level,
                instrumentation_options=self._env_config.logger_instrumentation_options, 
            )
            self._logger.info(
                f"Function logger initialized: {self._env_config.reflection_kind} {self._env_config.service_name}",
                extra={"logger_type": "function", "function_name": self._env_config.reflection_kind}
            )
        else:
            self._logger = create_app_logger(
                service_name=self._env_config.service_name,
                service_version=self._env_config.service_version,
                connection_string=self._env_config.logger_connection_string,
                log_level=actual_log_level,
                enable_console_logging=actual_enable_console,
                instrumentation_options=self._env_config.logger_instrumentation_options,
            )
            self._logger.info(
                f"App logger initialized: {self._env_config.reflection_kind} {self._env_config.service_name}",
                extra={"logger_type": "app", "service_kind": self._env_config.reflection_kind}
            )
        
        # Get local env manager from environment configuration (created in ConfigurationSetupBuilder)
        self._local_env_manager = self._env_config.local_env_manager
        if not self._local_env_manager:
            raise ValueError("Local environment manager not found in configuration. Ensure with_local_env_management() was called in ConfigurationSetupBuilder.")
        
        self._stage = ManagementInitializationStage.LOGGER_READY
        return self
    
    def with_identity(self, enable_token_cache: Optional[bool] = None, 
                     allow_unencrypted_storage: Optional[bool] = None) -> 'AzureManagementBuilder':
        """Initialize identity."""
        if self._stage != ManagementInitializationStage.LOGGER_READY:
            raise ValueError(f"Identity requires logger to be created first. Current stage: {self._stage}")
        
        # Use provided values or fall back to environment configuration
        actual_token_cache = enable_token_cache if enable_token_cache is not None else self._env_config.identity_enable_token_cache
        actual_unencrypted = allow_unencrypted_storage if allow_unencrypted_storage is not None else self._env_config.identity_allow_unencrypted_storage
        
        self._identity = create_azure_identity(
            service_name=self._env_config.service_name,
            service_version=self._env_config.service_version,
            enable_token_cache=actual_token_cache,
            allow_unencrypted_storage=actual_unencrypted,
            custom_credential_options=self._env_config.identity_custom_credential_options,
            connection_string=self._env_config.identity_connection_string,
            logger=self._logger,
        )
        
        self._logger.info("Identity manager initialized")
        self._stage = ManagementInitializationStage.IDENTITY_READY
        return self
    
    def with_keyvault(self, name: str = "default", vault_url: Optional[str] = None,
                     enable_secrets: Optional[bool] = None, enable_keys: Optional[bool] = None,
                     enable_certificates: Optional[bool] = None) -> 'AzureManagementBuilder':
        """Initialize named Key Vault.
        
        Reads configuration from environment variables if not provided:
        - key_vault_uri: Key Vault URL
        - KEYVAULT_ENABLE_SECRETS: Enable secrets (default: true)
        - KEYVAULT_ENABLE_KEYS: Enable keys (default: false)
        - KEYVAULT_ENABLE_CERTIFICATES: Enable certificates (default: false)
        """
        if self._stage < ManagementInitializationStage.IDENTITY_READY:
            raise ValueError(f"Key Vault requires identity to be created first. Current stage: {self._stage}")
        
        if name in self._keyvaults:
            raise ValueError(f"Key Vault '{name}' already configured")
        
        # Read environment variables directly for default keyvault, use provided values for named ones
        if not vault_url and name == "default":
            vault_url = os.getenv("key_vault_uri")
        
        # Environment variable fallbacks with sensible defaults
        actual_enable_secrets = enable_secrets if enable_secrets is not None else os.getenv("KEYVAULT_ENABLE_SECRETS", "true").lower() == "true"
        actual_enable_keys = enable_keys if enable_keys is not None else os.getenv("KEYVAULT_ENABLE_KEYS", "false").lower() == "true"
        actual_enable_certificates = enable_certificates if enable_certificates is not None else os.getenv("KEYVAULT_ENABLE_CERTIFICATES", "false").lower() == "true"
        
        # Create Key Vault if URL is available
        if vault_url:
            keyvault = create_azure_keyvault(
                vault_url=vault_url,
                azure_identity=self._identity,
                service_name=self._env_config.service_name,
                service_version=self._env_config.service_version,
                logger=self._logger,
                connection_string=self._env_config.logger_connection_string,  # Share logger connection
                enable_secrets=actual_enable_secrets,
                enable_keys=actual_enable_keys,
                enable_certificates=actual_enable_certificates,
            )
            self._keyvaults[name] = keyvault
            self._logger.info(f"Key Vault '{name}' initialized: {vault_url}")
        else:
            self._logger.info(f"No Key Vault URL configured for '{name}'. Skipping Key Vault initialization.")
        
        self._stage = ManagementInitializationStage.KEYVAULT_READY
        return self
    
    def build(self) -> AzureManagementConfiguration:
        """Build management configuration."""
        if self._stage < ManagementInitializationStage.KEYVAULT_READY:
            raise ValueError(f"Management configuration incomplete. Current stage: {self._stage}")
        
        config = AzureManagementConfiguration(
            logger=self._logger,
            local_env_manager=self._local_env_manager,
            identity=self._identity,
            keyvaults=self._keyvaults.copy()
        )
        
        config.validate()
        
        self._logger.info(
            f"Azure management configuration built successfully for service '{self._env_config.service_name}' v{self._env_config.service_version}",
            extra={
                "service_name": self._env_config.service_name,
                "service_version": self._env_config.service_version,
                "console_logging": self._env_config.logger_enable_console,
                "token_cache_enabled": self._env_config.identity_enable_token_cache,
                "telemetry_enabled": bool(self._env_config.logger_connection_string),
                "keyvaults_count": len(self._keyvaults),
                "keyvault_names": list(self._keyvaults.keys()),
                "primary_keyvault_enabled": bool(config.get_primary_keyvault()),
                "running_in_docker": self._env_config.running_in_docker,
            }
        )
        
        self._stage = ManagementInitializationStage.COMPLETE
        return config


class AzureResourceBuilder:
    """Builder for Azure resource services."""
    
    def __init__(self, management_config: AzureManagementConfiguration, env_config: EnvironmentConfiguration):
        """Initialize with management configuration and environment configuration.
        
        Args:
            management_config: Valid management configuration
            env_config: Environment configuration (use ConfigurationSetupDirector.build_default_setup() for defaults)
        """
        if not management_config or not management_config.validate():
            raise ValueError("Valid management configuration is required")
        if not env_config:
            raise ValueError("Environment configuration is required")
        
        self._management = management_config
        self._env_config = env_config
        self._storage_accounts: Dict[str, Any] = {}
        self._cosmosdb_clients: Dict[str, Any] = {}
        self._stage = ResourceInitializationStage.NOT_STARTED
    
    def with_storage(self, name: str = "default", account_url: Optional[str] = None, 
                    auto_construct_url: bool = True, enable_blob: Optional[bool] = None, 
                    enable_file: Optional[bool] = None, enable_queue: Optional[bool] = None) -> 'AzureResourceBuilder':
        """Initialize named storage account.
        
        Reads configuration from environment variables if not provided:
        - STORAGE_ACCOUNT_URL: Storage Account URL (default storage only)
        - STORAGE_ENABLE_BLOB: Enable blob storage (default: true)
        - STORAGE_ENABLE_FILE: Enable file storage (default: true)
        - STORAGE_ENABLE_QUEUE: Enable queue storage (default: true)
        """
        if name in self._storage_accounts:
            raise ValueError(f"Storage account '{name}' already configured")
        
        # Read environment variables directly for default storage, use provided values for named ones
        storage_url = account_url or (os.getenv("STORAGE_ACCOUNT_URL") if name == "default" else None)
        
        # Environment variable fallbacks with sensible defaults
        actual_enable_blob = enable_blob if enable_blob is not None else os.getenv("STORAGE_ENABLE_BLOB", "true").lower() == "true"
        actual_enable_file = enable_file if enable_file is not None else os.getenv("STORAGE_ENABLE_FILE", "true").lower() == "true"
        actual_enable_queue = enable_queue if enable_queue is not None else os.getenv("STORAGE_ENABLE_QUEUE", "true").lower() == "true"
        
        # Auto-construct storage URL from Key Vault secrets if requested
        if auto_construct_url and self._management.keyvault and not storage_url:
            try:
                project_code = self._management.keyvault.get_secret("project-code")
                azure_environment = self._management.keyvault.get_secret("resource-group-environment")
                
                # Different naming patterns based on storage account name
                if name == "default":
                    blob_account_name = f"stqueue{project_code}{azure_environment}"
                else:
                    blob_account_name = f"st{name}{project_code}{azure_environment}"
                    
                storage_url = f"https://{blob_account_name}.blob.core.windows.net/"
                self._management.logger.info(f"Auto-constructed storage URL for '{name}': {storage_url}")
            except Exception as e:
                self._management.logger.warning(f"Failed to auto-construct storage URL for '{name}': {e}")
                storage_url = None
        
        if storage_url:
            storage_account = create_azure_storage(
                account_url=storage_url,
                azure_identity=self._management.identity,
                service_name=self._env_config.service_name,
                service_version=self._env_config.service_version,
                logger=self._management.logger,
                connection_string=self._env_config.logger_connection_string,  # Share logger connection
                enable_blob_storage=actual_enable_blob,
                enable_file_storage=actual_enable_file,
                enable_queue_storage=actual_enable_queue,
            )
            self._storage_accounts[name] = storage_account
            self._management.logger.info(f"Storage account '{name}' initialized: {storage_url}")
        else:
            self._management.logger.info(f"No Storage URL configured for '{name}'. Skipping Storage initialization.")
        
        self._stage = ResourceInitializationStage.STORAGE_READY
        return self
    
    def with_cosmosdb(self, name: str = "default", endpoint: Optional[str] = None,
                     auto_construct_endpoint: bool = True) -> 'AzureResourceBuilder':
        """Initialize named CosmosDB client.
        
        Reads configuration from environment variables if not provided:
        - COSMOS_ENDPOINT: CosmosDB endpoint URL (default client only)
        """
        if name in self._cosmosdb_clients:
            raise ValueError(f"CosmosDB client '{name}' already configured")
        
        # Read environment variables directly for default cosmosdb, use provided values for named ones
        cosmos_endpoint = endpoint or (os.getenv("COSMOS_ENDPOINT") if name == "default" else None)
        
        # Auto-construct CosmosDB endpoint from Key Vault secrets if requested
        if auto_construct_endpoint and self._management.keyvault and not cosmos_endpoint:
            try:
                project_code = self._management.keyvault.get_secret("project-code")
                azure_environment = self._management.keyvault.get_secret("resource-group-environment")
                
                # Different naming patterns based on cosmosdb client name
                if name == "default":
                    cosmos_account_name = f"coscas-promptmgmt-{project_code}-{azure_environment}"
                else:
                    cosmos_account_name = f"coscas-{name}-{project_code}-{azure_environment}"
                    
                cosmos_endpoint = f"https://{cosmos_account_name}.documents.azure.com:443/"
                self._management.logger.info(f"Auto-constructed CosmosDB endpoint for '{name}': {cosmos_endpoint}")
            except Exception as e:
                self._management.logger.warning(f"Failed to auto-construct CosmosDB endpoint for '{name}': {e}")
                cosmos_endpoint = None
        
        if cosmos_endpoint:
            cosmosdb_client = create_azure_cosmosdb(
                endpoint=cosmos_endpoint,
                azure_identity=self._management.identity,
                service_name=self._env_config.service_name,
                service_version=self._env_config.service_version,
                logger=self._management.logger,
                connection_string=self._env_config.logger_connection_string,  # Share logger connection
            )
            self._cosmosdb_clients[name] = cosmosdb_client
            self._management.logger.info(f"CosmosDB client '{name}' initialized: {cosmos_endpoint}")
        else:
            self._management.logger.info(f"No CosmosDB endpoint configured for '{name}'. Skipping CosmosDB initialization.")
        
        return self
    
    def build(self) -> AzureResourceConfiguration:
        """Build resource configuration."""
        config = AzureResourceConfiguration(
            storage_accounts=self._storage_accounts.copy(),
            cosmosdb_clients=self._cosmosdb_clients.copy()
        )
        
        config.validate()
        
        self._management.logger.info(
            "Azure resource configuration built successfully",
            extra={
                "storage_accounts_count": len(self._storage_accounts),
                "storage_account_names": list(self._storage_accounts.keys()),
                "primary_storage_enabled": bool(config.get_primary_storage()),
                "cosmosdb_clients_count": len(self._cosmosdb_clients),
                "cosmosdb_client_names": list(self._cosmosdb_clients.keys()),
                "primary_cosmosdb_enabled": bool(config.get_primary_cosmosdb()),
            }
        )
        
        self._stage = ResourceInitializationStage.COMPLETE
        return config


# Directors are now in a separate module to avoid circular imports

__all__ = [
    # Configuration setup classes
    "ConfigurationSetupBuilder",
    "EnvironmentConfiguration",
    
    # Builder pattern classes
    "AzureManagementBuilder",
    "AzureResourceBuilder", 
    "AzureManagementConfiguration",
    "AzureResourceConfiguration",
    "AzureConfiguration"
]
