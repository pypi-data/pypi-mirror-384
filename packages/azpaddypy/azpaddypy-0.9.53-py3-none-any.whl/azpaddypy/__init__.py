"""AzPaddyPy - Azure configuration management with builder patterns.

A comprehensive Python package for Azure cloud services integration with
standardized configuration management, OpenTelemetry tracing, and builder patterns.

Key Features:
- Azure Identity management with token caching
- Azure Key Vault integration for secrets management
- Azure Storage operations (blob, file, queue)
- Comprehensive logging with Application Insights
- Builder patterns for flexible service composition
- Environment detection and configuration management

Usage:
    # Direct imports (simplified)
    from azpaddypy import logger, identity, keyvault, storage_account
    
    # Builder pattern (recommended for complex scenarios)
    from azpaddypy.builder import AzureManagementBuilder, AzureResourceBuilder
    from azpaddypy.builder.directors import ConfigurationSetupDirector
"""

from .mgmt import *
from .resources import *
from .builder import *
from .tools import *

# Create default configuration for direct imports (backward compatibility)
from .builder.directors import AzureManagementDirector, AzureResourceDirector

__all__ = [
    # Builder patterns (via builder module imports)
    "ConfigurationSetupBuilder", "ConfigurationSetupDirector", "EnvironmentConfiguration",
    "AzureManagementBuilder", "AzureResourceBuilder", 
    "AzureManagementConfiguration", "AzureResourceConfiguration", "AzureConfiguration",
    "AzureManagementDirector", "AzureConfigurationDirector", "AzureResourceDirector",
    # Tools
    "CosmosPromptManager", "create_cosmos_prompt_manager",
    "ConfigurationManager", "create_configuration_manager",
]