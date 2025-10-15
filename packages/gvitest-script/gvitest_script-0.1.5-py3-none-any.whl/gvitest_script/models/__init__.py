"""
数据模型定义模块

包含脚本生成器所需的所有数据模型和类型定义
"""

from typing import Dict, Any, Protocol, runtime_checkable


@runtime_checkable
class Serializable(Protocol):
    """统一序列化协议
    
    所有需要序列化的数据模型都应该实现这个协议，
    确保有统一的to_dict()方法用于字典转换
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        ...


def ensure_serializable(obj: Any) -> Serializable:
    """确保对象实现了Serializable协议
    
    Args:
        obj: 需要检查的对象
        
    Returns:
        Serializable: 确认实现了协议的对象
        
    Raises:
        TypeError: 如果对象未实现Serializable协议
    """
    if not isinstance(obj, Serializable):
        raise TypeError(f"对象 {type(obj).__name__} 未实现 Serializable 协议，缺少 to_dict() 方法")
    return obj


def safe_to_dict(obj: Any) -> Dict[str, Any]:
    """安全地将对象转换为字典
    
    Args:
        obj: 需要转换的对象
        
    Returns:
        Dict[str, Any]: 字典格式的数据
        
    Raises:
        TypeError: 如果对象无法序列化
    """
    if obj is None:
        return {}
    
    serializable_obj = ensure_serializable(obj)
    return serializable_obj.to_dict()

from .validation_model import (
    ValidationModel, ValidationModelConfig,
    ValidationMode, DataSource, ValidationType,
    ExpectedResultResponse, ExpectedResultGroup, ValidationResult
)
from .control_flow_models import (
    ForConfig, WhileConfig, Branch, ControlFlowConfig,
    ConditionExpression
)
from .script_context import (
    ScriptContext, ActionStep, ExecutionConfig,
    StepType, OperationType, ControlType, ElementInfo
)
from .config_models import (
    DeviceConfig, ValidationConfig, ControlFlowExecutionConfig,
    DEFAULT_VALIDATION_CONFIG, DEFAULT_CONTROL_FLOW_EXECUTION_CONFIG
)
from .image_processing_config import ImageProcessingConfig
from .real_time_tracking_config import RealTimeTrackingConfig  
from .logging_config import LoggingConfig

from .checkpoint import (
    CheckpointInfo,
    ExpectedCheckpoint,
    CheckpointValidationConfig,
    CheckpointType,
    CheckpointStatus,
    DEFAULT_CHECKPOINT_CONFIG
)

__all__ = [
    # 序列化协议和工具
    "Serializable",
    "ensure_serializable", 
    "safe_to_dict",
    # 验证模型和枚举
    "ValidationModel",
    "ValidationModelConfig", 
    "ValidationMode",
    "DataSource",
    "ValidationType",
    "ExpectedResultResponse",
    "ExpectedResultGroup",
    "ValidationResult", 
    # 上下文模型和枚举
    "ScriptContext",
    "ActionStep",
    "StepType",
    "OperationType", 
    "ControlType",
    "ElementInfo",
    # 配置模型
    "DeviceConfig",
    "ExecutionConfig",
    "ImageProcessingConfig",
    "RealTimeTrackingConfig",
    "LoggingConfig",
    "ValidationConfig",
    "ControlFlowExecutionConfig",
    "DEFAULT_VALIDATION_CONFIG",
    "DEFAULT_CONTROL_FLOW_EXECUTION_CONFIG",
                    # 控制流模型
                "ForConfig",
                "WhileConfig",
                "Branch",
                "ConditionExpression",
    # 检查点模型
    "CheckpointInfo",
    "ExpectedCheckpoint",
    "CheckpointValidationConfig",
    "CheckpointType",
    "CheckpointStatus",
    "DEFAULT_CHECKPOINT_CONFIG"
] 