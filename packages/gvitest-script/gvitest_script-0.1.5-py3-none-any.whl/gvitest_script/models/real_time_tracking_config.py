from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path


class TrackingMode(str, Enum):
    """状态追踪模式"""
    FILE = "file"           # 文件模式 - 写入状态文件
    HTTP = "http"           # HTTP模式 - 发送到API
    WEBSOCKET = "websocket" # WebSocket模式 - 实时推送
    HYBRID = "hybrid"       # 混合模式 - 同时使用多种方式


class TrackingLevel(str, Enum):
    """追踪详细程度"""
    MINIMAL = "minimal"     # 最小 - 只追踪基本进度
    NORMAL = "normal"       # 正常 - 追踪步骤状态和进度
    DETAILED = "detailed"   # 详细 - 追踪所有操作和中间结果
    DEBUG = "debug"         # 调试 - 追踪所有细节包括调试信息


class StatusUpdateFrequency(str, Enum):
    """状态更新频率"""
    REALTIME = "realtime"   # 实时 - 每个操作都更新
    STEP = "step"           # 步骤 - 每个步骤完成时更新
    MILESTONE = "milestone" # 里程碑 - 重要节点更新
    CUSTOM = "custom"       # 自定义 - 根据配置更新


class RealTimeTrackingConfig(BaseModel):
    """实时状态追踪配置"""
    
    # 基础配置
    enabled: bool = Field(default=True, description="是否启用实时状态追踪")
    mode: TrackingMode = Field(default=TrackingMode.FILE, description="追踪模式")
    level: TrackingLevel = Field(default=TrackingLevel.NORMAL, description="追踪详细程度")
    update_frequency: StatusUpdateFrequency = Field(default=StatusUpdateFrequency.STEP, description="状态更新频率")
    
    # 文件模式配置
    status_file_path: Optional[str] = Field(default=None, description="状态文件路径，为None时自动生成")
    status_file_format: str = Field(default="json", description="状态文件格式 (json/yaml)")
    file_update_interval: float = Field(default=0.5, description="文件更新间隔（秒）")
    keep_history: bool = Field(default=True, description="是否保留历史状态")
    max_history_entries: int = Field(default=100, description="最大历史记录数")
    
    # HTTP API 配置
    api_endpoint: Optional[str] = Field(default=None, description="HTTP API端点URL")
    api_method: str = Field(default="POST", description="HTTP请求方法")
    api_headers: Dict[str, str] = Field(default_factory=dict, description="HTTP请求头")
    api_timeout: float = Field(default=5.0, description="API请求超时时间（秒）")
    api_retry_count: int = Field(default=3, description="API请求重试次数")
    api_retry_delay: float = Field(default=1.0, description="API请求重试延迟（秒）")
    
    # WebSocket 配置
    websocket_url: Optional[str] = Field(default=None, description="WebSocket服务器URL")
    websocket_reconnect: bool = Field(default=True, description="是否自动重连")
    websocket_max_reconnect: int = Field(default=5, description="最大重连次数")
    websocket_ping_interval: float = Field(default=30.0, description="心跳间隔（秒）")
    
    # 追踪内容配置
    track_progress: bool = Field(default=True, description="追踪执行进度")
    track_screenshots: bool = Field(default=True, description="追踪截图状态")
    track_errors: bool = Field(default=True, description="追踪错误信息")
    track_performance: bool = Field(default=False, description="追踪性能指标")
    track_device_info: bool = Field(default=False, description="追踪设备信息")
    track_memory_usage: bool = Field(default=False, description="追踪内存使用")
    
    # 进度计算配置
    enable_eta: bool = Field(default=True, description="是否计算预估完成时间")
    eta_algorithm: str = Field(default="linear", description="ETA计算算法 (linear/exponential/adaptive)")
    progress_smoothing: float = Field(default=0.8, description="进度平滑系数 (0-1)")
    
    # 数据压缩和优化
    compress_data: bool = Field(default=False, description="是否压缩状态数据")
    max_data_size: int = Field(default=1024*1024, description="最大数据大小（字节）")
    truncate_long_strings: bool = Field(default=True, description="是否截断长字符串")
    max_string_length: int = Field(default=500, description="最大字符串长度")
    
    # 安全配置
    include_sensitive_data: bool = Field(default=False, description="是否包含敏感数据")
    sensitive_fields: List[str] = Field(default_factory=lambda: ["password", "token", "key"], description="敏感字段列表")
    
    def get_status_file_path(self, task_id: str, workspace_root: Path) -> Path:
        """获取状态文件路径"""
        if self.status_file_path:
            return Path(self.status_file_path)
        
        # 自动生成状态文件路径
        status_dir = workspace_root / task_id / "status"
        status_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = "json" if self.status_file_format == "json" else "yaml"
        return status_dir / f"real_time_status.{file_extension}"
    
    def should_update_now(self, update_type: str) -> bool:
        """判断是否应该现在更新状态"""
        if not self.enabled:
            return False
        
        if self.update_frequency == StatusUpdateFrequency.REALTIME:
            return True
        elif self.update_frequency == StatusUpdateFrequency.STEP:
            return update_type in ["step_start", "step_complete", "step_error"]
        elif self.update_frequency == StatusUpdateFrequency.MILESTONE:
            return update_type in ["task_start", "task_complete", "task_error", "checkpoint_reached"]
        else:  # CUSTOM
            # 自定义逻辑可以在这里扩展
            return update_type in ["step_complete", "task_complete", "task_error"]
    
    def get_tracking_fields(self) -> List[str]:
        """获取需要追踪的字段列表"""
        fields = ["timestamp", "script_id", "status"]
        
        if self.track_progress:
            fields.extend(["progress_percent", "current_step", "total_steps"])
        
        if self.track_screenshots:
            fields.extend(["screenshot_url", "screenshot_path"])
        
        if self.track_errors:
            fields.extend(["error_message", "error_details"])
        
        if self.track_performance:
            fields.extend(["execution_time", "step_duration"])
        
        if self.track_device_info:
            fields.extend(["device_id", "device_info"])
        
        if self.track_memory_usage:
            fields.extend(["memory_usage", "cpu_usage"])
        
        if self.enable_eta:
            fields.extend(["eta_seconds", "estimated_completion"])
        
        return fields
    
    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理敏感数据"""
        if not self.include_sensitive_data:
            for field in self.sensitive_fields:
                if field in data:
                    data[field] = "***REDACTED***"
        
        # 截断长字符串
        if self.truncate_long_strings:
            for key, value in data.items():
                if isinstance(value, str) and len(value) > self.max_string_length:
                    data[key] = value[:self.max_string_length] + "..."
        
        return data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，保持与其他模型的一致性"""
        return self.model_dump()


# 默认配置实例
DEFAULT_TRACKING_CONFIG = RealTimeTrackingConfig(
    enabled=True,
    mode=TrackingMode.FILE,
    level=TrackingLevel.NORMAL,
    update_frequency=StatusUpdateFrequency.STEP,
    track_progress=True,
    track_screenshots=True,
    track_errors=True,
    enable_eta=True
)

# 调试模式配置
DEBUG_TRACKING_CONFIG = RealTimeTrackingConfig(
    enabled=True,
    mode=TrackingMode.HYBRID,
    level=TrackingLevel.DEBUG,
    update_frequency=StatusUpdateFrequency.REALTIME,
    track_progress=True,
    track_screenshots=True,
    track_errors=True,
    track_performance=True,
    track_device_info=True,
    track_memory_usage=True,
    enable_eta=True,
    keep_history=True,
    max_history_entries=200
)

# 生产环境配置
PRODUCTION_TRACKING_CONFIG = RealTimeTrackingConfig(
    enabled=True,
    mode=TrackingMode.HTTP,
    level=TrackingLevel.NORMAL,
    update_frequency=StatusUpdateFrequency.MILESTONE,
    track_progress=True,
    track_screenshots=False,  # 生产环境可能不需要截图
    track_errors=True,
    track_performance=False,
    enable_eta=True,
    compress_data=True,
    include_sensitive_data=False
) 