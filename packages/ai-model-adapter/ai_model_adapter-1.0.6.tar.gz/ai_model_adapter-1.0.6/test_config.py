#!/usr/bin/env python3
"""
测试用例1: 配置管理测试
"""
import os
import asyncio
from model_adapter_refactored import (
    ConfigManager, 
    AdapterFactory, 
    ModelManager,
    QwenConfig,
    OpenRouterConfig,
    OllamaConfig,
    LMStudioConfig,
    OpenAICompatibleConfig,
    ConfigurationError
)

def test_config_classes():
    """测试配置类"""
    print("🧪 **测试配置类**")
    
    # 测试QwenConfig
    qwen_config = QwenConfig(
        api_key="test-key",
        model="qwen-turbo",
        base_url="https://test.com"
    )
    print(f"✅ QwenConfig: {qwen_config.api_key}, {qwen_config.model}")
    
    # 测试OpenRouterConfig
    openrouter_config = OpenRouterConfig(
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    print(f"✅ OpenRouterConfig: {openrouter_config.api_key}, {openrouter_config.model}")
    
    # 测试OllamaConfig
    ollama_config = OllamaConfig(
        host="http://localhost:11434",
        model="qwen3:0.6b"
    )
    print(f"✅ OllamaConfig: {ollama_config.host}, {ollama_config.model}")
    
    # 测试LMStudioConfig
    lmstudio_config = LMStudioConfig(
        host="http://localhost:1234",
        model="local-model"
    )
    print(f"✅ LMStudioConfig: {lmstudio_config.host}, {lmstudio_config.model}")
    
    # 测试OpenAICompatibleConfig
    openai_config = OpenAICompatibleConfig(
        api_key="test-key",
        model="Qwen/Qwen3-Coder-30B-A3B-Instruct",
        base_url="https://api.siliconflow.cn/v1"
    )
    print(f"✅ OpenAICompatibleConfig: {openai_config.base_url}, {openai_config.model}")

def test_config_manager():
    """测试配置管理器"""
    print("\n🔧 **测试配置管理器**")
    
    # 设置测试环境变量
    os.environ["QWEN_API_KEY"] = "test-qwen-key"
    os.environ["QWEN_MODEL"] = "qwen-flash"
    
    # 测试获取Qwen配置
    qwen_config = ConfigManager.get_qwen_config()
    if qwen_config:
        print(f"✅ 从环境变量获取Qwen配置: {qwen_config.api_key}")
    else:
        print("❌ 无法获取Qwen配置")
    
    # 测试获取OpenRouter配置（应该失败，因为没设置环境变量）
    openrouter_config = ConfigManager.get_openrouter_config()
    if openrouter_config:
        print(f"✅ 获取OpenRouter配置: {openrouter_config.api_key}")
    else:
        print("⚠️ 未设置OpenRouter环境变量（预期行为）")
    
    # 测试获取Ollama配置（使用默认值）
    ollama_config = ConfigManager.get_ollama_config()
    if ollama_config:
        print(f"✅ 获取Ollama配置: {ollama_config.host}")
    else:
        print("❌ 无法获取Ollama配置")
    
    # 测试获取LMStudio配置（使用默认值）
    lmstudio_config = ConfigManager.get_lmstudio_config()
    if lmstudio_config:
        print(f"✅ 获取LMStudio配置: {lmstudio_config.host}")
    else:
        print("❌ 无法获取LMStudio配置")
    
    # 测试获取OpenAI兼容配置（应该失败，因为没设置环境变量）
    openai_compatible_config = ConfigManager.get_openai_compatible_config()
    if openai_compatible_config:
        print(f"✅ 获取OpenAI兼容配置: {openai_compatible_config.base_url}")
    else:
        print("⚠️ 未设置OpenAI兼容环境变量（预期行为）")
    
    # 清理环境变量
    del os.environ["QWEN_API_KEY"]
    del os.environ["QWEN_MODEL"]

def test_adapter_factory():
    """测试适配器工厂"""
    print("\n🏭 **测试适配器工厂**")
    
    # 测试列出适配器
    adapters = AdapterFactory.list_adapters()
    print(f"✅ 可用适配器: {adapters}")
    
    # 测试使用自定义配置创建适配器
    try:
        qwen_adapter = AdapterFactory.create_adapter("qwen", {
            "api_key": "test-key",
            "model": "qwen-flash"
        })
        print("✅ 使用自定义配置创建Qwen适配器成功")
    except Exception as e:
        print(f"❌ 创建Qwen适配器失败: {e}")
    
    # 测试创建不存在的适配器
    try:
        invalid_adapter = AdapterFactory.create_adapter("invalid")
        print("❌ 应该抛出异常")
    except ConfigurationError as e:
        print(f"✅ 正确捕获配置错误: {e}")
    
    # 测试从环境变量创建适配器（应该失败）
    try:
        env_adapter = AdapterFactory.create_adapter("qwen")
        print("❌ 应该抛出异常")
    except ConfigurationError as e:
        print(f"✅ 正确捕获环境变量配置错误: {e}")

def test_model_manager():
    """测试模型管理器"""
    print("\n📊 **测试模型管理器**")
    
    manager = ModelManager()
    
    # 测试列出适配器
    adapters = manager.list_adapters()
    print(f"✅ 管理器可用适配器: {adapters}")
    
    # 测试获取适配器
    try:
        adapter = manager.get_adapter("ollama", {
            "host": "http://localhost:11434",
            "model": "qwen3:0.6b"
        })
        print("✅ 通过管理器创建Ollama适配器成功")
        print(f"   配置: {adapter.config.host}, {adapter.config.model}")
    except Exception as e:
        print(f"❌ 创建适配器失败: {e}")
    
    # 测试创建LMStudio适配器
    try:
        lmstudio_adapter = manager.get_adapter("lmstudio", {
            "host": "http://localhost:1234",
            "model": "local-model"
        })
        print("✅ 通过管理器创建LMStudio适配器成功")
        print(f"   配置: {lmstudio_adapter.config.host}, {lmstudio_adapter.config.model}")
    except Exception as e:
        print(f"❌ 创建LMStudio适配器失败: {e}")
    
    # 测试创建OpenAI兼容适配器
    try:
        openai_adapter = manager.get_adapter("openai_compatible", {
            "api_key": "test-key",
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct"
        })
        print("✅ 通过管理器创建OpenAI兼容适配器成功")
        print(f"   配置: {openai_adapter.config.base_url}, {openai_adapter.config.model}")
    except Exception as e:
        print(f"❌ 创建OpenAI兼容适配器失败: {e}")

if __name__ == "__main__":
    print("🚀 **配置管理测试开始**\n")
    
    test_config_classes()
    test_config_manager()
    test_adapter_factory()
    test_model_manager()
    
    print("\n🎉 **配置管理测试完成**")
