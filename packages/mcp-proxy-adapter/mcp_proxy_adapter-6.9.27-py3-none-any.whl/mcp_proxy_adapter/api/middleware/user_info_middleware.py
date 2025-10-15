"""
User Info Middleware

This middleware extracts user information from authentication headers
and sets it in request.state for use by commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from mcp_proxy_adapter.core.logging import get_global_logger

# Import mcp_security_framework components
try:
    from mcp_security_framework import AuthManager, PermissionManager
    from mcp_security_framework.schemas.config import AuthConfig, PermissionConfig

    _MCP_SECURITY_AVAILABLE = True
    print("✅ mcp_security_framework available in middleware")
except ImportError:
    _MCP_SECURITY_AVAILABLE = False
    print("⚠️ mcp_security_framework not available in middleware, " "using basic auth")


class UserInfoMiddleware(BaseHTTPMiddleware):
    """
    Middleware for setting user information in request.state.

    This middleware extracts user information from authentication headers
    and sets it in request.state for use by commands.
    """

    def __init__(self, app, config: Dict[str, Any]):
        """
        Initialize user info middleware.

        Args:
            app: FastAPI application
            config: Configuration dictionary
        """
        super().__init__(app)
        self.config = config

        # Initialize AuthManager if available
        self.auth_manager = None
        self._security_available = _MCP_SECURITY_AVAILABLE

        if self._security_available:
            try:
                # Get API keys configuration
                security_config = config.get("security", {})
                
                # Check if security is enabled
                security_enabled = security_config.get("enabled", False)
                if not security_enabled:
                    get_global_logger().info("ℹ️ Security disabled in configuration, using basic auth")
                    self._security_available = False
                else:
                    auth_config = security_config.get("auth", {})
                    permissions_config = security_config.get("permissions", {})

                    # Check if permissions are enabled
                    permissions_enabled = permissions_config.get("enabled", False)

                    # Only use mcp_security_framework if permissions are enabled
                    if permissions_enabled:
                        # Create AuthConfig for mcp_security_framework
                        mcp_auth_config = AuthConfig(
                            enabled=True,
                            methods=["api_key"],
                            api_keys=auth_config.get("api_keys", {}),
                        )

                        # Create PermissionConfig for mcp_security_framework
                        roles_file = permissions_config.get("roles_file")
                        if roles_file is None:
                            get_global_logger().warning("⚠️ Permissions enabled but no roles_file specified, using default configuration")
                            roles_file = None
                        
                        mcp_permission_config = PermissionConfig(
                            roles_file=roles_file,
                            default_role=permissions_config.get("default_role", "guest"),
                            admin_role=permissions_config.get("admin_role", "admin"),
                            role_hierarchy=permissions_config.get("role_hierarchy", {}),
                            permission_cache_enabled=permissions_config.get(
                                "permission_cache_enabled", True
                            ),
                            permission_cache_ttl=permissions_config.get(
                                "permission_cache_ttl", 300
                            ),
                            wildcard_permissions=permissions_config.get(
                                "wildcard_permissions", False
                            ),
                            strict_mode=permissions_config.get("strict_mode", True),
                            roles=permissions_config.get("roles", {}),
                        )

                        # Initialize PermissionManager first
                        self.permission_manager = PermissionManager(mcp_permission_config)

                        # Initialize AuthManager with permission_manager
                        self.auth_manager = AuthManager(
                            mcp_auth_config, self.permission_manager
                        )
                        get_global_logger().info(
                            "✅ User info middleware initialized with " "mcp_security_framework"
                        )
                    else:
                        # When permissions are disabled, use basic auth without mcp_security_framework
                        get_global_logger().info("ℹ️ Permissions disabled, using basic token auth without mcp_security_framework")
                        self._security_available = False
                        # Initialize api_keys for basic auth
                        self.api_keys = auth_config.get("api_keys", {})
            except Exception as e:
                get_global_logger().warning(f"⚠️ Failed to initialize AuthManager: {e}")
                self._security_available = False

        # Always initialize api_keys for fallback
        security_config = config.get("security", {})
        auth_config = security_config.get("auth", {})
        self.api_keys = auth_config.get("api_keys", {})
        
        if not self._security_available:
            # Fallback to basic API key handling
            get_global_logger().info("ℹ️ User info middleware initialized with basic auth")
        else:
            get_global_logger().info("ℹ️ User info middleware initialized with mcp_security_framework (fallback enabled)")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and set user info in request.state.

        Args:
            request: Request object
            call_next: Next handler

        Returns:
            Response object
        """
        get_global_logger().debug(f"🔍 UserInfoMiddleware.dispatch START - {request.method} {request.url.path}")
        get_global_logger().debug(f"🔍 UserInfoMiddleware - Headers: {dict(request.headers)}")
        get_global_logger().debug(f"🔍 UserInfoMiddleware - AuthManager available: {self.auth_manager is not None}")
        get_global_logger().debug(f"🔍 UserInfoMiddleware - Security available: {self._security_available}")
        
        # Extract API key from headers
        api_key = request.headers.get("X-API-Key")
        get_global_logger().debug(f"🔍 UserInfoMiddleware - API Key: {api_key[:8] + '...' if api_key else 'None'}")
        if api_key:
            if self.auth_manager and self._security_available:
                try:
                    # Use mcp_security_framework AuthManager
                    auth_result = self.auth_manager.authenticate_api_key(api_key)

                    if auth_result.is_valid:
                        # Set user info from AuthManager result
                        request.state.user = {
                            "id": api_key,
                            "role": (
                                auth_result.roles[0] if auth_result.roles else "guest"
                            ),
                            "roles": auth_result.roles or ["guest"],
                            "permissions": getattr(
                                auth_result, "permissions", ["read"]
                            ),
                        }
                        get_global_logger().debug(
                            f"✅ Authenticated user with "
                            f"mcp_security_framework: "
                            f"{request.state.user}"
                        )
                    else:
                        # Authentication failed
                        request.state.user = {
                            "id": None,
                            "role": "guest",
                            "roles": ["guest"],
                            "permissions": ["read"],
                        }
                        get_global_logger().debug(
                            f"❌ Authentication failed for API key: "
                            f"{api_key[:8]}..."
                        )
                except Exception as e:
                    get_global_logger().warning(
                        f"⚠️ AuthManager error: {e}, " f"falling back to basic auth"
                    )
                    self._security_available = False

            if not self._security_available:
                # Fallback to basic API key handling
                api_keys_dict = getattr(self, "api_keys", {})
                # Find role by API key value (not key)
                user_role = None
                for role, key_value in api_keys_dict.items():
                    if key_value == api_key:
                        user_role = role
                        break
                
                if user_role:
                    # Get permissions for this role from roles file if available
                    role_permissions = ["read"]  # default permissions
                    if (
                        hasattr(self, "roles_config")
                        and self.roles_config
                        and user_role in self.roles_config
                    ):
                        role_permissions = self.roles_config[user_role].get(
                            "permissions", ["read"]
                        )

                    # Set user info in request.state
                    request.state.user = {
                        "id": api_key,
                        "role": user_role,
                        "roles": [user_role],
                        "permissions": role_permissions,
                    }
                    get_global_logger().debug(
                        f"✅ User authenticated with API key: "
                        f"{api_key[:8]}..."
                    )
                else:
                    # API key not found
                    request.state.user = {
                        "id": None,
                        "role": "guest",
                        "roles": ["guest"],
                        "permissions": ["read"],
                    }
                    get_global_logger().debug(f"❌ API key not found: {api_key[:8]}...")
        else:
            # No API key provided - guest access
            request.state.user = {
                "id": None,
                "role": "guest",
                "roles": ["guest"],
                "permissions": ["read"],
            }
            get_global_logger().debug("ℹ️ No API key provided, using guest access")

        get_global_logger().debug(f"🔍 UserInfoMiddleware - About to call next handler")
        response = await call_next(request)
        get_global_logger().debug(f"🔍 UserInfoMiddleware - Next handler completed with status: {response.status_code}")
        return response
