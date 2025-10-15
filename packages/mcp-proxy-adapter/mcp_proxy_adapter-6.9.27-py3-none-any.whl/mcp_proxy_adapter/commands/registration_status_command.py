"""
Registration Status Command

This command provides information about the current proxy registration status,
including async registration state, heartbeat status, and statistics.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any
from dataclasses import dataclass

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.logging import get_global_logger


@dataclass
class RegistrationStatusCommandResult(SuccessResult):
    """Result of registration status command."""

    status: Dict[str, Any]
    message: str = "Registration status retrieved successfully"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": True,
            "status": self.status,
            "message": self.message,
        }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for result."""
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the command was successful",
                },
                "status": {
                    "type": "object",
                    "description": "Registration status information",
                    "properties": {
                        "state": {"type": "string", "description": "Current registration state"},
                        "server_key": {"type": "string", "description": "Server key if registered"},
                        "last_attempt": {"type": "number", "description": "Timestamp of last registration attempt"},
                        "last_success": {"type": "number", "description": "Timestamp of last successful registration"},
                        "last_error": {"type": "string", "description": "Last error message"},
                        "attempt_count": {"type": "integer", "description": "Total registration attempts"},
                        "success_count": {"type": "integer", "description": "Total successful registrations"},
                        "heartbeat_enabled": {"type": "boolean", "description": "Whether heartbeat is enabled"},
                        "heartbeat_interval": {"type": "integer", "description": "Heartbeat interval in seconds"},
                        "thread_alive": {"type": "boolean", "description": "Whether registration thread is alive"},
                    },
                },
                "message": {"type": "string", "description": "Result message"},
            },
            "required": ["success", "status", "message"],
        }


class RegistrationStatusCommand(Command):
    """Command to get proxy registration status."""

    name = "registration_status"
    descr = "Get current proxy registration status and statistics"
    category = "proxy"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"

    async def execute(self, **kwargs) -> RegistrationStatusCommandResult:
        """
        Execute registration status command.

        Returns:
            RegistrationStatusCommandResult with current status
        """
        get_global_logger().info("Executing registration status command")

        try:
            from mcp_proxy_adapter.core.async_proxy_registration import (
                get_registration_status,
            )

            status = get_registration_status()
            
            get_global_logger().info(f"Registration status retrieved: {status}")

            return RegistrationStatusCommandResult(
                status=status,
                message="Registration status retrieved successfully"
            )

        except Exception as e:
            get_global_logger().error(f"Failed to get registration status: {e}")
            
            error_status = {
                "state": "error",
                "error": str(e),
                "thread_alive": False
            }
            
            return RegistrationStatusCommandResult(
                status=error_status,
                message=f"Failed to get registration status: {e}"
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
