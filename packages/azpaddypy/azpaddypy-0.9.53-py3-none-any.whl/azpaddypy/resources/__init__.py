"""Azure resources package for azpaddypy.

This package contains modules for interacting with various Azure resources
including Key Vault, Storage, and other Azure services.
"""

from .keyvault import AzureKeyVault, create_azure_keyvault
from .storage import AzureStorage, create_azure_storage

__all__ = [
    "AzureKeyVault",
    "create_azure_keyvault",
    "AzureStorage", 
    "create_azure_storage",
] 