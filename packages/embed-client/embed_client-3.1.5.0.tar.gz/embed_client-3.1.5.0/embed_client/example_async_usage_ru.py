"""
Пример использования EmbeddingServiceAsyncClient со всеми режимами безопасности и ClientFactory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

ИСПОЛЬЗОВАНИЕ:
    # Базовое использование без аутентификации
    python embed_client/example_async_usage_ru.py --base-url http://localhost --port 8001
    
    # С аутентификацией по API ключу
    python embed_client/example_async_usage_ru.py --base-url http://localhost --port 8001 --auth-method api_key --api-key your_key
    
    # С JWT аутентификацией
    python embed_client/example_async_usage_ru.py --base-url http://localhost --port 8001 --auth-method jwt --jwt-secret secret --jwt-username user
    
    # С базовой аутентификацией
    python embed_client/example_async_usage_ru.py --base-url http://localhost --port 8001 --auth-method basic --username user --password pass
    
    # С файлом конфигурации
    python embed_client/example_async_usage_ru.py --config configs/http_token.json
    
    # С переменными окружения
    export EMBED_CLIENT_BASE_URL=http://localhost
    export EMBED_CLIENT_PORT=8001
    export EMBED_CLIENT_AUTH_METHOD=api_key
    export EMBED_CLIENT_API_KEY=your_key
    python embed_client/example_async_usage_ru.py

ПРИМЕРЫ РЕЖИМОВ БЕЗОПАСНОСТИ:
    # 1. HTTP - обычный HTTP без аутентификации
    python embed_client/example_async_usage_ru.py --base-url http://localhost --port 8001
    
    # 2. HTTP + Token - HTTP с аутентификацией по API ключу
    python embed_client/example_async_usage_ru.py --base-url http://localhost --port 8001 --auth-method api_key --api-key admin_key_123
    
    # 3. HTTPS - HTTPS с проверкой сертификатов сервера
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 9443
    
    # 4. HTTPS + Token - HTTPS с сертификатами сервера + аутентификация
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 9443 --auth-method jwt --jwt-secret secret --jwt-username admin
    
    # 5. mTLS - взаимная TLS с сертификатами клиента и сервера
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key
    
    # 6. mTLS + Roles - mTLS с контролем доступа на основе ролей
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key --roles admin,user

ПРИМЕРЫ ФАБРИКИ КЛИЕНТОВ:
    # Автоматическое определение режима безопасности
    python embed_client/example_async_usage_ru.py --factory-mode auto --base-url https://localhost --port 9443 --auth-method api_key --api-key key
    
    # Создание конкретного режима безопасности
    python embed_client/example_async_usage_ru.py --factory-mode https_token --base-url https://localhost --port 9443 --auth-method basic --username user --password pass
    
    # mTLS с фабрикой
    python embed_client/example_async_usage_ru.py --factory-mode mtls --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key

ПРИМЕРЫ SSL/TLS:
    # HTTPS с отключенной проверкой SSL
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 9443 --ssl-verify-mode CERT_NONE
    
    # mTLS с пользовательским CA сертификатом
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 8443 --cert-file mtls_certificates/client/embedding-service.crt --key-file mtls_certificates/client/embedding-service.key --ca-cert-file mtls_certificates/ca/ca.crt
    
    # HTTPS с пользовательскими настройками SSL
    python embed_client/example_async_usage_ru.py --base-url https://localhost --port 9443 --ssl-verify-mode CERT_REQUIRED --ssl-check-hostname --ssl-check-expiry

ПРИМЕРЫ КОНФИГУРАЦИИ:
    # Использование файла конфигурации
    python embed_client/example_async_usage_ru.py --config configs/https_token.json
    
    # Использование переменных окружения
    export EMBED_CLIENT_BASE_URL=https://secure.example.com
    export EMBED_CLIENT_PORT=9443
    export EMBED_CLIENT_AUTH_METHOD=api_key
    export EMBED_CLIENT_API_KEY=production_key
    python embed_client/example_async_usage_ru.py

Пример явного закрытия сессии:
    import asyncio
    from embed_client.async_client import EmbeddingServiceAsyncClient
    from embed_client.config import ClientConfig
    from embed_client.client_factory import ClientFactory, create_client
    
    async def main():
        # Метод 1: Прямое создание клиента
        client = EmbeddingServiceAsyncClient('http://localhost', 8001)
        await client.close()
        
        # Метод 2: Использование конфигурации
        config = ClientConfig()
        config.configure_server('http://localhost', 8001)
        client = EmbeddingServiceAsyncClient.from_config(config)
        await client.close()
        
        # Метод 3: Использование фабрики с автоматическим определением
        client = create_client('https://localhost', 9443, auth_method='api_key', api_key='key')
        await client.close()
        
        # Метод 4: Использование конкретного метода фабрики
        client = ClientFactory.create_https_token_client(
            'https://localhost', 9443, 'api_key', api_key='key'
        )
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
    """Парсинг аргументов командной строки и переменных окружения для конфигурации клиента."""
    parser = argparse.ArgumentParser(description="Пример Embedding Service Async Client - Все режимы безопасности")
    
    # Базовые параметры подключения
    parser.add_argument("--base-url", "-b", help="Базовый URL сервиса эмбеддингов")
    parser.add_argument("--port", "-p", type=int, help="Порт сервиса эмбеддингов")
    parser.add_argument("--config", "-c", help="Путь к файлу конфигурации")
    
    # Режим фабрики клиентов
    parser.add_argument("--factory-mode", choices=["auto", "http", "http_token", "https", "https_token", "mtls", "mtls_roles"],
                       default="auto", help="Режим фабрики клиентов (auto для автоматического определения)")
    
    # Параметры аутентификации
    parser.add_argument("--auth-method", choices=["none", "api_key", "jwt", "basic", "certificate"], 
                       default="none", help="Метод аутентификации")
    parser.add_argument("--api-key", help="API ключ для аутентификации api_key")
    parser.add_argument("--jwt-secret", help="JWT секрет для аутентификации jwt")
    parser.add_argument("--jwt-username", help="JWT имя пользователя для аутентификации jwt")
    parser.add_argument("--jwt-password", help="JWT пароль для аутентификации jwt")
    parser.add_argument("--username", help="Имя пользователя для базовой аутентификации")
    parser.add_argument("--password", help="Пароль для базовой аутентификации")
    parser.add_argument("--cert-file", help="Файл сертификата для аутентификации certificate")
    parser.add_argument("--key-file", help="Файл ключа для аутентификации certificate")
    
    # Параметры SSL/TLS
    parser.add_argument("--ssl-verify-mode", choices=["CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED"], 
                       default="CERT_REQUIRED", help="Режим проверки SSL сертификатов")
    parser.add_argument("--ssl-check-hostname", action="store_true", default=True, 
                       help="Включить проверку имени хоста SSL")
    parser.add_argument("--ssl-check-expiry", action="store_true", default=True, 
                       help="Включить проверку срока действия SSL сертификатов")
    parser.add_argument("--ca-cert-file", help="Файл CA сертификата для проверки SSL")
    
    # Контроль доступа на основе ролей (для mTLS + Roles)
    parser.add_argument("--roles", help="Список ролей через запятую для режима mTLS + Roles")
    parser.add_argument("--role-attributes", help="JSON строка атрибутов ролей для режима mTLS + Roles")
    
    # Дополнительные параметры
    parser.add_argument("--timeout", type=float, default=30.0, help="Таймаут запроса в секундах")
    parser.add_argument("--demo-mode", action="store_true", help="Запуск в демо режиме (показать все режимы безопасности)")
    
    args = parser.parse_args()
    
    # Если предоставлен файл конфигурации, загружаем его
    if args.config:
        try:
            config = ClientConfig()
            config.load_config_file(args.config)
            return config
        except Exception as e:
            print(f"Ошибка загрузки файла конфигурации {args.config}: {e}")
            sys.exit(1)
    
    # Иначе строим конфигурацию из аргументов и переменных окружения
    base_url = args.base_url or os.environ.get("EMBED_CLIENT_BASE_URL", "http://localhost")
    port = args.port or int(os.environ.get("EMBED_CLIENT_PORT", "8001"))
    
    if not base_url or not port:
        print("Ошибка: base_url и port должны быть предоставлены через аргументы --base-url/--port или переменные окружения EMBED_CLIENT_BASE_URL/EMBED_CLIENT_PORT.")
        sys.exit(1)
    
    # Строим словарь конфигурации
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
    
    # Добавляем конфигурацию аутентификации
    if args.auth_method == "api_key":
        api_key = args.api_key or os.environ.get("EMBED_CLIENT_API_KEY")
        if api_key:
            config_dict["auth"]["api_keys"] = {"user": api_key}
        else:
            print("Предупреждение: API ключ не предоставлен для аутентификации api_key")
    
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
            print("Предупреждение: JWT учетные данные не полностью предоставлены")
    
    elif args.auth_method == "basic":
        username = args.username or os.environ.get("EMBED_CLIENT_USERNAME")
        password = args.password or os.environ.get("EMBED_CLIENT_PASSWORD")
        
        if username and password:
            config_dict["auth"]["basic"] = {
                "username": username,
                "password": password
            }
        else:
            print("Предупреждение: Учетные данные базовой аутентификации не полностью предоставлены")
    
    elif args.auth_method == "certificate":
        cert_file = args.cert_file or os.environ.get("EMBED_CLIENT_CERT_FILE")
        key_file = args.key_file or os.environ.get("EMBED_CLIENT_KEY_FILE")
        
        if cert_file and key_file:
            config_dict["auth"]["certificate"] = {
                "cert_file": cert_file,
                "key_file": key_file
            }
        else:
            print("Предупреждение: Файлы сертификатов не полностью предоставлены")
    
    # Добавляем конфигурацию SSL если используется HTTPS или предоставлены SSL параметры
    if base_url.startswith("https://") or args.ssl_verify_mode != "CERT_REQUIRED" or args.ca_cert_file:
        config_dict["ssl"] = {
            "enabled": True,
            "verify_mode": args.ssl_verify_mode,
            "check_hostname": args.ssl_check_hostname,
            "check_expiry": args.ssl_check_expiry
        }
        
        if args.ca_cert_file:
            config_dict["ssl"]["ca_cert_file"] = args.ca_cert_file
        
        # Добавляем клиентские сертификаты для mTLS
        if args.cert_file:
            config_dict["ssl"]["cert_file"] = args.cert_file
        if args.key_file:
            config_dict["ssl"]["key_file"] = args.key_file
    
    # Добавляем контроль доступа на основе ролей для mTLS + Roles
    if args.roles:
        roles = [role.strip() for role in args.roles.split(",")]
        config_dict["roles"] = roles
    
    if args.role_attributes:
        try:
            role_attributes = json.loads(args.role_attributes)
            config_dict["role_attributes"] = role_attributes
        except json.JSONDecodeError:
            print("Предупреждение: Неверный JSON в role_attributes")
    
    return config_dict


def extract_embeddings(result):
    """Извлечение эмбеддингов из ответа API, поддерживая старый и новый форматы."""
    # Обработка прямого поля embeddings (совместимость со старым форматом)
    if "embeddings" in result:
        return result["embeddings"]
    
    # Обработка обертки result
    if "result" in result:
        res = result["result"]
        
        # Обработка прямого списка в result (старый формат)
        if isinstance(res, list):
            return res
        
        if isinstance(res, dict):
            # Обработка старого формата: result.embeddings
            if "embeddings" in res:
                return res["embeddings"]
            
            # Обработка старого формата: result.data.embeddings
            if "data" in res and isinstance(res["data"], dict) and "embeddings" in res["data"]:
                return res["data"]["embeddings"]
            
            # Обработка нового формата: result.data[].embedding
            if "data" in res and isinstance(res["data"], list):
                embeddings = []
                for item in res["data"]:
                    if isinstance(item, dict) and "embedding" in item:
                        embeddings.append(item["embedding"])
                    else:
                        raise ValueError(f"Неверный формат элемента в новом ответе API: {item}")
                return embeddings
    
    raise ValueError(f"Не удается извлечь эмбеддинги из ответа: {result}")


async def run_client_examples(client):
    """Запуск примеров операций с клиентом."""
    # Проверка здоровья
    try:
        health = await client.health()
        print("Состояние сервиса:", health)
    except EmbeddingServiceError as e:
        print(f"Ошибка при проверке здоровья: {e}")
        return
    
    # Получение схемы OpenAPI
    try:
        schema = await client.get_openapi_schema()
        print(f"Версия схемы OpenAPI: {schema.get('info', {}).get('version', 'неизвестно')}")
    except EmbeddingServiceError as e:
        print(f"Ошибка получения схемы OpenAPI: {e}")
    
    # Получение доступных команд
    try:
        commands = await client.get_commands()
        print(f"Доступные команды: {commands}")
    except EmbeddingServiceError as e:
        print(f"Ошибка получения команд: {e}")
    
    # Тест генерации эмбеддингов
    try:
        texts = ["Привет, мир!", "Это тестовое предложение.", "Сервис эмбеддингов работает!"]
        result = await client.cmd("embed", {"texts": texts})
        
        if result.get("success"):
            embeddings = extract_embeddings(result)
            print(f"Сгенерировано {len(embeddings)} эмбеддингов")
            print(f"Размерность первого эмбеддинга: {len(embeddings[0]) if embeddings else 0}")
        else:
            print(f"Генерация эмбеддингов не удалась: {result.get('error', 'Неизвестная ошибка')}")
    except EmbeddingServiceError as e:
        print(f"Ошибка при генерации эмбеддингов: {e}")


async def demonstrate_security_modes():
    """Демонстрация всех режимов безопасности с использованием ClientFactory."""
    print("=== Демонстрация режимов безопасности ===")
    
    # 1. HTTP режим
    print("\n1. HTTP режим (без аутентификации, без SSL):")
    try:
        client = ClientFactory.create_http_client("http://localhost", 8001)
        print(f"  Создан HTTP клиент: {client.base_url}:{client.port}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        await client.close()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # 2. HTTP + Token режим
    print("\n2. HTTP + Token режим (HTTP с API ключом):")
    try:
        client = ClientFactory.create_http_token_client(
            "http://localhost", 8001, "api_key", api_key="demo_key"
        )
        print(f"  Создан HTTP + Token клиент: {client.base_url}:{client.port}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        print(f"  Метод аутентификации: {client.get_auth_method()}")
        await client.close()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # 3. HTTPS режим
    print("\n3. HTTPS режим (HTTPS с сертификатами сервера):")
    try:
        client = ClientFactory.create_https_client("https://localhost", 9443)
        print(f"  Создан HTTPS клиент: {client.base_url}:{client.port}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"  SSL конфигурация: {ssl_config}")
        await client.close()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # 4. HTTPS + Token режим
    print("\n4. HTTPS + Token режим (HTTPS с сертификатами сервера + аутентификация):")
    try:
        client = ClientFactory.create_https_token_client(
            "https://localhost", 9443, "basic", username="admin", password="secret"
        )
        print(f"  Создан HTTPS + Token клиент: {client.base_url}:{client.port}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        print(f"  Метод аутентификации: {client.get_auth_method()}")
        await client.close()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # 5. mTLS режим
    print("\n5. mTLS режим (взаимная TLS с сертификатами клиента и сервера):")
    try:
        client = ClientFactory.create_mtls_client(
            "https://localhost", "mtls_certificates/client/embedding-service.crt", "mtls_certificates/client/embedding-service.key", 8443
        )
        print(f"  Создан mTLS клиент: {client.base_url}:{client.port}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  mTLS включен: {client.is_mtls_enabled()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        await client.close()
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # 6. mTLS + Roles режим
    print("\n6. mTLS + Roles режим (mTLS с контролем доступа на основе ролей):")
    try:
        client = ClientFactory.create_mtls_roles_client(
            "https://localhost", "client_cert.pem", "client_key.pem", 9443,
            roles=["admin", "user"], role_attributes={"department": "IT"}
        )
        print(f"  Создан mTLS + Roles клиент: {client.base_url}:{client.port}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  mTLS включен: {client.is_mtls_enabled()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        await client.close()
    except Exception as e:
        print(f"  Ошибка: {e}")


async def demonstrate_automatic_detection():
    """Демонстрация автоматического определения режима безопасности."""
    print("\n=== Автоматическое определение режима безопасности ===")
    
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
            print(f"  {base_url} + {auth_method or 'none'} + {cert_file or 'no cert'} -> {mode} ({expected})")
        except Exception as e:
            print(f"  Ошибка определения режима для {base_url}: {e}")


async def main():
    try:
        config = get_params()
        
        # Проверяем, запрошен ли демо режим
        if hasattr(config, 'demo_mode') and config.demo_mode:
            await demonstrate_security_modes()
            await demonstrate_automatic_detection()
            return
        
        # Создаем клиент на основе режима фабрики
        if isinstance(config, ClientConfig):
            # Использование объекта конфигурации
            client = EmbeddingServiceAsyncClient.from_config(config)
        else:
            # Использование словаря конфигурации
            factory_mode = getattr(config, 'factory_mode', 'auto')
            
            if factory_mode == "auto":
                # Автоматическое определение
                client = create_client(
                    config["server"]["host"], 
                    config["server"]["port"],
                    auth_method=config["auth"]["method"],
                    **{k: v for k, v in config.items() if k not in ["server", "auth", "ssl", "client"]}
                )
            else:
                # Конкретный метод фабрики
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
        
        print(f"Конфигурация клиента:")
        print(f"  Базовый URL: {client.base_url}")
        print(f"  Порт: {client.port}")
        print(f"  Аутентификация: {client.get_auth_method()}")
        print(f"  Аутентифицирован: {client.is_authenticated()}")
        if client.is_authenticated():
            headers = client.get_auth_headers()
            print(f"  Заголовки аутентификации: {headers}")
        print(f"  SSL включен: {client.is_ssl_enabled()}")
        print(f"  mTLS включен: {client.is_mtls_enabled()}")
        if client.is_ssl_enabled():
            ssl_config = client.get_ssl_config()
            print(f"  SSL конфигурация: {ssl_config}")
            protocols = client.get_supported_ssl_protocols()
            print(f"  Поддерживаемые SSL протоколы: {protocols}")
        print()
        
        # Пример явного открытия/закрытия
        print("Пример явного открытия/закрытия сессии:")
        await client.close()
        print("Сессия закрыта явно (пример ручного закрытия).\n")
        
        # Использование контекстного менеджера
        if isinstance(config, ClientConfig):
            async with EmbeddingServiceAsyncClient.from_config(config) as client:
                await run_client_examples(client)
        else:
            async with EmbeddingServiceAsyncClient(config_dict=config) as client:
                await run_client_examples(client)

    except EmbeddingServiceConfigError as e:
        print(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())