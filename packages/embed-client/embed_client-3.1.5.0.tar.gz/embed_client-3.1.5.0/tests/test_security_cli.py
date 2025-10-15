#!/usr/bin/env python3
"""
Test Security CLI Application
Tests all 8 security modes using the security CLI.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embed_client.security_cli import SecurityCLI, create_config_from_security_mode


class SecurityCLITester:
    """Tester for all 8 security modes."""
    
    def __init__(self):
        self.test_results = {}
        
    async def test_http_mode(self):
        """Test HTTP mode."""
        print("🔍 Testing HTTP mode...")
        
        config = create_config_from_security_mode("http", "localhost", 10001)
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["hello world"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ HTTP mode test passed")
                return True
            else:
                print("❌ HTTP mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ HTTP mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_http_token_mode(self):
        """Test HTTP + Token mode."""
        print("🔍 Testing HTTP + Token mode...")
        
        config = create_config_from_security_mode("http_token", "localhost", 10002, api_key="admin-secret-key")
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["authenticated text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ HTTP + Token mode test passed")
                return True
            else:
                print("❌ HTTP + Token mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ HTTP + Token mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_http_token_roles_mode(self):
        """Test HTTP + Token + Roles mode."""
        print("🔍 Testing HTTP + Token + Roles mode...")
        
        config = create_config_from_security_mode("http_token_roles", "localhost", 10003, api_key="admin-secret-key")
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["role-based text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ HTTP + Token + Roles mode test passed")
                return True
            else:
                print("❌ HTTP + Token + Roles mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ HTTP + Token + Roles mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_https_mode(self):
        """Test HTTPS mode."""
        print("🔍 Testing HTTPS mode...")
        
        config = create_config_from_security_mode(
            "https", "localhost", 10011,
            cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            key_file="/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key"
        )
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["https text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ HTTPS mode test passed")
                return True
            else:
                print("❌ HTTPS mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ HTTPS mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_https_token_mode(self):
        """Test HTTPS + Token mode."""
        print("🔍 Testing HTTPS + Token mode...")
        
        config = create_config_from_security_mode(
            "https_token", "localhost", 10012,
            api_key="admin-secret-key",
            cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            key_file="/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key"
        )
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["https authenticated text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ HTTPS + Token mode test passed")
                return True
            else:
                print("❌ HTTPS + Token mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ HTTPS + Token mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_https_token_roles_mode(self):
        """Test HTTPS + Token + Roles mode."""
        print("🔍 Testing HTTPS + Token + Roles mode...")
        
        config = create_config_from_security_mode(
            "https_token_roles", "localhost", 10013,
            api_key="admin-secret-key",
            cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.crt",
            key_file="/home/vasilyvz/projects/embed-client/mtls_certificates/server/embedding-service.key"
        )
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["https role-based text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ HTTPS + Token + Roles mode test passed")
                return True
            else:
                print("❌ HTTPS + Token + Roles mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ HTTPS + Token + Roles mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_mtls_mode(self):
        """Test mTLS mode."""
        print("🔍 Testing mTLS mode...")
        
        config = create_config_from_security_mode(
            "mtls", "localhost", 10021,
            cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.crt",
            key_file="/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.key",
            ca_cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt"
        )
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["mtls text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ mTLS mode test passed")
                return True
            else:
                print("❌ mTLS mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ mTLS mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_mtls_roles_mode(self):
        """Test mTLS + Roles mode."""
        print("🔍 Testing mTLS + Roles mode...")
        
        config = create_config_from_security_mode(
            "mtls_roles", "localhost", 10022,
            cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.crt",
            key_file="/home/vasilyvz/projects/embed-client/mtls_certificates/client/embedding-service.key",
            ca_cert_file="/home/vasilyvz/projects/embed-client/mtls_certificates/ca/ca.crt"
        )
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            # Test health
            health_ok = await cli.health_check()
            if not health_ok:
                return False
            
            # Test vectorization
            texts = ["mtls role-based text"]
            embeddings = await cli.vectorize_texts(texts, "json")
            
            if embeddings and len(embeddings) == len(texts):
                print("✅ mTLS + Roles mode test passed")
                return True
            else:
                print("❌ mTLS + Roles mode vectorization failed")
                return False
                
        except Exception as e:
            print(f"❌ mTLS + Roles mode test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def test_output_formats(self):
        """Test different output formats."""
        print("🔍 Testing output formats...")
        
        config = create_config_from_security_mode("http", "localhost", 8001)
        cli = SecurityCLI()
        
        try:
            if not await cli.connect(config):
                return False
            
            texts = ["format test"]
            
            # Test JSON format
            print("Testing JSON format...")
            embeddings_json = await cli.vectorize_texts(texts, "json")
            
            # Test CSV format
            print("Testing CSV format...")
            embeddings_csv = await cli.vectorize_texts(texts, "csv")
            
            # Test vectors format
            print("Testing vectors format...")
            embeddings_vectors = await cli.vectorize_texts(texts, "vectors")
            
            if all([embeddings_json, embeddings_csv, embeddings_vectors]):
                print("✅ Output formats test passed")
                return True
            else:
                print("❌ Output formats test failed")
                return False
                
        except Exception as e:
            print(f"❌ Output formats test failed: {e}")
            return False
        finally:
            await cli.disconnect()
    
    async def run_all_tests(self):
        """Run all security mode tests."""
        print("🧪 Starting comprehensive security mode tests...")
        print("=" * 60)
        
        tests = [
            ("http", self.test_http_mode),
            ("http_token", self.test_http_token_mode),
            ("http_token_roles", self.test_http_token_roles_mode),
            ("https", self.test_https_mode),
            ("https_token", self.test_https_token_mode),
            ("https_token_roles", self.test_https_token_roles_mode),
            ("mtls", self.test_mtls_mode),
            ("mtls_roles", self.test_mtls_roles_mode),
            ("output_formats", self.test_output_formats),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name} test...")
            success = await test_func()
            self.test_results[test_name] = success
        
        # Print results
        print("\n📊 Security Mode Test Results:")
        print("=" * 50)
        for test_name, success in self.test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:20} {status}")
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for success in self.test_results.values() if success)
        failed_tests = total_tests - passed_tests
        
        print(f"\n🎉 Security testing completed!")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        if failed_tests > 0:
            print(f"❌ {failed_tests} tests failed")
        else:
            print("✅ All security mode tests passed!")


async def main():
    """Main test function."""
    tester = SecurityCLITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
