from typing import Any, Dict, List, Optional, cast
import base64
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.credentials import AzureNamedKeyCredential

from .base import get_context, AzureMCPError


def list_storage_accounts(resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        ctx = get_context()
        client = ctx.storage_client

        if resource_group:
            accounts = list(client.storage_accounts.list_by_resource_group(resource_group))
        else:
            accounts = list(client.storage_accounts.list())

        result = []
        for acc in accounts:
            if hasattr(acc, "as_dict"):
                result.append(acc.as_dict())
            else:
                result.append({
                    "name": getattr(acc, "name", None),
                    "id": getattr(acc, "id", None),
                    "location": getattr(acc, "location", None),
                    "kind": getattr(acc, "kind", None),
                    "sku": getattr(acc, "sku", None),
                })

        return result

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(f"Failed to list storage accounts: {e}") from e


def list_storage_containers(
    account_name: str,
    resource_group: Optional[str] = None
) -> List[Dict[str, Any]]:
    try:
        ctx = get_context()
        client = ctx.storage_client

        if resource_group is None:
            found_rg = None
            for sa in list(client.storage_accounts.list()):
                if getattr(sa, "name", "").lower() == account_name.lower():
                    sa_id = getattr(sa, "id", "")
                    parts = [p for p in sa_id.split("/") if p]
                    if "resourceGroups" in parts:
                        rg_index = parts.index("resourceGroups") + 1
                        if rg_index < len(parts):
                            found_rg = parts[rg_index]
                            break

            if found_rg is None:
                raise AzureMCPError(
                    "resource_group not provided and could not be inferred for storage account"
                )
            resource_group = found_rg

        keys = client.storage_accounts.list_keys(resource_group, account_name)

        key_value: Optional[str] = None
        if hasattr(keys, "keys") and keys.keys and len(keys.keys) > 0:
            first = keys.keys[0]
            if isinstance(first, dict) and "value" in first:
                key_value = cast(str, first["value"])
            elif hasattr(first, "value"):
                key_value = first.value
            elif hasattr(first, "key"):
                key_value = first.key

        if key_value is None:
            try:
                key_value = cast(str, keys.as_dict()["keys"][0]["value"])
            except Exception:
                raise AzureMCPError(
                    "Could not parse storage account keys from management client response"
                )

        account_url = f"https://{account_name}.blob.core.windows.net"
        named_key_cred = AzureNamedKeyCredential(account_name, key_value)
        blob_service = BlobServiceClient(
            account_url=account_url,
            credential=named_key_cred
        )

        containers = blob_service.list_containers()
        result = []
        for c in containers:
            container_dict = {"name": getattr(c, "name", None)}

            try:
                props = {}
                if hasattr(c, "last_modified"):
                    props["lastModified"] = (
                        c.last_modified.isoformat() if c.last_modified else None
                    )
                if hasattr(c, "public_access"):
                    props["publicAccess"] = c.public_access
                if hasattr(c, "metadata"):
                    props["metadata"] = c.metadata
                container_dict["properties"] = props
            except Exception:
                pass

            result.append(container_dict)

        return result

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(
            f"Failed to list containers for storage account '{account_name}': {e}"
        ) from e


def upload_blob(
    account_name: str,
    container_name: str,
    blob_name: str,
    data: str,
    resource_group: Optional[str] = None,
    overwrite: bool = False,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    base64_encoded: bool = False
) -> Dict[str, Any]:
    try:
        ctx = get_context()
        client = ctx.storage_client

        if resource_group is None:
            found_rg = None
            for sa in list(client.storage_accounts.list()):
                if getattr(sa, "name", "").lower() == account_name.lower():
                    sa_id = getattr(sa, "id", "")
                    parts = [p for p in sa_id.split("/") if p]
                    if "resourceGroups" in parts:
                        rg_index = parts.index("resourceGroups") + 1
                        if rg_index < len(parts):
                            found_rg = parts[rg_index]
                            break

            if found_rg is None:
                raise AzureMCPError(
                    "resource_group not provided and could not be inferred for storage account"
                )
            resource_group = found_rg

        keys = client.storage_accounts.list_keys(resource_group, account_name)

        key_value: Optional[str] = None
        if hasattr(keys, "keys") and keys.keys and len(keys.keys) > 0:
            first = keys.keys[0]
            if isinstance(first, dict) and "value" in first:
                key_value = cast(str, first["value"])
            elif hasattr(first, "value"):
                key_value = first.value
            elif hasattr(first, "key"):
                key_value = first.key

        if key_value is None:
            try:
                key_value = cast(str, keys.as_dict()["keys"][0]["value"])
            except Exception:
                raise AzureMCPError(
                    "Could not parse storage account keys from management client response"
                )

        account_url = f"https://{account_name}.blob.core.windows.net"
        named_key_cred = AzureNamedKeyCredential(account_name, key_value)
        blob_service = BlobServiceClient(
            account_url=account_url,
            credential=named_key_cred
        )

        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        if base64_encoded:
            try:
                data_bytes = base64.b64decode(data)
            except Exception as e:
                raise AzureMCPError(f"Failed to decode base64 data: {e}") from e
        else:
            data_bytes = data.encode('utf-8')

        upload_kwargs: Dict[str, Any] = {}
        if content_type:
            upload_kwargs['content_settings'] = ContentSettings(content_type=content_type)
        if metadata:
            upload_kwargs['metadata'] = metadata

        blob_client.upload_blob(
            data_bytes,
            overwrite=overwrite,
            **upload_kwargs
        )

        blob_url = f"{account_url}/{container_name}/{blob_name}"

        return {
            "success": True,
            "blob_name": blob_name,
            "container_name": container_name,
            "account_name": account_name,
            "blob_url": blob_url,
            "size": len(data_bytes)
        }

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(
            f"Failed to upload blob '{blob_name}' to container '{container_name}' in storage account '{account_name}': {e}"
        ) from e


def download_blob(
    account_name: str,
    container_name: str,
    blob_name: str,
    resource_group: Optional[str] = None,
    return_base64: bool = False
) -> Dict[str, Any]:
    try:
        ctx = get_context()
        client = ctx.storage_client

        if resource_group is None:
            found_rg = None
            for sa in list(client.storage_accounts.list()):
                if getattr(sa, "name", "").lower() == account_name.lower():
                    sa_id = getattr(sa, "id", "")
                    parts = [p for p in sa_id.split("/") if p]
                    if "resourceGroups" in parts:
                        rg_index = parts.index("resourceGroups") + 1
                        if rg_index < len(parts):
                            found_rg = parts[rg_index]
                            break

            if found_rg is None:
                raise AzureMCPError(
                    "resource_group not provided and could not be inferred for storage account"
                )
            resource_group = found_rg

        keys = client.storage_accounts.list_keys(resource_group, account_name)

        key_value: Optional[str] = None
        if hasattr(keys, "keys") and keys.keys and len(keys.keys) > 0:
            first = keys.keys[0]
            if isinstance(first, dict) and "value" in first:
                key_value = cast(str, first["value"])
            elif hasattr(first, "value"):
                key_value = first.value
            elif hasattr(first, "key"):
                key_value = first.key

        if key_value is None:
            try:
                key_value = cast(str, keys.as_dict()["keys"][0]["value"])
            except Exception:
                raise AzureMCPError(
                    "Could not parse storage account keys from management client response"
                )

        account_url = f"https://{account_name}.blob.core.windows.net"
        named_key_cred = AzureNamedKeyCredential(account_name, key_value)
        blob_service = BlobServiceClient(
            account_url=account_url,
            credential=named_key_cred
        )

        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        blob_data = blob_client.download_blob()
        content = blob_data.readall()

        if return_base64:
            data_str = base64.b64encode(content).decode('utf-8')
        else:
            try:
                data_str = content.decode('utf-8')
            except UnicodeDecodeError:
                data_str = base64.b64encode(content).decode('utf-8')
                return_base64 = True

        blob_url = f"{account_url}/{container_name}/{blob_name}"
        blob_properties = blob_client.get_blob_properties()

        return {
            "success": True,
            "blob_name": blob_name,
            "container_name": container_name,
            "account_name": account_name,
            "blob_url": blob_url,
            "data": data_str,
            "size": len(content),
            "base64_encoded": return_base64,
            "content_type": blob_properties.content_settings.content_type if blob_properties.content_settings else None,
            "last_modified": blob_properties.last_modified.isoformat() if blob_properties.last_modified else None
        }

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(
            f"Failed to download blob '{blob_name}' from container '{container_name}' in storage account '{account_name}': {e}"
        ) from e


def list_blobs(
    account_name: str,
    container_name: str,
    resource_group: Optional[str] = None,
    name_starts_with: Optional[str] = None
) -> Dict[str, Any]:
    try:
        ctx = get_context()
        client = ctx.storage_client

        if resource_group is None:
            found_rg = None
            for sa in list(client.storage_accounts.list()):
                if getattr(sa, "name", "").lower() == account_name.lower():
                    sa_id = getattr(sa, "id", "")
                    parts = [p for p in sa_id.split("/") if p]
                    if "resourceGroups" in parts:
                        rg_index = parts.index("resourceGroups") + 1
                        if rg_index < len(parts):
                            found_rg = parts[rg_index]
                            break

            if found_rg is None:
                raise AzureMCPError(
                    "resource_group not provided and could not be inferred for storage account"
                )
            resource_group = found_rg

        keys = client.storage_accounts.list_keys(resource_group, account_name)

        key_value: Optional[str] = None
        if hasattr(keys, "keys") and keys.keys and len(keys.keys) > 0:
            first = keys.keys[0]
            if isinstance(first, dict) and "value" in first:
                key_value = cast(str, first["value"])
            elif hasattr(first, "value"):
                key_value = first.value
            elif hasattr(first, "key"):
                key_value = first.key

        if key_value is None:
            try:
                key_value = cast(str, keys.as_dict()["keys"][0]["value"])
            except Exception:
                raise AzureMCPError(
                    "Could not parse storage account keys from management client response"
                )

        account_url = f"https://{account_name}.blob.core.windows.net"
        named_key_cred = AzureNamedKeyCredential(account_name, key_value)
        blob_service = BlobServiceClient(
            account_url=account_url,
            credential=named_key_cred
        )

        container_client = blob_service.get_container_client(container_name)

        blob_names = []
        for blob in container_client.list_blobs(name_starts_with=name_starts_with):
            blob_names.append(blob.name)

        return {
            "success": True,
            "container_name": container_name,
            "account_name": account_name,
            "blob_count": len(blob_names),
            "blobs": blob_names
        }

    except AzureMCPError:
        raise
    except Exception as e:
        raise AzureMCPError(
            f"Failed to list blobs in container '{container_name}' in storage account '{account_name}': {e}"
        ) from e
