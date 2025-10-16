# 🔐 安全配置指南

## API密钥管理

为了保护你的API密钥安全，本项目使用环境变量来管理敏感信息。**绝不要将API密钥直接写在代码中！**

### 🚀 快速开始

1. **复制环境变量模板**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件，填入你的真实API密钥**
   ```bash
   # 使用你喜欢的编辑器
   nano .env
   # 或者
   code .env
   ```

3. **填入API密钥**
   ```env
   # Qwen (通义千问)
   QWEN_API_KEY=sk-your-real-qwen-api-key-here
   QWEN_MODEL=qwen-flash
   
   # OpenRouter
   OPENROUTER_API_KEY=sk-or-v1-your-real-openrouter-key-here
   OPENROUTER_MODEL=qwen/qwen3-next-80b-a3b-instruct
   
   # 腾讯云混元
   HUNYUAN_API_KEY=sk-your-real-hunyuan-key-here
   HUNYUAN_MODEL=hunyuan-turbos-latest
   
   # 通义万象 (图片生成)
   DASHSCOPE_API_KEY=sk-your-real-dashscope-key-here
   TONGYI_WANXIANG_MODEL=wan2.2-t2i-flash
   ```

### 🛡️ 安全特性

- ✅ **`.env` 文件已被 `.gitignore` 忽略** - 不会被提交到Git仓库
- ✅ **提供 `.env.example` 模板** - 其他开发者可以快速配置
- ✅ **代码中无硬编码密钥** - 所有敏感信息都从环境变量读取
- ✅ **自动检测缺失密钥** - demo会跳过未配置的API测试

### 📁 文件说明

| 文件 | 用途 | 是否提交到Git |
|------|------|---------------|
| `.env` | 包含真实API密钥的配置文件 | ❌ 不提交 (被.gitignore忽略) |
| `.env.example` | 环境变量模板文件 | ✅ 提交 (不含真实密钥) |
| `.gitignore` | Git忽略规则文件 | ✅ 提交 |

### 🔍 验证配置

运行demo来验证你的API密钥配置：

```bash
python3.11 demo.py
```

- ✅ 如果API密钥配置正确，会显示测试成功
- ⚠️ 如果API密钥未配置，会显示跳过测试的提示

### 🚨 重要提醒

1. **永远不要将 `.env` 文件提交到Git仓库**
2. **不要在代码中硬编码API密钥**
3. **不要在聊天记录、截图中暴露API密钥**
4. **定期轮换API密钥**
5. **为不同环境使用不同的API密钥**

### 🔄 环境变量优先级

1. `.env` 文件中的变量
2. 系统环境变量
3. 代码中的默认值

### 💡 最佳实践

- 为开发、测试、生产环境使用不同的API密钥
- 定期检查API密钥的使用情况和权限
- 使用最小权限原则，只给API密钥必要的权限
- 监控API密钥的使用情况，及时发现异常

### 🆘 如果API密钥泄露了怎么办？

1. **立即撤销泄露的API密钥**
2. **生成新的API密钥**
3. **更新 `.env` 文件**
4. **检查是否有异常使用记录**
5. **考虑更改相关账户密码**
