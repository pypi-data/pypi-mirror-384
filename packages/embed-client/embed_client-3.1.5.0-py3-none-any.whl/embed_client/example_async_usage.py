"""
Example usage of EmbeddingServiceAsyncClient with all security modes and ClientFactory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This example demonstrates all 6 security modes supported by the embed-client:
1. HTTP (plain HTTP without authentication)
2. HTTP + Token (HTTP with API key authentication)
3. HTTPS (HTTPS with server certificate verification)
4. HTTPS + Token (HTTPS with server certificates + authentication)
5. mTLS (mutual TLS with client and server certificates)
6. mTLS + Roles (mTLS with role-based access control)

USAGE:
    # Basic usage without authentication
    python embed_client/example_async_usage.py --base-url http://localhost --port 8001
    
    # With API key authentication
    python embed_client/example_async_usage.py --base-url http://localhost --port 8001 --auth-method api_key --api-key your_key
    
    # With JWT authentication
    python embed_client/example_async_usage.py --base-url http://localhost --port 8001 --auth-method jwt --jwt-secret secret --jwt-username user
    
    # With basic authentication
    python embed_client/example_async_usage.py --base-url http://localhost --port 8001 --auth-method basic --username user --password pass
    
    # With configuration file
    python embed_client/example_async_usage.py --config configs/http_token.json
    
    # With environment variables
    export EMBED_CLIENT_BASE_URL=http://localhost
    export EMBED_CLIENT_PORT=8001
    export EMBED_CLIENT_AUTH_METHOD=api_key
    export EMBED_CLIENT_API_KEY=your_key
    python embed_client/example_async_usage.py

SECURITY MODES EXAMPLES:
    # 1. HTTP - plain HTTP without authentication
    python embed_client/example_async_usage.py --base-url http://localhost --port 8001
    
    # 2. HTTP + Token - HTTP with API key authentication
    python embed_client/example_async_usage.py --base-url http://localhost --port 8001 --auth-method api_key --api-key admin_key_123
    
    # 3. HTTPS - HTTPS with server certificate verification
    python embed_client/example_async_usage.py --base-url https://localhost --port 9443
    
    # 4. HTTPS + Token - HTTPS with server certificates + authentication
    python embed_client/example_async_usage.py --base-url https://localhost --port 9443 --auth-method jwt --jwt-secret secret --jwt-username admin
    
    # 5. mTLS - mutual TLS with client and server certificates
    python embed_client/example_async_usage.py --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key
    
    # 6. mTLS + Roles - mTLS with role-based access control
    python embed_client/example_async_usage.py --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key --roles admin,user

CLIENT FACTORY EXAMPLES:
    # Automatic security mode detection
    python embed_client/example_async_usage.py --factory-mode auto --base-url https://localhost --port 9443 --auth-method api_key --api-key key
    
    # Specific security mode creation
    python embed_client/example_async_usage.py --factory-mode https_token --base-url https://localhost --port 9443 --auth-method basic --username user --password pass
    
    # mTLS with factory
    python embed_client/example_async_usage.py --factory-mode mtls --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key

SSL/TLS EXAMPLES:
    # HTTPS with SSL verification disabled
    python embed_client/example_async_usage.py --base-url https://localhost --port 9443 --ssl-verify-mode CERT_NONE
    
    # mTLS with custom CA certificate
    python embed_client/example_async_usage.py --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key --ca-cert-file mtls_certificates/ca/ca.crt
    
    # HTTPS with custom SSL settings
    python embed_client/example_async_usage.py --base-url https://localhost --port 9443 --ssl-verify-mode CERT_REQUIRED --ssl-check-hostname --ssl-check-expiry

CONFIGURATION EXAMPLES:
    # Using configuration file
    python embed_client/example_async_usage.py --config configs/https_token.json
    
    # Using environment variables
    export EMBED_CLIENT_BASE_URL=https://secure.example.com
    export EMBED_CLIENT_PORT=9443
    export EMBED_CLIENT_AUTH_METHOD=api_key
    export EMBED_CLIENT_API_KEY=production_key
    python embed_client/example_async_usage.py

DEMO MODE:
    # Show all security modes demonstration
    python embed_client/example_async_usage.py --demo-mode

PROGRAMMATIC USAGE EXAMPLES:
    import asyncio
    from embed_client.async_client import EmbeddingServiceAsyncClient
    from embed_client.config import ClientConfig
    from embed_client.client_factory import ClientFactory, create_client
    
    async def main():
        # Method 1: Direct client creation
        client = EmbeddingServiceAsyncClient('http://localhost', 8001)
        await client.close()
        
        # Method 2: Using configuration
        config = ClientConfig()
        config.configure_server('http://localhost', 8001)
        client = EmbeddingServiceAsyncClient.from_config(config)
        await client.close()
        
        # Method 3: Using factory with automatic detection
        client = create_client('https://localhost', 9443, auth_method='api_key', api_key='key')
        await client.close()
        
        # Method 4: Using specific factory method
        client = ClientFactory.create_https_token_client(
            'https://localhost', 9443, 'api_key', api_key='key'
        )
        await client.close()
        
        # Method 5: Using with_auth method for dynamic authentication
        client = EmbeddingServiceAsyncClient('http://localhost', 8001)
        client = client.with_auth('api_key', api_key='dynamic_key')
        await client.close()
    
    asyncio.run(main())
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional, Union

from embed_client.async_client import EmbeddingServiceAsyncClient, EmbeddingServiceError, EmbeddingServiceConfigError
from embed_client.config import ClientConfig
from embed_client.client_factory import (
    ClientFactory, SecurityMode, create_client, create_client_from_config,
    create_client_from_env, detect_security_mode
)


def get_params():
    """Parse command line arguments and environment variables for client configuration."""
    parser = argparse.ArgumentParser(description="Embedding Service Async Client Example - All Security Modes")
    
    # Basic connection parameters
    parser.add_argument("--base-url", "-b", help="Base URL of the embedding service")
    parser.add_argument("--port", "-p", type=int, help="Port of the embedding service")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    
    # Client factory mode
    parser.add_argument("--factory-mode", choices=["auto", "http", "http_token", "https", "https_token", "mtls", "mtls_roles"],
                       default="auto", help="Client factory mode (auto for automatic detection)")
    
    # Authentication parameters
    parser.add_argument("--auth-method", choices=["none", "api_key", "jwt", "basic", "certificate"], 
                       default="none", help="Authentication method")
    parser.add_argument("--api-key", help="API key for api_key authentication")
    parser.add_argument("--jwt-secret", help="JWT secret for jwt authentication")
    parser.add_argument("--jwt-username", help="JWT username for jwt authentication")
    parser.add_argument("--jwt-password", help="JWT password for jwt authentication")
    parser.add_argument("--username", help="Username for basic authentication")
    parser.add_argument("--password", help="Password for basic authentication")
    parser.add_argument("--cert-file", help="Certificate file for certificate authentication")
    parser.add_argument("--key-file", help="Key file for certificate authentication")
    
    # SSL/TLS parameters
    parser.add_argument("--ssl-verify-mode", choices=["CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED"], 
                       default="CERT_REQUIRED", help="SSL certificate verification mode")
    parser.add_argument("--ssl-check-hostname", action="store_true", default=True, 
                       help="Enable SSL hostname checking")
    parser.add_argument("--ssl-check-expiry", action="store_true", default=True, 
                       help="Enable SSL certificate expiry checking")
    parser.add_argument("--ca-cert-file", help="CA certificate file for SSL verification")
    
    # Role-based access control (for mTLS + Roles)
    parser.add_argument("--roles", help="Comma-separated list of roles for mTLS + Roles mode")
    parser.add_argument("--role-attributes", help="JSON string of role attributes for mTLS + Roles mode")
    
    # Additional parameters
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    parser.add_argument("--demo-mode", action="store_true", help="Run in demo mode (show all security modes)")
    
    args = parser.parse_args()
    
    # Store demo_mode in args for later use
    args.demo_mode = args.demo_mode
    
    # If demo mode is requested, return args directly
    if args.demo_mode:
        return args
    
    # If config file is provided, load it
    if args.config:
        try:
            config = ClientConfig()
            config.load_from_file(args.config)
            return config
        except Exception as e:
            print(f"Error loading config file {args.config}: {e}")
            sys.exit(1)
    
    # Otherwise, build config from arguments and environment variables
    base_url = args.base_url or os.environ.get("EMBED_CLIENT_BASE_URL", "http://localhost")
    port = args.port or int(os.environ.get("EMBED_CLIENT_PORT", "8001"))
    
    if not base_url or not port:
        print("Error: base_url and port must be provided via --base-url/--port arguments or EMBED_CLIENT_BASE_URL/EMBED_CLIENT_PORT environment variables.")
        sys.exit(1)
    
    # Build configuration dictionary
    config_dict = {
        "server": {
            "host": base_url,
            "port": port
        },
        "client": {
            "timeout": args.timeout
        },
        "auth": {
            "method": args.auth_method
        }
    }
    
    # Add authentication configuration
    if args.auth_method == "api_key":
        api_key = args.api_key or os.environ.get("EMBED_CLIENT_API_KEY")
        if api_key:
            config_dict["auth"]["api_keys"] = {"user": api_key}
        else:
            print("Warning: API key not provided for api_key authentication")
    
    elif args.auth_method == "jwt":
        jwt_secret = args.jwt_secret or os.environ.get("EMBED_CLIENT_JWT_SECRET")
        jwt_username = args.jwt_username or os.environ.get("EMBED_CLIENT_JWT_USERNAME")
        jwt_password = args.jwt_password or os.environ.get("EMBED_CLIENT_JWT_PASSWORD")
        
        if jwt_secret and jwt_username and jwt_password:
            config_dict["auth"]["jwt"] = {
                "secret": jwt_secret,
                "username": jwt_username,
                "password": jwt_password
            }
        else:
            print("Warning: JWT credentials not fully provided")
    
    elif args.auth_method == "basic":
        username = args.username or os.environ.get("EMBED_CLIENT_USERNAME")
        password = args.password or os.environ.get("EMBED_CLIENT_PASSWORD")
        
        if username and password:
            config_dict["auth"]["basic"] = {
                "username": username,
                "password": password
            }
        else:
            print("Warning: Basic auth credentials not fully provided")
    
    elif args.auth_method == "certificate":
        cert_file = args.cert_file or os.environ.get("EMBED_CLIENT_CERT_FILE")
        key_file = args.key_file or os.environ.get("EMBED_CLIENT_KEY_FILE")
        
        if cert_file and key_file:
            config_dict["auth"]["certificate"] = {
                "cert_file": cert_file,
                "key_file": key_file
            }
        else:
            print("Warning: Certificate files not fully provided")
    
    # Add SSL configuration if HTTPS is used or SSL parameters are provided
    if base_url.startswith("https://") or args.ssl_verify_mode != "CERT_REQUIRED" or args.ca_cert_file:
        # Force check_hostname=False for CERT_NONE mode
        check_hostname = args.ssl_check_hostname
        if args.ssl_verify_mode == "CERT_NONE":
            check_hostname = False
            
        config_dict["ssl"] = {
            "enabled": True,
            "verify_mode": args.ssl_verify_mode,
            "check_hostname": check_hostname,
            "check_expiry": args.ssl_check_expiry
        }
        
        if args.ca_cert_file:
            config_dict["ssl"]["ca_cert_file"] = args.ca_cert_file
        
        # Add client certificates for mTLS
        if args.cert_file:
            config_dict["ssl"]["cert_file"] = args.cert_file
        if args.key_file:
            config_dict["ssl"]["key_file"] = args.key_file
    
    # Add role-based access control for mTLS + Roles
    if args.roles:
        roles = [role.strip() for role in args.roles.split(",")]
        config_dict["roles"] = roles
    
    if args.role_attributes:
        try:
            role_attributes = json.loads(args.role_attributes)
            config_dict["role_attributes"] = role_attributes
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in role_attributes")
    
    return config_dict


def extract_embeddings(result):
    """Extract embeddings from the API response, supporting both old and new formats."""
    # Handle direct embeddings field (old format compatibility)
    if "embeddings" in result:
        return result["embeddings"]
    
    # Handle result wrapper
    if "result" in result:
        res = result["result"]
        
        # Handle direct list in result (old format)
        if isinstance(res, list):
            return res
        
        if isinstance(res, dict):
            # Handle old format: result.embeddings
            if "embeddings" in res:
                return res["embeddings"]
            
            # Handle old format: result.data.embeddings
            if "data" in res and isinstance(res["data"], dict) and "embeddings" in res["data"]:
                return res["data"]["embeddings"]
            
            # Handle new format: result.data[].embedding
            if "data" in res and isinstance(res["data"], list):
                embeddings = []
                for item in res["data"]:
                    if isinstance(item, dict) and "embedding" in item:
                        embeddings.append(item["embedding"])
                    else:
                        raise ValueError(f"Invalid item format in new API response: {item}")
                return embeddings
    
    raise ValueError(f"Cannot extract embeddings from response: {result}")


async def run_client_examples(client):
    """Run example operations with the client."""
    # Check health
    try:
        health = await client.health()
        print("Service health:", health)
    except EmbeddingServiceError as e:
        print(f"Error during health check: {e}")
        return
    
    # Get OpenAPI schema
    try:
        schema = await client.get_openapi_schema()
        print(f"OpenAPI schema version: {schema.get('info', {}).get('version', 'unknown')}")
    except EmbeddingServiceError as e:
        print(f"Error getting OpenAPI schema: {e}")
    
    # Get available commands
    try:
        commands = await client.get_commands()
        print(f"Available commands: {commands}")
    except EmbeddingServiceError as e:
        print(f"Error getting commands: {e}")
    
    # Test embedding generation
    try:
        texts = ["Hello, world!", "This is a test sentence.", "Embedding service is working!"]
        result = await client.cmd("embed", {"texts": texts})
        
        if result.get("success"):
            embeddings = extract_embeddings(result)
            print(f"Generated {len(embeddings)} embeddings")
            print(f"First embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        else:
            print(f"Embedding generation failed: {result.get('error', 'Unknown error')}")
    except EmbeddingServiceError as e:
        print(f"Error during embedding generation: {e}")


async def demonstrate_security_modes():
    """Demonstrate all security modes using ClientFactory."""
    print("=== Security Modes Demonstration ===")
    print("This demonstration shows how to create clients for all 6 security modes.")
    print("Note: These examples create client configurations but don't connect to actual servers.")
    
    # 1. HTTP mode
    print("\n1. HTTP Mode (no authentication, no SSL):")
    print("   Use case: Development, internal networks, trusted environments")
    try:
        client = ClientFactory.create_http_client("http://localhost", 8001)
        print(f"   ✓ Created HTTP client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        print(f"   ✓ Auth method: {client.get_auth_method()}")
        await client.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 2. HTTP + Token mode
    print("\n2. HTTP + Token Mode (HTTP with API key):")
    print("   Use case: API access control, simple authentication")
    try:
        client = ClientFactory.create_http_token_client(
            "http://localhost", 8001, "api_key", api_key="demo_key"
        )
        print(f"   ✓ Created HTTP + Token client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        print(f"   ✓ Auth method: {client.get_auth_method()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Auth headers: {headers}")
        await client.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 3. HTTPS mode
    print("\n3. HTTPS Mode (HTTPS with server certificates):")
    print("   Use case: Secure communication, public networks")
    try:
        client = ClientFactory.create_https_client("https://localhost", 9443)
        print(f"   ✓ Created HTTPS client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"   ✓ SSL config: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"   ✓ Supported SSL protocols: {protocols}")
        await client.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 4. HTTPS + Token mode
    print("\n4. HTTPS + Token Mode (HTTPS with server certificates + authentication):")
    print("   Use case: Secure API access, production environments")
    try:
        client = ClientFactory.create_https_token_client(
            "https://localhost", 9443, "basic", username="admin", password="secret"
        )
        print(f"   ✓ Created HTTPS + Token client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        print(f"   ✓ Auth method: {client.get_auth_method()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Auth headers: {headers}")
        await client.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 5. mTLS mode
    print("\n5. mTLS Mode (mutual TLS with client and server certificates):")
    print("   Use case: High security, client certificate authentication")
    try:
        client = ClientFactory.create_mtls_client(
            "https://localhost", "mtls_certificates/client/embedding-service.crt", "mtls_certificates/client/embedding-service.key", 8443
        )
        print(f"   ✓ Created mTLS client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ mTLS enabled: {client.is_mtls_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"   ✓ SSL config: {ssl_config}")
        await client.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 6. mTLS + Roles mode
    print("\n6. mTLS + Roles Mode (mTLS with role-based access control):")
    print("   Use case: Enterprise security, role-based permissions")
    try:
        client = ClientFactory.create_mtls_roles_client(
            "https://localhost", "mtls_certificates/client/embedding-service.crt", "mtls_certificates/client/embedding-service.key", 8443,
            roles=["admin", "user"], role_attributes={"department": "IT"}
        )
        print(f"   ✓ Created mTLS + Roles client: {client.base_url}:{client.port}")
        print(f"   ✓ SSL enabled: {client.is_ssl_enabled()}")
        print(f"   ✓ mTLS enabled: {client.is_mtls_enabled()}")
        print(f"   ✓ Authenticated: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"   ✓ Auth headers: {headers}")
        await client.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== Security Mode Summary ===")
    print("1. HTTP: Basic connectivity, no security")
    print("2. HTTP + Token: API key authentication over HTTP")
    print("3. HTTPS: Encrypted communication with server certificates")
    print("4. HTTPS + Token: Encrypted communication + authentication")
    print("5. mTLS: Mutual certificate authentication")
    print("6. mTLS + Roles: Mutual certificates + role-based access control")


async def demonstrate_automatic_detection():
    """Demonstrate automatic security mode detection."""
    print("\n=== Automatic Security Mode Detection ===")
    print("This shows how the client automatically detects the appropriate security mode.")
    
    test_cases = [
        ("http://localhost", None, None, None, None, "HTTP"),
        ("http://localhost", "api_key", None, None, None, "HTTP + Token"),
        ("https://localhost", None, None, None, None, "HTTPS"),
        ("https://localhost", "api_key", None, None, None, "HTTPS + Token"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS"),
        ("https://localhost", None, None, "cert.pem", "key.pem", "mTLS + Roles", {"roles": ["admin"]}),
    ]
    
    for case in test_cases:
        if len(case) == 6:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected = case
            kwargs = {}
        else:
            base_url, auth_method, ssl_enabled, cert_file, key_file, expected, kwargs = case
        
        try:
            mode = detect_security_mode(base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs)
            print(f"  ✓ {base_url} + {auth_method or 'none'} + {cert_file or 'no cert'} -> {mode} ({expected})")
        except Exception as e:
            print(f"  ✗ Error detecting mode for {base_url}: {e}")


async def demonstrate_with_auth_method():
    """Demonstrate the with_auth method for dynamic authentication."""
    print("\n=== Dynamic Authentication with with_auth() Method ===")
    print("This shows how to create clients with different authentication methods using the with_auth class method.")
    
    # Demonstrate different authentication methods
    auth_examples = [
        ("api_key", {"api_key": "dynamic_api_key"}, "API Key Authentication"),
        ("jwt", {"secret": "secret", "username": "user", "password": "pass"}, "JWT Authentication"),
        ("basic", {"username": "admin", "password": "secret"}, "Basic Authentication"),
        ("certificate", {"cert_file": "client.crt", "key_file": "client.key"}, "Certificate Authentication"),
    ]
    
    for auth_method, kwargs, description in auth_examples:
        try:
            print(f"\n{description}:")
            auth_client = EmbeddingServiceAsyncClient.with_auth("http://localhost", 8001, auth_method, **kwargs)
            print(f"  ✓ Auth method: {auth_client.get_auth_method()}")
            print(f"  ✓ Authenticated: {auth_client.is_authenticated()}")
            if auth_client.is_authenticated():
                headers = auth_client.get_auth_headers()
                print(f"  ✓ Auth headers: {headers}")
            await auth_client.close()
        except Exception as e:
            print(f"  ✗ Error with {auth_method}: {e}")
    
    print("\n✓ Dynamic authentication demonstration completed.")


async def main():
    try:
        config = get_params()
        
        # Check if demo mode is requested
        if hasattr(config, 'demo_mode') and config.demo_mode:
            await demonstrate_security_modes()
            await demonstrate_automatic_detection()
            await demonstrate_with_auth_method()
            return
        
        # Create client based on factory mode
        if isinstance(config, ClientConfig):
            # Using configuration object
            client = EmbeddingServiceAsyncClient.from_config(config)
        else:
            # Using configuration dictionary
            factory_mode = getattr(config, 'factory_mode', 'auto')
            
            if factory_mode == "auto":
                # Automatic detection
                client = create_client(
                    config["server"]["host"], 
                    config["server"]["port"],
                    auth_method=config["auth"]["method"],
                    **{k: v for k, v in config.items() if k not in ["server", "auth", "ssl", "client"]}
                )
            else:
                # Specific factory method
                base_url = config["server"]["host"]
                port = config["server"]["port"]
                auth_method = config["auth"]["method"]
                
                if factory_mode == "http":
                    client = ClientFactory.create_http_client(base_url, port)
                elif factory_mode == "http_token":
                    client = ClientFactory.create_http_token_client(base_url, port, auth_method, **config.get("auth", {}))
                elif factory_mode == "https":
                    client = ClientFactory.create_https_client(base_url, port)
                elif factory_mode == "https_token":
                    client = ClientFactory.create_https_token_client(base_url, port, auth_method, **config.get("auth", {}))
                elif factory_mode == "mtls":
                    cert_file = config.get("ssl", {}).get("cert_file", "client_cert.pem")
                    key_file = config.get("ssl", {}).get("key_file", "client_key.pem")
                    client = ClientFactory.create_mtls_client(base_url, cert_file, key_file, port)
                elif factory_mode == "mtls_roles":
                    cert_file = config.get("ssl", {}).get("cert_file", "client_cert.pem")
                    key_file = config.get("ssl", {}).get("key_file", "client_key.pem")
                    roles = config.get("roles", ["admin"])
                    role_attributes = config.get("role_attributes", {})
                    client = ClientFactory.create_mtls_roles_client(
                        base_url, cert_file, key_file, port, roles, role_attributes
                    )
                else:
                    client = EmbeddingServiceAsyncClient(config_dict=config)
        
        print(f"Client configuration:")
        print(f"  Base URL: {client.base_url}")
        print(f"  Port: {client.port}")
        print(f"  Authentication: {client.get_auth_method()}")
        print(f"  Authenticated: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"  Auth headers: {headers}")
        print(f"  SSL enabled: {client.is_ssl_enabled()}")
        print(f"  mTLS enabled: {client.is_mtls_enabled()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"  SSL config: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"  Supported SSL protocols: {protocols}")
        print()
        
        # Explicit open/close example
        print("Explicit session open/close example:")
        await client.close()
        print("Session closed explicitly (manual close example).\n")
        
        # Use context manager
        if isinstance(config, ClientConfig):
            async with EmbeddingServiceAsyncClient.from_config(config) as client:
                await run_client_examples(client)
        else:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                await run_client_examples(client)

    except EmbeddingServiceConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())