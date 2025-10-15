"""
SSL/TLS examples for embed-client.

This module provides examples of how to use the SSL/TLS manager
with different security modes and configurations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any
from embed_client.ssl_manager import ClientSSLManager, create_ssl_manager, create_ssl_context, create_connector


def get_http_config() -> Dict[str, Any]:
    """
    Get example configuration for HTTP (no SSL).
    
    Returns:
        Configuration dictionary for HTTP
    """
    return {
        "ssl": {
            "enabled": False
        }
    }


def get_https_config() -> Dict[str, Any]:
    """
    Get example configuration for HTTPS.
    
    Returns:
        Configuration dictionary for HTTPS
    """
    return {
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True
        }
    }


def get_https_with_ca_config() -> Dict[str, Any]:
    """
    Get example configuration for HTTPS with custom CA.
    
    Returns:
        Configuration dictionary for HTTPS with CA
    """
    return {
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True,
            "ca_cert_file": "certs/ca.crt"
        }
    }


def get_mtls_config() -> Dict[str, Any]:
    """
    Get example configuration for mTLS (mutual TLS).
    
    Returns:
        Configuration dictionary for mTLS
    """
    return {
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "check_expiry": True,
            "cert_file": "certs/client.crt",
            "key_file": "keys/client.key",
            "ca_cert_file": "certs/ca.crt"
        }
    }


def get_mtls_no_verify_config() -> Dict[str, Any]:
    """
    Get example configuration for mTLS without verification.
    
    Returns:
        Configuration dictionary for mTLS without verification
    """
    return {
        "ssl": {
            "enabled": True,
            "verify_mode": "CERT_NONE",
            "check_hostname": False,
            "check_expiry": False,
            "cert_file": "certs/client.crt",
            "key_file": "keys/client.key"
        }
    }


def demo_http_ssl():
    """Demonstrate HTTP SSL configuration (disabled)."""
    print("=== HTTP SSL Configuration Demo ===")
    
    config = get_http_config()
    ssl_manager = create_ssl_manager(config)
    
    print(f"SSL enabled: {ssl_manager.is_ssl_enabled()}")
    print(f"mTLS enabled: {ssl_manager.is_mtls_enabled()}")
    
    # Create SSL context
    context = ssl_manager.create_client_ssl_context()
    print(f"SSL context: {context}")
    
    # Create connector
    connector = ssl_manager.create_connector()
    print(f"Connector: {connector}")
    
    # Validate configuration
    errors = ssl_manager.validate_ssl_config()
    print(f"Validation errors: {errors}")


def demo_https_ssl():
    """Demonstrate HTTPS SSL configuration."""
    print("\n=== HTTPS SSL Configuration Demo ===")
    
    config = get_https_config()
    ssl_manager = create_ssl_manager(config)
    
    print(f"SSL enabled: {ssl_manager.is_ssl_enabled()}")
    print(f"mTLS enabled: {ssl_manager.is_mtls_enabled()}")
    
    # Create SSL context
    context = ssl_manager.create_client_ssl_context()
    print(f"SSL context: {context}")
    if context:
        print(f"  Verify mode: {context.verify_mode}")
        print(f"  Check hostname: {context.check_hostname}")
    
    # Create connector
    connector = ssl_manager.create_connector()
    print(f"Connector: {connector}")
    
    # Get supported protocols
    protocols = ssl_manager.get_supported_protocols()
    print(f"Supported protocols: {protocols}")
    
    # Validate configuration
    errors = ssl_manager.validate_ssl_config()
    print(f"Validation errors: {errors}")


def demo_https_with_ca_ssl():
    """Demonstrate HTTPS SSL configuration with custom CA."""
    print("\n=== HTTPS with CA SSL Configuration Demo ===")
    
    config = get_https_with_ca_config()
    ssl_manager = create_ssl_manager(config)
    
    print(f"SSL enabled: {ssl_manager.is_ssl_enabled()}")
    print(f"mTLS enabled: {ssl_manager.is_mtls_enabled()}")
    
    # Create SSL context
    context = ssl_manager.create_client_ssl_context()
    print(f"SSL context: {context}")
    if context:
        print(f"  Verify mode: {context.verify_mode}")
        print(f"  Check hostname: {context.check_hostname}")
    
    # Validate configuration
    errors = ssl_manager.validate_ssl_config()
    print(f"Validation errors: {errors}")


def demo_mtls_ssl():
    """Demonstrate mTLS SSL configuration."""
    print("\n=== mTLS SSL Configuration Demo ===")
    
    config = get_mtls_config()
    ssl_manager = create_ssl_manager(config)
    
    print(f"SSL enabled: {ssl_manager.is_ssl_enabled()}")
    print(f"mTLS enabled: {ssl_manager.is_mtls_enabled()}")
    
    # Create SSL context
    context = ssl_manager.create_client_ssl_context()
    print(f"SSL context: {context}")
    if context:
        print(f"  Verify mode: {context.verify_mode}")
        print(f"  Check hostname: {context.check_hostname}")
    
    # Validate configuration
    errors = ssl_manager.validate_ssl_config()
    print(f"Validation errors: {errors}")


def demo_mtls_no_verify_ssl():
    """Demonstrate mTLS SSL configuration without verification."""
    print("\n=== mTLS without Verification SSL Configuration Demo ===")
    
    config = get_mtls_no_verify_config()
    ssl_manager = create_ssl_manager(config)
    
    print(f"SSL enabled: {ssl_manager.is_ssl_enabled()}")
    print(f"mTLS enabled: {ssl_manager.is_mtls_enabled()}")
    
    # Create SSL context
    context = ssl_manager.create_client_ssl_context()
    print(f"SSL context: {context}")
    if context:
        print(f"  Verify mode: {context.verify_mode}")
        print(f"  Check hostname: {context.check_hostname}")
    
    # Validate configuration
    errors = ssl_manager.validate_ssl_config()
    print(f"Validation errors: {errors}")


def demo_certificate_validation():
    """Demonstrate certificate validation."""
    print("\n=== Certificate Validation Demo ===")
    
    config = {"ssl": {"enabled": True}}
    ssl_manager = create_ssl_manager(config)
    
    # Test with non-existent certificate
    result = ssl_manager.validate_certificate("nonexistent.crt")
    print(f"Non-existent certificate validation: {result}")
    
    # Test with invalid certificate
    result = ssl_manager.validate_certificate("invalid.crt")
    print(f"Invalid certificate validation: {result}")


def demo_ssl_context_creation():
    """Demonstrate SSL context creation using factory functions."""
    print("\n=== SSL Context Creation Demo ===")
    
    # HTTP (no SSL)
    config = get_http_config()
    context = create_ssl_context(config)
    print(f"HTTP SSL context: {context}")
    
    # HTTPS
    config = get_https_config()
    context = create_ssl_context(config)
    print(f"HTTPS SSL context: {context}")
    
    # mTLS
    config = get_mtls_config()
    context = create_ssl_context(config)
    print(f"mTLS SSL context: {context}")


def demo_connector_creation():
    """Demonstrate connector creation using factory functions."""
    print("\n=== Connector Creation Demo ===")
    
    # HTTP (no SSL)
    config = get_http_config()
    connector = create_connector(config)
    print(f"HTTP connector: {connector}")
    
    # HTTPS
    config = get_https_config()
    connector = create_connector(config)
    print(f"HTTPS connector: {connector}")
    
    # mTLS
    config = get_mtls_config()
    connector = create_connector(config)
    print(f"mTLS connector: {connector}")


def demo_ssl_configuration_validation():
    """Demonstrate SSL configuration validation."""
    print("\n=== SSL Configuration Validation Demo ===")
    
    # Valid configuration
    config = get_http_config()
    ssl_manager = create_ssl_manager(config)
    errors = ssl_manager.validate_ssl_config()
    print(f"Valid config errors: {errors}")
    
    # Invalid configuration (missing files)
    config = get_mtls_config()
    ssl_manager = create_ssl_manager(config)
    errors = ssl_manager.validate_ssl_config()
    print(f"Invalid config errors: {errors}")


def demo_ssl_capabilities():
    """Demonstrate SSL capabilities detection."""
    print("\n=== SSL Capabilities Demo ===")
    
    config = {"ssl": {"enabled": True}}
    ssl_manager = create_ssl_manager(config)
    
    protocols = ssl_manager.get_supported_protocols()
    print(f"Supported protocols: {protocols}")
    
    ssl_config = ssl_manager.get_ssl_config()
    print(f"SSL configuration: {ssl_config}")


def run_all_demos():
    """Run all SSL/TLS demos."""
    print("🔒 SSL/TLS Manager Examples")
    print("=" * 50)
    
    demo_http_ssl()
    demo_https_ssl()
    demo_https_with_ca_ssl()
    demo_mtls_ssl()
    demo_mtls_no_verify_ssl()
    demo_certificate_validation()
    demo_ssl_context_creation()
    demo_connector_creation()
    demo_ssl_configuration_validation()
    demo_ssl_capabilities()
    
    print("\n✅ All SSL/TLS demos completed!")


if __name__ == "__main__":
    run_all_demos()
