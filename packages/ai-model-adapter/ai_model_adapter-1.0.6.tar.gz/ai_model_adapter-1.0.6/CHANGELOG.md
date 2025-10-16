# 更新日志 (Changelog)

本文档记录了 ai-model-adapter 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.6] - 2025-10-15

### 新增 (Added)
- 🎉 **图像识别功能**: 添加了基于通义千问视觉模型 (qwen3-vl-plus) 的图像识别能力
  - `QwenVisionConfig`: 视觉模型配置类
  - `VisionAdapter`: 视觉识别适配器基类
  - `QwenVisionAdapter`: 通义千问视觉适配器实现
  - `POST /analyze-image`: 图像分析 HTTP API 接口
  - 支持流式和非流式图像分析
  - 支持思考模式（深度推理分析）
  
- 📚 **使用示例和文档**:
  - `vision_example.py`: 完整的 Python SDK 使用示例
  - `vision_api_example.py`: HTTP API 调用示例
  - `test_vision.py`: 快速功能测试脚本
  - `demo_vision.py`: 交互式演示脚本
  - `VISION_GUIDE.md`: 详细的图像识别使用指南
  - `VISION_SUMMARY.md`: 功能实现总结

### 改进 (Changed)
- 更新了适配器工厂，支持 `qwen_vision` 适配器
- 更新了配置管理器，支持视觉模型配置
- 扩展了 `__init__.py`，导出视觉相关的类和配置
- 更新了服务启动信息，显示图像识别功能

### 技术细节 (Technical)
- 实现了 OpenAI 兼容的图像分析 API 格式
- 支持思考模式参数配置 (`enable_thinking`, `thinking_budget`)
- 完整的错误处理和重试机制
- 支持 temperature、max_tokens、top_p 等生成参数

## [1.0.5] - 2025-09-30

### 新增 (Added)
- 腾讯云混元模型支持
- 图片生成功能增强（通义万象、即梦AI）
- 同步图片生成接口 (`/generate-image-sync`)

### 改进 (Changed)
- 优化了适配器架构
- 改进了错误处理机制
- 更新了文档和使用指南

### 修复 (Fixed)
- 修复了一些已知的 bug
- 改进了 API 响应格式

## [1.0.0] - 2025-09-01

### 新增 (Added)
- 初始版本发布
- 支持多种文本聊天模型
  - Qwen (通义千问)
  - OpenRouter
  - Ollama
  - LMStudio
  - OpenAI兼容接口
- 基础图片生成功能
- FastAPI REST API 服务
- CLI 命令行工具
- 完整的文档和示例

---

## 版本说明

### 版本号格式: MAJOR.MINOR.PATCH

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能性新增
- **PATCH**: 向后兼容的问题修复

### 变更类型

- `Added`: 新功能
- `Changed`: 现有功能的变更
- `Deprecated`: 即将废弃的功能
- `Removed`: 已删除的功能
- `Fixed`: 问题修复
- `Security`: 安全性相关的修复

---

**维护者**: 洛小山 (eason@miyang.ai)  
**许可证**: MIT  
**项目主页**: https://github.com/itshen/ai_adapter