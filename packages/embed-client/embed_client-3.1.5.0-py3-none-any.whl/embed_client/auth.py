"""
Authentication system for embed-client.

This module provides comprehensive authentication management for the embed-client,
supporting all security modes and authentication methods. It integrates with
mcp_security_framework when available and provides fallback implementations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import base64
import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

# Try to import mcp_security_framework components
try:
    from mcp_security_framework import (
        AuthManager,
        AuthConfig,
        PermissionConfig,
        PermissionManager,
        SecurityManager
    )
    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    print("Warning: mcp_security_framework not available. Using fallback authentication.")

# Fallback JWT implementation
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: PyJWT not available. JWT authentication will be disabled.")


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, error_code: int = 401):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthResult:
    """Authentication result container."""
    
    def __init__(self, success: bool, user_id: Optional[str] = None, 
                 roles: Optional[List[str]] = None, error: Optional[str] = None):
        self.success = success
        self.user_id = user_id
        self.roles = roles or []
        self.error = error


class ClientAuthManager:
    """
    Client Authentication Manager.
    
    This class provides authentication management for the embed-client,
    supporting multiple authentication methods with integration to
    mcp_security_framework when available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication manager.
        
        Args:
            config: Authentication configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize security framework components if available
        self.auth_manager = None
        self.permission_manager = None
        
        if SECURITY_FRAMEWORK_AVAILABLE:
            self._initialize_security_framework()
        else:
            self.logger.warning("mcp_security_framework not available, using fallback authentication")
    
    def _initialize_security_framework(self) -> None:
        """Initialize mcp_security_framework components."""
        try:
            # Create auth config
            auth_config = AuthConfig(
                enabled=self.config.get("auth", {}).get("enabled", True),
                methods=self.config.get("auth", {}).get("methods", ["api_key"]),
                api_keys=self.config.get("auth", {}).get("api_keys", {}),
                jwt_secret=self.config.get("auth", {}).get("jwt", {}).get("secret", ""),
                jwt_algorithm="HS256",
                jwt_expiry_hours=self.config.get("auth", {}).get("jwt", {}).get("expiry_hours", 24)
            )
            
            # Create permission config
            permission_config = PermissionConfig(
                enabled=self.config.get("security", {}).get("roles_enabled", False),
                roles_file=self.config.get("security", {}).get("roles_file") or "configs/roles.json"
            )
            
            # Create security config
            from mcp_security_framework import SecurityConfig
            security_config = SecurityConfig(
                auth=auth_config,
                permissions=permission_config
            )
            
            # Initialize managers
            self.security_manager = SecurityManager(security_config)
            self.auth_manager = self.security_manager.auth_manager
            self.permission_manager = self.security_manager.permission_manager
            
            self.logger.info("Security framework initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize security framework: {e}")
            self.auth_manager = None
            self.permission_manager = None
    
    def authenticate_api_key(self, api_key: str, header_name: str = "X-API-Key") -> AuthResult:
        """
        Authenticate using API key.
        
        Args:
            api_key: API key to authenticate
            header_name: Header name for API key
            
        Returns:
            AuthResult with authentication status
        """
        try:
            if self.auth_manager:
                # Use security framework
                result = self.auth_manager.authenticate_api_key(api_key)
                if result.status == AuthStatus.SUCCESS:
                    return AuthResult(
                        success=True,
                        user_id=result.user_id,
                        roles=result.roles
                    )
                else:
                    return AuthResult(success=False, error=result.error_message)
            else:
                # Fallback implementation
                return self._authenticate_api_key_fallback(api_key)
                
        except Exception as e:
            self.logger.error(f"API key authentication failed: {e}")
            return AuthResult(success=False, error=str(e))
    
    def _authenticate_api_key_fallback(self, api_key: str) -> AuthResult:
        """Fallback API key authentication."""
        api_keys = self.config.get("auth", {}).get("api_keys", {})
        
        # Check if API key exists
        for user_id, stored_key in api_keys.items():
            if stored_key == api_key:
                return AuthResult(success=True, user_id=user_id)
        
        return AuthResult(success=False, error="Invalid API key")
    
    def authenticate_jwt(self, token: str) -> AuthResult:
        """
        Authenticate using JWT token.
        
        Args:
            token: JWT token to authenticate
            
        Returns:
            AuthResult with authentication status
        """
        try:
            if self.auth_manager:
                # Use security framework
                result = self.auth_manager.validate_jwt_token(token)
                if result.status == AuthStatus.SUCCESS:
                    return AuthResult(
                        success=True,
                        user_id=result.user_id,
                        roles=result.roles
                    )
                else:
                    return AuthResult(success=False, error=result.error_message)
            else:
                # Fallback implementation
                return self._authenticate_jwt_fallback(token)
                
        except Exception as e:
            self.logger.error(f"JWT authentication failed: {e}")
            return AuthResult(success=False, error=str(e))
    
    def _authenticate_jwt_fallback(self, token: str) -> AuthResult:
        """Fallback JWT authentication."""
        if not JWT_AVAILABLE:
            return AuthResult(success=False, error="JWT not available")
        
        try:
            jwt_config = self.config.get("auth", {}).get("jwt", {})
            secret = jwt_config.get("secret", "")
            
            if not secret:
                return AuthResult(success=False, error="JWT secret not configured")
            
            # Decode and verify token
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            
            # Check expiration
            if "exp" in payload and payload["exp"] < time.time():
                return AuthResult(success=False, error="Token expired")
            
            return AuthResult(
                success=True,
                user_id=payload.get("sub", payload.get("user_id")),
                roles=payload.get("roles", [])
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(success=False, error="Token expired")
        except jwt.InvalidTokenError as e:
            return AuthResult(success=False, error=f"Invalid token: {e}")
    
    def authenticate_basic(self, username: str, password: str) -> AuthResult:
        """
        Authenticate using basic authentication.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            AuthResult with authentication status
        """
        try:
            if self.auth_manager:
                # Use security framework
                result = self.auth_manager.authenticate_basic(username, password)
                if result.status == AuthStatus.SUCCESS:
                    return AuthResult(
                        success=True,
                        user_id=result.user_id,
                        roles=result.roles
                    )
                else:
                    return AuthResult(success=False, error=result.error_message)
            else:
                # Fallback implementation
                return self._authenticate_basic_fallback(username, password)
                
        except Exception as e:
            self.logger.error(f"Basic authentication failed: {e}")
            return AuthResult(success=False, error=str(e))
    
    def _authenticate_basic_fallback(self, username: str, password: str) -> AuthResult:
        """Fallback basic authentication."""
        basic_config = self.config.get("auth", {}).get("basic", {})
        stored_username = basic_config.get("username")
        stored_password = basic_config.get("password")
        
        if username == stored_username and password == stored_password:
            return AuthResult(success=True, user_id=username)
        
        return AuthResult(success=False, error="Invalid credentials")
    
    def authenticate_certificate(self, cert_file: str, key_file: str) -> AuthResult:
        """
        Authenticate using client certificate.
        
        Args:
            cert_file: Path to client certificate file
            key_file: Path to client private key file
            
        Returns:
            AuthResult with authentication status
        """
        try:
            if self.auth_manager:
                # Use security framework
                result = self.auth_manager.authenticate_certificate(cert_file, key_file)
                if result.status == AuthStatus.SUCCESS:
                    return AuthResult(
                        success=True,
                        user_id=result.user_id,
                        roles=result.roles
                    )
                else:
                    return AuthResult(success=False, error=result.error_message)
            else:
                # Fallback implementation
                return self._authenticate_certificate_fallback(cert_file, key_file)
                
        except Exception as e:
            self.logger.error(f"Certificate authentication failed: {e}")
            return AuthResult(success=False, error=str(e))
    
    def _authenticate_certificate_fallback(self, cert_file: str, key_file: str) -> AuthResult:
        """Fallback certificate authentication."""
        try:
            # Basic file existence check
            import os
            if not os.path.exists(cert_file):
                return AuthResult(success=False, error="Certificate file not found")
            if not os.path.exists(key_file):
                return AuthResult(success=False, error="Key file not found")
            
            # For fallback, we just verify files exist
            # In a real implementation, you would validate the certificate
            return AuthResult(success=True, user_id="certificate_user")
            
        except Exception as e:
            return AuthResult(success=False, error=f"Certificate validation failed: {e}")
    
    def create_jwt_token(self, user_id: str, roles: Optional[List[str]] = None, 
                        expiry_hours: Optional[int] = None) -> str:
        """
        Create JWT token for user.
        
        Args:
            user_id: User identifier
            roles: List of user roles
            expiry_hours: Token expiry in hours
            
        Returns:
            JWT token string
        """
        try:
            if self.auth_manager:
                # Use security framework
                return self.auth_manager.create_jwt_token(user_id, roles, expiry_hours)
            else:
                # Fallback implementation
                return self._create_jwt_token_fallback(user_id, roles, expiry_hours)
                
        except Exception as e:
            self.logger.error(f"JWT token creation failed: {e}")
            raise AuthenticationError(f"Failed to create JWT token: {e}")
    
    def _create_jwt_token_fallback(self, user_id: str, roles: Optional[List[str]] = None,
                                  expiry_hours: Optional[int] = None) -> str:
        """Fallback JWT token creation."""
        if not JWT_AVAILABLE:
            raise AuthenticationError("JWT not available")
        
        jwt_config = self.config.get("auth", {}).get("jwt", {})
        secret = jwt_config.get("secret", "")
        expiry = expiry_hours or jwt_config.get("expiry_hours", 24)
        
        if not secret:
            raise AuthenticationError("JWT secret not configured")
        
        payload = {
            "sub": user_id,
            "user_id": user_id,
            "roles": roles or [],
            "exp": time.time() + (expiry * 3600),
            "iat": time.time()
        }
        
        return jwt.encode(payload, secret, algorithm="HS256")
    
    def get_auth_headers(self, auth_method: str, **kwargs) -> Dict[str, str]:
        """
        Get authentication headers for requests.
        
        Args:
            auth_method: Authentication method
            **kwargs: Additional authentication parameters
            
        Returns:
            Dictionary of headers
        """
        headers = {}
        
        if auth_method == "api_key":
            api_key = kwargs.get("api_key")
            header_name = kwargs.get("header", "X-API-Key")
            if api_key:
                headers[header_name] = api_key
                
        elif auth_method == "jwt":
            token = kwargs.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
                
        elif auth_method == "basic":
            username = kwargs.get("username")
            password = kwargs.get("password")
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
                
        elif auth_method == "certificate":
            # Certificate authentication is handled at SSL level
            pass
        
        return headers
    
    def validate_auth_config(self) -> List[str]:
        """
        Validate authentication configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        auth_config = self.config.get("auth", {})
        auth_method = auth_config.get("method", "none")
        
        if auth_method == "api_key":
            api_keys = auth_config.get("api_keys", {})
            if not api_keys:
                errors.append("API keys not configured for api_key authentication")
                
        elif auth_method == "jwt":
            jwt_config = auth_config.get("jwt", {})
            if not jwt_config.get("secret"):
                errors.append("JWT secret not configured")
            if not jwt_config.get("username"):
                errors.append("JWT username not configured")
            if not jwt_config.get("password"):
                errors.append("JWT password not configured")
                
        elif auth_method == "certificate":
            cert_config = auth_config.get("certificate", {})
            if not cert_config.get("cert_file"):
                errors.append("Certificate file not configured")
            if not cert_config.get("key_file"):
                errors.append("Key file not configured")
                
        elif auth_method == "basic":
            basic_config = auth_config.get("basic", {})
            if not basic_config.get("username"):
                errors.append("Basic auth username not configured")
            if not basic_config.get("password"):
                errors.append("Basic auth password not configured")
        
        return errors
    
    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self.config.get("auth", {}).get("method", "none") != "none"
    
    def get_auth_method(self) -> str:
        """Get current authentication method."""
        return self.config.get("auth", {}).get("method", "none")
    
    def get_supported_methods(self) -> List[str]:
        """Get list of supported authentication methods."""
        if SECURITY_FRAMEWORK_AVAILABLE:
            return ["api_key", "jwt", "certificate", "basic"]
        else:
            methods = ["api_key", "basic"]
            if JWT_AVAILABLE:
                methods.append("jwt")
            return methods


def create_auth_manager(config: Dict[str, Any]) -> ClientAuthManager:
    """
    Create authentication manager from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        ClientAuthManager instance
    """
    return ClientAuthManager(config)


def create_auth_headers(auth_method: str, **kwargs) -> Dict[str, str]:
    """
    Create authentication headers for requests.
    
    Args:
        auth_method: Authentication method
        **kwargs: Authentication parameters
        
    Returns:
        Dictionary of headers
    """
    # Create temporary auth manager for header generation
    temp_config = {"auth": {"method": auth_method}}
    auth_manager = ClientAuthManager(temp_config)
    return auth_manager.get_auth_headers(auth_method, **kwargs)
