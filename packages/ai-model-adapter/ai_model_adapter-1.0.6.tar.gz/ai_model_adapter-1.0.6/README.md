# AI模型适配器 - 简化版

一个简化的AI模型适配器，专注于**消息收发**和**图片生成**功能。

## 🎯 主要功能

### 💬 文本聊天
- **Qwen (通义千问)**: 阿里云大语言模型
- **OpenRouter**: 多模型聚合平台
- **腾讯云混元**: 腾讯云大语言模型
- **Ollama**: 本地部署模型
- **LMStudio**: 本地模型服务
- **OpenAI兼容**: 支持OpenAI格式的API

### 🎨 图片生成
- **通义万象**: 阿里云图片生成服务
- **即梦AI**: 火山引擎图片生成服务

## 🚀 快速开始

### 方式一：作为Python包安装（推荐）

#### 1. 从PyPI安装（发布后）
```bash
pip install ai-model-adapter
```

#### 2. 从GitHub安装
```bash
pip install git+https://github.com/itshen/ai_adapter.git
```

#### 3. 本地开发安装
```bash
git clone https://github.com/itshen/ai_adapter.git
cd ai_adapter
pip install -e .
```

### 方式二：直接使用源码

#### 1. 安装依赖
```bash
pip install httpx fastapi uvicorn pydantic python-dotenv
```

### 2. 设置环境变量
```bash
# 文本聊天
export QWEN_API_KEY='your-qwen-api-key'
export OPENROUTER_API_KEY='your-openrouter-api-key'
export HUNYUAN_API_KEY='your-hunyuan-api-key'

# 图片生成
export DASHSCOPE_API_KEY='your-dashscope-api-key'
export JIMENG_ACCESS_KEY='your-jimeng-access-key'
export JIMENG_SECRET_KEY='your-jimeng-secret-key'
```

### 3. 启动服务
```bash
python3.11 model_adapter_refactored.py
```

服务将在 http://localhost:8888 启动

### 4. 查看API文档
访问 http://localhost:8888/docs 查看完整的API文档

## 📖 API使用示例

### 文本聊天

#### 使用环境变量中的API密钥
```bash
curl -X POST "http://localhost:8888/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "qwen",
    "model": "qwen-plus"
  }'
```

#### 运行时提供API密钥（优先级更高）
```bash
curl -X POST "http://localhost:8888/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "qwen",
    "model": "qwen-plus",
    "api_key": "your-runtime-api-key"
  }'
```

### 流式聊天
```bash
curl -X POST "http://localhost:8888/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "qwen",
    "model":"qwen-plus",
    "stream": true
  }'
```

### 图片生成

系统提供两种图片生成模式：

#### 🔄 异步模式（推荐大批量）
提交任务后立即返回task_id，需要轮询查询结果：

```bash
# 1. 提交异步任务
curl -X POST "http://localhost:8888/generate-image" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一朵盛开的樱花",
    "provider": "tongyi_wanxiang",
    "api_key": "your-runtime-dashscope-key",
    "size": "1024*1024"
  }'

# 返回: {"task_id": "xxx", "status": "pending", ...}

# 2. 获取任务结果（推荐）
curl -X POST "http://localhost:8888/get-result" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "xxx",
    "provider": "tongyi_wanxiang",
    "api_key": "your-runtime-dashscope-key"
  }'

# 返回简化结果: {"success": true, "status": "completed", "images": ["url1"], ...}

# 或查询详细状态
curl -X POST "http://localhost:8888/task-status" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "xxx",
    "provider": "tongyi_wanxiang",
    "api_key": "your-runtime-dashscope-key"
  }'
```

#### ⏳ 同步模式（推荐单个图片）
阻塞等待直到任务完成再返回结果：

```bash
curl -X POST "http://localhost:8888/generate-image-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一朵盛开的樱花",
    "provider": "tongyi_wanxiang",
    "api_key": "your-runtime-dashscope-key",
    "size": "1024*1024",
    "timeout": 300,
    "poll_interval": 3
  }'

# 直接返回: {"status": "completed", "images": ["url1", "url2"], ...}
```

#### 🔧 同步模式参数说明
- `timeout`: 超时时间（秒），默认300秒（5分钟）
- `poll_interval`: 轮询间隔（秒），默认3秒

### 查询任务状态
```bash
curl -X POST "http://localhost:8888/task-status" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "your_task_id",
    "provider": "tongyi_wanxiang"
  }'
```

## 🔧 支持的适配器

| 适配器 | 类型 | 说明 |
|--------|------|------|
| qwen | 文本聊天 | 通义千问，支持多种模型 |
| openrouter | 文本聊天 | 多模型聚合平台 |
| tencent_hunyuan | 文本聊天 | 腾讯云混元，OpenAI兼容 |
| ollama | 文本聊天 | 本地部署，无需API密钥 |
| lmstudio | 文本聊天 | 本地模型服务 |
| openai_compatible | 文本聊天 | OpenAI格式兼容 |
| tongyi_wanxiang | 图片生成 | 通义万象2.2，异步任务 |
| jimeng | 图片生成 | 即梦AI 4.0，高质量输出 |

## 📝 代码示例

### 作为Python包使用（推荐）

#### 基本使用
```python
import asyncio
from ai_model_adapter import ModelManager

async def main():
    manager = ModelManager()
    
    # 文本聊天
    adapter = manager.get_adapter("qwen", {
        "api_key": "your-api-key",
        "model": "qwen-flash"
    })
    
    messages = [{"role": "user", "content": "你好"}]
    response = await adapter.chat(messages)
    print(response)
    
    # 图片生成
    image_adapter = manager.get_adapter("tongyi_wanxiang", {
        "api_key": "your-api-key"
    })
    
    result = await image_adapter.generate_image("一朵樱花")
    print(result)

asyncio.run(main())
```

#### 直接导入适配器
```python
import asyncio
from ai_model_adapter import QwenAdapter, TongyiWanxiangAdapter, QwenConfig, TongyiWanxiangConfig

async def main():
    # 使用配置类
    qwen_config = QwenConfig(
        api_key="your-api-key",
        model="qwen-flash"
    )
    qwen_adapter = QwenAdapter(qwen_config)
    
    # 文本聊天
    messages = [{"role": "user", "content": "你好"}]
    response = await qwen_adapter.chat(messages)
    print(response)
    
    # 图片生成
    image_config = TongyiWanxiangConfig(api_key="your-api-key")
    image_adapter = TongyiWanxiangAdapter(image_config)
    
    result = await image_adapter.generate_image("一朵樱花")
    print(result)

asyncio.run(main())
```

#### 创建FastAPI应用
```python
from ai_model_adapter import create_app

# 创建FastAPI应用实例
app = create_app()

# 可以添加自定义路由
@app.get("/custom")
async def custom_endpoint():
    return {"message": "自定义端点"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
```

### 直接使用源码
```python
import asyncio
from model_adapter import ModelManager

async def main():
    manager = ModelManager()
    
    # 文本聊天
    adapter = manager.get_adapter("qwen", {
        "api_key": "your-api-key",
        "model": "qwen-flash"
    })
    
    messages = [{"role": "user", "content": "你好"}]
    response = await adapter.chat(messages)
    print(response)
    
    # 图片生成
    image_adapter = manager.get_adapter("tongyi_wanxiang", {
        "api_key": "your-api-key"
    })
    
    result = await image_adapter.generate_image("一朵樱花")
    print(result)

asyncio.run(main())
```

## 🌟 特性

- ✅ **简化设计**: 移除复杂的工具调用功能，专注核心功能
- ✅ **统一接口**: 所有适配器使用相同的接口规范
- ✅ **流式支持**: 支持实时流式文本输出
- ✅ **异步任务**: 图片生成支持异步任务查询
- ✅ **错误处理**: 详细的错误信息和自动重试
- ✅ **智能配置**: 支持运行时配置优先，环境变量回退
- ✅ **类型安全**: 使用Pydantic进行数据验证

## ⚙️ 配置优先级

系统采用智能配置优先级机制：

### 🥇 第一优先级：运行时API参数
```bash
# API调用时直接提供密钥（最高优先级）
curl -X POST "http://localhost:8888/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "provider": "qwen",
    "model": "qwen-plus",
    "api_key": "runtime-key"
  }'
```

### 🥈 第二优先级：环境变量
```bash
# 设置环境变量作为默认配置
export QWEN_API_KEY='your-api-key'
```

### ❌ 没有配置：报错
如果既没有运行时配置，也没有环境变量，系统会返回配置错误。

### 💡 使用场景
- **开发环境**: 设置环境变量，方便本地调试
- **生产环境**: 通过API参数传入，提高安全性
- **测试环境**: 运行时覆盖特定配置进行测试

## 🔗 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat` | POST | 文本聊天接口 |
| `/generate-image` | POST | 异步图片生成接口 |
| `/generate-image-sync` | POST | 同步图片生成接口（阻塞等待） |
| `/get-result` | POST | 获取异步任务结果（简化版） |
| `/task-status` | POST | 查询任务状态（详细信息） |
| `/adapters` | GET | 列出可用适配器 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | API文档 |

## 📋 环境变量

### 文本聊天适配器
```bash
# Qwen (与通义万象共享DashScope密钥)
QWEN_API_KEY=your-dashscope-api-key
# 或者使用 DASHSCOPE_API_KEY=your-dashscope-api-key
QWEN_MODEL=qwen-flash

# OpenRouter  
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=qwen/qwen3-next-80b-a3b-instruct

# 腾讯云混元
HUNYUAN_API_KEY=your-hunyuan-api-key
HUNYUAN_MODEL=hunyuan-turbos-latest

# Ollama (本地)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:0.6b

# LMStudio (本地)
LMSTUDIO_HOST=http://localhost:1234
LMSTUDIO_MODEL=local-model

# OpenAI兼容
OPENAI_COMPATIBLE_API_KEY=your-api-key
OPENAI_COMPATIBLE_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_COMPATIBLE_MODEL=Qwen/Qwen3-Coder-30B-A3B-Instruct
```

### 图片生成适配器
```bash
# 通义万象 (与Qwen共享DashScope密钥)
DASHSCOPE_API_KEY=your-dashscope-api-key
# 或者使用 QWEN_API_KEY=your-dashscope-api-key
TONGYI_WANXIANG_MODEL=wan2.2-t2i-flash

# 即梦AI
JIMENG_ACCESS_KEY=your-jimeng-access-key
JIMENG_SECRET_KEY=your-jimeng-secret-key
JIMENG_MODEL=jimeng_t2i_v40
```

## 🧪 运行演示

```bash
# 运行完整演示
python3.11 demo.py

# 启动API服务（源码方式）
python3.11 model_adapter.py

# 启动API服务（包安装方式）
python3.11 -c "from ai_model_adapter import create_app; import uvicorn; uvicorn.run(create_app(), host='0.0.0.0', port=8888)"
```

## 📦 发布到PyPI

### 构建包
```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 检查包
twine check dist/*
```

### 发布到PyPI
```bash
# 发布到测试PyPI
twine upload --repository testpypi dist/*

# 发布到正式PyPI
twine upload dist/*
```

### 从测试PyPI安装
```bash
pip install --index-url https://test.pypi.org/simple/ ai-model-adapter
```

## 📄 许可证

MIT License

Copyright (c) 2025 Miyang Tech (Zhuhai Hengqin) Co., Ltd.

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 联系方式

- GitHub: https://github.com/itshen/
- 项目地址: https://github.com/itshen/ai_adapter