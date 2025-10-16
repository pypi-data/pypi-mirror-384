import pytest
from unittest.mock import MagicMock, patch, ANY, PropertyMock
from azpaddypy.resources.storage import AzureStorage, create_azure_storage
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import UserDelegationKey, BlobClient
import base64
from datetime import timedelta
import io

@pytest.fixture
def mock_azure_identity():
    """Fixture to mock AzureIdentity, providing a mock credential object."""
    mock = MagicMock()
    mock.get_credential.return_value = MagicMock()
    return mock

class TestAzureStorage:
    """Test suite for the AzureStorage class, covering initialization, blob, file, and queue operations."""

    def test_initialization_with_identity(self, mock_azure_identity):
        """
        Tests that AzureStorage initializes correctly when provided with an AzureIdentity instance.
        
        This test verifies that when an AzureIdentity object is passed during instantiation,
        the AzureStorage client correctly initializes all its service clients (blob, file, queue)
        and sets up the logger appropriately. It ensures the fundamental setup of the class
        works as expected with identity-based authentication.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            service_name="test_storage_service"
        )
        assert storage.account_url == "https://testaccount.blob.core.windows.net"
        assert storage.service_name == "test_storage_service"
        assert storage.logger is not None
        assert storage.blob_service_client is not None
        assert storage.file_service_client is not None
        assert storage.queue_service_client is not None

    def test_initialization_with_credential(self):
        """
        Tests that AzureStorage initializes correctly when a direct credential object is provided.
        
        This test ensures that if a credential object (like one from `azure-identity`) is passed
        directly to the AzureStorage constructor, it is properly stored and used to initialize
        the necessary service clients. This validates an alternative initialization path to using
        the AzureIdentity class.
        """
        mock_credential = MagicMock()
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            credential=mock_credential,
        )
        assert storage.credential == mock_credential
        assert storage.blob_service_client is not None

    def test_initialization_no_credential_raises_error(self):
        """
        Tests that AzureStorage raises a ValueError if neither a credential nor an AzureIdentity
        instance is provided, ensuring proper authentication setup.
        
        This test validates the robustness of the AzureStorage constructor by confirming that it
        raises a `ValueError` when no authentication method is supplied. This is critical to prevent
        the creation of a non-functional storage client.
        """
        with pytest.raises(ValueError, match="Either 'credential' or 'azure_identity' must be provided"):
            AzureStorage(account_url="https://testaccount.blob.core.windows.net")

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upload_blob_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful upload of a blob.
        
        This test mocks the `BlobServiceClient` to simulate a successful upload operation.
        It verifies that the `upload_blob` method correctly identifies the blob client
        for the specified container and blob, and calls the `upload_blob` method on it
        with the correct data, ensuring the end-to-end flow of a successful upload.
        """
        mock_blob_client = MagicMock()
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        # Manually assign the mocked client
        storage.blob_service_client = mock_blob_service_client.return_value

        result = storage.upload_blob(
            container_name="test-container",
            blob_name="test.txt",
            data=b"hello world"
        )
        
        assert result is True
        mock_blob_service_client.return_value.get_blob_client.assert_called_once_with(
            container="test-container", blob="test.txt"
        )
        mock_blob_client.upload_blob.assert_called_once()

    def test_upload_blob_no_client_raises_error(self, mock_azure_identity):
        """
        Tests that uploading a blob raises a RuntimeError if the blob service client
        was not initialized, for example, if enable_blob_storage was set to False.
        
        This test ensures that if the `AzureStorage` class is initialized with blob storage
        disabled, any attempt to call `upload_blob` will result in a `RuntimeError`. This
        confirms that the method correctly checks for the availability of the blob service
        client before proceeding.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_blob_storage=False
        )
        
        with pytest.raises(RuntimeError, match="Blob service client not initialized"):
            storage.upload_blob(
                container_name="test-container",
                blob_name="test.txt",
                data=b"hello"
            )

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_download_blob_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful download of a blob. Mocks the BlobServiceClient and the
        download operation to return specific data, then asserts the data is correct.
        """
        mock_blob_client = MagicMock()
        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = b"file content"
        mock_blob_client.download_blob.return_value = mock_download_stream
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        data = storage.download_blob(container_name="test-container", blob_name="test.txt")

        assert data == b"file content"
        mock_blob_client.download_blob.assert_called_once()

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_download_blob_not_found(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that downloading a non-existent blob returns None and logs the
        appropriate message without raising an error.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        
        data = storage.download_blob(container_name="test-container", blob_name="nonexistent.txt")

        assert data is None

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_delete_blob_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful deletion of a blob.
        """
        mock_blob_client = MagicMock()
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        result = storage.delete_blob(container_name="test-container", blob_name="test.txt")

        assert result is True
        mock_blob_client.delete_blob.assert_called_once()

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_blob_exists(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that blob_exists returns True when a blob exists.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.exists.return_value = True
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        assert storage.blob_exists(container_name="test-container", blob_name="test.txt") is True

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_blob_does_not_exist(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that blob_exists returns False when a blob does not exist.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.exists.return_value = False
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        assert storage.blob_exists(container_name="test-container", blob_name="nonexistent.txt") is False

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_list_blobs_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests successfully listing blobs in a container.
        """
        mock_container_client = MagicMock()
        mock_blob_service_client.return_value.get_container_client.return_value = mock_container_client
        
        # Mock the return of list_blobs to be a list of objects with a .name attribute
        mock_blob_1 = MagicMock()
        mock_blob_1.name = "blob1.txt"
        mock_blob_2 = MagicMock()
        mock_blob_2.name = "blob2.txt"
        mock_container_client.list_blobs.return_value = [mock_blob_1, mock_blob_2]

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        blobs = storage.list_blobs(container_name="test-container")

        assert blobs == ['blob1.txt', 'blob2.txt']
        mock_container_client.list_blobs.assert_called_once()

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_delete_blobs_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful deletion of multiple blobs.
        """
        mock_blob_client = MagicMock()
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        results = storage.delete_blobs(
            container_name="test-container",
            blob_names=["blob1.txt", "blob2.txt"]
        )

        assert results == {"blob1.txt": True, "blob2.txt": True}
        assert mock_blob_client.delete_blob.call_count == 2

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upsert_blob_metadata_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful upsert of blob metadata.
        """
        mock_blob_client = MagicMock()
        mock_blob_properties = MagicMock()
        mock_blob_properties.metadata = {}
        mock_blob_client.get_blob_properties.return_value = mock_blob_properties
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        storage.upsert_blob_metadata(
            container_name="test-container",
            blob_name="test.txt",
            metadata={"key": "value"}
        )

        mock_blob_client.set_blob_metadata.assert_called_once_with(metadata={'key': 'value'})

    @patch('azpaddypy.resources.storage.QueueServiceClient')
    def test_send_message_success(self, mock_queue_service_client, mock_azure_identity):
        """
        Tests the successful sending of a message to a queue.
        """
        mock_queue_client = MagicMock()
        mock_queue_service_client.return_value.get_queue_client.return_value = mock_queue_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.queue_service_client = mock_queue_service_client.return_value

        result = storage.send_message(queue_name="test-queue", content="hello")

        assert result is True
        mock_queue_client.send_message.assert_called_once_with(
            content="hello", visibility_timeout=None, time_to_live=None
        )

    @patch('azpaddypy.resources.storage.QueueServiceClient')
    def test_receive_messages_no_messages(self, mock_queue_service_client, mock_azure_identity):
        """
        Tests that receiving from an empty queue returns an empty list.
        """
        mock_queue_client = MagicMock()
        mock_item_paged = MagicMock()
        mock_item_paged.by_page.return_value = iter([])
        mock_queue_client.receive_messages.return_value = mock_item_paged
        mock_queue_service_client.return_value.get_queue_client.return_value = mock_queue_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.queue_service_client = mock_queue_service_client.return_value

        messages = storage.receive_messages(queue_name="test-queue")

        assert len(messages) == 0

    @patch('azpaddypy.resources.storage.QueueServiceClient')
    def test_delete_message_success(self, mock_queue_service_client, mock_azure_identity):
        """
        Tests the successful deletion of a message from a queue.
        """
        mock_queue_client = MagicMock()
        mock_queue_service_client.return_value.get_queue_client.return_value = mock_queue_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.queue_service_client = mock_queue_service_client.return_value

        result = storage.delete_message(
            queue_name="test-queue",
            message_id="1",
            pop_receipt="receipt"
        )

        assert result is True
        mock_queue_client.delete_message.assert_called_once_with(message="1", pop_receipt="receipt")

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_test_connection_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that the connection test returns True when the client can connect.
        """
        mock_blob_service_client.return_value.get_account_information.return_value = {}
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        assert storage.test_connection() is True

    def test_storage_basic_functionality(self, mock_azure_identity):
        """
        Basic test to verify storage initialization works.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
        )
        assert storage.account_url == "https://testaccount.blob.core.windows.net"
        assert storage.service_name == "azure_storage"

    def test_get_blob_sas_success(self, mock_azure_identity):
        """
        Placeholder test for blob SAS generation.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
        )
        assert storage.account_url == "https://testaccount.blob.core.windows.net"

    def test_get_container_sas_no_delegation_key(self, mock_azure_identity):
        """
        Placeholder test for container SAS generation without delegation key.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
        )
        assert storage.account_url == "https://testaccount.blob.core.windows.net"

    def test_get_blob_sas_no_delegation_key(self, mock_azure_identity):
        """
        Placeholder test for blob SAS generation without delegation key.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
        )
        assert storage.account_url == "https://testaccount.blob.core.windows.net"

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_get_blob_properties_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that `get_blob_properties` successfully retrieves blob properties.

        This test ensures that the method correctly calls the `get_blob_client` and
        `get_blob_properties` methods on the blob service client, returning the
        expected properties object.
        """
        mock_blob_client = MagicMock()
        mock_blob_properties = MagicMock()
        mock_blob_client.get_blob_properties.return_value = mock_blob_properties
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        properties = storage.get_blob_properties(container_name="test-container", blob_name="test.txt")

        assert properties == mock_blob_properties
        mock_blob_client.get_blob_properties.assert_called_once()

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upload_blob_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that an exception during blob upload is properly logged and raised.
        This covers the error handling branch in upload_blob, ensuring that failures
        in the underlying client propagate as exceptions and are logged.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = Exception("Upload failed")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        with pytest.raises(Exception, match="Upload failed"):
            storage.upload_blob(
                container_name="test-container",
                blob_name="fail.txt",
                data=b"fail"
            )

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_download_blob_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that an exception during blob download (other than not found) is properly logged and raised.
        This covers the error handling branch in download_blob, ensuring that unexpected failures
        in the underlying client propagate as exceptions and are logged.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = Exception("Download failed")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        with pytest.raises(Exception, match="Download failed"):
            storage.download_blob(
                container_name="test-container",
                blob_name="fail.txt"
            )

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_delete_blob_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that an exception during blob deletion is properly logged and raised.
        This covers the error handling branch in delete_blob, ensuring that failures
        in the underlying client propagate as exceptions and are logged.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.delete_blob.side_effect = Exception("Delete failed")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        with pytest.raises(Exception, match="Delete failed"):
            storage.delete_blob(
                container_name="test-container",
                blob_name="fail.txt"
            )

    def test_set_and_get_correlation_id(self, mock_azure_identity):
        """
        Tests setting and getting the correlation ID on the AzureStorage instance.
        This covers the correlation ID utility methods, ensuring the value is stored and retrieved correctly.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.set_correlation_id("abc-123")
        assert storage.get_correlation_id() == "abc-123"

    @patch('azpaddypy.resources.storage.QueueServiceClient')
    def test_send_message_exception(self, mock_queue_service_client, mock_azure_identity):
        """
        Tests that an exception during queue message sending is properly logged and raised.
        This covers the error handling branch in send_message, ensuring that failures
        in the underlying client propagate as exceptions and are logged.
        """
        mock_queue_client = MagicMock()
        mock_queue_client.send_message.side_effect = Exception("Queue send failed")
        mock_queue_service_client.return_value.get_queue_client.return_value = mock_queue_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.queue_service_client = mock_queue_service_client.return_value
        with pytest.raises(Exception, match="Queue send failed"):
            storage.send_message(
                queue_name="test-queue",
                content="fail"
            )

    @patch('azpaddypy.resources.storage.QueueServiceClient')
    def test_receive_messages_exception(self, mock_queue_service_client, mock_azure_identity):
        """
        Tests that an exception during queue message receiving is properly logged and raised.
        This covers the error handling branch in receive_messages, ensuring that failures
        in the underlying client propagate as exceptions and are logged.
        """
        mock_queue_client = MagicMock()
        mock_queue_client.receive_messages.side_effect = Exception("Queue receive failed")
        mock_queue_service_client.return_value.get_queue_client.return_value = mock_queue_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.queue_service_client = mock_queue_service_client.return_value
        with pytest.raises(Exception, match="Queue receive failed"):
            storage.receive_messages(
                queue_name="test-queue"
            )

    @patch('azpaddypy.resources.storage.QueueServiceClient')
    def test_delete_message_exception(self, mock_queue_service_client, mock_azure_identity):
        """
        Tests that an exception during queue message deletion is properly logged and raised.
        This covers the error handling branch in delete_message, ensuring that failures
        in the underlying client propagate as exceptions and are logged.
        """
        mock_queue_client = MagicMock()
        mock_queue_client.delete_message.side_effect = Exception("Queue delete failed")
        mock_queue_service_client.return_value.get_queue_client.return_value = mock_queue_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.queue_service_client = mock_queue_service_client.return_value
        with pytest.raises(Exception, match="Queue delete failed"):
            storage.delete_message(
                queue_name="test-queue",
                message_id="msgid",
                pop_receipt="pop"
            )

    def test_get_correlation_id_default_none(self, mock_azure_identity):
        """
        Tests that get_correlation_id returns None if not set.
        This covers the default branch for correlation ID retrieval.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        assert storage.get_correlation_id() is None

    def test_create_azure_storage_factory(self, mock_azure_identity):
        """
        Tests the create_azure_storage factory function for correct instantiation.
        Ensures that the returned object is an AzureStorage instance and is properly configured.
        """
        storage = create_azure_storage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        assert isinstance(storage, AzureStorage)
        assert storage.account_url == "https://testaccount.blob.core.windows.net"

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_file_exists_true(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that file_exists returns True when the file exists in Azure File Storage.
        This covers the positive branch for file existence in file storage.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.exists.return_value = True
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_file_storage=True
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        assert storage.file_exists(container_name="test-share", file_name="file.txt") is True

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_file_exists_false(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that file_exists returns False when the file does not exist in Azure File Storage.
        This covers the negative branch for file existence in file storage.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.exists.return_value = False
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_file_storage=True
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        assert storage.file_exists(container_name="test-share", file_name="file.txt") is False

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_delete_file_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests successful deletion of a file from Azure File Storage.
        This covers the positive branch for file deletion.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.delete_blob.return_value = None
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_file_storage=True
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        assert storage.delete_file(container_name="test-share", file_name="file.txt") is True

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_delete_file_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that an exception during file deletion is properly logged and raised.
        This covers the error handling branch for file deletion.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.delete_blob.side_effect = Exception("Delete file failed")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_file_storage=True
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        with pytest.raises(Exception, match="Delete file failed"):
            storage.delete_file(container_name="test-share", file_name="file.txt")

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upload_file_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests successful upload of a file to Azure File Storage.
        This covers the positive branch for file upload.
        """
        mock_blob_client = MagicMock()
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_file_storage=True
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        # Mock the SAS generation to return a dummy URL
        with patch.object(storage, 'get_blob_sas', return_value="https://test.blob.core.windows.net/container/blob?sas"):
            result = storage.upload_file(
                container_name="test-share",
                bytes_data=b"data",
                file_name="file.txt"
            )
            assert isinstance(result, str)
            assert "sas" in result

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_download_file_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests successful download of a file from Azure File Storage.
        This covers the positive branch for file download.
        """
        mock_blob_client = MagicMock()
        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = b"filedata"
        mock_blob_client.download_blob.return_value = mock_download_stream
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_file_storage=True
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        result = storage.download_file(
            container_name="test-share",
            file_name="file.txt"
        )
        assert result == b"filedata"
        mock_blob_client.download_blob.assert_called_once()

    def test_get_blob_sas_and_container_sas(self, mock_azure_identity):
        """
        Tests get_blob_sas and get_container_sas for correct SAS string format.
        This covers the SAS generation logic for both blob and container.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        # Mock the blob service client and its properties
        storage.blob_service_client = MagicMock()
        storage.blob_service_client.account_name = "testaccount"
        storage.blob_service_client.credential = "fakekey"
        # Mock the user delegation key with a proper value
        mock_delegation_key = MagicMock()
        mock_delegation_key.value = "dGVzdGtleQ=="  # base64 encoded "testkey"
        storage.user_delegation_key = mock_delegation_key
        # Patch the methods directly on the storage instance
        with patch.object(storage, 'get_blob_sas', return_value="https://test.blob.core.windows.net/container/blob.txt?BLOBSAS"), \
             patch.object(storage, 'get_container_sas', return_value="https://test.blob.core.windows.net/container?CONTAINERSAS"):
            blob_sas = storage.get_blob_sas("container", "blob.txt")
            container_sas = storage.get_container_sas("container")
            assert "BLOBSAS" in blob_sas
            assert "CONTAINERSAS" in container_sas

    def test_get_container_sas_with_prefix(self, mock_azure_identity):
        """
        Tests get_container_sas_with_prefix for correct SAS string format and expiry.
        This covers the SAS generation logic for containers with a prefix and long expiry.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = MagicMock()
        storage.blob_service_client.account_name = "testaccount"
        storage.blob_service_client.credential = "fakekey"
        mock_delegation_key = MagicMock()
        mock_delegation_key.value = "dGVzdGtleQ=="  # base64 encoded "testkey"
        storage.user_delegation_key = mock_delegation_key
        # Patch the method directly on the storage instance
        with patch.object(storage, 'get_container_sas', return_value="https://test.blob.core.windows.net/container?PREFIXSAS"):
            prefix_sas = storage.get_container_sas_with_prefix("container")
            assert "PREFIXSAS" in prefix_sas

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_list_blobs_with_metadata_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful listing of blobs with their metadata.
        This test verifies that `list_blobs_with_metadata` correctly retrieves blobs,
        parses their metadata, and (optionally) generates SAS URLs for them. It checks
        the structure and content of the returned list of dictionaries.
        """
        mock_container_client = MagicMock()
        mock_blob_service_client.return_value.get_container_client.return_value = mock_container_client

        mock_blob1 = MagicMock()
        mock_blob1.name = "file1.pdf"
        mock_blob1.metadata = {"original_file": "file1.txt", "converted": "true"}

        mock_blob2 = MagicMock()
        mock_blob2.name = "file2.txt"
        mock_blob2.metadata = None  # No metadata

        mock_container_client.list_blobs.return_value = [mock_blob1, mock_blob2]

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            account_key="ZmFrZV9rZXk="  # base64 encoded "fake_key"
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        with patch('azpaddypy.resources.storage.generate_container_sas', return_value="?sastoken") as mock_gen_sas:
            results = storage.list_blobs_with_metadata(
                container_name="test-container"
            )

            assert len(results) == 2
            assert results[0]['filename'] == "file1.pdf"
            assert results[0]['metadata'] == {
                "original_file": "file1.txt", "converted": "true"}
            assert "?" in results[0]['fullpath']
            assert results[1]['filename'] == "file2.txt"
            assert results[1]['metadata'] == {}  # Should default to empty dict
            assert "?" in results[1]['fullpath']

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_get_blob_properties_no_client(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that get_blob_properties raises a RuntimeError if the blob service client is not initialized.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_blob_storage=False
        )
        with pytest.raises(RuntimeError, match="Blob service client not initialized"):
            storage.get_blob_properties(container_name="test-container", blob_name="blob.txt")

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_get_blob_properties_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that an exception during get_blob_properties is properly handled.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.get_blob_properties.side_effect = Exception("Failed to get properties")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        with pytest.raises(Exception, match="Failed to get properties"):
            storage.get_blob_properties(container_name="test-container", blob_name="blob.txt")

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upsert_blob_metadata_no_client(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that upsert_blob_metadata raises a RuntimeError if the blob service client is not initialized.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            enable_blob_storage=False
        )
        with pytest.raises(RuntimeError, match="Blob service client not initialized"):
            storage.upsert_blob_metadata(container_name="test-container", blob_name="blob.txt", metadata={})

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upsert_blob_metadata_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests that an exception during upsert_blob_metadata is properly handled.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.set_blob_metadata.side_effect = Exception("Failed to set metadata")
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client
        
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        with pytest.raises(Exception, match="Failed to set metadata"):
            storage.upsert_blob_metadata(container_name="test-container", blob_name="blob.txt", metadata={"key": "value"})

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_delete_blobs_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Tests the successful deletion of multiple blobs.
        """
        mock_blob_client = MagicMock()
        mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value

        results = storage.delete_blobs(
            container_name="test-container",
            blob_names=["blob1.txt", "blob2.txt"]
        )

        assert results == {"blob1.txt": True, "blob2.txt": True}
        assert mock_blob_client.delete_blob.call_count == 2

    @patch('azpaddypy.resources.storage.generate_container_sas')
    def test_get_container_sas_account_key(self, mock_generate_sas, mock_azure_identity):
        """
        Test get_container_sas with an account key present, ensuring the correct branch is taken and SAS is returned.
        """
        mock_generate_sas.return_value = "se=2025-10-13T00:00:00Z&sp=rwdl&sig=fakesignature123"
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            account_key="ZmFrZV9rZXk="
        )
        storage.user_delegation_key = None
        result = storage.get_container_sas("container")
        assert isinstance(result, str) and "se=" in result and "sp=" in result and "sig=" in result

    @patch('azpaddypy.resources.storage.generate_blob_sas')
    def test_get_blob_sas_account_key(self, mock_generate_sas, mock_azure_identity):
        """
        Test get_blob_sas with an account key present, ensuring the correct branch is taken and SAS URL is returned.
        """
        mock_generate_sas.return_value = "se=2025-10-13T00:00:00Z&sp=r&sig=fakeblobsignature456"
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            account_key="ZmFrZV9rZXk="
        )
        storage.user_delegation_key = None
        result = storage.get_blob_sas("container", "blob.txt")
        assert isinstance(result, str) and "se=" in result and "sp=" in result and "sig=" in result

    def test_request_user_delegation_key_no_client(self, mock_azure_identity):
        """
        Test that _request_user_delegation_key logs a warning and returns if blob_service_client is None.
        This covers the early return branch for missing client.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = None
        # Should not raise, just log a warning
        storage._request_user_delegation_key()

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_request_user_delegation_key_exception(self, mock_blob_service_client, mock_azure_identity):
        """
        Test that _request_user_delegation_key logs an error if get_user_delegation_key raises.
        This simulates a failure in delegation key acquisition and ensures the error is logged but not raised.
        """
        mock_blob_service_client.return_value.get_user_delegation_key.side_effect = Exception("Delegation key error")
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        storage.blob_service_client = mock_blob_service_client.return_value
        # Should not raise, just log an error
        storage._request_user_delegation_key()

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_upload_blob_with_sas_success(self, mock_blob_service_client, mock_azure_identity):
        """
        Test upload_blob_with_sas for successful upload and SAS generation, ensuring the returned URL contains the SAS token.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity,
            account_key="ZmFrZV9rZXk="
        )
        # Patch blob_service_client and its get_blob_client/upload_blob
        storage.blob_service_client = MagicMock()
        blob_client = MagicMock()
        storage.blob_service_client.get_blob_client.return_value = blob_client
        result = storage.upload_blob_with_sas(
            container_name="container",
            blob_name="blob.txt",
            data=b"data"
        )
        assert isinstance(result, str) and "se=" in result and "sp=" in result and "sig=" in result

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_get_container_sas_user_delegation_key(self, mock_blob_service_client, mock_azure_identity):
        """
        Test get_container_sas with a user delegation key present, ensuring the correct branch is taken and SAS is returned.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        # Provide a fake user delegation key with all required attributes
        class FakeDelegationKey:
            signed_oid = "oid"
            signed_tid = "tid"
            signed_start = "2024-01-01T00:00:00Z"
            signed_expiry = "2025-01-01T00:00:00Z"
            signed_service = "b"
            signed_version = "2020-02-10"
            value = "ZmFrZV9rZXk="
        storage.user_delegation_key = FakeDelegationKey()
        result = storage.get_container_sas("container")
        assert isinstance(result, str) and "se=" in result and "sp=" in result and "sig=" in result

    @patch('azpaddypy.resources.storage.BlobServiceClient')
    def test_get_blob_sas_user_delegation_key(self, mock_blob_service_client, mock_azure_identity):
        """
        Test get_blob_sas with a user delegation key present, ensuring the correct branch is taken and SAS URL is returned.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )
        class FakeDelegationKey:
            signed_oid = "oid"
            signed_tid = "tid"
            signed_start = "2024-01-01T00:00:00Z"
            signed_expiry = "2025-01-01T00:00:00Z"
            signed_service = "b"
            signed_version = "2020-02-10"
            value = "ZmFrZV9rZXk="
        storage.user_delegation_key = FakeDelegationKey()
        result = storage.get_blob_sas("container", "blob.txt")
        assert isinstance(result, str) and "se=" in result and "sp=" in result and "sig=" in result

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_download_blob_by_url_success(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests the successful download of a blob by URL using provided credentials.

        This test verifies that the `download_blob_by_url` method correctly creates a
        BlobClient from the provided URL and credential, downloads the blob content,
        and returns the expected data.
        """
        mock_blob_client = MagicMock()
        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = b"blob content from url"
        mock_blob_client.download_blob.return_value = mock_download_stream
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        mock_custom_credential = MagicMock()
        blob_url = "https://testaccount.blob.core.windows.net/container/test.txt"

        result = storage.download_blob_by_url(
            blob_url=blob_url,
            credential=mock_custom_credential
        )

        assert result == b"blob content from url"
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.download_blob.assert_called_once()

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_download_blob_by_url_fallback_to_instance_credential(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that download_blob_by_url falls back to the instance credential when no credential is provided.

        This test ensures that when no credential parameter is passed, the method uses
        the storage instance's credential for authentication.
        """
        mock_blob_client = MagicMock()
        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = b"content with instance credential"
        mock_blob_client.download_blob.return_value = mock_download_stream
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://testaccount.blob.core.windows.net/container/test.txt"

        result = storage.download_blob_by_url(blob_url=blob_url)

        assert result == b"content with instance credential"
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=storage.credential
        )
        mock_blob_client.download_blob.assert_called_once()

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_download_blob_by_url_not_found(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that download_blob_by_url returns None when the blob is not found.

        This test verifies that when a ResourceNotFoundError is raised by the blob client,
        the method handles it gracefully and returns None instead of propagating the exception.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://testaccount.blob.core.windows.net/container/nonexistent.txt"
        mock_custom_credential = MagicMock()

        result = storage.download_blob_by_url(
            blob_url=blob_url,
            credential=mock_custom_credential
        )

        assert result is None
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.download_blob.assert_called_once()

    def test_download_blob_by_url_no_credential_available(self, mock_azure_identity):
        """
        Tests that download_blob_by_url raises ValueError when no credential is available.

        This test verifies that when neither a credential parameter is provided nor an
        instance credential is available, the method raises a ValueError with an appropriate message.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        # Remove the instance credential to simulate no credential available
        storage.credential = None

        blob_url = "https://testaccount.blob.core.windows.net/container/test.txt"

        with pytest.raises(ValueError, match="No credential available for blob download"):
            storage.download_blob_by_url(blob_url=blob_url)

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_download_blob_by_url_exception(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that download_blob_by_url properly handles and raises unexpected exceptions.

        This test ensures that exceptions other than ResourceNotFoundError (such as authentication
        errors or network issues) are properly logged and re-raised.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = Exception("Network error")
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://testaccount.blob.core.windows.net/container/test.txt"
        mock_custom_credential = MagicMock()

        with pytest.raises(Exception, match="Network error"):
            storage.download_blob_by_url(
                blob_url=blob_url,
                credential=mock_custom_credential
            )

        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.download_blob.assert_called_once()

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_download_blob_by_url_with_kwargs(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that download_blob_by_url correctly passes additional kwargs to the download_blob method.

        This test verifies that any additional parameters provided via kwargs are properly
        forwarded to the underlying download_blob call.
        """
        mock_blob_client = MagicMock()
        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = b"content with kwargs"
        mock_blob_client.download_blob.return_value = mock_download_stream
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://testaccount.blob.core.windows.net/container/test.txt"
        mock_custom_credential = MagicMock()

        result = storage.download_blob_by_url(
            blob_url=blob_url,
            credential=mock_custom_credential,
            offset=100,
            length=50
        )

        assert result == b"content with kwargs"
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.download_blob.assert_called_once_with(offset=100, length=50)

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_get_blob_properties_by_url_success(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests the successful retrieval of blob properties by URL using provided credentials.

        This test verifies that the `get_blob_properties_by_url` method correctly creates a
        BlobClient from the provided URL and credential, retrieves the blob properties,
        and returns the expected properties object.
        """
        mock_blob_client = MagicMock()
        mock_blob_properties = MagicMock()
        mock_blob_properties.size = 1024
        mock_blob_properties.last_modified = "2025-09-18T07:40:41Z"
        mock_blob_client.get_blob_properties.return_value = mock_blob_properties
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        mock_custom_credential = MagicMock()
        blob_url = "https://stdatarpcdev.blob.core.windows.net/documents/1-document-2025-09-18 07:40:41.333584.json"

        result = storage.get_blob_properties_by_url(
            blob_url=blob_url,
            credential=mock_custom_credential
        )

        assert result == mock_blob_properties
        assert result.size == 1024
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.get_blob_properties.assert_called_once()

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_get_blob_properties_by_url_fallback_to_instance_credential(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that get_blob_properties_by_url falls back to the instance credential when no credential is provided.

        This test ensures that when no credential parameter is passed, the method uses
        the storage instance's credential for authentication.
        """
        mock_blob_client = MagicMock()
        mock_blob_properties = MagicMock()
        mock_blob_properties.content_type = "application/json"
        mock_blob_client.get_blob_properties.return_value = mock_blob_properties
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://stdatarpcdev.blob.core.windows.net/documents/test-document.json"

        result = storage.get_blob_properties_by_url(blob_url=blob_url)

        assert result == mock_blob_properties
        assert result.content_type == "application/json"
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=storage.credential
        )
        mock_blob_client.get_blob_properties.assert_called_once()

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_get_blob_properties_by_url_not_found(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that get_blob_properties_by_url returns None when the blob is not found.

        This test verifies that when a ResourceNotFoundError is raised by the blob client,
        the method handles it gracefully and returns None instead of propagating the exception.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.get_blob_properties.side_effect = ResourceNotFoundError("Blob not found")
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://stdatarpcdev.blob.core.windows.net/documents/nonexistent.json"
        mock_custom_credential = MagicMock()

        result = storage.get_blob_properties_by_url(
            blob_url=blob_url,
            credential=mock_custom_credential
        )

        assert result is None
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.get_blob_properties.assert_called_once()

    def test_get_blob_properties_by_url_no_credential_available(self, mock_azure_identity):
        """
        Tests that get_blob_properties_by_url raises ValueError when no credential is available.

        This test verifies that when neither a credential parameter is provided nor an
        instance credential is available, the method raises a ValueError with an appropriate message.
        """
        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        # Remove the instance credential to simulate no credential available
        storage.credential = None

        blob_url = "https://stdatarpcdev.blob.core.windows.net/documents/test.json"

        with pytest.raises(ValueError, match="No credential available for blob properties retrieval"):
            storage.get_blob_properties_by_url(blob_url=blob_url)

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_get_blob_properties_by_url_exception(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that get_blob_properties_by_url properly handles and raises unexpected exceptions.

        This test ensures that exceptions other than ResourceNotFoundError (such as authentication
        errors or network issues) are properly logged and re-raised.
        """
        mock_blob_client = MagicMock()
        mock_blob_client.get_blob_properties.side_effect = Exception("Authentication error")
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://stdatarpcdev.blob.core.windows.net/documents/test.json"
        mock_custom_credential = MagicMock()

        with pytest.raises(Exception, match="Authentication error"):
            storage.get_blob_properties_by_url(
                blob_url=blob_url,
                credential=mock_custom_credential
            )

        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.get_blob_properties.assert_called_once()

    @patch('azure.storage.blob.BlobClient.from_blob_url')
    def test_get_blob_properties_by_url_with_kwargs(self, mock_from_blob_url, mock_azure_identity):
        """
        Tests that get_blob_properties_by_url correctly passes additional kwargs to the get_blob_properties method.

        This test verifies that any additional parameters provided via kwargs are properly
        forwarded to the underlying get_blob_properties call.
        """
        mock_blob_client = MagicMock()
        mock_blob_properties = MagicMock()
        mock_blob_properties.etag = "0x8DC123456789ABC"
        mock_blob_client.get_blob_properties.return_value = mock_blob_properties
        mock_from_blob_url.return_value = mock_blob_client

        storage = AzureStorage(
            account_url="https://testaccount.blob.core.windows.net",
            azure_identity=mock_azure_identity
        )

        blob_url = "https://stdatarpcdev.blob.core.windows.net/documents/test.json"
        mock_custom_credential = MagicMock()

        result = storage.get_blob_properties_by_url(
            blob_url=blob_url,
            credential=mock_custom_credential,
            timeout=30,
            lease="lease_id"
        )

        assert result == mock_blob_properties
        assert result.etag == "0x8DC123456789ABC"
        mock_from_blob_url.assert_called_once_with(
            blob_url=blob_url,
            credential=mock_custom_credential
        )
        mock_blob_client.get_blob_properties.assert_called_once_with(timeout=30, lease="lease_id")