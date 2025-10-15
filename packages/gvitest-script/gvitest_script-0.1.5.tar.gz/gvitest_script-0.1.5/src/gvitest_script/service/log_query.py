"""
日志查询服务
支持查询已完成的日志和实时日志查询
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class LogQueryRequest:
    """日志查询请求模型"""
    def __init__(self, script_id: str, lines: Optional[int] = None, from_end: bool = True):
        self.script_id = script_id
        self.lines = lines  # 查询的行数，None表示全部
        self.from_end = from_end  # 是否从末尾开始查询


class LogListResponse:
    """日志列表响应模型"""
    def __init__(self, script_id: str, log_files: List[Dict[str, Any]]):
        self.script_id = script_id
        self.log_files = log_files
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，保持与其他模型的一致性"""
        return {
            "script_id": self.script_id,
            "log_files": self.log_files
        }


class LogContentResponse:
    """日志内容响应模型"""
    def __init__(self, script_id: str, log_file: str, content: str, total_lines: int, queried_lines: int, timestamp: str):
        self.script_id = script_id
        self.log_file = log_file
        self.content = content
        self.total_lines = total_lines
        self.queried_lines = queried_lines
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，保持与其他模型的一致性"""
        return {
            "script_id": self.script_id,
            "log_file": self.log_file,
            "content": self.content,
            "total_lines": self.total_lines,
            "queried_lines": self.queried_lines,
            "timestamp": self.timestamp
        }


class LogQueryService:
    """日志查询服务"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.completed_tasks = set()  # 已完成的任务集合
        self.task_completion_times = {}  # script_id -> completion_time
    
    
    async def get_task_logs(self, script_id: str) -> LogListResponse:
        """获取任务的所有日志文件列表"""
        try:
            log_dir = self.workspace_root / script_id / "logs"
            if not log_dir.exists():
                raise FileNotFoundError(f"任务 {script_id} 的日志目录不存在")
            
            log_files = []
            for log_file in log_dir.glob("*.log"):
                stat = log_file.stat()
                # 去掉.log后缀
                filename_without_ext = log_file.stem
                log_files.append({
                    "filename": filename_without_ext,
                    "size": stat.st_size,
                    "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_current": self._is_current_log(log_file.name)
                })
            
            # 按创建时间排序，最新的在前
            log_files.sort(key=lambda x: x["created_time"], reverse=True)
            
            return LogListResponse(
                script_id=script_id,
                log_files=log_files
            )
        
        except Exception as e:
            logging.error(f"获取任务日志列表失败: {e}")
            raise RuntimeError(f"获取日志列表失败: {str(e)}")
    
    async def get_latest_log(self, script_id: str, lines: Optional[int] = None, from_end: bool = True) -> LogContentResponse:
        """获取任务的最新日志内容"""
        try:
            log_dir = self.workspace_root / script_id / "logs"
            if not log_dir.exists():
                raise FileNotFoundError(f"任务 {script_id} 的日志目录不存在")
            
            # 找到最新的日志文件
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                raise FileNotFoundError(f"任务 {script_id} 没有日志文件")
            
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            
            # 传入完整的文件名（带.log后缀）
            return await self._read_log_content(script_id, latest_log.name, lines, from_end)
        
        except Exception as e:
            logging.error(f"获取最新日志失败: {e}")
            raise RuntimeError(f"获取最新日志失败: {str(e)}")
    
    async def get_specific_log(self, script_id: str, log_filename: str, lines: Optional[int] = None, from_end: bool = True) -> LogContentResponse:
        """获取指定日志文件的内容"""
        try:
            # 如果传入的filename没有.log后缀，自动添加
            if not log_filename.endswith('.log'):
                actual_filename = f"{log_filename}.log"
            else:
                actual_filename = log_filename
            
            return await self._read_log_content(script_id, actual_filename, lines, from_end)
        
        except Exception as e:
            logging.error(f"获取指定日志失败: {e}")
            raise RuntimeError(f"获取日志失败: {str(e)}")
    
    
    async def _read_log_content(self, script_id: str, log_filename: str, lines: Optional[int], from_end: bool) -> LogContentResponse:
        """读取日志文件内容"""
        log_file = self.workspace_root / script_id / "logs" / log_filename
        
        if not log_file.exists():
            raise FileNotFoundError(f"日志文件 {log_filename} 不存在")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            if lines is None:
                # 读取全部内容
                content_lines = all_lines
                queried_lines = total_lines
            else:
                # 读取指定行数
                if from_end:
                    content_lines = all_lines[-lines:] if lines < total_lines else all_lines
                else:
                    content_lines = all_lines[:lines] if lines < total_lines else all_lines
                queried_lines = len(content_lines)
            
            content = ''.join(content_lines)
            
            # 返回时去掉.log后缀
            display_filename = log_filename[:-4] if log_filename.endswith('.log') else log_filename
            
            return LogContentResponse(
                script_id=script_id,
                log_file=display_filename,
                content=content,
                total_lines=total_lines,
                queried_lines=queried_lines,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise RuntimeError(f"读取日志文件失败: {str(e)}")
    
    
    def _is_current_log(self, filename: str) -> bool:
        """判断是否是当前正在写入的日志文件"""
        # 简单判断：最新的日志文件认为是当前文件
        # 实际应用中可以根据业务逻辑调整
        return True
    
    def mark_task_completed(self, script_id: str):
        """记录任务完成时间"""
        self.task_completion_times[script_id] = time.time()
        logging.info(f"任务 {script_id} 已完成")


# 创建日志查询服务的工厂函数
def create_log_query_service(workspace_root: Path) -> LogQueryService:
    """创建日志查询服务实例"""
    return LogQueryService(workspace_root) 