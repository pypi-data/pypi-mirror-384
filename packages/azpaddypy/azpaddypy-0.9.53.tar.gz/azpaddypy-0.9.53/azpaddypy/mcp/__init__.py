from .azure_mcp_server import mcp, initialize_server
from .services.base import AzureMCPError, get_context

__all__ = [
    "mcp",
    "initialize_server",
    "AzureMCPError",
    "get_context",
]

__version__ = "2.0.0"
