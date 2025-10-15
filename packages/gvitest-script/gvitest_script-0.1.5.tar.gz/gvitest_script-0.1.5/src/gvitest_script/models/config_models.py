"""
配置模型定义

包含图像处理、实时状态追踪、日志记录、控制流、验证等核心功能的配置类
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class ImageProcessingConfig:
    """图像处理统一配置"""
    # URL处理配置
    base_url: str = "http://localhost:8080"
    static_path: str = "/static"
    upload_path: str = "/uploads"
    
    # Base64转换配置
    enable_base64_output: bool = True
    base64_prefix: str = "data:image/png;base64,"
    max_base64_size: int = 10 * 1024 * 1024  # 10MB
    
    # 图像缓存配置
    enable_image_cache: bool = True
    cache_duration: int = 3600  # 1小时
    cache_max_size: int = 100  # 最多缓存100张图片
    
    # 图像处理配置
    auto_resize: bool = True
    max_width: int = 1920
    max_height: int = 1080
    quality: int = 85  # JPEG质量
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "static_path": self.static_path,
            "upload_path": self.upload_path,
            "enable_base64_output": self.enable_base64_output,
            "base64_prefix": self.base64_prefix,
            "max_base64_size": self.max_base64_size,
            "enable_image_cache": self.enable_image_cache,
            "cache_duration": self.cache_duration,
            "cache_max_size": self.cache_max_size,
            "auto_resize": self.auto_resize,
            "max_width": self.max_width,
            "max_height": self.max_height,
            "quality": self.quality
        }


@dataclass 
class RealTimeTrackingConfig:
    """实时状态追踪配置"""
    enable_tracking: bool = True
    status_file_name: str = "execution_status.json"
    update_interval: float = 0.5  # 状态更新间隔(秒)
    
    # 追踪内容配置
    track_step_progress: bool = True
    track_checkpoint_status: bool = True
    track_performance_metrics: bool = True
    track_screenshot_info: bool = True
    include_base64_screenshots: bool = True
    
    # 状态文件格式
    include_timestamp: bool = True
    include_duration: bool = True
    include_error_details: bool = True
    pretty_format: bool = True
    
    # API接口配置
    enable_http_api: bool = True
    api_port: int = 8080
    api_endpoint: str = "/api/v1/execution/status"
    
    # 进度计算配置
    calculate_eta: bool = True  # 计算预估完成时间
    smooth_progress: bool = True  # 平滑进度更新
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_tracking": self.enable_tracking,
            "status_file_name": self.status_file_name,
            "update_interval": self.update_interval,
            "track_step_progress": self.track_step_progress,
            "track_checkpoint_status": self.track_checkpoint_status,
            "track_performance_metrics": self.track_performance_metrics,
            "track_screenshot_info": self.track_screenshot_info,
            "include_base64_screenshots": self.include_base64_screenshots,
            "include_timestamp": self.include_timestamp,
            "include_duration": self.include_duration,
            "include_error_details": self.include_error_details,
            "pretty_format": self.pretty_format,
            "enable_http_api": self.enable_http_api,
            "api_port": self.api_port,
            "api_endpoint": self.api_endpoint,
            "calculate_eta": self.calculate_eta,
            "smooth_progress": self.smooth_progress
        }


@dataclass
class LoggingConfig:
    """日志配置 - 支持独立日志文件"""
    enable_separate_log: bool = True
    log_level: str = "INFO"
    log_format: str = "%(asctime)s [%(levelname)s] %(message)s"
    enable_step_tracking: bool = True
    enable_performance_logging: bool = False
    rotation_size: str = "10MB"
    retention_days: int = 30
    
    # 日志文件命名
    log_file_prefix: str = "execution_log"
    include_task_id: bool = True
    include_timestamp: bool = True
    
    # 新增：与现有日志系统集成
    use_loguru: bool = True
    enable_json_logging: bool = False
    log_to_console: bool = True
    enable_debug_screenshots: bool = True
    
    # 日志输出目录
    log_directory: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_separate_log": self.enable_separate_log,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "enable_step_tracking": self.enable_step_tracking,
            "enable_performance_logging": self.enable_performance_logging,
            "rotation_size": self.rotation_size,
            "retention_days": self.retention_days,
            "log_file_prefix": self.log_file_prefix,
            "include_task_id": self.include_task_id,
            "include_timestamp": self.include_timestamp,
            "use_loguru": self.use_loguru,
            "enable_json_logging": self.enable_json_logging,
            "log_to_console": self.log_to_console,
            "enable_debug_screenshots": self.enable_debug_screenshots,
            "log_directory": self.log_directory
        }
    
    def get_log_file_name(self, task_id: str) -> str:
        """生成日志文件名"""
        parts = [self.log_file_prefix]
        
        if self.include_task_id:
            parts.append(task_id)
            
        if self.include_timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)
            
        return "_".join(parts) + ".log"


@dataclass
class TemplateConfig:
    """模板引擎配置"""
    template_dir: str = "templates"
    auto_reload: bool = True
    cache_size: int = 100
    enable_async: bool = False
    
    # 自定义过滤器和函数
    custom_filters: Dict[str, str] = field(default_factory=dict)
    custom_functions: Dict[str, str] = field(default_factory=dict)
    
    # 模板继承和包含
    enable_inheritance: bool = True
    enable_includes: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_dir": self.template_dir,
            "auto_reload": self.auto_reload,
            "cache_size": self.cache_size,
            "enable_async": self.enable_async,
            "custom_filters": self.custom_filters,
            "custom_functions": self.custom_functions,
            "enable_inheritance": self.enable_inheritance,
            "enable_includes": self.enable_includes
        }


@dataclass
class DeviceConfig:
    """设备操作配置"""
    device_serial: Optional[str] = None
    connection_timeout: int = 30
    operation_timeout: int = 15
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # UI稳定性检查
    ui_stability_timeout: float = 5.0
    ui_stability_check_interval: float = 0.5
    ui_stability_max_retries: int = 3
    
    # 截图配置
    screenshot_format: str = "png"
    screenshot_quality: int = 85
    auto_screenshot: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_serial": self.device_serial,
            "connection_timeout": self.connection_timeout,
            "operation_timeout": self.operation_timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "ui_stability_timeout": self.ui_stability_timeout,
            "ui_stability_check_interval": self.ui_stability_check_interval,
            "ui_stability_max_retries": self.ui_stability_max_retries,
            "screenshot_format": self.screenshot_format,
            "screenshot_quality": self.screenshot_quality,
            "auto_screenshot": self.auto_screenshot
        }


@dataclass
class ValidationConfig:
    """验证功能配置 - 支持新的条件表达式系统"""
    # 图像相似度配置
    default_similarity_threshold: float = 0.8
    use_ssim_by_default: bool = True
    
    # 文本匹配配置
    default_text_matching: str = "contains"  # exact, contains, regex
    case_sensitive_by_default: bool = False
    
    # 摄像头检测配置
    default_camera_confidence: float = 0.7
    camera_analysis_timeout: float = 10.0
    
        # 并行验证配置
    enable_parallel_validation: bool = True
    max_parallel_validators: int = 3
    
    # 🔄 条件表达式配置（简化版）
    enable_condition_expression: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_similarity_threshold": self.default_similarity_threshold,
            "use_ssim_by_default": self.use_ssim_by_default,
            "default_text_matching": self.default_text_matching,
            "case_sensitive_by_default": self.case_sensitive_by_default,
            "default_camera_confidence": self.default_camera_confidence,
            "camera_analysis_timeout": self.camera_analysis_timeout,
            "enable_parallel_validation": self.enable_parallel_validation,
            "max_parallel_validators": self.max_parallel_validators,
            "enable_condition_expression": self.enable_condition_expression
        }


@dataclass
class ControlFlowExecutionConfig:
    """控制流执行配置 - 支持if/for/while等控制结构的执行参数"""
    # 控制流执行配置
    enable_control_flow: bool = True
    max_nesting_depth: int = 10      # 最大嵌套深度
    max_loop_iterations: int = 1000  # 最大循环迭代次数
    loop_timeout: float = 300.0      # 循环执行超时时间(秒)
    
    # 条件分支配置
    enable_short_circuit: bool = True  # 启用短路求值
    default_branch_timeout: float = 30.0  # 默认分支执行超时
    
    # 循环配置
    for_loop_timeout: float = 60.0   # for循环超时时间
    while_loop_timeout: float = 120.0  # while循环超时时间
    loop_check_interval: float = 1.0  # 循环检查间隔
    
    # 错误处理配置
    continue_on_branch_error: bool = False  # 分支错误时是否继续执行
    max_consecutive_failures: int = 3       # 最大连续失败次数
    
    # 调试配置
    enable_flow_debugging: bool = False     # 启用控制流调试
    log_flow_decisions: bool = True         # 记录控制流决策
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_control_flow": self.enable_control_flow,
            "max_nesting_depth": self.max_nesting_depth,
            "max_loop_iterations": self.max_loop_iterations,
            "loop_timeout": self.loop_timeout,
            "enable_short_circuit": self.enable_short_circuit,
            "default_branch_timeout": self.default_branch_timeout,
            "for_loop_timeout": self.for_loop_timeout,
            "while_loop_timeout": self.while_loop_timeout,
            "loop_check_interval": self.loop_check_interval,
            "continue_on_branch_error": self.continue_on_branch_error,
            "max_consecutive_failures": self.max_consecutive_failures,
            "enable_flow_debugging": self.enable_flow_debugging,
            "log_flow_decisions": self.log_flow_decisions
        }

# 默认配置实例
DEFAULT_TRACKING_CONFIG = RealTimeTrackingConfig()
DEFAULT_LOGGING_CONFIG = LoggingConfig()
DEFAULT_TEMPLATE_CONFIG = TemplateConfig()
DEFAULT_DEVICE_CONFIG = DeviceConfig()
DEFAULT_VALIDATION_CONFIG = ValidationConfig()
DEFAULT_CONTROL_FLOW_EXECUTION_CONFIG = ControlFlowExecutionConfig()
 