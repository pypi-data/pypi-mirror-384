"""
Async client for Embedding Service API (OpenAPI 3.0.2)

- 100% type-annotated
- English docstrings and examples
- Ready for PyPi
- Supports new API format with body, embedding, and chunks
- Supports all authentication methods (API Key, JWT, Basic Auth, Certificate)
- Integrates with mcp_security_framework
- Supports all security modes (HTTP, HTTPS, mTLS)

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, List, Optional, Union
import aiohttp
import asyncio
import os
import json
import logging
from pathlib import Path

# Import authentication, configuration, and SSL systems
from .auth import ClientAuthManager, create_auth_manager
from .config import ClientConfig
from .ssl_manager import ClientSSLManager, create_ssl_manager

class EmbeddingServiceError(Exception):
    """Base exception for EmbeddingServiceAsyncClient."""

class EmbeddingServiceConnectionError(EmbeddingServiceError):
    """Raised when the service is unavailable or connection fails."""

class EmbeddingServiceHTTPError(EmbeddingServiceError):
    """Raised for HTTP errors (4xx, 5xx)."""
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message

class EmbeddingServiceAPIError(EmbeddingServiceError):
    """Raised for errors returned by the API in the response body."""
    def __init__(self, error: Any):
        super().__init__(f"API error: {error}")
        self.error = error

class EmbeddingServiceConfigError(EmbeddingServiceError):
    """Raised for configuration errors (invalid base_url, port, etc.)."""

class EmbeddingServiceTimeoutError(EmbeddingServiceError):
    """Raised when request times out."""

class EmbeddingServiceJSONError(EmbeddingServiceError):
    """Raised when JSON parsing fails."""

class EmbeddingServiceAsyncClient:
    """
    Asynchronous client for the Embedding Service API.
    
    Supports both old and new API formats:
    - Old format: {"result": {"success": true, "data": {"embeddings": [...]}}}
    - New format: {"result": {"success": true, "data": {"embeddings": [...], "results": [{"body": "text", "embedding": [...], "tokens": [...], "bm25_tokens": [...]}]}}}
    
    Supports all authentication methods and security modes:
    - API Key authentication
    - JWT token authentication
    - Basic authentication
    - Certificate authentication (mTLS)
    - HTTP, HTTPS, and mTLS security modes
    
    Args:
        base_url (str, optional): Base URL of the embedding service (e.g., "http://localhost").
        port (int, optional): Port of the embedding service (e.g., 8001).
        timeout (float): Request timeout in seconds (default: 30).
        config (ClientConfig, optional): Configuration object with authentication and SSL settings.
        config_dict (dict, optional): Configuration dictionary with authentication and SSL settings.
        auth_manager (ClientAuthManager, optional): Authentication manager instance.
        
    Raises:
        EmbeddingServiceConfigError: If base_url or port is invalid.
    """
    def __init__(self, 
                 base_url: Optional[str] = None, 
                 port: Optional[int] = None, 
                 timeout: float = 30.0,
                 config: Optional[ClientConfig] = None,
                 config_dict: Optional[Dict[str, Any]] = None,
                 auth_manager: Optional[ClientAuthManager] = None):
        # Initialize configuration
        self.config = config
        self.config_dict = config_dict
        self.auth_manager = auth_manager
        
        # If config is provided, use it to set base_url and port
        if config:
            self.base_url = config.get("server.host", base_url or os.getenv("EMBEDDING_SERVICE_BASE_URL", "http://localhost"))
            self.port = config.get("server.port", port or int(os.getenv("EMBEDDING_SERVICE_PORT", "8001")))
            self.timeout = config.get("client.timeout", timeout)
        elif config_dict:
            server_config = config_dict.get("server", {})
            # ✅ ИСПРАВЛЕНИЕ: Использовать base_url из конфигурации, если он есть
            if "base_url" in server_config:
                self.base_url = server_config["base_url"]
                self.port = None  # Порт уже включен в base_url
            else:
                self.base_url = server_config.get("host", base_url or os.getenv("EMBEDDING_SERVICE_BASE_URL", "http://localhost"))
                self.port = server_config.get("port", port or int(os.getenv("EMBEDDING_SERVICE_PORT", "8001")))
            self.timeout = config_dict.get("client", {}).get("timeout", timeout)
        else:
            # Use provided parameters or environment variables
            try:
                self.base_url = base_url or os.getenv("EMBEDDING_SERVICE_BASE_URL", "http://localhost")
            except (TypeError, AttributeError) as e:
                raise EmbeddingServiceConfigError(f"Invalid base_url configuration: {e}") from e
            
            try:
                self.port = port or int(os.getenv("EMBEDDING_SERVICE_PORT", "8001"))
            except (ValueError, TypeError) as e:
                raise EmbeddingServiceConfigError(f"Invalid port configuration: {e}") from e
            self.timeout = timeout
        
        # Validate base_url
        try:
            if not self.base_url:
                raise EmbeddingServiceConfigError("base_url must be provided.")
            if not isinstance(self.base_url, str):
                raise EmbeddingServiceConfigError("base_url must be a string.")
            
            # Validate URL format
            if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
                raise EmbeddingServiceConfigError("base_url must start with http:// or https://")
        except (TypeError, AttributeError) as e:
            raise EmbeddingServiceConfigError(f"Invalid base_url configuration: {e}") from e
        
        # Validate port
        try:
            # ✅ ИСПРАВЛЕНИЕ: Порт не обязателен, если он уже в base_url
            if self.port is not None:
                if not isinstance(self.port, int) or self.port <= 0 or self.port > 65535:
                    raise EmbeddingServiceConfigError("port must be a valid integer between 1 and 65535.")
        except (ValueError, TypeError) as e:
            raise EmbeddingServiceConfigError(f"Invalid port configuration: {e}") from e
        
        # Validate timeout
        try:
            self.timeout = float(self.timeout)
            if self.timeout <= 0:
                raise EmbeddingServiceConfigError("timeout must be positive.")
        except (ValueError, TypeError) as e:
            raise EmbeddingServiceConfigError(f"Invalid timeout configuration: {e}") from e
        
        # Initialize authentication manager if not provided
        if not self.auth_manager and (self.config or self.config_dict):
            config_data = self.config_dict if self.config_dict else self.config.get_all()
            self.auth_manager = create_auth_manager(config_data)
        
        # Initialize SSL manager
        self.ssl_manager = None
        if self.config or self.config_dict:
            config_data = self.config_dict if self.config_dict else self.config.get_all()
            self.ssl_manager = create_ssl_manager(config_data)
        
        self._session: Optional[aiohttp.ClientSession] = None

    def _make_url(self, path: str, base_url: Optional[str] = None, port: Optional[int] = None) -> str:
        try:
            url = (base_url or self.base_url).rstrip("/")
            port_val = port if port is not None else self.port
            
            # ✅ ИСПРАВЛЕНИЕ: Проверить, есть ли уже порт в URL
            if "://" in url:
                protocol, rest = url.split("://", 1)
                if ":" in rest:  # Порт уже есть в URL
                    return f"{url}{path}"
                elif port_val is not None:  # Порта нет, добавить если есть
                    return f"{url}:{port_val}{path}"
                else:  # Порта нет и не указан
                    return f"{url}{path}"
            else:
                # Fallback для URL без протокола
                if port_val is not None:
                    return f"{url}:{port_val}{path}"
                else:
                    return f"{url}{path}"
        except Exception as e:
            raise EmbeddingServiceConfigError(f"Failed to construct URL: {e}") from e

    def _format_error_response(self, error: str, lang: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
        """
        Format error response in a standard way.
        Args:
            error (str): Error message
            lang (str, optional): Language of the text that caused the error
            text (str, optional): Text that caused the error
        Returns:
            dict: Formatted error response
        """
        response = {"error": f"Embedding service error: {error}"}
        if lang is not None:
            response["lang"] = lang
        if text is not None:
            response["text"] = text
        return response

    def extract_embeddings(self, result: Dict[str, Any]) -> List[List[float]]:
        """
        Extract embeddings from API response, supporting both old and new formats.
        
        Args:
            result: API response dictionary
            
        Returns:
            List of embedding vectors (list of lists of floats)
            
        Raises:
            ValueError: If embeddings cannot be extracted from the response
        """
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

    def extract_embedding_data(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract full embedding data from API response (new format only).
        
        Args:
            result: API response dictionary
            
        Returns:
            List of dictionaries with 'body', 'embedding', 'tokens', and 'bm25_tokens' fields
            
        Raises:
            ValueError: If data cannot be extracted or is in old format
        """
        if "result" in result and isinstance(result["result"], dict):
            res = result["result"]
            if "data" in res and isinstance(res["data"], dict) and "results" in res["data"]:
                # New format: result.data.results[]
                results = res["data"]["results"]
                if isinstance(results, list):
                    # Validate that all items have required fields
                    for i, item in enumerate(results):
                        if not isinstance(item, dict):
                            raise ValueError(f"Item {i} is not a dictionary: {item}")
                        if "body" not in item:
                            raise ValueError(f"Item {i} missing 'body' field: {item}")
                        if "embedding" not in item:
                            raise ValueError(f"Item {i} missing 'embedding' field: {item}")
                        if "tokens" not in item:
                            raise ValueError(f"Item {i} missing 'tokens' field: {item}")
                        if "bm25_tokens" not in item:
                            raise ValueError(f"Item {i} missing 'bm25_tokens' field: {item}")
                    
                    return results
            
            # Legacy support for old format: result.data[]
            if "data" in res and isinstance(res["data"], list):
                # Validate that all items have required fields
                for i, item in enumerate(res["data"]):
                    if not isinstance(item, dict):
                        raise ValueError(f"Item {i} is not a dictionary: {item}")
                    if "body" not in item:
                        raise ValueError(f"Item {i} missing 'body' field: {item}")
                    if "embedding" not in item:
                        raise ValueError(f"Item {i} missing 'embedding' field: {item}")
                    # Old format had 'chunks' instead of 'tokens'
                    if "chunks" not in item and "tokens" not in item:
                        raise ValueError(f"Item {i} missing 'chunks' or 'tokens' field: {item}")
                
                return res["data"]
        
        raise ValueError(f"Cannot extract embedding data from response (new format required): {result}")

    def extract_texts(self, result: Dict[str, Any]) -> List[str]:
        """
        Extract original texts from API response (new format only).
        
        Args:
            result: API response dictionary
            
        Returns:
            List of original text strings
            
        Raises:
            ValueError: If texts cannot be extracted or is in old format
        """
        data = self.extract_embedding_data(result)
        return [item["body"] for item in data]

    def extract_chunks(self, result: Dict[str, Any]) -> List[List[str]]:
        """
        Extract text chunks from API response (new format only).
        Note: This method now extracts 'tokens' instead of 'chunks' for compatibility.
        
        Args:
            result: API response dictionary
            
        Returns:
            List of token lists for each text
            
        Raises:
            ValueError: If chunks cannot be extracted or is in old format
        """
        data = self.extract_embedding_data(result)
        chunks = []
        for item in data:
            # New format uses 'tokens', old format used 'chunks'
            if "tokens" in item:
                chunks.append(item["tokens"])
            elif "chunks" in item:
                chunks.append(item["chunks"])
            else:
                raise ValueError(f"Item missing both 'tokens' and 'chunks' fields: {item}")
        return chunks

    def extract_tokens(self, result: Dict[str, Any]) -> List[List[str]]:
        """
        Extract tokens from API response (new format only).
        
        Args:
            result: API response dictionary
            
        Returns:
            List of token lists for each text
            
        Raises:
            ValueError: If tokens cannot be extracted or is in old format
        """
        data = self.extract_embedding_data(result)
        return [item["tokens"] for item in data]

    def extract_bm25_tokens(self, result: Dict[str, Any]) -> List[List[str]]:
        """
        Extract BM25 tokens from API response (new format only).
        
        Args:
            result: API response dictionary
            
        Returns:
            List of BM25 token lists for each text
            
        Raises:
            ValueError: If BM25 tokens cannot be extracted or is in old format
        """
        data = self.extract_embedding_data(result)
        return [item["bm25_tokens"] for item in data]

    async def __aenter__(self):
        try:
            # Create session with timeout configuration
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            # Create SSL connector if SSL manager is available
            connector = None
            if self.ssl_manager:
                connector = self.ssl_manager.create_connector()
            
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
            return self
        except Exception as e:
            raise EmbeddingServiceError(f"Failed to create HTTP session: {e}") from e

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                raise EmbeddingServiceError(f"Failed to close HTTP session: {e}") from e
            finally:
                self._session = None

    async def _parse_json_response(self, resp: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Parse JSON response with proper error handling.
        
        Args:
            resp: aiohttp response object
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            EmbeddingServiceJSONError: If JSON parsing fails
        """
        try:
            return await resp.json()
        except json.JSONDecodeError as e:
            try:
                text = await resp.text()
                raise EmbeddingServiceJSONError(f"Invalid JSON response: {e}. Response text: {text[:500]}...") from e
            except Exception as text_error:
                raise EmbeddingServiceJSONError(f"Invalid JSON response: {e}. Failed to get response text: {text_error}") from e
        except UnicodeDecodeError as e:
            raise EmbeddingServiceJSONError(f"Unicode decode error in response: {e}") from e
        except Exception as e:
            raise EmbeddingServiceJSONError(f"Unexpected error parsing JSON: {e}") from e

    async def health(self, base_url: Optional[str] = None, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Check the health of the service.
        Args:
            base_url (str, optional): Override base URL.
            port (int, optional): Override port.
        Returns:
            dict: Health status and model info.
        """
        url = self._make_url("/health", base_url, port)
        headers = self.get_auth_headers()
        try:
            async with self._session.get(url, headers=headers, timeout=self.timeout) as resp:
                await self._raise_for_status(resp)
                try:
                    data = await resp.json()
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
                    raise EmbeddingServiceJSONError(f"Invalid JSON response: {e}") from e
                if "error" in data:
                    raise EmbeddingServiceAPIError(data["error"])
                return data
        except EmbeddingServiceHTTPError:
            raise
        except EmbeddingServiceConnectionError:
            raise
        except EmbeddingServiceJSONError:
            raise
        except EmbeddingServiceTimeoutError:
            raise
        except aiohttp.ClientConnectionError as e:
            raise EmbeddingServiceConnectionError(f"Connection error: {e}") from e
        except aiohttp.ClientResponseError as e:
            raise EmbeddingServiceHTTPError(e.status, e.message) from e
        except asyncio.TimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Request timeout: {e}") from e
        except aiohttp.ServerTimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Server timeout: {e}") from e
        except aiohttp.ClientSSLError as e:
            raise EmbeddingServiceConnectionError(f"SSL error: {e}") from e
        except aiohttp.ClientOSError as e:
            raise EmbeddingServiceConnectionError(f"OS error: {e}") from e
        except Exception as e:
            raise EmbeddingServiceError(f"Unexpected error: {e}") from e

    async def get_openapi_schema(self, base_url: Optional[str] = None, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Get the OpenAPI schema of the service.
        Args:
            base_url (str, optional): Override base URL.
            port (int, optional): Override port.
        Returns:
            dict: OpenAPI schema.
        """
        url = self._make_url("/openapi.json", base_url, port)
        headers = self.get_auth_headers()
        try:
            async with self._session.get(url, headers=headers, timeout=self.timeout) as resp:
                await self._raise_for_status(resp)
                try:
                    data = await resp.json()
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
                    raise EmbeddingServiceJSONError(f"Invalid JSON response: {e}") from e
                if "error" in data:
                    raise EmbeddingServiceAPIError(data["error"])
                return data
        except EmbeddingServiceHTTPError:
            raise
        except EmbeddingServiceConnectionError:
            raise
        except EmbeddingServiceJSONError:
            raise
        except EmbeddingServiceTimeoutError:
            raise
        except aiohttp.ClientConnectionError as e:
            raise EmbeddingServiceConnectionError(f"Connection error: {e}") from e
        except aiohttp.ClientResponseError as e:
            raise EmbeddingServiceHTTPError(e.status, e.message) from e
        except asyncio.TimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Request timeout: {e}") from e
        except aiohttp.ServerTimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Server timeout: {e}") from e
        except aiohttp.ClientSSLError as e:
            raise EmbeddingServiceConnectionError(f"SSL error: {e}") from e
        except aiohttp.ClientOSError as e:
            raise EmbeddingServiceConnectionError(f"OS error: {e}") from e
        except Exception as e:
            raise EmbeddingServiceError(f"Unexpected error: {e}") from e

    async def get_commands(self, base_url: Optional[str] = None, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Get the list of available commands.
        Args:
            base_url (str, optional): Override base URL.
            port (int, optional): Override port.
        Returns:
            dict: List of commands and their descriptions.
        """
        url = self._make_url("/api/commands", base_url, port)
        headers = self.get_auth_headers()
        try:
            async with self._session.get(url, headers=headers, timeout=self.timeout) as resp:
                await self._raise_for_status(resp)
                try:
                    data = await resp.json()
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
                    raise EmbeddingServiceJSONError(f"Invalid JSON response: {e}") from e
                if "error" in data:
                    raise EmbeddingServiceAPIError(data["error"])
                return data
        except EmbeddingServiceHTTPError:
            raise
        except EmbeddingServiceConnectionError:
            raise
        except EmbeddingServiceJSONError:
            raise
        except EmbeddingServiceTimeoutError:
            raise
        except aiohttp.ClientConnectionError as e:
            raise EmbeddingServiceConnectionError(f"Connection error: {e}") from e
        except aiohttp.ClientResponseError as e:
            raise EmbeddingServiceHTTPError(e.status, e.message) from e
        except asyncio.TimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Request timeout: {e}") from e
        except aiohttp.ServerTimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Server timeout: {e}") from e
        except aiohttp.ClientSSLError as e:
            raise EmbeddingServiceConnectionError(f"SSL error: {e}") from e
        except aiohttp.ClientOSError as e:
            raise EmbeddingServiceConnectionError(f"OS error: {e}") from e
        except Exception as e:
            raise EmbeddingServiceError(f"Unexpected error: {e}") from e

    def _validate_texts(self, texts: List[str]) -> None:
        """
        Validate input texts before sending to the API.
        Args:
            texts (List[str]): List of texts to validate
        Raises:
            EmbeddingServiceAPIError: If texts are invalid
        """
        if not texts:
            raise EmbeddingServiceAPIError({
                "code": -32602,
                "message": "Empty texts list provided"
            })
        
        invalid_texts = []
        for i, text in enumerate(texts):
            if not isinstance(text, str):
                invalid_texts.append(f"Text at index {i} is not a string")
                continue
            if not text or not text.strip():
                invalid_texts.append(f"Text at index {i} is empty or contains only whitespace")
            elif len(text.strip()) < 2:  # Минимальная длина текста
                invalid_texts.append(f"Text at index {i} is too short (minimum 2 characters)")
        
        if invalid_texts:
            raise EmbeddingServiceAPIError({
                "code": -32602,
                "message": "Invalid input texts",
                "details": invalid_texts
            })

    async def cmd(self, command: str, params: Optional[Dict[str, Any]] = None, base_url: Optional[str] = None, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a command via JSON-RPC protocol.
        Args:
            command (str): Command to execute (embed, models, health, help, config).
            params (dict, optional): Parameters for the command.
            base_url (str, optional): Override base URL.
            port (int, optional): Override port.
        Returns:
            dict: Command execution result or error response in format:
                {
                    "error": {
                        "code": <код ошибки>,
                        "message": <сообщение об ошибке>,
                        "details": <опциональные детали ошибки>
                    }
                }
                или
                {
                    "result": {
                        "success": true,
                        "data": {
                            "embeddings": [[...], ...]
                        }
                    }
                }
        """
        if not command:
            raise EmbeddingServiceAPIError({
                "code": -32602,
                "message": "Command is required"
            })

        # Валидация текстов для команды embed
        if command == "embed" and params and "texts" in params:
            self._validate_texts(params["texts"])

        logger = logging.getLogger('EmbeddingServiceAsyncClient.cmd')
        url = self._make_url("/cmd", base_url, port)
        headers = self.get_auth_headers()
        payload = {"command": command}
        if params is not None:
            payload["params"] = params
        logger.info(f"Sending embedding command: url={url}, payload={payload}, headers={headers}")
        try:
            async with self._session.post(url, json=payload, headers=headers, timeout=self.timeout) as resp:
                logger.info(f"Embedding service HTTP status: {resp.status}")
                await self._raise_for_status(resp)
                try:
                    resp_json = await resp.json()
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
                    raise EmbeddingServiceJSONError(f"Invalid JSON response: {e}") from e
                logger.info(f"Embedding service response: {str(resp_json)[:300]}")
                # Обработка ошибок API
                if "error" in resp_json:
                    raise EmbeddingServiceAPIError(resp_json["error"])
                if "result" in resp_json:
                    result = resp_json["result"]
                    if isinstance(result, dict) and (result.get("success") is False or "error" in result):
                        raise EmbeddingServiceAPIError(result.get("error", result))
                return resp_json
        except EmbeddingServiceAPIError:
            raise
        except EmbeddingServiceHTTPError:
            raise
        except EmbeddingServiceConnectionError:
            raise
        except EmbeddingServiceJSONError:
            raise
        except EmbeddingServiceTimeoutError:
            raise
        except aiohttp.ServerTimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Server timeout: {e}") from e
        except aiohttp.ClientConnectionError as e:
            raise EmbeddingServiceConnectionError(f"Connection error: {e}") from e
        except aiohttp.ClientResponseError as e:
            raise EmbeddingServiceHTTPError(e.status, e.message) from e
        except asyncio.TimeoutError as e:
            raise EmbeddingServiceTimeoutError(f"Request timeout: {e}") from e
        except aiohttp.ClientSSLError as e:
            raise EmbeddingServiceConnectionError(f"SSL error: {e}") from e
        except aiohttp.ClientOSError as e:
            raise EmbeddingServiceConnectionError(f"OS error: {e}") from e
        except Exception as e:
            logger.error(f"Error in embedding cmd: {e}", exc_info=True)
            raise EmbeddingServiceError(f"Unexpected error: {e}") from e

    async def _raise_for_status(self, resp: aiohttp.ClientResponse):
        try:
            resp.raise_for_status()
        except aiohttp.ClientResponseError as e:
            raise EmbeddingServiceHTTPError(e.status, e.message) from e

    async def close(self) -> None:
        """
        Close the underlying HTTP session explicitly.

        This method allows the user to manually close the aiohttp.ClientSession used by the client.
        It is safe to call multiple times; if the session is already closed or was never opened, nothing happens.

        Raises:
            EmbeddingServiceError: If closing the session fails.
        """
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                raise EmbeddingServiceError(f"Failed to close HTTP session: {e}") from e
            finally:
                self._session = None

    # TODO: Add methods for /cmd, /api/commands, etc.
    
    @classmethod
    def from_config(cls, config: ClientConfig) -> "EmbeddingServiceAsyncClient":
        """
        Create client from ClientConfig object.
        
        Args:
            config: ClientConfig object with authentication and SSL settings
            
        Returns:
            EmbeddingServiceAsyncClient instance configured with the provided config
        """
        return cls(config=config)
    
    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, Any]) -> "EmbeddingServiceAsyncClient":
        """
        Create client from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary with authentication and SSL settings
            
        Returns:
            EmbeddingServiceAsyncClient instance configured with the provided config
        """
        return cls(config_dict=config_dict)
    
    @classmethod
    def from_config_file(cls, config_path: Union[str, Path]) -> "EmbeddingServiceAsyncClient":
        """
        Create client from configuration file.
        
        Args:
            config_path: Path to configuration file (JSON or YAML)
            
        Returns:
            EmbeddingServiceAsyncClient instance configured with the provided config
        """
        # ✅ ИСПРАВЛЕНИЕ: Создать объект ClientConfig и загрузить конфигурацию
        config = ClientConfig(config_path)
        config.load_config()
        return cls(config=config)
    
    @classmethod
    def with_auth(cls, 
                  base_url: str, 
                  port: int, 
                  auth_method: str, 
                  **kwargs) -> "EmbeddingServiceAsyncClient":
        """
        Create client with authentication configuration.
        
        Args:
            base_url: Base URL of the embedding service
            port: Port of the embedding service
            auth_method: Authentication method ("api_key", "jwt", "basic", "certificate")
            **kwargs: Additional authentication parameters
            
        Returns:
            EmbeddingServiceAsyncClient instance with authentication configured
            
        Examples:
            # API Key authentication
            client = EmbeddingServiceAsyncClient.with_auth(
                "http://localhost", 8001, "api_key", 
                api_keys={"user": "api_key_123"}
            )
            
            # JWT authentication
            client = EmbeddingServiceAsyncClient.with_auth(
                "http://localhost", 8001, "jwt",
                secret="secret", username="user", password="pass"
            )
            
            # Basic authentication
            client = EmbeddingServiceAsyncClient.with_auth(
                "http://localhost", 8001, "basic",
                username="user", password="pass"
            )
            
            # Certificate authentication
            client = EmbeddingServiceAsyncClient.with_auth(
                "https://localhost", 9443, "certificate",
                cert_file="certs/client.crt", key_file="keys/client.key"
            )
        """
        # Build configuration dictionary
        config_dict = {
            "server": {
                "host": base_url,
                "port": port
            },
            "client": {
                "timeout": kwargs.get("timeout", 30.0)
            },
            "auth": {
                "method": auth_method
            }
        }
        
        # Add authentication configuration based on method
        if auth_method == "api_key":
            if "api_keys" in kwargs:
                config_dict["auth"]["api_keys"] = kwargs["api_keys"]
            elif "api_key" in kwargs:
                config_dict["auth"]["api_keys"] = {"user": kwargs["api_key"]}
            else:
                raise ValueError("api_keys or api_key parameter required for api_key authentication")
        
        elif auth_method == "jwt":
            required_params = ["secret", "username", "password"]
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(f"{param} parameter required for jwt authentication")
            
            config_dict["auth"]["jwt"] = {
                "secret": kwargs["secret"],
                "username": kwargs["username"],
                "password": kwargs["password"],
                "expiry_hours": kwargs.get("expiry_hours", 24)
            }
        
        elif auth_method == "basic":
            required_params = ["username", "password"]
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(f"{param} parameter required for basic authentication")
            
            config_dict["auth"]["basic"] = {
                "username": kwargs["username"],
                "password": kwargs["password"]
            }
        
        elif auth_method == "certificate":
            required_params = ["cert_file", "key_file"]
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(f"{param} parameter required for certificate authentication")
            
            config_dict["auth"]["certificate"] = {
                "cert_file": kwargs["cert_file"],
                "key_file": kwargs["key_file"]
            }
        
        else:
            raise ValueError(f"Unsupported authentication method: {auth_method}")
        
        # Add SSL configuration if provided or if using HTTPS
        ssl_enabled = kwargs.get("ssl_enabled")
        if ssl_enabled is None:
            ssl_enabled = base_url.startswith("https://")
        
        if ssl_enabled or any(key in kwargs for key in ["ca_cert_file", "cert_file", "key_file", "ssl_enabled"]):
            config_dict["ssl"] = {
                "enabled": ssl_enabled,
                "verify_mode": kwargs.get("verify_mode", "CERT_REQUIRED"),
                "check_hostname": kwargs.get("check_hostname", True),
                "check_expiry": kwargs.get("check_expiry", True)
            }
            
            if "ca_cert_file" in kwargs:
                config_dict["ssl"]["ca_cert_file"] = kwargs["ca_cert_file"]
            
            if "cert_file" in kwargs:
                config_dict["ssl"]["cert_file"] = kwargs["cert_file"]
            
            if "key_file" in kwargs:
                config_dict["ssl"]["key_file"] = kwargs["key_file"]
        
        return cls(config_dict=config_dict)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for requests.
        
        Returns:
            Dictionary of authentication headers
        """
        if not self.auth_manager:
            return {}
        
        auth_method = self.auth_manager.get_auth_method()
        if auth_method == "none":
            return {}
        
        # Get authentication parameters from config
        auth_config = self.config_dict.get("auth", {}) if self.config_dict else {}
        if self.config:
            auth_config = self.config.get("auth", {})
        
        if auth_method == "api_key":
            api_keys = auth_config.get("api_keys", {})
            # Use first available API key
            for user_id, api_key in api_keys.items():
                return self.auth_manager.get_auth_headers("api_key", api_key=api_key)
        
        elif auth_method == "jwt":
            jwt_config = auth_config.get("jwt", {})
            username = jwt_config.get("username")
            password = jwt_config.get("password")
            if username and password:
                # Create JWT token
                token = self.auth_manager.create_jwt_token(username, ["user"])
                return self.auth_manager.get_auth_headers("jwt", token=token)
        
        elif auth_method == "basic":
            basic_config = auth_config.get("basic", {})
            username = basic_config.get("username")
            password = basic_config.get("password")
            if username and password:
                return self.auth_manager.get_auth_headers("basic", username=username, password=password)
        
        return {}
    
    def is_authenticated(self) -> bool:
        """
        Check if client is configured for authentication.
        
        Returns:
            True if authentication is configured, False otherwise
        """
        return self.auth_manager is not None and self.auth_manager.is_auth_enabled()
    
    def get_auth_method(self) -> str:
        """
        Get current authentication method.
        
        Returns:
            Authentication method name or "none" if not configured
        """
        if not self.auth_manager:
            return "none"
        return self.auth_manager.get_auth_method()
    
    def is_ssl_enabled(self) -> bool:
        """
        Check if SSL/TLS is enabled.
        
        Returns:
            True if SSL/TLS is enabled, False otherwise
        """
        if not self.ssl_manager:
            return False
        return self.ssl_manager.is_ssl_enabled()
    
    def is_mtls_enabled(self) -> bool:
        """
        Check if mTLS (mutual TLS) is enabled.
        
        Returns:
            True if mTLS is enabled, False otherwise
        """
        if not self.ssl_manager:
            return False
        return self.ssl_manager.is_mtls_enabled()
    
    def get_ssl_config(self) -> Dict[str, Any]:
        """
        Get current SSL configuration.
        
        Returns:
            Dictionary with SSL configuration or empty dict if not configured
        """
        if not self.ssl_manager:
            return {}
        return self.ssl_manager.get_ssl_config()
    
    def validate_ssl_config(self) -> List[str]:
        """
        Validate SSL configuration.
        
        Returns:
            List of validation errors
        """
        if not self.ssl_manager:
            return []
        return self.ssl_manager.validate_ssl_config()
    
    def get_supported_ssl_protocols(self) -> List[str]:
        """
        Get list of supported SSL/TLS protocols.
        
        Returns:
            List of supported protocol names
        """
        if not self.ssl_manager:
            return []
        return self.ssl_manager.get_supported_protocols() 