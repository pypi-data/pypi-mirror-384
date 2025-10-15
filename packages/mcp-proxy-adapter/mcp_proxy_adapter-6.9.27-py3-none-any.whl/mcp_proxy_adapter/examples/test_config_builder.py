#!/usr/bin/env python3
"""
Comprehensive Tests for Configuration Builder
Tests all combinations of protocols, authentication methods, and other parameters.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from config_builder import ConfigBuilder, ConfigFactory, Protocol, AuthMethod


class TestConfigBuilder:
    """Test cases for ConfigBuilder class."""
    
    def test_default_configuration(self):
        """Test default configuration structure."""
        builder = ConfigBuilder()
        config = builder.build()
        
        # Check required fields
        assert "uuid" in config
        assert "server" in config
        assert "ssl" in config
        assert "security" in config
        assert "protocols" in config
        
        # Check default values
        assert config["server"]["host"] == "0.0.0.0"
        assert config["server"]["port"] == 8000
        assert config["ssl"]["enabled"] is False
        assert config["security"]["enabled"] is False
    
    def test_set_server(self):
        """Test server configuration setting."""
        builder = ConfigBuilder()
        config = builder.set_server(host="127.0.0.1", port=9000, debug=True, log_level="DEBUG").build()
        
        assert config["server"]["host"] == "127.0.0.1"
        assert config["server"]["port"] == 9000
        assert config["server"]["debug"] is True
        assert config["server"]["log_level"] == "DEBUG"
    
    def test_set_logging(self):
        """Test logging configuration setting."""
        builder = ConfigBuilder()
        config = builder.set_logging(log_dir="/tmp/logs", level="WARNING", console_output=False).build()
        
        assert config["logging"]["log_dir"] == "/tmp/logs"
        assert config["logging"]["level"] == "WARNING"
        assert config["logging"]["console_output"] is False
    
    def test_set_protocol_http(self):
        """Test HTTP protocol configuration."""
        builder = ConfigBuilder()
        config = builder.set_protocol(Protocol.HTTP).build()
        
        assert config["ssl"]["enabled"] is False
        assert config["ssl"]["chk_hostname"] is False
        assert config["security"]["ssl"]["enabled"] is False
        assert config["security"]["ssl"]["chk_hostname"] is False
        assert config["protocols"]["allowed_protocols"] == ["http"]
        assert config["protocols"]["default_protocol"] == "http"
        assert config["protocols"]["protocol_handlers"]["http"]["enabled"] is True
        assert config["protocols"]["protocol_handlers"]["https"]["enabled"] is False
        assert config["protocols"]["protocol_handlers"]["mtls"]["enabled"] is False
    
    def test_set_protocol_https(self):
        """Test HTTPS protocol configuration."""
        builder = ConfigBuilder()
        config = builder.set_protocol(Protocol.HTTPS, cert_dir="/tmp/certs", key_dir="/tmp/keys").build()
        
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["chk_hostname"] is True
        assert config["ssl"]["cert_file"] == "/tmp/certs/server_cert.pem"
        assert config["ssl"]["key_file"] == "/tmp/keys/server_key.pem"
        assert config["ssl"]["ca_cert"] == "/tmp/certs/ca_cert.pem"
        
        assert config["security"]["ssl"]["enabled"] is True
        assert config["security"]["ssl"]["chk_hostname"] is True
        assert config["security"]["ssl"]["cert_file"] == "/tmp/certs/server_cert.pem"
        assert config["security"]["ssl"]["key_file"] == "/tmp/keys/server_key.pem"
        assert config["security"]["ssl"]["ca_cert_file"] == "/tmp/certs/ca_cert.pem"
        
        assert config["protocols"]["allowed_protocols"] == ["https"]
        assert config["protocols"]["default_protocol"] == "https"
        assert config["protocols"]["protocol_handlers"]["http"]["enabled"] is False
        assert config["protocols"]["protocol_handlers"]["https"]["enabled"] is True
        assert config["protocols"]["protocol_handlers"]["mtls"]["enabled"] is False
    
    def test_set_protocol_mtls(self):
        """Test mTLS protocol configuration."""
        builder = ConfigBuilder()
        config = builder.set_protocol(Protocol.MTLS, cert_dir="/tmp/certs", key_dir="/tmp/keys").build()
        
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["chk_hostname"] is True
        assert config["ssl"]["verify_client"] is True
        assert config["ssl"]["client_cert_required"] is True
        
        assert config["security"]["ssl"]["enabled"] is True
        assert config["security"]["ssl"]["chk_hostname"] is True
        assert config["security"]["ssl"]["client_cert_file"] == "/tmp/certs/admin_cert.pem"
        assert config["security"]["ssl"]["client_key_file"] == "/tmp/keys/admin_key.pem"
        assert config["security"]["ssl"]["verify_mode"] == "CERT_REQUIRED"
        
        assert config["protocols"]["allowed_protocols"] == ["mtls"]
        assert config["protocols"]["default_protocol"] == "mtls"
        assert config["protocols"]["protocol_handlers"]["http"]["enabled"] is False
        assert config["protocols"]["protocol_handlers"]["https"]["enabled"] is False
        assert config["protocols"]["protocol_handlers"]["mtls"]["enabled"] is True
        assert config["protocols"]["protocol_handlers"]["mtls"]["client_cert_required"] is True
    
    def test_set_auth_none(self):
        """Test no authentication configuration."""
        builder = ConfigBuilder()
        config = builder.set_auth(AuthMethod.NONE).build()
        
        assert config["security"]["enabled"] is False
        assert config["security"]["auth"]["enabled"] is False
    
    def test_set_auth_token(self):
        """Test token authentication configuration."""
        api_keys = {"admin": "admin-key", "user": "user-key"}
        builder = ConfigBuilder()
        config = builder.set_auth(AuthMethod.TOKEN, api_keys=api_keys).build()
        
        assert config["security"]["enabled"] is True
        assert config["security"]["auth"]["enabled"] is True
        assert config["security"]["auth"]["methods"] == ["api_key"]
        assert config["security"]["auth"]["api_keys"] == api_keys
    
    def test_set_auth_basic(self):
        """Test basic authentication configuration."""
        builder = ConfigBuilder()
        config = builder.set_auth(AuthMethod.BASIC).build()
        
        assert config["security"]["enabled"] is True
        assert config["security"]["auth"]["enabled"] is True
        assert config["security"]["auth"]["methods"] == ["basic_auth"]
        assert config["security"]["auth"]["basic_auth"] is True
    
    def test_set_auth_with_roles(self):
        """Test authentication with roles configuration."""
        roles = {"admin": ["read", "write"], "user": ["read"]}
        builder = ConfigBuilder()
        config = builder.set_auth(AuthMethod.TOKEN, roles=roles).build()
        
        assert config["security"]["auth"]["user_roles"] == roles
        assert config["roles"]["enabled"] is True
        assert config["security"]["permissions"]["enabled"] is True
    
    def test_set_proxy_registration(self):
        """Test proxy registration configuration."""
        builder = ConfigBuilder()
        config = builder.set_proxy_registration(
            enabled=True,
            proxy_url="https://proxy.example.com:8080",
            server_id="test_server",
            cert_dir="/tmp/certs"
        ).build()
        
        assert config["proxy_registration"]["enabled"] is True
        assert config["proxy_registration"]["server_url"] == "https://proxy.example.com:8080/register"
        assert config["proxy_registration"]["proxy_url"] == "https://proxy.example.com:8080"
        assert config["proxy_registration"]["fallback_proxy_url"] == "http://proxy.example.com:8080"
        assert config["proxy_registration"]["ssl"]["ca_cert"] == "/tmp/certs/ca_cert.pem"
        assert config["proxy_registration"]["server_id"] == "test_server"
        assert config["proxy_registration"]["server_name"] == "Test_Server Server"
        assert config["proxy_registration"]["description"] == "Test server for test_server"
    
    def test_set_debug(self):
        """Test debug configuration."""
        builder = ConfigBuilder()
        config = builder.set_debug(enabled=True, log_level="DEBUG").build()
        
        assert config["debug"]["enabled"] is True
        assert config["debug"]["log_level"] == "DEBUG"
        assert config["logging"]["level"] == "DEBUG"
    
    def test_set_commands(self):
        """Test commands configuration."""
        enabled = ["health", "echo", "test"]
        disabled = ["admin", "debug"]
        builder = ConfigBuilder()
        config = builder.set_commands(enabled_commands=enabled, disabled_commands=disabled).build()
        
        assert config["commands"]["enabled_commands"] == enabled
        assert config["commands"]["disabled_commands"] == disabled
    
    def test_set_hostname_check(self):
        """Test hostname check configuration."""
        builder = ConfigBuilder()
        
        # Test enabling hostname check
        config = builder.set_hostname_check(enabled=True).build()
        assert config["ssl"]["chk_hostname"] is True
        assert config["security"]["ssl"]["chk_hostname"] is True
        
        # Test disabling hostname check
        config = builder.set_hostname_check(enabled=False).build()
        assert config["ssl"]["chk_hostname"] is False
        assert config["security"]["ssl"]["chk_hostname"] is False
    
    def test_hostname_check_with_protocols(self):
        """Test hostname check behavior with different protocols."""
        # HTTP should have chk_hostname = False
        builder = ConfigBuilder()
        config = builder.set_protocol(Protocol.HTTP).build()
        assert config["ssl"]["chk_hostname"] is False
        assert config["security"]["ssl"]["chk_hostname"] is False
        
        # HTTPS should have chk_hostname = True
        builder = ConfigBuilder()
        config = builder.set_protocol(Protocol.HTTPS).build()
        assert config["ssl"]["chk_hostname"] is True
        assert config["security"]["ssl"]["chk_hostname"] is True
        
        # mTLS should have chk_hostname = True
        builder = ConfigBuilder()
        config = builder.set_protocol(Protocol.MTLS).build()
        assert config["ssl"]["chk_hostname"] is True
        assert config["security"]["ssl"]["chk_hostname"] is True
    
    def test_save_configuration(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            builder = ConfigBuilder()
            builder.set_server(port=9000)
            config_path = builder.save(Path(temp_dir) / "test_config.json")
            
            assert config_path.exists()
            
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config["server"]["port"] == 9000
    
    def test_reset_configuration(self):
        """Test configuration reset."""
        builder = ConfigBuilder()
        builder.set_server(port=9000)
        builder.set_auth(AuthMethod.TOKEN)
        
        config1 = builder.build()
        assert config1["server"]["port"] == 9000
        assert config1["security"]["enabled"] is True
        
        builder.reset()
        config2 = builder.build()
        assert config2["server"]["port"] == 8000  # Default value
        assert config2["security"]["enabled"] is False  # Default value


class TestConfigFactory:
    """Test cases for ConfigFactory class."""
    
    def test_create_http_simple(self):
        """Test HTTP simple configuration creation."""
        config = ConfigFactory.create_http_simple(host="127.0.0.1", port=9000, log_dir="/tmp/logs")
        
        assert config["server"]["host"] == "127.0.0.1"
        assert config["server"]["port"] == 9000
        assert config["logging"]["log_dir"] == "/tmp/logs"
        assert config["ssl"]["enabled"] is False
        assert config["security"]["enabled"] is False
        assert config["protocols"]["allowed_protocols"] == ["http"]
        assert config["proxy_registration"]["enabled"] is False
    
    def test_create_http_token(self):
        """Test HTTP token configuration creation."""
        api_keys = {"admin": "admin-key", "user": "user-key"}
        config = ConfigFactory.create_http_token(api_keys=api_keys)
        
        assert config["ssl"]["enabled"] is False
        assert config["security"]["enabled"] is True
        assert config["security"]["auth"]["enabled"] is True
        assert config["security"]["auth"]["methods"] == ["api_key"]
        assert config["security"]["auth"]["api_keys"] == api_keys
    
    def test_create_https_simple(self):
        """Test HTTPS simple configuration creation."""
        config = ConfigFactory.create_https_simple(cert_dir="/tmp/certs", key_dir="/tmp/keys")
        
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["cert_file"] == "/tmp/certs/server_cert.pem"
        assert config["ssl"]["key_file"] == "/tmp/keys/server_key.pem"
        assert config["protocols"]["allowed_protocols"] == ["https"]
        assert config["security"]["ssl"]["enabled"] is True
    
    def test_create_https_token(self):
        """Test HTTPS token configuration creation."""
        api_keys = {"admin": "admin-key"}
        config = ConfigFactory.create_https_token(api_keys=api_keys)
        
        assert config["ssl"]["enabled"] is True
        assert config["security"]["enabled"] is True
        assert config["security"]["auth"]["enabled"] is True
        assert config["security"]["auth"]["api_keys"] == api_keys
        assert config["protocols"]["allowed_protocols"] == ["https"]
    
    def test_create_mtls_simple(self):
        """Test mTLS simple configuration creation."""
        config = ConfigFactory.create_mtls_simple()
        
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["verify_client"] is True
        assert config["ssl"]["client_cert_required"] is True
        assert config["protocols"]["allowed_protocols"] == ["mtls"]
        assert config["security"]["ssl"]["verify_mode"] == "CERT_REQUIRED"
    
    def test_create_mtls_with_roles(self):
        """Test mTLS with roles configuration creation."""
        roles = {"admin": ["read", "write"], "user": ["read"]}
        config = ConfigFactory.create_mtls_with_roles(roles=roles)
        
        assert config["ssl"]["enabled"] is True
        assert config["protocols"]["allowed_protocols"] == ["mtls"]
        assert config["security"]["auth"]["user_roles"] == roles
        assert config["roles"]["enabled"] is True
        assert config["security"]["permissions"]["enabled"] is True
    
    def test_create_mtls_with_proxy(self):
        """Test mTLS with proxy configuration creation."""
        config = ConfigFactory.create_mtls_with_proxy(
            proxy_url="https://proxy.example.com:8080",
            server_id="test_server"
        )
        
        assert config["ssl"]["enabled"] is True
        assert config["protocols"]["allowed_protocols"] == ["mtls"]
        assert config["proxy_registration"]["enabled"] is True
        assert config["proxy_registration"]["proxy_url"] == "https://proxy.example.com:8080"
        assert config["proxy_registration"]["server_id"] == "test_server"
    
    def test_create_full_featured(self):
        """Test full-featured configuration creation."""
        config = ConfigFactory.create_full_featured()
        
        assert config["ssl"]["enabled"] is True
        assert config["protocols"]["allowed_protocols"] == ["mtls"]
        assert config["security"]["enabled"] is True
        assert config["security"]["auth"]["enabled"] is True
        assert config["proxy_registration"]["enabled"] is True
        assert config["debug"]["enabled"] is True
        assert config["roles"]["enabled"] is True
        assert config["security"]["permissions"]["enabled"] is True


class TestConfigurationCombinations:
    """Test all possible combinations of configuration parameters."""
    
    def test_all_protocol_auth_combinations(self):
        """Test all combinations of protocols and authentication methods."""
        protocols = [Protocol.HTTP, Protocol.HTTPS, Protocol.MTLS]
        auth_methods = [AuthMethod.NONE, AuthMethod.TOKEN, AuthMethod.BASIC]
        
        for protocol in protocols:
            for auth_method in auth_methods:
                builder = ConfigBuilder()
                config = (builder
                         .set_protocol(protocol)
                         .set_auth(auth_method)
                         .build())
                
                # Verify protocol settings
                if protocol == Protocol.HTTP:
                    assert config["ssl"]["enabled"] is False
                    assert config["protocols"]["allowed_protocols"] == ["http"]
                elif protocol == Protocol.HTTPS:
                    assert config["ssl"]["enabled"] is True
                    assert config["protocols"]["allowed_protocols"] == ["https"]
                elif protocol == Protocol.MTLS:
                    assert config["ssl"]["enabled"] is True
                    assert config["ssl"]["verify_client"] is True
                    assert config["protocols"]["allowed_protocols"] == ["mtls"]
                
                # Verify auth settings
                if auth_method == AuthMethod.NONE:
                    assert config["security"]["enabled"] is False
                else:
                    assert config["security"]["enabled"] is True
                    assert config["security"]["auth"]["enabled"] is True
    
    def test_proxy_registration_with_all_protocols(self):
        """Test proxy registration with all protocols."""
        protocols = [Protocol.HTTP, Protocol.HTTPS, Protocol.MTLS]
        
        for protocol in protocols:
            builder = ConfigBuilder()
            config = (builder
                     .set_protocol(protocol)
                     .set_proxy_registration(enabled=True, proxy_url="https://proxy.test:8080")
                     .build())
            
            assert config["proxy_registration"]["enabled"] is True
            assert config["proxy_registration"]["proxy_url"] == "https://proxy.test:8080"
            assert config["proxy_registration"]["server_url"] == "https://proxy.test:8080/register"
    
    def test_roles_with_all_auth_methods(self):
        """Test roles configuration with all authentication methods."""
        auth_methods = [AuthMethod.TOKEN, AuthMethod.BASIC]
        roles = {"admin": ["read", "write"], "user": ["read"]}
        
        for auth_method in auth_methods:
            builder = ConfigBuilder()
            config = (builder
                     .set_auth(auth_method, roles=roles)
                     .build())
            
            assert config["security"]["auth"]["user_roles"] == roles
            assert config["roles"]["enabled"] is True
            assert config["security"]["permissions"]["enabled"] is True
    
    def test_debug_with_all_combinations(self):
        """Test debug configuration with various combinations."""
        builder = ConfigBuilder()
        config = (builder
                 .set_protocol(Protocol.HTTPS)
                 .set_auth(AuthMethod.TOKEN)
                 .set_proxy_registration(enabled=True)
                 .set_debug(enabled=True)
                 .build())
        
        assert config["debug"]["enabled"] is True
        assert config["debug"]["log_level"] == "DEBUG"
        assert config["logging"]["level"] == "DEBUG"
        assert config["ssl"]["enabled"] is True
        assert config["security"]["enabled"] is True
        assert config["proxy_registration"]["enabled"] is True


def run_comprehensive_tests():
    """Run comprehensive tests and generate report."""
    print("🧪 Running Comprehensive Configuration Builder Tests")
    print("=" * 60)
    
    test_classes = [
        TestConfigBuilder,
        TestConfigFactory,
        TestConfigurationCombinations
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}")
        print("-" * 40)
        
        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                getattr(test_instance, test_method)()
                print(f"✅ {test_method}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {test_method}: {e}")
                failed_tests.append(f"{test_class.__name__}.{test_method}: {e}")
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("📊 TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"   • {failure}")
    else:
        print(f"\n🎉 All tests passed!")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)
