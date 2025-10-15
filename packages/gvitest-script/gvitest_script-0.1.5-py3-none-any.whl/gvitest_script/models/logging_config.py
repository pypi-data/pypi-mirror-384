"""
独立日志文件支持配置模型

实现日志文件命名规则、日志轮转和压缩、loguru日志系统集成等功能。
支持为每个脚本执行创建独立的日志文件，提供完整的执行跟踪。
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from pathlib import Path
import json
from enum import Enum
import re


class LogLevel(str, Enum):
    """日志级别"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """日志格式类型"""
    SIMPLE = "simple"           # 简单格式
    DETAILED = "detailed"       # 详细格式
    JSON = "json"              # JSON格式
    STRUCTURED = "structured"   # 结构化格式
    CUSTOM = "custom"          # 自定义格式


class RotationPolicy(str, Enum):
    """日志轮转策略"""
    SIZE = "size"              # 按文件大小
    TIME = "time"              # 按时间
    DAILY = "daily"            # 每日轮转
    WEEKLY = "weekly"          # 每周轮转
    MONTHLY = "monthly"        # 每月轮转


class CompressionType(str, Enum):
    """压缩类型"""
    NONE = "none"
    GZ = "gz"
    ZIP = "zip"
    TAR_GZ = "tar.gz"


class LogRotationConfig(BaseModel):
    """日志轮转配置"""
    
    # 轮转大小限制（MB）
    max_size_mb: int = Field(default=10, description="单个日志文件最大大小（MB）")
    
    # 保留文件数量
    backup_count: int = Field(default=5, description="保留的备份日志文件数量")
    
    # 轮转时间间隔
    rotation_interval: str = Field(default="daily", description="轮转时间间隔：daily, weekly, monthly")
    
    # 压缩备份文件
    compress_backup: bool = Field(default=True, description="是否压缩备份的日志文件")
    
    # 压缩格式
    compression_format: str = Field(default="gz", description="压缩格式：gz, bz2, xz")
    
    @validator('rotation_interval')
    def validate_rotation_interval(cls, v):
        valid_intervals = ['daily', 'weekly', 'monthly', 'hourly']
        if v not in valid_intervals:
            raise ValueError(f"轮转间隔必须是 {', '.join(valid_intervals)} 中的一个")
        return v
    
    @validator('compression_format')
    def validate_compression_format(cls, v):
        valid_formats = ['gz', 'bz2', 'xz']
        if v not in valid_formats:
            raise ValueError(f"压缩格式必须是 {', '.join(valid_formats)} 中的一个")
        return v


class LogFormatConfig(BaseModel):
    """日志格式配置"""
    
    # 时间格式
    time_format: str = Field(default="%Y-%m-%d %H:%M:%S", description="时间格式字符串")
    
    # 日志级别显示
    show_level: bool = Field(default=True, description="是否显示日志级别")
    
    # 显示源文件信息
    show_source: bool = Field(default=True, description="是否显示源文件和行号")
    
    # 显示进程ID
    show_process_id: bool = Field(default=False, description="是否显示进程ID")
    
    # 显示线程ID
    show_thread_id: bool = Field(default=False, description="是否显示线程ID")
    
    # JSON格式输出
    json_format: bool = Field(default=False, description="是否使用JSON格式输出")
    
    # 自定义字段
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义日志字段")
    
    def get_format_string(self) -> str:
        """获取loguru格式字符串"""
        if self.json_format:
            return self._get_json_format()
        else:
            return self._get_text_format()
    
    def _get_text_format(self) -> str:
        """获取文本格式字符串"""
        parts = []
        
        # 时间
        parts.append(f"{{time:{self.time_format}}}")
        
        # 日志级别
        if self.show_level:
            parts.append("{level}")
        
        # 进程ID
        if self.show_process_id:
            parts.append("{process}")
        
        # 线程ID
        if self.show_thread_id:
            parts.append("{thread}")
        
        # 源文件信息
        if self.show_source:
            parts.append("{name}:{function}:{line}")
        
        # 消息
        parts.append("{message}")
        
        return " | ".join(parts)
    
    def _get_json_format(self) -> str:
        """获取JSON格式字符串"""
        return "{time} | {level} | {name}:{function}:{line} | {message}"


class LoggingConfig(BaseModel):
    """独立日志文件配置"""
    
    # 基础配置
    enabled: bool = Field(default=True, description="是否启用独立日志")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    format_type: LogFormat = Field(default=LogFormat.DETAILED, description="日志格式类型")
    
    # 文件配置
    log_directory: Optional[str] = Field(default=None, description="日志目录，为None时自动生成")
    filename_template: str = Field(default="{task_id}_{timestamp}.log", description="日志文件名模板")
    encoding: str = Field(default="utf-8", description="文件编码")
    
    # 轮转配置
    enable_rotation: bool = Field(default=True, description="是否启用日志轮转")
    rotation_policy: RotationPolicy = Field(default=RotationPolicy.SIZE, description="轮转策略")
    max_file_size: str = Field(default="10 MB", description="最大文件大小")
    rotation_time: str = Field(default="00:00", description="轮转时间 (HH:MM)")
    max_files: int = Field(default=10, description="最大保留文件数")
    
    # 压缩配置
    enable_compression: bool = Field(default=True, description="是否启用压缩")
    compression_type: CompressionType = Field(default=CompressionType.GZ, description="压缩类型")
    compression_delay: int = Field(default=1, description="压缩延迟（天）")
    
    # 格式配置
    custom_format: Optional[str] = Field(default=None, description="自定义日志格式")
    include_timestamp: bool = Field(default=True, description="是否包含时间戳")
    include_level: bool = Field(default=True, description="是否包含日志级别")
    include_function: bool = Field(default=True, description="是否包含函数名")
    include_line: bool = Field(default=True, description="是否包含行号")
    include_thread: bool = Field(default=False, description="是否包含线程信息")
    include_process: bool = Field(default=False, description="是否包含进程信息")
    
    # 性能监控日志
    enable_performance_log: bool = Field(default=False, description="是否启用性能监控日志")
    performance_log_interval: float = Field(default=5.0, description="性能日志记录间隔（秒）")
    track_memory_usage: bool = Field(default=False, description="是否追踪内存使用")
    track_cpu_usage: bool = Field(default=False, description="是否追踪CPU使用")
    track_execution_time: bool = Field(default=True, description="是否追踪执行时间")
    
    # JSON格式配置
    json_ensure_ascii: bool = Field(default=False, description="JSON是否确保ASCII")
    json_indent: Optional[int] = Field(default=None, description="JSON缩进")
    json_sort_keys: bool = Field(default=True, description="JSON是否排序键")
    
    # 过滤配置
    exclude_modules: List[str] = Field(default_factory=list, description="排除的模块")
    include_only_modules: List[str] = Field(default_factory=list, description="仅包含的模块")
    exclude_patterns: List[str] = Field(default_factory=list, description="排除的正则模式")
    
    # 缓冲配置
    enable_buffering: bool = Field(default=False, description="是否启用缓冲")
    buffer_size: int = Field(default=1024, description="缓冲区大小")
    flush_interval: float = Field(default=1.0, description="刷新间隔（秒）")
    
    # 错误处理
    error_handling: str = Field(default="ignore", description="错误处理策略 (ignore/raise/log)")
    backup_on_error: bool = Field(default=True, description="错误时是否备份")
    
    @validator('filename_template')
    def validate_filename_template(cls, v):
        """验证文件名模板"""
        required_vars = ['{task_id}']
        for var in required_vars:
            if var not in v:
                raise ValueError(f"文件名模板必须包含 {var}")
        return v
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        """验证文件大小格式"""
        pattern = r'^\d+\s*(B|KB|MB|GB)$'
        if not re.match(pattern, v, re.IGNORECASE):
            raise ValueError("文件大小格式错误，例如: '10 MB', '1 GB'")
        return v
    
    @validator('rotation_time')
    def validate_rotation_time(cls, v):
        """验证轮转时间格式"""
        pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(pattern, v):
            raise ValueError("轮转时间格式错误，应为 HH:MM 格式")
        return v
    
    def get_log_directory(self, task_id: str, workspace_root: Path) -> Path:
        """获取日志目录路径"""
        if self.log_directory:
            return Path(self.log_directory)
        
        # 自动生成日志目录
        log_dir = workspace_root / task_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def get_log_filename(self, task_id: str, timestamp: datetime = None) -> str:
        """生成日志文件名"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # 替换模板变量
        filename = self.filename_template.format(
            task_id=task_id,
            timestamp=timestamp.strftime("%Y%m%d_%H%M%S"),
            date=timestamp.strftime("%Y%m%d"),
            time=timestamp.strftime("%H%M%S"),
            level=self.log_level.value.lower()
        )
        
        return filename
    
    def get_log_format(self) -> str:
        """获取日志格式字符串"""
        if self.format_type == LogFormat.CUSTOM and self.custom_format:
            return self.custom_format
        
        # 构建格式字符串
        format_parts = []
        
        if self.include_timestamp:
            format_parts.append("{time:YYYY-MM-DD HH:mm:ss.SSS}")
        
        if self.include_level:
            format_parts.append("{level: <8}")
        
        if self.include_process:
            format_parts.append("PID:{process}")
        
        if self.include_thread:
            format_parts.append("TID:{thread}")
        
        if self.include_function and self.include_line:
            format_parts.append("{name}:{function}:{line}")
        elif self.include_function:
            format_parts.append("{name}:{function}")
        else:
            format_parts.append("{name}")
        
        format_parts.append("{message}")
        
        if self.format_type == LogFormat.SIMPLE:
            return "{time:HH:mm:ss} | {level: <4} | {message}"
        elif self.format_type == LogFormat.DETAILED:
            return " | ".join(format_parts)
        elif self.format_type == LogFormat.JSON:
            return self._get_json_format()
        elif self.format_type == LogFormat.STRUCTURED:
            return self._get_structured_format()
        
        return " | ".join(format_parts)
    
    def _get_json_format(self) -> str:
        """获取JSON格式"""
        json_fields = []
        
        if self.include_timestamp:
            json_fields.append('"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}"')
        
        if self.include_level:
            json_fields.append('"level": "{level}"')
        
        if self.include_function:
            json_fields.append('"function": "{function}"')
        
        if self.include_line:
            json_fields.append('"line": {line}')
        
        if self.include_process:
            json_fields.append('"process": {process}')
        
        if self.include_thread:
            json_fields.append('"thread": "{thread}"')
        
        json_fields.extend([
            '"module": "{name}"',
            '"message": "{message}"'
        ])
        
        return "{" + ", ".join(json_fields) + "}"
    
    def _get_structured_format(self) -> str:
        """获取结构化格式"""
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name: <20} | "
            "{function: <15} | "
            "L{line: <4} | "
            "{message}"
        )
    
    def get_rotation_config(self) -> Dict[str, Any]:
        """获取轮转配置"""
        if not self.enable_rotation:
            return {}
        
        config = {}
        
        if self.rotation_policy == RotationPolicy.SIZE:
            config["rotation"] = self.max_file_size
        elif self.rotation_policy == RotationPolicy.TIME:
            config["rotation"] = self.rotation_time
        elif self.rotation_policy == RotationPolicy.DAILY:
            config["rotation"] = "1 day"
        elif self.rotation_policy == RotationPolicy.WEEKLY:
            config["rotation"] = "1 week"
        elif self.rotation_policy == RotationPolicy.MONTHLY:
            config["rotation"] = "1 month"
        
        if self.max_files > 0:
            config["retention"] = self.max_files
        
        if self.enable_compression:
            config["compression"] = self.compression_type.value
        
        return config
    
    def should_log_module(self, module_name: str) -> bool:
        """判断是否应该记录某个模块的日志"""
        # 检查排除列表
        if self.exclude_modules and module_name in self.exclude_modules:
            return False
        
        # 检查包含列表
        if self.include_only_modules and module_name not in self.include_only_modules:
            return False
        
        # 检查排除模式
        for pattern in self.exclude_patterns:
            if re.search(pattern, module_name):
                return False
        
        return True
    
    def get_performance_log_config(self) -> Dict[str, Any]:
        """获取性能监控日志配置"""
        if not self.enable_performance_log:
            return {}
        
        return {
            "interval": self.performance_log_interval,
            "track_memory": self.track_memory_usage,
            "track_cpu": self.track_cpu_usage,
            "track_execution": self.track_execution_time
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，保持与其他模型的一致性"""
        return self.model_dump()


# 预定义配置实例
DEFAULT_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.INFO,
    format_type=LogFormat.DETAILED,
    enable_rotation=True,
    rotation_policy=RotationPolicy.SIZE,
    max_file_size="10 MB",
    max_files=5,
    enable_compression=True,
    compression_type=CompressionType.GZ
)

DEBUG_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.DEBUG,
    format_type=LogFormat.DETAILED,
    include_function=True,
    include_line=True,
    include_thread=True,
    enable_performance_log=True,
    track_memory_usage=True,
    track_cpu_usage=True,
    enable_rotation=True,
    max_file_size="50 MB",
    max_files=10
)

PRODUCTION_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.WARNING,
    format_type=LogFormat.JSON,
    include_function=False,
    include_line=False,
    include_thread=False,
    enable_rotation=True,
    rotation_policy=RotationPolicy.DAILY,
    max_files=30,
    enable_compression=True,
    compression_type=CompressionType.GZ,
    enable_buffering=True,
    buffer_size=2048
)

MINIMAL_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.ERROR,
    format_type=LogFormat.SIMPLE,
    include_function=False,
    include_line=False,
    enable_rotation=False,
    enable_compression=False,
    enable_performance_log=False
)

# CAN 专用日志配置
CAN_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.INFO,
    format_type=LogFormat.STRUCTURED,
    filename_template="can_{task_id}_{timestamp}.log",
    include_timestamp=True,
    include_level=True,
    include_function=True,
    include_line=True,
    include_thread=True,  # CAN操作涉及多线程
    include_process=False,
    enable_rotation=True,
    rotation_policy=RotationPolicy.SIZE,
    max_file_size="20 MB",  # CAN日志可能较大
    max_files=15,  # 保留更多历史文件
    enable_compression=True,
    compression_type=CompressionType.GZ,
    # CAN相关模块过滤
    include_only_modules=[
        "can_utils", "can_handler", "can_models", 
        "utilities", "expression_utils"
    ],
    # 性能监控（CAN操作对性能敏感）
    enable_performance_log=True,
    performance_log_interval=3.0,
    track_memory_usage=True,
    track_cpu_usage=False,  # CPU监控可能影响CAN实时性
    track_execution_time=True
)

CAN_DEBUG_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.DEBUG,
    format_type=LogFormat.DETAILED,
    filename_template="can_debug_{task_id}_{timestamp}.log",
    include_timestamp=True,
    include_level=True,
    include_function=True,
    include_line=True,
    include_thread=True,
    include_process=True,
    enable_rotation=True,
    rotation_policy=RotationPolicy.SIZE,
    max_file_size="50 MB",  # 调试日志更大
    max_files=20,
    enable_compression=True,
    compression_type=CompressionType.GZ,
    # 详细的性能监控
    enable_performance_log=True,
    performance_log_interval=1.0,  # 更频繁的性能记录
    track_memory_usage=True,
    track_cpu_usage=True,
    track_execution_time=True,
    # 启用缓冲以提高性能
    enable_buffering=True,
    buffer_size=4096,
    flush_interval=0.5
)

CAN_PRODUCTION_LOGGING_CONFIG = LoggingConfig(
    enabled=True,
    log_level=LogLevel.WARNING,  # 生产环境只记录警告以上
    format_type=LogFormat.JSON,  # JSON格式便于日志分析
    filename_template="can_prod_{task_id}_{date}.log",
    include_timestamp=True,
    include_level=True,
    include_function=False,  # 生产环境不需要函数信息
    include_line=False,
    include_thread=True,  # 保留线程信息用于问题排查
    include_process=False,
    enable_rotation=True,
    rotation_policy=RotationPolicy.DAILY,  # 按日轮转
    max_files=90,  # 保留3个月
    enable_compression=True,
    compression_type=CompressionType.GZ,
    compression_delay=1,  # 1天后压缩
    # 排除调试信息
    exclude_patterns=[r".*debug.*", r".*trace.*"],
    # 高效的缓冲配置
    enable_buffering=True,
    buffer_size=8192,
    flush_interval=2.0,
    # 性能监控（简化）
    enable_performance_log=False,  # 生产环境关闭详细性能监控
    error_handling="log"  # 错误时记录而不是抛出
)


def get_can_logging_config(environment: str = "development") -> LoggingConfig:
    """
    根据环境获取CAN专用日志配置
    
    Args:
        environment: 环境类型 (development/debug/production)
    
    Returns:
        LoggingConfig: CAN日志配置
    """
    config_map = {
        "development": CAN_LOGGING_CONFIG,
        "debug": CAN_DEBUG_LOGGING_CONFIG,
        "production": CAN_PRODUCTION_LOGGING_CONFIG,
        "test": MINIMAL_LOGGING_CONFIG
    }
    
    return config_map.get(environment, CAN_LOGGING_CONFIG)


def create_can_logger_config(
    task_id: str,
    log_level: LogLevel = LogLevel.INFO,
    enable_debug: bool = False,
    enable_performance: bool = True
) -> Dict[str, Any]:
    """
    创建CAN专用的loguru配置
    
    Args:
        task_id: 任务ID
        log_level: 日志级别
        enable_debug: 是否启用调试模式
        enable_performance: 是否启用性能监控
    
    Returns:
        Dict: loguru配置字典
    """
    base_config = CAN_DEBUG_LOGGING_CONFIG if enable_debug else CAN_LOGGING_CONFIG
    
    # 自定义配置
    custom_config = LoggingConfig(
        enabled=True,
        log_level=log_level,
        format_type=LogFormat.STRUCTURED if not enable_debug else LogFormat.DETAILED,
        filename_template=f"can_{task_id}_{{timestamp}}.log",
        include_thread=True,  # CAN操作需要线程信息
        enable_performance_log=enable_performance,
        enable_rotation=True,
        max_file_size="30 MB" if enable_debug else "15 MB",
        max_files=25 if enable_debug else 10,
        enable_compression=True
    )
    
    return {
        "handlers": [
            {
                "sink": custom_config.get_log_filename(task_id),
                "format": custom_config.get_log_format(),
                "level": custom_config.log_level.value,
                "rotation": custom_config.max_file_size,
                "retention": custom_config.max_files,
                "compression": "gz" if custom_config.enable_compression else None,
                "enqueue": True,  # 异步日志
                "catch": True,    # 捕获异常
                "backtrace": enable_debug,  # 调试模式下启用回溯
                "diagnose": enable_debug    # 调试模式下启用诊断
            }
        ]
    }


# 默认日志配置
DEFAULT_LOGGING_CONFIG = LoggingConfig(
    log_directory="script_server/logs",
    log_filename_pattern="script_{script_id}_{timestamp}.log",
    log_level="INFO",
    format_config=LogFormatConfig(
        time_format="%Y-%m-%d %H:%M:%S",
        show_level=True,
        show_source=True,
        json_format=False
    ),
    rotation_config=LogRotationConfig(
        max_size_mb=10,
        backup_count=5,
        rotation_interval="daily",
        compress_backup=True
    ),
    enable_console=True,
    console_log_level="INFO",
    enable_performance_logging=True,
    enable_error_file=True,
    async_logging=True
) 