from typing import Optional, Dict, Any, Union, List, BinaryIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.fileshare import ShareServiceClient, ShareClient, ShareFileClient
from azure.storage.queue import QueueServiceClient, QueueClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError, ResourceExistsError
from azure.core.credentials import TokenCredential
from ..mgmt.logging import AzureLogger
from ..mgmt.identity import AzureIdentity
import io
from datetime import datetime, timedelta
import mimetypes
import chardet
from azure.storage.blob import (
    generate_blob_sas,
    generate_container_sas,
    ContentSettings,
    UserDelegationKey,
)


# Storage instance caching
_storage_instances: Dict[Any, "AzureStorage"] = {}


class AzureStorage:
    """Azure Storage Account management with comprehensive blob, file, and queue operations.

    Provides standardized Azure Storage operations using Azure SDK clients
    with integrated logging, error handling, and OpenTelemetry tracing support.
    Supports operations for blob storage, file shares, and queues with proper
    authentication and authorization handling. Container and queue creation
    is handled by infrastructure as code.

    Attributes:
        account_url: Azure Storage Account URL
        service_name: Service identifier for logging and tracing
        service_version: Service version for context
        logger: AzureLogger instance for structured logging
        credential: Azure credential for authentication
        blob_service_client: Azure Blob Service Client instance
        file_service_client: Azure File Share Service Client instance
        queue_service_client: Azure Queue Service Client instance
    """

    def __init__(
        self,
        account_url: str,
        credential: Optional[TokenCredential] = None,
        azure_identity: Optional[AzureIdentity] = None,
        account_key: Optional[str] = None,
        service_name: str = "azure_storage",
        service_version: str = "1.0.0",
        logger: Optional[AzureLogger] = None,
        connection_string: Optional[str] = None,
        enable_blob_storage: bool = True,
        enable_file_storage: bool = True,
        enable_queue_storage: bool = True,
    ):
        """Initialize Azure Storage with comprehensive configuration.

        Args:
            account_url: Azure Storage Account URL (e.g., https://account.blob.core.windows.net/)
            credential: Azure credential for authentication
            azure_identity: AzureIdentity instance for credential management
            account_key: Optional Azure Storage account key for SAS generation
            service_name: Service name for tracing context
            service_version: Service version for metadata
            logger: Optional AzureLogger instance
            connection_string: Application Insights connection string
            enable_blob_storage: Enable blob storage operations client
            enable_file_storage: Enable file storage operations client
            enable_queue_storage: Enable queue storage operations client

        Raises:
            ValueError: If neither credential nor azure_identity is provided
            Exception: If client initialization fails
        """
        self.account_url = account_url
        self.account_name = account_url.split(".")[0].split("//")[-1]
        self.account_key = account_key
        self.service_name = service_name
        self.service_version = service_version
        self.enable_blob_storage = enable_blob_storage
        self.enable_file_storage = enable_file_storage
        self.enable_queue_storage = enable_queue_storage

        # Initialize logger - use provided instance or create new one
        if logger is not None:
            self.logger = logger
        else:
            self.logger = AzureLogger(
                service_name=service_name,
                service_version=service_version,
                connection_string=connection_string,
                enable_console_logging=True,
            )

        # Setup credential
        if azure_identity is not None:
            self.credential = azure_identity.get_credential()
            self.azure_identity = azure_identity
        elif credential is not None:
            self.credential = credential
            self.azure_identity = None
        else:
            raise ValueError("Either 'credential' or 'azure_identity' must be provided")

        # Initialize clients
        self.blob_service_client = None
        self.file_service_client = None
        self.queue_service_client = None
        self.user_delegation_key: Optional[UserDelegationKey] = None
        
        self._setup_clients()

        self.logger.info(
            f"Azure Storage initialized for service '{service_name}' v{service_version}",
            extra={
                "account_url": account_url,
                "blob_enabled": enable_blob_storage,
                "file_enabled": enable_file_storage,
                "queue_enabled": enable_queue_storage,
            }
        )

    def _setup_clients(self):
        """Initialize Storage clients based on enabled features.

        Raises:
            Exception: If client initialization fails
        """
        try:
            if self.enable_blob_storage:
                self.blob_service_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=self.credential
                )
                self.logger.debug("BlobServiceClient initialized successfully")

                # If using token credential (RBAC), get a user delegation key for SAS generation
                if isinstance(self.credential, TokenCredential):
                    self._request_user_delegation_key()

            if self.enable_file_storage:
                # Convert blob URL to file URL
                file_url = self.account_url.replace('.blob.', '.file.')
                self.file_service_client = ShareServiceClient(
                    account_url=file_url,
                    credential=self.credential,
                    token_intent='backup'
                )
                self.logger.debug("ShareServiceClient initialized successfully")

            if self.enable_queue_storage:
                # Convert blob URL to queue URL
                queue_url = self.account_url.replace('.blob.', '.queue.')
                self.queue_service_client = QueueServiceClient(
                    account_url=queue_url,
                    credential=self.credential
                )
                self.logger.debug("QueueServiceClient initialized successfully")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize Storage clients: {e}",
                exc_info=True
            )
            raise

    def _request_user_delegation_key(self):
        """Request a user delegation key for generating user delegation SAS.
        The key is valid for 1 day.
        """
        if not self.blob_service_client:
            self.logger.warning("Blob service client not available. Cannot request user delegation key.")
            return
        
        try:
            self.logger.debug("Requesting user delegation key.")
            delegation_key_start_time = datetime.utcnow()
            delegation_key_expiry_time = delegation_key_start_time + timedelta(days=1)

            self.user_delegation_key = self.blob_service_client.get_user_delegation_key(
                key_start_time=delegation_key_start_time,
                key_expiry_time=delegation_key_expiry_time,
            )
            self.logger.info("Successfully obtained user delegation key.")
        except Exception as e:
            self.logger.error(f"Failed to get user delegation key: {e}", exc_info=True)
            # This is not a critical failure, SAS generation will fail later if key is needed.

    # Blob Storage Operations
    def upload_blob(
        self,
        container_name: str,
        blob_name: str,
        data: Union[bytes, str, BinaryIO],
        overwrite: bool = False,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Upload a blob to Azure Blob Storage. 
        If content_type is not provided, it will be inferred.

        Args:
            container_name: Name of the container
            blob_name: Name of the blob
            data: Data to upload (bytes, string, or file-like object)
            overwrite: Whether to overwrite existing blob
            metadata: Optional metadata for the blob
            content_type: Optional content type for the blob
            **kwargs: Additional parameters for blob upload

        Returns:
            True if blob was uploaded successfully

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If blob upload fails
        """
        with self.logger.create_span(
            "AzureStorage.upload_blob",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_upload",
                "storage.container_name": container_name,
                "storage.blob_name": blob_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Uploading blob to Azure Storage",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name,
                        "overwrite": overwrite,
                        "has_metadata": metadata is not None,
                        "content_type": content_type
                    }
                )

                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name,
                )
                
                if isinstance(data, str):
                    data = data.encode('utf-8')

                content_settings = None
                if content_type:
                    content_settings = ContentSettings(content_type=content_type)
                elif isinstance(data, bytes):
                    # Guess content type if not provided and data is bytes
                    guessed_type = mimetypes.MimeTypes().guess_type(blob_name)[0]
                    if guessed_type:
                        charset = ""
                        if "text" in guessed_type:
                            charset = f"; charset={chardet.detect(data)['encoding']}"
                        content_settings = ContentSettings(content_type=guessed_type + charset)

                kwargs['content_settings'] = content_settings

                blob_client.upload_blob(
                    data,
                    overwrite=overwrite,
                    metadata=metadata,
                    **kwargs
                )
                
                self.logger.info(
                    "Blob uploaded successfully",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name,
                        "overwrite": overwrite
                    }
                )
                
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to upload blob '{blob_name}': {e}",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    },
                    exc_info=True
                )
                raise

    def download_blob_by_url(
        self,
        blob_url: str,
        credential: Optional[TokenCredential] = None,
        **kwargs
    ) -> Optional[bytes]:
        """Download a blob directly by URL using specified credentials.

        Args:
            blob_url: Full URL to the blob (e.g., https://account.blob.core.windows.net/container/blob)
            credential: Azure credential for authentication (if None, uses instance credential)
            **kwargs: Additional parameters for blob download

        Returns:
            Blob data as bytes if found, None if not found

        Raises:
            ValueError: If blob URL is invalid or no credential available
            Exception: If blob download fails for reasons other than not found
        """
        with self.logger.create_span(
            "AzureStorage.download_blob_by_url",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_download_by_url",
                "storage.blob_url": blob_url
            }
        ):
            try:
                self.logger.debug(
                    "Downloading blob by URL",
                    extra={"blob_url": blob_url}
                )

                # Use provided credential or fall back to instance credential
                download_credential = credential if credential is not None else self.credential

                if download_credential is None:
                    raise ValueError("No credential available for blob download")

                # Create blob client directly from URL
                blob_client = BlobClient.from_blob_url(
                    blob_url=blob_url,
                    credential=download_credential
                )

                blob_data = blob_client.download_blob(**kwargs)
                content = blob_data.readall()

                self.logger.info(
                    "Blob downloaded successfully by URL",
                    extra={
                        "blob_url": blob_url,
                        "content_length": len(content) if content else 0
                    }
                )

                return content

            except ResourceNotFoundError:
                self.logger.warning(
                    f"Blob not found at URL: {blob_url}",
                    extra={"blob_url": blob_url}
                )
                return None
            except Exception as e:
                self.logger.error(
                    f"Failed to download blob by URL '{blob_url}': {e}",
                    extra={"blob_url": blob_url},
                    exc_info=True
                )
                raise

    def download_blob(
        self,
        container_name: str,
        blob_name: str,
        **kwargs
    ) -> Optional[bytes]:
        """Download a blob from Azure Blob Storage.

        Args:
            container_name: Name of the container
            blob_name: Name of the blob
            **kwargs: Additional parameters for blob download

        Returns:
            Blob data as bytes if found, None if not found

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If blob download fails for reasons other than not found
        """
        with self.logger.create_span(
            "AzureStorage.download_blob",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_download",
                "storage.container_name": container_name,
                "storage.blob_name": blob_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Downloading blob from Azure Storage",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    }
                )

                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )

                blob_data = blob_client.download_blob(**kwargs)
                content = blob_data.readall()
                
                self.logger.info(
                    "Blob downloaded successfully",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name,
                        "content_length": len(content) if content else 0
                    }
                )
                
                return content

            except ResourceNotFoundError:
                self.logger.warning(
                    f"Blob '{blob_name}' not found in container '{container_name}'",
                    extra={"container_name": container_name, "blob_name": blob_name}
                )
                return None
            except Exception as e:
                self.logger.error(
                    f"Failed to download blob '{blob_name}': {e}",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    },
                    exc_info=True
                )
                raise

    def delete_blob(
        self,
        container_name: str,
        blob_name: str,
        **kwargs
    ) -> bool:
        """Delete a blob from Azure Blob Storage.

        Args:
            container_name: Name of the container
            blob_name: Name of the blob to delete
            **kwargs: Additional parameters for blob deletion

        Returns:
            True if blob was deleted successfully

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If blob deletion fails
        """
        with self.logger.create_span(
            "AzureStorage.delete_blob",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_deletion",
                "storage.container_name": container_name,
                "storage.blob_name": blob_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Deleting blob from Azure Storage",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    }
                )

                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )

                blob_client.delete_blob(**kwargs)
                
                self.logger.info(
                    "Blob deleted successfully",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    }
                )
                
                return True

            except ResourceNotFoundError:
                self.logger.warning(
                    f"Blob '{blob_name}' not found in container '{container_name}' for deletion",
                    extra={"container_name": container_name, "blob_name": blob_name}
                )
                return False
            except Exception as e:
                self.logger.error(
                    f"Failed to delete blob '{blob_name}': {e}",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    },
                    exc_info=True
                )
                raise

    def list_blobs(
        self,
        container_name: str,
        name_starts_with: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """List blobs in a container.

        Args:
            container_name: Name of the container
            name_starts_with: Optional prefix to filter blob names
            **kwargs: Additional parameters for listing blobs

        Returns:
            List of blob names

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If listing blobs fails
        """
        with self.logger.create_span(
            "AzureStorage.list_blobs",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_listing",
                "storage.container_name": container_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Listing blobs from Azure Storage",
                    extra={
                        "container_name": container_name,
                        "name_starts_with": name_starts_with
                    }
                )

                container_client = self.blob_service_client.get_container_client(container_name)
                
                blob_names = []
                for blob in container_client.list_blobs(
                    name_starts_with=name_starts_with,
                    **kwargs
                ):
                    blob_names.append(blob.name)
                
                self.logger.info(
                    "Blobs listed successfully",
                    extra={
                        "container_name": container_name,
                        "blob_count": len(blob_names)
                    }
                )
                
                return blob_names

            except Exception as e:
                self.logger.error(
                    f"Failed to list blobs in container '{container_name}': {e}",
                    extra={"container_name": container_name},
                    exc_info=True
                )
                raise

    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if a blob exists in a container.

        Args:
            container_name: Name of the container
            blob_name: Name of the blob

        Returns:
            True if the blob exists, False otherwise

        Raises:
            RuntimeError: If blob service client is not initialized
        """
        if self.blob_service_client is None:
            error_msg = "Blob service client not initialized. Enable blob storage during initialization."
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        with self.logger.create_span(
            "AzureStorage.blob_exists",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_exists",
                "storage.container_name": container_name,
                "storage.blob_name": blob_name,
                "storage.account_url": self.account_url,
            },
        ):
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name, blob=blob_name
                )
                exists = blob_client.exists()
                self.logger.debug(f"Blob '{blob_name}' exists: {exists}")
                return exists
            except Exception as e:
                self.logger.error(
                    f"Failed to check existence for blob '{blob_name}': {e}",
                    extra={"container_name": container_name, "blob_name": blob_name},
                    exc_info=True,
                )
                raise

    def delete_blobs(
        self,
        container_name: str,
        blob_names: Union[List[str], Dict[str, Any]],
        integrated_vectorization: bool = False,
        **kwargs
    ) -> Dict[str, bool]:
        """Delete multiple blobs from Azure Blob Storage efficiently.

        Args:
            container_name: Name of the container
            blob_names: List of blob names or dict with filenames as keys
            integrated_vectorization: If True, use full paths; if False, extract filename from path
            **kwargs: Additional parameters for blob deletion

        Returns:
            Dictionary mapping blob names to deletion success status

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If batch deletion fails
        """
        with self.logger.create_span(
            "AzureStorage.delete_blobs",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_batch_deletion",
                "storage.container_name": container_name,
                "storage.account_url": self.account_url,
                "storage.blob_count": len(blob_names)
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Batch deleting blobs from Azure Storage",
                    extra={
                        "container_name": container_name,
                        "blob_count": len(blob_names),
                        "integrated_vectorization": integrated_vectorization
                    }
                )

                results = {}
                
                # Handle dict input (filename -> ids mapping)
                if isinstance(blob_names, dict):
                    filenames = list(blob_names.keys())
                else:
                    filenames = blob_names

                for filename in filenames:
                    try:
                        # Extract just the filename if not using integrated vectorization
                        blob_name = filename if integrated_vectorization else filename.split("/")[-1]
                        
                        blob_client = self.blob_service_client.get_blob_client(
                            container=container_name,
                            blob=blob_name
                        )
                        
                        # Check if blob exists before attempting deletion
                        if blob_client.exists():
                            blob_client.delete_blob(**kwargs)
                            results[filename] = True
                            self.logger.debug(f"Successfully deleted blob: {blob_name}")
                        else:
                            results[filename] = False
                            self.logger.warning(f"Blob not found for deletion: {blob_name}")
                            
                    except Exception as e:
                        results[filename] = False
                        self.logger.error(
                            f"Failed to delete blob '{filename}': {e}",
                            extra={"container_name": container_name, "blob_name": filename},
                            exc_info=True
                        )

                successful_deletions = sum(1 for success in results.values() if success)
                self.logger.info(
                    "Batch blob deletion completed",
                    extra={
                        "container_name": container_name,
                        "total_blobs": len(blob_names),
                        "successful_deletions": successful_deletions,
                        "failed_deletions": len(blob_names) - successful_deletions
                    }
                )
                
                return results

            except Exception as e:
                self.logger.error(
                    f"Failed to batch delete blobs in container '{container_name}': {e}",
                    extra={"container_name": container_name},
                    exc_info=True
                )
                raise

    def list_blobs_with_metadata(
        self,
        container_name: str,
        name_starts_with: Optional[str] = None,
        include_sas: bool = True,
        sas_expiry_delta: timedelta = timedelta(hours=3),
        converted_prefix: str = "converted/",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """List blobs with comprehensive metadata and optional SAS URLs.

        Args:
            container_name: Name of the container
            name_starts_with: Optional prefix to filter blob names
            include_sas: Whether to include SAS URLs for each blob
            sas_expiry_delta: Timedelta for SAS URL validity
            converted_prefix: Prefix used for converted files
            **kwargs: Additional parameters for listing blobs

        Returns:
            List of dictionaries containing blob information with metadata

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If listing blobs fails
        """
        with self.logger.create_span(
            "AzureStorage.list_blobs_with_metadata",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_listing_enhanced",
                "storage.container_name": container_name,
                "storage.account_url": self.account_url,
                "storage.include_sas": include_sas
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Listing blobs with metadata from Azure Storage",
                    extra={
                        "container_name": container_name,
                        "name_starts_with": name_starts_with,
                        "include_sas": include_sas
                    }
                )

                container_client = self.blob_service_client.get_container_client(container_name)
                
                # Get container SAS if needed
                container_sas = ""
                if include_sas:
                    try:
                        container_sas = self.get_container_sas(
                            container_name=container_name,
                            permission="r",
                            expiry_delta=sas_expiry_delta
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to generate container SAS: {e}")
                        include_sas = False

                files = []
                converted_files = {}
                
                # List all blobs with metadata
                for blob in container_client.list_blobs(
                    name_starts_with=name_starts_with,
                    include=["metadata"],
                    **kwargs
                ):
                    blob_info = {
                        "filename": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified,
                        "etag": blob.etag,
                        "content_type": getattr(blob, "content_settings", {}).get("content_type") if hasattr(blob, "content_settings") else None,
                        "metadata": blob.metadata or {},
                    }
                    
                    # Add SAS URL if requested
                    if include_sas and container_sas:
                        blob_info["fullpath"] = f"{self.account_url}{container_name}/{blob.name}?{container_sas}"
                    else:
                        blob_info["fullpath"] = f"{self.account_url}{container_name}/{blob.name}"
                    
                    # Process converted status from metadata
                    if blob.metadata:
                        blob_info["converted"] = blob.metadata.get("converted", "false") == "true"
                        blob_info["embeddings_added"] = blob.metadata.get("embeddings_added", "false") == "true"
                        blob_info["converted_filename"] = blob.metadata.get("converted_filename", "")
                    else:
                        blob_info["converted"] = False
                        blob_info["embeddings_added"] = False
                        blob_info["converted_filename"] = ""
                    
                    # Separate converted files from regular files
                    if not blob.name.startswith(converted_prefix):
                        blob_info["converted_path"] = ""
                        files.append(blob_info)
                    else:
                        converted_files[blob.name] = blob_info["fullpath"]

                # Link converted files to their originals
                for file_info in files:
                    converted_filename = file_info.get("converted_filename", "")
                    if converted_filename and converted_filename in converted_files:
                        file_info["converted"] = True
                        file_info["converted_path"] = converted_files[converted_filename]
                    
                    # Remove internal converted_filename from final output
                    file_info.pop("converted_filename", None)

                self.logger.info(
                    "Blobs listed with metadata successfully",
                    extra={
                        "container_name": container_name,
                        "blob_count": len(files),
                        "converted_files_count": len(converted_files),
                        "include_sas": include_sas
                    }
                )
                
                return files

            except Exception as e:
                self.logger.error(
                    f"Failed to list blobs with metadata in container '{container_name}': {e}",
                    extra={"container_name": container_name},
                    exc_info=True
                )
                raise

    def get_blob_properties(self, container_name: str, blob_name: str):
        """Get properties of a specific blob."""
        if self.blob_service_client is None:
            raise RuntimeError("Blob service client not initialized.")
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            return blob_client.get_blob_properties()
        except ResourceNotFoundError:
            self.logger.warning(f"Blob '{blob_name}' not found in container '{container_name}'.")
            return None
        except Exception as e:
            self.logger.error(
                f"Failed to get properties for blob '{blob_name}': {e}",
                exc_info=True,
            )
            raise

    def get_blob_properties_by_url(
        self,
        blob_url: str,
        credential: Optional[TokenCredential] = None,
        **kwargs
    ):
        """Get properties of a specific blob using its URL.

        Args:
            blob_url: Full URL to the blob (e.g., https://account.blob.core.windows.net/container/blob)
            credential: Azure credential for authentication (if None, uses instance credential)
            **kwargs: Additional parameters for blob property retrieval

        Returns:
            Blob properties if found, None if not found

        Raises:
            ValueError: If blob URL is invalid or no credential available
            Exception: If getting blob properties fails for reasons other than not found

        Example:
            ```python
            storage = AzureStorage(account_url="https://account.blob.core.windows.net/")
            url = "https://stdatarpcdev.blob.core.windows.net/documents/1-document-2025-09-18 07:40:41.333584.json"
            properties = storage.get_blob_properties_by_url(url)
            if properties:
                print(f"Blob size: {properties.size}")
                print(f"Last modified: {properties.last_modified}")
            ```
        """
        with self.logger.create_span(
            "AzureStorage.get_blob_properties_by_url",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_properties_by_url",
                "storage.blob_url": blob_url
            }
        ):
            try:
                self.logger.debug(
                    "Getting blob properties by URL",
                    extra={"blob_url": blob_url}
                )

                # Use provided credential or fall back to instance credential
                properties_credential = credential if credential is not None else self.credential

                if properties_credential is None:
                    raise ValueError("No credential available for blob properties retrieval")

                # Create blob client directly from URL
                blob_client = BlobClient.from_blob_url(
                    blob_url=blob_url,
                    credential=properties_credential
                )

                properties = blob_client.get_blob_properties(**kwargs)

                self.logger.info(
                    "Blob properties retrieved successfully by URL",
                    extra={
                        "blob_url": blob_url,
                        "blob_size": getattr(properties, 'size', 0),
                        "last_modified": getattr(properties, 'last_modified', None)
                    }
                )

                return properties

            except ResourceNotFoundError:
                self.logger.warning(
                    f"Blob not found at URL: {blob_url}",
                    extra={"blob_url": blob_url}
                )
                return None
            except Exception as e:
                self.logger.error(
                    f"Failed to get blob properties by URL '{blob_url}': {e}",
                    extra={"blob_url": blob_url},
                    exc_info=True
                )
                raise

    def upload_blob_with_sas(
        self,
        container_name: str,
        blob_name: str,
        data: Union[bytes, str, BinaryIO],
        overwrite: bool = True,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        sas_permission: str = "r",
        sas_expiry_delta: timedelta = timedelta(hours=3),
        **kwargs
    ) -> str:
        """Upload a blob and return its SAS URL.

        Args:
            container_name: Name of the container
            blob_name: Name of the blob
            data: Data to upload (bytes, string, or file-like object)
            overwrite: Whether to overwrite existing blob
            metadata: Optional metadata for the blob
            content_type: Optional content type for the blob
            sas_permission: SAS permissions for the generated URL
            sas_expiry_delta: Timedelta for SAS URL validity
            **kwargs: Additional parameters for blob upload

        Returns:
            Full blob URL with SAS token

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If blob upload or SAS generation fails
        """
        with self.logger.create_span(
            "AzureStorage.upload_blob_with_sas",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_upload_with_sas",
                "storage.container_name": container_name,
                "storage.blob_name": blob_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Uploading blob with SAS URL generation",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name,
                        "overwrite": overwrite,
                        "has_metadata": metadata is not None,
                        "content_type": content_type,
                        "sas_permission": sas_permission
                    }
                )

                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )
                
                # Handle content type detection similar to original logic
                content_settings = None
                if content_type:
                    content_settings = ContentSettings(content_type=content_type)
                elif isinstance(data, bytes):
                    # Guess content type if not provided and data is bytes
                    guessed_type = mimetypes.MimeTypes().guess_type(blob_name)[0]
                    if guessed_type:
                        charset = ""
                        if guessed_type == "text/plain":
                            detected_encoding = chardet.detect(data).get('encoding', 'utf-8')
                            charset = f"; charset={detected_encoding}"
                        final_content_type = guessed_type + charset
                        content_settings = ContentSettings(content_type=final_content_type)
                    else:
                        content_settings = ContentSettings(content_type="text/plain")

                kwargs['content_settings'] = content_settings

                # Upload the blob
                blob_client.upload_blob(
                    data,
                    overwrite=overwrite,
                    metadata=metadata,
                    **kwargs
                )
                
                # Generate SAS URL
                sas_url = self.get_blob_sas(
                    container_name=container_name,
                    blob_name=blob_name,
                    permission=sas_permission,
                    expiry_delta=sas_expiry_delta
                )
                
                self.logger.info(
                    "Blob uploaded with SAS URL generated successfully",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name,
                        "overwrite": overwrite,
                        "sas_permission": sas_permission
                    }
                )
                
                return sas_url

            except Exception as e:
                self.logger.error(
                    f"Failed to upload blob '{blob_name}' with SAS: {e}",
                    extra={
                        "container_name": container_name,
                        "blob_name": blob_name
                    },
                    exc_info=True
                )
                raise

    def upsert_blob_metadata(self, container_name: str, blob_name: str, metadata: Dict[str, str]):
        """Update or insert metadata for a specific blob.

        Args:
            container_name: The name of the container.
            blob_name: The name of the blob.
            metadata: A dictionary of metadata to upsert.

        Raises:
            RuntimeError: If blob service client is not initialized.
            Exception: If updating metadata fails.
        """
        with self.logger.create_span(
            "AzureStorage.upsert_blob_metadata",
            attributes={
                "service.name": self.service_name,
                "operation.type": "blob_metadata_upsert",
                "storage.container_name": container_name,
                "storage.blob_name": blob_name,
                "storage.account_url": self.account_url,
            },
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name, blob=blob_name
                )
                
                # Fetch existing metadata to avoid overwriting
                blob_properties = blob_client.get_blob_properties()
                existing_metadata = blob_properties.metadata
                
                # Update with new metadata
                existing_metadata.update(metadata)
                
                blob_client.set_blob_metadata(metadata=existing_metadata)
                self.logger.info(f"Successfully upserted metadata for blob '{blob_name}'.")

            except Exception as e:
                self.logger.error(
                    f"Failed to upsert metadata for blob '{blob_name}': {e}",
                    extra={"container_name": container_name, "blob_name": blob_name},
                    exc_info=True,
                )
                raise

    # Queue Operations
    def send_message(
        self,
        queue_name: str,
        content: str,
        visibility_timeout: Optional[int] = None,
        time_to_live: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Send a message to an Azure Storage Queue.

        Args:
            queue_name: Name of the queue
            content: Message content
            visibility_timeout: Optional visibility timeout in seconds
            time_to_live: Optional time to live in seconds
            **kwargs: Additional parameters for message sending

        Returns:
            True if message was sent successfully

        Raises:
            RuntimeError: If queue service client is not initialized
            Exception: If message sending fails
        """
        with self.logger.create_span(
            "AzureStorage.send_message",
            attributes={
                "service.name": self.service_name,
                "operation.type": "queue_send_message",
                "storage.queue_name": queue_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.queue_service_client is None:
                error_msg = "Queue service client not initialized. Enable queue storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Sending message to Azure Storage Queue",
                    extra={
                        "queue_name": queue_name,
                        "message_length": len(content),
                        "visibility_timeout": visibility_timeout,
                        "time_to_live": time_to_live
                    }
                )

                queue_client = self.queue_service_client.get_queue_client(queue_name)
                
                queue_client.send_message(
                    content=content,
                    visibility_timeout=visibility_timeout,
                    time_to_live=time_to_live,
                    **kwargs
                )
                
                self.logger.info(
                    "Message sent successfully",
                    extra={"queue_name": queue_name}
                )
                
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to send message to queue '{queue_name}': {e}",
                    extra={"queue_name": queue_name},
                    exc_info=True
                )
                raise

    def receive_messages(
        self,
        queue_name: str,
        messages_per_page: int = 1,
        visibility_timeout: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Receive messages from an Azure Storage Queue.

        Args:
            queue_name: Name of the queue
            messages_per_page: Number of messages to receive per page
            visibility_timeout: Optional visibility timeout in seconds
            **kwargs: Additional parameters for message receiving

        Returns:
            List of message dictionaries containing message data

        Raises:
            RuntimeError: If queue service client is not initialized
            Exception: If message receiving fails
        """
        with self.logger.create_span(
            "AzureStorage.receive_messages",
            attributes={
                "service.name": self.service_name,
                "operation.type": "queue_receive_messages",
                "storage.queue_name": queue_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.queue_service_client is None:
                error_msg = "Queue service client not initialized. Enable queue storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Receiving messages from Azure Storage Queue",
                    extra={
                        "queue_name": queue_name,
                        "messages_per_page": messages_per_page,
                        "visibility_timeout": visibility_timeout
                    }
                )

                queue_client = self.queue_service_client.get_queue_client(queue_name)
                
                messages = []
                for message_page in queue_client.receive_messages(
                    messages_per_page=messages_per_page,
                    visibility_timeout=visibility_timeout,
                    **kwargs
                ):
                    for message in message_page:
                        messages.append({
                            "id": message.id,
                            "content": message.content,
                            "dequeue_count": message.dequeue_count,
                            "insertion_time": message.insertion_time,
                            "expiration_time": message.expiration_time,
                            "pop_receipt": message.pop_receipt
                        })
                
                self.logger.info(
                    "Messages received successfully",
                    extra={
                        "queue_name": queue_name,
                        "message_count": len(messages)
                    }
                )
                
                return messages

            except Exception as e:
                self.logger.error(
                    f"Failed to receive messages from queue '{queue_name}': {e}",
                    extra={"queue_name": queue_name},
                    exc_info=True
                )
                raise

    def delete_message(
        self,
        queue_name: str,
        message_id: str,
        pop_receipt: str,
        **kwargs
    ) -> bool:
        """Delete a message from an Azure Storage Queue.

        Args:
            queue_name: Name of the queue
            message_id: ID of the message to delete
            pop_receipt: Pop receipt of the message
            **kwargs: Additional parameters for message deletion

        Returns:
            True if message was deleted successfully

        Raises:
            RuntimeError: If queue service client is not initialized
            Exception: If message deletion fails
        """
        with self.logger.create_span(
            "AzureStorage.delete_message",
            attributes={
                "service.name": self.service_name,
                "operation.type": "queue_delete_message",
                "storage.queue_name": queue_name,
                "storage.message_id": message_id,
                "storage.account_url": self.account_url
            }
        ):
            if self.queue_service_client is None:
                error_msg = "Queue service client not initialized. Enable queue storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Deleting message from Azure Storage Queue",
                    extra={
                        "queue_name": queue_name,
                        "message_id": message_id
                    }
                )

                queue_client = self.queue_service_client.get_queue_client(queue_name)
                
                queue_client.delete_message(
                    message=message_id,
                    pop_receipt=pop_receipt,
                    **kwargs
                )
                
                self.logger.info(
                    "Message deleted successfully",
                    extra={
                        "queue_name": queue_name,
                        "message_id": message_id
                    }
                )
                
                return True

            except Exception as e:
                self.logger.error(
                    f"Failed to delete message '{message_id}' from queue '{queue_name}': {e}",
                    extra={
                        "queue_name": queue_name,
                        "message_id": message_id
                    },
                    exc_info=True
                )
                raise

    def test_connection(self) -> bool:
        """Test connection to Azure Storage by attempting to list containers.

        Returns:
            True if connection is successful, False otherwise
        """
        with self.logger.create_span(
            "AzureStorage.test_connection",
            attributes={
                "service.name": self.service_name,
                "operation.type": "connection_test",
                "storage.account_url": self.account_url
            }
        ):
            try:
                self.logger.debug(
                    "Testing Azure Storage connection",
                    extra={"account_url": self.account_url}
                )

                if self.blob_service_client is not None:
                    # Try to list containers (limited to 1) to test connection
                    list(self.blob_service_client.list_containers(results_per_page=1))
                elif self.queue_service_client is not None:
                    # Try to list queues if blob storage is disabled
                    list(self.queue_service_client.list_queues(results_per_page=1))
                elif self.file_service_client is not None:
                    # Try to list shares if queues are disabled
                    list(self.file_service_client.list_shares(results_per_page=1))
                else:
                    self.logger.error("No clients available for connection testing")
                    return False

                self.logger.info("Azure Storage connection test successful")
                return True

            except Exception as e:
                self.logger.warning(
                    f"Azure Storage connection test failed: {e}",
                    extra={"account_url": self.account_url}
                )
                return False

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request/transaction tracking.

        Args:
            correlation_id: Unique identifier for transaction correlation
        """
        self.logger.set_correlation_id(correlation_id)

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID.

        Returns:
            Current correlation ID if set, otherwise None
        """
        return self.logger.get_correlation_id()

    # SAS Generation
    def get_container_sas(
        self,
        container_name: str,
        permission: str = "r",
        expiry_delta: timedelta = timedelta(hours=1),
    ) -> str:
        """Generate a SAS token for a container.

        Args:
            container_name: Name of the container.
            permission: SAS permissions (e.g., 'r' for read, 'w' for write).
            expiry_delta: Timedelta for how long the SAS is valid.

        Returns:
            The SAS token string.

        Raises:
            ValueError: If no valid credential (user delegation key or account key) is available.
        """
        with self.logger.create_span("AzureStorage.get_container_sas"):
            expiry_time = datetime.utcnow() + expiry_delta
            if self.user_delegation_key:
                self.logger.debug("Generating container SAS with user delegation key.")
                return generate_container_sas(
                    account_name=self.account_name,
                    container_name=container_name,
                    user_delegation_key=self.user_delegation_key,
                    permission=permission,
                    expiry=expiry_time,
                )
            elif self.account_key:
                self.logger.debug("Generating container SAS with account key.")
                return generate_container_sas(
                    account_name=self.account_name,
                    container_name=container_name,
                    account_key=self.account_key,
                    permission=permission,
                    expiry=expiry_time,
                )
            else:
                raise ValueError("Cannot generate SAS token. No user delegation key or account key is configured.")

    def get_blob_sas(
        self,
        container_name: str,
        blob_name: str,
        permission: str = "r",
        expiry_delta: timedelta = timedelta(hours=1),
    ) -> str:
        """Generate a SAS URL for a blob.

        Args:
            container_name: Name of the container.
            blob_name: Name of the blob.
            permission: SAS permissions.
            expiry_delta: Timedelta for how long the SAS is valid.

        Returns:
            The full blob URL with SAS token.
            
        Raises:
            ValueError: If no valid credential (user delegation key or account key) is available.
        """
        with self.logger.create_span("AzureStorage.get_blob_sas"):
            expiry_time = datetime.utcnow() + expiry_delta
            sas_token = ""
            if self.user_delegation_key:
                self.logger.debug("Generating blob SAS with user delegation key.")
                sas_token = generate_blob_sas(
                    account_name=self.account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    user_delegation_key=self.user_delegation_key,
                    permission=permission,
                    expiry=expiry_time,
                )
            elif self.account_key:
                self.logger.debug("Generating blob SAS with account key.")
                sas_token = generate_blob_sas(
                    account_name=self.account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    account_key=self.account_key,
                    permission=permission,
                    expiry=expiry_time,
                )
            else:
                raise ValueError("Cannot generate SAS token. No user delegation key or account key is configured.")
            
            return f"{self.account_url}{container_name}/{blob_name}?{sas_token}"

    def get_all_files(
        self,
        container_name: str,
        sas_expiry_delta: timedelta = timedelta(hours=3)
    ) -> List[Dict[str, Any]]:
        """Get all files in container with metadata and SAS URLs.
        
        This method provides the same interface as the original AzureBlobStorageClient.get_all_files()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            sas_expiry_delta: Timedelta for SAS URL validity (default 3 hours)

        Returns:
            List of file dictionaries with structure:
            {
                "filename": str,
                "converted": bool,
                "embeddings_added": bool,
                "fullpath": str,  # URL with SAS token
                "converted_path": str  # URL to converted file if available
            }

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If listing files fails
        """
        with self.logger.create_span(
            "AzureStorage.get_all_files",
            attributes={
                "service.name": self.service_name,
                "operation.type": "get_all_files",
                "storage.container_name": container_name,
                "storage.account_url": self.account_url
            }
        ):
            if self.blob_service_client is None:
                error_msg = "Blob service client not initialized. Enable blob storage during initialization."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            try:
                self.logger.debug(
                    "Getting all files from Azure Storage container",
                    extra={
                        "container_name": container_name,
                        "sas_expiry_delta": str(sas_expiry_delta)
                    }
                )

                container_client = self.blob_service_client.get_container_client(container_name)
                
                # Generate container SAS with same expiry as original (3 hours default)
                container_sas = self.get_container_sas(
                    container_name=container_name,
                    permission="r",
                    expiry_delta=sas_expiry_delta
                )

                files = []
                converted_files = {}
                
                # List all blobs with metadata
                for blob in container_client.list_blobs(include=["metadata"]):
                    blob_url = f"{self.account_url}{container_name}/{blob.name}?{container_sas}"
                    
                    if not blob.name.startswith("converted/"):
                        # Regular file
                        file_entry = {
                            "filename": blob.name,
                            "converted": (
                                blob.metadata.get("converted", "false") == "true"
                                if blob.metadata
                                else False
                            ),
                            "embeddings_added": (
                                blob.metadata.get("embeddings_added", "false") == "true"
                                if blob.metadata
                                else False
                            ),
                            "fullpath": blob_url,
                            "converted_filename": (
                                blob.metadata.get("converted_filename", "")
                                if blob.metadata
                                else ""
                            ),
                            "converted_path": "",
                        }
                        files.append(file_entry)
                    else:
                        # Converted file - store for linking
                        converted_files[blob.name] = blob_url

                # Link converted files to their originals
                for file_entry in files:
                    converted_filename = file_entry.pop("converted_filename", "")
                    if converted_filename and converted_filename in converted_files:
                        file_entry["converted"] = True
                        file_entry["converted_path"] = converted_files[converted_filename]

                self.logger.info(
                    "All files retrieved successfully",
                    extra={
                        "container_name": container_name,
                        "file_count": len(files)
                    }
                )

                return files

            except Exception as e:
                self.logger.error(
                    f"Failed to get all files from container '{container_name}': {e}",
                    extra={"container_name": container_name},
                    exc_info=True
                )
                raise

    def delete_files(
        self,
        container_name: str,
        files: Dict[str, Any],
        integrated_vectorization: bool = False
    ) -> None:
        """Delete files from Azure Blob Storage container.
        
        This method provides the same interface as the original AzureBlobStorageClient.delete_files()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            files: Dictionary with filenames as keys (values are typically IDs but ignored)
            integrated_vectorization: If True, use full paths; if False, extract filename from path

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If file deletion fails
        """
        with self.logger.create_span(
            "AzureStorage.delete_files",
            attributes={
                "service.name": self.service_name,
                "operation.type": "delete_files",
                "storage.container_name": container_name,
                "storage.account_url": self.account_url,
                "storage.file_count": len(files)
            }
        ):
            try:
                self.logger.debug(
                    "Deleting files from Azure Storage container",
                    extra={
                        "container_name": container_name,
                        "file_count": len(files),
                        "integrated_vectorization": integrated_vectorization
                    }
                )

                # Use the batch delete method
                results = self.delete_blobs(
                    container_name=container_name,
                    blob_names=files,
                    integrated_vectorization=integrated_vectorization
                )

                # Log summary of results
                successful_count = sum(1 for success in results.values() if success)
                failed_count = len(files) - successful_count

                if failed_count > 0:
                    failed_files = [filename for filename, success in results.items() if not success]
                    self.logger.warning(
                        f"Some files failed to delete: {failed_files}",
                        extra={
                            "container_name": container_name,
                            "failed_files": failed_files,
                            "failed_count": failed_count
                        }
                    )

                self.logger.info(
                    "File deletion completed",
                    extra={
                        "container_name": container_name,
                        "successful_deletions": successful_count,
                        "failed_deletions": failed_count
                    }
                )

            except Exception as e:
                self.logger.error(
                    f"Failed to delete files from container '{container_name}': {e}",
                    extra={"container_name": container_name},
                    exc_info=True
                )
                raise

    def file_exists(self, container_name: str, file_name: str) -> bool:
        """Check if a file exists in the container.
        
        This method provides the same interface as the original AzureBlobStorageClient.file_exists()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            file_name: Name of the file to check

        Returns:
            True if the file exists, False otherwise

        Raises:
            RuntimeError: If blob service client is not initialized
        """
        return self.blob_exists(container_name=container_name, blob_name=file_name)

    def upload_file(
        self,
        container_name: str,
        bytes_data: Union[bytes, str, BinaryIO],
        file_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        sas_expiry_delta: timedelta = timedelta(hours=3)
    ) -> str:
        """Upload a file and return its SAS URL.
        
        This method provides the same interface as the original AzureBlobStorageClient.upload_file()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            bytes_data: Data to upload
            file_name: Name of the file
            content_type: Optional content type
            metadata: Optional metadata
            sas_expiry_delta: SAS URL validity period

        Returns:
            Full blob URL with SAS token

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If upload or SAS generation fails
        """
        return self.upload_blob_with_sas(
            container_name=container_name,
            blob_name=file_name,
            data=bytes_data,
            overwrite=True,
            metadata=metadata,
            content_type=content_type,
            sas_permission="r",
            sas_expiry_delta=sas_expiry_delta
        )

    def download_file(self, container_name: str, file_name: str) -> Optional[bytes]:
        """Download a file from the container.
        
        This method provides the same interface as the original AzureBlobStorageClient.download_file()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            file_name: Name of the file to download

        Returns:
            File data as bytes if found, None if not found

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If download fails for reasons other than not found
        """
        return self.download_blob(container_name=container_name, blob_name=file_name)

    def delete_file(self, container_name: str, file_name: str) -> bool:
        """Delete a single file from the container.
        
        This method provides the same interface as the original AzureBlobStorageClient.delete_file()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            file_name: Name of the file to delete

        Returns:
            True if file was deleted successfully

        Raises:
            RuntimeError: If blob service client is not initialized
        """
        return self.delete_blob(container_name=container_name, blob_name=file_name)

    def get_container_sas_with_prefix(
        self,
        container_name: str,
        permission: str = "r",
        expiry_delta: timedelta = timedelta(days=365 * 5)
    ) -> str:
        """Generate a SAS token for a container with question mark prefix.
        
        This method provides the same interface as the original AzureBlobStorageClient.get_container_sas()
        method which returns a SAS token with a leading question mark and 5-year default expiry.

        Args:
            container_name: Name of the container
            permission: SAS permissions (default 'r' for read)
            expiry_delta: Timedelta for SAS validity (default 5 years)

        Returns:
            SAS token string with leading question mark

        Raises:
            ValueError: If no valid credential is available for SAS generation
        """
        sas_token = self.get_container_sas(
            container_name=container_name,
            permission=permission,
            expiry_delta=expiry_delta
        )
        return f"?{sas_token}"

    def upsert_file_metadata(
        self,
        container_name: str,
        file_name: str,
        metadata: Dict[str, str]
    ) -> None:
        """Update or insert metadata for a specific file.
        
        This method provides the same interface as the original AzureBlobStorageClient.upsert_blob_metadata()
        method for non-breaking compatibility.

        Args:
            container_name: Name of the container
            file_name: Name of the file
            metadata: Dictionary of metadata to upsert

        Raises:
            RuntimeError: If blob service client is not initialized
            Exception: If updating metadata fails
        """
        self.upsert_blob_metadata(
            container_name=container_name,
            blob_name=file_name,
            metadata=metadata
        )


def create_azure_storage(
    account_url: str,
    credential: Optional[TokenCredential] = None,
    azure_identity: Optional[AzureIdentity] = None,
    account_key: Optional[str] = None,
    service_name: str = "azure_storage",
    service_version: str = "1.0.0",
    logger: Optional[AzureLogger] = None,
    connection_string: Optional[str] = None,
    enable_blob_storage: bool = True,
    enable_file_storage: bool = True,
    enable_queue_storage: bool = True,
) -> AzureStorage:
    """Factory function to create cached AzureStorage instance.

    Returns existing storage instance if one with same configuration exists.
    Provides a convenient way to create an AzureStorage instance with
    common configuration patterns. If no credential or azure_identity
    is provided, creates a default AzureIdentity instance.

    Args:
        account_url: Azure Storage Account URL
        credential: Azure credential for authentication
        azure_identity: AzureIdentity instance for credential management
        account_key: Optional Azure Storage account key for SAS generation
        service_name: Service name for tracing context
        service_version: Service version for metadata
        logger: Optional AzureLogger instance
        connection_string: Application Insights connection string
        enable_blob_storage: Enable blob storage operations client
        enable_file_storage: Enable file storage operations client
        enable_queue_storage: Enable queue storage operations client

    Returns:
        Configured AzureStorage instance (cached if available)

    Example:
        # Basic usage with default credential
        storage = create_azure_storage("https://account.blob.core.windows.net/")
        
        # With custom service name and specific features
        storage = create_azure_storage(
            "https://account.blob.core.windows.net/",
            service_name="my_app",
            enable_file_storage=False,
            enable_queue_storage=False
        )
        
        # Note: Containers and queues should be created via infrastructure as code
    """
    # Handle default credential creation before caching
    if credential is None and azure_identity is None:
        # Create default AzureIdentity instance
        from ..mgmt.identity import create_azure_identity
        azure_identity = create_azure_identity(
            service_name=f"{service_name}_identity",
            service_version=service_version,
            connection_string=connection_string,
        )

    # Create cache key from configuration parameters
    # Use object identity for credential objects since they may not be hashable
    cache_key = (
        account_url,
        id(credential) if credential else None,
        id(azure_identity) if azure_identity else None,
        account_key,
        service_name,
        service_version,
        id(logger) if logger else None,
        connection_string,
        enable_blob_storage,
        enable_file_storage,
        enable_queue_storage,
    )

    # Return cached instance if available
    if cache_key in _storage_instances:
        return _storage_instances[cache_key]

    # Create new instance and cache it
    storage_instance = AzureStorage(
        account_url=account_url,
        credential=credential,
        azure_identity=azure_identity,
        account_key=account_key,
        service_name=service_name,
        service_version=service_version,
        logger=logger,
        connection_string=connection_string,
        enable_blob_storage=enable_blob_storage,
        enable_file_storage=enable_file_storage,
        enable_queue_storage=enable_queue_storage,
    )
    
    _storage_instances[cache_key] = storage_instance
    return storage_instance 