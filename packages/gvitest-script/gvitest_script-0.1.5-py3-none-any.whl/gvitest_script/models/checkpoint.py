"""
检查点相关数据模型
用于定义步骤执行过程中的验证点和预期结果验证
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class CheckpointType(Enum):
    """检查点类型枚举"""
    IMAGE = "image"           # 图像验证（与预期结果image验证统一）
    TEXT = "text"             # 文本验证（与预期结果text验证统一）
    UI_ELEMENT = "ui_element" # UI元素验证
    CAN_SIGNAL = "can_signal" # CAN信号验证
    CUSTOM = "custom"         # 自定义验证


class CheckpointStatus(Enum):
    """检查点状态枚举"""
    PENDING = "待执行"
    RUNNING = "执行中"
    PASSED = "通过"
    FAILED = "失败"
    SKIPPED = "跳过"
    ERROR = "错误"


@dataclass
class CheckpointInfo:
    """
    步骤级检查点信息 - 简化版本
    用于验证单个操作步骤的执行结果
    
    新格式设计：
    - type: 检查点类型 (image, text, ui_element, can_signal, custom)
    - description: 检查点描述
    - expected: 期望值，根据type类型进行不同解析
        - image类型: 图像文件路径
        - text类型: 期望的文本内容
        - ui_element类型: UI元素选择器或描述
        - can_signal类型: CAN信号期望值
        - custom类型: 自定义验证数据
    """
    # 基本信息
    type: str = CheckpointType.IMAGE.value
    description: str = ""
    expected: str = ""  # 统一的期望值字段，根据type进行解析

    # 验证图像数据（统一使用文件路径格式）
    screenshot_path: Optional[str] = None   # 验证截图文件路径
    target_bbox: Optional[List[float]] = None  # 目标坐标 [x1, y1, x2, y2]

    # 验证结果
    is_pass: Optional[bool] = None
    detail: str = ""
    similarity_score: Optional[float] = None  # 图像相似度分数

    # 配置参数
    timeout: int = 5000                       # 超时时间（毫秒）
    similarity_threshold: float = 0.8         # 相似度阈值
    retry_count: int = 3                      # 重试次数

    # 执行信息
    status: str = CheckpointStatus.PENDING.value
    execution_time: Optional[float] = None    # 执行耗时（秒）
    executed_at: Optional[str] = None         # 执行时间戳
    error_message: Optional[str] = None       # 错误信息
    

    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": self.type,
            "description": self.description,
            "expected": self.expected,
            "screenshot_path": self.screenshot_path,
            "target_bbox": self.target_bbox,
            "is_pass": self.is_pass,
            "detail": self.detail,
            "similarity_score": self.similarity_score,
            "timeout": self.timeout,
            "similarity_threshold": self.similarity_threshold,
            "retry_count": self.retry_count,
            "status": self.status,
            "execution_time": self.execution_time,
            "executed_at": self.executed_at,
            "error_message": self.error_message
        }
    
    def mark_as_passed(self, detail: str = "", similarity_score: Optional[float] = None):
        """标记检查点为通过"""
        self.is_pass = True
        self.status = CheckpointStatus.PASSED.value
        self.detail = detail
        self.similarity_score = similarity_score
        self.executed_at = datetime.now().isoformat()
    
    def mark_as_failed(self, detail: str = "", error_message: Optional[str] = None):
        """标记检查点为失败"""
        self.is_pass = False
        self.status = CheckpointStatus.FAILED.value
        self.detail = detail
        self.error_message = error_message
        self.executed_at = datetime.now().isoformat()
    
    def mark_as_error(self, error_message: str):
        """标记检查点为错误"""
        self.is_pass = False
        self.status = CheckpointStatus.ERROR.value
        self.error_message = error_message
        self.detail = f"检查点执行出错: {error_message}"
        self.executed_at = datetime.now().isoformat()


@dataclass
class ExpectedCheckpoint:
    """
    任务级预期检查点（兼容旧架构）
    注意：在新架构中，此概念已被 ExpectedResult 替代
    此类主要用于向后兼容和数据迁移
    """
    # 基本信息
    checkpoint_id: str
    checkpoint_type: str = CheckpointType.IMAGE.value
    description: str = ""

    # 验证配置（统一使用文件路径格式）
    target_image_path: Optional[str] = None
    expected_text: Optional[str] = None
    similarity_threshold: float = 0.8
    timeout: int = 30000  # 30秒

    # 验证结果
    is_pass: Optional[bool] = None
    actual_result: Optional[str] = None
    detail: str = ""
    screenshot_path: Optional[str] = None

    # 执行信息
    executed_at: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_type": self.checkpoint_type,
            "description": self.description,
            "target_image_path": self.target_image_path,
            "expected_text": self.expected_text,
            "similarity_threshold": self.similarity_threshold,
            "timeout": self.timeout,
            "is_pass": self.is_pass,
            "actual_result": self.actual_result,
            "detail": self.detail,
            "screenshot_path": self.screenshot_path,
            "executed_at": self.executed_at,
            "execution_time": self.execution_time
        }
    
    def to_expected_result(self) -> Dict[str, Any]:
        """转换为新架构的 ExpectedResult 字典格式"""
        # 确定验证模式和类型
        mode = "agent"  # 默认使用Agent模式
        validation_type = "image"  # 默认图像验证
        data_source = "adb_screenshot"

        if self.checkpoint_type == CheckpointType.TEXT.value:
            mode = "manual"
            validation_type = "text"
            data_source = "adb_screenshot"

        return {
            "id": self.checkpoint_id,
            "description": self.description,
            "mode": mode,
            "data_source": data_source,
            "validation_type": validation_type,
            "target_image_path": self.target_image_path or "",
            "reference_image_path": "",
            "target_bbox": [],  # 空列表，符合 List[float] 格式
            "target_text": self.expected_text or "",
            "wait_time": 0,
            "timeout": self.timeout // 1000,  # 转换为秒
            "is_pass": self.is_pass,
            "details": self.detail,
            "screenshot_path": self.screenshot_path,
            "execution_timestamp": self.executed_at,
            "execution_duration": self.execution_time
        }


@dataclass
class CheckpointValidationConfig:
    """检查点验证配置"""
    # 图像验证配置
    default_similarity_threshold: float = 0.8
    image_matching_algorithm: str = "ssim"  # ssim, template_match
    enable_multi_scale_matching: bool = True
    
    # 文本验证配置
    text_matching_case_sensitive: bool = False
    text_matching_type: str = "contains"  # exact, contains, regex
    
    # 执行配置
    default_timeout: int = 5000  # 毫秒
    default_retry_count: int = 3
    retry_delay: float = 1.0  # 秒
    
    # 截图配置
    take_screenshot_on_failure: bool = True
    screenshot_format: str = "png"
    screenshot_quality: int = 85
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "default_similarity_threshold": self.default_similarity_threshold,
            "image_matching_algorithm": self.image_matching_algorithm,
            "enable_multi_scale_matching": self.enable_multi_scale_matching,
            "text_matching_case_sensitive": self.text_matching_case_sensitive,
            "text_matching_type": self.text_matching_type,
            "default_timeout": self.default_timeout,
            "default_retry_count": self.default_retry_count,
            "retry_delay": self.retry_delay,
            "take_screenshot_on_failure": self.take_screenshot_on_failure,
            "screenshot_format": self.screenshot_format,
            "screenshot_quality": self.screenshot_quality
        }


# 默认检查点验证配置
DEFAULT_CHECKPOINT_CONFIG = CheckpointValidationConfig() 