"""
SSL/TLS Manager for embed-client.

This module provides SSL/TLS management for the embed-client, supporting
all security modes including HTTP, HTTPS, and mTLS. It integrates with
mcp_security_framework when available and provides fallback implementations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
import ssl
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import mcp_security_framework components
try:
    from mcp_security_framework import (
        SSLConfig,
        CertificateInfo,
        SecurityManager
    )
    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    print("Warning: mcp_security_framework not available. Using fallback SSL/TLS management.")

# Fallback certificate handling
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("Warning: cryptography not available. Limited SSL/TLS functionality.")


class SSLManagerError(Exception):
    """Raised when SSL/TLS operations fail."""
    
    def __init__(self, message: str, error_code: int = -32002):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ClientSSLManager:
    """
    Client SSL/TLS Manager.
    
    This class provides SSL/TLS management for the embed-client,
    supporting all security modes with integration to
    mcp_security_framework when available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SSL/TLS manager.
        
        Args:
            config: SSL/TLS configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize security framework components if available
        self.ssl_manager = None
        self.cert_manager = None
        
        if SECURITY_FRAMEWORK_AVAILABLE:
            self._initialize_security_framework()
        else:
            self.logger.warning("mcp_security_framework not available, using fallback SSL/TLS management")
    
    def _initialize_security_framework(self) -> None:
        """Initialize mcp_security_framework components."""
        try:
            # Create SSL config
            ssl_config_dict = self.config.get("ssl", {})
            
            # ✅ ИСПРАВЛЕНИЕ: Учитывать verify: false в mcp_security_framework
            verify_mode = ssl_config_dict.get("verify_mode", "CERT_REQUIRED")
            if ssl_config_dict.get("verify", True) == False:
                verify_mode = "CERT_NONE"
            
            ssl_config = SSLConfig(
                enabled=ssl_config_dict.get("enabled", False),
                cert_file=ssl_config_dict.get("cert_file") if ssl_config_dict.get("cert_file") and os.path.exists(ssl_config_dict.get("cert_file")) else None,
                key_file=ssl_config_dict.get("key_file") if ssl_config_dict.get("key_file") and os.path.exists(ssl_config_dict.get("key_file")) else None,
                ca_cert_file=ssl_config_dict.get("ca_cert_file") if ssl_config_dict.get("ca_cert_file") and os.path.exists(ssl_config_dict.get("ca_cert_file")) else None,
                # ✅ ИСПРАВЛЕНИЕ: Правильно мапить клиентские сертификаты для mTLS
                client_cert_file=ssl_config_dict.get("cert_file") if ssl_config_dict.get("cert_file") and os.path.exists(ssl_config_dict.get("cert_file")) else None,
                client_key_file=ssl_config_dict.get("key_file") if ssl_config_dict.get("key_file") and os.path.exists(ssl_config_dict.get("key_file")) else None,
                verify_mode=verify_mode,  # ✅ ИСПРАВЛЕНИЕ: Использовать правильный verify_mode
                check_hostname=ssl_config_dict.get("check_hostname", True),
                check_expiry=ssl_config_dict.get("check_expiry", True)
            )
            
            # Create permission config (required by SecurityManager)
            from mcp_security_framework import PermissionConfig
            permission_config = PermissionConfig(
                enabled=False,
                roles_file="configs/roles.json"
            )
            
            # Create security config
            from mcp_security_framework import SecurityConfig
            security_config = SecurityConfig(
                ssl=ssl_config,
                permissions=permission_config
            )
            
            # Initialize managers
            self.ssl_manager = SecurityManager(security_config)
            
            self.logger.info("Security framework SSL/TLS components initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize security framework SSL/TLS: {e}")
            self.ssl_manager = None
            self.cert_manager = None
    
    def create_client_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for client connections.
        
        Returns:
            SSL context for client connections or None if SSL is disabled
        """
        # Check if SSL is enabled first
        if not self.is_ssl_enabled():
            return None
            
        try:
            # ✅ ИСПРАВЛЕНИЕ: Использовать SecurityManager правильно
            if self.ssl_manager and hasattr(self.ssl_manager, 'create_ssl_context'):
                # ✅ ИСПРАВЛЕНИЕ: Передаем клиентские сертификаты явно для mTLS
                ssl_config = self.config.get("ssl", {})
                return self.ssl_manager.create_ssl_context(
                    context_type="client",
                    client_cert_file=ssl_config.get("cert_file"),
                    client_key_file=ssl_config.get("key_file"),
                    ca_cert_file=ssl_config.get("ca_cert_file"),
                    verify_mode=ssl_config.get("verify_mode", "CERT_NONE") if ssl_config.get("verify", True) == False else "CERT_REQUIRED"
                )
            else:
                # Fallback если SecurityManager недоступен
                return self._create_client_ssl_context_fallback()
                
        except Exception as e:
            self.logger.error(f"Failed to create client SSL context: {e}")
            raise SSLManagerError(f"Failed to create client SSL context: {e}")
    
    def _create_client_ssl_context_fallback(self) -> Optional[ssl.SSLContext]:
        """Fallback SSL context creation."""
        ssl_config = self.config.get("ssl", {})
        
        if not ssl_config.get("enabled", False):
            return None
        
        try:
            # ✅ ИСПРАВЛЕНИЕ: Обработать verify: false
            verify_mode = ssl_config.get("verify_mode", "CERT_REQUIRED")
            if ssl_config.get("verify", True) == False:
                verify_mode = "CERT_NONE"
            
            check_hostname = ssl_config.get("check_hostname", True)
            
            # Force check_hostname=False for CERT_NONE mode
            if verify_mode == "CERT_NONE":
                check_hostname = False
            
            # Create SSL context based on verification mode
            if verify_mode == "CERT_NONE":
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                # ✅ ИСПРАВЛЕНИЕ: При CERT_NONE не загружаем сертификаты для верификации
                # Но можем загрузить клиентские сертификаты для mTLS аутентификации
                cert_file = ssl_config.get("cert_file")
                key_file = ssl_config.get("key_file")
                if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
                    context.load_cert_chain(cert_file, key_file)
                return context
            else:
                context = ssl.create_default_context()
                context.check_hostname = check_hostname
                if verify_mode == "CERT_OPTIONAL":
                    context.verify_mode = ssl.CERT_OPTIONAL
                else:  # CERT_REQUIRED
                    context.verify_mode = ssl.CERT_REQUIRED
                
                # Load CA certificate if provided (только при верификации)
                ca_cert_file = ssl_config.get("ca_cert_file")
                if ca_cert_file and os.path.exists(ca_cert_file):
                    context.load_verify_locations(ca_cert_file)
                
                # Load client certificate if provided (for mTLS)
                cert_file = ssl_config.get("cert_file")
                key_file = ssl_config.get("key_file")
                if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
                    context.load_cert_chain(cert_file, key_file)
                
                return context
            
        except Exception as e:
            raise SSLManagerError(f"Failed to create SSL context: {e}")
    
    def create_connector(self) -> Optional[Any]:
        """
        Create aiohttp connector with SSL context.
        
        Returns:
            aiohttp connector with SSL context or None if SSL is disabled
        """
        try:
            import aiohttp
            
            ssl_context = self.create_client_ssl_context()
            if ssl_context is None:
                return None
            
            return aiohttp.TCPConnector(ssl=ssl_context)
            
        except ImportError:
            self.logger.error("aiohttp not available for connector creation")
            return None
        except Exception as e:
            self.logger.error(f"Failed to create connector: {e}")
            return None
    
    def validate_certificate(self, cert_file: str) -> Dict[str, Any]:
        """
        Validate certificate file.
        
        Args:
            cert_file: Path to certificate file
            
        Returns:
            Dictionary with validation results
        """
        try:
            if self.ssl_manager and CRYPTOGRAPHY_AVAILABLE:
                # Use security framework
                cert_info = extract_certificate_info(cert_file)
                return {
                    "valid": True,
                    "subject": str(cert_info.subject),
                    "issuer": str(cert_info.issuer),
                    "not_valid_before": cert_info.not_valid_before.isoformat(),
                    "not_valid_after": cert_info.not_valid_after.isoformat(),
                    "serial_number": str(cert_info.serial_number),
                    "is_self_signed": is_certificate_self_signed(cert_file)
                }
            else:
                # Fallback implementation
                return self._validate_certificate_fallback(cert_file)
                
        except Exception as e:
            self.logger.error(f"Certificate validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _validate_certificate_fallback(self, cert_file: str) -> Dict[str, Any]:
        """Fallback certificate validation."""
        if not CRYPTOGRAPHY_AVAILABLE:
            return {
                "valid": False,
                "error": "cryptography not available for certificate validation"
            }
        
        try:
            if not os.path.exists(cert_file):
                return {
                    "valid": False,
                    "error": "Certificate file not found"
                }
            
            # Basic file existence and readability check
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            
            # Try to parse certificate
            cert = x509.load_pem_x509_certificate(cert_data)
            
            return {
                "valid": True,
                "subject": str(cert.subject),
                "issuer": str(cert.issuer),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "serial_number": str(cert.serial_number)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Certificate validation failed: {e}"
            }
    
    def get_ssl_config(self) -> Dict[str, Any]:
        """
        Get current SSL configuration.
        
        Returns:
            Dictionary with SSL configuration
        """
        return self.config.get("ssl", {})
    
    def is_ssl_enabled(self) -> bool:
        """
        Check if SSL/TLS is enabled.
        
        Returns:
            True if SSL/TLS is enabled, False otherwise
        """
        return self.config.get("ssl", {}).get("enabled", False)
    
    def is_mtls_enabled(self) -> bool:
        """
        Check if mTLS (mutual TLS) is enabled.
        
        Returns:
            True if mTLS is enabled, False otherwise
        """
        ssl_config = self.config.get("ssl", {})
        return (ssl_config.get("enabled", False) and 
                bool(ssl_config.get("cert_file")) and 
                bool(ssl_config.get("key_file")))
    
    def get_certificate_info(self, cert_file: str) -> Optional[Dict[str, Any]]:
        """
        Get certificate information.
        
        Args:
            cert_file: Path to certificate file
            
        Returns:
            Dictionary with certificate information or None if not available
        """
        try:
            if self.ssl_manager and CRYPTOGRAPHY_AVAILABLE:
                # Use security framework
                cert_info = extract_certificate_info(cert_file)
                return {
                    "subject": str(cert_info.subject),
                    "issuer": str(cert_info.issuer),
                    "not_valid_before": cert_info.not_valid_before.isoformat(),
                    "not_valid_after": cert_info.not_valid_after.isoformat(),
                    "serial_number": str(cert_info.serial_number),
                    "version": cert_info.version,
                    "signature_algorithm": str(cert_info.signature_algorithm_oid),
                    "is_self_signed": is_certificate_self_signed(cert_file)
                }
            else:
                # Fallback implementation
                return self._get_certificate_info_fallback(cert_file)
                
        except Exception as e:
            self.logger.error(f"Failed to get certificate info: {e}")
            return None
    
    def _get_certificate_info_fallback(self, cert_file: str) -> Optional[Dict[str, Any]]:
        """Fallback certificate info extraction."""
        if not CRYPTOGRAPHY_AVAILABLE:
            return None
        
        try:
            if not os.path.exists(cert_file):
                return None
            
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data)
            
            return {
                "subject": str(cert.subject),
                "issuer": str(cert.issuer),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "serial_number": str(cert.serial_number),
                "version": cert.version.name,
                "signature_algorithm": str(cert.signature_algorithm_oid)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract certificate info: {e}")
            return None
    
    def validate_ssl_config(self) -> List[str]:
        """
        Validate SSL configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        ssl_config = self.config.get("ssl", {})
        
        if not ssl_config.get("enabled", False):
            return errors  # SSL disabled, no validation needed
        
        # Check certificate files if mTLS is configured
        cert_file = ssl_config.get("cert_file")
        key_file = ssl_config.get("key_file")
        
        if cert_file and not os.path.exists(cert_file):
            errors.append(f"Certificate file not found: {cert_file}")
        
        if key_file and not os.path.exists(key_file):
            errors.append(f"Key file not found: {key_file}")
        
        # Check CA certificate if provided
        ca_cert_file = ssl_config.get("ca_cert_file")
        if ca_cert_file and not os.path.exists(ca_cert_file):
            errors.append(f"CA certificate file not found: {ca_cert_file}")
        
        # Validate certificate if provided
        if cert_file and os.path.exists(cert_file):
            validation_result = self.validate_certificate(cert_file)
            if not validation_result.get("valid", False):
                errors.append(f"Certificate validation failed: {validation_result.get('error', 'Unknown error')}")
        
        return errors
    
    def get_supported_protocols(self) -> List[str]:
        """
        Get list of supported SSL/TLS protocols.
        
        Returns:
            List of supported protocol names
        """
        protocols = []
        
        try:
            # Check available protocols
            if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
                protocols.append("TLSv1.2")
            if hasattr(ssl, 'PROTOCOL_TLSv1_3'):
                protocols.append("TLSv1.3")
            if hasattr(ssl, 'PROTOCOL_TLS'):
                protocols.append("TLS")
            
            # Fallback to basic protocols
            if not protocols:
                protocols = ["SSLv23", "TLS"]
                
        except Exception as e:
            self.logger.warning(f"Failed to detect supported protocols: {e}")
            protocols = ["TLS"]  # Basic fallback
        
        return protocols


def create_ssl_manager(config: Dict[str, Any]) -> ClientSSLManager:
    """
    Create SSL/TLS manager from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        ClientSSLManager instance
    """
    return ClientSSLManager(config)


def create_ssl_context(config: Dict[str, Any]) -> Optional[ssl.SSLContext]:
    """
    Create SSL context from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        SSL context or None if SSL is disabled
    """
    ssl_manager = ClientSSLManager(config)
    return ssl_manager.create_client_ssl_context()


def create_connector(config: Dict[str, Any]) -> Optional[Any]:
    """
    Create aiohttp connector from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        aiohttp connector or None if SSL is disabled
    """
    ssl_manager = ClientSSLManager(config)
    return ssl_manager.create_connector()
