from typing import Optional, Any, Dict, List, Union, AsyncGenerator
from contextlib import asynccontextmanager
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.core.exceptions import ClientAuthenticationError, ServiceRequestError, ServiceResponseError, ResourceNotFoundError
from azure.core.credentials import TokenCredential
from ..mgmt.logging import AzureLogger
from ..mgmt.identity import AzureIdentity

class AzureCosmosDB:
    """
    Azure Cosmos DB management with standardized client initialization,
    caching, and both synchronous and asynchronous operations.
    """

    def __init__(
        self,
        endpoint: str,
        credential: Optional[TokenCredential] = None,
        azure_identity: Optional[AzureIdentity] = None,
        service_name: str = "azure_cosmosdb",
        service_version: str = "1.0.0",
        logger: Optional[AzureLogger] = None,
        connection_string: Optional[str] = None,
    ):
        self.endpoint = endpoint
        self.service_name = service_name
        self.service_version = service_version

        if logger:
            self.logger = logger
        else:
            self.logger = AzureLogger(
                service_name=service_name,
                service_version=service_version,
                connection_string=connection_string,
                enable_console_logging=True,
            )

        if azure_identity:
            self.credential = azure_identity.get_credential()
        elif credential:
            self.credential = credential
        else:
            raise ValueError("Either 'credential' or 'azure_identity' must be provided.")

        self.client: Optional[CosmosClient] = None
        self._setup_client()

        self.logger.info(
            f"Azure Cosmos DB initialized for service '{service_name}' v{service_version}",
            extra={"endpoint": endpoint}
        )

    def _setup_client(self):
        """Initialize the synchronous CosmosClient."""
        try:
            self.client = CosmosClient(url=self.endpoint, credential=self.credential)
            self.logger.debug("CosmosClient initialized successfully.")
        except (ClientAuthenticationError, ServiceRequestError, ServiceResponseError) as e:
            self.logger.error(f"Failed to initialize CosmosClient: {e}", exc_info=True)
            raise

    def get_client(self) -> CosmosClient:
        """Get the configured synchronous CosmosClient instance."""
        if not self.client:
            raise RuntimeError("Cosmos DB sync client is not initialized.")
        return self.client

    @asynccontextmanager
    async def async_client_context(self) -> AsyncGenerator[AsyncCosmosClient, None]:
        """
        Provide an asynchronous context manager for the Cosmos DB async client.
        Ensures the client is properly initialized and closed.
        """
        async_client = None
        try:
            self.logger.debug("Entering async client context.")
            async_client = AsyncCosmosClient(url=self.endpoint, credential=self.credential)
            yield async_client
        finally:
            if async_client:
                await async_client.close()
            self.logger.debug("Exited async client context.")
            
    def get_database(self, database_name: str) -> DatabaseProxy:
        """Get a proxy for a database."""
        with self.logger.create_span("AzureCosmosDB.get_database"):
            return self.get_client().get_database_client(database_name)

    def get_container(self, database_name: str, container_name: str) -> ContainerProxy:
        """Get a proxy for a container."""
        with self.logger.create_span("AzureCosmosDB.get_container"):
            database_client = self.get_database(database_name)
            return database_client.get_container_client(container_name)

    def read_item(
        self,
        database_name: str,
        container_name: str,
        item_id: str,
        partition_key: str,
        max_integrated_cache_staleness_in_ms: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Read an item from a container."""
        with self.logger.create_span("AzureCosmosDB.read_item", attributes={"item_id": item_id}):
            try:
                container_client = self.get_container(database_name, container_name)
                options = {}
                if max_integrated_cache_staleness_in_ms is not None:
                    options['max_integrated_cache_staleness_in_ms'] = max_integrated_cache_staleness_in_ms
                
                item = container_client.read_item(item=item_id, partition_key=partition_key, **options)
                self.logger.debug(f"Successfully read item '{item_id}'.")
                return item
            except ResourceNotFoundError:
                self.logger.warning(f"Item '{item_id}' not found.")
                return None
            except Exception as e:
                self.logger.error(f"Failed to read item '{item_id}': {e}", exc_info=True)
                raise

    def query_items(
        self,
        database_name: str,
        container_name: str,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        enable_cross_partition_query: bool = True,
        max_integrated_cache_staleness_in_ms: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query items in a container."""
        with self.logger.create_span("AzureCosmosDB.query_items"):
            try:
                container_client = self.get_container(database_name, container_name)
                options = {'enable_cross_partition_query': enable_cross_partition_query}
                if max_integrated_cache_staleness_in_ms is not None:
                    options['max_integrated_cache_staleness_in_ms'] = max_integrated_cache_staleness_in_ms
                
                items = list(container_client.query_items(
                    query=query,
                    parameters=parameters,
                    **options
                ))
                self.logger.debug(f"Query returned {len(items)} items.")
                return items
            except Exception as e:
                self.logger.error(f"Failed to query items: {e}", exc_info=True)
                raise
                
    def upsert_item(self, database_name: str, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert an item into a container."""
        item_id = item.get("id", "N/A")
        with self.logger.create_span("AzureCosmosDB.upsert_item", attributes={"item_id": item_id}):
            try:
                container_client = self.get_container(database_name, container_name)
                result = container_client.upsert_item(body=item)
                self.logger.debug(f"Successfully upserted item '{item_id}'.")
                return result
            except Exception as e:
                self.logger.error(f"Failed to upsert item '{item_id}': {e}", exc_info=True)
                raise

    def delete_item(
        self,
        database_name: str,
        container_name: str,
        item_id: str,
        partition_key: str
    ) -> bool:
        """
        Delete an item from a container.

        Args:
            database_name: Name of the database.
            container_name: Name of the container.
            item_id: ID of the item to delete.
            partition_key: Partition key value for the item.
        Returns:
            True if the item was deleted, False if not found.
        Raises:
            Exception for errors other than not found.
        """
        with self.logger.create_span("AzureCosmosDB.delete_item", attributes={"item_id": item_id}):
            try:
                container_client = self.get_container(database_name, container_name)
                container_client.delete_item(item=item_id, partition_key=partition_key)
                self.logger.debug(f"Successfully deleted item '{item_id}'.")
                return True
            except ResourceNotFoundError:
                self.logger.warning(f"Item '{item_id}' not found for deletion.")
                return False
            except Exception as e:
                self.logger.error(f"Failed to delete item '{item_id}': {e}", exc_info=True)
                raise


def create_azure_cosmosdb(
    endpoint: str,
    credential: Optional[TokenCredential] = None,
    azure_identity: Optional[AzureIdentity] = None,
    service_name: str = "azure_cosmosdb",
    service_version: str = "1.0.0",
    logger: Optional[AzureLogger] = None,
    connection_string: Optional[str] = None,
) -> AzureCosmosDB:
    """
    Factory function to create an instance of AzureCosmosDB.
    """
    return AzureCosmosDB(
        endpoint=endpoint,
        credential=credential,
        azure_identity=azure_identity,
        service_name=service_name,
        service_version=service_version,
        logger=logger,
        connection_string=connection_string,
    ) 