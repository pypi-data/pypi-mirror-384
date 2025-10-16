from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

from .services import base
from .services import resources
from .services import storage
from .services import cosmos
from .services import subscription
from .services import aiagents

mcp = FastMCP("Azure Infrastructure")


def initialize_server(
    credential: Optional[Any] = None,
    subscription_id: Optional[str] = None,
    auto_discover: bool = True,
) -> None:
    ctx = base.get_context()

    if subscription_id or credential:
        ctx.initialize(credential=credential, subscription_id=subscription_id)
    elif auto_discover:
        ctx.initialize_with_auto_discovery()
    else:
        pass


@mcp.tool(description="List all resource groups in the current Azure subscription")
def list_resource_groups() -> List[Dict[str, Any]]:
    return resources.list_resource_groups()


@mcp.tool(description="List all Azure resources within a specific resource group")
def list_resources_in_group(resource_group: str) -> List[Dict[str, Any]]:
    return resources.list_resources_in_group(resource_group)


@mcp.tool(
    description="Export an Azure Resource Manager (ARM) template for a resource group, capturing all resource configurations"
)
def export_resource_group_template(resource_group: str) -> Dict[str, Any]:
    return resources.export_resource_group_template(resource_group)


@mcp.tool(
    description="Decompile an ARM template JSON file to Bicep format. Optionally specify output path, otherwise returns Bicep content as string"
)
def decompile_arm_to_bicep(
    arm_template_path: str, output_path: Optional[str] = None
) -> str:
    return resources.decompile_arm_to_bicep(arm_template_path, output_path)


@mcp.tool(
    description="List Azure Storage accounts. Optionally filter by resource group, otherwise lists all storage accounts in the subscription"
)
def list_storage_accounts(resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
    return storage.list_storage_accounts(resource_group)


@mcp.tool(description="List all blob containers in a specific Azure Storage account")
def list_storage_containers(
    account_name: str, resource_group: Optional[str] = None
) -> List[Dict[str, Any]]:
    return storage.list_storage_containers(account_name, resource_group)


@mcp.tool(
    description="Upload data to Azure Blob Storage. Supports base64-encoded data, custom content types, metadata, and overwrite control"
)
def upload_blob(
    account_name: str,
    container_name: str,
    blob_name: str,
    data: str,
    resource_group: Optional[str] = None,
    overwrite: bool = False,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    base64_encoded: bool = False,
) -> Dict[str, Any]:
    return storage.upload_blob(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        data=data,
        resource_group=resource_group,
        overwrite=overwrite,
        content_type=content_type,
        metadata=metadata,
        base64_encoded=base64_encoded,
    )


@mcp.tool(
    description="Download a blob from Azure Blob Storage. Optionally return content as base64-encoded string for binary data"
)
def download_blob(
    account_name: str,
    container_name: str,
    blob_name: str,
    resource_group: Optional[str] = None,
    return_base64: bool = False,
) -> Dict[str, Any]:
    return storage.download_blob(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        resource_group=resource_group,
        return_base64=return_base64,
    )


@mcp.tool(
    description="List all blobs in an Azure Storage container. Optionally filter by name prefix to narrow results"
)
def list_blobs(
    account_name: str,
    container_name: str,
    resource_group: Optional[str] = None,
    name_starts_with: Optional[str] = None,
) -> Dict[str, Any]:
    return storage.list_blobs(
        account_name=account_name,
        container_name=container_name,
        resource_group=resource_group,
        name_starts_with=name_starts_with,
    )


@mcp.tool(
    description="List Azure Cosmos DB accounts. Optionally filter by resource group, otherwise lists all accounts in the subscription"
)
def list_cosmosdb_accounts(
    resource_group: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return cosmos.list_cosmosdb_accounts(resource_group)


@mcp.tool(
    description="List all SQL API databases in a specific Azure Cosmos DB account"
)
def list_cosmosdb_sql_databases(
    account_name: str, resource_group: str
) -> List[Dict[str, Any]]:
    return cosmos.list_cosmosdb_sql_databases(account_name, resource_group)


@mcp.tool(
    description="List all containers (collections) in a specific Azure Cosmos DB SQL API database"
)
def list_cosmosdb_sql_containers(
    account_name: str, resource_group: str, database_name: str
) -> List[Dict[str, Any]]:
    return cosmos.list_cosmosdb_sql_containers(
        account_name, resource_group, database_name
    )


@mcp.tool(
    description="List all Azure subscriptions available to the current authenticated user"
)
def list_subscriptions() -> List[Dict[str, Any]]:
    return subscription.list_subscriptions()


@mcp.tool(
    description="Get detailed information about the currently active Azure subscription"
)
def get_subscription_info() -> Dict[str, Any]:
    return subscription.get_subscription_info()


@mcp.tool(
    description="List all available Azure regions (locations) for the current subscription"
)
def list_locations() -> List[Dict[str, Any]]:
    return subscription.list_locations()


@mcp.tool(
    description="List all AI agents in Azure AI Foundry. Optionally specify a project endpoint, otherwise uses auto-discovered project"
)
def list_ai_agents(ai_project_endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
    return aiagents.list_ai_agents(ai_project_endpoint)


@mcp.tool(description="List all Azure AI Foundry projects in the current subscription")
def list_ai_foundry_projects() -> List[Dict[str, Any]]:
    return aiagents.list_ai_foundry_projects()


@mcp.tool(
    description="Get detailed information about a specific AI agent by name in Azure AI Foundry. E.g. ai_project_endpoint=https://example-cog-service-dev.services.ai.azure.com/api/projects/example-project"
)
def get_ai_agent(
    name: str, ai_project_endpoint: Optional[str] = None
) -> Dict[str, Any]:
    return aiagents.get_ai_agent(name, ai_project_endpoint)


@mcp.tool(
    description="Create a new AI agent in Azure AI Foundry with specified model and instructions"
)
def create_ai_agent(
    name: str, model: str, instructions: str, ai_project_endpoint: Optional[str] = None
) -> Dict[str, Any]:
    return aiagents.create_ai_agent(name, model, instructions, ai_project_endpoint)


@mcp.tool(description="Delete an AI agent from Azure AI Foundry by its agent ID")
def delete_ai_agent(
    agent_id: str, ai_project_endpoint: Optional[str] = None
) -> Dict[str, Any]:
    return aiagents.delete_ai_agent(agent_id, ai_project_endpoint)


@mcp.tool(
    description="Send a message to an AI agent and get its response. Optionally specify thread_id to continue a conversation"
)
def invoke_ai_agent(
    agent_id: str,
    user_message: str,
    thread_id: Optional[str] = None,
    ai_project_endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    return aiagents.invoke_ai_agent(
        agent_id, user_message, thread_id, ai_project_endpoint
    )


if __name__ == "__main__":
    try:
        initialize_server(auto_discover=True)
        print("Azure MCP Server initialized successfully with auto-discovery")
    except base.AzureMCPError as e:
        print(f"Warning: Failed to auto-initialize: {e}")
        print("Server will attempt initialization on first tool use.")

    mcp.run()
