"""
embed-client: Async client for Embedding Service API with comprehensive authentication, SSL/TLS, and mTLS support

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from .async_client import EmbeddingServiceAsyncClient
from .config import ClientConfig
from .auth import AuthManager
from .ssl_manager import ClientSSLManager
from .client_factory import ClientFactory

__version__ = "3.1.0.2"
__all__ = [
    "EmbeddingServiceAsyncClient",
    "ClientConfig", 
    "AuthManager",
    "ClientSSLManager",
    "ClientFactory"
]