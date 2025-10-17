"""Tests for azpaddypy.mcp.services modules.

Tests Azure service modules used by the MCP server.
"""

import pytest
from unittest.mock import Mock, patch

from azpaddypy.mcp.services import base
from azpaddypy.mcp.services import resources
from azpaddypy.mcp.services import storage
from azpaddypy.mcp.services import cosmos
from azpaddypy.mcp.services import subscription


@pytest.fixture(autouse=True)
def reset_context():
    """Reset the global context before each test."""
    ctx = base.get_context()
    ctx.reset()
    yield
    ctx.reset()


@pytest.fixture
def mock_credential():
    """Create a mock Azure credential."""
    return Mock()


@pytest.fixture
def mock_subscription_id():
    """Create a mock subscription ID."""
    return "12345678-1234-1234-1234-123456789abc"


# =============================================================================
# Base Module Tests
# =============================================================================

class TestAzureServiceContext:
    """Test the AzureServiceContext class."""

    def test_initialize_with_explicit_params(self, mock_credential, mock_subscription_id):
        """Test explicit initialization."""
        ctx = base.get_context()
        ctx.initialize(credential=mock_credential, subscription_id=mock_subscription_id)

        assert ctx._credential == mock_credential
        assert ctx._subscription_id == mock_subscription_id
        assert ctx._initialized is True

    def test_initialize_requires_subscription_id(self, mock_credential):
        """Test that initialization requires subscription ID."""
        ctx = base.get_context()

        with pytest.raises(base.AzureMCPError, match="subscription_id must be provided"):
            ctx.initialize(credential=mock_credential, subscription_id=None)

    def test_initialize_with_auto_discovery_success(self):
        """Test successful initialization with auto-discovery."""
        mock_credential = Mock()
        mock_subscription = Mock()
        mock_subscription.subscription_id = "auto-discovered-sub-id"

        with patch.object(base, "DefaultAzureCredential") as mock_cred_class, \
             patch.object(base, "SubscriptionClient") as mock_client_class:
            mock_cred_class.return_value = mock_credential
            mock_client = Mock()
            mock_client.subscriptions.list.return_value = [mock_subscription]
            mock_client_class.return_value = mock_client

            ctx = base.get_context()
            ctx.initialize_with_auto_discovery()

            assert ctx._credential == mock_credential
            assert ctx._subscription_id == "auto-discovered-sub-id"
            assert ctx._initialized is True

    def test_initialize_with_auto_discovery_no_subscriptions(self):
        """Test auto-discovery when no subscriptions are found."""
        mock_credential = Mock()

        with patch.object(base, "DefaultAzureCredential") as mock_cred_class, \
             patch.object(base, "SubscriptionClient") as mock_client_class:
            mock_cred_class.return_value = mock_credential
            mock_client = Mock()
            mock_client.subscriptions.list.return_value = []
            mock_client_class.return_value = mock_client

            ctx = base.get_context()

            with pytest.raises(base.AzureMCPError, match="No Azure subscriptions found"):
                ctx.initialize_with_auto_discovery()

    def test_ensure_initialized_auto_initializes(self, monkeypatch, mock_credential):
        """Test that ensure_initialized auto-initializes when needed."""
        monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "auto-init-sub-id")

        with patch.object(base, "DefaultAzureCredential") as mock_cred_class:
            mock_cred_class.return_value = mock_credential

            ctx = base.get_context()
            ctx.ensure_initialized()

            assert ctx._credential == mock_credential
            assert ctx._subscription_id == "auto-init-sub-id"

    def test_credential_property_auto_initializes(self, monkeypatch, mock_credential):
        """Test that accessing credential property auto-initializes."""
        monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "auto-init-sub-id")

        with patch.object(base, "DefaultAzureCredential") as mock_cred_class:
            mock_cred_class.return_value = mock_credential

            ctx = base.get_context()
            cred = ctx.credential

            assert cred == mock_credential

    def test_reset_clears_state(self, mock_credential, mock_subscription_id):
        """Test that reset clears all state."""
        ctx = base.get_context()
        ctx.initialize(credential=mock_credential, subscription_id=mock_subscription_id)

        ctx.reset()

        assert ctx._credential is None
        assert ctx._subscription_id is None
        assert ctx._initialized is False


# =============================================================================
# Resources Module Tests
# =============================================================================

class TestResourcesModule:
    """Test the resources service module."""

    @pytest.fixture
    def setup_context(self, mock_credential, mock_subscription_id):
        """Setup initialized context."""
        ctx = base.get_context()
        ctx.initialize(credential=mock_credential, subscription_id=mock_subscription_id)

    def test_list_resource_groups(self, setup_context):
        """Test listing resource groups with application tag extraction."""
        mock_rg1 = Mock()
        mock_rg1.as_dict.return_value = {
            "name": "rg-1",
            "location": "eastus",
            "tags": {"application": "web-app", "environment": "prod"}
        }
        mock_rg2 = Mock()
        mock_rg2.as_dict.return_value = {
            "name": "rg-2",
            "location": "westus",
            "tags": None
        }

        with patch.object(base, "ResourceManagementClient") as mock_client_class:
            mock_client = Mock()
            mock_client.resource_groups.list.return_value = [mock_rg1, mock_rg2]
            mock_client_class.return_value = mock_client

            result = resources.list_resource_groups()

            assert len(result) == 2
            assert result[0]["name"] == "rg-1"
            assert result[0]["application"] == "web-app"
            assert result[1]["name"] == "rg-2"
            assert result[1]["application"] == "None"

    def test_list_resources_in_group(self, setup_context):
        """Test listing resources in a resource group."""
        mock_resource = Mock()
        mock_resource.as_dict.return_value = {
            "name": "storage-account",
            "type": "Microsoft.Storage/storageAccounts"
        }

        with patch.object(base, "ResourceManagementClient") as mock_client_class:
            mock_client = Mock()
            mock_client.resources.list_by_resource_group.return_value = [mock_resource]
            mock_client_class.return_value = mock_client

            result = resources.list_resources_in_group("test-rg")

            assert len(result) == 1
            assert result[0]["name"] == "storage-account"


# =============================================================================
# Storage Module Tests
# =============================================================================

class TestStorageModule:
    """Test the storage service module."""

    @pytest.fixture
    def setup_context(self, mock_credential, mock_subscription_id):
        """Setup initialized context."""
        ctx = base.get_context()
        ctx.initialize(credential=mock_credential, subscription_id=mock_subscription_id)

    def test_list_storage_accounts_all(self, setup_context):
        """Test listing all storage accounts."""
        mock_account = Mock()
        mock_account.as_dict.return_value = {
            "name": "storageaccount1",
            "location": "eastus"
        }

        with patch.object(base, "StorageManagementClient") as mock_client_class:
            mock_client = Mock()
            mock_client.storage_accounts.list.return_value = [mock_account]
            mock_client_class.return_value = mock_client

            result = storage.list_storage_accounts()

            assert len(result) == 1
            assert result[0]["name"] == "storageaccount1"

    def test_list_storage_accounts_by_resource_group(self, setup_context):
        """Test listing storage accounts in a resource group."""
        mock_account = Mock()
        mock_account.as_dict.return_value = {
            "name": "storageaccount1",
            "location": "eastus"
        }

        with patch.object(base, "StorageManagementClient") as mock_client_class:
            mock_client = Mock()
            mock_client.storage_accounts.list_by_resource_group.return_value = [mock_account]
            mock_client_class.return_value = mock_client

            result = storage.list_storage_accounts(resource_group="test-rg")

            assert len(result) == 1
            mock_client.storage_accounts.list_by_resource_group.assert_called_once_with("test-rg")


# =============================================================================
# Cosmos Module Tests
# =============================================================================

class TestCosmosModule:
    """Test the cosmos service module."""

    @pytest.fixture
    def setup_context(self, mock_credential, mock_subscription_id):
        """Setup initialized context."""
        ctx = base.get_context()
        ctx.initialize(credential=mock_credential, subscription_id=mock_subscription_id)

    def test_list_cosmosdb_accounts(self, setup_context):
        """Test listing Cosmos DB accounts."""
        mock_account = Mock()
        mock_account.as_dict.return_value = {
            "name": "cosmosaccount1",
            "location": "eastus"
        }

        with patch.object(base, "CosmosDBManagementClient") as mock_client_class:
            mock_client = Mock()
            mock_client.database_accounts.list.return_value = [mock_account]
            mock_client_class.return_value = mock_client

            result = cosmos.list_cosmosdb_accounts()

            assert len(result) == 1
            assert result[0]["name"] == "cosmosaccount1"

    def test_list_cosmosdb_sql_databases(self, setup_context):
        """Test listing Cosmos DB SQL databases."""
        mock_database = Mock()
        mock_database.as_dict.return_value = {
            "name": "database1",
            "id": "/subscriptions/.../databases/database1"
        }

        with patch.object(base, "CosmosDBManagementClient") as mock_client_class:
            mock_client = Mock()
            mock_client.sql_resources.list_sql_databases.return_value = [mock_database]
            mock_client_class.return_value = mock_client

            result = cosmos.list_cosmosdb_sql_databases("account1", "test-rg")

            assert len(result) == 1
            assert result[0]["name"] == "database1"


# =============================================================================
# Subscription Module Tests
# =============================================================================

class TestSubscriptionModule:
    """Test the subscription service module."""

    @pytest.fixture
    def setup_context(self, mock_credential, mock_subscription_id):
        """Setup initialized context."""
        ctx = base.get_context()
        ctx.initialize(credential=mock_credential, subscription_id=mock_subscription_id)

    def test_list_subscriptions(self):
        """Test listing all subscriptions without requiring context initialization."""
        mock_sub1 = Mock()
        mock_sub1.as_dict.return_value = {
            "subscriptionId": "sub-id-1",
            "displayName": "Subscription 1",
            "state": "Enabled",
            "tenantId": "tenant-1"
        }
        mock_sub2 = Mock()
        mock_sub2.as_dict.return_value = {
            "subscriptionId": "sub-id-2",
            "displayName": "Subscription 2",
            "state": "Enabled",
            "tenantId": "tenant-2"
        }

        with patch("azure.identity.DefaultAzureCredential") as mock_cred_class, \
             patch("azure.mgmt.resource.SubscriptionClient") as mock_client_class:
            mock_credential = Mock()
            mock_cred_class.return_value = mock_credential
            mock_client = Mock()
            mock_client.subscriptions.list.return_value = [mock_sub1, mock_sub2]
            mock_client_class.return_value = mock_client

            result = subscription.list_subscriptions()

            assert len(result) == 2
            assert result[0]["subscriptionId"] == "sub-id-1"
            assert result[1]["subscriptionId"] == "sub-id-2"
            mock_client_class.assert_called_once_with(mock_credential)

    def test_get_subscription_info(self, setup_context, mock_subscription_id):
        """Test getting subscription information."""
        mock_subscription = Mock()
        mock_subscription.as_dict.return_value = {
            "subscriptionId": mock_subscription_id,
            "displayName": "Test Subscription",
            "state": "Enabled"
        }

        with patch.object(base, "SubscriptionClient") as mock_client_class:
            mock_client = Mock()
            mock_client.subscriptions.get.return_value = mock_subscription
            mock_client_class.return_value = mock_client

            result = subscription.get_subscription_info()

            assert result["subscriptionId"] == mock_subscription_id
            assert result["displayName"] == "Test Subscription"

    def test_list_locations(self, setup_context, mock_subscription_id):
        """Test listing Azure locations."""
        mock_location = Mock()
        mock_location.as_dict.return_value = {
            "name": "eastus",
            "displayName": "East US"
        }

        with patch.object(base, "SubscriptionClient") as mock_client_class:
            mock_client = Mock()
            mock_client.subscriptions.list_locations.return_value = [mock_location]
            mock_client_class.return_value = mock_client

            result = subscription.list_locations()

            assert len(result) == 1
            assert result[0]["name"] == "eastus"
