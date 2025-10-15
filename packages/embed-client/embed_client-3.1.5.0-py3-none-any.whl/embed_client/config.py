"""
Client configuration management module.

This module provides configuration management for the embed-client,
supporting all security modes and authentication methods.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
import os
from typing import Any, Dict, Optional, List, Union
from pathlib import Path


class ClientConfig:
    """
    Configuration management class for the embed-client.
    Allows loading settings from configuration file and environment variables.
    Supports all security modes and authentication methods.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize client configuration.

        Args:
            config_path: Path to configuration file. If not specified,
                        "./config.json" is used.
        """
        self.config_path = config_path or "./config.json"
        self.config_data: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """
        Load configuration from file and environment variables.
        """
        # Set default config values
        self.config_data = {
            "server": {
                "host": "localhost",
                "port": 8001,
                "base_url": "http://localhost:8001"
            },
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
            "auth": {
                "method": "none",  # none, api_key, jwt, certificate, basic
                "api_key": {
                    "key": None,
                    "header": "X-API-Key"
                },
                "jwt": {
                    "username": None,
                    "password": None,
                    "secret": None,
                    "expiry_hours": 24
                },
                "certificate": {
                    "enabled": False,
                    "cert_file": None,
                    "key_file": None,
                    "ca_cert_file": None
                },
                "basic": {
                    "username": None,
                    "password": None
                }
            },
            "ssl": {
                "enabled": False,
                "verify": True,
                "check_hostname": True,
                "cert_file": None,
                "key_file": None,
                "ca_cert_file": None,
                "client_cert_required": False
            },
            "security": {
                "enabled": False,
                "roles_enabled": False,
                "roles_file": None
            },
            "logging": {
                "enabled": False,
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }

        # Try to load configuration from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._update_nested_dict(self.config_data, file_config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")

        # Load configuration from environment variables
        self._load_env_variables()

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
        Environment variables should be in format EMBED_CLIENT_SECTION_KEY=value.
        For example, EMBED_CLIENT_SERVER_PORT=8080.
        """
        prefix = "EMBED_CLIENT_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split("_", 1)
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

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Path to configuration file. If not specified,
                  self.config_path is used.
        """
        save_path = path or self.config_path
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f, indent=2)

    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """
        Update nested dictionary recursively.

        Args:
            d: Dictionary to update
            u: Dictionary with new values

        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d

    def configure_auth_mode(self, mode: str, **kwargs) -> None:
        """
        Configure authentication mode.

        Args:
            mode: Authentication mode (none, api_key, jwt, certificate, basic)
            **kwargs: Additional configuration parameters
        """
        self.set("auth.method", mode)
        
        if mode == "api_key":
            if "key" in kwargs:
                self.set("auth.api_key.key", kwargs["key"])
            if "header" in kwargs:
                self.set("auth.api_key.header", kwargs["header"])
        elif mode == "jwt":
            if "username" in kwargs:
                self.set("auth.jwt.username", kwargs["username"])
            if "password" in kwargs:
                self.set("auth.jwt.password", kwargs["password"])
            if "secret" in kwargs:
                self.set("auth.jwt.secret", kwargs["secret"])
            if "expiry_hours" in kwargs:
                self.set("auth.jwt.expiry_hours", kwargs["expiry_hours"])
        elif mode == "certificate":
            self.set("auth.certificate.enabled", True)
            if "cert_file" in kwargs:
                self.set("auth.certificate.cert_file", kwargs["cert_file"])
            if "key_file" in kwargs:
                self.set("auth.certificate.key_file", kwargs["key_file"])
            if "ca_cert_file" in kwargs:
                self.set("auth.certificate.ca_cert_file", kwargs["ca_cert_file"])
        elif mode == "basic":
            if "username" in kwargs:
                self.set("auth.basic.username", kwargs["username"])
            if "password" in kwargs:
                self.set("auth.basic.password", kwargs["password"])

    def configure_ssl(self, enabled: bool = True, **kwargs) -> None:
        """
        Configure SSL/TLS settings.

        Args:
            enabled: Enable SSL/TLS
            **kwargs: Additional SSL configuration parameters
        """
        self.set("ssl.enabled", enabled)
        
        if "verify" in kwargs:
            self.set("ssl.verify", kwargs["verify"])
        if "check_hostname" in kwargs:
            self.set("ssl.check_hostname", kwargs["check_hostname"])
        if "cert_file" in kwargs:
            self.set("ssl.cert_file", kwargs["cert_file"])
        if "key_file" in kwargs:
            self.set("ssl.key_file", kwargs["key_file"])
        if "ca_cert_file" in kwargs:
            self.set("ssl.ca_cert_file", kwargs["ca_cert_file"])
        if "client_cert_required" in kwargs:
            self.set("ssl.client_cert_required", kwargs["client_cert_required"])

    def configure_server(self, host: str, port: int, base_url: Optional[str] = None) -> None:
        """
        Configure server connection settings.

        Args:
            host: Server host
            port: Server port
            base_url: Full server URL (optional, will be constructed if not provided)
        """
        self.set("server.host", host)
        self.set("server.port", port)
        
        if base_url:
            self.set("server.base_url", base_url)
        else:
            protocol = "https" if self.get("ssl.enabled", False) else "http"
            self.set("server.base_url", f"{protocol}://{host}:{port}")

    def get_server_url(self) -> str:
        """
        Get the complete server URL.

        Returns:
            Server URL string
        """
        return self.get("server.base_url", "http://localhost:8001")

    def get_auth_method(self) -> str:
        """
        Get the authentication method.

        Returns:
            Authentication method string
        """
        return self.get("auth.method", "none")

    def is_ssl_enabled(self) -> bool:
        """
        Check if SSL/TLS is enabled.

        Returns:
            True if SSL is enabled, False otherwise
        """
        return self.get("ssl.enabled", False)

    def is_auth_enabled(self) -> bool:
        """
        Check if authentication is enabled.

        Returns:
            True if authentication is enabled, False otherwise
        """
        return self.get("auth.method", "none") != "none"

    def is_security_enabled(self) -> bool:
        """
        Check if security features are enabled.

        Returns:
            True if security is enabled, False otherwise
        """
        return self.get("security.enabled", False)

    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate server configuration
        host = self.get("server.host")
        port = self.get("server.port")
        if not host:
            errors.append("Server host is required")
        if not port or not isinstance(port, int) or port <= 0:
            errors.append("Server port must be a positive integer")
        
        # Validate authentication configuration
        auth_method = self.get("auth.method", "none")
        if auth_method == "api_key":
            if not self.get("auth.api_key.key"):
                errors.append("API key is required for api_key authentication")
        elif auth_method == "jwt":
            if not all([self.get("auth.jwt.username"), 
                       self.get("auth.jwt.password"), 
                       self.get("auth.jwt.secret")]):
                errors.append("Username, password, and secret are required for JWT authentication")
        elif auth_method == "certificate":
            if not all([self.get("auth.certificate.cert_file"), 
                       self.get("auth.certificate.key_file")]):
                errors.append("Certificate and key files are required for certificate authentication")
        elif auth_method == "basic":
            if not all([self.get("auth.basic.username"), 
                       self.get("auth.basic.password")]):
                errors.append("Username and password are required for basic authentication")
        
        # Validate SSL configuration
        if self.get("ssl.enabled", False):
            if self.get("ssl.cert_file") and not os.path.exists(self.get("ssl.cert_file")):
                errors.append(f"SSL certificate file not found: {self.get('ssl.cert_file')}")
            if self.get("ssl.key_file") and not os.path.exists(self.get("ssl.key_file")):
                errors.append(f"SSL key file not found: {self.get('ssl.key_file')}")
            if self.get("ssl.ca_cert_file") and not os.path.exists(self.get("ssl.ca_cert_file")):
                errors.append(f"SSL CA certificate file not found: {self.get('ssl.ca_cert_file')}")
        
        return errors

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
        minimal_config["auth"]["method"] = "none"
        minimal_config["logging"]["enabled"] = False
        
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
        secure_config["auth"]["method"] = "certificate"
        secure_config["ssl"]["verify"] = True
        secure_config["ssl"]["check_hostname"] = True
        secure_config["ssl"]["client_cert_required"] = True
        
        return secure_config

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ClientConfig':
        """
        Create ClientConfig instance from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.config_data = config._update_nested_dict(config.config_data, config_dict)
        return config

    @classmethod
    def from_file(cls, config_path: str) -> 'ClientConfig':
        """
        Create ClientConfig instance from file.

        Args:
            config_path: Path to configuration file

        Returns:
            ClientConfig instance
        """
        config = cls(config_path)
        return config

    @classmethod
    def create_http_config(cls, host: str = "localhost", port: int = 8001) -> 'ClientConfig':
        """
        Create configuration for HTTP connection without authentication.

        Args:
            host: Server host
            port: Server port

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.configure_server(host, port)
        config.configure_auth_mode("none")
        config.configure_ssl(False)
        return config

    @classmethod
    def create_http_token_config(cls, host: str = "localhost", port: int = 8001, 
                                api_key: str = None) -> 'ClientConfig':
        """
        Create configuration for HTTP connection with API key authentication.

        Args:
            host: Server host
            port: Server port
            api_key: API key for authentication

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.configure_server(host, port)
        config.configure_auth_mode("api_key", key=api_key)
        config.configure_ssl(False)
        return config

    @classmethod
    def create_https_config(cls, host: str = "localhost", port: int = 8443,
                           cert_file: str = None, key_file: str = None,
                           ca_cert_file: str = None) -> 'ClientConfig':
        """
        Create configuration for HTTPS connection without authentication.

        Args:
            host: Server host
            port: Server port
            cert_file: Client certificate file
            key_file: Client key file
            ca_cert_file: CA certificate file

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.configure_ssl(True, cert_file=cert_file, key_file=key_file, 
                           ca_cert_file=ca_cert_file)
        config.configure_server(host, port)
        config.configure_auth_mode("none")
        return config

    @classmethod
    def create_https_token_config(cls, host: str = "localhost", port: int = 8443,
                                 api_key: str = None, cert_file: str = None,
                                 key_file: str = None, ca_cert_file: str = None) -> 'ClientConfig':
        """
        Create configuration for HTTPS connection with API key authentication.

        Args:
            host: Server host
            port: Server port
            api_key: API key for authentication
            cert_file: Client certificate file
            key_file: Client key file
            ca_cert_file: CA certificate file

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.configure_ssl(True, cert_file=cert_file, key_file=key_file,
                           ca_cert_file=ca_cert_file)
        config.configure_server(host, port)
        config.configure_auth_mode("api_key", key=api_key)
        return config

    @classmethod
    def create_mtls_config(cls, host: str = "localhost", port: int = 8443,
                          cert_file: str = None, key_file: str = None,
                          ca_cert_file: str = None) -> 'ClientConfig':
        """
        Create configuration for mTLS connection with client certificates.

        Args:
            host: Server host
            port: Server port
            cert_file: Client certificate file
            key_file: Client key file
            ca_cert_file: CA certificate file

        Returns:
            ClientConfig instance
        """
        config = cls()
        config.configure_ssl(True, cert_file=cert_file, key_file=key_file,
                           ca_cert_file=ca_cert_file, client_cert_required=True)
        config.configure_server(host, port)
        config.configure_auth_mode("certificate", cert_file=cert_file, 
                                 key_file=key_file, ca_cert_file=ca_cert_file)
        return config


# Singleton instance
config = ClientConfig()
