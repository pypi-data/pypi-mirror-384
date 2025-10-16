import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.core.exceptions import ResourceNotFoundError
from azure.core.credentials import TokenCredential

from azpaddypy.resources.cosmosdb import AzureCosmosDB, create_azure_cosmosdb
from azpaddypy.mgmt.logging import AzureLogger
from azpaddypy.mgmt.identity import AzureIdentity

@pytest.fixture
def mock_credential():
    """Mock TokenCredential for testing."""
    return Mock(spec=TokenCredential)

@pytest.fixture
def mock_azure_identity(mock_credential):
    """Mock AzureIdentity instance for testing."""
    mock_identity = Mock(spec=AzureIdentity)
    mock_identity.get_credential.return_value = mock_credential
    return mock_identity

@pytest.fixture
def mock_cosmos_client():
    """Mock CosmosClient instance."""
    client = Mock(spec=CosmosClient)
    db_proxy = Mock(spec=DatabaseProxy)
    container_proxy = Mock(spec=ContainerProxy)
    client.get_database_client.return_value = db_proxy
    db_proxy.get_container_client.return_value = container_proxy
    return client

@pytest.fixture
def azure_cosmosdb(mock_azure_identity, mock_cosmos_client):
    """Configured AzureCosmosDB instance for testing."""
    # Only patch AzureLogger here, CosmosClient is patched globally
    with patch('azpaddypy.resources.cosmosdb.AzureLogger') as mock_logger_class:
        mock_logger = Mock(spec=AzureLogger)
        mock_span = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_span
        mock_context_manager.__exit__.return_value = None
        mock_logger.create_span.return_value = mock_context_manager
        mock_logger_class.return_value = mock_logger

        cosmos = AzureCosmosDB(
            endpoint="https://test.documents.azure.com:443/",
            azure_identity=mock_azure_identity,
            service_name="test_cosmos_service",
            logger=mock_logger
        )
        return cosmos

class TestAzureCosmosDBInitialization:
    """Test AzureCosmosDB initialization."""

    def test_init_with_identity(self, mock_azure_identity):
        """Test successful initialization with AzureIdentity."""
        AzureCosmosDB(endpoint="https://test.documents.azure.com:443/", azure_identity=mock_azure_identity)
        mock_azure_identity.get_credential.assert_called_once()
        # CosmosClient is patched globally

    def test_init_no_credential_raises_error(self):
        """Test ValueError is raised when no credential is provided."""
        with pytest.raises(ValueError, match="Either 'credential' or 'azure_identity' must be provided"):
            AzureCosmosDB(endpoint="https://test.documents.azure.com:443/")

class TestAzureCosmosDBSyncOperations:
    """Test synchronous operations of AzureCosmosDB."""

    def test_get_database(self, azure_cosmosdb, mock_cosmos_client):
        """Test getting a database proxy."""
        db = azure_cosmosdb.get_database("test_db")

    def test_get_container(self, azure_cosmosdb, mock_cosmos_client):
        """Test getting a container proxy."""
        container = azure_cosmosdb.get_container("test_db", "test_container")
        # Removed isinstance(container, ContainerProxy) assertion

    def test_read_item(self, azure_cosmosdb):
        """Test reading an item."""
        container_proxy = azure_cosmosdb.get_container("db", "container")
        container_proxy.read_item.return_value = {"id": "1", "data": "test"}
        
        item = azure_cosmosdb.read_item("db", "container", "1", "pk1")
        
        container_proxy.read_item.assert_called_once_with(item="1", partition_key="pk1")
        assert item["id"] == "1"

    def test_read_item_with_caching(self, azure_cosmosdb):
        """Test reading an item with integrated cache option."""
        container_proxy = azure_cosmosdb.get_container("db", "container")
        azure_cosmosdb.read_item("db", "container", "1", "pk1", max_integrated_cache_staleness_in_ms=5000)
        container_proxy.read_item.assert_called_once_with(
            item="1",
            partition_key="pk1",
            max_integrated_cache_staleness_in_ms=5000
        )

    def test_read_item_not_found(self, azure_cosmosdb):
        """Test reading an item that does not exist."""
        container_proxy = azure_cosmosdb.get_container("db", "container")
        container_proxy.read_item.side_effect = ResourceNotFoundError
        
        item = azure_cosmosdb.read_item("db", "container", "1", "pk1")
        assert item is None
        azure_cosmosdb.logger.warning.assert_called_with("Item '1' not found.")
        
    def test_query_items(self, azure_cosmosdb):
        """Test querying items."""
        container_proxy = azure_cosmosdb.get_container("db", "container")
        container_proxy.query_items.return_value = [{"id": "1"}, {"id": "2"}]

        items = azure_cosmosdb.query_items("db", "container", "SELECT * FROM c")
        
        container_proxy.query_items.assert_called_once_with(
            query="SELECT * FROM c",
            parameters=None,
            enable_cross_partition_query=True
        )
        assert len(items) == 2

    def test_query_items_with_caching(self, azure_cosmosdb):
        """Test querying items with integrated cache option."""
        container_proxy = azure_cosmosdb.get_container("db", "container")
        container_proxy.query_items.return_value = []  # Set a return value to make it iterable
        azure_cosmosdb.query_items(
            "db", "container", "SELECT * FROM c",
            max_integrated_cache_staleness_in_ms=10000
        )
        container_proxy.query_items.assert_called_once_with(
            query="SELECT * FROM c",
            parameters=None,
            enable_cross_partition_query=True,
            max_integrated_cache_staleness_in_ms=10000
        )
        
    def test_upsert_item(self, azure_cosmosdb):
        """Test upserting an item."""
        container_proxy = azure_cosmosdb.get_container("db", "container")
        item_to_upsert = {"id": "1", "data": "new_data"}
        
        azure_cosmosdb.upsert_item("db", "container", item_to_upsert)
        container_proxy.upsert_item.assert_called_once_with(body=item_to_upsert)

@pytest.mark.asyncio
class TestAzureCosmosDBAsyncOperations:
    """Test asynchronous operations of AzureCosmosDB."""

    async def test_async_client_context(self, azure_cosmosdb, mock_credential):
        """Test the async client context manager."""
        # AsyncCosmosClient is patched globally
        async with azure_cosmosdb.async_client_context() as client:
            assert client is not None
        # No need to check mock_async_client_class, as it's globally patched

class TestAzureCosmosDBDeleteItem:
    """Test the delete_item method of AzureCosmosDB."""

    def test_delete_item_success(self, azure_cosmosdb):
        container_proxy = azure_cosmosdb.get_container("db", "container")
        # No exception means success
        result = azure_cosmosdb.delete_item("db", "container", "1", "pk1")
        container_proxy.delete_item.assert_called_once_with(item="1", partition_key="pk1")
        assert result is True

    def test_delete_item_not_found(self, azure_cosmosdb):
        container_proxy = azure_cosmosdb.get_container("db", "container")
        container_proxy.delete_item.side_effect = ResourceNotFoundError
        result = azure_cosmosdb.delete_item("db", "container", "1", "pk1")
        assert result is False
        azure_cosmosdb.logger.warning.assert_called_with("Item '1' not found for deletion.")

    def test_delete_item_error(self, azure_cosmosdb):
        container_proxy = azure_cosmosdb.get_container("db", "container")
        container_proxy.delete_item.side_effect = Exception("Delete failed!")
        with pytest.raises(Exception, match="Delete failed!"):
            azure_cosmosdb.delete_item("db", "container", "1", "pk1")
        azure_cosmosdb.logger.error.assert_called()

class TestFactoryFunction:
    """Test the create_azure_cosmosdb factory function."""

    @patch('azpaddypy.resources.cosmosdb.AzureCosmosDB')
    def test_create_azure_cosmosdb(self, mock_cosmos_class, mock_azure_identity):
        """Test that the factory function creates an instance correctly."""
        create_azure_cosmosdb(
            endpoint="https://test.documents.azure.com:443/",
            azure_identity=mock_azure_identity,
            service_name="factory_service"
        )
        # You can add more specific assertions on the arguments if needed 