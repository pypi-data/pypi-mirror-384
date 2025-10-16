"""Azure configuration and builder patterns.

This module provides sophisticated builder patterns for orchestrating Azure services
with comprehensive configuration management and environment detection.
"""

from .configuration import (
    # Configuration setup classes
    ConfigurationSetupBuilder,
    EnvironmentConfiguration,
    
    # Builder pattern classes
    AzureManagementBuilder,
    AzureResourceBuilder, 
    AzureManagementConfiguration,
    AzureResourceConfiguration,
    AzureConfiguration
)

from .directors import (
    # Director pattern classes
    ConfigurationSetupDirector,
    AzureManagementDirector,
    AzureResourceDirector, 
)

__all__ = [
    # Configuration setup classes
    "ConfigurationSetupBuilder",
    "EnvironmentConfiguration",
    
    # Builder pattern classes
    "AzureManagementBuilder",
    "AzureResourceBuilder", 
    "AzureManagementConfiguration",
    "AzureResourceConfiguration",
    "AzureConfiguration",
    
    # Director pattern classes
    "ConfigurationSetupDirector",
    "AzureManagementDirector",
    "AzureResourceDirector", 
] 