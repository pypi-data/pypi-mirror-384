"""
Module for microservice configuration management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import logging
import os
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)

# Import validation if available
try:
    from .core.config_validator import ConfigValidator, ValidationResult, ValidationLevel
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    logger.warning("Configuration validation not available. Install the package to enable validation.")

# Import configuration errors
from .core.errors import ConfigError, ValidationResult


class Config:
    """
    Configuration management class for the microservice.
    Allows loading settings from configuration file and environment variables.
    Supports optional features that can be enabled/disabled.
    """

    def __init__(self, config_path: Optional[str] = None, validate_on_load: bool = True):
        """
        Initialize configuration.

        Args:
            config_path: Path to configuration file. If not specified,
                        "./config.json" is used.
            validate_on_load: Whether to validate configuration on load (default: True)
        
        Raises:
            ConfigError: If configuration validation fails
        """
        self.config_path = config_path or "./config.json"
        self.config_data: Dict[str, Any] = {}
        self.validate_on_load = validate_on_load
        self.validation_results: List[ValidationResult] = []
        self.validator = None
        
        if VALIDATION_AVAILABLE:
            self.validator = ConfigValidator()
        
        # Don't auto-load config - let user call load_from_file explicitly

    def load_config(self) -> None:
        """
        Load configuration from file and environment variables.
        NO DEFAULT VALUES - configuration must be complete and valid.
        """
        # Load configuration from file - NO DEFAULTS
        if not os.path.exists(self.config_path):
            raise ConfigError(f"Configuration file '{self.config_path}' does not exist. Use the configuration generator to create a valid configuration.")
        
        try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Configuration file '{self.config_path}' contains invalid JSON: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration from '{self.config_path}': {e}")
        
        # Validate configuration BEFORE applying any logic
        if self.validate_on_load:
            if VALIDATION_AVAILABLE and self.validator:
                self.validator.config_data = self.config_data
                validation_results = self.validator.validate_config()
                
                # Check for critical errors
                errors = [r for r in validation_results if r.level == "error"]
                if errors:
                    error_summary = "\n".join([f"[{r.section}.{r.key if r.key else 'root'}] {r.message}" for r in errors])
                    raise ConfigError(f"Configuration validation failed with {len(errors)} error(s):\n{error_summary}", errors)
                
                # Store validation results for later access
                self.validation_results = validation_results
            else:
                raise ConfigError("Configuration validation is not available. Install required dependencies.")
        
        # Load configuration from environment variables (overrides file values)
        self._load_env_variables()
        
        # Apply hostname check logic based on SSL configuration
        self._validate_security_config()
        self._apply_hostname_check_logic()

    def load_from_file(self, config_path: str) -> None:
        """
        Load configuration from the specified file.

        Args:
            config_path: Path to configuration file.
        """
        self.config_path = config_path
        self.load_config()

    def _load_env_variables(self) -> None:
        """
        Load configuration from environment variables.
        Environment variables should be in format SERVICE_SECTION_KEY=value.
        For example, SERVICE_SERVER_PORT=8080.
        """
        prefix = "SERVICE_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix) :].lower().split("_", 1)
                if len(parts) == 2:
                    section, param = parts
                    if section not in self.config_data:
                        self.config_data[section] = {}
                    self.config_data[section][param] = self._convert_env_value(value)

    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable value to appropriate type.

        Args:
            value: Value as string

        Returns:
            Converted value
        """
        # Try to convert to appropriate type
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.isdigit():
            return int(value)
        else:
            try:
                return float(value)
            except ValueError:
                return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value for key.

        Args:
            key: Configuration key in format "section.param"
            default: Default value if key not found

        Returns:
            Configuration value
        """
        parts = key.split(".")

        # Get value from config
        value = self.config_data
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]

        return value

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration values
        """
        return self.config_data.copy()

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value for key.

        Args:
            key: Configuration key in format "section.param"
            value: Configuration value
        """
        parts = key.split(".")
        if len(parts) == 1:
            self.config_data[key] = value
        else:
            section = parts[0]
            param_key = ".".join(parts[1:])

            if section not in self.config_data:
                self.config_data[section] = {}

            current = self.config_data[section]
            for part in parts[1:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value
            
            # Special handling for chk_hostname - mark it as user-set
            if key == "transport.ssl.chk_hostname":
                if "ssl" not in self.config_data.get("transport", {}):
                    self.config_data["transport"]["ssl"] = {}
                self.config_data["transport"]["ssl"]["_chk_hostname_user_set"] = True

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Path to configuration file. If not specified,
                  self.config_path is used.
        """
        save_path = path or self.config_path
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.config_data, f, indent=2)


    def enable_feature(self, feature: str) -> None:
        """
        Enable a specific feature in the configuration.

        Args:
            feature: Feature to enable (ssl, auth, roles, proxy_registration,
                     security)
        """
        if feature == "ssl":
            self.set("ssl.enabled", True)
            self.set("security.ssl.enabled", True)
        elif feature == "auth":
            self.set("security.auth.enabled", True)
        elif feature == "roles":
            self.set("security.permissions.enabled", True)
            self.set("roles.enabled", True)
        elif feature == "proxy_registration":
            self.set("proxy_registration.enabled", True)
        elif feature == "security":
            self.set("security.enabled", True)
        elif feature == "rate_limit":
            self.set("security.rate_limit.enabled", True)
        elif feature == "certificates":
            self.set("security.certificates.enabled", True)
        else:
            raise ValueError(f"Unknown feature: {feature}")

    def disable_feature(self, feature: str) -> None:
        """
        Disable a specific feature in the configuration.

        Args:
            feature: Feature to disable (ssl, auth, roles, proxy_registration,
                     security)
        """
        if feature == "ssl":
            self.set("ssl.enabled", False)
            self.set("security.ssl.enabled", False)
        elif feature == "auth":
            self.set("security.auth.enabled", False)
        elif feature == "roles":
            self.set("security.permissions.enabled", False)
            self.set("roles.enabled", False)
        elif feature == "proxy_registration":
            self.set("proxy_registration.enabled", False)
        elif feature == "security":
            self.set("security.enabled", False)
        elif feature == "rate_limit":
            self.set("security.rate_limit.enabled", False)
        elif feature == "certificates":
            self.set("security.certificates.enabled", False)
        else:
            raise ValueError(f"Unknown feature: {feature}")

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a specific feature is enabled.

        Args:
            feature: Feature to check (ssl, auth, roles, proxy_registration,
                     security)

        Returns:
            True if feature is enabled, False otherwise
        """
        if feature == "ssl":
            return self.get("ssl.enabled", False) or self.get(
                "security.ssl.enabled", False
            )
        elif feature == "auth":
            return self.get("security.auth.enabled", False)
        elif feature == "roles":
            return self.get("security.permissions.enabled", False) or self.get(
                "roles.enabled", False
            )
        elif feature == "proxy_registration":
            return self.get("proxy_registration.enabled", False)
        elif feature == "security":
            return self.get("security.enabled", False)
        elif feature == "rate_limit":
            return self.get("security.rate_limit.enabled", False)
        elif feature == "certificates":
            return self.get("security.certificates.enabled", False)
        else:
            raise ValueError(f"Unknown feature: {feature}")

    def get_enabled_features(self) -> List[str]:
        """
        Get list of all enabled features.

        Returns:
            List of enabled feature names
        """
        features = []
        if self.is_feature_enabled("ssl"):
            features.append("ssl")
        if self.is_feature_enabled("auth"):
            features.append("auth")
        if self.is_feature_enabled("roles"):
            features.append("roles")
        if self.is_feature_enabled("proxy_registration"):
            features.append("proxy_registration")
        if self.is_feature_enabled("security"):
            features.append("security")
        if self.is_feature_enabled("rate_limit"):
            features.append("rate_limit")
        if self.is_feature_enabled("certificates"):
            features.append("certificates")
        return features

    def configure_auth_mode(self, mode: str, **kwargs) -> None:
        """
        Configure authentication mode.

        Args:
            mode: Authentication mode (api_key, jwt, certificate, basic, oauth2)
            **kwargs: Additional configuration parameters
        """
        if mode == "api_key":
            self.set("security.auth.methods", ["api_key"])
            if "api_keys" in kwargs:
                self.set("security.auth.api_keys", kwargs["api_keys"])
        elif mode == "jwt":
            self.set("security.auth.methods", ["jwt"])
            if "jwt_secret" in kwargs:
                self.set("security.auth.jwt_secret", kwargs["jwt_secret"])
        elif mode == "certificate":
            self.set("security.auth.methods", ["certificate"])
            self.set("security.auth.certificate_auth", True)
        elif mode == "basic":
            self.set("security.auth.methods", ["basic"])
            self.set("security.auth.basic_auth", True)
        elif mode == "oauth2":
            self.set("security.auth.methods", ["oauth2"])
            if "oauth2_config" in kwargs:
                self.set("security.auth.oauth2_config", kwargs["oauth2_config"])
        else:
            raise ValueError(f"Unknown authentication mode: {mode}")

    def configure_proxy_registration_mode(self, mode: str, **kwargs) -> None:
        """
        Configure proxy registration mode.

        Args:
            mode: Registration mode (token, certificate, api_key, none)
            **kwargs: Additional configuration parameters
        """
        if mode == "none":
            self.set("proxy_registration.enabled", False)
        else:
            self.set("proxy_registration.enabled", True)

            if mode == "token":
                self.set("proxy_registration.auth_method", "token")
                if "token" in kwargs:
                    self.set("proxy_registration.token.token", kwargs["token"])
            elif mode == "certificate":
                self.set("proxy_registration.auth_method", "certificate")
                if "cert_file" in kwargs:
                    self.set(
                        "proxy_registration.certificate.cert_file", kwargs["cert_file"]
                    )
                if "key_file" in kwargs:
                    self.set(
                        "proxy_registration.certificate.key_file", kwargs["key_file"]
                    )
            elif mode == "api_key":
                self.set("proxy_registration.auth_method", "api_key")
                if "key" in kwargs:
                    self.set("proxy_registration.api_key.key", kwargs["key"])

    def create_minimal_config(self) -> Dict[str, Any]:
        """
        Create minimal configuration with only essential features.

        Returns:
            Minimal configuration dictionary
        """
        minimal_config = self.config_data.copy()

        # Disable all optional features
        minimal_config["ssl"]["enabled"] = False
        minimal_config["security"]["enabled"] = False
        minimal_config["security"]["auth"]["enabled"] = False
        minimal_config["security"]["permissions"]["enabled"] = False
        minimal_config["security"]["rate_limit"]["enabled"] = False
        minimal_config["security"]["certificates"]["enabled"] = False
        minimal_config["proxy_registration"]["enabled"] = False
        minimal_config["roles"]["enabled"] = False

        return minimal_config

    def create_secure_config(self) -> Dict[str, Any]:
        """
        Create secure configuration with all security features enabled.

        Returns:
            Secure configuration dictionary
        """
        secure_config = self.config_data.copy()

        # Enable all security features
        secure_config["ssl"]["enabled"] = True
        secure_config["security"]["enabled"] = True
        secure_config["security"]["auth"]["enabled"] = True
        secure_config["security"]["permissions"]["enabled"] = True
        secure_config["security"]["rate_limit"]["enabled"] = True
        secure_config["security"]["certificates"]["enabled"] = True
        secure_config["proxy_registration"]["enabled"] = True
        secure_config["roles"]["enabled"] = True

        return secure_config

    def _validate_security_config(self) -> None:
        """
        Validate security configuration and log warnings for incomplete setup.
        """
        if not self.get("security.enabled", False):
            return
            
        # Check if security is enabled but no authentication methods are configured
        tokens = self.get("security.tokens", {})
        roles = self.get("security.roles", {})
        roles_file = self.get("security.roles_file")
        
        has_tokens = bool(tokens and any(tokens.values()))
        has_roles = bool(roles and any(roles.values()))
        has_roles_file = bool(roles_file and os.path.exists(roles_file))
        
        if not (has_tokens or has_roles or has_roles_file):
            logger.warning(
                "Security is enabled but no authentication methods are configured. "
                "Please configure tokens, roles, or roles_file in the security section."
            )

    def _apply_hostname_check_logic(self) -> None:
        """
        Apply hostname check logic based on protocol configuration.
        chk_hostname should be True for HTTPS/mTLS protocols, False for HTTP.
        Only set default values if chk_hostname is not explicitly configured.
        """
        protocol = self.get("server.protocol", "http")
        ssl_enabled = self.get("transport.ssl.enabled", False)
        
        # Check if chk_hostname is explicitly set by the user
        # We check if it was set by looking for a special flag
        transport_section = self.config_data.get("transport", {})
        ssl_section = transport_section.get("ssl", {})
        chk_hostname_explicitly_set = ssl_section.get("_chk_hostname_user_set", False)
        
        # Set chk_hostname based on protocol only if not explicitly set
        if not chk_hostname_explicitly_set:
            if protocol in ["https", "mtls"]:
                # For HTTPS/mTLS, enable hostname checking by default
                self.set("transport.ssl.chk_hostname", True)
                logger.debug(f"Set chk_hostname=True for protocol {protocol} (default)")
            else:
                # For HTTP, disable hostname checking
                self.set("transport.ssl.chk_hostname", False)
                logger.debug(f"Set chk_hostname=False for protocol {protocol} (default)")
        else:
            # Log the explicitly set value
            chk_hostname_value = self.get("transport.ssl.chk_hostname")
            logger.debug(f"Using explicitly set chk_hostname={chk_hostname_value} for protocol {protocol}")

    def validate(self) -> List[ValidationResult]:
        """
        Validate current configuration.
        
        Returns:
            List of validation results
            
        Raises:
            ConfigError: If validation is not available or critical errors are found
        """
        if not VALIDATION_AVAILABLE:
            raise ConfigError("Configuration validation is not available. Please install the package properly.")
        
        if not self.validator:
            self.validator = ConfigValidator()
        
        self.validator.config_data = self.config_data
        self.validation_results = self.validator.validate_config()
        
        # Log validation results
        for result in self.validation_results:
            if result.level == ValidationLevel.ERROR:
                get_global_logger().error(f"Configuration error: {result.message}")
            elif result.level == ValidationLevel.WARNING:
                get_global_logger().warning(f"Configuration warning: {result.message}")
            else:
                get_global_logger().info(f"Configuration info: {result.message}")
        
        # Raise ConfigError if there are critical errors
        errors = [r for r in self.validation_results if r.level == ValidationLevel.ERROR]
        if errors:
            error_summary = "\n".join([f"[{r.section}.{r.key if r.key else 'root'}] {r.message}" for r in errors])
            raise ConfigError(f"Configuration validation failed with {len(errors)} error(s):\n{error_summary}", errors)
        
        return self.validation_results
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        if not VALIDATION_AVAILABLE:
            return True
        
        return all(result.level != ValidationLevel.ERROR for result in self.validation_results)
    
    def get_validation_errors(self) -> List[ValidationResult]:
        """Get all validation errors."""
        return [r for r in self.validation_results if r.level == ValidationLevel.ERROR]
    
    def get_validation_warnings(self) -> List[ValidationResult]:
        """Get all validation warnings."""
        return [r for r in self.validation_results if r.level == ValidationLevel.WARNING]
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        if not VALIDATION_AVAILABLE or not self.validator:
            return {"total_issues": 0, "errors": 0, "warnings": 0, "info": 0, "is_valid": True}
        
        return self.validator.get_validation_summary()
    
    def print_validation_report(self) -> None:
        """Print detailed validation report."""
        if not VALIDATION_AVAILABLE or not self.validator:
            print("Configuration validation not available")
            return
        
        self.validator.print_validation_report()
    
    def check_feature_requirements(self, feature: str) -> List[ValidationResult]:
        """Check if all requirements for a feature are met."""
        if not VALIDATION_AVAILABLE:
            return []
        
        results = []
        
        if feature == "security":
            if self.get("security.enabled", False):
                tokens = self.get("security.tokens", {})
                roles = self.get("security.roles", {})
                roles_file = self.get("security.roles_file")
                
                has_tokens = bool(tokens and any(tokens.values()))
                has_roles = bool(roles and any(roles.values()))
                has_roles_file = bool(roles_file and os.path.exists(roles_file))
                
                if not (has_tokens or has_roles or has_roles_file):
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message="Security is enabled but no authentication methods are configured",
                        section="security",
                        suggestion="Configure tokens, roles, or roles_file"
                    ))
        
        elif feature == "roles":
            if self.get("roles.enabled", False):
                config_file = self.get("roles.config_file")
                if not config_file:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message="Roles are enabled but config_file is not specified",
                        section="roles",
                        key="config_file"
                    ))
                elif not os.path.exists(config_file):
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"Roles config file '{config_file}' does not exist",
                        section="roles",
                        key="config_file"
                    ))
        
        elif feature == "ssl":
            if self.get("ssl.enabled", False):
                cert_file = self.get("ssl.cert_file")
                key_file = self.get("ssl.key_file")
                
                if not cert_file:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message="SSL is enabled but cert_file is not specified",
                        section="ssl",
                        key="cert_file"
                    ))
                elif not os.path.exists(cert_file):
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"SSL certificate file '{cert_file}' does not exist",
                        section="ssl",
                        key="cert_file"
                    ))
                
                if not key_file:
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message="SSL is enabled but key_file is not specified",
                        section="ssl",
                        key="key_file"
                    ))
                elif not os.path.exists(key_file):
                    results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        message=f"SSL key file '{key_file}' does not exist",
                        section="ssl",
                        key="key_file"
                    ))
        
        return results


# Singleton instance - will be created when needed
config = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = Config()
    return config
