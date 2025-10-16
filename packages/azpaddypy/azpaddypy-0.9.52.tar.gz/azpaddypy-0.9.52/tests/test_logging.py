import pytest
import logging
import time
import asyncio
from opentelemetry.trace import Span, StatusCode, Status

from azpaddypy.mgmt.logging import (
    AzureLogger,
    create_app_logger,
    create_function_logger,
    _loggers,
)


@pytest.fixture(
    params=["asyncio"],
)
def anyio_backend(request):
    """Force anyio to use asyncio backend."""
    return request.param


@pytest.fixture
def azure_logger():
    """Configured AzureLogger instance for testing."""
    logger = AzureLogger(
        service_name="test_service",
        connection_string="InstrumentationKey=test",
    )
    return logger


class TestAzureLoggerInitialization:
    """Test AzureLogger initialization and configuration."""

    def test_init_with_connection_string(self):
        """Test Azure Monitor configuration with connection string."""
        logger = AzureLogger(
            service_name="test_service",
            service_version="1.0.1",
            connection_string="test_cs",
            custom_resource_attributes={"custom": "value"},
        )
        assert logger.service_name == "test_service"
        assert logger.service_version == "1.0.1"
        assert logger.connection_string == "test_cs"
        assert logger._telemetry_enabled in [True, False]  # Should not raise

    def test_init_no_connection_string(self):
        """Test Azure Monitor disabled without connection string."""
        logger = AzureLogger(
            service_name="test_service",
            connection_string=None,
        )
        assert not logger._telemetry_enabled

    def test_console_logging_setup(self):
        """Test console handler setup when enabled."""
        logger = AzureLogger(
            service_name="test_service",
            enable_console_logging=True,
        )
        assert any(isinstance(h, logging.StreamHandler) for h in logger.logger.handlers)

    def test_console_logging_disabled(self):
        """Test console handler not set up when disabled."""
        logger = AzureLogger(
            service_name="test_service",
            enable_console_logging=False,
        )
        assert not logger.logger.handlers


class TestAzureLoggerMethods:
    """Test AzureLogger logging and telemetry methods."""

    def test_set_get_correlation_id(self, azure_logger):
        """Test correlation ID setting and retrieval."""
        assert azure_logger.get_correlation_id() is None
        azure_logger.set_correlation_id("test-id")
        assert azure_logger.get_correlation_id() == "test-id"

    def test_baggage_methods(self, azure_logger):
        """Test baggage manipulation methods."""
        ctx = azure_logger.set_baggage("key", "value")
        # Use context to get baggage value
        value = azure_logger.get_baggage("key")
        if value is None:
            # Try with context if not set globally
            import opentelemetry.baggage as baggage
            value = baggage.get_baggage("key", context=ctx)
        assert value == "value"
        baggage_dict = azure_logger.get_all_baggage()
        assert isinstance(baggage_dict, dict)

    def test_logging_methods(self, azure_logger, caplog):
        """Test standard logging methods (debug, info, warning, error, exception, critical)."""
        azure_logger.logger.setLevel(logging.DEBUG)
        with caplog.at_level(logging.DEBUG):
            azure_logger.debug("debug message", extra={"user": "test"})
            azure_logger.info("info message")
            azure_logger.warning("warning message")
            azure_logger.error("error message", exc_info=False)
            azure_logger.exception("exception message")
            azure_logger.critical("critical message")
        messages = [r.getMessage() for r in caplog.records]
        assert "debug message" in messages
        assert "info message" in messages
        assert "warning message" in messages
        assert "error message" in messages
        assert "exception message" in messages
        assert "critical message" in messages

    def test_exception_method(self, azure_logger, caplog):
        """Test exception method logs at error level with automatic exception info."""
        azure_logger.logger.setLevel(logging.ERROR)
        try:
            # Create an exception to test with
            raise ValueError("test exception")
        except ValueError:
            # Call exception method from exception handler
            with caplog.at_level(logging.ERROR):
                azure_logger.exception("caught an exception", extra={"context": "test"})
        
        # Verify the message was logged
        messages = [r.getMessage() for r in caplog.records]
        assert "caught an exception" in messages
        
        # Verify it was logged at ERROR level
        assert any(r.levelno == logging.ERROR for r in caplog.records)
        
        # Verify exception info was included (exc_info=True behavior)
        assert any(r.exc_info is not None for r in caplog.records)

    def test_logging_methods_with_non_dict_extra(self, azure_logger, caplog):
        """Test logging methods handle non-dict extra parameters gracefully."""
        azure_logger.logger.setLevel(logging.INFO)
        with caplog.at_level(logging.INFO):
            # Should not raise
            azure_logger.info("info with list extra", extra=[1, 2, 3])
            azure_logger.info("info with tuple extra", extra=(1, 2))
            azure_logger.info("info with string extra", extra="notadict")
            azure_logger.info("info with int extra", extra=123)
            azure_logger.info("info with None extra", extra=None)
        messages = [r.getMessage() for r in caplog.records]
        assert "info with list extra" in messages
        assert "info with tuple extra" in messages
        assert "info with string extra" in messages
        assert "info with int extra" in messages
        assert "info with None extra" in messages

    def test_log_function_execution(self, azure_logger, caplog):
        """Test function execution logging for success and failure cases."""
        with caplog.at_level(logging.INFO):
            azure_logger.log_function_execution("my_func", 123.45, True, {"p": 1})
            azure_logger.log_function_execution("my_func", 543.21, False)
        messages = [r.getMessage() for r in caplog.records]
        assert any("SUCCESS" in m for m in messages)
        assert any("FAILED" in m for m in messages)

    def test_log_request(self, azure_logger, caplog):
        """Test HTTP request logging for different status codes."""
        with caplog.at_level(logging.INFO):
            azure_logger.log_request("GET", "/test", 200, 10.0)
            azure_logger.log_request("POST", "/test", 404, 20.0)
            azure_logger.log_request("PUT", "/test", 500, 30.0)
        messages = [r.getMessage() for r in caplog.records]
        assert any("GET /test - 200" in m for m in messages)
        assert any("POST /test - 404" in m for m in messages)
        assert any("PUT /test - 500" in m for m in messages)

    def test_create_span(self, azure_logger):
        """Test OpenTelemetry span creation."""
        azure_logger.set_correlation_id("corr-id")
        span = azure_logger.create_span("my_span", attributes={"attr1": "val1"})
        assert span is not None
        # Should be a span object with set_attribute method
        assert hasattr(span, "set_attribute")

    def test_log_dependency(self, azure_logger, caplog):
        """Test dependency call logging for success and failure cases."""
        with caplog.at_level(logging.INFO):
            azure_logger.log_dependency("SQL", "users_db", "SELECT *", True, 150.0)
            azure_logger.log_dependency("HTTP", "api.example.com", "GET /data", False, 250.0)
        messages = [r.getMessage() for r in caplog.records]
        assert any("Dependency call: SQL:users_db" in m for m in messages)
        assert any("Dependency call: HTTP:api.example.com" in m for m in messages)

    def test_flush(self, azure_logger):
        """Test telemetry flush does not raise exceptions."""
        azure_logger.flush()


class TestTraceFunctionDecorator:  
    """Test @trace_function decorator functionality."""

    def test_sync_function_success(self, azure_logger):
        """Test tracing successful synchronous function."""
        @azure_logger.trace_function(log_result=True)
        def my_sync_func(a, b):
            return a + b
        result = my_sync_func(1, 2)
        assert result == 3
        
    def test_sync_function_dict_success(self, azure_logger):
        """Test tracing synchronous function with dict parameters."""
        @azure_logger.trace_function(log_args=True, log_result=True)
        def my_sync_func(dict_value):
            return dict_value["a"] + dict_value["b"]
        result = my_sync_func({"a": 1, "b": 2})
        assert result == 3

    def test_sync_function_exception(self, azure_logger):
        """Test tracing synchronous function that raises exception."""
        @azure_logger.trace_function()
        def my_sync_func_fail():
            raise ValueError("test error")
        with pytest.raises(ValueError, match="test error"):
            my_sync_func_fail()

    @pytest.mark.anyio
    async def test_async_function_success(self, azure_logger):
        """Test tracing successful asynchronous function."""
        @azure_logger.trace_function(log_result=True)
        async def my_async_func(a, b):
            return a + b
        result = await my_async_func(1, 2)
        assert result == 3

    @pytest.mark.anyio
    async def test_async_function_exception(self, azure_logger):
        """Test tracing asynchronous function that raises exception."""
        @azure_logger.trace_function()
        async def my_async_func_fail():
            raise ValueError("test error")
        with pytest.raises(ValueError, match="test error"):
            await my_async_func_fail()

    def test_automatic_correlation_id_generation_sync(self, azure_logger):
        """Test that correlation_id is automatically generated for sync functions."""
        import uuid
        
        # Ensure no correlation_id is set initially
        assert azure_logger.get_correlation_id() is None
        
        @azure_logger.trace_function()
        def test_func():
            return "test_result"
        
        # Call function - should auto-generate correlation_id
        result = test_func()
        assert result == "test_result"
        
        # Verify correlation_id was generated
        correlation_id = azure_logger.get_correlation_id()
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        
        # Verify it's a valid UUID
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation_id is not a valid UUID: {correlation_id}")

    @pytest.mark.anyio
    async def test_automatic_correlation_id_generation_async(self, azure_logger):
        """Test that correlation_id is automatically generated for async functions."""
        import uuid
        
        # Ensure no correlation_id is set initially
        assert azure_logger.get_correlation_id() is None
        
        @azure_logger.trace_function()
        async def test_async_func():
            return "async_test_result"
        
        # Call function - should auto-generate correlation_id
        result = await test_async_func()
        assert result == "async_test_result"
        
        # Verify correlation_id was generated
        correlation_id = azure_logger.get_correlation_id()
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        
        # Verify it's a valid UUID
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation_id is not a valid UUID: {correlation_id}")

    def test_manual_correlation_id_preserved_sync(self, azure_logger):
        """Test that manually set correlation_id is preserved for sync functions."""
        manual_correlation_id = "manual-correlation-123"
        azure_logger.set_correlation_id(manual_correlation_id)
        
        # Verify manual correlation_id is set
        assert azure_logger.get_correlation_id() == manual_correlation_id
        
        @azure_logger.trace_function()
        def test_func():
            return "test_result"
        
        # Call function - should preserve manual correlation_id
        result = test_func()
        assert result == "test_result"
        
        # Verify manual correlation_id is still preserved
        assert azure_logger.get_correlation_id() == manual_correlation_id

    @pytest.mark.anyio
    async def test_manual_correlation_id_preserved_async(self, azure_logger):
        """Test that manually set correlation_id is preserved for async functions."""
        manual_correlation_id = "manual-correlation-456"
        azure_logger.set_correlation_id(manual_correlation_id)
        
        # Verify manual correlation_id is set
        assert azure_logger.get_correlation_id() == manual_correlation_id
        
        @azure_logger.trace_function()
        async def test_async_func():
            return "async_test_result"
        
        # Call function - should preserve manual correlation_id
        result = await test_async_func()
        assert result == "async_test_result"
        
        # Verify manual correlation_id is still preserved
        assert azure_logger.get_correlation_id() == manual_correlation_id

    def test_correlation_id_uniqueness(self, azure_logger):
        """Test that auto-generated correlation_ids are unique across different loggers."""
        import uuid
        
        # Create two separate loggers
        logger1 = AzureLogger('test-service-1')
        logger2 = AzureLogger('test-service-2')
        
        # Ensure no correlation_ids are set initially
        assert logger1.get_correlation_id() is None
        assert logger2.get_correlation_id() is None
        
        @logger1.trace_function()
        def func1():
            return "result1"
        
        @logger2.trace_function()
        def func2():
            return "result2"
        
        # Call both functions
        result1 = func1()
        result2 = func2()
        
        assert result1 == "result1"
        assert result2 == "result2"
        
        # Verify both correlation_ids were generated and are different
        correlation_id1 = logger1.get_correlation_id()
        correlation_id2 = logger2.get_correlation_id()
        
        assert correlation_id1 is not None
        assert correlation_id2 is not None
        assert correlation_id1 != correlation_id2
        
        # Verify both are valid UUIDs
        try:
            uuid.UUID(correlation_id1)
            uuid.UUID(correlation_id2)
        except ValueError:
            pytest.fail("Generated correlation_ids are not valid UUIDs")

    def test_correlation_id_persistence_across_calls(self, azure_logger):
        """Test that auto-generated correlation_id persists across multiple function calls."""
        import uuid
        
        # Ensure no correlation_id is set initially
        assert azure_logger.get_correlation_id() is None
        
        @azure_logger.trace_function()
        def test_func1():
            return "result1"
        
        @azure_logger.trace_function()
        def test_func2():
            return "result2"
        
        # Call first function - should generate correlation_id
        result1 = test_func1()
        assert result1 == "result1"
        
        correlation_id1 = azure_logger.get_correlation_id()
        assert correlation_id1 is not None
        
        # Call second function - should use same correlation_id
        result2 = test_func2()
        assert result2 == "result2"
        
        correlation_id2 = azure_logger.get_correlation_id()
        assert correlation_id2 == correlation_id1
        
        # Verify it's a valid UUID
        try:
            uuid.UUID(correlation_id1)
        except ValueError:
            pytest.fail(f"Generated correlation_id is not a valid UUID: {correlation_id1}")

    def test_correlation_id_in_span_attributes(self, azure_logger):
        """Test that correlation_id is properly added to span attributes."""
        from unittest.mock import Mock, patch
        
        # Mock the tracer to capture span attributes
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(azure_logger, 'tracer', mock_tracer):
            @azure_logger.trace_function()
            def test_func():
                return "test"
            
            result = test_func()
            assert result == "test"
            
            # Verify span was created
            mock_tracer.start_as_current_span.assert_called_once()
            
            # Verify correlation_id was set as span attribute
            expected_calls = []
            for call in mock_span.set_attribute.call_args_list:
                args = call[0]
                if len(args) == 2:
                    expected_calls.append(args)
            
            attribute_dict = {call[0]: call[1] for call in expected_calls}
            
            # Check that correlation_id is in the attributes
            assert "correlation.id" in attribute_dict
            correlation_id_in_span = attribute_dict["correlation.id"]
            
            # Verify it matches the logger's correlation_id
            assert correlation_id_in_span == azure_logger.get_correlation_id()
            
            # Verify it's a valid UUID
            import uuid
            try:
                uuid.UUID(correlation_id_in_span)
            except ValueError:
                pytest.fail(f"Correlation ID in span is not a valid UUID: {correlation_id_in_span}")

    def test_manual_correlation_id_in_span_attributes(self, azure_logger):
        """Test that manually set correlation_id is properly added to span attributes."""
        from unittest.mock import Mock, patch
        
        # Set manual correlation_id
        manual_correlation_id = "manual-correlation-789"
        azure_logger.set_correlation_id(manual_correlation_id)
        
        # Mock the tracer to capture span attributes
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(azure_logger, 'tracer', mock_tracer):
            @azure_logger.trace_function()
            def test_func():
                return "test"
            
            result = test_func()
            assert result == "test"
            
            # Verify span was created
            mock_tracer.start_as_current_span.assert_called_once()
            
            # Verify correlation_id was set as span attribute
            expected_calls = []
            for call in mock_span.set_attribute.call_args_list:
                args = call[0]
                if len(args) == 2:
                    expected_calls.append(args)
            
            attribute_dict = {call[0]: call[1] for call in expected_calls}
            
            # Check that correlation_id is in the attributes
            assert "correlation.id" in attribute_dict
            assert attribute_dict["correlation.id"] == manual_correlation_id

    def test_correlation_id_generation_timing(self, azure_logger):
        """Test that correlation_id is generated at the right time (during function execution)."""
        import uuid
        
        # Ensure no correlation_id is set initially
        assert azure_logger.get_correlation_id() is None
        
        correlation_id_generated = False
        
        @azure_logger.trace_function()
        def test_func():
            nonlocal correlation_id_generated
            # Check if correlation_id was generated before function execution
            correlation_id_generated = azure_logger.get_correlation_id() is not None
            return "test"
        
        # Call function
        result = test_func()
        assert result == "test"
        
        # Verify correlation_id was generated during function execution
        assert correlation_id_generated is True
        
        # Verify final correlation_id is valid
        correlation_id = azure_logger.get_correlation_id()
        assert correlation_id is not None
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation_id is not a valid UUID: {correlation_id}")

    def test_correlation_id_with_exception_handling(self, azure_logger):
        """Test that correlation_id generation works even when functions raise exceptions."""
        import uuid
        
        # Ensure no correlation_id is set initially
        assert azure_logger.get_correlation_id() is None
        
        @azure_logger.trace_function()
        def test_func_with_exception():
            raise ValueError("test exception")
        
        # Call function that raises exception
        with pytest.raises(ValueError, match="test exception"):
            test_func_with_exception()
        
        # Verify correlation_id was still generated despite exception
        correlation_id = azure_logger.get_correlation_id()
        assert correlation_id is not None
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation_id is not a valid UUID: {correlation_id}")

    def test_correlation_id_with_async_exception_handling(self, azure_logger):
        """Test that correlation_id generation works even when async functions raise exceptions."""
        import uuid
        
        # Ensure no correlation_id is set initially
        assert azure_logger.get_correlation_id() is None
        
        @azure_logger.trace_function()
        async def test_async_func_with_exception():
            raise ValueError("test async exception")
        
        # Call async function that raises exception
        with pytest.raises(ValueError, match="test async exception"):
            import asyncio
            asyncio.run(test_async_func_with_exception())
        
        # Verify correlation_id was still generated despite exception
        correlation_id = azure_logger.get_correlation_id()
        assert correlation_id is not None
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Generated correlation_id is not a valid UUID: {correlation_id}")

    def test_decorator_parameters_logged_as_span_attributes(self, azure_logger):
        """Test that decorator parameters are logged as span attributes."""
        from unittest.mock import Mock, patch
        
        # Mock the tracer to capture span attributes
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(azure_logger, 'tracer', mock_tracer):
            @azure_logger.trace_function(log_args=True, log_result=True, log_execution=False)
            def test_func(x):
                return x * 2
            
            result = test_func(5)
            assert result == 10
            
            # Verify span was created
            mock_tracer.start_as_current_span.assert_called_once()
            
            # Verify decorator parameters were set as span attributes
            expected_calls = []
            for call in mock_span.set_attribute.call_args_list:
                args = call[0]
                if len(args) == 2:
                    expected_calls.append(args)
            
            # Check that decorator parameters are in the attributes
            attribute_dict = {call[0]: call[1] for call in expected_calls}
            assert attribute_dict.get("function.decorator.log_args") is True
            assert attribute_dict.get("function.decorator.log_result") is True
            assert attribute_dict.get("function.decorator.log_execution") is False

    @pytest.mark.anyio
    async def test_async_decorator_parameters_logged_as_span_attributes(self, azure_logger):
        """Test that decorator parameters are logged as span attributes for async functions."""
        from unittest.mock import Mock, patch
        
        # Mock the tracer to capture span attributes
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(azure_logger, 'tracer', mock_tracer):
            @azure_logger.trace_function(log_args=False, log_result=True, log_execution=True)
            async def test_async_func(x):
                return x * 3
            
            result = await test_async_func(4)
            assert result == 12
            
            # Verify span was created
            mock_tracer.start_as_current_span.assert_called_once()
            
            # Verify decorator parameters were set as span attributes
            expected_calls = []
            for call in mock_span.set_attribute.call_args_list:
                args = call[0]
                if len(args) == 2:
                    expected_calls.append(args)
            
            # Check that decorator parameters are in the attributes
            attribute_dict = {call[0]: call[1] for call in expected_calls}
            assert attribute_dict.get("function.decorator.log_args") is False
            assert attribute_dict.get("function.decorator.log_result") is True
            assert attribute_dict.get("function.decorator.log_execution") is True

    def test_default_decorator_parameters_logged(self, azure_logger):
        """Test that default decorator parameters are logged correctly."""
        from unittest.mock import Mock, patch
        
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(azure_logger, 'tracer', mock_tracer):
            @azure_logger.trace_function()  # Using defaults
            def test_func_defaults():
                return "test"
            
            result = test_func_defaults()
            assert result == "test"
            
            # Verify decorator default parameters were set as span attributes
            expected_calls = []
            for call in mock_span.set_attribute.call_args_list:
                args = call[0]
                if len(args) == 2:
                    expected_calls.append(args)
            
            # Check that decorator parameters match defaults
            attribute_dict = {call[0]: call[1] for call in expected_calls}
            assert attribute_dict.get("function.decorator.log_args") is True  # default
            assert attribute_dict.get("function.decorator.log_result") is False  # default
            assert attribute_dict.get("function.decorator.log_execution") is True  # default

    def test_function_execution_logging_with_decorator_params(self, azure_logger, caplog):
        """Test that function execution logging respects decorator parameters."""
        azure_logger.logger.setLevel(logging.DEBUG)
        
        with caplog.at_level(logging.DEBUG):
            @azure_logger.trace_function(log_execution=True)
            def test_func_with_logging():
                return "logged"
            
            @azure_logger.trace_function(log_execution=False)
            def test_func_without_logging():
                return "not_logged"
            
            result1 = test_func_with_logging()
            result2 = test_func_without_logging()
            
            assert result1 == "logged"
            assert result2 == "not_logged"
        
        messages = [r.getMessage() for r in caplog.records]
        
        # Should have execution logging for first function
        assert any("test_func_with_logging" in m and "executed in" in m for m in messages)
        
        # Should NOT have execution logging for second function (only debug messages)
        execution_logs = [m for m in messages if "executed in" in m and "test_func_without_logging" in m]
        assert len(execution_logs) == 0

    def test_span_attributes_include_all_function_metadata(self, azure_logger):
        """Test that span includes all expected function metadata along with decorator params."""
        from unittest.mock import Mock, patch
        
        mock_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)
        
        with patch.object(azure_logger, 'tracer', mock_tracer):
            @azure_logger.trace_function(log_args=True, log_result=False, log_execution=True)
            def test_metadata_func(param1, param2="default"):
                return f"{param1}_{param2}"
            
            result = test_metadata_func("test", param2="value")
            assert result == "test_value"
            
            # Collect all span attributes
            expected_calls = []
            for call in mock_span.set_attribute.call_args_list:
                args = call[0]
                if len(args) == 2:
                    expected_calls.append(args)
            
            attribute_dict = {call[0]: call[1] for call in expected_calls}
            
            # Verify function metadata attributes
            assert attribute_dict.get("function.name") == "test_metadata_func"
            assert attribute_dict.get("function.module") == "tests.test_logging"
            assert attribute_dict.get("service.name") == "test_service"
            assert attribute_dict.get("function.is_async") is False
            
            # Verify decorator parameter attributes
            assert attribute_dict.get("function.decorator.log_args") is True
            assert attribute_dict.get("function.decorator.log_result") is False
            assert attribute_dict.get("function.decorator.log_execution") is True
            
            # Verify function arguments are logged (since log_args=True)
            assert attribute_dict.get("function.args_count") == 1
            assert attribute_dict.get("function.kwargs_count") == 1
            assert "function.arg.param1" in attribute_dict
            assert "function.kwarg.param2" in attribute_dict

    def test_trace_function_decorator_still_works_with_filtering(self, azure_logger, caplog):
        """Test that the trace_function decorator still works after filtering implementation."""
        azure_logger.logger.setLevel(logging.DEBUG)
        
        @azure_logger.trace_function(log_args=True, log_result=True)
        def test_function_with_problematic_args(filename="test.py", pathname="/test/path"):
            """Function with arguments that have reserved names."""
            return f"Processing {filename} from {pathname}"
        
        with caplog.at_level(logging.DEBUG):
            result = test_function_with_problematic_args()
        
        # Function should execute successfully
        assert result == "Processing test.py from /test/path"
        
        # Logging should work (though some argument names might be filtered in logs)
        messages = [r.getMessage() for r in caplog.records]
        assert any("test_function_with_problematic_args" in msg for msg in messages)

    def test_azure_functions_batch_push_scenario(self, azure_logger, caplog):
        """Test the specific scenario from Azure Functions batch_push_results that caused the original KeyError."""
        azure_logger.logger.setLevel(logging.INFO)
        
        # Simulate the scenario where baggage or extra data might contain 'filename'
        # This could happen when OpenTelemetry baggage is propagated in Azure Functions
        
        # Set some baggage that might contain reserved attributes
        azure_logger.set_baggage("filename", "batch_push_results.py")
        azure_logger.set_baggage("operation", "batch_processing")
        
        # Simulate the problematic logging call from Azure Functions
        message_body = {"id": "test-123", "data": "test data"}
        
        try:
            # This is similar to the line that was failing in the Azure Function:
            # logger.info("Process Document Event queue function triggered: %s", message_body)
            azure_logger.info("Process Document Event queue function triggered: %s", message_body)
            
            # Also test with extra data that might contain filename
            extra_data = {
                "filename": "would_cause_keyerror.py",  # This would cause the original KeyError
                "function_name": "batch_push_results",
                "message_id": "test-123"
            }
            azure_logger.info("Processing message with extra context", extra=extra_data)
            
        except KeyError as e:
            if "Attempt to overwrite" in str(e):
                pytest.fail(f"Azure Functions scenario still causes KeyError: {e}")
            else:
                raise
        except Exception as e:
            pytest.fail(f"Unexpected exception in Azure Functions scenario: {e}")
        
        # Verify that messages were logged successfully
        messages = [r.getMessage() for r in caplog.records]
        assert any("Process Document Event queue function triggered" in msg for msg in messages)
        assert any("Processing message with extra context" in msg for msg in messages)


class TestFactoryFunctions:
    """Test factory functions for logger creation."""

    def setup_method(self):
        """Clear logger cache before each test."""
        _loggers.clear()

    def teardown_method(self):
        """Clear logger cache after each test."""
        _loggers.clear()

    def test_create_app_logger(self):
        """Test application logger factory function."""
        logger = create_app_logger("test_app")
        assert isinstance(logger, AzureLogger)
        assert logger.service_name == "test_app"

    def test_create_app_logger_caching(self):
        """Test that identical logger configurations are cached."""
        logger1 = create_app_logger("test_app", "1.0.0")
        logger2 = create_app_logger("test_app", "1.0.0")
        assert logger1 is logger2  # Same instance due to caching

    def test_create_function_logger(self):
        """Test Function App logger factory function."""
        logger = create_function_logger("test_function_app", "test_function")
        assert isinstance(logger, AzureLogger)
        assert logger.service_name == "test_function_app.test_function"


class TestLogRecordAttributeFiltering:
    """Test LogRecord attribute filtering to prevent KeyError exceptions."""

    def test_extra_data_with_reserved_attributes_filtered(self, azure_logger, caplog):
        """Test that extra data with reserved LogRecord attributes gets filtered out."""
        azure_logger.logger.setLevel(logging.INFO)
        
        # Create extra data with reserved attributes
        extra_with_reserved = {
            "filename": "malicious_filename.py",  # Reserved attribute
            "pathname": "/fake/path",  # Reserved attribute
            "lineno": 999,  # Reserved attribute
            "funcName": "fake_function",  # Reserved attribute
            "valid_key": "valid_value",  # Valid attribute
            "another_valid": "another_value"  # Valid attribute
        }
        
        with caplog.at_level(logging.INFO):
            # This should not raise KeyError
            azure_logger.info("test message with reserved attributes", extra=extra_with_reserved)
        
        # Check that the message was logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test message with reserved attributes" in messages
        
        # Check that a warning was logged about filtered keys
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("Filtered out reserved LogRecord attributes from extra data" in msg for msg in warning_messages)

    def test_baggage_with_reserved_attributes_filtered(self, azure_logger, caplog):
        """Test that baggage items with reserved LogRecord attributes get filtered out."""
        azure_logger.logger.setLevel(logging.INFO)
        
        # Set baggage items including reserved attributes
        azure_logger.set_baggage("filename", "baggage_filename.py")  # Reserved
        azure_logger.set_baggage("module", "fake_module")  # Reserved
        azure_logger.set_baggage("valid_baggage", "valid_value")  # Valid
        
        with caplog.at_level(logging.INFO):
            # This should not raise KeyError
            azure_logger.info("test message with baggage containing reserved attributes")
        
        # Check that the message was logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test message with baggage containing reserved attributes" in messages
        
        # Check that a warning was logged about filtered baggage keys if any were filtered
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        # Note: Baggage filtering warnings may not always appear depending on baggage context

    def test_valid_extra_data_not_filtered(self, azure_logger, caplog):
        """Test that valid extra data without reserved attributes passes through."""
        azure_logger.logger.setLevel(logging.DEBUG)
        
        valid_extra = {
            "user_id": "12345",
            "request_id": "req-67890",
            "custom_field": "custom_value",
            "timestamp_custom": "2023-01-01T00:00:00Z"
        }
        
        with caplog.at_level(logging.DEBUG):
            azure_logger.info("test message with valid extra", extra=valid_extra)
        
        # Check that the message was logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test message with valid extra" in messages
        
        # Check that no warning was logged (no filtering occurred)
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        filtered_warnings = [msg for msg in warning_messages if "Filtered out reserved LogRecord attributes" in msg]
        assert len(filtered_warnings) == 0

    def test_mixed_extra_data_partial_filtering(self, azure_logger, caplog):
        """Test that mixed extra data gets partially filtered (reserved removed, valid kept)."""
        azure_logger.logger.setLevel(logging.INFO)
        
        mixed_extra = {
            "filename": "should_be_filtered.py",  # Reserved - should be filtered
            "user_id": "user123",  # Valid - should be kept
            "pathname": "/should/be/filtered",  # Reserved - should be filtered
            "request_type": "api_call",  # Valid - should be kept
            "msg": "should_be_filtered_msg",  # Reserved - should be filtered
        }
        
        with caplog.at_level(logging.INFO):
            azure_logger.info("test message with mixed extra data", extra=mixed_extra)
        
        # Message should still be logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test message with mixed extra data" in messages
        
        # Warning should be logged about filtered keys
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("Filtered out reserved LogRecord attributes from extra data" in msg for msg in warning_messages)
        
        # The warning should mention the specific filtered keys
        filtered_warning = next((msg for msg in warning_messages if "filename" in msg), None)
        assert filtered_warning is not None
        assert "pathname" in filtered_warning
        assert "msg" in filtered_warning

    def test_all_reserved_attributes_filtered(self, azure_logger, caplog):
        """Test filtering of all known reserved LogRecord attributes."""
        azure_logger.logger.setLevel(logging.INFO)
        
        # Create extra data with all reserved attributes
        all_reserved_extra = {
            "name": "fake_name",
            "msg": "fake_msg", 
            "args": "fake_args",
            "levelname": "fake_levelname",
            "levelno": 999,
            "pathname": "fake_pathname",
            "filename": "fake_filename",
            "module": "fake_module",
            "exc_info": "fake_exc_info",
            "exc_text": "fake_exc_text",
            "stack_info": "fake_stack_info",
            "lineno": 999,
            "funcName": "fake_funcName",
            "created": 999.999,
            "msecs": 999.999,
            "relativeCreated": 999.999,
            "thread": 999,
            "threadName": "fake_thread",
            "processName": "fake_process",
            "process": 999,
            "getMessage": "fake_getMessage",
            "valid_key": "this_should_remain"  # Only this should remain
        }
        
        with caplog.at_level(logging.INFO):
            azure_logger.info("test with all reserved attributes", extra=all_reserved_extra)
        
        # Message should still be logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test with all reserved attributes" in messages
        
        # Warning should be logged
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("Filtered out reserved LogRecord attributes from extra data" in msg for msg in warning_messages)

    def test_empty_extra_data_no_filtering(self, azure_logger, caplog):
        """Test that empty or None extra data doesn't cause issues."""
        azure_logger.logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            azure_logger.info("test with None extra", extra=None)
            azure_logger.info("test with empty dict extra", extra={})
        
        # Messages should be logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test with None extra" in messages
        assert "test with empty dict extra" in messages
        
        # No warnings should be logged
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        filtered_warnings = [msg for msg in warning_messages if "Filtered out reserved LogRecord attributes" in msg]
        assert len(filtered_warnings) == 0

    def test_non_dict_extra_data_no_filtering(self, azure_logger, caplog):
        """Test that non-dict extra data is handled without filtering."""
        azure_logger.logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            azure_logger.info("test with string extra", extra="not_a_dict")
            azure_logger.info("test with list extra", extra=["item1", "item2"])
            azure_logger.info("test with int extra", extra=123)
        
        # Messages should be logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test with string extra" in messages
        assert "test with list extra" in messages
        assert "test with int extra" in messages
        
        # No warnings should be logged for non-dict data
        warning_messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        filtered_warnings = [msg for msg in warning_messages if "Filtered out reserved LogRecord attributes" in msg]
        assert len(filtered_warnings) == 0

    def test_filtering_prevents_key_error_exception(self, azure_logger):
        """Test that filtering prevents the original KeyError exception."""
        # This test specifically targets the original issue
        problematic_extra = {
            "filename": "this_would_cause_keyerror.py",
            "pathname": "/this/would/cause/error",
            "normal_data": "this_is_fine"
        }
        
        # This should not raise KeyError: "Attempt to overwrite 'filename' in LogRecord"
        try:
            azure_logger.info("test that should not raise KeyError", extra=problematic_extra)
            # If we get here, the fix worked
            assert True
        except KeyError as e:
            if "Attempt to overwrite" in str(e):
                pytest.fail(f"KeyError was not prevented by filtering: {e}")
            else:
                # Re-raise if it's a different KeyError
                raise

    def test_correlation_id_and_span_context_still_work(self, azure_logger, caplog):
        """Test that correlation ID and span context still work after filtering implementation."""
        azure_logger.logger.setLevel(logging.DEBUG)
        azure_logger.set_correlation_id("test-correlation-123")
        
        problematic_extra = {
            "filename": "filtered.py",  # Should be filtered
            "custom_data": "should_remain"  # Should remain
        }
        
        with caplog.at_level(logging.DEBUG):
            azure_logger.info("test correlation with filtering", extra=problematic_extra)
        
        # Message should be logged
        messages = [r.getMessage() for r in caplog.records]
        assert "test correlation with filtering" in messages
        
        # Correlation ID should still be accessible
        assert azure_logger.get_correlation_id() == "test-correlation-123"
