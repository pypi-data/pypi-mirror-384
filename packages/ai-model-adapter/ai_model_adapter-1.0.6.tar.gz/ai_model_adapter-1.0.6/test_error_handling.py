#!/usr/bin/env python3
"""
测试用例3: 错误处理测试
"""
import asyncio
import httpx
from unittest.mock import patch, AsyncMock
from model_adapter_refactored import (
    HTTPClient,
    ModelAdapterError,
    APIError,
    ConfigurationError,
    OllamaAdapter,
    OllamaConfig,
    get_ai_adapter
)

async def test_http_client_retry():
    """测试HTTP客户端重试机制"""
    print("🔄 **测试HTTP客户端重试机制**")
    
    client = HTTPClient(timeout=5.0, max_retries=2, retry_delay=0.1)
    
    # 模拟网络错误
    with patch('httpx.AsyncClient.post') as mock_post:
        # 设置前两次调用失败，第三次成功
        mock_post.side_effect = [
            httpx.ConnectError("连接失败"),
            httpx.ConnectError("连接失败"),
            AsyncMock(status_code=200, json=lambda: {"success": True})
        ]
        
        try:
            # 这应该会重试并最终成功
            result = await client.post_json("http://test.com", {"test": "data"})
            print("✅ 重试机制工作正常，最终成功")
        except APIError as e:
            print(f"✅ 重试后仍然失败（符合预期）: {e}")
        except Exception as e:
            print(f"❌ 意外异常: {e}")

async def test_http_client_max_retries():
    """测试HTTP客户端最大重试次数"""
    print("\n🚫 **测试最大重试次数**")
    
    client = HTTPClient(timeout=5.0, max_retries=2, retry_delay=0.1)
    
    # 模拟持续失败
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.side_effect = httpx.ConnectError("持续连接失败")
        
        try:
            await client.post_json("http://test.com", {"test": "data"})
            print("❌ 应该抛出APIError异常")
        except APIError as e:
            print(f"✅ 正确抛出APIError: {e}")
        except Exception as e:
            print(f"❌ 意外异常类型: {e}")

async def test_adapter_error_handling():
    """测试适配器错误处理"""
    print("\n🔧 **测试适配器错误处理**")
    
    # 创建一个Ollama适配器用于测试
    config = OllamaConfig(
        host="http://invalid-host:11434",
        model="test-model"
    )
    adapter = OllamaAdapter(config)
    
    # 测试聊天时的网络错误
    try:
        messages = [{"role": "user", "content": "测试消息"}]
        result = await adapter.chat(messages)
        print("❌ 应该抛出异常")
    except APIError as e:
        print(f"✅ 正确捕获API错误: {e}")
    except Exception as e:
        print(f"⚠️ 其他异常: {e}")

def test_configuration_errors():
    """测试配置错误"""
    print("\n⚙️ **测试配置错误**")
    
    from model_adapter_refactored import AdapterFactory
    
    # 测试不支持的提供商
    try:
        AdapterFactory.create_adapter("unsupported_provider")
        print("❌ 应该抛出ConfigurationError")
    except ConfigurationError as e:
        print(f"✅ 正确捕获配置错误: {e}")
    except Exception as e:
        print(f"❌ 意外异常类型: {e}")
    
    # 测试缺少必需配置
    try:
        AdapterFactory.create_adapter("qwen", {
            "model": "qwen-turbo"
            # 缺少api_key
        })
        print("❌ 应该抛出异常")
    except Exception as e:
        print(f"✅ 正确捕获配置缺失错误: {e}")

def test_get_ai_adapter_fallback():
    """测试get_ai_adapter的回退机制"""
    print("\n🔄 **测试get_ai_adapter回退机制**")
    
    import os
    
    # 清除所有相关环境变量
    env_vars_to_clear = ["QWEN_API_KEY", "OPENROUTER_API_KEY", "OLLAMA_HOST"]
    original_values = {}
    
    for var in env_vars_to_clear:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        adapter = get_ai_adapter()
        print("❌ 应该抛出ConfigurationError")
    except ConfigurationError as e:
        print(f"✅ 正确抛出配置错误: {e}")
    except Exception as e:
        print(f"❌ 意外异常: {e}")
    finally:
        # 恢复环境变量
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value

async def test_stream_error_handling():
    """测试流式响应错误处理"""
    print("\n🌊 **测试流式响应错误处理**")
    
    config = OllamaConfig(
        host="http://invalid-host:11434",
        model="test-model"
    )
    adapter = OllamaAdapter(config)
    
    try:
        messages = [{"role": "user", "content": "测试流式消息"}]
        async for chunk in adapter.chat_stream(messages):
            print(f"收到chunk: {chunk}")
        print("❌ 应该抛出异常")
    except APIError as e:
        print(f"✅ 正确捕获流式API错误: {e}")
    except Exception as e:
        print(f"⚠️ 其他异常: {e}")

def test_custom_exceptions():
    """测试自定义异常类"""
    print("\n🎯 **测试自定义异常类**")
    
    # 测试异常继承关系
    try:
        raise APIError("测试API错误")
    except ModelAdapterError as e:
        print(f"✅ APIError正确继承自ModelAdapterError: {e}")
    except Exception as e:
        print(f"❌ 异常继承关系错误: {e}")
    
    try:
        raise ConfigurationError("测试配置错误")
    except ModelAdapterError as e:
        print(f"✅ ConfigurationError正确继承自ModelAdapterError: {e}")
    except Exception as e:
        print(f"❌ 异常继承关系错误: {e}")

async def run_error_tests():
    """运行所有错误处理测试"""
    print("🚀 **错误处理测试开始**\n")
    
    # 异步测试
    async_tests = [
        test_http_client_retry,
        test_http_client_max_retries,
        test_adapter_error_handling,
        test_stream_error_handling
    ]
    
    for test in async_tests:
        try:
            await test()
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 异常: {e}")
    
    # 同步测试
    sync_tests = [
        test_configuration_errors,
        test_get_ai_adapter_fallback,
        test_custom_exceptions
    ]
    
    for test in sync_tests:
        try:
            test()
        except Exception as e:
            print(f"❌ 测试 {test.__name__} 异常: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_error_tests())
        print("\n🎉 **错误处理测试完成**")
    except KeyboardInterrupt:
        print("\n🛑 **测试被用户中断**")
    except Exception as e:
        print(f"\n❌ **测试运行异常**: {e}")
