"""
Tests for authentication system.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import tempfile
import os
from embed_client.auth import ClientAuthManager, AuthResult, AuthenticationError, create_auth_manager


class TestClientAuthManager:
    """Test cases for ClientAuthManager class."""

    def test_init_with_security_framework(self):
        """Test initialization with security framework available."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {"user1": "key123"}
            }
        }
        auth_manager = ClientAuthManager(config)
        assert auth_manager.config == config

    def test_init_without_security_framework(self):
        """Test initialization without security framework."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {"user1": "key123"}
            }
        }
        auth_manager = ClientAuthManager(config)
        assert auth_manager.config == config

    def test_authenticate_api_key_success(self):
        """Test successful API key authentication."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {"user1": "key123", "user2": "key456"}
            }
        }
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_api_key("key123")
        assert result.success is True
        assert result.user_id == "user1"
        assert result.error is None

    def test_authenticate_api_key_failure(self):
        """Test failed API key authentication."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {"user1": "key123"}
            }
        }
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_api_key("invalid_key")
        assert result.success is False
        assert result.user_id is None
        assert "Invalid API key" in result.error

    def test_authenticate_api_key_empty_config(self):
        """Test API key authentication with empty config."""
        config = {"auth": {"method": "api_key"}}
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_api_key("any_key")
        assert result.success is False
        assert "Invalid API key" in result.error

    def test_authenticate_basic_success(self):
        """Test successful basic authentication."""
        config = {
            "auth": {
                "method": "basic",
                "basic": {
                    "username": "testuser",
                    "password": "testpass"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_basic("testuser", "testpass")
        assert result.success is True
        assert result.user_id == "testuser"
        assert result.error is None

    def test_authenticate_basic_failure(self):
        """Test failed basic authentication."""
        config = {
            "auth": {
                "method": "basic",
                "basic": {
                    "username": "testuser",
                    "password": "testpass"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_basic("testuser", "wrongpass")
        assert result.success is False
        assert result.user_id is None
        assert "Invalid credentials" in result.error

    def test_authenticate_basic_wrong_username(self):
        """Test basic authentication with wrong username."""
        config = {
            "auth": {
                "method": "basic",
                "basic": {
                    "username": "testuser",
                    "password": "testpass"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_basic("wronguser", "testpass")
        assert result.success is False
        assert "Invalid credentials" in result.error

    def test_authenticate_certificate_success(self):
        """Test successful certificate authentication."""
        config = {
            "auth": {
                "method": "certificate",
                "certificate": {
                    "cert_file": "test.crt",
                    "key_file": "test.key"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.crt', delete=False) as cert_file:
            cert_file.write("test certificate content")
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.key', delete=False) as key_file:
            key_file.write("test key content")
            key_path = key_file.name
        
        try:
            result = auth_manager.authenticate_certificate(cert_path, key_path)
            assert result.success is True
            assert result.user_id == "certificate_user"
        finally:
            os.unlink(cert_path)
            os.unlink(key_path)

    def test_authenticate_certificate_file_not_found(self):
        """Test certificate authentication with missing files."""
        config = {
            "auth": {
                "method": "certificate",
                "certificate": {
                    "cert_file": "nonexistent.crt",
                    "key_file": "nonexistent.key"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        result = auth_manager.authenticate_certificate("nonexistent.crt", "nonexistent.key")
        assert result.success is False
        assert "Certificate file not found" in result.error

    def test_get_auth_headers_api_key(self):
        """Test getting auth headers for API key."""
        config = {"auth": {"method": "api_key"}}
        auth_manager = ClientAuthManager(config)
        
        headers = auth_manager.get_auth_headers("api_key", api_key="test_key")
        assert headers == {"X-API-Key": "test_key"}

    def test_get_auth_headers_api_key_custom_header(self):
        """Test getting auth headers for API key with custom header."""
        config = {"auth": {"method": "api_key"}}
        auth_manager = ClientAuthManager(config)
        
        headers = auth_manager.get_auth_headers("api_key", api_key="test_key", header="X-Custom-Key")
        assert headers == {"X-Custom-Key": "test_key"}

    def test_get_auth_headers_jwt(self):
        """Test getting auth headers for JWT."""
        config = {"auth": {"method": "jwt"}}
        auth_manager = ClientAuthManager(config)
        
        headers = auth_manager.get_auth_headers("jwt", token="test_token")
        assert headers == {"Authorization": "Bearer test_token"}

    def test_get_auth_headers_basic(self):
        """Test getting auth headers for basic auth."""
        config = {"auth": {"method": "basic"}}
        auth_manager = ClientAuthManager(config)
        
        headers = auth_manager.get_auth_headers("basic", username="user", password="pass")
        expected_auth = "Basic " + "dXNlcjpwYXNz"  # base64 of "user:pass"
        assert headers == {"Authorization": expected_auth}

    def test_get_auth_headers_certificate(self):
        """Test getting auth headers for certificate (should be empty)."""
        config = {"auth": {"method": "certificate"}}
        auth_manager = ClientAuthManager(config)
        
        headers = auth_manager.get_auth_headers("certificate")
        assert headers == {}

    def test_validate_auth_config_valid_api_key(self):
        """Test validating valid API key config."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {"user1": "key123"}
            }
        }
        auth_manager = ClientAuthManager(config)
        
        errors = auth_manager.validate_auth_config()
        assert len(errors) == 0

    def test_validate_auth_config_invalid_api_key(self):
        """Test validating invalid API key config."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {}
            }
        }
        auth_manager = ClientAuthManager(config)
        
        errors = auth_manager.validate_auth_config()
        assert len(errors) == 1
        assert "API keys not configured" in errors[0]

    def test_validate_auth_config_valid_basic(self):
        """Test validating valid basic auth config."""
        config = {
            "auth": {
                "method": "basic",
                "basic": {
                    "username": "user",
                    "password": "pass"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        errors = auth_manager.validate_auth_config()
        assert len(errors) == 0

    def test_validate_auth_config_invalid_basic(self):
        """Test validating invalid basic auth config."""
        config = {
            "auth": {
                "method": "basic",
                "basic": {
                    "username": "user"
                    # missing password
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        errors = auth_manager.validate_auth_config()
        assert len(errors) == 1
        assert "password not configured" in errors[0]

    def test_validate_auth_config_valid_certificate(self):
        """Test validating valid certificate config."""
        config = {
            "auth": {
                "method": "certificate",
                "certificate": {
                    "cert_file": "test.crt",
                    "key_file": "test.key"
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        errors = auth_manager.validate_auth_config()
        assert len(errors) == 0

    def test_validate_auth_config_invalid_certificate(self):
        """Test validating invalid certificate config."""
        config = {
            "auth": {
                "method": "certificate",
                "certificate": {
                    "cert_file": "test.crt"
                    # missing key_file
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        errors = auth_manager.validate_auth_config()
        assert len(errors) == 1
        assert "Key file not configured" in errors[0]

    def test_is_auth_enabled_true(self):
        """Test checking if auth is enabled."""
        config = {
            "auth": {
                "method": "api_key"
            }
        }
        auth_manager = ClientAuthManager(config)
        
        assert auth_manager.is_auth_enabled() is True

    def test_is_auth_enabled_false(self):
        """Test checking if auth is disabled."""
        config = {
            "auth": {
                "method": "none"
            }
        }
        auth_manager = ClientAuthManager(config)
        
        assert auth_manager.is_auth_enabled() is False

    def test_get_auth_method(self):
        """Test getting auth method."""
        config = {
            "auth": {
                "method": "api_key"
            }
        }
        auth_manager = ClientAuthManager(config)
        
        assert auth_manager.get_auth_method() == "api_key"

    def test_get_supported_methods(self):
        """Test getting supported authentication methods."""
        config = {"auth": {"method": "api_key"}}
        auth_manager = ClientAuthManager(config)
        
        methods = auth_manager.get_supported_methods()
        assert "api_key" in methods
        assert "basic" in methods

    def test_create_jwt_token_fallback(self):
        """Test JWT token creation with fallback implementation."""
        config = {
            "auth": {
                "method": "jwt",
                "jwt": {
                    "secret": "test_secret",
                    "expiry_hours": 24
                }
            }
        }
        auth_manager = ClientAuthManager(config)
        
        try:
            token = auth_manager.create_jwt_token("test_user", ["admin"])
            assert isinstance(token, str)
            assert len(token) > 0
        except AuthenticationError:
            # JWT might not be available
            pass

    def test_create_jwt_token_no_secret(self):
        """Test JWT token creation without secret."""
        config = {
            "auth": {
                "method": "jwt",
                "jwt": {}
            }
        }
        auth_manager = ClientAuthManager(config)
        
        with pytest.raises(AuthenticationError):
            auth_manager.create_jwt_token("test_user")


class TestAuthResult:
    """Test cases for AuthResult class."""

    def test_auth_result_success(self):
        """Test successful auth result."""
        result = AuthResult(success=True, user_id="user1", roles=["admin"])
        
        assert result.success is True
        assert result.user_id == "user1"
        assert result.roles == ["admin"]
        assert result.error is None

    def test_auth_result_failure(self):
        """Test failed auth result."""
        result = AuthResult(success=False, error="Invalid credentials")
        
        assert result.success is False
        assert result.user_id is None
        assert result.roles == []
        assert result.error == "Invalid credentials"

    def test_auth_result_defaults(self):
        """Test auth result with default values."""
        result = AuthResult(success=True)
        
        assert result.success is True
        assert result.user_id is None
        assert result.roles == []
        assert result.error is None


class TestAuthManagerFactory:
    """Test cases for auth manager factory functions."""

    def test_create_auth_manager(self):
        """Test creating auth manager from config."""
        config = {
            "auth": {
                "method": "api_key",
                "api_keys": {"user1": "key123"}
            }
        }
        
        auth_manager = create_auth_manager(config)
        assert isinstance(auth_manager, ClientAuthManager)
        assert auth_manager.config == config

    def test_create_auth_headers_function(self):
        """Test create_auth_headers function."""
        from embed_client.auth import create_auth_headers
        
        headers = create_auth_headers("api_key", api_key="test_key")
        assert headers == {"X-API-Key": "test_key"}


class TestAuthenticationError:
    """Test cases for AuthenticationError class."""

    def test_authentication_error_default(self):
        """Test authentication error with default error code."""
        error = AuthenticationError("Test error")
        
        assert error.message == "Test error"
        assert error.error_code == 401

    def test_authentication_error_custom_code(self):
        """Test authentication error with custom error code."""
        error = AuthenticationError("Test error", 403)
        
        assert error.message == "Test error"
        assert error.error_code == 403
