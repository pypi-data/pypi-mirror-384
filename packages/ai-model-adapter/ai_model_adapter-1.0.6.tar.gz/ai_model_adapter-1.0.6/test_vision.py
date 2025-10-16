#!/usr/bin/env python3
"""
图像识别功能快速测试脚本

用于验证图像识别功能是否正常工作。

Copyright (c) 2025 Miyang Tech (Zhuhai Hengqin) Co., Ltd.
License: MIT
"""

import asyncio
import os
from ai_model_adapter import QwenVisionConfig, QwenVisionAdapter

async def test_vision():
    """测试图像识别功能"""
    print("🧪 **图像识别功能测试**")
    
    # 检查API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量 DASHSCOPE_API_KEY")
        print("💡 示例: export DASHSCOPE_API_KEY='your-api-key'")
        return False
    
    try:
        # 创建配置
        config = QwenVisionConfig(
            api_key=api_key,
            model="qwen3-vl-plus"
        )
        
        # 创建适配器
        adapter = QwenVisionAdapter(config)
        
        # 测试图片
        test_image = "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
        
        print(f"📷 测试图片: {test_image}")
        print("🤖 正在分析...")
        
        # 分析图像
        result = await adapter.analyze_image(
            image_url=test_image,
            text="图中描绘的是什么景象？"
        )
        
        # 检查结果
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"✅ **分析成功**: {content}")
            return True
        else:
            print(f"⚠️ **响应格式异常**: {result}")
            return False
            
    except Exception as e:
        print(f"❌ **测试失败**: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 **AI模型适配器 - 图像识别功能测试**")
    print("=" * 50)
    
    success = await test_vision()
    
    if success:
        print("\n🎉 **测试通过！图像识别功能正常工作**")
        print("📖 **使用示例**: python3.11 vision_example.py")
        print("🌐 **API示例**: python3.11 vision_api_example.py")
    else:
        print("\n❌ **测试失败！请检查配置和网络连接**")

if __name__ == "__main__":
    asyncio.run(main())
