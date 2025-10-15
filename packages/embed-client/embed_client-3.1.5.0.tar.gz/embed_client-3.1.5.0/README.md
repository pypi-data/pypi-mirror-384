# embed-client

Асинхронный клиент для Embedding Service API с поддержкой всех режимов безопасности.

## Возможности

- ✅ **Асинхронный API** - полная поддержка async/await
- ✅ **Все режимы безопасности** - HTTP, HTTPS, mTLS
- ✅ **Аутентификация** - API Key, JWT, Basic Auth, Certificate
- ✅ **SSL/TLS поддержка** - полная интеграция с mcp_security_framework
- ✅ **Конфигурация** - файлы конфигурации, переменные окружения, аргументы
- ✅ **Обратная совместимость** - API формат не изменился, добавлена только безопасность
- ✅ **Типизация** - 100% type-annotated код
- ✅ **Тестирование** - 84+ тестов с полным покрытием

## Quick Start: Примеры запуска

### Базовое использование

**Вариант 1: через аргументы командной строки**

```sh
# HTTP без аутентификации
python embed_client/example_async_usage.py --base-url http://localhost --port 8001

# HTTP с API ключом
python embed_client/example_async_usage.py --base-url http://localhost --port 8001 \
  --auth-method api_key --api-key admin_key_123

# HTTPS с SSL
python embed_client/example_async_usage.py --base-url https://localhost --port 9443 \
  --ssl-verify-mode CERT_REQUIRED

# mTLS с сертификатами
python embed_client/example_async_usage.py --base-url https://localhost --port 9443 \
  --cert-file certs/client.crt --key-file keys/client.key --ca-cert-file certs/ca.crt
```

**Вариант 2: через переменные окружения**

```sh
export EMBED_CLIENT_BASE_URL=http://localhost
export EMBED_CLIENT_PORT=8001
export EMBED_CLIENT_AUTH_METHOD=api_key
export EMBED_CLIENT_API_KEY=admin_key_123
python embed_client/example_async_usage.py
```

**Вариант 3: через файл конфигурации**

```sh
python embed_client/example_async_usage.py --config configs/https_token.json
```

### Режимы безопасности

#### 1. HTTP (без аутентификации)
```python
from embed_client.async_client import EmbeddingServiceAsyncClient

client = EmbeddingServiceAsyncClient(
    base_url="http://localhost",
    port=8001
)
```

#### 2. HTTP + Token
```python
from embed_client.config import ClientConfig

# API Key
config = ClientConfig.create_http_token_config(
    "http://localhost", 8001, {"user": "api_key_123"}
)

# JWT
config = ClientConfig.create_http_jwt_config(
    "http://localhost", 8001, "secret", "username", "password"
)

# Basic Auth
config = ClientConfig.create_http_basic_config(
    "http://localhost", 8001, "username", "password"
)
```

#### 3. HTTPS
```python
config = ClientConfig.create_https_config(
    "https://localhost", 9443,
    ca_cert_file="certs/ca.crt"
)
```

#### 4. mTLS (взаимная аутентификация)
```python
config = ClientConfig.create_mtls_config(
    "https://localhost", 9443,
    cert_file="certs/client.crt",
    key_file="keys/client.key",
    ca_cert_file="certs/ca.crt"
)
```

### Программное использование

```python
import asyncio
from embed_client.async_client import EmbeddingServiceAsyncClient
from embed_client.config import ClientConfig

async def main():
    # Создание конфигурации
    config = ClientConfig.create_http_token_config(
        "http://localhost", 8001, {"user": "api_key_123"}
    )
    
    # Использование клиента
    async with EmbeddingServiceAsyncClient.from_config(config) as client:
        # Проверка статуса
        print(f"Аутентификация: {client.get_auth_method()}")
        print(f"SSL включен: {client.is_ssl_enabled()}")
        print(f"mTLS включен: {client.is_mtls_enabled()}")
        
        # Выполнение запроса
        result = await client.cmd("embed", params={"texts": ["hello world"]})
        
        # Извлечение данных
        embeddings = client.extract_embeddings(result)
        texts = client.extract_texts(result)
        tokens = client.extract_tokens(result)
        bm25_tokens = client.extract_bm25_tokens(result)
        
        print(f"Эмбеддинги: {embeddings}")
        print(f"Тексты: {texts}")
        print(f"Токены: {tokens}")
        print(f"BM25 токены: {bm25_tokens}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Установка

```bash
# Установка из PyPI
pip install embed-client

# Установка в режиме разработки
git clone <repository>
cd embed-client
pip install -e .
```

## Зависимости

- `aiohttp` - асинхронные HTTP запросы
- `PyJWT>=2.0.0` - JWT токены
- `cryptography>=3.0.0` - криптография и сертификаты
- `pydantic>=2.0.0` - валидация конфигурации

## Тестирование

```bash
# Запуск всех тестов
pytest tests/

# Запуск тестов с покрытием
pytest tests/ --cov=embed_client

# Запуск конкретных тестов
pytest tests/test_async_client.py -v
pytest tests/test_config.py -v
pytest tests/test_auth.py -v
pytest tests/test_ssl_manager.py -v
```

## Документация

- [Формат API и режимы безопасности](docs/api_format.md)
- [Примеры использования](embed_client/example_async_usage.py)
- [Примеры на русском](embed_client/example_async_usage_ru.py)

## Безопасность

### Рекомендации

1. **Используйте HTTPS** для продакшена
2. **Включите проверку сертификатов** (CERT_REQUIRED)
3. **Используйте mTLS** для критически важных систем
4. **Регулярно обновляйте сертификаты**
5. **Храните приватные ключи в безопасном месте**

### Поддерживаемые протоколы

- TLS 1.2
- TLS 1.3
- SSL 3.0 (устаревший, не рекомендуется)

## Лицензия

MIT License

## Автор

**Vasiliy Zdanovskiy**  
Email: vasilyvz@gmail.com

---

**Важно:**
- Используйте `--base-url` (через дефис), а не `--base_url` (через подчеркивание).
- Значение base_url должно содержать `http://` или `https://`.
- Аргументы должны быть отдельными (через пробел), а не через `=`.