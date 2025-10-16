#!/usr/bin/env python3
"""
AI模型适配器 - 安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-model-adapter",
    version="1.0.6",
    author="洛小山",
    author_email="eason@miyang.ai",
    description="一个简化的AI模型适配器，支持文本聊天、图像识别和图片生成功能",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/itshen/ai_adapter",
    project_urls={
        "Bug Tracker": "https://github.com/itshen/ai_adapter/issues",
        "Documentation": "https://github.com/itshen/ai_adapter#readme",
        "Source Code": "https://github.com/itshen/ai_adapter",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-adapter=ai_model_adapter.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, llm, chatbot, image-generation, image-recognition, vision, api-adapter",
    license="MIT",
)
