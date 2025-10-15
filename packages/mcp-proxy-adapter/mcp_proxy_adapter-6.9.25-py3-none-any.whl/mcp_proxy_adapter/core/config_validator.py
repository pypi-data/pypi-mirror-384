"""
Configuration Validator for MCP Proxy Adapter
Validates configuration files and ensures all required settings are present and correct.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
import ssl
import socket

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Import ValidationResult and exceptions from errors to avoid circular imports
from .errors import ValidationResult, MissingConfigKeyError


class ConfigValidator:
    """
    Comprehensive configuration validator for MCP Proxy Adapter.
    
    Validates:
    - Required sections and keys
    - File existence for referenced files
    - Feature flag dependencies
    - Protocol-specific requirements
    - Security configuration consistency
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration validator.

        Args:
            config_path: Path to configuration file for validation
        """
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.validation_results: List[ValidationResult] = []
        
        # Define required sections and their keys
        self.required_sections = {
            "server": {
                "host": str,
                "port": int,
                "protocol": str,
                "debug": bool,
                "log_level": str
            },
            "logging": {
                "level": str,
                "log_dir": str,
                "log_file": str,
                "error_log_file": str,
                "access_log_file": str,
                "max_file_size": (str, int),
                "backup_count": int,
                "format": str,
                "date_format": str,
                "console_output": bool,
                "file_output": bool
            },
            "commands": {
                "auto_discovery": bool,
                "commands_directory": str,
                "catalog_directory": str,
                "plugin_servers": list,
                "auto_install_dependencies": bool,
                "enabled_commands": list,
                "disabled_commands": list,
                "custom_commands_path": str
            },
            "transport": {
                "type": str,
                "port": (int, type(None)),
                "verify_client": bool,
                "chk_hostname": bool
            },
            "proxy_registration": {
                "enabled": bool,
                "proxy_url": str,
                "server_id": str,
                "server_name": str,
                "description": str,
                "version": str,
                "registration_timeout": int,
                "retry_attempts": int,
                "retry_delay": int,
                "auto_register_on_startup": bool,
                "auto_unregister_on_shutdown": bool
            },
            "debug": {
                "enabled": bool,
                "level": str
            },
            "security": {
                "enabled": bool,
                "tokens": dict,
                "roles": dict,
                "roles_file": (str, type(None))
            },
            "roles": {
                "enabled": bool,
                "config_file": (str, type(None)),
                "default_policy": dict,
                "auto_load": bool,
                "validation_enabled": bool
            }
        }
        
        # Define feature flags and their dependencies
        self.feature_flags = {
            "security": {
                "enabled_key": "security.enabled",
                "dependencies": ["security.tokens", "security.roles"],
                "required_files": ["security.roles_file"],
                "optional_files": []
            },
            "roles": {
                "enabled_key": "roles.enabled",
                "dependencies": ["roles.config_file"],
                "required_files": ["roles.config_file"],
                "optional_files": []
            },
            "proxy_registration": {
                "enabled_key": "proxy_registration.enabled",
                "dependencies": ["proxy_registration.proxy_url"],
                "required_files": [],
                "optional_files": [
                    "proxy_registration.certificate.cert_file",
                    "proxy_registration.certificate.key_file"
                ]
            },
            "ssl": {
                "enabled_key": "ssl.enabled",
                "dependencies": ["ssl.cert_file", "ssl.key_file"],
                "required_files": ["ssl.cert_file", "ssl.key_file"],
                "optional_files": ["ssl.ca_cert"]
            },
            "transport_ssl": {
                "enabled_key": "transport.ssl.enabled",
                "dependencies": ["transport.ssl.cert_file", "transport.ssl.key_file"],
                "required_files": ["transport.ssl.cert_file", "transport.ssl.key_file"],
                "optional_files": ["transport.ssl.ca_cert"]
            }
        }
        
        # Protocol-specific requirements
        self.protocol_requirements = {
            "http": {
                "ssl_enabled": False,
                "client_verification": False,
                "required_files": []
            },
            "https": {
                "ssl_enabled": True,
                "client_verification": False,
                "required_files": ["ssl.cert_file", "ssl.key_file"]
            },
            "mtls": {
                "ssl_enabled": True,
                "client_verification": True,
                "required_files": ["ssl.cert_file", "ssl.key_file", "ssl.ca_cert"]
            }
        }
    
    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from file.

        Args:
            config_path: Path to configuration file
        """
        if config_path:
            self.config_path = config_path
            
        if not self.config_path or not os.path.exists(self.config_path):
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Configuration file not found: {self.config_path}",
                section="config_file"
            ))
            return
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except json.JSONDecodeError as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Invalid JSON in configuration file: {e}",
                section="config_file"
            ))
        except Exception as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Error loading configuration file: {e}",
                section="config_file"
            ))
    
    def validate_config(self, config_data: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """
        Validate configuration data.

        Args:
            config_data: Configuration data to validate. If None, uses loaded config.
            
        Returns:
            List of validation results
        """
        if config_data is not None:
            self.config_data = config_data
            
        if not self.config_data:
            self.validation_results.append(ValidationResult(
                level="error",
                message="No configuration data to validate",
                section="config_data"
            ))
            return self.validation_results
            
        # Clear previous results
        self.validation_results = []
        
        # Perform all validation checks
        self._validate_required_sections()
        self._validate_feature_flags()
        self._validate_protocol_requirements()
        self._validate_file_existence()
        self._validate_security_consistency()
        self._validate_ssl_configuration()
        self._validate_proxy_registration()
        self._validate_roles_configuration()
        self._validate_uuid_format()
        self._validate_unknown_fields()
        
        return self.validation_results
    
    def validate_all(self, config_data: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """
        Alias for validate_config method for backward compatibility.

        Args:
            config_data: Configuration data to validate. If None, uses loaded config.
            
        Returns:
            List of validation results
        """
        return self.validate_config(config_data)
    
    def _validate_required_sections(self) -> None:
        """Validate that all required sections and keys are present for enabled features only."""
        # Always required sections (core functionality)
        always_required = {
            "server": self.required_sections["server"],
            "logging": self.required_sections["logging"],
            "commands": self.required_sections["commands"]
        }
        
        # Check always required sections
        for section_name, required_keys in always_required.items():
            if section_name not in self.config_data:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"Required section '{section_name}' is missing",
                    section=section_name
                ))
                continue
                
            section_data = self.config_data[section_name]
            for key, expected_type in required_keys.items():
                if key not in section_data:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Required key '{key}' is missing in section '{section_name}'",
                        section=section_name,
                        key=key
                    ))
                else:
                    # Validate type
                    value = section_data[key]
                    if isinstance(expected_type, tuple):
                        if not isinstance(value, expected_type):
                            expected_names = [t.__name__ for t in expected_type]
                            self.validation_results.append(ValidationResult(
                                level="error",
                                message=f"Key '{key}' in section '{section_name}' has wrong type. Expected {' or '.join(expected_names)}, got {type(value).__name__}",
                                section=section_name,
                                key=key
                            ))
                    else:
                        if not isinstance(value, expected_type):
                            self.validation_results.append(ValidationResult(
                                level="error",
                                message=f"Key '{key}' in section '{section_name}' has wrong type. Expected {expected_type.__name__}, got {type(value).__name__}",
                                section=section_name,
                                key=key
                            ))
        
        # Check conditional sections based on feature flags
        protocol = self._get_nested_value_safe("server.protocol", "http")
        
        for feature_name, feature_config in self.feature_flags.items():
            enabled_key = feature_config["enabled_key"]
            
            # Skip SSL validation for HTTP protocol
            if feature_name in ["ssl", "transport_ssl"] and protocol not in ["https", "mtls"]:
                continue
            
            # Only check if the enabled key exists in the configuration
            if not self._has_nested_key(enabled_key):
                continue
                
            is_enabled = self._get_nested_value_safe(enabled_key, False)
            
            if is_enabled and feature_name in self.required_sections:
                section_name = feature_name
                required_keys = self.required_sections[section_name]
                
                if section_name not in self.config_data:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Required section '{section_name}' is missing for enabled feature",
                        section=section_name
                    ))
                    continue
                    
                section_data = self.config_data[section_name]
                for key, expected_type in required_keys.items():
                    # Check if key allows None (optional)
                    is_optional = isinstance(expected_type, tuple) and type(None) in expected_type
                    
                    if key not in section_data:
                        # Only report error if key is not optional
                        if not is_optional:
                            self.validation_results.append(ValidationResult(
                                level="error",
                                message=f"Required key '{key}' is missing in section '{section_name}' for enabled feature",
                                section=section_name,
                                key=key
                            ))
                    else:
                        # Validate type
                        value = section_data[key]
                        if isinstance(expected_type, tuple):
                            if not isinstance(value, expected_type):
                                expected_names = [t.__name__ for t in expected_type]
                                self.validation_results.append(ValidationResult(
                                    level="error",
                                    message=f"Key '{key}' in section '{section_name}' has wrong type. Expected {' or '.join(expected_names)}, got {type(value).__name__}",
                                    section=section_name,
                                    key=key
                                ))
                        else:
                            if not isinstance(value, expected_type):
                                self.validation_results.append(ValidationResult(
                                    level="error",
                                    message=f"Key '{key}' in section '{section_name}' has wrong type. Expected {expected_type.__name__}, got {type(value).__name__}",
                                    section=section_name,
                                    key=key
                                ))
    
    def _validate_feature_flags(self) -> None:
        """Validate feature flags and their dependencies."""
        protocol = self._get_nested_value_safe("server.protocol", "http")
        
        for feature_name, feature_config in self.feature_flags.items():
            enabled_key = feature_config["enabled_key"]
            
            # Skip SSL validation for HTTP protocol
            if feature_name in ["ssl", "transport_ssl"] and protocol not in ["https", "mtls"]:
                continue
            
            # Check if the enabled key exists in the configuration
            if not self._has_nested_key(enabled_key):
                # Skip validation if the feature flag key doesn't exist
                continue
                
            is_enabled = self._get_nested_value_safe(enabled_key, False)
            
            if is_enabled:
                # Check dependencies
                for dependency in feature_config["dependencies"]:
                    if not self._has_nested_key(dependency):
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message=f"Feature '{feature_name}' is enabled but required dependency '{dependency}' is missing",
                            section=feature_name,
                            key=dependency
                        ))
                
                # Check required files
                for file_key in feature_config["required_files"]:
                    if self._has_nested_key(file_key):
                        file_path = self._get_nested_value(file_key)
                        if file_path and not os.path.exists(file_path):
                            self.validation_results.append(ValidationResult(
                                level="error",
                                message=f"Feature '{feature_name}' is enabled but required file '{file_path}' does not exist",
                                section=feature_name,
                                key=file_key
                        ))
            else:
                # Feature is disabled - check that optional files are not required
                for file_key in feature_config["optional_files"]:
                    if self._has_nested_key(file_key):
                        file_path = self._get_nested_value(file_key)
                        if file_path and not os.path.exists(file_path):
                            self.validation_results.append(ValidationResult(
                                level="warning",
                                message=f"Optional file '{file_path}' for disabled feature '{feature_name}' does not exist",
                                section=feature_name,
                                key=file_key,
                                suggestion="This is not an error since the feature is disabled"
                            ))
    
    def _validate_protocol_requirements(self) -> None:
        """Validate protocol-specific requirements."""
        protocol = self._get_nested_value_safe("server.protocol", "http")
        
        # Check mTLS protocol requirements
        if protocol == "mtls":
            # mTLS requires HTTPS protocol
            if not self._has_nested_key("ssl.enabled"):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="mTLS protocol requires SSL configuration",
                    section="ssl",
                    key="enabled"
                ))
            else:
                ssl_enabled = self._get_nested_value_safe("ssl.enabled", False)
                if not ssl_enabled:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message="mTLS protocol requires SSL to be enabled",
                        section="ssl",
                        key="enabled"
                    ))
        
        if protocol not in self.protocol_requirements:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Unsupported protocol: {protocol}",
                section="server",
                key="protocol"
            ))
            return

        requirements = self.protocol_requirements[protocol]
        
        # Check SSL requirements
        if requirements["ssl_enabled"]:
            # Only check SSL if ssl section exists
            if self._has_nested_key("ssl.enabled"):
                ssl_enabled = self._get_nested_value_safe("ssl.enabled", False)
                if not ssl_enabled:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Protocol '{protocol}' requires SSL to be enabled",
                        section="ssl",
                        key="enabled"
                ))
            
            # Check required SSL files
            for file_key in requirements["required_files"]:
                if self._has_nested_key(file_key):
                    file_path = self._get_nested_value(file_key)
                    if not file_path:
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message=f"Protocol '{protocol}' requires {file_key} to be specified",
                            section="ssl",
                            key=file_key.split(".")[-1]
                        ))
                    elif not os.path.exists(file_path):
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message=f"Protocol '{protocol}' requires file '{file_path}' to exist",
                            section="ssl",
                            key=file_key.split(".")[-1]
                        ))
        
        # Check client verification requirements
        if requirements["client_verification"]:
            verify_client = self._get_nested_value_safe("transport.ssl.verify_client", False)
            if not verify_client:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"Protocol '{protocol}' requires client certificate verification",
                    section="transport.ssl",
                    key="verify_client"
                ))
    
    def _validate_file_existence(self) -> None:
        """Validate that all referenced files exist."""
        protocol = self._get_nested_value_safe("server.protocol", "http")
        
        file_keys = [
            "logging.log_dir",
            "commands.commands_directory",
            "commands.catalog_directory",
            "commands.custom_commands_path",
            "security.roles_file",
            "roles.config_file"
        ]
        
        # Only add SSL-related files if protocol requires SSL
        if protocol in ["https", "mtls"]:
            file_keys.extend([
                "ssl.cert_file",
                "ssl.key_file",
                "ssl.ca_cert",
                "transport.ssl.cert_file",
                "transport.ssl.key_file",
                "transport.ssl.ca_cert"
            ])
        
        # Only add proxy registration files if proxy registration is enabled
        if self._has_nested_key("proxy_registration.enabled"):
            proxy_enabled = self._get_nested_value_safe("proxy_registration.enabled", False)
            if proxy_enabled:
                file_keys.extend([
                    "proxy_registration.certificate.cert_file",
                    "proxy_registration.certificate.key_file"
                ])
        
        for file_key in file_keys:
            # Skip if the key doesn't exist in the configuration
            if not self._has_nested_key(file_key):
                continue
                
            file_path = self._get_nested_value_safe(file_key)
            if file_path and not os.path.exists(file_path):
                # Check if this is a required file based on enabled features
                is_required = self._is_file_required_for_enabled_features(file_key)
                level = "error" if is_required else "warning"
                
                self.validation_results.append(ValidationResult(
                    level=level,
                    message=f"Referenced file '{file_path}' does not exist",
                    section=file_key.split(".")[0],
                    key=file_key.split(".")[-1],
                    suggestion="Create the file or update the configuration" if is_required else "This file is optional"
                ))
    
    def _validate_security_consistency(self) -> None:
        """Validate security configuration consistency."""
        security_enabled = self._get_nested_value_safe("security.enabled", False)
        
        if security_enabled:
            # Check if authentication is properly configured
            tokens = self._get_nested_value_safe("security.tokens", {})
            roles = self._get_nested_value_safe("security.roles", {})
            roles_file = self._get_nested_value_safe("security.roles_file")
            
            has_tokens = bool(tokens and any(tokens.values()))
            has_roles = bool(roles and any(roles.values()))
            has_roles_file = bool(roles_file and os.path.exists(roles_file))
            
            if not (has_tokens or has_roles or has_roles_file):
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message="Security is enabled but no authentication methods are configured",
                    section="security",
                    suggestion="Configure tokens, roles, or roles_file in the security section"
                ))
            
            # Check roles consistency
            if has_roles and has_roles_file:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message="Both inline roles and roles_file are configured. roles_file will take precedence",
                    section="security",
                    suggestion="Remove either inline roles or roles_file configuration"
                ))
    
    def _validate_proxy_registration(self) -> None:
        """Validate proxy registration configuration."""
        registration_enabled = self._get_nested_value_safe("proxy_registration.enabled", False)
        
        if registration_enabled:
            if not self._has_nested_key("proxy_registration.proxy_url"):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="Proxy registration is enabled but proxy_url is not specified",
                    section="proxy_registration",
                    key="proxy_url"
                ))
            else:
                proxy_url = self._get_nested_value("proxy_registration.proxy_url")
                if not proxy_url:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message="Proxy registration is enabled but proxy_url is not specified",
                        section="proxy_registration",
                        key="proxy_url"
                    ))
            
            # Check authentication method consistency
            auth_method = self._get_nested_value_safe("proxy_registration.auth_method", "none")
            if auth_method != "none":
                if auth_method == "certificate":
                    if not self._has_nested_key("proxy_registration.certificate.cert_file"):
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message="Certificate authentication requires cert_file",
                            section="proxy_registration.certificate",
                            key="cert_file"
                        ))
                    else:
                        cert_file = self._get_nested_value("proxy_registration.certificate.cert_file")
                    
                    if not self._has_nested_key("proxy_registration.certificate.key_file"):
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message="Certificate authentication requires key_file",
                            section="proxy_registration.certificate",
                            key="key_file"
                        ))
                    else:
                        key_file = self._get_nested_value("proxy_registration.certificate.key_file")
                    
                    if not cert_file or not key_file:
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message="Certificate authentication is enabled but certificate files are not specified",
                            section="proxy_registration",
                            key="certificate"
                        ))
                elif auth_method == "token":
                    if not self._has_nested_key("proxy_registration.token.token"):
                        self.validation_results.append(ValidationResult(
                            level="error",
                            message="Token authentication requires token",
                            section="proxy_registration.token",
                            key="token"
                        ))
                    else:
                        token = self._get_nested_value("proxy_registration.token.token")
                        if not token:
                            self.validation_results.append(ValidationResult(
                                level="error",
                                message="Token authentication is enabled but token is not specified",
                                section="proxy_registration",
                                key="token"
                            ))
    
    def _validate_ssl_configuration(self) -> None:
        """Validate SSL configuration with detailed certificate validation."""
        # Only validate SSL if the protocol requires it
        protocol = self._get_nested_value_safe("server.protocol", "http")
        if protocol not in ["https", "mtls"]:
            return

        # Only validate SSL if the ssl section exists
        if not self._has_nested_key("ssl.enabled"):
            return

        ssl_enabled = self._get_nested_value_safe("ssl.enabled", False)
        
        if ssl_enabled:
            # Initialize variables
            cert_file = None
            key_file = None
            ca_cert = None
            
            if not self._has_nested_key("ssl.cert_file"):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="SSL is enabled but cert_file is not specified",
                    section="ssl",
                    key="cert_file"
                ))
            else:
                cert_file = self._get_nested_value("ssl.cert_file")
            
            if not self._has_nested_key("ssl.key_file"):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="SSL is enabled but key_file is not specified",
                    section="ssl",
                    key="key_file"
                ))
            else:
                key_file = self._get_nested_value("ssl.key_file")
            
            # CA cert is optional for HTTPS but may be required for mTLS with client verification
            if self._has_nested_key("ssl.ca_cert"):
                ca_cert = self._get_nested_value_safe("ssl.ca_cert")
            
            # Check certificate file
            if not cert_file:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="SSL is enabled but cert_file is not specified",
                    section="ssl",
                    key="cert_file"
                ))
            elif not os.path.exists(cert_file):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"SSL certificate file '{cert_file}' does not exist",
                    section="ssl",
                    key="cert_file"
                ))
            else:
                # Validate certificate file
                self._validate_certificate_file(cert_file, "ssl", "cert_file")
            
            # Check key file
            if not key_file:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="SSL is enabled but key_file is not specified",
                    section="ssl",
                    key="key_file"
                ))
            elif not os.path.exists(key_file):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"SSL key file '{key_file}' does not exist",
                    section="ssl",
                    key="key_file"
                ))
            else:
                # Validate key file
                self._validate_key_file(key_file, "ssl", "key_file")
            
            # Check CA certificate if specified
            if ca_cert:
                if not os.path.exists(ca_cert):
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"SSL CA certificate file '{ca_cert}' does not exist",
                        section="ssl",
                        key="ca_cert"
                    ))
                else:
                    # Validate CA certificate
                    self._validate_ca_certificate_file(ca_cert, "ssl", "ca_cert")
            
            # Validate certificate-key pair if both exist
            if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
                self._validate_certificate_key_pair(cert_file, key_file, ca_cert, "ssl")
    
    def _validate_roles_configuration(self) -> None:
        """Validate roles configuration."""
        roles_enabled = self._get_nested_value_safe("roles.enabled", False)
        
        if roles_enabled:
            if not self._has_nested_key("roles.config_file"):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message="Roles are enabled but config_file is not specified",
                    section="roles",
                    key="config_file"
                ))
            else:
                config_file = self._get_nested_value("roles.config_file")
                if not config_file:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message="Roles are enabled but config_file is not specified",
                        section="roles",
                        key="config_file"
                    ))
                elif not os.path.exists(config_file):
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Roles config file '{config_file}' does not exist",
                        section="roles",
                        key="config_file"
                    ))  
    
    def _get_nested_value(self, key: str) -> Any:
        """Get value from nested dictionary using dot notation. Raises exception if key not found."""
        keys = key.split(".")
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise MissingConfigKeyError(k, ".".join(keys[:keys.index(k)]))
                
        return value
    
    def _has_nested_key(self, key: str) -> bool:
        """Check if nested key exists in configuration."""
        keys = key.split(".")
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
                
        return True
    
    def _get_nested_value_safe(self, key: str, default: Any = None) -> Any:
        """Get value from nested dictionary using dot notation with fallback."""
        try:
            return self._get_nested_value(key)
        except MissingConfigKeyError:
            return default
    
    def _is_file_required_for_enabled_features(self, file_key: str) -> bool:
        """Check if file is required based on enabled features."""
        for feature_name, feature_config in self.feature_flags.items():
            enabled_key = feature_config["enabled_key"]
            is_enabled = self._get_nested_value_safe(enabled_key, False)
            
            if is_enabled and file_key in feature_config["required_files"]:
                return True
                
        return False
    
    def _validate_certificate_file(self, cert_file: str, section: str, key: str) -> None:
        """Validate certificate file format and content."""
        try:
            import cryptography
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization
            
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            
            # Try to parse as PEM
            try:
                cert = x509.load_pem_x509_certificate(cert_data)
            except Exception:
                # Try to parse as DER
                try:
                    cert = x509.load_der_x509_certificate(cert_data)
                except Exception as e:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Certificate file '{cert_file}' is not a valid PEM or DER certificate: {e}",
                        section=section,
                        key=key
                    ))
                    return
            
            # Check certificate expiration
            now = datetime.now(timezone.utc)
            not_after = cert.not_valid_after_utc
            
            if now > not_after:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"Certificate '{cert_file}' has expired on {not_after.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    section=section,
                    key=key
                ))
            elif (not_after - now).days < 30:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message=f"Certificate '{cert_file}' expires in {(not_after - now).days} days on {not_after.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    section=section,
                    key=key,
                    suggestion="Consider renewing the certificate"
                ))
            
            # Check if certificate is self-signed
            issuer = cert.issuer
            subject = cert.subject
            
            if issuer == subject:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message=f"Certificate '{cert_file}' is self-signed",
                    section=section,
                    key=key,
                    suggestion="Consider using a certificate from a trusted CA for production"
                ))
            
            # Check certificate key usage
            try:
                key_usage = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.KEY_USAGE)
                if not key_usage.value.digital_signature:
                    self.validation_results.append(ValidationResult(
                        level="warning",
                        message=f"Certificate '{cert_file}' does not have digital signature key usage",
                        section=section,
                        key=key,
                        suggestion="Ensure the certificate supports digital signature for SSL/TLS"
                    ))
            except x509.ExtensionNotFound:
                pass  # Key usage extension not present, which is sometimes OK
            
        except ImportError:
            # cryptography library not available, do basic validation
            self.validation_results.append(ValidationResult(
                level="warning",
                message=f"Cannot validate certificate '{cert_file}' - cryptography library not available",
                section=section,
                key=key,
                suggestion="Install cryptography library for detailed certificate validation"
            ))
        except Exception as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Error validating certificate '{cert_file}': {e}",
                section=section,
                key=key
            ))
    
    def _validate_key_file(self, key_file: str, section: str, key: str) -> None:
        """Validate private key file format and content."""
        try:
            import cryptography
            from cryptography.hazmat.primitives import serialization
            
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            # Try to parse as PEM
            try:
                private_key = serialization.load_pem_private_key(
                    key_data, 
                    password=None
                )
            except Exception:
                # Try to parse as DER
                try:
                    private_key = serialization.load_der_private_key(
                        key_data, 
                        password=None
                    )
                except Exception as e:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Key file '{key_file}' is not a valid PEM or DER private key: {e}",
                        section=section,
                        key=key
                    ))
                    return
            
            # Check key size
            if hasattr(private_key, 'key_size'):
                if private_key.key_size < 2048:
                    self.validation_results.append(ValidationResult(
                        level="warning",
                        message=f"Private key '{key_file}' has key size {private_key.key_size} bits, which is below recommended 2048 bits",
                        section=section,
                        key=key,
                        suggestion="Consider using a key with at least 2048 bits for better security"
                    ))
            
        except ImportError:
            # cryptography library not available, do basic validation
            self.validation_results.append(ValidationResult(
                level="warning",
                message=f"Cannot validate private key '{key_file}' - cryptography library not available",
                section=section,
                key=key,
                suggestion="Install cryptography library for detailed key validation"
            ))
        except Exception as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Error validating private key '{key_file}': {e}",
                section=section,
                key=key
            ))
    
    def _validate_ca_certificate_file(self, ca_cert_file: str, section: str, key: str) -> None:
        """Validate CA certificate file."""
        try:
            import cryptography
            from cryptography import x509
            
            with open(ca_cert_file, 'rb') as f:
                ca_data = f.read()
            
            # Try to parse as PEM
            try:
                ca_cert = x509.load_pem_x509_certificate(ca_data)
            except Exception:
                # Try to parse as DER
                try:
                    ca_cert = x509.load_der_x509_certificate(ca_data)
                except Exception as e:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"CA certificate file '{ca_cert_file}' is not a valid PEM or DER certificate: {e}",
                        section=section,
                        key=key
                    ))
            return

            # Check CA certificate expiration
            now = datetime.now(timezone.utc)
            not_after = ca_cert.not_valid_after.replace(tzinfo=timezone.utc)
            
            if now > not_after:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"CA certificate '{ca_cert_file}' has expired on {not_after.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    section=section,
                    key=key
                ))
            elif (not_after - now).days < 30:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message=f"CA certificate '{ca_cert_file}' expires in {(not_after - now).days} days on {not_after.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    section=section,
                    key=key,
                    suggestion="Consider renewing the CA certificate"
                ))
            
            # Check if CA certificate has CA basic constraint
            try:
                basic_constraints = ca_cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.BASIC_CONSTRAINTS)
                if not basic_constraints.value.ca:
                    self.validation_results.append(ValidationResult(
                        level="warning",
                        message=f"CA certificate '{ca_cert_file}' does not have CA basic constraint set",
                        section=section,
                        key=key,
                        suggestion="Ensure the certificate is marked as a CA certificate"
                    ))
            except x509.ExtensionNotFound:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message=f"CA certificate '{ca_cert_file}' does not have basic constraints extension",
                    section=section,
                    key=key,
                    suggestion="Consider using a proper CA certificate with basic constraints"
                ))
            
        except ImportError:
            # cryptography library not available
            self.validation_results.append(ValidationResult(
                level="warning",
                message=f"Cannot validate CA certificate '{ca_cert_file}' - cryptography library not available",
                section=section,
                key=key,
                suggestion="Install cryptography library for detailed CA certificate validation"
            ))
        except Exception as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Error validating CA certificate '{ca_cert_file}': {e}",
                section=section,
                key=key
            ))
    
    def _validate_certificate_key_pair(self, cert_file: str, key_file: str, ca_cert_file: Optional[str], section: str) -> None:
        """Validate that certificate and key are a matching pair."""
        try:
            import cryptography
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import rsa, padding
            
            # Load certificate
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            
            try:
                cert = x509.load_pem_x509_certificate(cert_data)
            except Exception:
                cert = x509.load_der_x509_certificate(cert_data)
            
            # Load private key
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            try:
                private_key = serialization.load_pem_private_key(key_data, password=None)
            except Exception:
                private_key = serialization.load_der_private_key(key_data, password=None)
            
            # Check if certificate public key matches private key
            cert_public_key = cert.public_key()
            
            # For RSA keys, compare modulus
            if isinstance(cert_public_key, rsa.RSAPublicKey) and isinstance(private_key, rsa.RSAPrivateKey):
                if cert_public_key.public_numbers().n != private_key.public_key().public_numbers().n:
                    self.validation_results.append(ValidationResult(
                        level="error",
                        message=f"Certificate '{cert_file}' and private key '{key_file}' do not match",
                        section=section,
                        key="cert_file",
                        suggestion="Ensure the certificate and private key are from the same key pair"
                    ))
            return

            # If CA certificate is provided, validate certificate chain
            if ca_cert_file and os.path.exists(ca_cert_file):
                self._validate_certificate_chain(cert_file, ca_cert_file, section)
            
        except ImportError:
            # cryptography library not available
            self.validation_results.append(ValidationResult(
                level="warning",
                message=f"Cannot validate certificate-key pair - cryptography library not available",
                section=section,
                key="cert_file",
                suggestion="Install cryptography library for detailed certificate validation"
            ))
        except Exception as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Error validating certificate-key pair: {e}",
                section=section,
                key="cert_file"
            ))
    
    def _validate_certificate_chain(self, cert_file: str, ca_cert_file: str, section: str) -> None:
        """Validate certificate chain against CA certificate."""
        try:
            import cryptography
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            
            # Load certificate
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            
            try:
                cert = x509.load_pem_x509_certificate(cert_data)
            except Exception:
                cert = x509.load_der_x509_certificate(cert_data)
            
            # Load CA certificate
            with open(ca_cert_file, 'rb') as f:
                ca_data = f.read()
            
            try:
                ca_cert = x509.load_pem_x509_certificate(ca_data)
            except Exception:
                ca_cert = x509.load_der_x509_certificate(ca_data)
            
            # Verify certificate signature with CA
            try:
                ca_cert.public_key().verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    cert.signature_algorithm_oid._name
                )
            except Exception as e:
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"Certificate '{cert_file}' is not signed by CA certificate '{ca_cert_file}': {e}",
                    section=section,
                    key="cert_file",
                    suggestion="Ensure the certificate is properly signed by the CA"
                ))
                return
            
            # Check if certificate issuer matches CA subject
            if cert.issuer != ca_cert.subject:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message=f"Certificate issuer '{cert.issuer}' does not match CA subject '{ca_cert.subject}'",
                    section=section,
                    key="cert_file",
                    suggestion="Verify that the certificate is issued by the correct CA"
                ))
            
        except ImportError:
            # cryptography library not available
            self.validation_results.append(ValidationResult(
                level="warning",
                message=f"Cannot validate certificate chain - cryptography library not available",
                section=section,
                key="cert_file",
                suggestion="Install cryptography library for detailed certificate chain validation"
            ))
        except Exception as e:
            self.validation_results.append(ValidationResult(
                level="error",
                message=f"Error validating certificate chain: {e}",
                section=section,
                key="cert_file"
            ))
    
    def _validate_uuid_format(self) -> None:
        """Validate UUID4 format in configuration."""
        
        # Check root level UUID
        if "uuid" in self.config_data:
            uuid_value = self.config_data["uuid"]
            if not self._is_valid_uuid4(uuid_value):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"Invalid UUID4 format: '{uuid_value}'. Expected format: xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx",
                    section="uuid",
                    key="uuid"
                ))
        
        # Check proxy_registration UUID if it exists
        if self._has_nested_key("proxy_registration.uuid"):
            uuid_value = self._get_nested_value("proxy_registration.uuid")
            if not self._is_valid_uuid4(uuid_value):
                self.validation_results.append(ValidationResult(
                    level="error",
                    message=f"Invalid UUID4 format in proxy_registration: '{uuid_value}'. Expected format: xxxxxxxx-xxxx-4xxx-xxxx-xxxxxxxxxxxx",
                    section="proxy_registration",
                    key="uuid"
                ))
    
    def _is_valid_uuid4(self, uuid_str: str) -> bool:
        """Check if string is a valid UUID4."""
        if not isinstance(uuid_str, str):
            return False
        
        uuid4_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        return bool(re.match(uuid4_pattern, uuid_str, re.IGNORECASE))
    
    def _validate_unknown_fields(self) -> None:
        """Validate that no unknown fields are present in configuration."""
        # Define all known sections and their allowed fields
        known_sections = {
            "server": {"host", "port", "protocol", "debug", "log_level"},
            "logging": {"level", "file", "log_dir", "log_file", "error_log_file", "access_log_file", 
                       "max_file_size", "backup_count", "format", "date_format", "console_output", "file_output"},
            "commands": {"auto_discovery", "commands_directory", "catalog_directory", "plugin_servers",
                        "auto_install_dependencies", "enabled_commands", "disabled_commands", "custom_commands_path"},
            "transport": {"type", "port", "verify_client", "chk_hostname", "ssl"},
            "proxy_registration": {"enabled", "proxy_url", "server_id", "server_name", "description", "version",
                                 "registration_timeout", "retry_attempts", "retry_delay", "auto_register_on_startup",
                                 "auto_unregister_on_shutdown", "uuid", "heartbeat"},
            "debug": {"enabled", "level"},
            "security": {"enabled", "tokens", "roles", "roles_file"},
            "roles": {"enabled", "config_file", "default_policy", "auto_load", "validation_enabled"},
            "ssl": {"enabled", "cert_file", "key_file", "ca_cert"},
            "uuid": set()  # Root level UUID
        }
        
        # Check for unknown root level fields
        for field in self.config_data:
            if field not in known_sections:
                self.validation_results.append(ValidationResult(
                    level="warning",
                    message=f"Unknown field '{field}' at root level",
                    section=field,
                    suggestion="Check if this field is needed or if it's a typo"
                ))
        
        # Check for unknown fields in known sections
        for section_name, allowed_fields in known_sections.items():
            if section_name in self.config_data:
                section_data = self.config_data[section_name]
                if isinstance(section_data, dict):
                    for field in section_data:
                        if field not in allowed_fields:
                            self.validation_results.append(ValidationResult(
                                level="warning",
                                message=f"Unknown field '{field}' in section '{section_name}'",
                                section=section_name,
                                key=field,
                                suggestion="Check if this field is needed or if it's a typo"
                            ))
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        error_count = sum(1 for r in self.validation_results if r.level == "error")
        warning_count = sum(1 for r in self.validation_results if r.level == "warning")
        info_count = sum(1 for r in self.validation_results if r.level == "info")
        
        return {
            "total_issues": len(self.validation_results),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "is_valid": error_count == 0
        }
    
    def print_validation_report(self) -> None:
        """Print detailed validation report."""
        summary = self.get_validation_summary()
        
        print("=" * 60)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        print(f"Total issues: {summary['total_issues']}")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Info: {summary['info']}")
        print(f"Configuration is valid: {summary['is_valid']}")
        print("=" * 60)
        
        if self.validation_results:
            for result in self.validation_results:
                level_symbol = {
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }[result.level]
                
                location = f"{result.section}.{result.key}" if result.key else result.section
                print(f"{level_symbol} [{result.level.value.upper()}] {result.message}")
                if location:
                    print(f"   Location: {location}")
                if result.suggestion:
                    print(f"   Suggestion: {result.suggestion}")
                print()
        else:
            print("✅ No issues found in configuration!")


def validate_config_file(config_path: str) -> bool:
    """
    Validate a configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if configuration is valid, False otherwise
    """
    validator = ConfigValidator(config_path)
    validator.load_config()
    validator.validate_config()
    
    validator.print_validation_report()
    return validator.get_validation_summary()["is_valid"]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python config_validator.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    is_valid = validate_config_file(config_file)
    sys.exit(0 if is_valid else 1)