from .azure_mcp_server import mcp, initialize_server
from .services.base import AzureMCPError

if __name__ == "__main__":
    try:
        initialize_server(auto_discover=True)
        print("Azure MCP Server initialized successfully with auto-discovery")
    except AzureMCPError as e:
        print(f"Warning: Failed to auto-initialize: {e}")
        print("Server will attempt initialization on first tool use.")

    print("Starting Azure Infrastructure MCP Server...")
    mcp.run()
