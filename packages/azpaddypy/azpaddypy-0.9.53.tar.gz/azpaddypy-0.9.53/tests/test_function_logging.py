# Test Azure Function App logging integration
# Run: python -m pytest test_function_logging.py -v
#
# Example curl test for HTTP trigger:
# curl -X POST http://localhost:7071/api/test-function \
#   -H "Content-Type: application/json" \
#   -d '{"request_id": "123", "action": "test"}'

import json
import time
import os
import asyncio
from azpaddypy.mgmt.logging import create_function_logger


def load_local_settings():
    """Load Application Insights configuration from local.settings.json."""
    try:
        # Check current directory first, then parent
        settings_path = "local.settings.json"
        if not os.path.exists(settings_path):
            settings_path = os.path.join("..", "local.settings.json")
            if not os.path.exists(settings_path):
                print(
                    "Error: local.settings.json not found in current or parent directory"
                )
                return {}

        with open(settings_path, "r") as f:
            settings = json.load(f)
            values = settings.get("Values", {})
            print(f"Successfully loaded settings from {settings_path}")
            return values
    except Exception as e:
        print(f"Error loading local.settings.json: {e}")
        return {}


def test_function():
    """Sample function to demonstrate function tracing."""
    time.sleep(0.1)  # Simulate work
    # Function completes successfully without returning value for testing


# async def test_async_function():
#     """Sample async function to demonstrate async function tracing"""
#     await asyncio.sleep(0.1)  # Simulate some async work
#     return "async test result"


async def main():
    # Load Application Insights configuration
    settings = load_local_settings()
    connection_string = settings.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not connection_string:
        print(
            "Warning: No Application Insights connection string found in local.settings.json"
        )
        return

    print(f"Using Application Insights connection string: {connection_string[:30]}...")

    # Create function logger
    logger = create_function_logger(
        connection_string=connection_string,
        function_app_name="test-function-app",
        function_name="test-function",
        service_version="1.0.0",
    )

    # Set request correlation and context
    logger.set_correlation_id("test-correlation-123")
    context = logger.set_baggage("user_id", "12345")
    context = logger.set_baggage("request_type", "api_call")

    # Test all logging levels
    logger.debug("This is a debug message from function")
    logger.info("This is an info message from function")
    logger.warning("This is a warning message from function")
    logger.error("This is an error message from function")
    logger.critical("This is a critical message from function")

    # Test structured logging with extra data
    logger.info(
        "Function message with extra data",
        extra={"user_id": "123", "action": "test", "custom_field": "custom_value"},
    )

    # Test performance logging
    logger.log_function_execution(
        function_name="test_function",
        duration_ms=150.5,
        success=True,
        extra={"test_param": "test_value"},
    )

    # Test HTTP request logging
    logger.log_request(
        method="GET",
        url="http://test.com/api",
        status_code=200,
        duration_ms=250.75,
        extra={"request_id": "req-123"},
    )

    # Test dependency tracking
    logger.log_dependency(
        dependency_type="HTTP",
        name="external-api",
        command="GET /api/data",
        success=True,
        duration_ms=100.25,
        extra={"endpoint": "/api/data"},
    )

    # Test manual span creation
    with logger.create_span("test_span") as span:
        span.set_attribute("test.attribute", "test_value")
        logger.info("Message within span")

    # Test sync function tracing decorator
    @logger.trace_function(log_args=True, log_result=True)
    def process_user_request():
        # Get request context from baggage
        user_id = logger.get_baggage("user_id")
        request_type = logger.get_baggage("request_type")

        # Log request processing with context
        logger.info(
            f"Processing {request_type} request for user {user_id}",
            extra={
                "request_type": request_type,
                "user_id": user_id,
                "processing_stage": "start",
            },
        )

        # Simulate processing
        time.sleep(0.1)

        return {"status": "processed", "user_id": user_id}

    # Test async function tracing decorator
    @logger.trace_function(log_args=True, log_result=True)
    async def process_user_request_async():
        # Get request context from baggage
        user_id = logger.get_baggage("user_id")
        request_type = logger.get_baggage("request_type")

        # Log async request processing
        logger.info(
            f"Processing async {request_type} request for user {user_id}",
            extra={
                "request_type": request_type,
                "user_id": user_id,
                "processing_stage": "start",
                "is_async": True,
            },
        )

        # Simulate async processing
        await asyncio.sleep(0.1)

        return {"status": "processed_async", "user_id": user_id}

    # Execute traced functions
    sync_result = process_user_request()
    async_result = await process_user_request_async()

    # Test span events
    with logger.create_span("event_test_span") as span:
        logger.add_span_event("test_event", {"event_data": "test"})
        logger.info("Message with span event")

    # Test span status
    with logger.create_span("status_test_span") as span:
        from opentelemetry.trace import StatusCode

        logger.set_span_status(StatusCode.OK, "Operation successful")
        logger.info("Message with span status")

    # Test logging with span context
    logger.log_with_span(
        span_name="context_test_span",
        message="Message with span context",
        span_attributes={"context.attribute": "test"},
    )

    # Flush telemetry data
    logger.flush()


if __name__ == "__main__":
    asyncio.run(main())
