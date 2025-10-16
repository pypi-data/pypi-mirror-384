"""Azure configuration directors.

This module provides director patterns for common Azure configuration setups.
Directors orchestrate builders to create pre-configured combinations of Azure services.
"""

from .configuration import (
    ConfigurationSetupBuilder,
    AzureManagementBuilder,
    AzureResourceBuilder,
    AzureManagementConfiguration,
    AzureResourceConfiguration,
    AzureConfiguration,
)


class ConfigurationSetupDirector:
    """Director for common setup configurations."""
    
    @staticmethod
    def build_default_config():
        """Build default environment configuration.
        
        Note: This method does not set any Azure credentials directly.
        Azure credentials should be configured through:
        1. Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
        2. Azure CLI authentication
        3. Managed Identity when running in Azure
        4. Visual Studio Code/Azure Developer CLI authentication
        
        For local development, use Azure CLI 'az login' or set environment variables.
        """
        configuration_config = {
                    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
                    "AzureWebJobsDashboard": "UseDevelopmentStorage=true",
                    "input_queue_connection__queueServiceUri": "UseDevelopmentStorage=true",
                    "AzureWebJobsStorage__accountName": "UseDevelopmentStorage=true",
                    "AzureWebJobsStorage__blobServiceUri": "UseDevelopmentStorage=true"
                }
        return (ConfigurationSetupBuilder()
                .with_local_env_management()  # FIRST: Load .env files and environment variables
                .with_environment_detection()
                .with_environment_variables(configuration_config, in_docker=False, in_machine=True)  # Development storage only for local machine
                .with_service_configuration()
                .with_logging_configuration()
                .with_identity_configuration()
                .build())  # keyvault/storage configs removed - now handled directly in service creation


class AzureManagementDirector:
    """Director for common management configurations."""
    
    @staticmethod
    def build_default_config(configuration_config) -> AzureManagementConfiguration:
        """Build default management configuration."""
        return (AzureManagementBuilder(configuration_config)
                .with_logger()
                .with_identity()
                .with_keyvault()
                .build())


class AzureResourceDirector:
    """Director for common combined configurations."""
    
    @staticmethod
    def build_default_config(configuration_config, management_config) -> AzureConfiguration:
        """Build default configuration."""
        # Create environment config once and reuse it
        #env_config = ConfigurationSetupDirector.build_default_setup()
        
        # Create management config using the same environment config
        # Create resource config using the same environment config
        resource_config = AzureResourceBuilder(management_config=management_config, env_config=configuration_config).with_storage().build()
        return AzureConfiguration(management=management_config, resources=resource_config)
    



__all__ = [
    "ConfigurationSetupDirector",
    "AzureManagementDirector", 
    "AzureResourceDirector"] 