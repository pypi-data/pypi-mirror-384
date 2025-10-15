"""
统一错误处理机制
包括错误恢复、监控告警和详细的错误信息
"""
import logging
import traceback
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
from pathlib import Path

from ..models.api_models import ErrorCode


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"          # 低：警告级别，不影响主要功能
    MEDIUM = "medium"    # 中：错误级别，影响部分功能
    HIGH = "high"        # 高：严重错误，影响核心功能
    CRITICAL = "critical" # 危急：系统级错误，需要立即处理


class ErrorCategory(Enum):
    """错误分类"""
    VALIDATION = "validation"      # 验证错误
    EXECUTION = "execution"        # 执行错误
    SYSTEM = "system"             # 系统错误
    NETWORK = "network"           # 网络错误
    RESOURCE = "resource"         # 资源错误
    BUSINESS = "business"         # 业务逻辑错误
    CAN = "can"                   # CAN相关错误


@dataclass
class ErrorContext:
    """错误上下文信息"""
    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_code: ErrorCode
    message: str
    details: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # 业务上下文
    script_id: Optional[str] = None
    step_number: Optional[int] = None
    action_type: Optional[str] = None
    
    # 系统上下文
    system_info: Dict[str, Any] = field(default_factory=dict)
    request_info: Dict[str, Any] = field(default_factory=dict)
    
    # 恢复信息
    recovery_attempted: bool = False
    recovery_success: bool = False
    recovery_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "category": self.category.value,
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "stack_trace": self.stack_trace,
            "script_id": self.script_id,
            "step_number": self.step_number,
            "action_type": self.action_type,
            "system_info": self.system_info,
            "request_info": self.request_info,
            "recovery_attempted": self.recovery_attempted,
            "recovery_success": self.recovery_success,
            "recovery_details": self.recovery_details
        }


@dataclass
class RecoveryStrategy:
    """错误恢复策略"""
    name: str
    description: str
    max_attempts: int
    retry_delay: float
    recovery_function: Callable[[ErrorContext], bool]
    applicable_errors: List[ErrorCode]
    
    def is_applicable(self, error_code: ErrorCode) -> bool:
        """检查策略是否适用于指定错误"""
        return error_code in self.applicable_errors


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.error_log_file = workspace_root / "logs" / "error_log.json"
        self.recovery_strategies: List[RecoveryStrategy] = []
        self.error_callbacks: List[Callable[[ErrorContext], None]] = []
        self.monitoring_enabled = True
        
        # 确保日志目录存在
        self.error_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认恢复策略
        self._init_default_recovery_strategies()
    
    def _init_default_recovery_strategies(self):
        """初始化默认恢复策略"""
        
        # 设备连接恢复策略
        def recover_device_connection(context: ErrorContext) -> bool:
            """恢复设备连接"""
            try:
                logging.info(f"尝试恢复设备连接 - 错误ID: {context.error_id}")
                # 这里可以添加实际的设备重连逻辑
                # 例如：重新初始化uiautomator2连接
                time.sleep(2)  # 等待设备稳定
                return True
            except Exception as e:
                logging.error(f"设备连接恢复失败: {e}")
                return False
        
        self.recovery_strategies.append(RecoveryStrategy(
            name="device_connection_recovery",
            description="设备连接恢复策略",
            max_attempts=3,
            retry_delay=2.0,
            recovery_function=recover_device_connection,
            applicable_errors=[ErrorCode.DEVICE_CONNECTION_FAILED, ErrorCode.DEVICE_OPERATION_FAILED]
        ))
        
        # UI稳定性恢复策略
        def recover_ui_stability(context: ErrorContext) -> bool:
            """恢复UI稳定性"""
            try:
                logging.info(f"尝试恢复UI稳定性 - 错误ID: {context.error_id}")
                # 这里可以添加UI稳定性恢复逻辑
                # 例如：等待更长时间或执行特定操作
                time.sleep(3)  # 等待UI稳定
                return True
            except Exception as e:
                logging.error(f"UI稳定性恢复失败: {e}")
                return False
        
        self.recovery_strategies.append(RecoveryStrategy(
            name="ui_stability_recovery",
            description="UI稳定性恢复策略",
            max_attempts=2,
            retry_delay=3.0,
            recovery_function=recover_ui_stability,
            applicable_errors=[ErrorCode.UI_STABILITY_TIMEOUT]
        ))
        
        # 截图恢复策略
        def recover_screenshot(context: ErrorContext) -> bool:
            """恢复截图功能"""
            try:
                logging.info(f"尝试恢复截图功能 - 错误ID: {context.error_id}")
                # 这里可以添加截图恢复逻辑
                # 例如：清理临时文件、重新初始化截图功能
                return True
            except Exception as e:
                logging.error(f"截图功能恢复失败: {e}")
                return False
        
        self.recovery_strategies.append(RecoveryStrategy(
            name="screenshot_recovery",
            description="截图功能恢复策略",
            max_attempts=2,
            retry_delay=1.0,
            recovery_function=recover_screenshot,
            applicable_errors=[ErrorCode.SCREENSHOT_FAILED]
        ))
        
        # CAN连接恢复策略
        def recover_can_connection(context: ErrorContext) -> bool:
            """恢复CAN连接"""
            try:
                logging.info(f"尝试恢复CAN连接 - 错误ID: {context.error_id}")
                # 这里可以添加实际的CAN连接恢复逻辑
                # 例如：重新连接MQTT、重置CAN服务器连接等
                time.sleep(1)  # 等待网络稳定
                return True
            except Exception as e:
                logging.error(f"CAN连接恢复失败: {e}")
                return False
        
        self.recovery_strategies.append(RecoveryStrategy(
            name="can_connection_recovery",
            description="CAN连接恢复策略",
            max_attempts=3,
            retry_delay=2.0,
            recovery_function=recover_can_connection,
            applicable_errors=[ErrorCode.NETWORK_ERROR]  # 假设网络错误包含CAN连接问题
        ))
        
        # CAN采集恢复策略
        def recover_can_capture(context: ErrorContext) -> bool:
            """恢复CAN信号采集"""
            try:
                logging.info(f"尝试恢复CAN信号采集 - 错误ID: {context.error_id}")
                # 这里可以添加实际的CAN采集恢复逻辑
                # 例如：重启采集线程、清理文件锁等
                time.sleep(1)
                return True
            except Exception as e:
                logging.error(f"CAN采集恢复失败: {e}")
                return False
        
        self.recovery_strategies.append(RecoveryStrategy(
            name="can_capture_recovery", 
            description="CAN信号采集恢复策略",
            max_attempts=2,
            retry_delay=3.0,
            recovery_function=recover_can_capture,
            applicable_errors=[ErrorCode.RESOURCE_EXHAUSTED]  # 资源耗尽错误包含采集问题
        ))
    
    def handle_error(
        self,
        error_code: ErrorCode,
        message: str,
        details: str = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.EXECUTION,
        script_id: str = None,
        step_number: int = None,
        action_type: str = None,
        system_info: Dict[str, Any] = None,
        request_info: Dict[str, Any] = None,
        attempt_recovery: bool = True
    ) -> ErrorContext:
        """处理错误"""
        
        # 生成错误ID
        import uuid
        error_id = str(uuid.uuid4())
        
        # 创建错误上下文
        error_context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            error_code=error_code,
            message=message,
            details=details,
            stack_trace=traceback.format_exc() if details else None,
            script_id=script_id,
            step_number=step_number,
            action_type=action_type,
            system_info=system_info or {},
            request_info=request_info or {}
        )
        
        # 记录错误
        self._log_error(error_context)
        
        # 尝试恢复（如果启用）
        if attempt_recovery and severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]:
            self._attempt_recovery(error_context)
        
        # 触发监控告警
        if self.monitoring_enabled:
            self._trigger_monitoring_alert(error_context)
        
        # 执行错误回调
        for callback in self.error_callbacks:
            try:
                callback(error_context)
            except Exception as e:
                logging.error(f"错误回调执行失败: {e}")
        
        return error_context
    
    def _log_error(self, error_context: ErrorContext):
        """记录错误到日志文件"""
        try:
            # 读取现有错误日志
            error_logs = []
            if self.error_log_file.exists():
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    try:
                        error_logs = json.load(f)
                    except json.JSONDecodeError:
                        error_logs = []
            
            # 添加新错误
            error_logs.append(error_context.to_dict())
            
            # 保持最近1000条错误记录
            if len(error_logs) > 1000:
                error_logs = error_logs[-1000:]
            
            # 写入文件
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(error_logs, f, ensure_ascii=False, indent=2, default=str)
            
            # 同时写入标准日志
            log_level = {
                ErrorSeverity.LOW: logging.WARNING,
                ErrorSeverity.MEDIUM: logging.ERROR,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(error_context.severity, logging.ERROR)
            
            logging.log(log_level, f"错误 [{error_context.error_id}]: {error_context.message}")
            if error_context.details:
                logging.log(log_level, f"详情: {error_context.details}")
                
        except Exception as e:
            logging.error(f"记录错误日志失败: {e}")
    
    def _attempt_recovery(self, error_context: ErrorContext):
        """尝试错误恢复"""
        applicable_strategies = [
            strategy for strategy in self.recovery_strategies
            if strategy.is_applicable(error_context.error_code)
        ]
        
        if not applicable_strategies:
            logging.info(f"没有适用的恢复策略 - 错误: {error_context.error_code}")
            return
        
        error_context.recovery_attempted = True
        
        for strategy in applicable_strategies:
            logging.info(f"尝试恢复策略: {strategy.name}")
            
            for attempt in range(strategy.max_attempts):
                try:
                    if strategy.recovery_function(error_context):
                        error_context.recovery_success = True
                        error_context.recovery_details = f"恢复策略 '{strategy.name}' 成功，尝试次数: {attempt + 1}"
                        logging.info(error_context.recovery_details)
                        return
                    else:
                        logging.warning(f"恢复策略 '{strategy.name}' 尝试 {attempt + 1} 失败")
                        if attempt < strategy.max_attempts - 1:
                            time.sleep(strategy.retry_delay)
                
                except Exception as e:
                    logging.error(f"恢复策略 '{strategy.name}' 执行异常: {e}")
                    if attempt < strategy.max_attempts - 1:
                        time.sleep(strategy.retry_delay)
        
        error_context.recovery_details = f"所有恢复策略都失败了"
        logging.error(error_context.recovery_details)
    
    def _trigger_monitoring_alert(self, error_context: ErrorContext):
        """触发监控告警"""
        try:
            # 根据错误严重程度决定是否发送告警
            if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                alert_data = {
                    "alert_type": "error",
                    "severity": error_context.severity.value,
                    "error_id": error_context.error_id,
                    "message": error_context.message,
                    "script_id": error_context.script_id,
                    "timestamp": error_context.timestamp
                }
                
                # 这里可以集成实际的监控系统
                # 例如：发送到钉钉、邮件、短信等
                logging.warning(f"监控告警: {json.dumps(alert_data, ensure_ascii=False)}")
                
        except Exception as e:
            logging.error(f"触发监控告警失败: {e}")
    
    def add_recovery_strategy(self, strategy: RecoveryStrategy):
        """添加自定义恢复策略"""
        self.recovery_strategies.append(strategy)
    
    def add_error_callback(self, callback: Callable[[ErrorContext], None]):
        """添加错误回调函数"""
        self.error_callbacks.append(callback)
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计信息"""
        try:
            if not self.error_log_file.exists():
                return {"total": 0, "by_severity": {}, "by_category": {}, "by_code": {}}
            
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                error_logs = json.load(f)
            
            # 过滤指定时间范围内的错误
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_errors = [
                error for error in error_logs
                if datetime.fromisoformat(error["timestamp"]) > cutoff_time
            ]
            
            # 统计信息
            stats = {
                "total": len(recent_errors),
                "by_severity": {},
                "by_category": {},
                "by_code": {},
                "recovery_success_rate": 0.0
            }
            
            # 按严重程度统计
            for error in recent_errors:
                severity = error.get("severity", "unknown")
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                
                category = error.get("category", "unknown")
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                
                error_code = error.get("error_code", "unknown")
                stats["by_code"][str(error_code)] = stats["by_code"].get(str(error_code), 0) + 1
            
            # 计算恢复成功率
            recovery_attempted = sum(1 for error in recent_errors if error.get("recovery_attempted", False))
            recovery_success = sum(1 for error in recent_errors if error.get("recovery_success", False))
            
            if recovery_attempted > 0:
                stats["recovery_success_rate"] = round(recovery_success / recovery_attempted * 100, 2)
            
            return stats
            
        except Exception as e:
            logging.error(f"获取错误统计失败: {e}")
            return {"error": str(e)}
    
    def clear_old_errors(self, days: int = 30):
        """清理旧的错误记录"""
        try:
            if not self.error_log_file.exists():
                return
            
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                error_logs = json.load(f)
            
            # 过滤保留指定天数内的错误
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            
            filtered_errors = [
                error for error in error_logs
                if datetime.fromisoformat(error["timestamp"]) > cutoff_time
            ]
            
            # 写回文件
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_errors, f, ensure_ascii=False, indent=2, default=str)
            
            removed_count = len(error_logs) - len(filtered_errors)
            logging.info(f"清理了 {removed_count} 条旧错误记录")
            
        except Exception as e:
            logging.error(f"清理旧错误记录失败: {e}")


# 全局错误处理器实例
_global_error_handler: Optional[ErrorHandler] = None


def init_error_handler(workspace_root: Path) -> ErrorHandler:
    """初始化全局错误处理器"""
    global _global_error_handler
    _global_error_handler = ErrorHandler(workspace_root)
    return _global_error_handler


def get_error_handler() -> Optional[ErrorHandler]:
    """获取全局错误处理器"""
    return _global_error_handler


def handle_error(
    error_code: ErrorCode,
    message: str,
    **kwargs
) -> ErrorContext:
    """快捷错误处理函数"""
    if _global_error_handler is None:
        raise RuntimeError("错误处理器未初始化，请先调用 init_error_handler()")
    
    return _global_error_handler.handle_error(error_code, message, **kwargs)


# 装饰器：自动错误处理
def auto_error_handler(
    error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.EXECUTION,
    attempt_recovery: bool = True
):
    """自动错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = handle_error(
                    error_code=error_code,
                    message=f"函数 {func.__name__} 执行失败: {str(e)}",
                    details=traceback.format_exc(),
                    severity=severity,
                    category=category,
                    attempt_recovery=attempt_recovery
                )
                
                # 如果恢复成功，重新尝试执行
                if error_context.recovery_success and attempt_recovery:
                    logging.info(f"恢复成功，重新执行函数: {func.__name__}")
                    return func(*args, **kwargs)
                else:
                    # 重新抛出异常
                    raise
        return wrapper
    return decorator


# ========== CAN 专用异常类 ==========

class CanError(Exception):
    """CAN操作基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "CAN_GENERAL_ERROR"
        self.details = details
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp
        }


class CanSendError(CanError):
    """CAN信号发送异常"""
    
    def __init__(self, message: str, channel_id: str = None, frame_id: str = None, 
                 signals: List[str] = None, **kwargs):
        super().__init__(message, error_code="CAN_SEND_ERROR", **kwargs)
        self.channel_id = channel_id
        self.frame_id = frame_id
        self.signals = signals or []
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "channel_id": self.channel_id,
            "frame_id": self.frame_id,
            "signals": self.signals
        })
        return result


class CanCaptureError(CanError):
    """CAN信号采集异常"""
    
    def __init__(self, message: str, task_id: str = None, channel_list: List[str] = None,
                 file_path: str = None, **kwargs):
        super().__init__(message, error_code="CAN_CAPTURE_ERROR", **kwargs)
        self.task_id = task_id
        self.channel_list = channel_list or []
        self.file_path = file_path
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "task_id": self.task_id,
            "channel_list": self.channel_list,
            "file_path": self.file_path
        })
        return result


class CanValidationError(CanError):
    """CAN信号验证异常"""
    
    def __init__(self, message: str, signal_name: str = None, expected_values: List[Dict] = None,
                 actual_value: Any = None, **kwargs):
        super().__init__(message, error_code="CAN_VALIDATION_ERROR", **kwargs)
        self.signal_name = signal_name
        self.expected_values = expected_values or []
        self.actual_value = actual_value
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "signal_name": self.signal_name,
            "expected_values": self.expected_values,
            "actual_value": self.actual_value
        })
        return result


class CanConnectionError(CanError):
    """CAN连接异常"""
    
    def __init__(self, message: str, ip: str = None, port: int = None, **kwargs):
        super().__init__(message, error_code="CAN_CONNECTION_ERROR", **kwargs)
        self.ip = ip
        self.port = port
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "ip": self.ip,
            "port": self.port
        })
        return result


class CanConfigurationError(CanError):
    """CAN配置异常"""
    
    def __init__(self, message: str, config_field: str = None, config_value: Any = None, **kwargs):
        super().__init__(message, error_code="CAN_CONFIGURATION_ERROR", **kwargs)
        self.config_field = config_field
        self.config_value = config_value
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "config_field": self.config_field,
            "config_value": self.config_value
        })
        return result 