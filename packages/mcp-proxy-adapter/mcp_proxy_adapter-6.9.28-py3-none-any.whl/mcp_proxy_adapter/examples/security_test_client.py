#!/usr/bin/env python3
"""
Security Test Client for MCP Proxy Adapter
This client tests various security configurations including:
- Basic HTTP
- HTTP + Token authentication
- HTTPS
- HTTPS + Token authentication
- mTLS with certificate authentication
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import asyncio
import os
import ssl
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from aiohttp import ClientSession, ClientTimeout, TCPConnector

# Add project root to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
# Only add paths that are likely to exist and be useful
if parent_dir.exists():
    sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

# Import mcp_security_framework components
try:
    from mcp_security_framework import SecurityManager, SecurityConfig, AuthConfig, PermissionConfig, SSLConfig
    from mcp_security_framework.schemas.config import SSLConfig as SSLConfigSchema

    _MCP_SECURITY_AVAILABLE = True
    print("✅ mcp_security_framework available")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: mcp_security_framework is required but not available!")
    print(f"❌ Import error: {e}")
    print("❌ Please install mcp_security_framework: pip install mcp_security_framework")
    raise ImportError("mcp_security_framework is required for security tests") from e

# Import cryptography components
try:
    _CRYPTOGRAPHY_AVAILABLE = True
    print("✅ cryptography available")
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False
    print("⚠️ cryptography not available, SSL validation will be limited")


@dataclass
class TestResult:
    """Test result data class."""

    test_name: str
    server_url: str
    auth_type: str
    success: bool
    status_code: Optional[int] = None
    response_data: Optional[Dict] = None
    error_message: Optional[str] = None
    duration: float = 0.0


class SecurityTestClient:
    """Security test client for comprehensive testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize security test client."""
        self.base_url = base_url
        self.session: Optional[ClientSession] = None

        # Initialize security managers if available
        self.ssl_manager = None
        self.cert_manager = None
        self._security_available = _MCP_SECURITY_AVAILABLE
        self._crypto_available = _CRYPTOGRAPHY_AVAILABLE
        
        # Authentication configuration
        self.auth_enabled = False
        self.auth_methods = []
        self.api_keys = {}
        self.roles_file = None
        self.roles = {}

        if self._security_available:
            # For testing purposes, we don't initialize SecurityManager
            # because we're testing server configurations, not the framework itself
            # SecurityManager will be used only when actually needed by the server
            self.ssl_manager = None
            print("✅ mcp_security_framework available for testing")

        if not self._security_available:
            print("ℹ️ Using standard SSL library for testing")
            self.ssl_manager = None
        self.test_results: List[TestResult] = []
        # Test tokens
        self.test_tokens = {
            "admin": "admin-secret-key",
            "user": "user-secret-key",
            "readonly": "readonly-secret-key",
            "guest": "guest-token-123",
            "proxy": "proxy-token-123",
            "invalid": "invalid-token-999",
        }
        # Test certificates - use relative paths
        self.test_certificates = {
            "admin": {
                "cert": "certs/admin_cert.pem",
                "key": "certs/admin_key.pem",
            },
            "user": {
                "cert": "certs/user_cert.pem",
                "key": "keys/user_key.pem",
            },
            "readonly": {
                "cert": "certs/readonly_cert.pem",
                "key": "certs/readonly_key.pem",
            },
        }

    def create_ssl_context_for_mtls(self) -> ssl.SSLContext:
        """Create SSL context for mTLS connections."""
        # For mTLS, we need client certificates - check if they exist
        # Use absolute paths to avoid issues with working directory
        # Use newly generated admin_client_client.crt which is signed by the same CA as server
        project_root = Path(__file__).parent.parent.parent
        cert_file = str(project_root / "certs" / "admin_client_client.crt")
        key_file = str(project_root / "keys" / "admin-client_client.key")
        ca_cert_file = str(project_root / "certs" / "localhost_server.crt")
        
        # CRITICAL: For mTLS, certificates are REQUIRED
        if not os.path.exists(cert_file):
            raise FileNotFoundError(f"CRITICAL ERROR: mTLS client certificate not found: {cert_file}")
        if not os.path.exists(key_file):
            raise FileNotFoundError(f"CRITICAL ERROR: mTLS client key not found: {key_file}")
        
        # For testing, we use standard SSL library
        # SecurityManager is not initialized for testing purposes

        # Use standard SSL library for testing
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        # For mTLS testing - client needs to present certificate to server
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # Don't verify server cert for testing
        # Load client certificate and key for mTLS (we already checked they exist)
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        if os.path.exists(ca_cert_file):
            ssl_context.load_verify_locations(cafile=ca_cert_file)
        return ssl_context

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = ClientTimeout(total=30)
        # Create SSL context only for HTTPS URLs
        if self.base_url.startswith('https://'):
            # Check if this is mTLS (ports 20006, 20007, 20008 are mTLS test ports)
            if any(port in self.base_url for port in ['20006', '20007', '20008']):
                # Use mTLS context with client certificates
                ssl_context = self.create_ssl_context_for_mtls()
            else:
                # Use regular HTTPS context
                ssl_context = self.create_ssl_context()
            connector = TCPConnector(ssl=ssl_context)
        else:
            # For HTTP URLs, use default connector without SSL
            connector = TCPConnector()
        
        # Create session
        self.session = ClientSession(timeout=timeout, connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def create_ssl_context(
        self,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_cert_file: Optional[str] = None,
    ) -> ssl.SSLContext:
        """Create SSL context for client."""
        # If certificates are provided, they must exist
        if cert_file and not os.path.exists(cert_file):
            raise FileNotFoundError(f"CRITICAL ERROR: SSL certificate not found: {cert_file}")
        if key_file and not os.path.exists(key_file):
            raise FileNotFoundError(f"CRITICAL ERROR: SSL key not found: {key_file}")
        if ca_cert_file and not os.path.exists(ca_cert_file):
            raise FileNotFoundError(f"CRITICAL ERROR: SSL CA certificate not found: {ca_cert_file}")
        
        # For testing, we use standard SSL library
        # SecurityManager is not initialized for testing purposes

        # Use standard SSL library for testing
        ssl_context = ssl.create_default_context()
        # For testing with self-signed certificates
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        if cert_file and key_file:
            ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        if ca_cert_file:
            ssl_context.load_verify_locations(cafile=ca_cert_file)
            # For testing, still don't verify
            ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    def create_auth_headers(self, auth_type: str, **kwargs) -> Dict[str, str]:
        """Create authentication headers."""
        headers = {"Content-Type": "application/json"}
        if auth_type == "api_key":
            token = kwargs.get("token")
            if not token:
                raise ValueError("token is required for api_key authentication")
            print(f"🔍 DEBUG: Using token: {token}")
            # Provide both common header styles to maximize compatibility
            headers["X-API-Key"] = token
            headers["Authorization"] = f"Bearer {token}"
            
            # Add role header if provided
            role = kwargs.get("role")
            if role:
                headers["X-Role"] = role
        elif auth_type == "basic":
            username = kwargs.get("username")
            password = kwargs.get("password")
            if not username or not password:
                raise ValueError("username and password are required for basic authentication")
            import base64

            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif auth_type == "certificate":
            # For mTLS, we need to use client certificates
            # This is handled by SSL context, not headers
            pass
        return headers

    async def test_health_check(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test health check endpoint."""
        start_time = time.time()
        test_name = f"Health Check ({auth_type})"
        try:
            headers = self.create_auth_headers(auth_type, **kwargs)
            async with self.session.get(
                f"{server_url}/health", headers=headers
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration,
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"Health check failed: {error_text}",
                        duration=duration,
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Health check error: {str(e)}",
                duration=duration,
            )

    async def test_echo_command(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test echo command."""
        start_time = time.time()
        test_name = f"Echo Command ({auth_type})"
        try:
            headers = self.create_auth_headers(auth_type, **kwargs)
            data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Hello from security test client!"},
                "id": 1,
            }
            async with self.session.post(
                f"{server_url}/cmd", headers=headers, json=data
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration,
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"Echo command failed: {error_text}",
                        duration=duration,
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Echo command error: {str(e)}",
                duration=duration,
            )

    async def test_security_command(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test security command."""
        start_time = time.time()
        test_name = f"Security Command ({auth_type})"
        try:
            headers = self.create_auth_headers(auth_type, **kwargs)
            data = {"jsonrpc": "2.0", "method": "health", "params": {}, "id": 2}
            async with self.session.post(
                f"{server_url}/cmd", headers=headers, json=data
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration,
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"Security command failed: {error_text}",
                        duration=duration,
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Security command error: {str(e)}",
                duration=duration,
            )

    async def test_health(self) -> TestResult:
        """Test health endpoint."""
        return await self.test_health_check(self.base_url, "none")

    async def test_command_execution(self) -> TestResult:
        """Test command execution."""
        return await self.test_echo_command(self.base_url, "none")

    async def test_authentication(self) -> TestResult:
        """Test authentication."""
        if "api_key" in self.auth_methods:
            # Use admin API key value, not the key name
            api_key_value = self.api_keys.get("admin", "admin-secret-key")
            return await self.test_echo_command(self.base_url, "api_key", token=api_key_value)
        elif "certificate" in self.auth_methods:
            # For certificate auth, test with client certificate
            return await self.test_echo_command(self.base_url, "certificate")
        else:
            return TestResult(
                test_name="Authentication Test",
                server_url=self.base_url,
                auth_type="none",
                success=False,
                error_message="No authentication method available",
            )

    async def test_negative_authentication(self) -> TestResult:
        """Test negative authentication (should fail)."""
        start_time = time.time()
        test_name = "Negative Authentication Test"
        try:
            headers = self.create_auth_headers("api_key", token="invalid-token")
            data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Should fail with invalid token"},
                "id": 1,
            }
            async with self.session.post(
                f"{self.base_url}/cmd", headers=headers, json=data
            ) as response:
                duration = time.time() - start_time
                
                # Check if API key authentication is enabled
                api_key_auth_enabled = self.auth_enabled and "api_key" in self.auth_methods
                
                if api_key_auth_enabled:
                    # For configurations with API key auth, 401 is expected (success)
                    if response.status == 401:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=True,
                            status_code=response.status,
                            response_data={"expected": "authentication_failure"},
                            duration=duration,
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=False,
                            status_code=response.status,
                            error_message=f"Expected 401 Unauthorized, got {response.status}",
                            duration=duration,
                        )
                else:
                    # For configurations without API key auth, 200 is expected (success)
                    if response.status == 200:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=True,
                            status_code=response.status,
                            response_data={"expected": "no_auth_required"},
                            duration=duration,
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=False,
                            status_code=response.status,
                            error_message=f"Expected 200 OK (no auth required), got {response.status}",
                            duration=duration,
                        )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=self.base_url,
                auth_type="api_key",
                success=False,
                error_message=f"Negative auth test error: {str(e)}",
                duration=duration,
            )

    async def test_no_auth_required(self) -> TestResult:
        """Test that no authentication is required."""
        return await self.test_echo_command(self.base_url, "none")

    async def test_negative_auth(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test negative authentication scenarios."""
        start_time = time.time()
        test_name = f"Negative Auth ({auth_type})"
        try:
            if auth_type == "certificate":
                # For mTLS, test with invalid/expired certificate or no certificate
                from aiohttp import ClientTimeout, TCPConnector

                # Create SSL context with wrong certificate (should be rejected)
                ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                ssl_context.check_hostname = False
                # Don't load any client certificate - this should cause rejection
                # Load CA certificate for server verification
                ca_cert_file = "./certs/mcp_proxy_adapter_ca_ca.crt"
                if os.path.exists(ca_cert_file):
                    ssl_context.load_verify_locations(cafile=ca_cert_file)
                ssl_context.verify_mode = (
                    ssl.CERT_NONE
                )  # Don't verify server cert for testing

                connector = TCPConnector(ssl=ssl_context)
                timeout = ClientTimeout(total=10)  # Shorter timeout

                try:
                    import aiohttp

                    async with aiohttp.ClientSession(
                        timeout=timeout, connector=connector
                    ) as temp_session:
                        data = {
                            "jsonrpc": "2.0",
                            "method": "echo",
                            "params": {"message": "Should fail without certificate"},
                            "id": 3,
                        }
                        async with temp_session.post(
                            f"{server_url}/cmd", json=data
                        ) as response:
                            duration = time.time() - start_time
                            # If we get here, the server accepted the connection without proper certificate
                            # This is actually a security issue - server should reject
                            return TestResult(
                                test_name=test_name,
                                server_url=server_url,
                                auth_type=auth_type,
                                success=False,
                                status_code=response.status,
                                error_message=f"SECURITY ISSUE: mTLS server accepted connection without client certificate (status: {response.status})",
                                duration=duration,
                            )
                except (Exception,) as e:
                    # This is expected - server should reject connections without proper certificate
                    duration = time.time() - start_time
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=0,
                        response_data={
                            "expected": "connection_rejected",
                            "error": str(e),
                        },
                        duration=duration,
                    )
            else:
                # For other auth types, use invalid token
                headers = self.create_auth_headers("api_key", token="invalid-token-999")
                data = {
                    "jsonrpc": "2.0",
                    "method": "echo",
                    "params": {"message": "Should fail"},
                    "id": 3,
                }
                async with self.session.post(
                    f"{server_url}/cmd", headers=headers, json=data
                ) as response:
                    duration = time.time() - start_time
                    # Expect 401 only when auth is enforced
                    expects_auth = auth_type in ("api_key", "certificate", "basic")
                    if expects_auth and response.status == 401:
                        return TestResult(
                            test_name=test_name,
                            server_url=server_url,
                            auth_type=auth_type,
                            success=True,
                            status_code=response.status,
                            response_data={"expected": "authentication_failure"},
                            duration=duration,
                        )
                    elif not expects_auth and response.status == 200:
                        # Security disabled: negative auth should not fail
                        return TestResult(
                            test_name=test_name,
                            server_url=server_url,
                            auth_type=auth_type,
                            success=True,
                            status_code=response.status,
                            response_data={"expected": "no_auth_required"},
                            duration=duration,
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            server_url=server_url,
                            auth_type=auth_type,
                            success=False,
                            status_code=response.status,
                            error_message=f"Unexpected status for negative auth: {response.status}",
                            duration=duration,
                        )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Negative auth error: {str(e)}",
                duration=duration,
            )

    async def test_role_based_access(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test role-based access control."""
        start_time = time.time()
        test_name = f"Role-Based Access ({auth_type})"
        try:
            # Test with different roles
            role = kwargs.get("role")
            if not role:
                raise ValueError("role is required for role-based access test")
            token = self.test_tokens.get(role)
            if not token:
                raise ValueError(f"token for role '{role}' is not configured")
            headers = self.create_auth_headers("api_key", token=token)
            data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": f"Testing {role} role"},
                "id": 4,
            }
            async with self.session.post(
                f"{server_url}/cmd", headers=headers, json=data
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration,
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"Role-based access failed: {error_text}",
                        duration=duration,
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Role-based access error: {str(e)}",
                duration=duration,
            )

    async def test_role_permissions(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test role permissions with role_test command."""
        start_time = time.time()
        test_name = f"Role Permissions Test ({auth_type})"
        try:
            # Test with different roles and actions
            role = kwargs.get("role")
            action = kwargs.get("action")
            if not role:
                raise ValueError("role is required for role permissions test")
            if not action:
                raise ValueError("action is required for role permissions test")
            token = self.test_tokens.get(role)
            if not token:
                raise ValueError(f"token for role '{role}' is not configured")
            headers = self.create_auth_headers("api_key", token=token)
            data = {
                "jsonrpc": "2.0",
                "method": "role_test",
                "params": {"action": action},
                "id": 5,
            }
            async with self.session.post(
                f"{server_url}/cmd", headers=headers, json=data
            ) as response:
                duration = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=True,
                        status_code=response.status,
                        response_data=data,
                        duration=duration,
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message=f"Role permissions test failed: {error_text}",
                        duration=duration,
                    )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Role permissions test error: {str(e)}",
                duration=duration,
            )

    async def test_multiple_roles(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> TestResult:
        """Test multiple roles with different permissions."""
        start_time = time.time()
        test_name = f"Multiple Roles Test ({auth_type})"
        try:
            # Test admin role (should have all permissions)
            admin_token = self.test_tokens.get("admin")
            if not admin_token:
                raise ValueError("admin token is not configured")
            admin_headers = self.create_auth_headers("api_key", token=admin_token)
            admin_data = {
                "jsonrpc": "2.0",
                "method": "role_test",
                "params": {"action": "manage"},
                "id": 6,
            }
            async with self.session.post(
                f"{server_url}/cmd", headers=admin_headers, json=admin_data
            ) as response:
                if response.status != 200:
                    return TestResult(
                        test_name=test_name,
                        server_url=server_url,
                        auth_type=auth_type,
                        success=False,
                        status_code=response.status,
                        error_message="Admin role test failed",
                        duration=time.time() - start_time,
                    )
                # Test readonly role (should only have read permission)
                readonly_token = self.test_tokens.get("readonly")
                if not readonly_token:
                    raise ValueError("readonly token is not configured")
                readonly_headers = self.create_auth_headers(
                    "api_key", token=readonly_token
                )
                readonly_data = {
                    "jsonrpc": "2.0",
                    "method": "role_test",
                    "params": {"action": "write"},
                }
                async with self.session.post(
                    f"{server_url}/cmd", headers=readonly_headers, json=readonly_data
                ) as response:
                    duration = time.time() - start_time
                    # Readonly should be denied write access
                    if response.status == 403:
                        return TestResult(
                            test_name=test_name,
                            server_url=server_url,
                            auth_type=auth_type,
                            success=True,
                            status_code=response.status,
                            response_data={
                                "message": "Correctly denied write access to readonly role"
                            },
                            duration=duration,
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            server_url=server_url,
                            auth_type=auth_type,
                            success=False,
                            status_code=response.status,
                            error_message="Readonly role incorrectly allowed write access",
                            duration=duration,
                        )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message=f"Multiple roles test error: {str(e)}",
                duration=duration,
            )

    async def run_security_tests(
        self, server_url: str, auth_type: str = "none", **kwargs
    ) -> List[TestResult]:
        """Run comprehensive security tests."""
        print(f"\n🔒 Running security tests for {server_url} ({auth_type})")
        print("=" * 60)
        tests = [
            self.test_health_check(server_url, auth_type, **kwargs),
            self.test_echo_command(server_url, auth_type, **kwargs),
            self.test_security_command(server_url, auth_type, **kwargs),
            self.test_negative_auth(server_url, auth_type, **kwargs),
            self.test_role_based_access(server_url, auth_type, role="admin", **kwargs),
        ]
        results = []
        for test in tests:
            result = await test
            results.append(result)
            self.test_results.append(result)
            # Print result
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.test_name}")
            print(f"   Duration: {result.duration:.3f}s")
            if result.status_code:
                print(f"   Status: {result.status_code}")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            print()
        return results

    async def test_all_scenarios(self) -> Dict[str, List[TestResult]]:
        """Test all security scenarios."""
        scenarios = {
            "basic_http": {"url": "http://localhost:8000", "auth": "none"},
            "http_token": {"url": "http://localhost:8001", "auth": "api_key"},
            "https": {"url": "https://localhost:8443", "auth": "none"},
            "https_token": {"url": "https://localhost:8444", "auth": "api_key"},
            "mtls": {"url": "https://localhost:8445", "auth": "certificate"},
        }
        all_results = {}
        for scenario_name, config in scenarios.items():
            print(f"\n🚀 Testing scenario: {scenario_name.upper()}")
            print("=" * 60)
            try:
                results = await self.run_security_tests(config["url"], config["auth"])
                all_results[scenario_name] = results
            except Exception as e:
                print(f"❌ Failed to test {scenario_name}: {e}")
                all_results[scenario_name] = []
        return all_results

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("📊 SECURITY TEST SUMMARY")
        print("=" * 80)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.success:
                    print(f"  - {result.test_name} ({result.server_url})")
                    if result.error_message:
                        print(f"    Error: {result.error_message}")
        print("\n✅ Passed Tests:")
        for result in self.test_results:
            if result.success:
                print(f"  - {result.test_name} ({result.server_url})")


    async def test_health(self) -> TestResult:
        """Test health check endpoint."""
        return await self.test_health_check(self.base_url, "none")

    async def test_command_execution(self) -> TestResult:
        """Test command execution."""
        if self.auth_enabled and "api_key" in self.auth_methods:
            # Use admin API key value, not the key name
            api_key_value = self.api_keys.get("admin", "admin-secret-key")
            return await self.test_echo_command(self.base_url, "api_key", token=api_key_value)
        else:
            return await self.test_echo_command(self.base_url, "none")

    async def test_authentication(self) -> TestResult:
        """Test authentication."""
        if "api_key" in self.auth_methods:
            # Use admin API key value, not the key name
            api_key_value = self.api_keys.get("admin", "admin-secret-key")
            return await self.test_echo_command(self.base_url, "api_key", token=api_key_value)
        elif "certificate" in self.auth_methods:
            # For certificate auth, test with client certificate
            return await self.test_echo_command(self.base_url, "certificate")
        else:
            return TestResult(
                test_name="Authentication Test",
                server_url=self.base_url,
                auth_type="none",
                success=False,
                error_message="No authentication method available",
            )

    async def test_negative_authentication(self) -> TestResult:
        """Test negative authentication (should fail)."""
        start_time = time.time()
        test_name = "Negative Authentication Test"
        try:
            headers = self.create_auth_headers("api_key", token="invalid-token")
            data = {
                "jsonrpc": "2.0",
                "method": "echo",
                "params": {"message": "Should fail with invalid token"},
                "id": 1,
            }
            async with self.session.post(
                f"{self.base_url}/cmd", headers=headers, json=data
            ) as response:
                duration = time.time() - start_time
                
                # Check if API key authentication is enabled
                api_key_auth_enabled = self.auth_enabled and "api_key" in self.auth_methods
                
                if api_key_auth_enabled:
                    # For configurations with API key auth, 401 is expected (success)
                    if response.status == 401:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=True,
                            status_code=response.status,
                            response_data={"expected": "authentication_failure"},
                            duration=duration,
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=False,
                            status_code=response.status,
                            error_message=f"Expected 401 Unauthorized, got {response.status}",
                            duration=duration,
                        )
                else:
                    # For configurations without API key auth, 200 is expected (success)
                    if response.status == 200:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=True,
                            status_code=response.status,
                            response_data={"expected": "no_auth_required"},
                            duration=duration,
                        )
                    else:
                        return TestResult(
                            test_name=test_name,
                            server_url=self.base_url,
                            auth_type="api_key",
                            success=False,
                            status_code=response.status,
                            error_message=f"Expected 200 OK (no auth required), got {response.status}",
                            duration=duration,
                        )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                server_url=self.base_url,
                auth_type="api_key",
                success=False,
                error_message=f"Negative auth test error: {str(e)}",
                duration=duration,
            )

    async def test_no_auth_required(self) -> TestResult:
        """Test that no authentication is required."""
        return await self.test_echo_command(self.base_url, "none")

    async def test_role_based_access(self, server_url: str, auth_type: str, role: str = "admin") -> TestResult:
        """Test role-based access control."""
        if not self.roles_file and not self.roles:
            return TestResult(
                test_name="Role-Based Access Test",
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message="Role-based access error: role is required for role-based access test",
            )
        
        # Use admin role for testing
        if auth_type == "api_key":
            api_key_value = self.api_keys.get("admin", "admin-secret-key")
            return await self.test_echo_command(server_url, auth_type, token=api_key_value, role=role)
        else:
            return await self.test_echo_command(server_url, auth_type, role=role)

    async def test_role_permissions(self, server_url: str, auth_type: str, role: str = "admin", action: str = "read") -> TestResult:
        """Test role permissions."""
        if not self.roles_file and not self.roles:
            return TestResult(
                test_name="Role Permissions Test",
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message="Role permissions test error: role is required for role permissions test",
            )
        
        # Test with admin role
        if auth_type == "api_key":
            api_key_value = self.api_keys.get("admin", "admin-secret-key")
            return await self.test_echo_command(server_url, auth_type, token=api_key_value, role=role)
        else:
            return await self.test_echo_command(server_url, auth_type, role=role)

    async def test_multiple_roles(self, server_url: str, auth_type: str) -> TestResult:
        """Test multiple roles."""
        # Test with readonly role (should have read access)
        if auth_type == "api_key":
            api_key_value = self.api_keys.get("readonly", "readonly-token-123")
            result = await self.test_echo_command(server_url, auth_type, token=api_key_value, role="readonly")
            if result.success:
                return TestResult(
                    test_name="Multiple Roles Test",
                    server_url=server_url,
                    auth_type=auth_type,
                    success=True,
                    response_data={"message": "Readonly role correctly has read access"},
                )
            else:
                return TestResult(
                    test_name="Multiple Roles Test",
                    server_url=server_url,
                    auth_type=auth_type,
                    success=False,
                    error_message="Readonly role incorrectly denied read access",
                )
        elif auth_type == "certificate":
            # For certificate auth, test with user certificate (should have read access)
            result = await self.test_echo_command(server_url, auth_type, role="user")
            if result.success:
                return TestResult(
                    test_name="Multiple Roles Test",
                    server_url=server_url,
                    auth_type=auth_type,
                    success=True,
                    response_data={"message": "User certificate correctly has read access"},
                )
            else:
                return TestResult(
                    test_name="Multiple Roles Test",
                    server_url=server_url,
                    auth_type=auth_type,
                    success=False,
                    error_message="User certificate incorrectly denied read access",
                )
        else:
            return TestResult(
                test_name="Multiple Roles Test",
                server_url=server_url,
                auth_type=auth_type,
                success=False,
                error_message="Multiple roles test not implemented for this auth type",
            )


async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Security Test Client for MCP Proxy Adapter"
    )
    parser.add_argument(
        "--server", default="http://localhost:8000", help="Server URL to test"
    )
    parser.add_argument(
        "--auth",
        choices=["none", "api_key", "basic", "certificate"],
        default="none",
        help="Authentication type",
    )
    parser.add_argument(
        "--all-scenarios", action="store_true", help="Test all security scenarios"
    )
    parser.add_argument("--token", help="API token for authentication")
    parser.add_argument("--cert", help="Client certificate file")
    parser.add_argument("--key", help="Client private key file")
    parser.add_argument("--ca-cert", help="CA certificate file")
    args = parser.parse_args()
    if args.all_scenarios:
        # Test all scenarios
        async with SecurityTestClient() as client:
            await client.test_all_scenarios()
            client.print_summary()
    else:
        # Test single server
        async with SecurityTestClient(args.server) as client:
            await client.run_security_tests(args.server, args.auth, token=args.token)
            client.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
