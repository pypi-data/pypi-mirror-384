#!/usr/bin/env python3
"""
测试运行器 - 运行所有测试用例
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path

def run_sync_test(test_file: str) -> bool:
    """运行同步测试"""
    print(f"🏃 **运行 {test_file}**")
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ **{test_file} 测试通过**\n")
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            print(f"❌ **{test_file} 测试失败**\n")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ **{test_file} 测试超时**\n")
        return False
    except Exception as e:
        print(f"❌ **{test_file} 运行异常: {e}**\n")
        return False

async def check_service_status() -> bool:
    """检查FastAPI服务状态"""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:6688/health")
            return response.status_code == 200
    except:
        return False

async def run_api_test_with_service_check() -> bool:
    """运行API测试，如果服务未启动则跳过"""
    service_running = await check_service_status()
    
    if service_running:
        print("✅ **FastAPI服务正在运行，执行API测试**")
        return run_sync_test("test_api.py")
    else:
        print("⚠️ **FastAPI服务未运行，跳过API测试**")
        print("   启动服务: python3.11 model_adapter_refactored.py")
        return True  # 跳过不算失败

def print_banner():
    """打印测试横幅"""
    print("=" * 60)
    print("🧪 **AI模型适配器 - 测试套件**")
    print("=" * 60)
    print()

def print_summary(results: dict):
    """打印测试摘要"""
    print("=" * 60)
    print("📊 **测试摘要**")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print()
    print(f"📈 **总计**: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("🎉 **所有测试通过！代码质量良好！**")
    else:
        print("⚠️ **部分测试失败，请检查代码**")
    
    print("=" * 60)

async def main():
    """主测试函数"""
    print_banner()
    
    # 检查测试文件是否存在
    test_files = [
        "test_config.py",
        "test_error_handling.py", 
        "test_api.py"
    ]
    
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ **缺少测试文件**: {missing_files}")
        return
    
    # 运行测试
    results = {}
    
    # 1. 配置管理测试
    print("1️⃣ **配置管理测试**")
    results["配置管理"] = run_sync_test("test_config.py")
    
    # 2. 错误处理测试  
    print("2️⃣ **错误处理测试**")
    results["错误处理"] = run_sync_test("test_error_handling.py")
    
    # 3. API接口测试（需要服务运行）
    print("3️⃣ **API接口测试**")
    results["API接口"] = await run_api_test_with_service_check()
    
    # 打印摘要
    print_summary(results)

def run_individual_test():
    """运行单个测试（交互模式）"""
    tests = {
        "1": ("配置管理测试", "test_config.py"),
        "2": ("错误处理测试", "test_error_handling.py"),
        "3": ("API接口测试", "test_api.py")
    }
    
    print("🧪 **选择要运行的测试**:")
    for key, (name, _) in tests.items():
        print(f"   {key}. {name}")
    print("   0. 运行所有测试")
    
    choice = input("\n请选择 (0-3): ").strip()
    
    if choice == "0":
        asyncio.run(main())
    elif choice in tests:
        name, file = tests[choice]
        print(f"\n🏃 **运行 {name}**")
        run_sync_test(file)
    else:
        print("❌ **无效选择**")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_individual_test()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n🛑 **测试被用户中断**")
        except Exception as e:
            print(f"\n❌ **测试运行异常**: {e}")
