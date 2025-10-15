#!/usr/bin/env python3
"""
Script Server - 核心功能演示脚本

演示独立脚本生成服务的核心功能，包括：
- 脚本生成
- 脚本执行
- 执行结果查询
- 日志查询

使用方法：
    python -m src.gvitest_script.demos.demo
"""

import json
import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from gvitest_script.service.script import create_script_service


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT / "script_workspace"


async def test_script_generation(service):
    example_data = json.load(open(PROJECT_ROOT / "examples/basic_script_request_v2.json"))
    try:
        result = await service.generate_script(example_data)
        print("*" * 100)
        print(f"生成脚本结果: {result}")
        print("*" * 100)
    except Exception as e:
        print(f"❌ 错误: {e}")

async def test_script_execution(service):
    script_id = "script_basic"
    try:
        execution_data = {
            "script_id": script_id,
        }
        result = await service.execute_script(execution_data)
        print("*" * 100)
        print(f"执行脚本结果: {result}")
        print("*" * 100)
        
        # 固定等待5秒
        print("⏳ 等待脚本执行5秒...")
        await asyncio.sleep(5)

    except Exception as e:
        print(f"❌ 错误: {e}")


async def test_script_execution_result(service):
    script_id = "script_basic"
    try:
        result = await service.get_final_execution_result(script_id)
        print("*" * 100)
        print(f"执行结果: {result}")
        print("*" * 100)
    except Exception as e:
        print(f"❌ 错误: {e}")

async def get_latest_log(service):
    script_id = "script_basic"
    try:
        result = await service.get_latest_log(script_id, lines=5)
        print("*" * 100)
        print(f"最新日志: {result}")
        print("*" * 100)
    except Exception as e:
        print(f"❌ 错误: {e}")


async def demo(service):
    """演示脚本生成服务的核心功能"""
    print("🚀 开始脚本生成服务演示")
    
    # 1. 生成脚本
    print("\n📝 1. 生成脚本...")
    await test_script_generation(service)
    
    # 2. 执行脚本
    print("\n▶️  2. 执行脚本...")
    await test_script_execution(service)
    
    # 3. 获取执行结果
    print("\n📊 3. 获取执行结果...")
    await test_script_execution_result(service)
    
    # 4. 查询日志
    print("\n📋 4. 查询最新日志...")
    await get_latest_log(service)
    
    print("\n🎉 演示完成!")


def main():
    """演示函数 - 运行脚本生成服务核心功能演示"""
    try:
        # 创建服务
        service = create_script_service(
            workspace_root=WORKSPACE_ROOT,
            log_level="INFO",
            enable_file_server=True,
            file_server_port=8080
        )
        
        # 运行演示
        asyncio.run(demo(service))
            
    except KeyboardInterrupt:
        print("\n\n⏹️  演示已停止")
    except Exception as e:
        print(f"\n❌ 演示运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
