from typing import Any, Dict, List, Optional

from .base import get_context, AzureMCPError


def list_cosmosdb_accounts(resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        ctx = get_context()
        client = ctx.cosmos_client

        if resource_group:
            accounts = list(client.database_accounts.list_by_resource_group(resource_group))
        else:
            accounts = list(client.database_accounts.list())

        return [a.as_dict() for a in accounts]

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to list Cosmos DB accounts: {e}") from e


def list_cosmosdb_sql_databases(
    account_name: str,
    resource_group: str
) -> List[Dict[str, Any]]:
    try:
        ctx = get_context()
        client = ctx.cosmos_client

        dbs = list(client.sql_resources.list_sql_databases(resource_group, account_name))
        return [
            d.as_dict() if hasattr(d, "as_dict") else dict(d)
            for d in dbs
        ]

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(
            f"Failed to list SQL databases for Cosmos DB account '{account_name}': {e}"
        ) from e


def list_cosmosdb_sql_containers(
    account_name: str,
    resource_group: str,
    database_name: str
) -> List[Dict[str, Any]]:
    try:
        ctx = get_context()
        client = ctx.cosmos_client

        containers = list(client.sql_resources.list_sql_containers(
            resource_group,
            account_name,
            database_name
        ))
        return [
            c.as_dict() if hasattr(c, "as_dict") else dict(c)
            for c in containers
        ]

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(
            f"Failed to list SQL containers for database '{database_name}' "
            f"in account '{account_name}': {e}"
        ) from e
