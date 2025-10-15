"""
脚本上下文数据模型
用于模板渲染时的数据传递和管理
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from enum import Enum

from .validation_model import ValidationModel
from .logging_config import LoggingConfig
from .image_processing_config import ImageProcessingConfig
from .real_time_tracking_config import RealTimeTrackingConfig
from .control_flow_models import ControlFlowConfig
from .can_models import CanConfigs


class StepType(Enum):
    """步骤类型"""
    ACTION = "action"
    CONTROL_FLOW = "control_flow"


class OperationType(Enum):
    """操作类型"""
    # 基础操作
    CLICK = "click"
    LONG_CLICK = "long_click"
    SWIPE = "swipe"
    TYPE = "type"
    INPUT = "input"
    DRAG = "drag"
    KEY = "key"
    START_APP = "start_app"
    STOP_APP = "stop_app"
    KILL_ALL = "kill_all"
    WAIT = "wait"
    
    # 黑化卡闪检测操作
    BLACK_OPEN = "black_open"
    BLACK_CLOSE = "black_close"
    FLOWER_OPEN = "flower_open"
    FLOWER_CLOSE = "flower_close"
    LAG_OPEN = "lag_open"
    LAG_CLOSE = "lag_close"
    FLASH_OPEN = "flash_open"
    FLASH_CLOSE = "flash_close"
    
    # CAN 操作
    CAN_SEND = "can_send"


class ControlType(Enum):
    """控制流类型"""
    IF_ELSEIF_ELSE = "if_elseif_else"
    FOR = "for"
    WHILE = "while"


@dataclass
class ElementInfo:
    """元素信息 - 包含UI元素的位置、属性和相关图像数据"""
    # 坐标位置信息
    start_x: Optional[float] = None  # 元素左上角X坐标（像素）
    start_y: Optional[float] = None  # 元素左上角Y坐标（像素）
    end_x: Optional[float] = None    # 元素右下角X坐标（像素，用于拖拽操作）
    end_y: Optional[float] = None    # 元素右下角Y坐标（像素，用于拖拽操作）
    width: Optional[float] = None    # 元素宽度（像素）
    height: Optional[float] = None   # 元素高度（像素）
    
    # 文本和属性信息
    text: Optional[str] = None          # 元素显示文本内容
    content_desc: Optional[str] = None  # 元素无障碍描述
    direction: Optional[str] = None     # 滑动方向（up/down/left/right）
    key: Optional[str] = None           # 按键代码（用于按键操作）
    
    # 应用相关信息
    app_package: Optional[str] = None   # 应用包名

    # 等待时间
    wait_time: Optional[int] = None      # 等待时间（毫秒）
    
    # 🎯 图像数据 - 目标图标相关（用于图像匹配定位）
    icon_path: Optional[str] = None    # 目标图标/元素图片的文件路径（用于前端显示和图像定位）
    
    # 📐 边界框信息
    bbox: Optional[List[float]] = None     # 边界框坐标 [x_min, y_min, x_max, y_max]（用于精确定位）
     
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "start_x": self.start_x,
            "start_y": self.start_y,
            "end_x": self.end_x,
            "end_y": self.end_y,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "content_desc": self.content_desc,
            "direction": self.direction,
            "key": self.key,
            "app_package": self.app_package,
            "wait_time": self.wait_time,
            "icon_path": self.icon_path,
            "bbox": self.bbox,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElementInfo':
        """从字典创建ElementInfo实例"""
        return cls(**data)


# 从独立的checkpoint模型文件导入CheckpointInfo
from .checkpoint import CheckpointInfo, ExpectedCheckpoint, DEFAULT_CHECKPOINT_CONFIG


@dataclass
class ActionStep:
    """动作步骤 - 单个操作步骤的完整信息（平铺动作序列版本）"""
    # 必需字段
    id: str
    step_name: str
    step_type: str  # "action" 或 "control_flow"
    mode: str  # 执行模式：agent, manual
    source_task_id: str  # 源任务ID，用于预期结果绑定
    verify_after: bool = False  # 是否在步骤执行后进行验证

    # 可选字段
    step_group_id: Optional[str] = None
    step_number: Optional[Union[int, str]] = None
    screenshot_path: Optional[str] = None
    
    # 条件必需字段（根据step_type）
    operation_type: Optional[str] = None  # step_type="action"时必需
    element_info: Optional[ElementInfo] = None
    checkpoint: Optional[CheckpointInfo] = None
    control_flow_config: Optional[ControlFlowConfig] = None  # step_type="control_flow"时必需
    can_configs: Optional[CanConfigs] = None  # operation_type="can_send"时必需
    
    # 📸 步骤执行截图数据
    screenshot_url: Optional[str] = None    # 步骤执行时的截图URL（内部存储路径）
    
    script: Optional[str] = None
    template_name: Optional[str] = None  # 自定义模板名称
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # 执行状态
    status: str = "pending"  # pending, running, success, failed
    duration: Optional[float] = None
    error_message: Optional[str] = None
    
    # 🔄 重试和截图配置
    requires_screenshot: bool = True     # 是否需要在执行前后截图（用于验证和调试）
    requires_ui_stability: bool = True   # 是否需要等待UI稳定后再执行
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """初始化后处理"""
        # 数据验证
        if self.step_type == "action":
            if not self.operation_type:
                raise ValueError("action类型必须提供operation_type")
        elif self.step_type == "control_flow":
            if not self.control_flow_config:
                raise ValueError("control_flow类型必须提供control_flow_config")
        
        # 初始化默认值
        if self.element_info is None:
            self.element_info = ElementInfo()
        if self.checkpoint is None:
            self.checkpoint = CheckpointInfo()
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "id": self.id,
            "step_name": self.step_name,
            "step_type": self.step_type,
            "mode": self.mode,
            "verify_after": self.verify_after
        }
        
        # 添加可选字段
        if self.step_group_id:
            result["step_group_id"] = self.step_group_id
        if self.step_number:
            result["step_number"] = self.step_number
        if self.screenshot_path:
            result["screenshot_path"] = self.screenshot_path
        if self.source_task_id:
            result["source_task_id"] = self.source_task_id
        
        # 添加条件字段
        if self.operation_type:
            result["operation_type"] = self.operation_type
        if self.element_info:
            result["element_info"] = self.element_info.to_dict()
        if self.checkpoint:
            result["checkpoint"] = self.checkpoint.to_dict()
        if self.control_flow_config:
            result["control_flow_config"] = self.control_flow_config.to_dict()
        if self.can_configs:
            result["can_configs"] = self.can_configs.to_dict()
        
        # 添加其他字段
        if self.screenshot_url:
            result["screenshot_url"] = self.screenshot_url
        if self.script:
            result["script"] = self.script
        if self.template_name:
            result["template_name"] = self.template_name
        if self.created_at:
            result["created_at"] = self.created_at
        if self.updated_at:
            result["updated_at"] = self.updated_at
        if self.status:
            result["status"] = self.status
        if self.duration:
            result["duration"] = self.duration
        if self.error_message:
            result["error_message"] = self.error_message
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionStep':
        """从字典创建ActionStep实例"""
        # 处理条件字段
        element_info = None
        if "element_info" in data and data["element_info"]:
            element_info = ElementInfo.from_dict(data["element_info"])
        
        checkpoint = None
        if "checkpoint" in data and data["checkpoint"]:
            checkpoint = CheckpointInfo(**data["checkpoint"])
        
        control_flow_config = None
        if "control_flow_config" in data and data["control_flow_config"]:
            control_flow_config = ControlFlowConfig.from_dict(data["control_flow_config"])
        
        can_configs = None
        if "can_configs" in data and data["can_configs"]:
            can_configs = CanConfigs.from_dict(data["can_configs"])
        
        return cls(
            id=data["id"],
            step_name=data["step_name"],
            step_type=data["step_type"],
            mode=data["mode"],
            step_group_id=data.get("step_group_id"),
            step_number=data.get("step_number"),
            screenshot_path=data.get("screenshot_path"),
            source_task_id=data.get("source_task_id"),
            verify_after=data.get("verify_after", False),
            operation_type=data.get("operation_type"),
            element_info=element_info,
            checkpoint=checkpoint,
            control_flow_config=control_flow_config,
            can_configs=can_configs,
            screenshot_url=data.get("screenshot_url"),
            script=data.get("script"),
            template_name=data.get("template_name"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            status=data.get("status", "pending"),
            duration=data.get("duration"),
            error_message=data.get("error_message")
        )


@dataclass
class DeviceConfig:
    """设备配置"""
    device_id: Optional[str] = None
    platform: str = "android"
    connect_timeout: int = 30
    command_timeout: int = 15
    retry_count: int = 3
    ui_stability_timeout: float = 5.0
    ui_stability_check_interval: float = 0.5
    ui_stability_max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "device_id": self.device_id,
            "platform": self.platform,
            "connect_timeout": self.connect_timeout,
            "command_timeout": self.command_timeout,
            "retry_count": self.retry_count,
            "ui_stability_timeout": self.ui_stability_timeout,
            "ui_stability_check_interval": self.ui_stability_check_interval,
            "ui_stability_max_retries": self.ui_stability_max_retries
        }


@dataclass
class ExecutionConfig:
    """执行配置 - 脚本执行时的各项配置参数"""
    workspace_root: str
    runner_dir: Optional[str] = None
    
    # 📸 截图配置
    screenshot_format: str = "png"           # 截图文件格式（png/jpg/webp）
    screenshot_quality: int = 85             # 截图质量（1-100，仅对jpg格式有效）
    enable_step_screenshots: bool = True     # 是否为每个步骤自动截图（用于调试和验证）
    
    # ⚡ 性能和执行配置
    enable_performance_monitoring: bool = False
    step_delay: float = 0.5
    error_continue: bool = False
    max_execution_time: int = 3600  # 1小时
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "workspace_root": self.workspace_root,
            "runner_dir": self.runner_dir,
            "screenshot_format": self.screenshot_format,
            "screenshot_quality": self.screenshot_quality,
            "enable_step_screenshots": self.enable_step_screenshots,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "step_delay": self.step_delay,
            "error_continue": self.error_continue,
            "max_execution_time": self.max_execution_time
        }


@dataclass
class ScriptContext:
    """脚本生成上下文"""
    script_id: str
    description: str = ""
    
    # 核心数据
    action_sequence: List[ActionStep] = field(default_factory=list)
    expected_results: Dict[str, List[ValidationModel]] = field(default_factory=dict)  # 按source_task_id分组
    
    # 配置对象
    device_config: Optional[DeviceConfig] = None
    execution_config: Optional[ExecutionConfig] = None
    logging_config: Optional[LoggingConfig] = None
    image_processing_config: Optional[ImageProcessingConfig] = None
    real_time_tracking_config: Optional[RealTimeTrackingConfig] = None
    
    # 模板相关
    template_vars: Dict[str, Any] = field(default_factory=dict)
    main_template: str = "main/script_main.j2"
    
    # 兼容性
    legacy_compatibility: bool = True
    
    # 元数据
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: str = "2.0"
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
            
        # 初始化默认配置
        if self.device_config is None:
            self.device_config = DeviceConfig()
        if self.execution_config is None:
            self.execution_config = ExecutionConfig(
                workspace_root=str(Path.home() / ".gvitest" / "workspace")
            )
        if self.logging_config is None:
            from .logging_config import DEFAULT_LOGGING_CONFIG
            self.logging_config = DEFAULT_LOGGING_CONFIG
        if self.image_processing_config is None:
            from .image_processing_config import DEFAULT_IMAGE_CONFIG
            self.image_processing_config = DEFAULT_IMAGE_CONFIG
        if self.real_time_tracking_config is None:
            from .real_time_tracking_config import DEFAULT_TRACKING_CONFIG
            self.real_time_tracking_config = DEFAULT_TRACKING_CONFIG
    
    # from_legacy_data 方法已删除，因为不再需要处理旧格式数据
    # 新版API直接通过构造函数创建ScriptContext对象
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "script_id": self.script_id,
            "description": self.description,
            "action_sequence": [step.to_dict() for step in self.action_sequence],
            "expected_results": {
                task_id: [vm.to_dict() for vm in validation_models]
                for task_id, validation_models in self.expected_results.items()
            },
            "device_config": self.device_config.to_dict() if self.device_config else {},
            "execution_config": self.execution_config.to_dict() if self.execution_config else {},
            "logging_config": self.logging_config.to_dict() if self.logging_config else {},
            "image_processing_config": self.image_processing_config.to_dict() if self.image_processing_config else {},
            "real_time_tracking_config": self.real_time_tracking_config.to_dict() if self.real_time_tracking_config else {},
            "template_vars": self.template_vars,
            "main_template": self.main_template,
            "legacy_compatibility": self.legacy_compatibility,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version
        }
    
    def get_workspace_root(self) -> Path:
        """获取工作空间根目录"""
        return Path(self.execution_config.workspace_root)
    
    def get_task_workspace(self) -> Path:
        """获取任务工作空间目录"""
        return self.get_workspace_root() / self.script_id
    
    def get_runner_dir(self) -> Path:
        """获取运行器目录"""
        if self.execution_config.runner_dir:
            return Path(self.execution_config.runner_dir)
        return self.get_task_workspace() / "runner"
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now().isoformat()
    
    def add_action_step(self, step: ActionStep):
        """添加动作步骤"""
        self.action_sequence.append(step)
        self.update_timestamp()
    
    def add_expected_result(self, task_id: str, result: ValidationModel):
        """添加预期结果到指定任务"""
        if task_id not in self.expected_results:
            self.expected_results[task_id] = []
        self.expected_results[task_id].append(result)
        self.update_timestamp()
    
    def get_step_by_id(self, step_id: str) -> Optional[ActionStep]:
        """根据ID获取步骤"""
        for step in self.action_sequence:
            if step.id == step_id:
                return step
        return None
    
    def get_result_by_id(self, result_id: str) -> Optional[ValidationModel]:
        """根据ID获取预期结果"""
        for task_id, validation_models in self.expected_results.items():
            for result in validation_models:
                if result.id == result_id:
                    return result
        return None
    
    def get_results_by_task_id(self, task_id: str) -> List[ValidationModel]:
        """根据任务ID获取预期结果列表"""
        return self.expected_results.get(task_id, []) 