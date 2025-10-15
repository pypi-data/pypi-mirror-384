# MCP Proxy Adapter

**Author:** Vasiliy Zdanovskiy  
**Email:** vasilyvz@gmail.com

## Overview

MCP Proxy Adapter is a comprehensive framework for building JSON-RPC API servers with built-in security, SSL/TLS support, and proxy registration capabilities. It provides a unified interface for command execution, protocol management, and security enforcement.

## Features

- **JSON-RPC API**: Full JSON-RPC 2.0 support with built-in commands
- **Security Framework**: Integrated authentication, authorization, and SSL/TLS
- **Protocol Management**: HTTP, HTTPS, and mTLS protocol support
- **Proxy Registration**: Automatic registration with proxy servers
- **Command System**: Extensible command registry with built-in commands
- **Configuration Management**: Comprehensive configuration with environment variable overrides

## Quick Start

1. **Installation**:
   ```bash
   pip install mcp-proxy-adapter
   ```

2. **Basic Configuration**:
   ```bash
   # Use the comprehensive config with all options disabled by default
   python -m mcp_proxy_adapter --config config.json
   ```

3. **Access the API**:
   - Health check: `GET http://localhost:8000/health`
   - JSON-RPC: `POST http://localhost:8000/api/jsonrpc`
   - REST API: `POST http://localhost:8000/cmd`
   - Documentation: `http://localhost:8000/docs`

## Configuration

The adapter uses a comprehensive JSON configuration file (`config.json`) that includes all available options with sensible defaults. All features are disabled by default and can be enabled as needed:

- **Server settings**: Host, port, debug mode
- **Security**: Authentication methods, SSL/TLS, permissions
- **Protocols**: HTTP/HTTPS/mTLS configuration
- **Proxy registration**: Automatic server registration
- **Logging**: Comprehensive logging configuration
- **Commands**: Built-in and custom command management

See `docs/EN/configuration.md` for complete configuration documentation.

## Built-in Commands

- `health` - Server health check
- `echo` - Echo test command
- `config` - Configuration management
- `help` - Command help and documentation
- `reload` - Configuration reload
- `settings` - Settings management
- `load`/`unload` - Command loading/unloading
- `plugins` - Plugin management
- `proxy_registration` - Proxy registration control
- `transport_management` - Transport protocol management
- `role_test` - Role-based access testing

## Security Features

- **Authentication**: API keys, JWT tokens, certificate-based auth
- **Authorization**: Role-based permissions with wildcard support
- **SSL/TLS**: Full SSL/TLS and mTLS support
- **Rate Limiting**: Configurable request rate limiting
- **Security Headers**: Automatic security header injection

## Examples

The `mcp_proxy_adapter/examples/` directory contains comprehensive examples for different use cases:

- **Basic Framework**: Simple HTTP server setup
- **Full Application**: Complete application with custom commands and hooks
- **Security Testing**: Comprehensive security test suite
- **Certificate Generation**: SSL/TLS certificate management

### Test Environment Setup

The framework includes a comprehensive test environment setup that automatically creates configurations, generates certificates, and runs tests:

```bash
# Create a complete test environment with all configurations and certificates
python -m mcp_proxy_adapter.examples.setup_test_environment

# Create test environment in a specific directory
python -m mcp_proxy_adapter.examples.setup_test_environment /path/to/test/dir

# Skip certificate generation (use existing certificates)
python -m mcp_proxy_adapter.examples.setup_test_environment --skip-certs

# Skip running tests (setup only)
python -m mcp_proxy_adapter.examples.setup_test_environment --skip-tests
```

### Configuration Generation

Generate test configurations from a comprehensive template:

```bash
# Generate all test configurations
python -m mcp_proxy_adapter.examples.create_test_configs

# Generate from specific comprehensive config
python -m mcp_proxy_adapter.examples.create_test_configs --comprehensive-config config.json

# Generate specific configuration types
python -m mcp_proxy_adapter.examples.create_test_configs --types http,https,mtls
```

### Certificate Generation

Generate SSL/TLS certificates for testing:

```bash
# Generate all certificates using mcp_security_framework
python -m mcp_proxy_adapter.examples.generate_all_certificates

# Generate certificates with custom configuration
python -m mcp_proxy_adapter.examples.generate_certificates_framework --config cert_config.json
```

### Security Testing

Run comprehensive security tests:

```bash
# Run all security tests
python -m mcp_proxy_adapter.examples.run_security_tests_fixed

# Run full test suite (includes setup, config generation, certificate generation, and testing)
python -m mcp_proxy_adapter.examples.run_full_test_suite
```

### Complete Workflow Example

```bash
# 1. Install the package
pip install mcp-proxy-adapter

# 2. Create test environment (automatically runs tests)
python -m mcp_proxy_adapter.examples.setup_test_environment

# 3. Or run individual steps:
# Generate certificates
python -m mcp_proxy_adapter.examples.generate_all_certificates

# Generate configurations
python -m mcp_proxy_adapter.examples.create_test_configs

# Run security tests
python -m mcp_proxy_adapter.examples.run_security_tests_fixed

# 4. Start server with generated configuration
python -m mcp_proxy_adapter --config configs/http_simple.json
```

## Development

The project follows a modular architecture:

- `mcp_proxy_adapter/api/` - FastAPI application and handlers
- `mcp_proxy_adapter/commands/` - Command system and built-in commands
- `mcp_proxy_adapter/core/` - Core functionality and utilities
- `mcp_proxy_adapter/config.py` - Configuration management

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please contact vasilyvz@gmail.com.
