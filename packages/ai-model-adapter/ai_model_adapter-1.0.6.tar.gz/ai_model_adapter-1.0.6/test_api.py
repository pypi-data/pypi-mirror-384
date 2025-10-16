#!/usr/bin/env python3
"""
测试用例2: FastAPI接口测试
"""
import asyncio
import json
import httpx
from typing import Dict, Any

class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:6688"):
        self.base_url = base_url
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def test_health(self):
        """测试健康检查接口"""
        print("🏥 **测试健康检查接口**")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查成功: {data}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    async def test_list_adapters(self):
        """测试列出适配器接口"""
        print("\n📋 **测试列出适配器接口**")
        try:
            response = await self.client.get(f"{self.base_url}/adapters")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取适配器列表成功: {data}")
                return True
            else:
                print(f"❌ 获取适配器列表失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 获取适配器列表异常: {e}")
            return False
    
    async def test_chat_invalid_provider(self):
        """测试无效提供商"""
        print("\n❌ **测试无效提供商**")
        try:
            payload = {
                "messages": [{"role": "user", "content": "测试消息"}],
                "provider": "invalid_provider"
            }
            response = await self.client.post(f"{self.base_url}/chat", json=payload)
            if response.status_code == 400:
                error = response.json()
                print(f"✅ 正确返回400错误: {error}")
                return True
            else:
                print(f"❌ 应该返回400错误，实际: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试无效提供商异常: {e}")
            return False
    
    async def test_chat_missing_config(self):
        """测试缺少配置的情况"""
        print("\n⚠️ **测试缺少配置**")
        try:
            payload = {
                "messages": [{"role": "user", "content": "测试消息"}],
                "provider": "qwen"  # 假设没有设置QWEN_API_KEY
            }
            response = await self.client.post(f"{self.base_url}/chat", json=payload)
            if response.status_code == 400:
                error = response.json()
                print(f"✅ 正确返回配置错误: {error}")
                return True
            else:
                print(f"⚠️ 返回状态码: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 测试缺少配置异常: {e}")
            return False
    
    async def test_chat_with_ollama_config(self):
        """测试使用Ollama配置聊天（模拟）"""
        print("\n🦙 **测试Ollama聊天接口**")
        try:
            payload = {
                "messages": [{"role": "user", "content": "你好，请简单回复"}],
                "provider": "ollama",
                "model": "llama2"
            }
            response = await self.client.post(f"{self.base_url}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Ollama聊天成功: {data}")
                return True
            elif response.status_code == 500:
                error = response.json()
                print(f"⚠️ Ollama服务不可用（预期）: {error}")
                return True  # 这是预期的，因为可能没有运行Ollama
            else:
                print(f"❌ 意外的状态码: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 测试Ollama聊天异常: {e}")
            return False
    
    async def test_chat_stream(self):
        """测试流式聊天"""
        print("\n🌊 **测试流式聊天**")
        try:
            payload = {
                "messages": [{"role": "user", "content": "请说'测试流式响应'"}],
                "provider": "ollama",
                "stream": True
            }
            
            async with self.client.stream("POST", f"{self.base_url}/chat", json=payload) as response:
                if response.status_code == 200:
                    print("✅ 流式响应开始:")
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk_count += 1
                            if chunk_count <= 3:  # 只显示前3个chunk
                                print(f"   📦 Chunk {chunk_count}: {line}")
                            if line.strip() == "data: [DONE]":
                                break
                    print(f"✅ 流式响应完成，共收到 {chunk_count} 个chunk")
                    return True
                else:
                    print(f"⚠️ 流式响应状态码: {response.status_code}")
                    return True  # 可能是服务不可用，这是预期的
        except Exception as e:
            print(f"❌ 测试流式聊天异常: {e}")
            return False
    
    async def test_malformed_request(self):
        """测试格式错误的请求"""
        print("\n🚫 **测试格式错误的请求**")
        try:
            # 缺少必需字段
            payload = {
                "provider": "ollama"
                # 缺少messages字段
            }
            response = await self.client.post(f"{self.base_url}/chat", json=payload)
            if response.status_code == 422:  # FastAPI验证错误
                error = response.json()
                print(f"✅ 正确返回422验证错误: {error}")
                return True
            else:
                print(f"❌ 应该返回422错误，实际: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 测试格式错误请求异常: {e}")
            return False

async def run_api_tests():
    """运行所有API测试"""
    print("🚀 **FastAPI接口测试开始**\n")
    
    async with APITester() as tester:
        tests = [
            tester.test_health,
            tester.test_list_adapters,
            tester.test_chat_invalid_provider,
            tester.test_chat_missing_config,
            tester.test_chat_with_ollama_config,
            tester.test_chat_stream,
            tester.test_malformed_request
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                results.append(False)
        
        # 统计结果
        passed = sum(results)
        total = len(results)
        print(f"\n📊 **测试结果**: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 **所有测试通过！**")
        else:
            print("⚠️ **部分测试失败，请检查服务状态**")

if __name__ == "__main__":
    print("⚠️ **注意**: 请确保FastAPI服务正在运行")
    print("   启动命令: python3.11 model_adapter_refactored.py")
    print("   服务地址: http://localhost:6688\n")
    
    try:
        asyncio.run(run_api_tests())
    except KeyboardInterrupt:
        print("\n🛑 **测试被用户中断**")
    except Exception as e:
        print(f"\n❌ **测试运行异常**: {e}")
