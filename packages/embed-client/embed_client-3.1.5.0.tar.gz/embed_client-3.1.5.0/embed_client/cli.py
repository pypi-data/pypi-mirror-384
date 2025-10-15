#!/usr/bin/env python3
"""
CLI Application for Text Vectorization
Command-line interface for embedding text using embed-client.

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


class VectorizationCLI:
    """CLI application for text vectorization."""
    
    def __init__(self):
        self.client = None
        
    async def connect(self, config: Dict[str, Any]):
        """Connect to embedding service."""
        try:
            self.client = EmbeddingServiceAsyncClient(config_dict=config)
            await self.client.__aenter__()
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from embedding service."""
        if self.client:
            await self.client.close()
    
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


def create_config_from_args(args) -> Dict[str, Any]:
    """Create configuration from command line arguments."""
    config = {
        "server": {
            "host": args.host,
            "port": args.port
        },
        "auth": {"method": "none"},
        "ssl": {"enabled": False},
        "security": {"enabled": False}
    }
    
    # Add authentication if specified
    if args.api_key:
        config["auth"]["method"] = "api_key"
        config["security"] = {
            "enabled": True,
            "tokens": {"user": args.api_key}
        }
    
    # Add SSL if specified
    if args.ssl:
        config["ssl"]["enabled"] = True
        if args.cert_file:
            config["ssl"]["cert_file"] = args.cert_file
        if args.key_file:
            config["ssl"]["key_file"] = args.key_file
        if args.ca_cert_file:
            config["ssl"]["ca_cert_file"] = args.ca_cert_file
    
    return config


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="CLI Application for Text Vectorization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Vectorize text from command line
  python -m embed_client.cli vectorize "hello world" "test text"
  
  # Vectorize text from file
  python -m embed_client.cli vectorize --file texts.txt
  
  # Use HTTPS with authentication
  python -m embed_client.cli vectorize "hello world" --host https://localhost --port 8443 --api-key your-key
  
  # Use mTLS
  python -m embed_client.cli vectorize "hello world" --ssl --cert-file client.crt --key-file client.key
  
  # Get help from service
  python -m embed_client.cli help
  
  # Check service health
  python -m embed_client.cli health
        """
    )
    
    # Connection options
    parser.add_argument("--host", default="http://localhost", help="Server host (default: http://localhost)")
    parser.add_argument("--port", type=int, default=8001, help="Server port (default: 8001)")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL/TLS")
    parser.add_argument("--cert-file", help="Client certificate file")
    parser.add_argument("--key-file", help="Client private key file")
    parser.add_argument("--ca-cert-file", help="CA certificate file")
    
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
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Create CLI instance
    cli = VectorizationCLI()
    
    try:
        # Connect to service
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
            
            await cli.vectorize_texts(texts, args.format)
            
        elif args.command == "health":
            await cli.health_check()
            
        elif args.command == "help":
            await cli.get_help(args.command)
            
        elif args.command == "commands":
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
