import logging
import os
import functools
import time
import asyncio
import uuid
from typing import Optional, Dict, Any, Union, Callable
from datetime import datetime
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry import baggage
from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource


class AzureLogger:
    """Azure-integrated logger with OpenTelemetry distributed tracing.

    Provides comprehensive logging with Azure Monitor integration, correlation
    tracking, baggage propagation, and automated function tracing for Azure
    applications with seamless local development support.

    CLOUD ROLE NAME INTEGRATION:
    The service_name parameter automatically sets the cloud role name for 
    Application Insights. When multiple services emit telemetry to the same 
    Application Insights resource, each service will appear as a separate 
    node on the Application Map, enabling proper service topology visualization.

    CORRELATION ID AUTOMATION:
    The trace_function decorator automatically generates UUID4 correlation IDs
    when none are manually set, ensuring consistent distributed tracing across
    all function calls without requiring manual configuration.

    Supports all standard logging levels (debug, info, warning, error, exception, 
    critical) with enhanced context including trace IDs, correlation IDs, and 
    baggage propagation.

    Attributes:
        service_name: Service identifier for telemetry and cloud role name
        service_version: Service version for context
        connection_string: Application Insights connection string
        logger: Python logger instance
        tracer: OpenTelemetry tracer for spans
    """

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        connection_string: Optional[str] = None,
        log_level: int = logging.INFO,
        enable_console_logging: bool = True,
        custom_resource_attributes: Optional[Dict[str, str]] = None,
        instrumentation_options: Optional[Dict[str, Any]] = None,
        cloud_role_name: Optional[str] = None,
    ):
        """Initialize Azure Logger with OpenTelemetry tracing.

        The service_name parameter automatically sets the cloud role name for 
        Application Insights Application Map visualization. When multiple services
        emit telemetry to the same Application Insights resource, each service
        will appear as a separate node on the Application Map.

        Args:
            service_name: Service identifier for telemetry and cloud role name
            service_version: Service version for metadata
            connection_string: Application Insights connection string
            log_level: Python logging level (default: INFO)
            enable_console_logging: Enable console output for local development
            custom_resource_attributes: Additional OpenTelemetry resource attributes
            instrumentation_options: Azure Monitor instrumentation options
            cloud_role_name: Override cloud role name (defaults to service_name)
        """
        self.service_name = service_name
        self.service_version = service_version
        self.connection_string = connection_string or os.getenv(
            "APPLICATIONINSIGHTS_CONNECTION_STRING"
        )

        # Use explicit cloud role name or default to service name
        effective_cloud_role_name = cloud_role_name or service_name
        self.cloud_role_name = effective_cloud_role_name

        # Configure resource attributes according to Azure Monitor OpenTelemetry best practices
        # NOTE: Azure Monitor cloud role name uses service.namespace + service.name, 
        # or falls back to service.name if service.namespace isn't set
        resource_attributes = {
            "service.name": effective_cloud_role_name,
            "service.version": service_version,
        }

        if custom_resource_attributes:
            resource_attributes.update(custom_resource_attributes)

        # Configure Azure Monitor if connection string available
        if self.connection_string:
            try:
                # Create a Resource with the attributes to ensure they're properly applied
                # This ensures Azure Monitor correctly maps service.name to cloud role name
                resource = Resource.create(resource_attributes)
                
                configure_azure_monitor(
                    connection_string=self.connection_string,
                    resource=resource,
                    enable_live_metrics=True,
                    instrumentation_options=instrumentation_options,
                )
                self._telemetry_enabled = True
            except Exception as e:
                print(f"Warning: Failed to configure Azure Monitor: {e}")
                self._telemetry_enabled = False
        else:
            self._telemetry_enabled = False
            print(
                "Warning: No Application Insights connection string found. Telemetry disabled."
            )

        # Configure Python logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()

        if enable_console_logging:
            self._setup_console_handler()

        # Initialize OpenTelemetry tracer and correlation context
        self.tracer = trace.get_tracer(__name__)
        self._correlation_id = None
        

        self.info(
            f"Azure Logger initialized for service '{service_name}' v{service_version} "
            f"(cloud role: '{effective_cloud_role_name}')"
        )

    def _setup_console_handler(self):
        """Configure console handler for local development."""
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request/transaction tracking.

        Manually sets the correlation ID that will be used for all subsequent
        tracing operations. This value takes precedence over auto-generated
        correlation IDs in the trace_function decorator.

        Args:
            correlation_id: Unique identifier for transaction correlation

        Note:
            If not set manually, the trace_function decorator will automatically
            generate a UUID4 correlation_id on first use.
        """
        self._correlation_id = correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID.

        Returns the currently active correlation ID, whether manually set
        or automatically generated by the trace_function decorator.

        Returns:
            Current correlation ID if set (manual or auto-generated), otherwise None
        """
        return self._correlation_id

    def set_baggage(self, key: str, value: str) -> Context:
        """Set baggage item in OpenTelemetry context.

        Args:
            key: Baggage key
            value: Baggage value

        Returns:
            Updated context with baggage item
        """
        return baggage.set_baggage(key, value)

    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage item from current context.

        Args:
            key: Baggage key

        Returns:
            Baggage value if exists, otherwise None
        """
        return baggage.get_baggage(key)

    def get_all_baggage(self) -> Dict[str, str]:
        """Get all baggage items from current context.

        Returns:
            Dictionary of all baggage items
        """
        return dict(baggage.get_all())

    def _enhance_extra(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enrich log records with contextual information.

        Args:
            extra: Optional custom data dictionary

        Returns:
            Enhanced dictionary with service context, correlation ID, trace
            context, and baggage items, with built-in LogRecord attributes filtered out
        """
        # Define built-in LogRecord attributes that should not be overwritten
        reserved_attributes = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'getMessage'
        }
        
        enhanced_extra = {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self._correlation_id:
            enhanced_extra["correlation_id"] = self._correlation_id

        # Add span context if available
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            enhanced_extra["trace_id"] = format(span_context.trace_id, "032x")
            enhanced_extra["span_id"] = format(span_context.span_id, "016x")

        # Add baggage items, filtering out any reserved attribute names
        baggage_items = self.get_all_baggage()
        if baggage_items:
            # Filter baggage items to avoid conflicts with LogRecord attributes
            filtered_baggage = {k: v for k, v in baggage_items.items() if k not in reserved_attributes}
            if filtered_baggage:
                enhanced_extra["baggage"] = filtered_baggage
            
            # Log warning if any baggage keys were filtered out
            filtered_baggage_keys = set(baggage_items.keys()) - set(filtered_baggage.keys())
            if filtered_baggage_keys:
                # Use the base logger directly to avoid infinite recursion
                self.logger.warning(
                    f"Filtered out reserved LogRecord attributes from baggage: {filtered_baggage_keys}"
                )

        if isinstance(extra, dict):
            # Filter out any keys that would conflict with built-in LogRecord attributes
            filtered_extra = {k: v for k, v in extra.items() if k not in reserved_attributes}
            enhanced_extra.update(filtered_extra)
            
            # Log warning if any keys were filtered out
            filtered_keys = set(extra.keys()) - set(filtered_extra.keys())
            if filtered_keys:
                # Use the base logger directly to avoid infinite recursion
                self.logger.warning(
                    f"Filtered out reserved LogRecord attributes from extra data: {filtered_keys}"
                )

        return enhanced_extra

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message with enhanced context."""
        self.logger.debug(message, extra=self._enhance_extra(extra))

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message with enhanced context."""
        self.logger.info(message, extra=self._enhance_extra(extra))

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message with enhanced context."""
        self.logger.warning(message, extra=self._enhance_extra(extra))

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = True,
    ):
        """Log error message with enhanced context and exception info."""
        self.logger.error(message, extra=self._enhance_extra(extra), exc_info=exc_info)

    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log exception message with enhanced context and automatic exception info.
        
        This method is a convenience method equivalent to calling error() with 
        exc_info=True. It should typically be called only from exception handlers.
        
        Args:
            message: Exception message to log
            extra: Additional custom properties
        """
        self.logger.error(message, extra=self._enhance_extra(extra), exc_info=True)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message with enhanced context."""
        self.logger.critical(message, extra=self._enhance_extra(extra))

    def log_function_execution(
        self,
        function_name: str,
        duration_ms: float,
        success: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Log function execution metrics for performance monitoring.

        Args:
            function_name: Name of executed function
            duration_ms: Execution duration in milliseconds
            success: Whether function executed successfully
            extra: Additional custom properties
        """
        log_data = {
            "function_name": function_name,
            "duration_ms": duration_ms,
            "success": success,
            "performance_category": "function_execution",
        }

        if extra:
            log_data.update(extra)

        message = f"Function '{function_name}' executed in {duration_ms:.2f}ms - {'SUCCESS' if success else 'FAILED'}"

        if success:
            self.info(message, extra=log_data)
        else:
            self.error(message, extra=log_data, exc_info=False)

    def log_request(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Log HTTP request with comprehensive details.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            status_code: HTTP response status code
            duration_ms: Request duration in milliseconds
            extra: Additional custom properties
        """
        log_data = {
            "http_method": method,
            "http_url": str(url),
            "http_status_code": status_code,
            "duration_ms": duration_ms,
            "request_category": "http_request",
        }

        if extra:
            log_data.update(extra)

        # Determine log level and status based on status code
        if status_code < 400:
            log_level = logging.INFO
            status_text = "SUCCESS"
        elif status_code < 500:
            log_level = logging.WARNING
            status_text = "CLIENT_ERROR"
        else:
            log_level = logging.ERROR
            status_text = "SERVER_ERROR"

        message = (
            f"{method} {url} - {status_code} - {duration_ms:.2f}ms - {status_text}"
        )
        self.logger.log(log_level, message, extra=self._enhance_extra(log_data))

    def create_span(
        self,
        span_name: str,
        attributes: Optional[Dict[str, Union[str, int, float, bool]]] = None,
    ) -> Span:
        """Create OpenTelemetry span for distributed tracing.

        Args:
            span_name: Name for the span
            attributes: Initial span attributes

        Returns:
            OpenTelemetry span context manager
        """
        span = self.tracer.start_span(span_name)

        # Add default service attributes
        span.set_attribute("service.name", self.service_name)
        span.set_attribute("service.version", self.service_version)

        if self._correlation_id:
            span.set_attribute("correlation.id", self._correlation_id)

        # Add custom attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def _setup_span_for_function_trace(
        self,
        span: Span,
        func: Callable,
        is_async: bool,
        log_args: bool,
        args: tuple,
        kwargs: dict,
        log_result: bool,
        log_execution: bool,
    ):
        """Configure span attributes for function tracing."""
        span.set_attribute("function.name", func.__name__)
        span.set_attribute("function.module", func.__module__)
        span.set_attribute("service.name", self.service_name)
        span.set_attribute("function.is_async", is_async)

        # Add decorator parameters as span attributes
        span.set_attribute("function.decorator.log_args", log_args)
        span.set_attribute("function.decorator.log_result", log_result)
        span.set_attribute("function.decorator.log_execution", log_execution)

        if self._correlation_id:
            span.set_attribute("correlation.id", self._correlation_id)

        if log_args:
            if args:
                span.set_attribute("function.args_count", len(args))
                # Add positional arguments as span attributes
                import inspect
                try:
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())
                    for i, arg_value in enumerate(args):
                        param_name = param_names[i] if i < len(param_names) else f"arg_{i}"
                        try:
                            # Convert to string for safe serialization
                            attr_value = str(arg_value)
                            # Truncate if too long to avoid excessive data
                            if len(attr_value) > 1000:
                                attr_value = attr_value[:1000] + "..."
                            span.set_attribute(f"function.arg.{param_name}", attr_value)
                        except Exception:
                            span.set_attribute(f"function.arg.{param_name}", "<non-serializable>")
                except Exception:
                    # Fallback if signature inspection fails
                    for i, arg_value in enumerate(args):
                        try:
                            attr_value = str(arg_value)
                            if len(attr_value) > 1000:
                                attr_value = attr_value[:1000] + "..."
                            span.set_attribute(f"function.arg.{i}", attr_value)
                        except Exception:
                            span.set_attribute(f"function.arg.{i}", "<non-serializable>")
                            
            if kwargs:
                span.set_attribute("function.kwargs_count", len(kwargs))
                # Add keyword arguments as span attributes
                for key, value in kwargs.items():
                    try:
                        attr_value = str(value)
                        # Truncate if too long to avoid excessive data
                        if len(attr_value) > 1000:
                            attr_value = attr_value[:1000] + "..."
                        span.set_attribute(f"function.kwarg.{key}", attr_value)
                    except Exception:
                        span.set_attribute(f"function.kwarg.{key}", "<non-serializable>")

    def _handle_function_success(
        self,
        span: Span,
        func: Callable,
        duration_ms: float,
        result: Any,
        log_result: bool,
        log_execution: bool,
        is_async: bool,
        args: tuple,
        kwargs: dict,
    ):
        """Handle successful function execution in tracing."""
        span.set_attribute("function.duration_ms", duration_ms)
        span.set_attribute("function.success", True)
        span.set_status(Status(StatusCode.OK))

        if log_result and result is not None:
            span.set_attribute("function.has_result", True)
            span.set_attribute("function.result_type", type(result).__name__)
            try:
                # Convert to string for safe serialization
                attr_value = str(result)
                # Truncate if too long to avoid excessive data
                if len(attr_value) > 1000:
                    attr_value = attr_value[:1000] + "..."
                span.set_attribute("function.result", attr_value)
            except Exception:
                span.set_attribute("function.result", "<non-serializable>")

        if log_execution:
            self.log_function_execution(
                func.__name__,
                duration_ms,
                True,
                {
                    "args_count": len(args) if args else 0,
                    "kwargs_count": len(kwargs) if kwargs else 0,
                    "is_async": is_async,
                },
            )

        log_prefix = "Async function" if is_async else "Function"
        self.debug(f"{log_prefix} execution completed: {func.__name__}")

    def _handle_function_exception(
        self,
        span: Span,
        func: Callable,
        duration_ms: float,
        e: Exception,
        log_execution: bool,
        is_async: bool,
    ):
        """Handle failed function execution in tracing."""
        span.set_status(Status(StatusCode.ERROR, description=str(e)))
        span.record_exception(e)
        if log_execution:
            self.log_function_execution(
                function_name=func.__name__, duration_ms=duration_ms, success=False
            )
            self.error(
                f"Exception in {'async ' if is_async else ''}"
                f"function '{func.__name__}': {e}"
            )

    def trace_function(
        self,
        function_name: Optional[str] = None,
        log_execution: bool = True,
        log_args: bool = True,
        log_result: bool = False,
    ) -> Callable:
        """Trace function execution with OpenTelemetry.

        This decorator provides a simple way to instrument a function by automatically
        creating an OpenTelemetry span to trace its execution. It measures execution
        time, captures arguments, and records the result as attributes on the span.
        It supports both synchronous and asynchronous functions.

        A correlation ID is automatically managed. If one is not already set on the
        logger instance, a new UUID4 correlation ID will be generated and used for
        the function's trace, ensuring that all related logs and traces can be
        linked together.

        Args:
            function_name (Optional[str]):
                Specifies a custom name for the span. If not provided, the name of the
                decorated function is used. Defaults to None.
            log_execution (bool):
                When True, a log message is emitted at the start and end of the function's
                execution, including the execution duration. This provides a clear
                record of the function's lifecycle. Defaults to True.
            log_args (bool):
                When True, the arguments passed to the function are recorded as
                attributes on the span. It captures argument names and their string
                representations, truncating long values to 1000 characters.
                This is useful for understanding the context of the function call.
                Sensitive arguments should be handled with care. Defaults to True.
            log_result (bool):
                When True, the function's return value is recorded as an attribute
                on the span. It captures the result's type and its string
                representation, truncating long values to 1000 characters. This
                should be used cautiously, as large or sensitive return values may
                be captured. Defaults to False.

        Returns:
            Callable: A decorator that can be applied to a function.

        Examples:
            Basic usage with default settings:
            Logs execution, arguments, but not the result.

            @logger.trace_function()
            def sample_function(param1, param2="default"):
                return "done"

            Customizing the span name:
            The span will be named "MyCustomTask" instead of "process_data".

            @logger.trace_function(function_name="MyCustomTask")
            def process_data(data):
                # processing logic
                return {"status": "processed"}

            Logging the result:
            Enable `log_result=True` to capture the function's return value.

            @logger.trace_function(log_result=True)
            def get_user_id(username):
                return 12345

            Disabling argument logging for sensitive data:
            If a function handles sensitive information, disable argument logging.

            @logger.trace_function(log_args=False)
            def process_payment(credit_card_details):
                # payment processing logic
                pass

            Tracing an asynchronous function:
            The decorator works with async functions without any extra configuration.

            @logger.trace_function(log_result=True)
            async def fetch_remote_data(url):
                # async data fetching
                return await http_get(url)
        """

        def decorator(func):
            # Determine if the function is async at decoration time
            is_async = asyncio.iscoroutinefunction(func)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = function_name or f"{func.__module__}.{func.__name__}"
                with self.tracer.start_as_current_span(span_name) as span:
                    # Auto-generate correlation_id if not set - ensures consistent tracing
                    # Manual correlation_ids take precedence over auto-generated ones
                    if not self._correlation_id:
                        self._correlation_id = str(uuid.uuid4())
                    
                    self._setup_span_for_function_trace(
                        span, func, True, log_args, args, kwargs, log_result, log_execution
                    )
                    start_time = time.time()
                    try:
                        self.debug(
                            f"Starting async function execution: {func.__name__}"
                        )
                        result = await func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000
                        self._handle_function_success(
                            span,
                            func,
                            duration_ms,
                            result,
                            log_result,
                            log_execution,
                            True,
                            args,
                            kwargs,
                        )
                        return result
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        self._handle_function_exception(
                            span, func, duration_ms, e, log_execution, True
                        )
                        raise

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span_name = function_name or f"{func.__module__}.{func.__name__}"
                with self.tracer.start_as_current_span(span_name) as span:
                    # Auto-generate correlation_id if not set - ensures consistent tracing
                    # Manual correlation_ids take precedence over auto-generated ones
                    if not self._correlation_id:
                        self._correlation_id = str(uuid.uuid4())
                    
                    self._setup_span_for_function_trace(
                        span, func, False, log_args, args, kwargs, log_result, log_execution
                    )
                    start_time = time.time()
                    try:
                        self.debug(f"Starting function execution: {func.__name__}")
                        result = func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000
                        self._handle_function_success(
                            span,
                            func,
                            duration_ms,
                            result,
                            log_result,
                            log_execution,
                            False,
                            args,
                            kwargs,
                        )
                        return result
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        self._handle_function_exception(
                            span, func, duration_ms, e, log_execution, False
                        )
                        raise

            # Return appropriate wrapper based on function type
            if is_async:
                return async_wrapper
            return sync_wrapper

        return decorator

    def add_span_attributes(self, attributes: Dict[str, Union[str, int, float, bool]]):
        """Add attributes to current active span."""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            for key, value in attributes.items():
                current_span.set_attribute(key, value)

    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current active span."""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            event_attributes = attributes or {}
            if self._correlation_id:
                event_attributes["correlation_id"] = self._correlation_id
            current_span.add_event(name, event_attributes)

    def set_span_status(
        self, status_code: StatusCode, description: Optional[str] = None
    ):
        """Set status of current active span."""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_status(Status(status_code, description))

    def log_with_span(
        self,
        span_name: str,
        message: str,
        level: int = logging.INFO,
        extra: Optional[Dict[str, Any]] = None,
        span_attributes: Optional[Dict[str, Union[str, int, float, bool]]] = None,
    ):
        """Log message within a span context.

        Args:
            span_name: Name for the span
            message: Log message
            level: Python logging level
            extra: Additional log properties
            span_attributes: Attributes to add to span
        """
        with self.tracer.start_as_current_span(span_name) as span:
            if span_attributes:
                for key, value in span_attributes.items():
                    span.set_attribute(key, value)

            self.logger.log(level, message, extra=self._enhance_extra(extra))

    def log_dependency(
        self,
        dependency_type: str,
        name: str,
        command: str,
        success: bool,
        duration_ms: float,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Log external dependency calls for monitoring.

        Args:
            dependency_type: Type of dependency (SQL, HTTP, etc.)
            name: Dependency identifier
            command: Command/query executed
            success: Whether call was successful
            duration_ms: Call duration in milliseconds
            extra: Additional properties
        """
        log_data = {
            "dependency_type": dependency_type,
            "dependency_name": name,
            "dependency_command": command,
            "dependency_success": success,
            "duration_ms": duration_ms,
            "category": "dependency_call",
        }

        if extra:
            log_data.update(extra)

        log_level = logging.INFO if success else logging.ERROR
        status = "SUCCESS" if success else "FAILED"
        message = f"Dependency call: {dependency_type}:{name} - {duration_ms:.2f}ms - {status}"

        self.logger.log(log_level, message, extra=self._enhance_extra(log_data))

    def flush(self):
        """Flush pending telemetry data."""
        if self._telemetry_enabled:
            try:
                from opentelemetry.sdk.trace import TracerProvider

                tracer_provider = trace.get_tracer_provider()
                if hasattr(tracer_provider, "force_flush"):
                    tracer_provider.force_flush(timeout_millis=5000)
            except Exception as e:
                self.warning(f"Failed to flush telemetry: {e}")


# Factory functions with logger caching
_loggers: Dict[Any, "AzureLogger"] = {}


def create_app_logger(
    service_name: str,
    service_version: str = "1.0.0",
    connection_string: Optional[str] = None,
    log_level: int = logging.INFO,
    enable_console_logging: bool = True,
    custom_resource_attributes: Optional[Dict[str, str]] = None,
    instrumentation_options: Optional[Dict[str, Any]] = None,
    cloud_role_name: Optional[str] = None,
) -> AzureLogger:
    """Create cached AzureLogger instance for applications.

    Returns existing logger if one with same configuration exists.
    The service_name automatically becomes the cloud role name in Application Insights
    unless explicitly overridden with cloud_role_name parameter.

    Args:
        service_name: Service identifier for telemetry and cloud role name
        service_version: Service version for metadata
        connection_string: Application Insights connection string
        log_level: Python logging level
        enable_console_logging: Enable console output
        custom_resource_attributes: Additional OpenTelemetry resource attributes
        instrumentation_options: Azure Monitor instrumentation options
        cloud_role_name: Override cloud role name (defaults to service_name)

    Returns:
        Configured AzureLogger instance
    """
    resolved_connection_string = connection_string or os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    attr_items = (
        tuple(sorted(custom_resource_attributes.items()))
        if custom_resource_attributes
        else None
    )

    params_key = (
        service_name,
        service_version,
        resolved_connection_string,
        log_level,
        enable_console_logging,
        attr_items,
        cloud_role_name,
    )

    if params_key in _loggers:
        return _loggers[params_key]

    logger = AzureLogger(
        service_name=service_name,
        service_version=service_version,
        connection_string=connection_string,
        log_level=log_level,
        enable_console_logging=enable_console_logging,
        custom_resource_attributes=custom_resource_attributes,
        instrumentation_options=instrumentation_options,
        cloud_role_name=cloud_role_name,
    )
    _loggers[params_key] = logger
    return logger


def create_function_logger(
    function_app_name: str,
    function_name: str,
    service_version: str = "1.0.0",
    connection_string: Optional[str] = None,
    log_level: int = logging.INFO,
    instrumentation_options: Optional[Dict[str, Any]] = None,
    cloud_role_name: Optional[str] = None,
) -> AzureLogger:
    """Create AzureLogger optimized for Azure Functions.

    Automatically creates cloud role name in the format '{function_app_name}.{function_name}'
    unless explicitly overridden. This ensures each function appears as a separate
    component in the Application Insights Application Map.

    Args:
        function_app_name: Azure Function App name
        function_name: Specific function name
        service_version: Service version for metadata
        connection_string: Application Insights connection string
        log_level: Python logging level
        instrumentation_options: Azure Monitor instrumentation options
        cloud_role_name: Override cloud role name (defaults to '{function_app_name}.{function_name}')

    Returns:
        Configured AzureLogger with Azure Functions context
    """
    custom_attributes = {
        "azure.function.app": function_app_name,
        "azure.function.name": function_name,
        "azure.resource.type": "function",
    }

    default_service_name = f"{function_app_name}.{function_name}"

    return create_app_logger(
        service_name=default_service_name,
        service_version=service_version,
        connection_string=connection_string,
        log_level=log_level,
        custom_resource_attributes=custom_attributes,
        instrumentation_options=instrumentation_options,
        cloud_role_name=cloud_role_name,
    )
