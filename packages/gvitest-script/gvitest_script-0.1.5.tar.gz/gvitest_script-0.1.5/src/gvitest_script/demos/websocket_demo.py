#!/usr/bin/env python3
"""
WebSocket演示脚本

演示WebSocket实时推送功能，包括：
- 全局日志流推送
- 任务日志流推送
- 全局状态流推送
- 任务状态流推送

使用方法：
    python -m src.gvitest_script.demos.websocket_demo
"""

import asyncio
import json
import logging
import sys
import time
import threading
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from gvitest_script.service.script import create_script_service
from gvitest_script.service.websocket_server import create_websocket_server


PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT / "script_workspace"


async def test_websocket_connection():
    """测试WebSocket连接"""
    import websockets
    
    print("🔌 测试WebSocket连接...")
    
    # 测试全局日志流
    try:
        uri = 'ws://127.0.0.1:8090/logs/realtime'
        print(f"📡 连接到全局日志流: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ 全局日志流连接成功!")
            
            # 等待接收消息
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 收到消息 {i+1}: {data.get('type', 'unknown')}")
                    if data.get('type') == 'connected':
                        print(f"   {data.get('message')}")
                except asyncio.TimeoutError:
                    print(f"⏰ 等待消息超时 {i+1}")
                    break
                    
    except Exception as e:
        print(f"❌ 全局日志流连接失败: {e}")
    
    # 测试任务日志流
    try:
        uri = 'ws://127.0.0.1:8090/logs/script_basic/realtime'
        print(f"\n📡 连接到任务日志流: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ 任务日志流连接成功!")
            
            # 等待接收消息
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 收到消息 {i+1}: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    print(f"⏰ 等待消息超时 {i+1}")
                    break
                    
    except Exception as e:
        print(f"❌ 任务日志流连接失败: {e}")
    
    # 测试全局状态流
    try:
        uri = 'ws://127.0.0.1:8090/status/realtime'
        print(f"\n📊 连接到全局状态流: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ 全局状态流连接成功!")
            
            # 等待接收消息
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 收到消息 {i+1}: {data.get('type', 'unknown')}")
                    if data.get('type') == 'connected':
                        print(f"   {data.get('message')}")
                except asyncio.TimeoutError:
                    print(f"⏰ 等待消息超时 {i+1}")
                    break
                    
    except Exception as e:
        print(f"❌ 全局状态流连接失败: {e}")
    
    # 测试任务状态流
    try:
        uri = 'ws://127.0.0.1:8090/status/script_basic/realtime'
        print(f"\n📊 连接到任务状态流: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ 任务状态流连接成功!")
            
            # 等待接收消息
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 收到消息 {i+1}: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    print(f"⏰ 等待消息超时 {i+1}")
                    break
                    
    except Exception as e:
        print(f"❌ 任务状态流连接失败: {e}")


async def demo_websocket_realtime():
    """演示WebSocket实时推送功能"""
    print("🚀 开始WebSocket实时推送演示")
    
    # 1. 测试WebSocket连接
    print("\n🔌 1. 测试WebSocket连接...")
    await test_websocket_connection()
    
    # 2. 生成并执行脚本以产生日志和状态更新
    print("\n📝 2. 生成并执行脚本...")
    service = create_script_service(
        workspace_root=WORKSPACE_ROOT,
        log_level="INFO",
        enable_file_server=True,
        file_server_port=8080
    )
    
    # 生成脚本
    example_data = {
        "script_id": "websocket_demo",
        "action_sequence": [
            {
                "id": "step1",
                "step_name": "WebSocket演示步骤",
                "operation_type": "click",
                "element_info": {"x": 100, "y": 200}
            }
        ],
        "expected_results": {}
    }
    
    try:
        result = await service.generate_script(example_data)
        print(f"✅ 脚本生成: {result.get('success', False)}")
        
        if result.get('success'):
            # 执行脚本
            execution_data = {"script_id": "websocket_demo"}
            exec_result = await service.execute_script(execution_data)
            print(f"✅ 脚本执行: {exec_result.get('success', False)}")
            
            # 等待脚本执行产生日志
            print("⏳ 等待脚本执行产生日志...")
            await asyncio.sleep(3)
            
    except Exception as e:
        print(f"❌ 脚本操作失败: {e}")
    
    print("\n🎉 WebSocket演示完成!")
    print(f"\n🌐 WebSocket服务器端点:")
    print(f"   - 全局日志流: ws://127.0.0.1:8090/logs/realtime")
    print(f"   - 任务日志流: ws://127.0.0.1:8090/logs/{{script_id}}/realtime")
    print(f"   - 全局状态流: ws://127.0.0.1:8090/status/realtime")
    print(f"   - 任务状态流: ws://127.0.0.1:8090/status/{{script_id}}/realtime")
    print(f"\n💡 可以使用WebSocket客户端连接到上述地址测试实时推送功能")


def start_websocket_server(websocket_server):
    """在单独线程中启动WebSocket服务器"""
    try:
        websocket_server.run(host="127.0.0.1", port=8090)
    except Exception as e:
        print(f"❌ WebSocket服务器启动失败: {e}")


def main():
    """WebSocket演示主函数"""
    try:
        # 创建脚本服务
        service = create_script_service(
            workspace_root=WORKSPACE_ROOT,
            log_level="INFO",
            enable_file_server=True,
            file_server_port=8080
        )
        
        # 创建WebSocket服务器
        websocket_server = create_websocket_server(
            workspace_root=WORKSPACE_ROOT,
            log_service=service.log_query_service,
            status_service=service.status_tracking_service
        )
        
        # 在单独线程中启动WebSocket服务器
        print("🌐 启动WebSocket服务器...")
        server_thread = threading.Thread(
            target=start_websocket_server, 
            args=(websocket_server,),
            daemon=True
        )
        server_thread.start()
        
        # 等待WebSocket服务启动
        time.sleep(2)
        
        # 运行WebSocket演示
        asyncio.run(demo_websocket_realtime())
        
        # 保持程序运行，让WebSocket服务继续工作
        print("\n🔄 WebSocket服务器继续运行中... (按Ctrl+C停止)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  服务已停止")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  演示已停止")
    except Exception as e:
        print(f"\n❌ 演示运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
