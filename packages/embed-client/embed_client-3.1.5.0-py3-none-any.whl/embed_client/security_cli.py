#!/usr/bin/env python3
"""
Security CLI Application for Text Vectorization
Command-line interface supporting all 8 security modes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.client_factory import ClientFactory


class SecurityCLI:
    """CLI application supporting all 8 security modes."""
    
    def __init__(self):
        self.client = None
        
    async def connect(self, config: Dict[str, Any]):
        """Connect to embedding service."""
        try:
            # Создаем клиент и входим в контекст
            self.client = EmbeddingServiceAsyncClient(config_dict=config)
            await self.client.__aenter__()
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from embedding service."""
        if self.client:
            await self.client.__aexit__(None, None, None)
    
    async def health_check(self) -> bool:
        """Check service health."""
        try:
            result = await self.client.health()
            print(f"✅ Service health: {result.get('status', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def vectorize_texts(self, texts: List[str], output_format: str = "json") -> Optional[List[List[float]]]:
        """Vectorize texts."""
        try:
            params = {"texts": texts}
            result = await self.client.cmd("embed", params=params)
            
            # Extract embeddings from result
            embeddings = self._extract_embeddings(result)
            
            if output_format == "json":
                print(json.dumps(embeddings, indent=2))
            elif output_format == "csv":
                self._print_csv(embeddings)
            elif output_format == "vectors":
                self._print_vectors(embeddings)
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Vectorization failed: {e}")
            return None
    
    def _extract_embeddings(self, result: Dict[str, Any]) -> List[List[float]]:
        """Extract embeddings from API response."""
        # Handle different response formats
        if "embeddings" in result:
            return result["embeddings"]
        
        if "result" in result:
            res = result["result"]
            
            if isinstance(res, list):
                return res
            
            if isinstance(res, dict):
                if "embeddings" in res:
                    return res["embeddings"]
                
                # ✅ ИСПРАВЛЕНИЕ: Обработать новый формат ответа
                if "data" in res and isinstance(res["data"], dict):
                    if "embeddings" in res["data"]:
                        return res["data"]["embeddings"]
                
                if "data" in res and isinstance(res["data"], list):
                    embeddings = []
                    for item in res["data"]:
                        if isinstance(item, dict) and "embedding" in item:
                            embeddings.append(item["embedding"])
                        else:
                            embeddings.append(item)
                    return embeddings
        
        raise ValueError(f"Cannot extract embeddings from response: {result}")
    
    def _print_csv(self, embeddings: List[List[float]]):
        """Print embeddings in CSV format."""
        for i, embedding in enumerate(embeddings):
            print(f"text_{i}," + ",".join(map(str, embedding)))
    
    def _print_vectors(self, embeddings: List[List[float]]):
        """Print embeddings as vectors."""
        for i, embedding in enumerate(embeddings):
            print(f"Text {i}: [{', '.join(map(str, embedding))}]")
    
    async def get_help(self, command: Optional[str] = None):
        """Get help information."""
        try:
            if command:
                result = await self.client.cmd("help", params={"command": command})
            else:
                result = await self.client.cmd("help")
            
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Help request failed: {e}")
    
    async def get_commands(self):
        """Get available commands."""
        try:
            result = await self.client.get_commands()
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Commands request failed: {e}")


def create_config_from_security_mode(security_mode: str, host: str, port: int, **kwargs) -> Dict[str, Any]:
    """Create configuration based on security mode."""
    
    # Base configuration
    config = {
        "server": {"host": host, "port": port},
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "security": {"enabled": False}
    }
    
    if security_mode == "http":
        # HTTP - plain HTTP without authentication
        config["server"]["host"] = f"http://{host.split('://')[-1]}"
        
    elif security_mode == "http_token":
        # HTTP + Token - HTTP with API Key authentication
        config["server"]["host"] = f"http://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")}
        }
        
    elif security_mode == "http_token_roles":
        # HTTP + Token + Roles - HTTP with API Key and role-based access control
        config["server"]["host"] = f"http://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")},
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"]
            }
        }
        
    elif security_mode == "https":
        # HTTPS - HTTPS with server certificate verification
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["ssl"] = {
            "enabled": True,
            "verify": False,  # Отключаем проверку для самоподписанных сертификатов
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
            "ca_cert_file": kwargs.get("ca_cert_file")
        }
        
    elif security_mode == "https_token":
        # HTTPS + Token - HTTPS with server certificates + authentication
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file")
        }
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")}
        }
        
    elif security_mode == "https_token_roles":
        # HTTPS + Token + Roles - HTTPS with server certificates + authentication + roles
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "api_key"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file")
        }
        config["security"] = {
            "enabled": True,
            "tokens": {"user": kwargs.get("api_key", "admin-secret-key")},
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"]
            }
        }
        
    elif security_mode == "mtls":
        # mTLS - mutual TLS with client and server certificates
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "certificate"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
            "ca_cert_file": kwargs.get("ca_cert_file")
        }
        
    elif security_mode == "mtls_roles":
        # mTLS + Roles - mTLS with role-based access control
        config["server"]["host"] = f"https://{host.split('://')[-1]}"
        config["auth"]["method"] = "certificate"
        config["ssl"] = {
            "enabled": True,
            "cert_file": kwargs.get("cert_file"),
            "key_file": kwargs.get("key_file"),
            "ca_cert_file": kwargs.get("ca_cert_file")
        }
        config["security"] = {
            "enabled": True,
            "roles": {
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read", "write"],
                "readonly": ["read"]
            }
        }
    
    return config


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Security CLI Application for Text Vectorization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Security Modes:
  http              - Plain HTTP without authentication
  http_token        - HTTP with API Key authentication
  http_token_roles  - HTTP with API Key and role-based access control
  https             - HTTPS with server certificate verification
  https_token       - HTTPS with server certificates + authentication
  https_token_roles - HTTPS with server certificates + authentication + roles
  mtls              - Mutual TLS with client and server certificates
  mtls_roles        - mTLS with role-based access control

Examples:
  # HTTP without authentication
  python -m embed_client.security_cli vectorize --mode http "hello world"
  
  # HTTP with token authentication
  python -m embed_client.security_cli vectorize --mode http_token --api-key your-key "hello world"
  
  # HTTPS with server certificates
  python -m embed_client.security_cli vectorize --mode https --cert-file server.crt --key-file server.key "hello world"
  
  # mTLS with client certificates
  python -m embed_client.security_cli vectorize --mode mtls --cert-file client.crt --key-file client.key --ca-cert-file ca.crt "hello world"
  
  # mTLS with roles
  python -m embed_client.security_cli vectorize --mode mtls_roles --cert-file client.crt --key-file client.key --ca-cert-file ca.crt "hello world"
        """
    )
    
    # Security mode selection
    parser.add_argument(
        "--mode", 
        choices=[
            "http", "http_token", "http_token_roles",
            "https", "https_token", "https_token_roles", 
            "mtls", "mtls_roles"
        ],
        required=True,
        help="Security mode to use"
    )
    
    # Connection options
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="Server port (default: 8001)")
    
    # Authentication options
    parser.add_argument("--api-key", help="API key for authentication (required for token modes)")
    
    # SSL/TLS options
    parser.add_argument("--cert-file", help="Certificate file (required for HTTPS/mTLS modes)")
    parser.add_argument("--key-file", help="Private key file (required for HTTPS/mTLS modes)")
    parser.add_argument("--ca-cert-file", help="CA certificate file (required for mTLS modes)")
    
    # Output options
    parser.add_argument("--format", choices=["json", "csv", "vectors"], default="json", help="Output format")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Vectorize command
    vectorize_parser = subparsers.add_parser("vectorize", help="Vectorize text")
    vectorize_parser.add_argument("texts", nargs="*", help="Texts to vectorize")
    vectorize_parser.add_argument("--file", "-f", help="File containing texts (one per line)")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check service health")
    
    # Help command
    help_parser = subparsers.add_parser("help", help="Get help from service")
    help_parser.add_argument("--command", help="Specific command to get help for")
    
    # Commands command
    commands_parser = subparsers.add_parser("commands", help="Get available commands")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Validate required arguments based on security mode
    if "token" in args.mode and not args.api_key:
        print("❌ API key required for token-based authentication modes")
        return 1
    
    if "https" in args.mode or "mtls" in args.mode:
        if not args.cert_file or not args.key_file:
            print("❌ Certificate and key files required for HTTPS/mTLS modes")
            return 1
    
    if "mtls" in args.mode and not args.ca_cert_file:
        print("❌ CA certificate file required for mTLS modes")
        return 1
    
    # Create configuration
    config = create_config_from_security_mode(
        args.mode,
        args.host,
        args.port,
        api_key=args.api_key,
        cert_file=args.cert_file,
        key_file=args.key_file,
        ca_cert_file=args.ca_cert_file
    )
    
    # Create CLI instance
    cli = SecurityCLI()
    
    try:
        # Connect to service
        print(f"🔌 Connecting using {args.mode} mode...")
        if not await cli.connect(config):
            return 1
        
        # Execute command
        if args.command == "vectorize":
            texts = args.texts
            if args.file:
                with open(args.file, 'r') as f:
                    texts.extend(line.strip() for line in f if line.strip())
            
            if not texts:
                print("❌ No texts provided")
                return 1
            
            print(f"🔤 Vectorizing {len(texts)} texts using {args.mode} mode...")
            await cli.vectorize_texts(texts, args.format)
            
        elif args.command == "health":
            print(f"🏥 Checking service health using {args.mode} mode...")
            await cli.health_check()
            
        elif args.command == "help":
            print(f"❓ Getting help using {args.mode} mode...")
            await cli.get_help(args.command)
            
        elif args.command == "commands":
            print(f"📋 Getting commands using {args.mode} mode...")
            await cli.get_commands()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
