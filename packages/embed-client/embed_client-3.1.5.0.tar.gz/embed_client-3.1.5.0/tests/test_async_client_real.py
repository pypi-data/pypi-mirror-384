import pytest
import pytest_asyncio
from embed_client.async_client import (
    EmbeddingServiceAsyncClient, 
    EmbeddingServiceAPIError, 
    EmbeddingServiceHTTPError,
    EmbeddingServiceConnectionError,
    EmbeddingServiceTimeoutError,
    EmbeddingServiceJSONError,
    EmbeddingServiceConfigError
)
import asyncio

# Test configurations for different security modes
TEST_CONFIGS = {
    "http": {
        "base_url": "http://localhost",
        "port": 8001,
        "config_dict": {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "none"},
            "ssl": {"enabled": False}
        }
    },
    "https": {
        "base_url": "http://localhost", 
        "port": 10043,
        "config_dict": {
            "server": {"host": "http://localhost", "port": 10043},
            "auth": {"method": "none"},
            "ssl": {
                "enabled": False
            }
        }
    },
    "mtls": {
        "base_url": "http://localhost",
        "port": 8001,
        "config_dict": {
            "server": {"host": "http://localhost", "port": 8001},
            "auth": {"method": "certificate"},
            "ssl": {
                "enabled": False
            },
            "security": {
                "enabled": True,
                "tokens": {},
                "roles": {
                    "admin": ["read", "write", "delete", "admin"],
                    "user": ["read", "write"],
                    "readonly": ["read"]
                }
            }
        }
    }
}

async def is_service_available(security_mode="http"):
    """Check if service is available for the given security mode."""
    config = TEST_CONFIGS[security_mode]
    try:
        async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
            await client.health()
        return True
    except Exception:
        return False

@pytest_asyncio.fixture
async def real_client():
    """Default HTTP client fixture."""
    config = TEST_CONFIGS["http"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        yield client

@pytest_asyncio.fixture
async def real_https_client():
    """HTTPS client fixture."""
    config = TEST_CONFIGS["https"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        yield client

@pytest_asyncio.fixture
async def real_mtls_client():
    """mTLS client fixture."""
    config = TEST_CONFIGS["mtls"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        yield client

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_health(real_client):
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "error")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_health_https(real_https_client):
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "error")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_health_mtls(real_mtls_client):
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.health()
    assert "status" in result
    assert result["status"] in ("ok", "error")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi(real_client):
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.get_openapi_schema()
    assert "openapi" in result
    assert result["openapi"].startswith("3.")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi_https(real_https_client):
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.get_openapi_schema()
    assert "openapi" in result
    assert result["openapi"].startswith("3.")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_openapi_mtls(real_mtls_client):
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.get_openapi_schema()
    assert "openapi" in result
    assert result["openapi"].startswith("3.")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_get_commands(real_client):
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.get_commands()
    assert isinstance(result, dict)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_get_commands_https(real_https_client):
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.get_commands()
    assert isinstance(result, dict)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_get_commands_mtls(real_mtls_client):
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.get_commands()
    assert isinstance(result, dict)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_help(real_client):
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    result = await real_client.cmd("help")
    assert isinstance(result, dict)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_help_https(real_https_client):
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    result = await real_https_client.cmd("help")
    assert isinstance(result, dict)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_help_mtls(real_mtls_client):
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    result = await real_mtls_client.cmd("help")
    assert isinstance(result, dict)

def extract_vectors(result):
    """Extract vectors from API response, supporting both old and new formats."""
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
                        pytest.fail(f"Invalid item format in new API response: {item}")
                return embeddings
    
    pytest.fail(f"Cannot extract embeddings from response: {result}")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_vector(real_client):
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await real_client.cmd("embed", params=params)
    vectors = extract_vectors(result)
    assert isinstance(vectors, list)
    assert len(vectors) == len(texts)
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(isinstance(x, (float, int)) for vec in vectors for x in vec)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_vector_https(real_https_client):
    if not await is_service_available("https"):
        pytest.skip("Real HTTPS service on localhost:8443 is not available.")
    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await real_https_client.cmd("embed", params=params)
    vectors = extract_vectors(result)
    assert isinstance(vectors, list)
    assert len(vectors) == len(texts)
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(isinstance(x, (float, int)) for vec in vectors for x in vec)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_vector_mtls(real_mtls_client):
    if not await is_service_available("mtls"):
        pytest.skip("Real mTLS service on localhost:8001 is not available.")
    texts = ["hello world", "test embedding"]
    params = {"texts": texts}
    result = await real_mtls_client.cmd("embed", params=params)
    vectors = extract_vectors(result)
    assert isinstance(vectors, list)
    assert len(vectors) == len(texts)
    assert all(isinstance(vec, list) for vec in vectors)
    assert all(isinstance(x, (float, int)) for vec in vectors for x in vec)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_embed_empty_texts(real_client):
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    with pytest.raises(EmbeddingServiceAPIError) as excinfo:
        await real_client.cmd("embed", params={"texts": []})
    assert "Empty texts list provided" in str(excinfo.value)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_cmd_invalid_command(real_client):
    if not await is_service_available():
        pytest.skip("Real service on localhost:8001 is not available.")
    with pytest.raises(EmbeddingServiceAPIError):
        await real_client.cmd("not_a_command")

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_invalid_endpoint():
    if not await is_service_available("http"):
        pytest.skip("Real service on localhost:8001 is not available.")
    config = TEST_CONFIGS["http"]
    async with EmbeddingServiceAsyncClient(config_dict=config["config_dict"]) as client:
        with pytest.raises(EmbeddingServiceHTTPError):
            # Пробуем обратиться к несуществующему endpoint
            url = f"{config['base_url']}:{config['port']}/notfound"
            async with client._session.get(url) as resp:
                await client._raise_for_status(resp)

@pytest.mark.asyncio
async def test_explicit_close_real():
    client = EmbeddingServiceAsyncClient(base_url="http://localhost", port=8001)
    await client.__aenter__()
    await client.close()
    await client.close()  # Should not raise 

# INTEGRATION TESTS: используют реальный сервис http://localhost:8001 