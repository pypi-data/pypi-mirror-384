#!/usr/bin/env python3
"""
AI模型适配器命令行接口
"""

import argparse
import asyncio
import sys
import uvicorn
from .model_adapter import create_app

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="AI模型适配器命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  ai-adapter serve                    # 启动API服务器（默认端口8888）
  ai-adapter serve --port 9000        # 启动API服务器（指定端口）
  ai-adapter serve --host 0.0.0.0     # 启动API服务器（指定主机）
  ai-adapter --version                # 显示版本信息
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="ai-model-adapter 1.0.6"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # serve 子命令
    serve_parser = subparsers.add_parser("serve", help="启动API服务器")
    serve_parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="服务器主机地址 (默认: 127.0.0.1)"
    )
    serve_parser.add_argument(
        "--port", 
        type=int, 
        default=8888, 
        help="服务器端口 (默认: 8888)"
    )
    serve_parser.add_argument(
        "--reload", 
        action="store_true", 
        help="启用自动重载（开发模式）"
    )
    serve_parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="日志级别 (默认: info)"
    )
    
    args = parser.parse_args()
    
    if args.command == "serve":
        serve_command(args)
    elif args.command is None:
        parser.print_help()
        sys.exit(1)

def serve_command(args):
    """启动API服务器"""
    print(f"🚀 启动AI模型适配器服务器...")
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"🔧 日志级别: {args.log_level}")
    
    if args.reload:
        print("🔄 自动重载模式已启用")
    
    print("=" * 50)
    
    try:
        app = create_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
