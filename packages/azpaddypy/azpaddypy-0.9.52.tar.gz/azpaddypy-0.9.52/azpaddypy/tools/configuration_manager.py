"""
Azure Configuration Management Tool.

This module provides a comprehensive configuration management system that unifies
environment variables and JSON configuration files with access tracking and
verbose reporting capabilities.

Features:
- Multi-source configuration loading (environment variables, JSON files)
- Access time tracking with human-readable timestamps
- Verbose pretty printing with origin tracking
- Real-time configuration state management
- Configurable precedence hierarchy
- Comprehensive error handling and logging
"""

import os
import json
import pathlib
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from ..mgmt.logging import AzureLogger, create_app_logger
from ..builder.configuration import EnvironmentConfiguration


class ConfigSource(Enum):
    """Configuration source types."""
    ENVIRONMENT = "Environment Variable"
    CONFIG_FILE = "Configuration File"
    DEFAULT = "Default Value"
    KEYVAULT = "Azure Key Vault"
    RUNTIME = "Runtime Set"


@dataclass
class ConfigEntry:
    """Configuration entry with metadata."""
    key: str
    value: Any
    source: ConfigSource
    source_detail: str  # File path or "Environment"
    loaded_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0

    def mark_accessed(self):
        """Mark this entry as accessed and update counters."""
        self.last_accessed = time.time()
        self.access_count += 1

    def get_human_readable_last_access(self) -> str:
        """Get human readable last access time (seconds granularity)."""
        dt = datetime.fromtimestamp(self.last_accessed)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def get_human_readable_loaded_at(self) -> str:
        """Get human readable loaded time (seconds granularity)."""
        dt = datetime.fromtimestamp(self.loaded_at)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class LogExecution:
    """Configuration for function execution logging."""
    log_execution: bool
    log_args: bool
    log_result: bool

    @classmethod
    def from_config_manager(cls, config_manager: 'ConfigurationManager') -> 'LogExecution':
        """Create LogExecution instance from configuration manager."""
        return cls(
            log_execution=config_manager.get_config(key="log_execution", default=True),
            log_args=config_manager.get_config(key="log_args", default=False),
            log_result=config_manager.get_config(key="log_result", default=False),
        )

    def to_dict(self) -> Dict[str, bool]:
        """Convert LogExecution instance to dictionary."""
        return {
            "log_execution": self.log_execution,
            "log_args": self.log_args,
            "log_result": self.log_result,
        }


class ConfigurationManager:
    """
    Comprehensive configuration management with multi-source support,
    access tracking, and verbose reporting capabilities.
    
    This tool follows the azpaddypy pattern for resource management with
    proper logging, error handling, and configuration management. It provides
    unified access to environment variables and JSON configuration files
    with detailed tracking and reporting features.
    
    Features:
    - Multi-source configuration loading
    - Access time tracking with human-readable timestamps  
    - Verbose pretty printing with origin information
    - Configurable precedence hierarchy
    - Real-time configuration state management
    - Comprehensive error handling and logging
    """

    def __init__(
        self,
        environment_configuration: EnvironmentConfiguration,
        configs_dir: str = "./configs",
        auto_reload: bool = False,
        include_env_vars: bool = True,
        env_var_prefix: Optional[str] = None,
        logger: Optional[AzureLogger] = None,
        keyvault_clients: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ConfigurationManager.
        
        Args:
            environment_configuration: Environment configuration from ConfigurationSetupBuilder
            configs_dir: Directory containing JSON configuration files
            auto_reload: Whether to automatically reload configs on access
            include_env_vars: Whether to include environment variables
            env_var_prefix: Filter environment variables by prefix (e.g., "APP_")
            logger: Optional AzureLogger instance (if not provided, creates one from environment config)
            keyvault_clients: Optional dictionary of named keyvault clients.
        """
        self.environment_configuration = environment_configuration
        self.configs_dir = pathlib.Path(configs_dir)
        self.auto_reload = auto_reload
        self.include_env_vars = include_env_vars
        self.env_var_prefix = env_var_prefix
        self.keyvault_clients = keyvault_clients or {}

        # Extract service info from environment configuration
        self.service_name = environment_configuration.service_name
        self.service_version = environment_configuration.service_version

        # Create or use provided logger
        if logger:
            self.logger = logger
        else:
            self.logger = create_app_logger(
                service_name=f"{self.service_name}_config_manager",
                service_version=self.service_version,
                connection_string=environment_configuration.logger_connection_string,
                log_level=getattr(logging, environment_configuration.logger_log_level.upper(), logging.INFO),
                enable_console_logging=environment_configuration.logger_enable_console,
            )

        # Internal storage for configuration entries
        self._config_entries: Dict[str, ConfigEntry] = {}
        self._file_timestamps: Dict[str, float] = {}
        
        # Load initial configuration
        self._load_all_configurations()

        self.logger.info(
            f"Configuration Manager initialized for service '{self.service_name}' v{self.service_version}",
            extra={
                "configs_dir": str(self.configs_dir),
                "auto_reload": auto_reload,
                "include_env_vars": include_env_vars,
                "env_var_prefix": env_var_prefix,
                "total_configs": len(self._config_entries)
            }
        )

    def _load_all_configurations(self):
        """Load configurations from all sources."""
        with self.logger.create_span("ConfigurationManager._load_all_configurations"):
            self._config_entries.clear()
            
            # Load environment variables first (lowest precedence)
            if self.include_env_vars:
                self._load_environment_variables()
            
            # Load JSON configuration files (higher precedence)
            self._load_config_files()
            
            self.logger.info(f"Loaded {len(self._config_entries)} configuration entries from all sources")

    def _load_environment_variables(self):
        """Load environment variables into configuration."""
        with self.logger.create_span("ConfigurationManager._load_environment_variables"):
            loaded_count = 0
            
            for key, value in os.environ.items():
                # Apply prefix filter if specified
                if self.env_var_prefix and not key.startswith(self.env_var_prefix):
                    continue
                
                self._config_entries[key] = ConfigEntry(
                    key=key,
                    value=value,
                    source=ConfigSource.ENVIRONMENT,
                    source_detail="Environment Variable"
                )
                loaded_count += 1
            
            self.logger.debug(f"Loaded {loaded_count} environment variables")

    def _load_config_files(self):
        """Load JSON configuration files from configs directory."""
        with self.logger.create_span("ConfigurationManager._load_config_files"):
            if not self.configs_dir.exists():
                self.logger.warning(f"Configs directory does not exist: {self.configs_dir}")
                return
            
            loaded_files = 0
            loaded_entries = 0
            
            # Find all JSON files in configs directory
            json_files = list(self.configs_dir.glob("*.json"))
            
            for json_file in json_files:
                try:
                    file_stats = json_file.stat()
                    file_timestamp = file_stats.st_mtime
                    
                    # Track file timestamps for reload detection
                    self._file_timestamps[str(json_file)] = file_timestamp
                    
                    with open(json_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Flatten nested JSON structure (without filename prefix)
                    flattened = self._flatten_json(config_data)
                    
                    for key, value in flattened.items():
                        # Use relative path if possible, otherwise use absolute path
                        try:
                            relative_path = json_file.relative_to(pathlib.Path.cwd())
                            source_detail = str(relative_path)
                        except ValueError:
                            # File is not in current working directory (e.g., temp dir during testing)
                            source_detail = str(json_file)
                            
                        self._config_entries[key] = ConfigEntry(
                            key=key,
                            value=value,
                            source=ConfigSource.CONFIG_FILE,
                            source_detail=source_detail
                        )
                        loaded_entries += 1
                    
                    loaded_files += 1
                    self.logger.debug(f"Loaded configuration file: {json_file}")
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON in file {json_file}: {e}")
                except Exception as e:
                    self.logger.error(f"Error loading config file {json_file}: {e}", exc_info=True)
            
            self.logger.info(f"Loaded {loaded_files} config files with {loaded_entries} entries")

    def _flatten_json(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested JSON structure with dot notation."""
        result = {}
        
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                result.update(self._flatten_json(value, new_key))
            else:
                result[new_key] = value
        
        return result

    def _check_and_reload(self):
        """Check if files have changed and reload if necessary."""
        if not self.auto_reload:
            return
        
        needs_reload = False
        
        # Check if any tracked files have been modified
        for file_path, stored_timestamp in self._file_timestamps.items():
            file_obj = pathlib.Path(file_path)
            if file_obj.exists():
                current_timestamp = file_obj.stat().st_mtime
                if current_timestamp > stored_timestamp:
                    needs_reload = True
                    break
        
        # Check for new files
        if self.configs_dir.exists():
            current_files = set(str(f) for f in self.configs_dir.glob("*.json"))
            tracked_files = set(self._file_timestamps.keys())
            if current_files != tracked_files:
                needs_reload = True
        
        if needs_reload:
            self.logger.info("Configuration files changed, reloading...")
            self._load_all_configurations()

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with access tracking.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        self._check_and_reload()
        
        with self.logger.create_span("ConfigurationManager.get_config", attributes={"config_key": key}):
            if key in self._config_entries:
                entry = self._config_entries[key]
                entry.mark_accessed()
                
                self.logger.debug(f"Retrieved config: {key}", extra={
                    "source": entry.source.value,
                    "source_detail": entry.source_detail,
                    "access_count": entry.access_count
                })
                
                return entry.value
            else:
                self.logger.debug(f"Config key not found, using default: {key}", extra={"default": default})
                return default

    def set_config(self, key: str, value: Any, env: bool = False):
        """
        Set a configuration value at runtime.

        This will overwrite any existing value for the given key.

        Args:
            key: The configuration key to set.
            value: The value to set.
            env: If True, also set the value as an environment variable.
        """
        with self.logger.create_span("ConfigurationManager.set_config", attributes={"config_key": key, "set_env": env}):
            self._config_entries[key] = ConfigEntry(
                key=key,
                value=value,
                source=ConfigSource.RUNTIME,
                source_detail="Set at runtime"
            )
            self.logger.info(f"Configuration key '{key}' was set at runtime.")

            if env:
                try:
                    os.environ[key] = str(value)
                    self.logger.info(f"Environment variable '{key}' was also set.")
                except Exception as e:
                    self.logger.error(f"Failed to set environment variable for key '{key}': {e}", exc_info=True)

    def get_keyvault_secret(self, keyvault_name: str, secret_name: str, ttl: Optional[int] = None) -> Any:
        """
        Get a secret from Azure Key Vault with optional TTL caching.

        If ttl is None or 0, it always fetches from Key Vault.
        If ttl is > 0 (seconds), it checks the cache first.

        Args:
            keyvault_name: The name of the keyvault client to use.
            secret_name: The name of the secret to retrieve.
            ttl: Time-to-live for the secret in seconds.

        Returns:
            The secret value, or None if not found.
        """
        with self.logger.create_span("ConfigurationManager.get_keyvault_secret", attributes={"keyvault_name": keyvault_name, "secret_name": secret_name, "ttl": ttl}):
            config_key = f"keyvault.{keyvault_name}.{secret_name}"

            # Check cache if TTL is enabled
            if ttl and ttl > 0:
                if config_key in self._config_entries:
                    entry = self._config_entries[config_key]
                    age_seconds = time.time() - entry.loaded_at
                    if age_seconds < ttl:
                        self.logger.debug(f"Secret '{secret_name}' found in cache and is within TTL.", extra={"key": config_key})
                        return self.get_config(config_key)

            # Fetch from Key Vault
            if keyvault_name not in self.keyvault_clients:
                self.logger.error(f"Key Vault client '{keyvault_name}' not configured.", extra={"keyvault_name": keyvault_name})
                return None

            kv_client = self.keyvault_clients[keyvault_name]
            try:
                self.logger.debug(f"Fetching secret '{secret_name}' from Key Vault '{keyvault_name}'.", extra={"key": config_key})
                secret_value = kv_client.get_secret(secret_name=secret_name)

                if secret_value is None:
                    self.logger.warning(f"Secret '{secret_name}' not found in Key Vault '{keyvault_name}'")
                    return None

                self._config_entries[config_key] = ConfigEntry(
                    key=config_key,
                    value=secret_value,
                    source=ConfigSource.KEYVAULT,
                    source_detail=keyvault_name,
                    loaded_at=time.time() # Reset loaded_at on fetch
                )
                
                return self.get_config(config_key)

            except Exception as e:
                self.logger.error(f"Failed to retrieve secret '{secret_name}' from Key Vault '{keyvault_name}': {e}", exc_info=True)
                return None

    def set_keyvault_secret(self, keyvault_name: str, secret_name: str, secret_value: Any, local: bool = False, env: bool = False):
        """
        Set a secret in Azure Key Vault and optionally in the local config.

        Args:
            keyvault_name: The name of the keyvault client to use.
            secret_name: The name of the secret to set.
            secret_value: The secret value of the secret to set.
            local: If True, also store the secret in the local configuration cache.
            env: If True and local is True, also set as an environment variable.
        """
        with self.logger.create_span("ConfigurationManager.set_keyvault_secret", attributes={"keyvault_name": keyvault_name, "secret_name": secret_name, "local": local, "env": env}):
            if keyvault_name not in self.keyvault_clients:
                self.logger.error(f"Key Vault client '{keyvault_name}' not configured.", extra={"keyvault_name": keyvault_name})
                return

            kv_client = self.keyvault_clients[keyvault_name]
            try:
                self.logger.debug(f"Setting secret '{secret_name}' in Key Vault '{keyvault_name}'.")
                # Key Vault secrets must be strings
                kv_client.set_secret(secret_name, str(secret_value))
                self.logger.info(f"Successfully set secret '{secret_name}' in Key Vault '{keyvault_name}'.")

                if local:
                    config_key = f"keyvault.{keyvault_name}.{secret_name}"
                    self.set_config(key=config_key, value=secret_value, env=env)

            except Exception as e:
                self.logger.error(f"Failed to set secret '{secret_name}' in Key Vault '{keyvault_name}': {e}", exc_info=True)

    def get_all_configs(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all configuration values
        """
        self._check_and_reload()
        
        with self.logger.create_span("ConfigurationManager.get_all_configs"):
            result = {}
            for key, entry in self._config_entries.items():
                entry.mark_accessed()
                result[key] = entry.value
            
            self.logger.debug(f"Retrieved all configs: {len(result)} entries")
            return result

    def has_config(self, key: str) -> bool:
        """Check if configuration key exists."""
        self._check_and_reload()
        return key in self._config_entries

    def reload_configs(self) -> bool:
        """
        Manually reload all configuration sources.
        
        Returns:
            True if reload was successful
        """
        try:
            with self.logger.create_span("ConfigurationManager.reload_configs"):
                old_count = len(self._config_entries)
                self._load_all_configurations()
                new_count = len(self._config_entries)
                
                self.logger.info(f"Configuration reloaded: {old_count} -> {new_count} entries")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to reload configurations: {e}", exc_info=True)
            return False

    def __repr__(self) -> str:
        """
        Generate verbose representation of all configurations with origin and access info.
        
        Returns:
            Formatted string with detailed configuration information
        """
        self._check_and_reload()
        
        with self.logger.create_span("ConfigurationManager.__repr__"):
            output = []
            output.append("=" * 80)
            output.append(f"Configuration Manager Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            output.append("=" * 80)
            output.append(f"Service: {self.service_name} v{self.service_version}")
            output.append(f"Configs Directory: {self.configs_dir}")
            output.append(f"Total Entries: {len(self._config_entries)}")
            output.append("")
            
            # Group by source for better organization
            by_source = {}
            for entry in self._config_entries.values():
                source_key = f"{entry.source.value} ({entry.source_detail})"
                if source_key not in by_source:
                    by_source[source_key] = []
                by_source[source_key].append(entry)
            
            # Sort sources for consistent output
            for source_key in sorted(by_source.keys()):
                entries = by_source[source_key]
                output.append(f"📁 {source_key}")
                output.append("-" * 60)
                
                # Sort entries by key
                for entry in sorted(entries, key=lambda x: x.key):
                    # Hide sensitive values in repr by default
                    value_display = "[HIDDEN]" if any(sensitive in entry.key.lower() 
                                                     for sensitive in ['password', 'secret', 'key', 'token']) else entry.value
                    if isinstance(value_display, str) and len(value_display) > 50:
                        value_display = value_display[:47] + "..."
                    
                    output.append(f"  🔑 {entry.key}")
                    output.append(f"      Value: {value_display}")
                    output.append(f"      Loaded: {entry.get_human_readable_loaded_at()}")
                    output.append(f"      Last Access: {entry.get_human_readable_last_access()}")
                    output.append(f"      Access Count: {entry.access_count}")
                    output.append("")
                
                output.append("")
            
            if not by_source:
                output.append("No configuration entries found.")
            
            output.append("=" * 80)
            
            result = "\n".join(output)
            self.logger.debug("Generated configuration report", extra={
                "total_entries": len(self._config_entries),
                "total_sources": len(by_source)
            })
            
            return result

    def get_filtered_report(self, filter_prefix: Optional[str] = None, show_values: bool = True) -> str:
        """
        Generate filtered configuration report.
        
        Args:
            filter_prefix: Only show keys starting with this prefix
            show_values: Whether to show actual values (set False for sensitive data)
            
        Returns:
            Formatted string with filtered configuration information
        """
        self._check_and_reload()
        
        with self.logger.create_span("ConfigurationManager.get_filtered_report"):
            output = []
            output.append("=" * 80)
            output.append(f"Filtered Configuration Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if filter_prefix:
                output.append(f"Filter: Keys starting with '{filter_prefix}'")
            output.append("=" * 80)
            output.append(f"Service: {self.service_name} v{self.service_version}")
            output.append("")
            
            # Group by source for better organization
            by_source = {}
            for entry in self._config_entries.values():
                if filter_prefix and not entry.key.startswith(filter_prefix):
                    continue
                    
                source_key = f"{entry.source.value} ({entry.source_detail})"
                if source_key not in by_source:
                    by_source[source_key] = []
                by_source[source_key].append(entry)
            
            # Sort sources for consistent output
            for source_key in sorted(by_source.keys()):
                entries = by_source[source_key]
                output.append(f"📁 {source_key}")
                output.append("-" * 60)
                
                # Sort entries by key
                for entry in sorted(entries, key=lambda x: x.key):
                    value_display = entry.value if show_values else "[HIDDEN]"
                    if isinstance(value_display, str) and len(value_display) > 50:
                        value_display = value_display[:47] + "..."
                    
                    output.append(f"  🔑 {entry.key}")
                    output.append(f"      Value: {value_display}")
                    output.append(f"      Loaded: {entry.get_human_readable_loaded_at()}")
                    output.append(f"      Last Access: {entry.get_human_readable_last_access()}")
                    output.append(f"      Access Count: {entry.access_count}")
                    output.append("")
                
                output.append("")
            
            if not by_source:
                output.append("No configuration entries found.")
                if filter_prefix:
                    output.append(f"(No entries match filter: '{filter_prefix}')")
            
            output.append("=" * 80)
            
            result = "\n".join(output)
            self.logger.debug("Generated filtered report", extra={
                "total_entries": len(self._config_entries),
                "filtered_sources": len(by_source),
                "filter_prefix": filter_prefix
            })
            
            return result

    def get_access_stats(self) -> Dict[str, Any]:
        """
        Get configuration access statistics.
        
        Returns:
            Dictionary with access statistics
        """
        self._check_and_reload()
        
        total_accesses = sum(entry.access_count for entry in self._config_entries.values())
        accessed_entries = sum(1 for entry in self._config_entries.values() if entry.access_count > 0)
        
        most_accessed = max(self._config_entries.values(), key=lambda x: x.access_count, default=None)
        
        return {
            "total_entries": len(self._config_entries),
            "accessed_entries": accessed_entries,
            "unaccessed_entries": len(self._config_entries) - accessed_entries,
            "total_accesses": total_accesses,
            "most_accessed_key": most_accessed.key if most_accessed else None,
            "most_accessed_count": most_accessed.access_count if most_accessed else 0,
            "sources": {
                source.value: sum(1 for entry in self._config_entries.values() if entry.source == source)
                for source in ConfigSource
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the configuration manager.
        
        Returns:
            Dictionary with health check results
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": {
                "name": self.service_name,
                "version": self.service_version
            },
            "checks": {}
        }
        
        try:
            # Check configs directory
            if self.configs_dir.exists():
                health_status["checks"]["configs_directory"] = {
                    "status": "healthy",
                    "path": str(self.configs_dir),
                    "exists": True
                }
            else:
                health_status["checks"]["configs_directory"] = {
                    "status": "warning",
                    "path": str(self.configs_dir),
                    "exists": False,
                    "message": "Configs directory does not exist"
                }
            
            # Check configuration loading
            config_count = len(self._config_entries)
            health_status["checks"]["configuration_loading"] = {
                "status": "healthy",
                "total_entries": config_count
            }
            
            # Check file accessibility
            accessible_files = 0
            total_files = len(list(self.configs_dir.glob("*.json"))) if self.configs_dir.exists() else 0
            
            if self.configs_dir.exists():
                for json_file in self.configs_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            json.load(f)
                        accessible_files += 1
                    except Exception:
                        pass
            
            health_status["checks"]["file_accessibility"] = {
                "status": "healthy" if accessible_files == total_files else "warning",
                "accessible_files": accessible_files,
                "total_files": total_files
            }
            
            self.logger.info("Configuration manager health check completed successfully")
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            health_status["checks"]["error"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            self.logger.error(f"Configuration manager health check failed: {e}", exc_info=True)
        
        return health_status


def create_configuration_manager(
    environment_configuration: EnvironmentConfiguration,
    configs_dir: str = "./configs",
    auto_reload: bool = False,
    include_env_vars: bool = True,
    env_var_prefix: Optional[str] = None,
    logger: Optional[AzureLogger] = None,
    keyvault_clients: Optional[Dict[str, Any]] = None,
) -> ConfigurationManager:
    """
    Factory function to create an instance of ConfigurationManager.
    
    Args:
        environment_configuration: Environment configuration from ConfigurationSetupBuilder
        configs_dir: Directory containing JSON configuration files
        auto_reload: Whether to automatically reload configs on access
        include_env_vars: Whether to include environment variables
        env_var_prefix: Filter environment variables by prefix (e.g., "APP_")
        logger: Optional AzureLogger instance (if not provided, creates one from environment config)
        keyvault_clients: Optional dictionary of named keyvault clients.
        
    Returns:
        Configured ConfigurationManager instance
    """
    return ConfigurationManager(
        environment_configuration=environment_configuration,
        configs_dir=configs_dir,
        auto_reload=auto_reload,
        include_env_vars=include_env_vars,
        env_var_prefix=env_var_prefix,
        logger=logger,
        keyvault_clients=keyvault_clients,
    ) 