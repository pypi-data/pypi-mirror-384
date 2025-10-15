"""
CAN 相关数据模型定义

包含 CAN 发送配置、信号采集配置、验证条件等核心数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List,Union
import re
import os


@dataclass
class CanValueRule:
    """CAN 信号值规则"""
    relation: str  # 比较关系: >, <, =, >=, <=, !=
    value: int     # 目标整数值
    
    def __post_init__(self):
        """验证关系操作符"""
        if self.relation not in ['>', '<', '=', '>=', '<=', '!=']:
            raise ValueError(f"Invalid relation: {self.relation}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation": self.relation,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanValueRule':
        """从字典创建 CanValueRule 实例"""
        return cls(
            relation=data["relation"],
            value=data["value"]
        )


@dataclass 
class CanConfigs:
    """CAN 发送配置"""
    channel_id: str  # CAN 通道 ID
    frame_id: int    # 帧 ID（整数）
    signals: Dict[str, Any]  # 信号字典，形如 {"HU_MediaVolSET": 0}
    duration: int  # 信号发送持续时间（毫秒）
    interval: int  # 信号发送间隔时间（毫秒）
    ip: str = "127.0.0.1"  # CAN Server 地址
    
    def __post_init__(self):
        """验证 CAN 配置参数"""
        # 验证必需字段
        if not self.channel_id:
            raise ValueError("channel_id is required")
        if not self.frame_id:
            raise ValueError("frame_id is required")
        if not self.signals:
            raise ValueError("signals list cannot be empty")
        if self.duration <= 0:
            raise ValueError("duration must be positive")
        if self.interval <= 0:
            raise ValueError("interval must be positive")
            
        # 验证 signals 为字典格式
        if not isinstance(self.signals, dict):
            raise ValueError(f"signals must be a dictionary, got {type(self.signals)}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "frame_id": self.frame_id,
            "signals": self.signals,
            "duration": self.duration,
            "interval": self.interval,
            "ip": self.ip
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanConfigs':
        """从字典创建 CanConfigs 实例"""
        return cls(
            channel_id=data["channel_id"],
            frame_id=int(data["frame_id"]),  # 确保转换为整数
            signals=data["signals"],
            duration=data["duration"],
            interval=data["interval"],
            ip=data.get("ip", "127.0.0.1")
        )


@dataclass
class CanCapture:
    """CAN 采集配置"""
    channel_list: List[str]  # 要订阅的 CAN 通道列表
    ip: str = "127.0.0.1"    # MQTT/采集服务地址
    
    def __post_init__(self):
        """验证 CAN 采集配置"""
        if not self.channel_list:
            raise ValueError("channel_list cannot be empty")
        
        # 验证通道列表中的每个通道ID
        for channel in self.channel_list:
            if not isinstance(channel, str) or not channel.strip():
                raise ValueError(f"Invalid channel ID: {channel}")
    
    def get_file_path(self, runner_dir: str, task_id: str) -> str:
        """
        自动生成采集文件路径
        
        Args:
            runner_dir: 脚本运行目录 (如: /workspace/{script_id}/runner)
            task_id: 任务ID (如: drive_task, login_task)
        
        Returns:
            str: CAN信号文件路径
        """
        # 在runner_dir下创建can_signals目录
        can_dir = os.path.join(runner_dir, 'can_signals')
        os.makedirs(can_dir, exist_ok=True)
        
        # 使用时间戳生成唯一文件名
        import time
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        return os.path.join(can_dir, f'{task_id}_signals_{timestamp}.txt')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_list": self.channel_list,
            "ip": self.ip
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanCapture':
        """从字典创建 CanCapture 实例"""
        return cls(
            channel_list=data["channel_list"],
            ip=data.get("ip", "127.0.0.1")
        )





@dataclass
class CanTaskResult:
    """CAN 任务执行结果"""
    task_id: str
    capture_file_path: Optional[str] = None
    conditions_results: List[Dict[str, Any]] = field(default_factory=list)
    expression_result: Optional[bool] = None
    expression: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "capture_file_path": self.capture_file_path,
            "conditions_results": self.conditions_results,
            "expression_result": self.expression_result,
            "expression": self.expression,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanTaskResult':
        """从字典创建 CanTaskResult 实例"""
        return cls(
            task_id=data["task_id"],
            capture_file_path=data.get("capture_file_path"),
            conditions_results=data.get("conditions_results", []),
            expression_result=data.get("expression_result"),
            expression=data.get("expression"),
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time")
        )


@dataclass
class CanSendResult:
    """CAN 发送结果"""
    success: bool
    message: str
    channel_id: str
    frame_id: int
    signals: Dict[str, Any]
    execution_time: Optional[float] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "channel_id": self.channel_id,
            "frame_id": self.frame_id,
            "signals": self.signals,
            "execution_time": self.execution_time,
            "error_code": self.error_code
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CanSendResult':
        """从字典创建 CanSendResult 实例"""
        return cls(
            success=data["success"],
            message=data["message"],
            channel_id=data["channel_id"],
            frame_id=data["frame_id"],
            signals=data["signals"],
            execution_time=data.get("execution_time"),
            error_code=data.get("error_code")
        )


# 工具函数
def validate_can_signal_format(signal: str) -> bool:
    """验证 CAN 信号格式是否正确"""
    # 支持格式：NAME=VALUE，其中VALUE可以是：
    # - 十进制数字：123, -456, +789
    # - 十六进制数字：0x123, 0xFF, 0x0
    # - 浮点数：12.34, -56.78
    pattern = re.compile(r'^[A-Za-z0-9_]+=[-+]?(?:0x[0-9A-Fa-f]+|[0-9]+(?:\.[0-9]+)?)$')
    return bool(pattern.match(signal))


def parse_can_signal(signal: str) -> tuple[str, Union[int, float]]:
    """解析 CAN 信号字符串，返回 (name, value)"""
    if not validate_can_signal_format(signal):
        raise ValueError(f"Invalid signal format: {signal}")
    
    name, value_str = signal.split('=', 1)
    
    # 处理十六进制值
    if value_str.startswith('0x') or value_str.startswith('0X'):
        value = int(value_str, 16)
    else:
        # 处理十进制和浮点数
        try:
            if '.' in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
        except ValueError:
            raise ValueError(f"Cannot parse value: {value_str}")
    
    return name, value





# 默认配置
DEFAULT_CAN_CAPTURE_IP = "127.0.0.1"
DEFAULT_CAN_SERVER_IP = "127.0.0.1"
DEFAULT_CAN_WAIT_TIME = 0