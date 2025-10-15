"""
Module for FastAPI application setup.
"""

import json
import ssl
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager
import asyncio

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from mcp_proxy_adapter.api.handlers import (
    execute_command,
    handle_json_rpc,
    handle_batch_json_rpc,
    get_server_health,
    get_commands_list,
)
from mcp_proxy_adapter.api.middleware import setup_middleware
from mcp_proxy_adapter.api.schemas import (
    JsonRpcRequest,
    JsonRpcSuccessResponse,
    JsonRpcErrorResponse,
    HealthResponse,
    CommandListResponse,
    APIToolDescription,
)
from mcp_proxy_adapter.api.tools import get_tool_description, execute_tool
from mcp_proxy_adapter.config import config
from mcp_proxy_adapter.core.errors import MicroserviceError, NotFoundError
from mcp_proxy_adapter.core.logging import get_global_logger, RequestLogger
from mcp_proxy_adapter.core.ssl_utils import SSLUtils
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.custom_openapi import custom_openapi_with_fallback


def _determine_registration_url(config: Dict[str, Any]) -> str:
    """
    Determine the registration URL for proxy registration.
    
    Logic:
    1. Protocol: registration.protocol > server.protocol > fallback to http
    2. Host: public_host > hostname (if server.host is 0.0.0.0/127.0.0.1) > server.host
    3. Port: public_port > server.port
    
    Args:
        config: Application configuration
        
    Returns:
        Complete registration URL
    """
    import os
    import socket
    
    # Get server configuration
    server_config = config.get("server", {})
    server_host = server_config.get("host", "0.0.0.0")
    server_port = server_config.get("port", 8000)
    server_protocol = server_config.get("protocol", "http")
    
    # Get registration configuration
    reg_cfg = config.get("registration", config.get("proxy_registration", {}))
    public_host = reg_cfg.get("public_host")
    public_port = reg_cfg.get("public_port")
    registration_protocol = reg_cfg.get("protocol")
    
    # Determine protocol
    if registration_protocol:
        # Use protocol from registration configuration
        # Convert mtls to https for URL construction (mTLS is still HTTPS)
        protocol = "https" if registration_protocol == "mtls" else registration_protocol
        get_global_logger().info(f"🔍 Using registration.protocol: {registration_protocol} -> {protocol}")
    else:
        # Fallback to server protocol
        verify_client = config.get("transport", {}).get("verify_client", False)
        ssl_enabled = server_protocol in ["https", "mtls"] or verify_client
        protocol = "https" if ssl_enabled else "http"
        get_global_logger().info(f"⚠️  Fallback to server.protocol: {server_protocol} -> {protocol} (verify_client={verify_client})")
    
    # Determine host
    if not public_host:
        if server_host in ("0.0.0.0", "127.0.0.1"):
            # Try to get hostname, fallback to docker host addr
            try:
                hostname = socket.gethostname()
                # Use hostname if it's not localhost
                if hostname and hostname not in ("localhost", "127.0.0.1"):
                    resolved_host = hostname
                else:
                    resolved_host = os.getenv("DOCKER_HOST_ADDR", "172.17.0.1")
            except Exception:
                resolved_host = os.getenv("DOCKER_HOST_ADDR", "172.17.0.1")
        else:
            resolved_host = server_host
    else:
        resolved_host = public_host
        
    # Determine port
    resolved_port = public_port or server_port
    
    # Build URL
    server_url = f"{protocol}://{resolved_host}:{resolved_port}"
    
    get_global_logger().info(
        "🔍 Registration URL selection: server_host=%s, server_port=%s, public_host=%s, public_port=%s, protocol=%s, resolved_host=%s, resolved_port=%s, server_url=%s",
        server_host, server_port, public_host, public_port, protocol, resolved_host, resolved_port, server_url
    )
    
    return server_url


def create_lifespan(config_path: Optional[str] = None, current_config: Optional[Dict[str, Any]] = None):
    """
    Create lifespan manager for the FastAPI application.

    Args:
        config_path: Path to configuration file (optional)
        current_config: Current configuration data (optional)

    Returns:
        Lifespan context manager
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Lifespan manager for the FastAPI application. Handles startup and shutdown events.
        """
        # Startup events
        from mcp_proxy_adapter.commands.command_registry import registry
        from mcp_proxy_adapter.core.proxy_registration import (
            register_with_proxy,
            unregister_from_proxy,
            initialize_proxy_registration,
        )

        # Proxy registration manager will be initialized in registry.reload_system()
        # after all commands are loaded to ensure complete command schema

        # Compute server_url EARLY and inject into registration manager so
        # that reload_system (which may perform registration) uses the correct
        # externally reachable address.
        # Use current_config from closure or fallback to global config
        config_to_use = current_config
        if config_to_use is None:
            # Fallback: try to get config from global instance
            try:
                from mcp_proxy_adapter.config import get_config
                config_to_use = get_config().get_all()
            except Exception:
                config_to_use = {}
        
        server_config = config_to_use.get("server")
        if not server_config:
            raise ValueError("server configuration is required")
        server_host = server_config.get("host")
        server_port = server_config.get("port")
        if not server_host:
            raise ValueError("server.host is required")
        if not server_port:
            raise ValueError("server.port is required")

        # Check port availability BEFORE starting registration manager
        from mcp_proxy_adapter.core.utils import check_port_availability, handle_port_conflict
        
        print(f"🔍 Checking external server port availability: {server_host}:{server_port}")
        if not check_port_availability(server_host, server_port):
            print(f"❌ CRITICAL: External server port {server_port} is occupied")
            handle_port_conflict(server_host, server_port)
            return  # Exit the function immediately
        print(f"✅ External server port {server_port} is available")

        # Determine registration URL using unified logic
        early_server_url = _determine_registration_url(config_to_use)
        try:
            from mcp_proxy_adapter.core.proxy_registration import (
                register_with_proxy,
                unregister_from_proxy,
                initialize_proxy_registration,
            )

            # Initialize proxy registration
            initialize_proxy_registration(config_to_use)
            get_global_logger().info(
                "🔍 Initialized proxy registration with server_url: %s",
                early_server_url,
            )
            
        except Exception as e:
            get_global_logger().error(f"Failed to initialize async registration: {e}")

        # Initialize system using unified logic (may perform registration)
        # Set global config for reload_system
        from mcp_proxy_adapter.config import Config
        config_obj = Config()
        config_obj.config_data = config_to_use
        
        # Set global config for command registry
        from mcp_proxy_adapter.config import get_config
        global_config = get_config()
        global_config.config_data = config_to_use
        
        if config_path:
            init_result = await registry.reload_system(config_path=config_path, config_obj=config_obj)
        else:
            init_result = await registry.reload_system(config_obj=config_obj)

        get_global_logger().info(
            f"Application started with {init_result['total_commands']} commands registered"
        )
        get_global_logger().info(f"System initialization result: {init_result}")

        # Proxy registration manager is already initialized in registry.reload_system()

        # Recompute registration URL AFTER config reload using final config
        try:
            final_config = config_to_use  # config_to_use is already a dict
            server_config = final_config.get("server", {})
            server_host = server_config.get("host", "0.0.0.0")
            server_port = server_config.get("port", 8000)

            # Determine registration URL using unified logic
            server_url = _determine_registration_url(final_config)
            
            # Update proxy registration with final server URL
            try:
                get_global_logger().info(f"🔍 Updated proxy registration with final server_url: {server_url}")
                    
            except Exception as e:
                get_global_logger().error(f"Failed to update proxy registration: {e}")
            
            try:
                print("🔍 Registration server_url resolved to (print):", server_url)
            except Exception:
                pass
        except Exception as e:
            get_global_logger().error(f"Failed to recompute registration URL: {e}")
            server_url = early_server_url

        # Proxy registration is now handled in registry.reload_system() 
        # after all commands are loaded, ensuring complete command schema
        get_global_logger().info("ℹ️ Proxy registration will be handled after command loading completes")
        
        # Add delayed registration task to allow server to fully start
        async def delayed_registration():
            """Delayed registration to ensure server is fully started."""
            await asyncio.sleep(2)  # Wait for server to start listening
            get_global_logger().info("🔄 Attempting delayed proxy registration after server startup")
            try:
                from mcp_proxy_adapter.core.proxy_registration import register_with_proxy, initialize_proxy_registration
                # Ensure proxy registration manager is initialized
                initialize_proxy_registration(config_to_use)
                success = await register_with_proxy(server_url)
                if success:
                    get_global_logger().info("✅ Delayed proxy registration successful")
                else:
                    get_global_logger().warning("⚠️ Delayed proxy registration failed")
            except Exception as e:
                get_global_logger().error(f"❌ Delayed proxy registration error: {e}")
        
        asyncio.create_task(delayed_registration())

        yield  # Application is running

        # Shutdown events
        get_global_logger().info("Application shutting down")

        # Stop proxy registration (this will also unregister)
        try:
            unregistration_success = await unregister_from_proxy()
            if unregistration_success:
                get_global_logger().info("✅ Proxy unregistration completed successfully")
            else:
                get_global_logger().warning("⚠️ Proxy unregistration failed or was disabled")
            
        except Exception as e:
            get_global_logger().error(f"❌ Failed to stop proxy registration: {e}")

    return lifespan


def create_ssl_context(
    app_config: Optional[Dict[str, Any]] = None
) -> Optional[ssl.SSLContext]:
    """
    Create SSL context based on configuration.

    Args:
        app_config: Application configuration dictionary (optional)

    Returns:
        SSL context if SSL is enabled and properly configured, None otherwise
    """
    current_config = app_config if app_config is not None else config.get_all()

    # Check SSL configuration from new structure
    protocol = current_config.get("server", {}).get("protocol", "http")
    verify_client = current_config.get("transport", {}).get("verify_client", False)
    ssl_enabled = protocol in ["https", "mtls"] or verify_client

    if not ssl_enabled:
        get_global_logger().info("SSL is disabled in configuration")
        return None

    # Get certificate paths from configuration
    cert_file = current_config.get("transport", {}).get("cert_file")
    key_file = current_config.get("transport", {}).get("key_file")
    ca_cert = current_config.get("transport", {}).get("ca_cert")
    
    # Convert relative paths to absolute paths
    if cert_file and not Path(cert_file).is_absolute():
        project_root = Path(__file__).parent.parent.parent
        cert_file = str(project_root / cert_file)
    if key_file and not Path(key_file).is_absolute():
        project_root = Path(__file__).parent.parent.parent
        key_file = str(project_root / key_file)
    if ca_cert and not Path(ca_cert).is_absolute():
        project_root = Path(__file__).parent.parent.parent
        ca_cert = str(project_root / ca_cert)

    if not cert_file or not key_file:
        get_global_logger().warning("SSL enabled but certificate or key file not specified")
        return None

    try:
        # Create SSL context using SSLUtils
        ssl_context = SSLUtils.create_ssl_context(
            cert_file=cert_file,
            key_file=key_file,
            ca_cert=ca_cert,
            verify_client=current_config.get("transport", {}).get("verify_client", False),
            cipher_suites=[],
            min_tls_version="1.2",
            max_tls_version="1.3",
        )

        get_global_logger().info(
            f"SSL context created successfully for mode: https_only"
        )
        return ssl_context

    except Exception as e:
        get_global_logger().error(f"Failed to create SSL context: {e}")
        return None


def create_app(
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    app_config: Optional[Dict[str, Any]] = None,
    config_path: Optional[str] = None,
) -> FastAPI:
    """
    Creates and configures FastAPI application.

    Args:
        title: Application title (default: "MCP Proxy Adapter")
        description: Application description (default: "JSON-RPC API for interacting with MCP Proxy")
        version: Application version (default: "1.0.0")
        app_config: Application configuration dictionary (optional)
        config_path: Path to configuration file (optional)

    Returns:
        Configured FastAPI application.

    Raises:
        SystemExit: If authentication is enabled but required files are missing (security issue)
    """
    # Use provided configuration or fallback to global config
    if app_config is not None:
        if hasattr(app_config, "get_all"):
            current_config = app_config.get_all()
        elif hasattr(app_config, "keys"):
            current_config = app_config
        else:
            # If app_config is not a dict-like object, use it as is
            current_config = app_config
    else:
        # If no app_config provided, try to get global config
        try:
            from mcp_proxy_adapter.config import get_config
            current_config = get_config().get_all()
        except Exception:
            # If global config is not available, create empty config
            current_config = {}

    # Debug: Check what config is passed to create_app
    if app_config:
        if hasattr(app_config, "keys"):
            print(
                f"🔍 Debug: create_app received app_config keys: {list(app_config.keys())}"
            )
            # Debug SSL configuration
            protocol = app_config.get("server", {}).get("protocol", "http")
            verify_client = app_config.get("transport", {}).get("verify_client", False)
            ssl_enabled = protocol in ["https", "mtls"] or verify_client
            print(f"🔍 Debug: create_app SSL config: enabled={ssl_enabled}")
            print(f"🔍 Debug: create_app protocol: {protocol}")
            print(f"🔍 Debug: create_app verify_client: {verify_client}")
        else:
            print(f"🔍 Debug: create_app received app_config type: {type(app_config)}")
    else:
        print("🔍 Debug: create_app received no app_config, using global config")

    # Security check: Validate configuration strictly at startup (fail-fast)
    try:
        from mcp_proxy_adapter.core.config_validator import ConfigValidator

        _validator = ConfigValidator()
        _validator.config_data = current_config
        _validation_results = _validator.validate_config()
        errors = [r for r in _validation_results if r.level == "error"]
        warnings = [r for r in _validation_results if r.level == "warning"]
        
        if errors:
            get_global_logger().critical("CRITICAL CONFIG ERROR: Invalid configuration at startup:")
            for _e in errors:
                get_global_logger().critical(f"  - {_e.message}")
            raise SystemExit(1)
        for _w in warnings:
            get_global_logger().warning(f"Config warning: {_w.message}")
    except Exception as _ex:
        get_global_logger().error(f"Failed to run startup configuration validation: {_ex}")

    # Security check: Validate all authentication configurations before startup (legacy checks kept for compatibility)
    security_errors = []

    print(f"🔍 Debug: current_config keys: {list(current_config.keys())}")
    if "security" in current_config:
        print(f"🔍 Debug: security config: {current_config['security']}")
    if "roles" in current_config:
        print(f"🔍 Debug: roles config: {current_config['roles']}")

    # Check security framework configuration only if enabled
    security_config = current_config.get("security", {})
    if security_config.get("enabled", False):
        # Validate security framework configuration
        from mcp_proxy_adapter.core.unified_config_adapter import UnifiedConfigAdapter

        adapter = UnifiedConfigAdapter()
        validation_result = adapter.validate_configuration(current_config)

        if not validation_result.is_valid:
            security_errors.extend(validation_result.errors)

        # Check SSL configuration within security framework
        ssl_config = security_config.get("ssl", {})
        if ssl_config.get("enabled", False):
            cert_file = ssl_config.get("cert_file")
            key_file = ssl_config.get("key_file")

            print(
                f"🔍 Debug: api/app.py security.ssl: cert_file={cert_file}, key_file={key_file}"
            )
            print(
                f"🔍 Debug: api/app.py security.ssl: cert_file exists={Path(cert_file).exists() if cert_file else 'None'}"
            )
            print(
                f"🔍 Debug: api/app.py security.ssl: key_file exists={Path(key_file).exists() if key_file else 'None'}"
            )

            if cert_file and not Path(cert_file).exists():
                security_errors.append(
                    f"SSL is enabled but certificate file not found: {cert_file}"
                )

            if key_file and not Path(key_file).exists():
                security_errors.append(
                    f"SSL is enabled but private key file not found: {key_file}"
                )

            # Check mTLS configuration
            ca_cert_file = ssl_config.get("ca_cert_file")
            if ca_cert_file and not Path(ca_cert_file).exists():
                security_errors.append(
                    f"mTLS is enabled but CA certificate file not found: {ca_cert_file}"
                )

    # Legacy configuration checks for backward compatibility
    roles_config = current_config.get("roles", {})
    print(f"🔍 Debug: roles_config = {roles_config}")
    if roles_config.get("enabled", False):
        roles_config_path = roles_config.get("config_file", "schemas/roles_schema.json")
        print(f"🔍 Debug: Checking roles file: {roles_config_path}")
        if not Path(roles_config_path).exists():
            security_errors.append(
                f"Roles are enabled but schema file not found: {roles_config_path}"
            )

    # Check new security framework permissions configuration
    security_config = current_config.get("security", {})
    permissions_config = security_config.get("permissions", {})
    if permissions_config.get("enabled", False):
        roles_file = permissions_config.get("roles_file")
        if roles_file and not Path(roles_file).exists():
            security_errors.append(
                f"Permissions are enabled but roles file not found: {roles_file}"
            )

    legacy_ssl_config = current_config.get("ssl", {})
    if legacy_ssl_config.get("enabled", False):
        # Check SSL certificate files
        cert_file = legacy_ssl_config.get("cert_file")
        key_file = legacy_ssl_config.get("key_file")

        print(
            f"🔍 Debug: api/app.py legacy.ssl: cert_file={cert_file}, key_file={key_file}"
        )
        print(
            f"🔍 Debug: api/app.py legacy.ssl: cert_file exists={Path(cert_file).exists() if cert_file else 'None'}"
        )
        print(
            f"🔍 Debug: api/app.py legacy.ssl: key_file exists={Path(key_file).exists() if key_file else 'None'}"
        )

        if cert_file and not Path(cert_file).exists():
            security_errors.append(
                f"Legacy SSL is enabled but certificate file not found: {cert_file}"
            )

        if key_file and not Path(key_file).exists():
            security_errors.append(
                f"Legacy SSL is enabled but private key file not found: {key_file}"
            )

        # Check mTLS configuration
        if legacy_ssl_config.get("mode") == "mtls":
            ca_cert = legacy_ssl_config.get("ca_cert")
            if ca_cert and not Path(ca_cert).exists():
                security_errors.append(
                    f"Legacy mTLS is enabled but CA certificate file not found: {ca_cert}"
                )

    # Check token authentication configuration
    token_auth_config = legacy_ssl_config.get("token_auth", {})
    if token_auth_config.get("enabled", False):
        tokens_file = token_auth_config.get("tokens_file", "tokens.json")
        if not Path(tokens_file).exists():
            security_errors.append(
                f"Token authentication is enabled but tokens file not found: {tokens_file}"
            )

    # Check general authentication
    if current_config.get("auth_enabled", False):
        # If auth is enabled, check if any authentication method is properly configured
        ssl_enabled = legacy_ssl_config.get("enabled", False)
        roles_enabled = roles_config.get("enabled", False)
        token_auth_enabled = token_auth_config.get("enabled", False)

        if not (ssl_enabled or roles_enabled or token_auth_enabled):
            security_errors.append(
                "Authentication is enabled but no authentication method is properly configured"
            )

    # If there are security errors, block startup
    if security_errors:
        get_global_logger().critical(
            "CRITICAL SECURITY ERROR: Authentication configuration issues detected:"
        )
        for error in security_errors:
            get_global_logger().critical(f"  - {error}")
        get_global_logger().critical("Server startup blocked for security reasons.")
        get_global_logger().critical(
            "Please fix authentication configuration or disable authentication features."
        )
        raise SystemExit(1)

    # Use provided parameters or defaults
    app_title = title or "MCP Proxy Adapter"
    app_description = description or "JSON-RPC API for interacting with MCP Proxy"
    app_version = version or "1.0.0"

    # Create application
    app = FastAPI(
        title=app_title,
        description=app_description,
        version=app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=create_lifespan(config_path, current_config),
    )
    
    # CRITICAL FIX: Register commands immediately during app creation
    # This ensures commands are available before the server starts accepting requests
    try:
        from mcp_proxy_adapter.commands.builtin_commands import register_builtin_commands
        get_global_logger().info("Registering built-in commands during app creation...")
        registered_count = register_builtin_commands()
        get_global_logger().info(f"Registered {registered_count} built-in commands during app creation")
    except Exception as e:
        get_global_logger().error(f"Failed to register built-in commands during app creation: {e}")
        # Don't fail app creation, but log the error

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify concrete domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware for debugging
    @app.middleware("http")
    async def debug_request_middleware(request: Request, call_next):
        get_global_logger().debug(f"FastAPI Request START: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            get_global_logger().debug(f"FastAPI Request COMPLETED: {response.status_code}")
            return response
        except Exception as e:
            get_global_logger().error(f"FastAPI Request ERROR: {e}", exc_info=True)
            raise

    # Setup middleware using the new middleware package
    setup_middleware(app, current_config)
    
    # Add request logging middleware
    # @app.middleware("http")
    # async def log_requests(request: Request, call_next):
    #     get_global_logger().info(f"🔍 REQUEST LOG: {request.method} {request.url.path}")
    #     get_global_logger().info(f"🔍 REQUEST LOG: Headers: {dict(request.headers)}")
    #     get_global_logger().info(f"🔍 REQUEST LOG: Client: {request.client}")
    #     response = await call_next(request)
    #     get_global_logger().info(f"🔍 RESPONSE LOG: Status: {response.status_code}")
    #     return response

    # Use custom OpenAPI schema
    app.openapi = lambda: custom_openapi_with_fallback(app)

    # Explicit endpoint for OpenAPI schema
    @app.get("/openapi.json")
    async def get_openapi_schema():
        """
        Returns optimized OpenAPI schema compatible with MCP-Proxy.
        """
        return custom_openapi_with_fallback(app)

    # JSON-RPC handler
    @app.post(
        "/api/jsonrpc",
        response_model=Union[
            JsonRpcSuccessResponse,
            JsonRpcErrorResponse,
            List[Union[JsonRpcSuccessResponse, JsonRpcErrorResponse]],
        ],
    )
    async def jsonrpc_endpoint(
        request: Request,
        request_data: Union[Dict[str, Any], List[Dict[str, Any]]] = Body(...),
    ):
        """
        Endpoint for handling JSON-RPC requests.
        Supports both single and batch requests.
        """
        # Get request_id from middleware state
        request_id = getattr(request.state, "request_id", None)

        # Create request get_global_logger() for this endpoint
        req_logger = RequestLogger(__name__, request_id) if request_id else get_global_logger()

        # Check if it's a batch request
        if isinstance(request_data, list):
            # Process batch request
            if len(request_data) == 0:
                # Empty batch request is invalid
                req_logger.warning("Invalid Request: Empty batch request")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request. Empty batch request",
                        },
                        "id": None,
                    },
                )
            return await handle_batch_json_rpc(request_data, request)
        else:
            # Process single request
            return await handle_json_rpc(request_data, request_id, request)

    # Command execution endpoint (/cmd)
    @app.post("/cmd")
    async def cmd_endpoint(request: Request, command_data: Dict[str, Any] = Body(...)):
        """
        Universal endpoint for executing commands.
        Supports two formats:
        1. CommandRequest:
        {
            "command": "command_name",
            "params": {
                // Command parameters
            }
        }

        2. JSON-RPC:
        {
            "jsonrpc": "2.0",
            "method": "command_name",
            "params": {
                // Command parameters
            },
            "id": 123
        }
        """
        # Get request_id from middleware state
        request_id = getattr(request.state, "request_id", None)

        # Create request get_global_logger() for this endpoint
        req_logger = RequestLogger(__name__, request_id) if request_id else get_global_logger()

        try:
            # Determine request format (CommandRequest or JSON-RPC)
            if "jsonrpc" in command_data and "method" in command_data:
                # JSON-RPC format
                return await handle_json_rpc(command_data, request_id, request)

            # CommandRequest format
            if "command" not in command_data:
                req_logger.warning("Missing required field 'command'")
                return JSONResponse(
                    status_code=200,
                    content={
                        "error": {
                            "code": -32600,
                            "message": "Отсутствует обязательное поле 'command'",
                        }
                    },
                )

            command_name = command_data["command"]
            params = command_data.get("params", {})

            req_logger.debug(
                f"Executing command via /cmd: {command_name}, params: {params}"
            )

            # Check if command exists
            if not registry.command_exists(command_name):
                req_logger.warning(f"Command '{command_name}' not found")
                return JSONResponse(
                    status_code=200,
                    content={
                        "error": {
                            "code": -32601,
                            "message": f"Команда '{command_name}' не найдена",
                        }
                    },
                )

            # Execute command
            try:
                result = await execute_command(
                    command_name, params, request_id, request
                )
                return {"result": result}
            except MicroserviceError as e:
                # Handle command execution errors
                req_logger.error(f"Error executing command '{command_name}': {str(e)}")
                return JSONResponse(status_code=200, content={"error": e.to_dict()})
            except NotFoundError as e:
                # Специальная обработка для help-команды: возвращаем result с пустым commands и error
                if command_name == "help":
                    return {
                        "result": {
                            "success": False,
                            "commands": {},
                            "error": str(e),
                            "note": 'To get detailed information about a specific command, call help with parameter: POST /cmd {"command": "help", "params": {"cmdname": "<command_name>"}}',
                        }
                    }
                # Для остальных команд — стандартная ошибка
                return JSONResponse(
                    status_code=200,
                    content={"error": {"code": e.code, "message": str(e)}},
                )

        except json.JSONDecodeError:
            req_logger.error("JSON decode error")
            return JSONResponse(
                status_code=200,
                content={"error": {"code": -32700, "message": "Parse error"}},
            )
        except Exception as e:
            req_logger.exception(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=200,
                content={
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": {"details": str(e)},
                    }
                },
            )

    # Direct command call
    @app.post("/api/command/{command_name}")
    async def command_endpoint(
        request: Request, command_name: str, params: Dict[str, Any] = Body(default={})
    ):
        """
        Endpoint for direct command call.
        """
        # Get request_id from middleware state
        request_id = getattr(request.state, "request_id", None)

        try:
            result = await execute_command(command_name, params, request_id, request)
            return result
        except MicroserviceError as e:
            # Convert to proper HTTP status code
            status_code = 400 if e.code < 0 else e.code
            return JSONResponse(status_code=status_code, content=e.to_dict())

    # Server health check
    @app.get("/health", operation_id="health_check")
    async def health_endpoint():
        """
        Health check endpoint.
        Returns server status and basic information.
        """
        return {"status": "ok", "model": "mcp-proxy-adapter", "version": "1.0.0"}

    # Graceful shutdown endpoint
    @app.post("/shutdown")
    async def shutdown_endpoint():
        """
        Graceful shutdown endpoint.
        Triggers server shutdown after completing current requests.
        """
        import asyncio

        # Schedule shutdown after a short delay to allow response
        async def delayed_shutdown():
            await asyncio.sleep(1)
            # This will trigger the lifespan shutdown event
            import os

            os._exit(0)

        # Start shutdown task
        asyncio.create_task(delayed_shutdown())

        return {
            "status": "shutting_down",
            "message": "Server shutdown initiated. New requests will be rejected.",
        }

    # List of available commands
    @app.get("/api/commands", response_model=CommandListResponse)
    async def commands_list_endpoint():
        """
        Endpoint for getting list of available commands.
        """
        commands = await get_commands_list()
        return {"commands": commands}

    # Get command information by name
    @app.get("/api/commands/{command_name}")
    async def command_info_endpoint(request: Request, command_name: str):
        """
        Endpoint for getting information about a specific command.
        """
        # Get request_id from middleware state
        request_id = getattr(request.state, "request_id", None)

        # Create request get_global_logger() for this endpoint
        req_logger = RequestLogger(__name__, request_id) if request_id else get_global_logger()

        try:
            command_info = registry.get_command_info(command_name)
            return command_info
        except NotFoundError as e:
            req_logger.warning(f"Command '{command_name}' not found")
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": 404,
                        "message": f"Command '{command_name}' not found",
                    }
                },
            )

    # Get API tool description
    @app.get("/api/tools/{tool_name}")
    async def tool_description_endpoint(tool_name: str, format: Optional[str] = "json"):
        """
        Получить подробное описание инструмента API.

        Возвращает полное описание инструмента API с доступными командами,
        их параметрами и примерами использования. Формат возвращаемых данных
        может быть JSON или Markdown (text).

        Args:
            tool_name: Имя инструмента API
            format: Формат вывода (json, text, markdown, html)
        """
        try:
            description = get_tool_description(tool_name, format)

            if format.lower() in ["text", "markdown", "html"]:
                if format.lower() == "html":
                    return Response(content=description, media_type="text/html")
                else:
                    return JSONResponse(
                        content={"description": description},
                        media_type="application/json",
                    )
            else:
                return description

        except NotFoundError as e:
            get_global_logger().warning(f"Tool not found: {tool_name}")
            return JSONResponse(
                status_code=404, content={"error": {"code": 404, "message": str(e)}}
            )
        except Exception as e:
            get_global_logger().exception(f"Error generating tool description: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": f"Error generating tool description: {str(e)}",
                    }
                },
            )

    # Execute API tool
    @app.post("/api/tools/{tool_name}")
    async def execute_tool_endpoint(tool_name: str, params: Dict[str, Any] = Body(...)):
        """
        Выполнить инструмент API с указанными параметрами.

        Args:
            tool_name: Имя инструмента API
            params: Параметры инструмента
        """
        try:
            result = await execute_tool(tool_name, **params)
            return result
        except NotFoundError as e:
            get_global_logger().warning(f"Tool not found: {tool_name}")
            return JSONResponse(
                status_code=404, content={"error": {"code": 404, "message": str(e)}}
            )
        except Exception as e:
            get_global_logger().exception(f"Error executing tool {tool_name}: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {"code": 500, "message": f"Error executing tool: {str(e)}"}
                },
            )

    return app
