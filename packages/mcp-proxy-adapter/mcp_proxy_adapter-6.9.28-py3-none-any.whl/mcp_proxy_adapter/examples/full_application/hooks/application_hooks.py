"""
Application Hooks
This module demonstrates application-level hooks in the full application example.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ApplicationHooks:
    """Application-level hooks."""

    @staticmethod
    def on_startup():
        """Hook executed on application startup."""
        get_global_logger().info("🚀 Application startup hook executed")
        # Initialize application-specific resources
        get_global_logger().info("📊 Initializing application metrics")
        get_global_logger().info("🔐 Loading security configurations")
        get_global_logger().info("📝 Setting up logging")

    @staticmethod
    def on_shutdown():
        """Hook executed on application shutdown."""
        get_global_logger().info("🛑 Application shutdown hook executed")
        # Cleanup application resources
        get_global_logger().info("🧹 Cleaning up resources")
        get_global_logger().info("💾 Saving application state")
        get_global_logger().info("📊 Finalizing metrics")

    @staticmethod
    def before_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Hook executed before processing any request."""
        get_global_logger().info(f"🔧 Application hook: before_request with data: {request_data}")
        # Add request metadata
        request_data["app_metadata"] = {
            "request_id": f"req_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "application": "full_application_example",
        }
        return request_data

    @staticmethod
    def after_request(result: Dict[str, Any]) -> Dict[str, Any]:
        """Hook executed after processing any request."""
        get_global_logger().info(f"🔧 Application hook: after_request with result: {result}")
        # Add response metadata
        result["app_response_metadata"] = {
            "processed_at": datetime.now().isoformat(),
            "application": "full_application_example",
            "version": "1.0.0",
        }
        return result

    @staticmethod
    def on_error(error: Exception, context: Dict[str, Any]):
        """Hook executed when an error occurs."""
        get_global_logger().error(f"🔧 Application hook: on_error - {error} in context: {context}")
        # Log error details
        get_global_logger().error(f"Error type: {type(error).__name__}")
        get_global_logger().error(f"Error message: {str(error)}")
        get_global_logger().error(f"Context: {context}")

    @staticmethod
    def on_command_registered(command_name: str, command_info: Dict[str, Any]):
        """Hook executed when a command is registered."""
        get_global_logger().info(f"🔧 Application hook: on_command_registered - {command_name}")
        get_global_logger().info(f"Command info: {command_info}")
        # Track registered commands
        get_global_logger().info(f"📝 Command '{command_name}' registered successfully")

    @staticmethod
    def on_command_executed(command_name: str, execution_time: float, success: bool):
        """Hook executed when a command is executed."""
        get_global_logger().info(f"🔧 Application hook: on_command_executed - {command_name}")
        get_global_logger().info(f"Execution time: {execution_time}s, Success: {success}")
        # Track command execution metrics
        if success:
            get_global_logger().info(
                f"✅ Command '{command_name}' executed successfully in {execution_time}s"
            )
        else:
            get_global_logger().warning(f"⚠️ Command '{command_name}' failed after {execution_time}s")
