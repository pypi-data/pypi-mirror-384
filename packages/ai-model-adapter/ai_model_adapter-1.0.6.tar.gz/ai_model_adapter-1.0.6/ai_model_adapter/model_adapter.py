"""
模型适配器 - 简化版本，只支持消息收发和图片生成
移除了所有工具调用相关功能
"""
import json
import httpx
import asyncio
import os
import hashlib
import hmac
import base64
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from contextlib import asynccontextmanager

# 自定义异常类
class ModelAdapterError(Exception):
    """模型适配器基础异常"""
    pass

class APIError(ModelAdapterError):
    """API调用异常"""
    pass

class ConfigurationError(ModelAdapterError):
    """配置异常"""
    pass

# 配置类
@dataclass
class AdapterConfig:
    """适配器基础配置"""
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class QwenConfig:
    """Qwen配置"""
    api_key: str
    model: str
    base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class QwenVisionConfig:
    """Qwen视觉模型配置"""
    api_key: str
    model: str = "qwen3-vl-plus"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_thinking: bool = False
    thinking_budget: int = 500

@dataclass
class OpenRouterConfig:
    """OpenRouter配置"""
    api_key: str
    model: str
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class OllamaConfig:
    """Ollama配置"""
    host: str
    model: str
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class LMStudioConfig:
    """LMStudio配置"""
    host: str
    model: str
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class OpenAICompatibleConfig:
    """OpenAI兼容配置"""
    api_key: str
    model: str
    base_url: str
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class TongyiWanxiangConfig:
    """通义万象配置"""
    api_key: str
    model: str = "wan2.2-t2i-flash"
    base_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    task_url: str = "https://dashscope.aliyuncs.com/api/v1/tasks"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class JimengConfig:
    """即梦AI配置"""
    access_key: str
    secret_key: str
    model: str = "jimeng_t2i_v40"
    base_url: str = "https://visual.volcengineapi.com"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

@dataclass
class TencentHunyuanConfig:
    """腾讯云混元配置"""
    api_key: str
    model: str = "hunyuan-turbos-latest"
    base_url: str = "https://api.hunyuan.cloud.tencent.com/v1"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

# HTTP客户端封装
class HTTPClient:
    """HTTP客户端封装"""
    
    def __init__(self, timeout: float = 60.0, max_retries: int = 3, retry_delay: float = 1.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    @asynccontextmanager
    async def get_client(self):
        """获取HTTP客户端"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            yield client
    
    async def post_json(self, url: str, data: dict, headers: dict = None) -> dict:
        """发送POST JSON请求，支持自动重试"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.get_client() as client:
                    print(f"HTTP: POST请求 {url}，尝试 {attempt + 1}/{self.max_retries}")
                    response = await client.post(url, json=data, headers=headers or {})
                    
                    # 检查HTTP状态码
                    if response.status_code >= 400:
                        error_detail = f"HTTP {response.status_code}"
                        try:
                            error_body = response.json()
                            if isinstance(error_body, dict):
                                error_msg = error_body.get("message") or error_body.get("error", {}).get("message", "")
                                if error_msg:
                                    error_detail += f": {error_msg}"
                        except:
                            error_detail += f": {response.text[:200]}"
                        
                        raise httpx.HTTPStatusError(
                            f"HTTP错误 {response.status_code}: {error_detail}",
                            request=response.request,
                            response=response
                        )
                    
                    response.raise_for_status()
                    
                    try:
                        json_response = response.json()
                        print(f"HTTP: POST请求成功，响应大小: {len(str(json_response))} 字符")
                        return json_response
                    except json.JSONDecodeError as e:
                        raise APIError(f"HTTP响应不是有效的JSON格式: {e}, 响应内容: {response.text[:500]}")
                        
            except httpx.HTTPError as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    error_msg = f"HTTP POST请求失败，已重试 {self.max_retries} 次: {type(e).__name__}: {str(e)}"
                    print(error_msg)
                    raise APIError(error_msg)
                
                wait_time = self.retry_delay * (attempt + 1)
                print(f"HTTP: 请求失败，{wait_time}秒后重试: {e}")
                await asyncio.sleep(wait_time)
    
    async def get_json(self, url: str, headers: dict = None) -> dict:
        """发送GET JSON请求，支持自动重试"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.get_client() as client:
                    print(f"HTTP: GET请求 {url}，尝试 {attempt + 1}/{self.max_retries}")
                    response = await client.get(url, headers=headers or {})
                    
                    # 检查HTTP状态码
                    if response.status_code >= 400:
                        error_detail = f"HTTP {response.status_code}"
                        try:
                            error_body = response.json()
                            if isinstance(error_body, dict):
                                error_msg = error_body.get("message") or error_body.get("error", {}).get("message", "")
                                if error_msg:
                                    error_detail += f": {error_msg}"
                        except:
                            error_detail += f": {response.text[:200]}"
                        
                        raise httpx.HTTPStatusError(
                            f"HTTP错误 {response.status_code}: {error_detail}",
                            request=response.request,
                            response=response
                        )
                    
                    response.raise_for_status()
                    
                    try:
                        json_response = response.json()
                        print(f"HTTP: GET请求成功，响应大小: {len(str(json_response))} 字符")
                        return json_response
                    except json.JSONDecodeError as e:
                        raise APIError(f"HTTP响应不是有效的JSON格式: {e}, 响应内容: {response.text[:500]}")
                        
            except httpx.HTTPError as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    error_msg = f"HTTP GET请求失败，已重试 {self.max_retries} 次: {type(e).__name__}: {str(e)}"
                    print(error_msg)
                    raise APIError(error_msg)
                
                wait_time = self.retry_delay * (attempt + 1)
                print(f"HTTP: 请求失败，{wait_time}秒后重试: {e}")
                await asyncio.sleep(wait_time)
    
    @asynccontextmanager
    async def post_stream(self, url: str, data: dict, headers: dict = None):
        """POST 流式请求"""
        try:
            async with self.get_client() as client:
                async with client.stream("POST", url, json=data, headers=headers or {}) as response:
                    response.raise_for_status()
                    yield response
        except httpx.HTTPError as e:
            raise APIError(f"流式请求失败: {e}")

class ModelAdapter(ABC):
    """模型适配器基类"""
    
    def __init__(self, config):
        self.config = config
        self.http_client = HTTPClient(
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
    
    @abstractmethod
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """流式聊天"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """非流式聊天"""
        pass
    
    async def chat_completion(self, messages: List[Dict], **kwargs) -> str:
        """聊天完成接口 - 返回纯文本响应"""
        result = await self.chat(messages, **kwargs)
        # 从响应中提取文本内容
        if isinstance(result, dict):
            return result.get('content', result.get('response', str(result)))
        return str(result)

class ImageGenerationAdapter(ABC):
    """图片生成适配器基类"""
    
    def __init__(self, config):
        self.config = config
        self.http_client = HTTPClient(
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成图片"""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        pass

class VisionAdapter(ABC):
    """视觉识别适配器基类"""
    
    def __init__(self, config):
        self.config = config
        self.http_client = HTTPClient(
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
    
    @abstractmethod
    async def analyze_image(self, image_url: str, text: str = "图中描绘的是什么景象？", **kwargs) -> Dict[str, Any]:
        """分析图像"""
        pass
    
    @abstractmethod
    async def analyze_image_stream(self, image_url: str, text: str = "图中描绘的是什么景象？", **kwargs) -> AsyncGenerator[str, None]:
        """流式分析图像"""
        pass

class OllamaAdapter(ModelAdapter):
    """Ollama适配器"""
    
    def __init__(self, config: OllamaConfig):
        super().__init__(config)
        self.host = config.host.rstrip('/')
        self.model = config.model
    
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Ollama流式聊天"""
        url = f"{self.host}/api/chat"
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        async with self.http_client.post_stream(url, data) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        if chunk.get("message", {}).get("content"):
                            yield chunk["message"]["content"]
                        
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Ollama非流式聊天"""
        url = f"{self.host}/api/chat"
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        return await self.http_client.post_json(url, data)

class QwenAdapter(ModelAdapter):
    """通义千问适配器"""
    
    def __init__(self, config: QwenConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url
    
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """Qwen流式聊天"""
        # 对于Qwen，我们先使用非流式API，因为流式API可能有兼容性问题
        response = await self.chat(messages, **kwargs)
        
        # 提取内容并模拟流式返回
        if "output" in response and "choices" in response["output"]:
            choices = response["output"]["choices"]
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "")
                # 将内容分块返回，模拟流式效果
                words = content.split()
                for i, word in enumerate(words):
                    if i > 0:
                        yield " "
                    yield word
                    # 添加小延迟模拟流式效果
                    await asyncio.sleep(0.01)
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Qwen非流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "input": {"messages": messages},
            "parameters": {
                "result_format": "message"
            }
        }
        
        return await self.http_client.post_json(self.base_url, data, headers)

class QwenVisionAdapter(VisionAdapter):
    """通义千问视觉适配器"""
    
    def __init__(self, config: QwenVisionConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url
        self.enable_thinking = config.enable_thinking
        self.thinking_budget = config.thinking_budget
    
    async def analyze_image(self, image_url: str, text: str = "图中描绘的是什么景象？", **kwargs) -> Dict[str, Any]:
        """分析图像 - 非流式"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建消息内容
        content = [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": text}
        ]
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
        
        # 添加思考模式参数
        if self.enable_thinking:
            data["extra_body"] = {
                "enable_thinking": self.enable_thinking,
                "thinking_budget": self.thinking_budget
            }
        
        # 添加其他可选参数
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            data["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        
        print(f"通义千问视觉: 分析图像 {image_url[:50]}...")
        return await self.http_client.post_json(self.base_url, data, headers)
    
    async def analyze_image_stream(self, image_url: str, text: str = "图中描绘的是什么景象？", **kwargs) -> AsyncGenerator[str, None]:
        """分析图像 - 流式"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建消息内容
        content = [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": text}
        ]
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "stream": True
        }
        
        # 添加思考模式参数
        if self.enable_thinking:
            data["extra_body"] = {
                "enable_thinking": self.enable_thinking,
                "thinking_budget": self.thinking_budget
            }
        
        # 添加其他可选参数
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            data["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        
        print(f"通义千问视觉: 流式分析图像 {image_url[:50]}...")
        
        async with self.http_client.post_stream(self.base_url, data, headers) as response:
            is_answering = False
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line_data = line[6:]
                    if line_data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(line_data)
                        
                        # 处理思考过程
                        if chunk.get("choices") and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            
                            # 跳过思考过程，只输出回复内容
                            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                                continue
                            
                            # 开始回复内容
                            if delta.get("content"):
                                if not is_answering:
                                    is_answering = True
                                yield delta["content"]
                                
                    except json.JSONDecodeError:
                        continue

class OpenRouterAdapter(ModelAdapter):
    """OpenRouter适配器"""
    
    def __init__(self, config: OpenRouterConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url
    
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """OpenRouter流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        async with self.http_client.post_stream(self.base_url, data, headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line_data = line[6:]
                    if line_data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(line_data)
                        if chunk.get("choices"):
                            delta = chunk["choices"][0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """OpenRouter非流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages
        }
        
        return await self.http_client.post_json(self.base_url, data, headers)

class LMStudioAdapter(ModelAdapter):
    """LMStudio适配器"""
    
    def __init__(self, config: LMStudioConfig):
        super().__init__(config)
        self.host = config.host.rstrip('/')
        self.model = config.model
        self.base_url = f"{self.host}/v1/chat/completions"
    
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """LMStudio流式聊天"""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        async with self.http_client.post_stream(self.base_url, data, headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line_data = line[6:]
                    if line_data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(line_data)
                        if chunk.get("choices"):
                            delta = chunk["choices"][0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """LMStudio非流式聊天"""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages
        }
        
        return await self.http_client.post_json(self.base_url, data, headers)

class OpenAICompatibleAdapter(ModelAdapter):
    """OpenAI兼容适配器"""
    
    def __init__(self, config: OpenAICompatibleConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url.rstrip('/') + '/chat/completions'
    
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """OpenAI兼容流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        async with self.http_client.post_stream(self.base_url, data, headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line_data = line[6:]
                    if line_data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(line_data)
                        if chunk.get("choices"):
                            delta = chunk["choices"][0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """OpenAI兼容非流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages
        }
        
        return await self.http_client.post_json(self.base_url, data, headers)

class TencentHunyuanAdapter(ModelAdapter):
    """腾讯云混元适配器 - OpenAI兼容接口"""
    
    def __init__(self, config: TencentHunyuanConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url.rstrip('/') + '/chat/completions'
    
    async def chat_stream(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]:
        """腾讯云混元流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "enable_enhancement": kwargs.get("enable_enhancement", True)
        }
        
        # 添加可选参数
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            data["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        
        async with self.http_client.post_stream(self.base_url, data, headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line_data = line[6:]
                    if line_data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(line_data)
                        if chunk.get("choices"):
                            delta = chunk["choices"][0].get("delta", {})
                            if delta.get("content"):
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """腾讯云混元非流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "enable_enhancement": kwargs.get("enable_enhancement", True)
        }
        
        # 添加可选参数
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            data["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            data["top_p"] = kwargs["top_p"]
        
        return await self.http_client.post_json(self.base_url, data, headers)

class TongyiWanxiangAdapter(ImageGenerationAdapter):
    """通义万象图片生成适配器"""
    
    def __init__(self, config: TongyiWanxiangConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url
        self.task_url = config.task_url
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成图片 - 提交异步任务到通义万象"""
        # 验证输入参数
        if not prompt or not isinstance(prompt, str):
            raise APIError("通义万象: prompt参数必须是非空字符串")
        
        if len(prompt) > 800:
            raise APIError(f"通义万象: prompt长度({len(prompt)})超过800字符限制")
        
        # 验证图片尺寸格式
        size = kwargs.get("size", "1024*1024")
        if not isinstance(size, str) or "*" not in size:
            raise APIError(f"通义万象: size参数格式错误，应为'宽*高'格式，当前值: {size}")
        
        # 验证生成数量
        n = kwargs.get("n", 1)
        if not isinstance(n, int) or n < 1 or n > 4:
            raise APIError(f"通义万象: n参数必须是1-4之间的整数，当前值: {n}")
        
        # 构建请求头，启用异步模式
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # 关键：启用异步任务模式
        }
        
        # 构建请求数据
        data = {
            "model": self.model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "size": size,
                "n": n
            }
        }
        
        print(f"通义万象: 提交图片生成任务，prompt长度: {len(prompt)}, 尺寸: {size}, 数量: {n}")
        response = await self.http_client.post_json(self.base_url, data, headers)
        
        # 验证响应格式
        if not isinstance(response, dict):
            raise APIError(f"通义万象: 响应格式错误，期望dict，实际: {type(response)}")
        
        if "output" not in response:
            raise APIError(f"通义万象: 响应缺少output字段，响应内容: {response}")
        
        if "task_id" not in response["output"]:
            raise APIError(f"通义万象: 响应缺少task_id字段，output内容: {response['output']}")
        
        task_id = response["output"]["task_id"]
        print(f"通义万象: 任务提交成功，task_id: {task_id}")
        return response
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询通义万象图片生成任务状态"""
        # 验证task_id参数
        if not task_id or not isinstance(task_id, str):
            raise APIError("通义万象: task_id参数必须是非空字符串")
        
        if len(task_id.strip()) == 0:
            raise APIError("通义万象: task_id不能为空白字符串")
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 构建查询URL
        url = f"{self.task_url}/{task_id.strip()}"
        
        print(f"通义万象: 查询任务状态，task_id: {task_id}")
        response = await self.http_client.get_json(url, headers)
        
        # 验证响应格式
        if not isinstance(response, dict):
            raise APIError(f"通义万象: 查询响应格式错误，期望dict，实际: {type(response)}")
        
        # 检查是否有错误信息
        if "code" in response and response["code"] != "Success":
            error_code = response.get("code", "Unknown")
            error_msg = response.get("message", "未知错误")
            raise APIError(f"通义万象: 查询失败，错误码: {error_code}，错误信息: {error_msg}")
        
        # 验证output字段
        if "output" not in response:
            raise APIError(f"通义万象: 查询响应缺少output字段，响应内容: {response}")
        
        output = response["output"]
        task_status = output.get("task_status", "UNKNOWN")
        print(f"通义万象: 任务状态查询成功，task_id: {task_id}, 状态: {task_status}")
        
        return response

class JimengAdapter(ImageGenerationAdapter):
    """即梦AI图片生成适配器"""
    
    def __init__(self, config: JimengConfig):
        super().__init__(config)
        self.access_key = config.access_key
        self.secret_key = config.secret_key
        self.model = config.model
        self.base_url = config.base_url
        self.region = "cn-north-1"
        self.service = "cv"
    
    def _sign(self, key: bytes, msg: str) -> bytes:
        """HMAC签名"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    def _get_signature_key(self, key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
        """获取签名密钥"""
        k_date = self._sign(key.encode('utf-8'), date_stamp)
        k_region = self._sign(k_date, region_name)
        k_service = self._sign(k_region, service_name)
        k_signing = self._sign(k_service, 'request')
        return k_signing
    
    def _create_signed_headers(self, method: str, canonical_uri: str, query_string: str, body: str) -> Dict[str, str]:
        """创建带签名的请求头"""
        # 获取当前时间
        t = datetime.utcnow()
        current_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')
        
        # 计算payload hash
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        
        # 构建规范请求头
        host = 'visual.volcengineapi.com'
        content_type = 'application/json'
        signed_headers = 'content-type;host;x-content-sha256;x-date'
        
        canonical_headers = (
            f'content-type:{content_type}\n'
            f'host:{host}\n'
            f'x-content-sha256:{payload_hash}\n'
            f'x-date:{current_date}\n'
        )
        
        # 构建规范请求
        canonical_request = (
            f'{method}\n'
            f'{canonical_uri}\n'
            f'{query_string}\n'
            f'{canonical_headers}\n'
            f'{signed_headers}\n'
            f'{payload_hash}'
        )
        
        # 构建签名字符串
        algorithm = 'HMAC-SHA256'
        credential_scope = f'{date_stamp}/{self.region}/{self.service}/request'
        string_to_sign = (
            f'{algorithm}\n'
            f'{current_date}\n'
            f'{credential_scope}\n'
            f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
        )
        
        # 计算签名
        signing_key = self._get_signature_key(self.secret_key, date_stamp, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # 构建Authorization头
        authorization_header = (
            f'{algorithm} '
            f'Credential={self.access_key}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, '
            f'Signature={signature}'
        )
        
        return {
            'X-Date': current_date,
            'Authorization': authorization_header,
            'X-Content-Sha256': payload_hash,
            'Content-Type': content_type
        }
    
    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成图片 - 提交异步任务到即梦AI"""
        # 验证输入参数
        if not prompt or not isinstance(prompt, str):
            raise APIError("即梦AI: prompt参数必须是非空字符串")
        
        if len(prompt) > 800:
            print(f"即梦AI: 警告 - prompt长度({len(prompt)})超过建议的800字符")
        
        # 构建请求数据
        data = {
            "req_key": self.model,
            "prompt": prompt,
            "size": kwargs.get("size", 4194304),
            "scale": kwargs.get("scale", 0.5),
            "force_single": kwargs.get("force_single", False)
        }
        
        # 添加可选参数
        if "image_urls" in kwargs:
            data["image_urls"] = kwargs["image_urls"]
        
        if "width" in kwargs and "height" in kwargs:
            data["width"] = kwargs["width"]
            data["height"] = kwargs["height"]
        
        # 序列化请求体
        body = json.dumps(data)
        query_string = "Action=CVSync2AsyncSubmitTask&Version=2022-08-31"
        canonical_uri = "/"
        
        # 创建火山引擎签名头
        headers = self._create_signed_headers("POST", canonical_uri, query_string, body)
        url = f"{self.base_url}?{query_string}"
        
        print(f"即梦AI: 提交图片生成任务，prompt长度: {len(prompt)}")
        response = await self.http_client.post_json(url, data, headers)
        
        # 验证响应格式
        if not isinstance(response, dict):
            raise APIError(f"即梦AI: 响应格式错误，期望dict，实际: {type(response)}")
        
        # 检查响应状态
        code = response.get("code")
        if code != 10000:
            message = response.get("message", "未知错误")
            raise APIError(f"即梦AI: 提交任务失败，错误码: {code}，错误信息: {message}")
        
        # 验证data字段
        if "data" not in response:
            raise APIError(f"即梦AI: 响应缺少data字段，响应内容: {response}")
        
        if "task_id" not in response["data"]:
            raise APIError(f"即梦AI: 响应缺少task_id字段，data内容: {response['data']}")
        
        task_id = response["data"]["task_id"]
        print(f"即梦AI: 任务提交成功，task_id: {task_id}")
        return response
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询即梦AI图片生成任务状态"""
        # 验证task_id参数
        if not task_id or not isinstance(task_id, str):
            raise APIError("即梦AI: task_id参数必须是非空字符串")
        
        if len(task_id.strip()) == 0:
            raise APIError("即梦AI: task_id不能为空白字符串")
        
        # 构建请求数据
        data = {
            "req_key": self.model,
            "task_id": task_id.strip(),
            "req_json": json.dumps({"return_url": True})  # 返回图片URL而非base64
        }
        
        # 序列化请求体
        body = json.dumps(data)
        query_string = "Action=CVSync2AsyncGetResult&Version=2022-08-31"
        canonical_uri = "/"
        
        # 创建火山引擎签名头
        headers = self._create_signed_headers("POST", canonical_uri, query_string, body)
        url = f"{self.base_url}?{query_string}"
        
        print(f"即梦AI: 查询任务状态，task_id: {task_id}")
        response = await self.http_client.post_json(url, data, headers)
        
        # 验证响应格式
        if not isinstance(response, dict):
            raise APIError(f"即梦AI: 查询响应格式错误，期望dict，实际: {type(response)}")
        
        # 检查基本响应结构
        if "data" not in response:
            # 可能是错误响应，检查是否有错误信息
            code = response.get("code")
            message = response.get("message", "未知错误")
            if code and code != 10000:
                raise APIError(f"即梦AI: 查询失败，错误码: {code}，错误信息: {message}")
            else:
                raise APIError(f"即梦AI: 查询响应缺少data字段，响应内容: {response}")
        
        data_field = response["data"]
        status = data_field.get("status", "unknown")
        
        print(f"即梦AI: 任务状态查询成功，task_id: {task_id}, 状态: {status}")
        return response

# 配置管理器
class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def get_qwen_config() -> Optional[QwenConfig]:
        """获取Qwen配置"""
        api_key = os.getenv("QWEN_API_KEY")
        if not api_key:
            return None
            
        return QwenConfig(
            api_key=api_key,
            model=os.getenv("QWEN_MODEL", "qwen-flash")
        )
    
    @staticmethod
    def get_qwen_vision_config() -> Optional[QwenVisionConfig]:
        """获取Qwen视觉配置"""
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not api_key:
            return None
            
        return QwenVisionConfig(
            api_key=api_key,
            model=os.getenv("QWEN_VISION_MODEL", "qwen3-vl-plus"),
            enable_thinking=os.getenv("QWEN_VISION_THINKING", "false").lower() == "true",
            thinking_budget=int(os.getenv("QWEN_VISION_THINKING_BUDGET", "500"))
        )
    
    @staticmethod
    def get_openrouter_config() -> Optional[OpenRouterConfig]:
        """获取OpenRouter配置"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return None
            
        return OpenRouterConfig(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "qwen/qwen3-next-80b-a3b-instruct")
        )
    
    @staticmethod
    def get_ollama_config() -> Optional[OllamaConfig]:
        """获取Ollama配置"""
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")
        
        return OllamaConfig(
            host=host,
            model=model
        )
    
    @staticmethod
    def get_lmstudio_config() -> Optional[LMStudioConfig]:
        """获取LMStudio配置"""
        host = os.getenv("LMSTUDIO_HOST", "http://localhost:1234")
        model = os.getenv("LMSTUDIO_MODEL", "local-model")
        
        return LMStudioConfig(
            host=host,
            model=model
        )
    
    @staticmethod
    def get_openai_compatible_config() -> Optional[OpenAICompatibleConfig]:
        """获取OpenAI兼容配置"""
        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.siliconflow.cn/v1")
        model = os.getenv("OPENAI_COMPATIBLE_MODEL", "Qwen/Qwen3-Coder-30B-A3B-Instruct")
        
        if not api_key:
            return None
            
        return OpenAICompatibleConfig(
            api_key=api_key,
            model=model,
            base_url=base_url
        )
    
    @staticmethod
    def get_tongyi_wanxiang_config() -> Optional[TongyiWanxiangConfig]:
        """获取通义万象配置"""
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return None
            
        return TongyiWanxiangConfig(
            api_key=api_key,
            model=os.getenv("TONGYI_WANXIANG_MODEL", "wan2.2-t2i-flash")
        )
    
    @staticmethod
    def get_jimeng_config() -> Optional[JimengConfig]:
        """获取即梦AI配置"""
        access_key = os.getenv("JIMENG_ACCESS_KEY")
        secret_key = os.getenv("JIMENG_SECRET_KEY")
        
        if not access_key or not secret_key:
            return None
            
        return JimengConfig(
            access_key=access_key,
            secret_key=secret_key,
            model=os.getenv("JIMENG_MODEL", "jimeng_t2i_v40")
        )
    
    @staticmethod
    def get_tencent_hunyuan_config() -> Optional[TencentHunyuanConfig]:
        """获取腾讯云混元配置"""
        api_key = os.getenv("HUNYUAN_API_KEY")
        if not api_key:
            return None
            
        return TencentHunyuanConfig(
            api_key=api_key,
            model=os.getenv("HUNYUAN_MODEL", "hunyuan-turbos-latest")
        )

# 适配器工厂
class AdapterFactory:
    """适配器工厂"""
    
    _adapters = {
        "qwen": (QwenAdapter, ConfigManager.get_qwen_config),
        "qwen_vision": (QwenVisionAdapter, ConfigManager.get_qwen_vision_config),
        "openrouter": (OpenRouterAdapter, ConfigManager.get_openrouter_config),
        "ollama": (OllamaAdapter, ConfigManager.get_ollama_config),
        "lmstudio": (LMStudioAdapter, ConfigManager.get_lmstudio_config),
        "openai_compatible": (OpenAICompatibleAdapter, ConfigManager.get_openai_compatible_config),
        "tongyi_wanxiang": (TongyiWanxiangAdapter, ConfigManager.get_tongyi_wanxiang_config),
        "jimeng": (JimengAdapter, ConfigManager.get_jimeng_config),
        "tencent_hunyuan": (TencentHunyuanAdapter, ConfigManager.get_tencent_hunyuan_config)
    }
    
    @classmethod
    def create_adapter(cls, provider: str, config: dict = None) -> ModelAdapter:
        """创建适配器实例"""
        if provider not in cls._adapters:
            raise ConfigurationError(f"不支持的提供商: {provider}")
            
        adapter_class, config_getter = cls._adapters[provider]
        
        if config:
            # 使用提供的配置
            if provider == "qwen":
                adapter_config = QwenConfig(**config)
            elif provider == "qwen_vision":
                adapter_config = QwenVisionConfig(**config)
            elif provider == "openrouter":
                adapter_config = OpenRouterConfig(**config)
            elif provider == "ollama":
                adapter_config = OllamaConfig(**config)
            elif provider == "lmstudio":
                adapter_config = LMStudioConfig(**config)
            elif provider == "openai_compatible":
                adapter_config = OpenAICompatibleConfig(**config)
            elif provider == "tongyi_wanxiang":
                adapter_config = TongyiWanxiangConfig(**config)
            elif provider == "jimeng":
                adapter_config = JimengConfig(**config)
            elif provider == "tencent_hunyuan":
                adapter_config = TencentHunyuanConfig(**config)
        else:
            # 从环境变量获取配置
            adapter_config = config_getter()
            if not adapter_config:
                raise ConfigurationError(f"无法获取{provider}的配置，请检查环境变量")
                
        return adapter_class(adapter_config)
    
    @classmethod
    def list_adapters(cls) -> List[str]:
        """列出可用适配器"""
        return list(cls._adapters.keys())

class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, ModelAdapter] = {}
        self.factory = AdapterFactory()
    
    def get_adapter(self, provider: str, config: dict = None) -> ModelAdapter:
        """获取适配器"""
        return self.factory.create_adapter(provider, config)
    
    def list_adapters(self) -> List[str]:
        """列出可用适配器"""
        return self.factory.list_adapters()

# 全局模型管理器
model_manager = ModelManager()

def get_ai_adapter() -> ModelAdapter:
    """获取默认的AI适配器"""
    # 按优先级尝试不同的适配器
    providers = ["qwen", "openrouter"]
    
    for provider in providers:
        try:
            return model_manager.get_adapter(provider)
        except ConfigurationError as e:
            print(f"无法创建{provider}适配器: {e}")
            continue
        except Exception as e:
            print(f"创建{provider}适配器时发生未知错误: {e}")
            continue
    
    # 最后尝试使用默认的Ollama配置
    try:
        return model_manager.get_adapter("ollama", {
            "host": "http://localhost:11434",
            "model": "qwen3:0.6b"
        })
    except Exception as e:
        print(f"创建默认Ollama适配器失败: {e}")
    
    raise ConfigurationError("无法创建任何AI适配器，请检查配置或启动Ollama服务")

# FastAPI服务
def create_app():
    """创建FastAPI应用实例"""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import StreamingResponse
        from pydantic import BaseModel
        import uvicorn
    except ImportError:
        raise ImportError("请安装FastAPI和uvicorn: pip install fastapi uvicorn")
    
    app = FastAPI(title="AI模型适配器服务 - 简化版", version="1.0.0")
    
    class ChatRequest(BaseModel):
        messages: List[Dict[str, Any]]
        provider: str = "qwen"
        model: Optional[str] = None
        stream: bool = False
        # OpenAI兼容适配器专用字段
        api_key: Optional[str] = None
        base_url: Optional[str] = None
    
    class ChatResponse(BaseModel):
        content: str
        provider: str
        model: str
    
    class ImageGenerationRequest(BaseModel):
        prompt: str
        provider: str = "tongyi_wanxiang"
        model: Optional[str] = None
        # 通用参数
        size: Optional[str] = None
        width: Optional[int] = None
        height: Optional[int] = None
        n: Optional[int] = 1
        # 通义万象参数
        # 即梦AI参数
        scale: Optional[float] = None
        force_single: Optional[bool] = None
        image_urls: Optional[List[str]] = None
        # 配置参数
        api_key: Optional[str] = None
        access_key: Optional[str] = None
        secret_key: Optional[str] = None
    
    class ImageGenerationResponse(BaseModel):
        task_id: Optional[str] = None
        status: str
        images: Optional[List[str]] = None
        provider: str
        model: str
        message: Optional[str] = None
    
    class TaskStatusRequest(BaseModel):
        task_id: str
        provider: str = "tongyi_wanxiang"
        # 配置参数
        api_key: Optional[str] = None
        access_key: Optional[str] = None
        secret_key: Optional[str] = None
    
    class ImageGenerationSyncRequest(BaseModel):
        prompt: str
        provider: str = "tongyi_wanxiang"
        model: Optional[str] = None
        # 通用参数
        size: Optional[str] = None
        width: Optional[int] = None
        height: Optional[int] = None
        n: Optional[int] = 1
        # 通义万象参数
        # 即梦AI参数
        scale: Optional[float] = None
        force_single: Optional[bool] = None
        image_urls: Optional[List[str]] = None
        # 配置参数
        api_key: Optional[str] = None
        access_key: Optional[str] = None
        secret_key: Optional[str] = None
        # 同步参数
        timeout: Optional[int] = 300  # 超时时间（秒）
        poll_interval: Optional[int] = 3  # 轮询间隔（秒）
    
    class VisionAnalysisRequest(BaseModel):
        image_url: str
        text: str = "图中描绘的是什么景象？"
        provider: str = "qwen_vision"
        model: Optional[str] = None
        stream: bool = False
        # 配置参数
        api_key: Optional[str] = None
        enable_thinking: Optional[bool] = None
        thinking_budget: Optional[int] = None
        # 生成参数
        temperature: Optional[float] = None
        max_tokens: Optional[int] = None
        top_p: Optional[float] = None
    
    class VisionAnalysisResponse(BaseModel):
        content: str
        provider: str
        model: str
        image_url: str
        thinking_content: Optional[str] = None
    
    @app.post("/chat")
    async def chat(request: ChatRequest):
        """聊天接口"""
        try:
            # 构建配置
            config = {}
            if request.model:
                config["model"] = request.model
            
            # 处理运行时API密钥
            if request.api_key:
                config["api_key"] = request.api_key
            
            # 对于OpenAI兼容适配器，需要特殊处理
            if request.provider == "openai_compatible":
                if not request.api_key or not request.base_url:
                    raise HTTPException(
                        status_code=400, 
                        detail="OpenAI兼容适配器需要提供api_key和base_url参数"
                    )
                config.update({
                    "api_key": request.api_key,
                    "base_url": request.base_url
                })
            
            # 获取适配器
            adapter = model_manager.get_adapter(request.provider, config if config else None)
            
            if request.stream:
                # 流式响应
                async def generate():
                    async for chunk in adapter.chat_stream(request.messages):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(generate(), media_type="text/plain")
            else:
                # 非流式响应
                result = await adapter.chat(request.messages)
                
                # 提取内容
                content = ""
                if isinstance(result, dict):
                    if "output" in result and "choices" in result["output"]:
                        # Qwen格式
                        choices = result["output"]["choices"]
                        if choices and "message" in choices[0]:
                            content = choices[0]["message"].get("content", "")
                    elif "choices" in result:
                        # OpenRouter格式
                        choices = result["choices"]
                        if choices and "message" in choices[0]:
                            content = choices[0]["message"].get("content", "")
                    elif "message" in result:
                        # Ollama格式
                        content = result["message"].get("content", "")
                    else:
                        content = str(result)
                
                return ChatResponse(
                    content=content,
                    provider=request.provider,
                    model=request.model or "default"
                )
                
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except APIError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"未知错误: {e}")
    
    @app.post("/analyze-image")
    async def analyze_image(request: VisionAnalysisRequest):
        """图像识别接口"""
        try:
            # 构建配置
            config = {}
            if request.model:
                config["model"] = request.model
            
            # 处理运行时API密钥
            if request.api_key:
                config["api_key"] = request.api_key
            
            # 处理思考模式参数
            if request.enable_thinking is not None:
                config["enable_thinking"] = request.enable_thinking
            if request.thinking_budget is not None:
                config["thinking_budget"] = request.thinking_budget
            
            # 获取适配器
            adapter = model_manager.get_adapter(request.provider, config if config else None)
            
            # 检查是否为视觉适配器
            if not isinstance(adapter, VisionAdapter):
                raise HTTPException(
                    status_code=400, 
                    detail=f"提供商 {request.provider} 不支持图像识别"
                )
            
            # 构建分析参数
            kwargs = {}
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if request.max_tokens is not None:
                kwargs["max_tokens"] = request.max_tokens
            if request.top_p is not None:
                kwargs["top_p"] = request.top_p
            
            if request.stream:
                # 流式响应
                async def generate():
                    async for chunk in adapter.analyze_image_stream(request.image_url, request.text, **kwargs):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(generate(), media_type="text/plain")
            else:
                # 非流式响应
                result = await adapter.analyze_image(request.image_url, request.text, **kwargs)
                
                # 提取内容
                content = ""
                thinking_content = None
                
                if isinstance(result, dict):
                    if "choices" in result and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        if "message" in choice:
                            content = choice["message"].get("content", "")
                        
                        # 提取思考内容（如果有）
                        if "reasoning_content" in choice:
                            thinking_content = choice["reasoning_content"]
                    else:
                        content = str(result)
                
                return VisionAnalysisResponse(
                    content=content,
                    provider=request.provider,
                    model=request.model or adapter.model,
                    image_url=request.image_url,
                    thinking_content=thinking_content
                )
                
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except APIError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"未知错误: {e}")
    
    @app.post("/generate-image")
    async def generate_image(request: ImageGenerationRequest):
        """图片生成接口"""
        try:
            # 构建配置
            config = {}
            if request.model:
                config["model"] = request.model
            
            # 根据提供商设置配置
            if request.provider == "tongyi_wanxiang":
                if request.api_key:
                    config["api_key"] = request.api_key
            elif request.provider == "jimeng":
                if request.access_key and request.secret_key:
                    config["access_key"] = request.access_key
                    config["secret_key"] = request.secret_key
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail="即梦AI需要提供access_key和secret_key参数"
                    )
            
            # 获取适配器
            adapter = model_manager.get_adapter(request.provider, config if config else None)
            
            # 检查是否为图片生成适配器
            if not isinstance(adapter, ImageGenerationAdapter):
                raise HTTPException(
                    status_code=400, 
                    detail=f"提供商 {request.provider} 不支持图片生成"
                )
            
            # 构建生成参数
            kwargs = {}
            if request.size:
                kwargs["size"] = request.size
            if request.width and request.height:
                kwargs["width"] = request.width
                kwargs["height"] = request.height
            if request.n:
                kwargs["n"] = request.n
            if request.scale is not None:
                kwargs["scale"] = request.scale
            if request.force_single is not None:
                kwargs["force_single"] = request.force_single
            if request.image_urls:
                kwargs["image_urls"] = request.image_urls
            
            # 提交图片生成任务
            result = await adapter.generate_image(request.prompt, **kwargs)
            
            # 解析响应
            if request.provider == "tongyi_wanxiang":
                if "output" in result and "task_id" in result["output"]:
                    return ImageGenerationResponse(
                        task_id=result["output"]["task_id"],
                        status="pending",
                        provider=request.provider,
                        model=request.model or adapter.model,
                        message="任务已提交，请使用task_id查询结果"
                    )
            elif request.provider == "jimeng":
                if "data" in result and "task_id" in result["data"]:
                    return ImageGenerationResponse(
                        task_id=result["data"]["task_id"],
                        status="pending", 
                        provider=request.provider,
                        model=request.model or adapter.model,
                        message="任务已提交，请使用task_id查询结果"
                    )
            
            # 如果响应格式不符合预期
            return ImageGenerationResponse(
                status="error",
                provider=request.provider,
                model=request.model or adapter.model,
                message=f"响应格式异常: {result}"
            )
                
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except APIError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"未知错误: {e}")
    
    @app.post("/task-status")
    async def get_task_status(request: TaskStatusRequest):
        """查询任务状态接口"""
        try:
            # 构建配置
            config = {}
            
            # 根据提供商设置配置
            if request.provider == "tongyi_wanxiang":
                if request.api_key:
                    config["api_key"] = request.api_key
            elif request.provider == "jimeng":
                if request.access_key and request.secret_key:
                    config["access_key"] = request.access_key
                    config["secret_key"] = request.secret_key
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail="即梦AI需要提供access_key和secret_key参数"
                    )
            
            # 获取适配器
            adapter = model_manager.get_adapter(request.provider, config if config else None)
            
            # 检查是否为图片生成适配器
            if not isinstance(adapter, ImageGenerationAdapter):
                raise HTTPException(
                    status_code=400, 
                    detail=f"提供商 {request.provider} 不支持图片生成"
                )
            
            # 查询任务状态
            result = await adapter.get_task_status(request.task_id)
            
            # 解析响应
            if request.provider == "tongyi_wanxiang":
                if "output" in result:
                    output = result["output"]
                    task_status = output.get("task_status")
                    
                    if task_status == "SUCCEEDED":
                        # 提取图片URL
                        images = []
                        if "results" in output:
                            for result_item in output["results"]:
                                if "url" in result_item:
                                    images.append(result_item["url"])
                        
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="completed",
                            images=images,
                            provider=request.provider,
                            model=adapter.model,
                            message="任务完成"
                        )
                    elif task_status == "FAILED":
                        error_msg = output.get("message", "未知错误")
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="failed",
                            provider=request.provider,
                            model=adapter.model,
                            message=f"任务失败: {error_msg}"
                        )
                    else:
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="processing",
                            provider=request.provider,
                            model=adapter.model,
                            message=f"任务状态: {task_status}"
                        )
            
            elif request.provider == "jimeng":
                if "data" in result:
                    data = result["data"]
                    status = data.get("status")
                    
                    if status == "done" and result.get("code") == 10000:
                        # 提取图片URL
                        images = data.get("image_urls", [])
                        
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="completed",
                            images=images,
                            provider=request.provider,
                            model=adapter.model,
                            message="任务完成"
                        )
                    elif status == "done":
                        error_msg = result.get("message", "未知错误")
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="failed",
                            provider=request.provider,
                            model=adapter.model,
                            message=f"任务失败: {error_msg}"
                        )
                    elif status in ["in_queue", "generating"]:
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="processing",
                            provider=request.provider,
                            model=adapter.model,
                            message=f"任务状态: {status}"
                        )
                    elif status == "not_found":
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="not_found",
                            provider=request.provider,
                            model=adapter.model,
                            message="任务未找到"
                        )
                    elif status == "expired":
                        return ImageGenerationResponse(
                            task_id=request.task_id,
                            status="expired",
                            provider=request.provider,
                            model=adapter.model,
                            message="任务已过期"
                        )
            
            # 如果响应格式不符合预期
            return ImageGenerationResponse(
                task_id=request.task_id,
                status="unknown",
                provider=request.provider,
                model=adapter.model,
                message=f"响应格式异常: {result}"
            )
                
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except APIError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"未知错误: {e}")
    
    @app.post("/generate-image-sync")
    async def generate_image_sync(request: ImageGenerationSyncRequest):
        """同步图片生成接口 - 阻塞直到完成"""
        try:
            # 构建配置
            config = {}
            
            # 根据提供商设置配置
            if request.provider == "tongyi_wanxiang":
                if request.api_key:
                    config["api_key"] = request.api_key
                if request.model:
                    config["model"] = request.model
            elif request.provider == "jimeng":
                if request.access_key and request.secret_key:
                    config["access_key"] = request.access_key
                    config["secret_key"] = request.secret_key
                elif not config:
                    # 如果没有提供运行时密钥，尝试从环境变量获取
                    import os
                    env_access_key = os.getenv("JIMENG_ACCESS_KEY")
                    env_secret_key = os.getenv("JIMENG_SECRET_KEY")
                    if env_access_key and env_secret_key:
                        config["access_key"] = env_access_key
                        config["secret_key"] = env_secret_key
                    else:
                        raise HTTPException(
                            status_code=400, 
                            detail="即梦AI需要提供access_key和secret_key参数或设置环境变量"
                        )
                if request.model:
                    config["model"] = request.model
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"同步模式暂不支持提供商: {request.provider}"
                )
            
            # 获取适配器
            adapter = model_manager.get_adapter(request.provider, config if config else None)
            
            # 检查是否为图片生成适配器
            if not isinstance(adapter, ImageGenerationAdapter):
                raise HTTPException(
                    status_code=400, 
                    detail=f"提供商 {request.provider} 不支持图片生成"
                )
            
            # 构建生成参数
            kwargs = {}
            if request.size:
                kwargs["size"] = request.size
            if request.n:
                kwargs["n"] = request.n
            if request.width:
                kwargs["width"] = request.width
            if request.height:
                kwargs["height"] = request.height
            if request.scale is not None:
                kwargs["scale"] = request.scale
            if request.force_single is not None:
                kwargs["force_single"] = request.force_single
            if request.image_urls:
                kwargs["image_urls"] = request.image_urls
            
            print(f"🕐 **开始同步图片生成** - 提供商: {request.provider}, 超时: {request.timeout}秒")
            
            # 提交图片生成任务
            result = await adapter.generate_image(request.prompt, **kwargs)
            
            # 提取task_id
            task_id = None
            if request.provider == "tongyi_wanxiang":
                if "output" in result and "task_id" in result["output"]:
                    task_id = result["output"]["task_id"]
            elif request.provider == "jimeng":
                if "data" in result and "task_id" in result["data"]:
                    task_id = result["data"]["task_id"]
            
            if not task_id:
                raise HTTPException(status_code=500, detail="无法获取任务ID")
            
            print(f"📋 **任务已提交** - Task ID: {task_id}")
            
            # 轮询等待结果
            import time
            start_time = time.time()
            poll_count = 0
            
            while time.time() - start_time < request.timeout:
                poll_count += 1
                print(f"🔄 **轮询检查 #{poll_count}** - 等待 {request.poll_interval} 秒...")
                
                await asyncio.sleep(request.poll_interval)
                
                try:
                    # 查询任务状态
                    status_result = await adapter.get_task_status(task_id)
                    
                    if request.provider == "tongyi_wanxiang":
                        if "output" in status_result:
                            output = status_result["output"]
                            task_status = output.get("task_status")
                            
                            if task_status == "SUCCEEDED":
                                # 提取图片URL
                                images = []
                                if "results" in output:
                                    for result_item in output["results"]:
                                        if "url" in result_item:
                                            images.append(result_item["url"])
                                
                                print(f"✅ **任务完成** - 生成 {len(images)} 张图片")
                                return ImageGenerationResponse(
                                    task_id=task_id,
                                    status="completed",
                                    images=images,
                                    provider=request.provider,
                                    model=request.model or adapter.model,
                                    message=f"同步任务完成，耗时 {int(time.time() - start_time)} 秒"
                                )
                            elif task_status == "FAILED":
                                error_msg = output.get("message", "未知错误")
                                print(f"❌ **任务失败** - {error_msg}")
                                return ImageGenerationResponse(
                                    task_id=task_id,
                                    status="failed",
                                    provider=request.provider,
                                    model=request.model or adapter.model,
                                    message=f"任务失败: {error_msg}"
                                )
                            else:
                                print(f"⏳ **任务进行中** - 状态: {task_status}")
                    
                    elif request.provider == "jimeng":
                        if "data" in status_result:
                            data = status_result["data"]
                            status = data.get("status")
                            
                            if status == "done" and status_result.get("code") == 10000:
                                # 提取图片URL
                                images = data.get("image_urls", [])
                                
                                print(f"✅ **任务完成** - 生成 {len(images)} 张图片")
                                return ImageGenerationResponse(
                                    task_id=task_id,
                                    status="completed",
                                    images=images,
                                    provider=request.provider,
                                    model=request.model or adapter.model,
                                    message=f"同步任务完成，耗时 {int(time.time() - start_time)} 秒"
                                )
                            elif status == "done":
                                error_msg = status_result.get("message", "未知错误")
                                print(f"❌ **任务失败** - {error_msg}")
                                return ImageGenerationResponse(
                                    task_id=task_id,
                                    status="failed",
                                    provider=request.provider,
                                    model=request.model or adapter.model,
                                    message=f"任务失败: {error_msg}"
                                )
                            else:
                                print(f"⏳ **任务进行中** - 状态: {status}")
                
                except Exception as poll_error:
                    print(f"⚠️ **轮询错误** - {poll_error}")
                    continue
            
            # 超时返回
            elapsed = int(time.time() - start_time)
            print(f"⏰ **任务超时** - 已等待 {elapsed} 秒")
            return ImageGenerationResponse(
                task_id=task_id,
                status="timeout",
                provider=request.provider,
                model=request.model or adapter.model,
                message=f"任务超时（{elapsed}秒），请稍后使用task_id查询结果"
            )
                
        except ConfigurationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except APIError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"未知错误: {e}")
    
    @app.get("/adapters")
    async def list_adapters():
        """列出可用适配器"""
        return {"adapters": model_manager.list_adapters()}
    
    @app.get("/health")
    async def health():
        """健康检查"""
        return {"status": "ok"}
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    print("🚀 **启动AI模型适配器服务 - 简化版**")
    print("📍 **服务地址**: http://localhost:8888")
    print("📖 **API文档**: http://localhost:8888/docs")
    print("🔧 **支持的适配器**:")
    print("   💬 文本聊天: qwen, openrouter, tencent_hunyuan, ollama, lmstudio, openai_compatible")
    print("   👁️ 图像识别: qwen_vision")
    print("   🎨 图片生成: tongyi_wanxiang, jimeng")
    print("\n🎯 **API接口**:")
    print("   - POST /chat: 文本聊天")
    print("   - POST /analyze-image: 图像识别")
    print("   - POST /generate-image: 图片生成")
    print("   - POST /generate-image-sync: 同步图片生成")
    print("   - POST /task-status: 查询任务状态")
    print("   - GET /adapters: 列出可用适配器")
    print("   - GET /health: 健康检查")
    print("\n💡 **环境变量配置**:")
    print("   文本聊天:")
    print("   - QWEN_API_KEY: 通义千问API密钥")
    print("   - OPENROUTER_API_KEY: OpenRouter API密钥") 
    print("   - HUNYUAN_API_KEY: 腾讯云混元API密钥")
    print("   - OLLAMA_HOST: Ollama服务地址 (默认: http://localhost:11434)")
    print("   - LMSTUDIO_HOST: LMStudio服务地址 (默认: http://localhost:1234)")
    print("   - OPENAI_COMPATIBLE_API_KEY: OpenAI兼容API密钥")
    print("   - OPENAI_COMPATIBLE_BASE_URL: OpenAI兼容服务地址 (默认: SiliconFlow)")
    print("   图像识别:")
    print("   - DASHSCOPE_API_KEY: 通义千问视觉API密钥")
    print("   - QWEN_VISION_MODEL: 视觉模型名称 (默认: qwen3-vl-plus)")
    print("   - QWEN_VISION_THINKING: 是否开启思考模式 (默认: false)")
    print("   - QWEN_VISION_THINKING_BUDGET: 思考Token预算 (默认: 500)")
    print("   图片生成:")
    print("   - DASHSCOPE_API_KEY: 通义万象API密钥")
    print("   - JIMENG_ACCESS_KEY: 即梦AI访问密钥")
    print("   - JIMENG_SECRET_KEY: 即梦AI秘密密钥")
    print("\n⚡ **使用python3.11启动**: python3.11 model_adapter.py")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
