# flake8: noqa: E501
"""
Module for proxy registration functionality with security framework integration.

This module handles automatic registration and unregistration of the server
with the MCP proxy server during startup and shutdown, using mcp_security_framework
for secure connections and authentication.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import time
import ssl
import traceback
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from urllib.parse import urljoin

import aiohttp
import os
import glob

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.core.client_security import create_client_security_manager


class ProxyRegistrationError(Exception):
    """Exception raised when proxy registration fails."""

    pass


class ProxyRegistrationManager:
    """
    Manager for proxy registration functionality with security framework integration.

    Handles automatic registration and unregistration of the server
    with the MCP proxy server using secure authentication methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the proxy registration manager.

        Args:
            config: Application configuration
        """
        self.config = config
        # Try both registration and proxy_registration for backward compatibility
        self.registration_config = config.get(
            "registration", config.get("proxy_registration", {})
        )
        # Auto-fill minimal TLS settings from global SSL if missing to support minimal config
        try:
            reg_ssl = self.registration_config.get("ssl", {})
            if not isinstance(reg_ssl, dict):
                reg_ssl = {}
            global_ssl = config.get("security", {}).get("ssl", {}) or config.get("ssl", {})
            if isinstance(global_ssl, dict):
                if not reg_ssl.get("ca_cert") and global_ssl.get("ca_cert"):
                    reg_ssl["ca_cert"] = global_ssl.get("ca_cert")
                # Keep verify_mode if already set; default to CERT_REQUIRED if global verify_client true
                if not reg_ssl.get("verify_mode") and isinstance(global_ssl.get("verify_client"), bool):
                    reg_ssl["verify_mode"] = "CERT_REQUIRED" if global_ssl.get("verify_client") else "CERT_NONE"
            if reg_ssl:
                self.registration_config["ssl"] = reg_ssl
        except Exception:
            pass

        # Check if registration is enabled
        self.enabled = self.registration_config.get("enabled", False)
        
        # Basic registration settings - only validate if enabled
        if self.enabled:
            self.proxy_url = self.registration_config.get("proxy_url")
            if not self.proxy_url:
                raise ValueError(
                    "proxy_url is required in registration configuration. "
                    "Please specify a valid proxy URL in your configuration."
                )
        else:
            self.proxy_url = None
            
        if self.enabled:
            self.server_id = self.registration_config.get("server_id")
            if not self.server_id:
                # Try to get from proxy_info.name as fallback
                self.server_id = self.registration_config.get("proxy_info", {}).get("name")
                if not self.server_id:
                    raise ValueError(
                        "server_id is required in registration configuration. "
                        "Please specify a server_id or proxy_info.name in your configuration."
                    )
            # UUID is mandatory for registration payload
            # Try to get UUID from proxy_registration section first, then from root config
            self.uuid = self.registration_config.get("uuid") or self.config.get("uuid")
            if not self.uuid:
                raise ValueError(
                    "uuid is required in registration configuration. "
                    "Please specify a UUID under 'proxy_registration.uuid' or at root level in your configuration."
                )
            
            # Validate UUID4 format
            import re
            uuid4_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            if not re.match(uuid4_pattern, self.uuid, re.IGNORECASE):
                error_msg = f"Invalid UUID4 format: '{self.uuid}'. Expected format: xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx"
                get_global_logger().error(f"❌ UUID validation failed: {error_msg}")
                raise ValueError(error_msg)
            
            get_global_logger().info(f"✅ UUID validation passed: {self.uuid}")
            self.server_name = self.registration_config.get("server_name")
            if not self.server_name:
                # Try to get from proxy_info.name as fallback
                self.server_name = self.registration_config.get("proxy_info", {}).get("name")
                if not self.server_name:
                    raise ValueError(
                        "server_name is required in registration configuration. "
                        "Please specify a server_name or proxy_info.name in your configuration."
                    )
            self.description = self.registration_config.get("description")
            if not self.description:
                # Try to get from proxy_info.description as fallback
                self.description = self.registration_config.get("proxy_info", {}).get("description")
                if not self.description:
                    raise ValueError(
                        "description is required in registration configuration. "
                        "Please specify a description or proxy_info.description in your configuration."
                    )
        else:
            self.server_id = None
            self.uuid = None
            self.server_name = None
            self.description = None
            
        if self.enabled:
            self.version = self.registration_config.get("version")
            if not self.version:
                # Try to get from proxy_info.version as fallback
                self.version = self.registration_config.get("proxy_info", {}).get("version")
                if not self.version:
                    raise ValueError(
                        "version is required in registration configuration. "
                        "Please specify a version or proxy_info.version in your configuration."
                    )
        else:
            self.version = None

        # Heartbeat settings - only validate if enabled
        if self.enabled:
            heartbeat_config = self.registration_config.get("heartbeat", {})
            heartbeat_enabled = heartbeat_config.get("enabled", True)
            
            if heartbeat_enabled:
                self.timeout = heartbeat_config.get("timeout")
                if self.timeout is None:
                    raise ValueError(
                        "heartbeat.timeout is required in registration configuration. "
                        "Please specify a timeout value."
                    )
                self.retry_attempts = heartbeat_config.get("retry_attempts")
                if self.retry_attempts is None:
                    raise ValueError(
                        "heartbeat.retry_attempts is required in registration configuration. "
                        "Please specify a retry_attempts value."
                    )
                self.retry_delay = heartbeat_config.get("retry_delay")
                if self.retry_delay is None:
                    raise ValueError(
                        "heartbeat.retry_delay is required in registration configuration. "
                        "Please specify a retry_delay value."
                    )
                self.heartbeat_interval = heartbeat_config.get("interval")
                if self.heartbeat_interval is None:
                    raise ValueError(
                        "heartbeat.interval is required in registration configuration. "
                        "Please specify an interval value."
                    )
            else:
                # Heartbeat disabled - use defaults
                self.timeout = heartbeat_config.get("timeout", 30)
                self.retry_attempts = heartbeat_config.get("retry_attempts", 3)
                self.retry_delay = heartbeat_config.get("retry_delay", 5)
                self.heartbeat_interval = heartbeat_config.get("interval", 30)
        else:
            self.timeout = None
            self.retry_attempts = None
            self.retry_delay = None
            self.heartbeat_interval = None

        # Auto registration settings
        if self.enabled:
            self.auto_register = self.registration_config.get("enabled")
            if self.auto_register is None:
                raise ValueError(
                    "enabled is required in registration configuration. "
                    "Please specify whether registration is enabled (true/false)."
                )
        else:
            self.auto_register = False
            
        self.auto_unregister = True  # Always unregister on shutdown

        # Initialize client security manager
        self.client_security = create_client_security_manager(config)

        # Registration state
        self.registered = False
        self.server_key: Optional[str] = None
        self.server_url: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        get_global_logger().info(
            "Proxy registration manager initialized with security framework integration"
        )

    def is_enabled(self) -> bool:
        """
        Check if proxy registration is enabled.

        Returns:
            True if registration is enabled, False otherwise.
        """
        return self.enabled

    def set_server_url(self, server_url: str) -> None:
        """
        Set the server URL for registration.

        Args:
            server_url: The URL where this server is accessible.
        """
        self.server_url = server_url
        get_global_logger().info(f"Proxy registration server URL set to: {server_url}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for registration requests.

        Returns:
            Dictionary of authentication headers
        """
        if not self.client_security:
            return {"Content-Type": "application/json"}

        auth_method = self.registration_config.get("auth_method", "certificate")

        if auth_method == "certificate":
            return self.client_security.get_client_auth_headers("certificate")
        elif auth_method == "token":
            token_config = self.registration_config.get("token", {})
            token = token_config.get("token")
            return self.client_security.get_client_auth_headers("jwt", token=token)
        elif auth_method == "api_key":
            api_key_config = self.registration_config.get("api_key", {})
            api_key = api_key_config.get("key")
            return self.client_security.get_client_auth_headers(
                "api_key", api_key=api_key
            )
        else:
            return {"Content-Type": "application/json"}

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for secure connections using registration SSL configuration.

        Returns:
            SSL context or None if SSL not needed
        """
        get_global_logger().debug("_create_ssl_context called")
        
        # Decide SSL strictly by proxy URL scheme: use SSL only for https proxy URLs
        try:
            from urllib.parse import urlparse as _urlparse
            scheme = _urlparse(self.proxy_url).scheme if self.proxy_url else "http"
            if scheme.lower() != "https":
                get_global_logger().debug("Proxy URL is HTTP, skipping SSL context creation for registration")
                return None
        except Exception:
            get_global_logger().debug("Failed to parse proxy_url, assuming HTTP and skipping SSL context")
            return None
            
        if not self.client_security:
            get_global_logger().debug("SSL context creation failed: client_security is None")
            return None

        try:
            # Check if SSL is enabled for registration
            cert_config = self.registration_config.get("certificate", {})
            ssl_config = self.registration_config.get("ssl", {})

            # FALLBACK: if no explicit registration SSL/certs provided, reuse global SSL config
            if not cert_config and not ssl_config:
                global_ssl = self.config.get("security", {}).get("ssl", {}) or self.config.get("ssl", {})
                if global_ssl:
                    # Map global ssl to registration-style configs
                    mapped_cert = {}
                    if global_ssl.get("cert_file") and global_ssl.get("key_file"):
                        mapped_cert = {
                            "cert_file": global_ssl.get("cert_file"),
                            "key_file": global_ssl.get("key_file"),
                        }
                    mapped_ssl = {}
                    if global_ssl.get("ca_cert"):
                        mapped_ssl["ca_cert"] = global_ssl.get("ca_cert")
                    if global_ssl.get("verify_client") is not None:
                        mapped_ssl["verify_mode"] = (
                            "CERT_REQUIRED" if global_ssl.get("verify_client") else "CERT_NONE"
                        )
                    cert_config = mapped_cert
                    ssl_config = mapped_ssl

            # If still no client certificate specified, raise clear error
            if not cert_config or not cert_config.get("cert_file") or not cert_config.get("key_file"):
                raise ValueError(
                    "Client certificate configuration is required for mTLS proxy registration. "
                    "Please configure 'proxy_registration.certificate.cert_file' and 'proxy_registration.certificate.key_file' "
                    "in your configuration file."
                )

            get_global_logger().debug(
                f"SSL context creation: cert_config={cert_config}, ssl_config={ssl_config}"
            )

            # SSL is enabled if certificate config exists or SSL config exists
            if cert_config or ssl_config:
                # Create a custom SSL context based on registration configuration
                ca_file = ssl_config.get("ca_cert") if isinstance(ssl_config, dict) else None
                if ca_file and Path(ca_file).exists():
                    context = ssl.create_default_context(cafile=ca_file)
                else:
                    # No CA certificate configured - use system default
                    context = ssl.create_default_context()
                    get_global_logger().warning(
                        "No CA certificate configured for proxy registration. "
                        "This may cause SSL verification failures if the proxy uses self-signed certificates. "
                        "Consider configuring 'proxy_registration.ssl.ca_cert' in your configuration file."
                    )

                # Load client certificates if provided
                if cert_config:
                    cert_file = cert_config.get("cert_file")
                    key_file = cert_config.get("key_file")

                    if cert_file and key_file:
                        context.load_cert_chain(cert_file, key_file)
                        get_global_logger().debug(
                            f"Loaded client certificates for mTLS: cert={cert_file}, key={key_file}"
                        )

                # Configure SSL verification based on registration settings
                if ssl_config:
                    ca_cert_file = ssl_config.get("ca_cert")
                    verify_mode = ssl_config.get("verify_mode", "CERT_REQUIRED")
                    verify_ssl = ssl_config.get("verify_ssl", True)
                    verify_hostname = ssl_config.get("verify_hostname", True)  # ✅ Read verify_hostname setting

                    # Load CA certificate if provided
                    if ca_cert_file:
                        context.load_verify_locations(ca_cert_file)
                        get_global_logger().debug(f"Loaded CA certificate: {ca_cert_file}")

                    # Check if verify_ssl is disabled in ssl_config
                    if verify_ssl == False:
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        get_global_logger().debug("SSL verification disabled (verify_ssl=False)")
                    elif verify_mode == "CERT_NONE":
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        get_global_logger().debug("SSL verification disabled (CERT_NONE)")
                    elif verify_mode == "CERT_REQUIRED":
                        context.check_hostname = verify_hostname  # ✅ Use verify_hostname setting
                        context.verify_mode = ssl.CERT_REQUIRED
                        get_global_logger().debug(f"SSL verification enabled (CERT_REQUIRED), hostname check: {verify_hostname}")
                    else:
                        # For test environments, default to CERT_NONE to avoid certificate issues
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        get_global_logger().debug("SSL verification disabled (default for test environment)")
                else:
                    # No specific ssl_config, default to CERT_NONE for test environments
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    get_global_logger().debug("Using CERT_NONE for test environment (no ssl_config)")

                get_global_logger().info("Created custom SSL context for proxy registration")
                return context
            else:
                get_global_logger().debug(
                    "SSL context creation skipped: no cert_config or ssl_config"
                )

            return None
        except Exception as e:
            get_global_logger().warning(f"Failed to create SSL context: {e}")
            # Don't fail the entire operation, just return None
            return None

    async def register_server(self) -> bool:
        """
        Register the server with the proxy using secure authentication.

        Returns:
            True if registration was successful, False otherwise.
        """
        if not self.is_enabled():
            get_global_logger().info("Proxy registration is disabled in configuration")
            return False

        if not self.server_url:
            get_global_logger().error("Server URL not set, cannot register with proxy")
            return False

        # Normalize server_url for docker host if needed
        try:
            if self.server_url:
                from urllib.parse import urlparse, urlunparse
                import os as _os
                parsed = urlparse(self.server_url)
                if parsed.hostname in ("localhost", "127.0.0.1"):
                    docker_addr = _os.getenv("DOCKER_HOST_ADDR", "172.17.0.1")
                    port = parsed.port
                    if not port:
                        port = 443 if parsed.scheme == "https" else 80
                    new_netloc = f"{docker_addr}:{port}"
                    normalized = urlunparse(parsed._replace(netloc=new_netloc))
                    if normalized != self.server_url:
                        self.server_url = normalized
                        get_global_logger().info(
                            f"Normalized server_url for docker host: {self.server_url}"
                        )
        except Exception as _e:
            get_global_logger().debug(f"server_url normalization skipped: {_e}")

        # Prepare registration data with proxy info
        proxy_info = self.registration_config.get("proxy_info", {})
        registration_data = {
            "server_id": self.server_id,
            "uuid": self.uuid,
            "server_url": self.server_url,
            "server_name": self.server_name,
            "description": self.description,
            "version": self.version,
            "capabilities": proxy_info.get("capabilities", ["jsonrpc", "rest"]),
            "endpoints": proxy_info.get(
                "endpoints",
                {"jsonrpc": "/api/jsonrpc", "rest": "/cmd", "health": "/health"},
            ),
        }

        get_global_logger().info(f"Attempting to register server with proxy at {self.proxy_url}")
        get_global_logger().debug(f"Registration data: {registration_data}")

        # Do not block application startup: single attempt, no sleeps here
        for attempt in range(1):
            try:
                success, result = await self._make_secure_registration_request(
                    registration_data
                )

                if success:
                    self.registered = True
                    # Safely extract server_key from result
                    if isinstance(result, dict):
                        self.server_key = result.get("server_key")
                    else:
                        self.server_key = None
                    get_global_logger().info(
                        f"✅ Successfully registered with proxy. Server key: {self.server_key}"
                    )

                    # Start heartbeat if enabled
                    if self.registration_config.get("heartbeat", {}).get(
                        "enabled", True
                    ):
                        await self._start_heartbeat()

                    return True
                else:
                    # Be robust if result is not a dict
                    error_msg = None
                    get_global_logger().error(f"DEBUG: result type = {type(result)}, result = {result}")
                    if isinstance(result, dict):
                        get_global_logger().error(f"DEBUG: result is dict, getting error field")
                        error_field = result.get("error", {})
                        get_global_logger().error(f"DEBUG: error_field type = {type(error_field)}, error_field = {error_field}")
                        if isinstance(error_field, dict):
                            error_msg = error_field.get("message", "Unknown error")
                        elif isinstance(error_field, str):
                            error_msg = error_field
                        else:
                            error_msg = str(error_field)

                        # Auto-recovery: already registered case → force unregistration then retry once
                        error_code = result.get("error_code") or (result.get("error", {}).get("code") if isinstance(result.get("error"), dict) else None)
                        already_registered = False
                        existing_server_key = None
                        # Prefer structured detail if provided
                        if isinstance(result.get("details"), dict):
                            existing_server_key = result.get("details", {}).get("existing_server_key")
                        # Fallback: parse from error message text
                        if not existing_server_key and isinstance(error_msg, str) and "already registered as" in error_msg:
                            try:
                                # Expecting: "... already registered as <server_id>_<copy_number>"
                                tail = error_msg.split("already registered as", 1)[1].strip()
                                existing_server_key = tail.split()[0]
                            except Exception:
                                existing_server_key = None

                        if (error_code in ("DUPLICATE_SERVER_URL", "REGISTRATION_ERROR") or already_registered) and existing_server_key:
                            try:
                                get_global_logger().info(f"Attempting auto-unregistration of existing instance: {existing_server_key}")
                                # Build unregistration payload using parsed server_key
                                try:
                                    copy_number = int(existing_server_key.split("_")[-1])
                                except Exception:
                                    copy_number = 1
                                unregistration_data = {"server_id": self.server_id, "copy_number": copy_number}
                                # Reuse secure unregistration request directly
                                unreg_success, _unreg_result = await self._make_secure_unregistration_request(unregistration_data)
                                if unreg_success:
                                    get_global_logger().info("Auto-unregistration succeeded, retrying registration once...")
                                    # Retry registration once immediately
                                    retry_success, retry_result = await self._make_secure_registration_request(registration_data)
                                    if retry_success:
                                        self.registered = True
                                        if isinstance(retry_result, dict):
                                            self.server_key = retry_result.get("server_key")
                                        else:
                                            self.server_key = None
                                        get_global_logger().info(f"✅ Successfully registered after auto-unregistration. Server key: {self.server_key}")
                                        if self.registration_config.get("heartbeat", {}).get("enabled", True):
                                            await self._start_heartbeat()
                                        return True
                                    else:
                                        get_global_logger().warning(f"Retry registration failed after auto-unregistration: {retry_result}")
                                else:
                                    get_global_logger().warning(f"Auto-unregistration failed: {_unreg_result}")
                            except Exception as _auto_e:
                                get_global_logger().warning(f"Auto-unregistration/registration flow error: {_auto_e}")
                    else:
                        error_msg = str(result)
                    get_global_logger().warning(
                        f"❌ Registration attempt {attempt + 1} failed: {error_msg}"
                    )

            except Exception as e:
                get_global_logger().error(
                    f"❌ Registration attempt {attempt + 1} failed with exception: {e}"
                )
                get_global_logger().error(f"Full traceback: {traceback.format_exc()}")

        get_global_logger().error(
            f"❌ Failed to register with proxy after {self.retry_attempts} attempts"
        )
        return False

    async def unregister_server(self) -> bool:
        """
        Unregister the server from the proxy.

        Returns:
            True if unregistration was successful, False otherwise.
        """
        if not self.is_enabled():
            get_global_logger().info("Proxy registration is disabled, skipping unregistration")
            return True

        if not self.registered or not self.server_key:
            get_global_logger().info("Server not registered with proxy, skipping unregistration")
            return True

        # Stop heartbeat
        await self._stop_heartbeat()

        # Extract copy_number from server_key (format: server_id_copy_number)
        try:
            copy_number = int(self.server_key.split("_")[-1])
        except (ValueError, IndexError):
            copy_number = 1

        unregistration_data = {"server_id": self.server_id, "copy_number": copy_number}

        get_global_logger().info(f"Attempting to unregister server from proxy at {self.proxy_url}")
        get_global_logger().debug(f"Unregistration data: {unregistration_data}")

        try:
            success, result = await self._make_secure_unregistration_request(
                unregistration_data
            )

            if success:
                unregistered = result.get("unregistered", False)
                if unregistered:
                    get_global_logger().info("✅ Successfully unregistered from proxy")
                else:
                    get_global_logger().warning("⚠️ Server was not found in proxy registry")

                self.registered = False
                self.server_key = None
                return True
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                get_global_logger().error(f"❌ Failed to unregister from proxy: {error_msg}")
                return False

        except Exception as e:
            get_global_logger().error(f"❌ Unregistration failed with exception: {e}")
            return False

    async def _make_secure_registration_request(
        self, data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Make secure registration request to proxy using security framework.

        Args:
            data: Registration data.

        Returns:
            Tuple of (success, result).
        """
        url = urljoin(self.proxy_url, "/register")

        # Get authentication headers
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"

        # Create SSL context if needed
        ssl_context = self._create_ssl_context()

        # Create connector with SSL context
        connector = None
        if ssl_context:
            connector = aiohttp.TCPConnector(ssl=ssl_context)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    try:
                        result = await response.json()
                        get_global_logger().debug(f"Response JSON parsed successfully: {type(result)} - {result}")
                    except Exception as e:
                        text_body = await response.text()
                        get_global_logger().debug(f"JSON parsing failed: {e}, text_body: {text_body}")
                        result = {"success": False, "error": {"code": "NON_JSON_RESPONSE", "message": text_body}}

                    # Validate response headers if security framework available
                    if self.client_security:
                        self.client_security.validate_server_response(
                            dict(response.headers)
                        )

                    # Check both HTTP status and JSON success field
                    if response.status == 200:
                        success = result.get("success", False)
                        if not success:
                            error_info = result.get("error", {})
                            error_msg = error_info.get("message", "Unknown error")
                            error_code = error_info.get("code", "UNKNOWN_ERROR")

                            # Handle duplicate server URL as successful registration
                            if error_code == "DUPLICATE_SERVER_URL":
                                get_global_logger().info(
                                    f"✅ Server already registered: {error_msg}"
                                )
                                # Extract server_key from details if available
                                details = error_info.get("details", {})
                                existing_server_key = details.get("existing_server_key")
                                if existing_server_key:
                                    result["server_key"] = existing_server_key
                                    get_global_logger().info(
                                        f"✅ Retrieved existing server key: {existing_server_key}"
                                    )
                                # Return success=True for duplicate registration
                                return True, result
                            else:
                                get_global_logger().warning(
                                    f"Registration failed: {error_code} - {error_msg}"
                                )
                        return success, result
                    else:
                        get_global_logger().warning(
                            f"Registration failed with HTTP status: {response.status}"
                        )
                        # Ensure result is a dict for consistent error handling
                        if isinstance(result, str):
                            result = {"success": False, "error": {"code": "HTTP_ERROR", "message": result}}
                        return False, result
        finally:
            if connector:
                await connector.close()

    async def _make_secure_unregistration_request(
        self, data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Make secure unregistration request to proxy using security framework.

        Args:
            data: Unregistration data.

        Returns:
            Tuple of (success, result).
        """
        url = urljoin(self.proxy_url, "/unregister")

        # Get authentication headers
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"

        # Create SSL context if needed
        ssl_context = self._create_ssl_context()

        # Create connector with SSL context
        connector = None
        if ssl_context:
            connector = aiohttp.TCPConnector(ssl=ssl_context)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    result = await response.json()

                    # Validate response headers if security framework available
                    if self.client_security:
                        self.client_security.validate_server_response(
                            dict(response.headers)
                        )

                    # Check both HTTP status and JSON success field
                    if response.status == 200:
                        success = result.get("success", False)
                        if not success:
                            error_info = result.get("error", {})
                            error_msg = error_info.get("message", "Unknown error")
                            error_code = error_info.get("code", "UNKNOWN_ERROR")
                            get_global_logger().warning(
                                f"Unregistration failed: {error_code} - {error_msg}"
                            )
                        return success, result
                    else:
                        get_global_logger().warning(
                            f"Unregistration failed with HTTP status: {response.status}"
                        )
                        return False, result
        finally:
            if connector:
                await connector.close()

    async def _start_heartbeat(self) -> None:
        """Start heartbeat task for keeping registration alive."""
        if self.heartbeat_task and not self.heartbeat_task.done():
            return

        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        get_global_logger().info("Heartbeat task started")

    async def _stop_heartbeat(self) -> None:
        """Stop heartbeat task."""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            get_global_logger().info("Heartbeat task stopped")

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop to keep registration alive."""
        while self.registered:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if not self.registered:
                    break

                # Send heartbeat
                success = await self._send_heartbeat()
                if not success:
                    get_global_logger().warning("Heartbeat failed, attempting to re-register")
                    await self.register_server()

            except asyncio.CancelledError:
                break
            except Exception as e:
                get_global_logger().error(f"Heartbeat error: {e}")

    async def heartbeat(self) -> bool:
        """
        Public method to send heartbeat to proxy server.
        
        Returns:
            True if heartbeat was successful, False otherwise.
        """
        return await self._send_heartbeat()

    async def _send_heartbeat(self) -> bool:
        """Send heartbeat to proxy server."""
        if not self.server_key:
            return False

        url = urljoin(self.proxy_url, "/heartbeat")

        # Get authentication headers
        headers = self._get_auth_headers()

        # Create SSL context if needed
        ssl_context = self._create_ssl_context()

        # Create connector with SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Prefer GET heartbeat (container exposes GET /heartbeat)
                try:
                    async with session.get(url, headers=headers, timeout=timeout) as resp:
                        if resp.status == 200:
                            get_global_logger().debug("Heartbeat (GET) succeeded")
                            return True
                        # If method not allowed, fall back to POST
                        if resp.status != 405:
                            get_global_logger().warning(
                                f"Heartbeat (GET) failed with status: {resp.status}"
                            )
                except Exception as ge:
                    get_global_logger().debug(f"Heartbeat (GET) error: {ge}")

                # Fallback to POST if GET not supported
                heartbeat_data = {
                    "server_id": self.server_id,
                    "server_key": self.server_key,
                    "timestamp": int(time.time()),
                }
                post_headers = dict(headers)
                post_headers["Content-Type"] = "application/json"
                async with session.post(
                    url, json=heartbeat_data, headers=post_headers, timeout=timeout
                ) as resp:
                    if resp.status == 200:
                        get_global_logger().debug("Heartbeat (POST) succeeded")
                        return True
                        get_global_logger().warning(
                        f"Heartbeat (POST) failed with status: {resp.status}"
                        )
                        return False
        except Exception as e:
            get_global_logger().error(f"Heartbeat error: {e}")
            return False
        finally:
            if connector:
                await connector.close()

    def get_registration_status(self) -> Dict[str, Any]:
        """
        Get current registration status.

        Returns:
            Dictionary with registration status information.
        """
        status = {
            "enabled": self.is_enabled(),
            "registered": self.registered,
            "server_key": self.server_key,
            "server_url": self.server_url,
            "proxy_url": self.proxy_url,
            "server_id": self.server_id,
            "heartbeat_active": self.heartbeat_task is not None
            and not self.heartbeat_task.done(),
        }

        # Add security information if available
        if self.client_security:
            status["security_enabled"] = True
            status["ssl_enabled"] = self.client_security.is_ssl_enabled()
            status["auth_methods"] = self.client_security.get_supported_auth_methods()

            cert_info = self.client_security.get_client_certificate_info()
            if cert_info:
                status["client_certificate"] = cert_info
        else:
            status["security_enabled"] = False

        return status


# Global proxy registration manager instance (will be initialized with config)
proxy_registration_manager: Optional[ProxyRegistrationManager] = None


def initialize_proxy_registration(config: Dict[str, Any]) -> None:
    """
    Initialize global proxy registration manager.

    Args:
        config: Application configuration
    """
    global proxy_registration_manager
    proxy_registration_manager = ProxyRegistrationManager(config)


async def register_with_proxy(server_url: str) -> bool:
    """
    Register the server with the proxy.

    Args:
        server_url: The URL where this server is accessible.

    Returns:
        True if registration was successful, False otherwise.
    """
    if not proxy_registration_manager:
        get_global_logger().error("Proxy registration manager not initialized")
        return False

    proxy_registration_manager.set_server_url(server_url)
    return await proxy_registration_manager.register_server()


async def unregister_from_proxy() -> bool:
    """
    Unregister the server from the proxy.

    Returns:
        True if unregistration was successful, False otherwise.
    """
    if not proxy_registration_manager:
        get_global_logger().error("Proxy registration manager not initialized")
        return False

    return await proxy_registration_manager.unregister_server()


def get_proxy_registration_status() -> Dict[str, Any]:
    """
    Get current proxy registration status.

    Returns:
        Dictionary with registration status information.
    """
    if not proxy_registration_manager:
        return {"error": "Proxy registration manager not initialized"}

    return proxy_registration_manager.get_registration_status()
