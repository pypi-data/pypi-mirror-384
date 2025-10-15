"""
纯WebSocket服务器
为独立服务提供WebSocket接口，实现实时日志和状态推送
不依赖HTTP服务器
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import websockets
from websockets.server import WebSocketServerProtocol

from .log_query import LogQueryService
from .status_tracking import StatusTrackingService


class WebSocketServer:
    """纯WebSocket服务器"""
    
    def __init__(self, workspace_root: Path, log_service: LogQueryService, status_service: StatusTrackingService):
        self.workspace_root = workspace_root
        self.log_service = log_service
        self.status_service = status_service
        
        # WebSocket连接管理
        self.log_connections: Dict[str, List[WebSocketServerProtocol]] = {}  # script_id -> List[WebSocket]
        self.global_log_connections: List[WebSocketServerProtocol] = []  # 全局日志连接
        self.status_connections: Dict[str, List[WebSocketServerProtocol]] = {}  # script_id -> List[WebSocket]
        self.global_status_connections: List[WebSocketServerProtocol] = []  # 全局状态连接
        
        # 监控任务
        self.monitoring_tasks: Set[asyncio.Task] = set()
    
    async def handle_log_connection(self, websocket: WebSocketServerProtocol, script_id: str):
        """处理单个任务的日志WebSocket连接"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}" if websocket.remote_address else "unknown"
        logging.info(f"📡 日志WebSocket连接: script_id={script_id}, client={client_info}")
        
        try:
            # 添加到连接池
            if script_id not in self.log_connections:
                self.log_connections[script_id] = []
            self.log_connections[script_id].append(websocket)
            
            # 发送当前日志内容
            await self._send_current_log(websocket, script_id)
            
            # 开始实时监控
            await self._monitor_log_changes(websocket, script_id)
            
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"🔌 日志WebSocket正常断开: script_id={script_id}, client={client_info}")
            self._remove_log_connection(script_id, websocket)
        except Exception as e:
            logging.error(f"❌ 日志WebSocket异常: script_id={script_id}, client={client_info}, error={e}")
            self._remove_log_connection(script_id, websocket)
    
    async def handle_global_log_connection(self, websocket: WebSocketServerProtocol):
        """处理全局日志WebSocket连接"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}" if websocket.remote_address else "unknown"
        logging.info(f"🌐 全局日志WebSocket连接: client={client_info}")
        
        try:
            # 添加到全局连接池
            self.global_log_connections.append(websocket)
            
            # 发送欢迎消息
            await websocket.send(json.dumps({
                "type": "connected",
                "message": "已连接到全局日志流",
                "timestamp": datetime.now().isoformat()
            }))
            
            # 开始全局日志监控
            await self._monitor_global_log_changes(websocket)
            
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"🔌 全局日志WebSocket正常断开: client={client_info}")
            self._remove_global_log_connection(websocket)
        except Exception as e:
            logging.error(f"❌ 全局日志WebSocket异常: client={client_info}, error={e}")
            self._remove_global_log_connection(websocket)
    
    async def handle_status_connection(self, websocket: WebSocketServerProtocol, script_id: str):
        """处理单个任务的状态WebSocket连接"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}" if websocket.remote_address else "unknown"
        logging.info(f"📊 状态WebSocket连接: script_id={script_id}, client={client_info}")
        
        try:
            # 添加到连接池
            if script_id not in self.status_connections:
                self.status_connections[script_id] = []
            self.status_connections[script_id].append(websocket)
            
            # 发送当前状态
            await self._send_current_status(websocket, script_id)
            
            # 开始实时监控
            await self._monitor_status_changes(websocket, script_id)
            
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"🔌 状态WebSocket正常断开: script_id={script_id}, client={client_info}")
            self._remove_status_connection(script_id, websocket)
        except Exception as e:
            logging.error(f"❌ 状态WebSocket异常: script_id={script_id}, client={client_info}, error={e}")
            self._remove_status_connection(script_id, websocket)
    
    async def handle_global_status_connection(self, websocket: WebSocketServerProtocol):
        """处理全局状态WebSocket连接"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}" if websocket.remote_address else "unknown"
        logging.info(f"🌐 全局状态WebSocket连接: client={client_info}")
        
        try:
            # 添加到全局连接池
            self.global_status_connections.append(websocket)
            
            # 发送欢迎消息
            await websocket.send(json.dumps({
                "type": "connected",
                "message": "已连接到全局状态流",
                "timestamp": datetime.now().isoformat()
            }))
            
            # 开始全局状态监控
            await self._monitor_global_status_changes(websocket)
            
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"🔌 全局状态WebSocket正常断开: client={client_info}")
            self._remove_global_status_connection(websocket)
        except Exception as e:
            logging.error(f"❌ 全局状态WebSocket异常: client={client_info}, error={e}")
            self._remove_global_status_connection(websocket)
    
    async def _send_current_log(self, websocket: WebSocketServerProtocol, script_id: str):
        """发送当前日志内容"""
        try:
            # 获取最新日志
            log_dir = self.workspace_root / script_id / "logs"
            if not log_dir.exists():
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"任务 {script_id} 的日志目录不存在"
                }))
                return
            
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                await websocket.send(json.dumps({
                    "type": "info",
                    "message": f"任务 {script_id} 暂无日志文件"
                }))
                return
            
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # 发送当前日志内容（最后50行）
            log_response = await self.log_service._read_log_content(script_id, latest_log.name, 50, True)
            await websocket.send(json.dumps({
                "type": "initial",
                "data": log_response.to_dict()
            }))
            
        except Exception as e:
            logging.error(f"发送当前日志失败: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"发送日志失败: {str(e)}"
            }))
    
    async def _send_current_status(self, websocket: WebSocketServerProtocol, script_id: str):
        """发送当前状态"""
        try:
            status_data = await self.status_service._read_status_file(script_id)
            if status_data:
                await websocket.send(json.dumps({
                    "type": "current_status",
                    "data": status_data
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"任务 {script_id} 状态文件不存在"
                }))
        except Exception as e:
            logging.error(f"发送当前状态失败: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"发送状态失败: {str(e)}"
            }))
    
    async def _monitor_log_changes(self, websocket: WebSocketServerProtocol, script_id: str):
        """监控日志文件变化"""
        log_dir = self.workspace_root / script_id / "logs"
        last_size = 0
        last_file = None
        
        while True:
            try:
                # 找到最新的日志文件
                log_files = list(log_dir.glob("*.log"))
                if not log_files:
                    await asyncio.sleep(1)
                    continue
                
                current_file = max(log_files, key=lambda f: f.stat().st_mtime)
                current_size = current_file.stat().st_size
                
                # 如果文件变化或大小变化
                if current_file != last_file or current_size != last_size:
                    if current_file != last_file:
                        # 新文件，发送完整内容
                        log_response = await self.log_service._read_log_content(script_id, current_file.name, 50, True)
                        await websocket.send(json.dumps({
                            "type": "new_file",
                            "data": log_response.to_dict()
                        }))
                    elif current_size > last_size:
                        # 文件增长，发送新增内容
                        await self._send_incremental_log_content(websocket, current_file, last_size)
                    
                    last_file = current_file
                    last_size = current_size
                
                await asyncio.sleep(0.5)  # 500ms检查一次
                
            except websockets.exceptions.ConnectionClosed:
                logging.info("日志WebSocket连接已断开，退出监控循环")
                break
            except Exception as e:
                logging.error(f"监控日志变化异常: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_status_changes(self, websocket: WebSocketServerProtocol, script_id: str):
        """监控状态文件变化"""
        status_file = self.workspace_root / script_id / "status" / "real_time_status.json"
        last_mtime = 0
        
        while True:
            try:
                # 检查状态文件是否变化
                if status_file.exists():
                    current_mtime = status_file.stat().st_mtime
                    if current_mtime > last_mtime:
                        # 文件已更新，发送新状态
                        status_data = await self.status_service._read_status_file(script_id)
                        if status_data:
                            await websocket.send(json.dumps({
                                "type": "status_update",
                                "data": status_data,
                                "timestamp": datetime.now().isoformat()
                            }))
                        last_mtime = current_mtime
                
                await asyncio.sleep(0.5)  # 500ms检查一次
                
            except websockets.exceptions.ConnectionClosed:
                logging.info("状态WebSocket连接已断开，退出监控循环")
                break
            except Exception as e:
                logging.error(f"监控状态变化异常: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_global_log_changes(self, websocket: WebSocketServerProtocol):
        """监控全局日志文件变化"""
        monitored_files = {}  # file_path -> last_size
        
        while True:
            try:
                # 扫描所有任务的日志目录
                for task_dir in self.workspace_root.iterdir():
                    if not task_dir.is_dir():
                        continue
                    
                    script_id = task_dir.name
                    log_dir = task_dir / "logs"
                    if not log_dir.exists():
                        continue
                    
                    # 检查该任务下的所有日志文件
                    for log_file in log_dir.glob("*.log"):
                        try:
                            current_size = log_file.stat().st_size
                            file_path = str(log_file)
                            
                            # 如果是新文件或文件增长了
                            if file_path not in monitored_files:
                                # 新文件，发送最后10行
                                monitored_files[file_path] = current_size
                                await self._send_global_log_update(websocket, task_dir.name, log_file, "new_file", lines=10)
                            elif current_size > monitored_files[file_path]:
                                # 文件增长，发送新增内容
                                await self._send_global_incremental_log_content(websocket, task_dir.name, log_file, monitored_files[file_path])
                                monitored_files[file_path] = current_size
                        except Exception as file_error:
                            logging.debug(f"处理日志文件异常: {log_file}, error={file_error}")
                
                await asyncio.sleep(0.5)  # 检查间隔
                
            except websockets.exceptions.ConnectionClosed:
                logging.info("全局日志WebSocket连接已断开，退出监控循环")
                break
            except Exception as e:
                logging.error(f"全局日志监控异常: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_global_status_changes(self, websocket: WebSocketServerProtocol):
        """监控全局状态文件变化"""
        monitored_files = {}  # file_path -> last_mtime
        
        while True:
            try:
                # 扫描所有任务的状态目录
                for task_dir in self.workspace_root.iterdir():
                    if not task_dir.is_dir():
                        continue
                    
                    script_id = task_dir.name
                    status_file = task_dir / "status" / "real_time_status.json"
                    
                    if status_file.exists():
                        try:
                            current_mtime = status_file.stat().st_mtime
                            file_path = str(status_file)
                            
                            # 如果是新文件或文件已更新
                            if file_path not in monitored_files:
                                # 新文件，发送当前状态
                                monitored_files[file_path] = current_mtime
                                status_data = await self.status_service._read_status_file(script_id)
                                if status_data:
                                    await websocket.send(json.dumps({
                                        "type": "new_status",
                                        "script_id": script_id,
                                        "data": status_data,
                                        "timestamp": datetime.now().isoformat()
                                    }))
                            elif current_mtime > monitored_files[file_path]:
                                # 文件已更新，发送新状态
                                monitored_files[file_path] = current_mtime
                                status_data = await self.status_service._read_status_file(script_id)
                                if status_data:
                                    await websocket.send(json.dumps({
                                        "type": "status_update",
                                        "script_id": script_id,
                                        "data": status_data,
                                        "timestamp": datetime.now().isoformat()
                                    }))
                        except Exception as file_error:
                            logging.debug(f"处理状态文件异常: {status_file}, error={file_error}")
                
                await asyncio.sleep(0.5)  # 检查间隔
                
            except websockets.exceptions.ConnectionClosed:
                logging.info("全局状态WebSocket连接已断开，退出监控循环")
                break
            except Exception as e:
                logging.error(f"全局状态监控异常: {e}")
                await asyncio.sleep(1)
    
    async def _send_incremental_log_content(self, websocket: WebSocketServerProtocol, log_file: Path, last_position: int):
        """发送增量日志内容"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(last_position)
                new_content = f.read()
            
            if new_content:
                # 去掉.log后缀
                display_filename = log_file.name[:-4] if log_file.name.endswith('.log') else log_file.name
                await websocket.send(json.dumps({
                    "type": "incremental",
                    "data": {
                        "log_file": display_filename,
                        "content": new_content,
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
        except Exception as e:
            logging.error(f"发送增量日志内容失败: {e}")
            raise  # 重新抛出异常，让上层处理WebSocket断开
    
    async def _send_global_log_update(self, websocket: WebSocketServerProtocol, script_id: str, log_file: Path, update_type: str, lines: int = 50):
        """发送全局日志更新"""
        try:
            log_response = await self.log_service._read_log_content(script_id, log_file.name, lines, True)
            await websocket.send(json.dumps({
                "type": update_type,
                "script_id": script_id,
                "data": log_response.to_dict(),
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logging.error(f"发送全局日志更新失败: {e}")
    
    async def _send_global_incremental_log_content(self, websocket: WebSocketServerProtocol, script_id: str, log_file: Path, last_size: int):
        """发送全局增量日志内容"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(last_size)
                new_content = f.read()
            
            if new_content.strip():
                await websocket.send(json.dumps({
                    "type": "incremental",
                    "script_id": script_id,
                    "log_file": log_file.stem,  # 去掉.log后缀
                    "content": new_content,
                    "timestamp": datetime.now().isoformat()
                }))
        except Exception as e:
            logging.error(f"发送全局增量日志内容失败: {e}")
    
    def _remove_log_connection(self, script_id: str, websocket: WebSocketServerProtocol):
        """移除日志WebSocket连接"""
        if script_id in self.log_connections:
            if websocket in self.log_connections[script_id]:
                self.log_connections[script_id].remove(websocket)
            
            # 如果没有连接了，清理空列表
            if not self.log_connections[script_id]:
                del self.log_connections[script_id]
    
    def _remove_global_log_connection(self, websocket: WebSocketServerProtocol):
        """移除全局日志WebSocket连接"""
        try:
            if websocket in self.global_log_connections:
                self.global_log_connections.remove(websocket)
                logging.info("全局日志WebSocket连接已移除")
        except Exception as e:
            logging.error(f"移除全局日志WebSocket连接失败: {e}")
    
    def _remove_status_connection(self, script_id: str, websocket: WebSocketServerProtocol):
        """移除状态WebSocket连接"""
        if script_id in self.status_connections:
            if websocket in self.status_connections[script_id]:
                self.status_connections[script_id].remove(websocket)
            
            # 如果没有连接了，清理空列表
            if not self.status_connections[script_id]:
                del self.status_connections[script_id]
    
    def _remove_global_status_connection(self, websocket: WebSocketServerProtocol):
        """移除全局状态WebSocket连接"""
        try:
            if websocket in self.global_status_connections:
                self.global_status_connections.remove(websocket)
                logging.info("全局状态WebSocket连接已移除")
        except Exception as e:
            logging.error(f"移除全局状态WebSocket连接失败: {e}")
    
    async def start(self, host: str = "127.0.0.1", port: int = 8090):
        """启动WebSocket服务器"""
        logging.info(f"🌐 启动纯WebSocket服务器: {host}:{port}")
        logging.info(f"📡 WebSocket端点:")
        logging.info(f"   - 全局日志流: ws://{host}:{port}/logs/realtime")
        logging.info(f"   - 任务日志流: ws://{host}:{port}/logs/{{script_id}}/realtime")
        logging.info(f"   - 全局状态流: ws://{host}:{port}/status/realtime")
        logging.info(f"   - 任务状态流: ws://{host}:{port}/status/{{script_id}}/realtime")
        
        async def handle_connection(websocket: WebSocketServerProtocol, path: str):
            """处理WebSocket连接"""
            try:
                # 解析路径
                path_parts = path.strip('/').split('/')
                
                if len(path_parts) >= 2:
                    if path_parts[0] == 'logs':
                        if path_parts[1] == 'realtime':
                            # 全局日志流
                            await self.handle_global_log_connection(websocket)
                        else:
                            # 特定任务的日志流
                            script_id = path_parts[1]
                            await self.handle_log_connection(websocket, script_id)
                    elif path_parts[0] == 'status':
                        if path_parts[1] == 'realtime':
                            # 全局状态流
                            await self.handle_global_status_connection(websocket)
                        else:
                            # 特定任务的状态流
                            script_id = path_parts[1]
                            await self.handle_status_connection(websocket, script_id)
                    else:
                        await websocket.close(code=1008, reason="Invalid path")
                else:
                    await websocket.close(code=1008, reason="Invalid path")
                    
            except Exception as e:
                logging.error(f"处理WebSocket连接异常: {e}")
                try:
                    await websocket.close()
                except:
                    pass
        
        # 启动WebSocket服务器
        server = await websockets.serve(handle_connection, host, port)
        logging.info(f"✅ WebSocket服务器已启动: {host}:{port}")
        
        # 保持服务器运行
        await server.wait_closed()
    
    def run(self, host: str = "127.0.0.1", port: int = 8090):
        """运行WebSocket服务器（同步版本）"""
        asyncio.run(self.start(host, port))


# 创建WebSocket服务器的工厂函数
def create_websocket_server(workspace_root: Path, log_service: LogQueryService, status_service: StatusTrackingService) -> WebSocketServer:
    """创建WebSocket服务器实例"""
    return WebSocketServer(workspace_root, log_service, status_service)
