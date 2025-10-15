"""
Middleware package for API.
This package contains middleware components for request processing.
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.config import config
from .base import BaseMiddleware
from .factory import MiddlewareFactory
from .protocol_middleware import setup_protocol_middleware

# Export mcp_security_framework availability
try:
    from .user_info_middleware import _MCP_SECURITY_AVAILABLE
    mcp_security_framework = _MCP_SECURITY_AVAILABLE
except ImportError:
    mcp_security_framework = False


def setup_middleware(app: FastAPI, app_config: Optional[Dict[str, Any]] = None) -> None:
    """
    Sets up middleware for application using the new middleware factory.

    Args:
        app: FastAPI application instance.
        app_config: Application configuration dictionary (optional)
    """
    # Use provided configuration or fallback to global config
    current_config = app_config if app_config is not None else config.get_all()

    # Add protocol middleware FIRST (before other middleware)
    setup_protocol_middleware(app, current_config)

    # Create middleware factory
    factory = MiddlewareFactory(app, current_config)

    # Validate middleware configuration
    if not factory.validate_middleware_config():
        get_global_logger().error("Middleware configuration validation failed")
        raise SystemExit(1)

    get_global_logger().info("Using unified security middleware")
    middleware_list = factory.create_all_middleware()

    # Add middleware to application AFTER protocol middleware
    for middleware in middleware_list:
        # For ASGI middleware, we need to wrap the application
        if hasattr(middleware, "dispatch"):
            # This is a proper ASGI middleware
            app.middleware("http")(middleware.dispatch)
        else:
            get_global_logger().warning(
                f"Middleware {middleware.__class__.__name__} doesn't have dispatch method"
            )

    # Log middleware information
    middleware_info = factory.get_middleware_info()
    get_global_logger().info(f"Middleware setup completed:")
    get_global_logger().info(f"  - Total middleware: {middleware_info['total_middleware']}")
    get_global_logger().info(f"  - Types: {', '.join(middleware_info['middleware_types'])}")
    get_global_logger().info(f"  - Security enabled: {middleware_info['security_enabled']}")
