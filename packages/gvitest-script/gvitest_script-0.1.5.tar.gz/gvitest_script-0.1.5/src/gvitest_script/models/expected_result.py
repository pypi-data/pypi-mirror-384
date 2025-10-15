"""
统一验证模型

支持预期结果验证、控制流条件判断、迭代条件判断
- 统一的验证数据结构，可复用于多种场景
- 支持Agent模式和手动模式的验证
- 支持图像、文本、元素等多种验证类型
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import json
from datetime import datetime


class ValidationMode(Enum):
    """验证模式"""
    AGENT = "agent"     # Agent自动模式
    MANUAL = "manual"   # 手动模式（默认，更灵活）


class DataSource(Enum):
    """数据来源"""
    ADB_SCREENSHOT = "adb_screenshot"        # ADB截图（Agent和Manual模式共用）
    CAMERA_PHOTO = "camera_photo"            # 摄像头拍照（Agent和Manual模式共用）
    CAN_SIGNAL = "can_signal"                # CAN信号（Manual模式专用）


class ValidationType(Enum):
    """验证类型"""
    IMAGE = "image"    # 图像匹配
    TEXT = "text"      # 文本检测（OCR/元素检测）
    SIGNAL = "signal"  # CAN信号验证（使用can_title和can_values）


# 移除复杂的配置对象，改为简单字段


@dataclass
class ValidationModel:
    """
    统一验证模型 - 支持预期结果验证、控制流条件判断、迭代条件判断

    这是可复用的数据结构，支持：
    1. 预期结果验证（expected_results）
    2. 控制流条件判断（if/while的condition）
    3. 迭代条件判断（for循环的迭代条件）

    支持的模式和数据源组合：
    
    Agent模式（自动图像验证）：
    1. agent + adb_screenshot：Agent使用ADB截图进行自动图像匹配
    2. agent + camera_photo：Agent使用摄像头拍照进行自动图像匹配
    
    Manual模式（手动验证）：
    3. manual + adb_screenshot + image：对ADB截图进行手动图像匹配
    4. manual + adb_screenshot + text：对ADB截图进行手动文本检测（OCR）
    5. manual + camera_photo + image：对摄像头拍照进行手动图像匹配
    6. manual + camera_photo + text：对摄像头拍照进行手动文本检测（OCR）
    

    """
    id: str
    description: str
    mode: ValidationMode

    # 🔧 统一基础配置（所有模式必需）
    data_source: DataSource                       # 数据来源（所有模式必需）
    validation_type: Optional[ValidationType] = None  # 验证类型（手动模式必需）

    # 🎯 统一图像配置（Agent和手动模式共用）
    target_image_path: Optional[str] = None      # 目标图像文件路径（小图标/元素）
    reference_image_path: Optional[str] = None   # 参考图文件路径（完整截图）
    target_bbox: Optional[List[float]] = None      # 目标坐标 [x1, y1, x2, y2]
    roi_coordinates: Optional[List[float]] = None  # 感兴趣区域坐标 [x1, y1, x2, y2]，None表示全图
    similarity_threshold: float = 0.8           # 相似度阈值（0.0-1.0）

    # 📝 文本验证配置
    target_text: Optional[str] = None            # 目标文本（text验证类型必需）
    expect_exists: bool = True                   # 期望存在（True=期望存在，False=期望不存在）
    wait_time: Optional[int] = None              # 等待时间（秒）
    timeout: Optional[int] = None                # 超时时间（秒）
    
    # 🚗 CAN信号验证配置
    can_title: Optional[str] = None              # CAN信号名称（signal验证类型必需）
    can_values: Optional[List[Dict]] = None      # CAN信号值规则列表（signal验证类型必需）

    # ✅ 执行结果数据
    is_pass: Optional[bool] = None               # 验证是否通过（True/False/None=未执行）
    details: str = ""                            # 详细验证结果说明
    validation_screenshot_path: Optional[str] = None  # 验证截图路径（当前验证时的截图）
    execution_duration: Optional[float] = None  # 执行耗时（秒）
    execution_timestamp: Optional[str] = None   # 执行时间戳
    
    def __post_init__(self):
        """数据验证和后处理"""
        if self.mode == ValidationMode.AGENT:
            # Agent模式验证
            if self.data_source not in [DataSource.ADB_SCREENSHOT, DataSource.CAMERA_PHOTO]:
                raise ValueError("Agent模式必须使用ADB_SCREENSHOT或CAMERA_PHOTO数据源")
            if not self.target_image_path:
                raise ValueError("Agent模式需要提供target_image_path")
            if not self.reference_image_path:
                raise ValueError("Agent模式需要提供reference_image_path")
            if not self.target_bbox or len(self.target_bbox) != 4:
                raise ValueError("Agent模式需要提供target_bbox [x1, y1, x2, y2]")

        elif self.mode == ValidationMode.MANUAL:
            # 手动模式验证
            if self.data_source not in [DataSource.ADB_SCREENSHOT, DataSource.CAMERA_PHOTO, DataSource.CAN_SIGNAL]:
                raise ValueError("手动模式必须使用ADB_SCREENSHOT、CAMERA_PHOTO或CAN_SIGNAL数据源")
            if not self.validation_type:
                raise ValueError("手动模式需要指定validation_type")

            # 验证类型配置检查
            if self.validation_type == ValidationType.IMAGE:
                if not self.target_image_path:
                    raise ValueError("image验证类型需要提供target_image_path")
                if not self.reference_image_path:
                    raise ValueError("image验证类型需要提供reference_image_path")
                if not self.target_bbox or len(self.target_bbox) != 4:
                    raise ValueError("image验证类型需要提供target_bbox [x1, y1, x2, y2]")
            elif self.validation_type == ValidationType.TEXT and not self.target_text:
                raise ValueError("text验证类型需要提供target_text")
            elif self.validation_type == ValidationType.SIGNAL:
                if self.data_source != DataSource.CAN_SIGNAL:
                    raise ValueError("signal验证类型必须使用CAN_SIGNAL数据源")
                if not self.can_title:
                    raise ValueError("signal验证类型必须提供can_title")
                if not self.can_values:
                    raise ValueError("signal验证类型必须提供can_values")


    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""
        result = {
            "id": self.id,
            "description": self.description,
            "mode": self.mode.value,
            "is_pass": self.is_pass,
            "details": self.details,
            "reference_image_path": self.reference_image_path,
            "target_image_path": self.target_image_path,
            "validation_screenshot_path": self.validation_screenshot_path,
            "execution_duration": self.execution_duration,
            "execution_timestamp": self.execution_timestamp
        }

        # 添加统一的数据源配置
        result.update({
            "data_source": self.data_source.value,
            "similarity_threshold": self.similarity_threshold
        })

        # 添加模式特定的配置
        if self.mode == ValidationMode.AGENT:
            result.update({
                "target_image_path": self.target_image_path,
                "reference_image_path": self.reference_image_path,
                "target_bbox": self.target_bbox,
                "roi_coordinates": self.roi_coordinates
            })
        elif self.mode == ValidationMode.MANUAL:
            result.update({
                "validation_type": self.validation_type.value if self.validation_type else None
            })

            # 根据验证类型添加对应的目标配置
            if self.validation_type == ValidationType.IMAGE:
                result.update({
                    "target_image_path": self.target_image_path,
                    "reference_image_path": self.reference_image_path,
                    "target_bbox": self.target_bbox,
                    "roi_coordinates": self.roi_coordinates
                })
            elif self.validation_type == ValidationType.TEXT:
                result["target_text"] = self.target_text
            elif self.validation_type == ValidationType.SIGNAL:
                result.update({
                    "can_title": self.can_title,
                    "can_values": self.can_values
                })


        # 添加通用字段
        result["expect_exists"] = self.expect_exists
        if self.wait_time is not None:
            result["wait_time"] = self.wait_time
        if self.timeout is not None:
            result["timeout"] = self.timeout

        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationModel':
        """从字典创建ValidationModel实例"""
        # 基础字段
        # 🔧 修复：为mode字段提供默认值，避免KeyError
        mode_value = data.get("mode", "manual")  # 默认为manual模式
        mode = ValidationMode(mode_value)
        data_source = DataSource(data["data_source"])
        
        # 手动模式字段
        validation_type = None
        if mode == ValidationMode.MANUAL:
            if "validation_type" in data:
                validation_type = ValidationType(data["validation_type"])
        
        return cls(
            id=data.get("id", "unknown_validation"),
            description=data.get("description", "ValidationModel"),
            mode=mode,
            data_source=data_source,
            validation_type=validation_type,
            target_image_path=data.get("target_image_path"),
            reference_image_path=data.get("reference_image_path"),
            target_bbox=data.get("target_bbox"),
            roi_coordinates=data.get("roi_coordinates"),
            similarity_threshold=0.8,  # 写死为0.8，不再从接口接收
            target_text=data.get("target_text"),
            expect_exists=data.get("expect_exists", True),  # 默认为True（期望存在）
            can_title=data.get("can_title"),
            can_values=data.get("can_values"),
            wait_time=data.get("wait_time"),
            timeout=data.get("timeout"),
            is_pass=data.get("is_pass"),
            details=data.get("details", ""),
            validation_screenshot_path=data.get("validation_screenshot_path"),
            execution_duration=data.get("execution_duration"),
            execution_timestamp=data.get("execution_timestamp")
        )
    
    def start_execution(self,
        is_pass: bool = None, 
        details: str = None, 
        validation_screenshot_path: str = None, 
        duration: float = None):
        """
        记录验证执行结果
        
        Args:
            is_pass: 验证是否通过
            details: 详细结果说明
            validation_screenshot_path: 验证截图路径
            duration: 执行耗时
        """
        self.is_pass = is_pass
        self.details = details
        self.validation_screenshot_path = validation_screenshot_path
        if duration is not None:
            self.execution_duration = duration
    
    def finish_execution(self, is_pass: bool, details: str, 
                        validation_screenshot_path: str = None, duration: float = None):
        """完成执行验证"""
        self.is_pass = is_pass
        self.details = details
        self.validation_screenshot_path = validation_screenshot_path
        if duration is not None:
            self.execution_duration = duration


@dataclass
class ValidationModelConfig:
    """验证模型列表配置"""
    results: List[ValidationModel] = field(default_factory=list)
    execution_mode: str = "sequential"  # sequential, parallel
    stop_on_required_failure: bool = True
    max_parallel_workers: int = 3
    
    def add_result(self, result: ValidationModel):
        """添加验证模型"""
        self.results.append(result)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "results": [r.to_dict() for r in self.results],
            "execution_mode": self.execution_mode,
            "stop_on_required_failure": self.stop_on_required_failure,
            "max_parallel_workers": self.max_parallel_workers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationModelConfig':
        """从字典创建配置实例"""
        results = [ValidationModel.from_dict(r) for r in data.get("results", [])]
        return cls(
            results=results,
            execution_mode=data.get("execution_mode", "sequential"),
            stop_on_required_failure=data.get("stop_on_required_failure", True),
            max_parallel_workers=data.get("max_parallel_workers", 3)
        )


# 添加详细的响应状态枚举
class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"         # 等待执行
    RUNNING = "running"         # 正在执行
    COMPLETED = "completed"     # 执行完成
    FAILED = "failed"          # 执行失败
    ERROR = "error"            # 执行错误
    TIMEOUT = "timeout"        # 执行超时
    CANCELLED = "cancelled"    # 执行取消


class ValidationResult(Enum):
    """验证结果类型"""
    PASS = "pass"              # 验证通过
    FAIL = "fail"              # 验证失败
    PARTIAL = "partial"        # 部分通过
    UNKNOWN = "unknown"        # 未知结果


@dataclass
class ExpectedResultGroup:
    """
    预期结果组 - 支持表达式和多个验证模型
    
    结构：
    {
        "expression": "([预期结果1] || [预期结果2]) && ([预期结果3])",
        "expected_result": ValidationModel
    }
    """
    expression: Optional[str] = None  # 条件表达式，如 "([预期结果1] || [预期结果2]) && ([预期结果3])"
    expected_result: Optional[ValidationModel] = None  # 单个预期结果（向后兼容）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        
        if self.expression:
            result["expression"] = self.expression
        
        if self.expected_result:
            result["expected_result"] = self.expected_result.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpectedResultGroup':
        """从字典创建ExpectedResultGroup实例"""
        expected_result = None
        if "expected_result" in data and data["expected_result"]:
            expected_result = ValidationModel.from_dict(data["expected_result"])
        
        return cls(
            expression=data.get("expression"),
            expected_result=expected_result
        )


@dataclass
class ExpectedResultResponse:
    """
    预期结果响应数据模型 - 基于模板实际输出
    对应 result_validation_v2.j2 模板中的 result_data 结构
    """
    # 🆔 基础信息（来自模板） - 必需字段
    id: str                                      # 预期结果ID
    description: str                             # 预期结果描述
    mode: str                                    # 验证模式 (agent/manual)
    is_pass: bool                                # 验证是否通过
    details: str                                 # 详细验证结果说明
    execution_timestamp: str                     # 执行时间戳
    execution_duration: float                    # 执行耗时（秒）
    
    # 🔧 模式特定配置（仅manual模式有） - 可选字段
    data_source: Optional[str] = None            # 数据来源 (adb_screenshot/camera_photo)
    validation_type: Optional[str] = None        # 验证类型 (image/text)
    screenshot_path: Optional[str] = None        # 验证时的截图文件路径
    
    # 📋 扩展字段（可选，用于API响应增强）
    request_id: Optional[str] = None             # 关联的请求ID（API层添加）
    validation_result: Optional[ValidationResult] = None  # 验证结果类型（基于is_pass自动设置）
    error_code: Optional[int] = None             # 错误代码（异常时）
    error_message: Optional[str] = None          # 错误信息（异常时）
    
    def __post_init__(self):
        """后处理验证"""
        # 自动设置validation_result
        if self.validation_result is None:
            self.validation_result = ValidationResult.PASS if self.is_pass else ValidationResult.FAIL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            # 基础信息（模板输出）
            "id": self.id,
            "description": self.description,
            "mode": self.mode,
            "is_pass": self.is_pass,
            "details": self.details,
            "execution_duration": self.execution_duration,
            "execution_timestamp": self.execution_timestamp,
            
            # 扩展字段
            "validation_result": self.validation_result.value if self.validation_result else None,
        }
        
        # 添加可选字段
        if self.screenshot_path:
            result["screenshot_path"] = self.screenshot_path
        
        # 添加模式特定字段
        if self.data_source:
            result["data_source"] = self.data_source
        if self.validation_type:
            result["validation_type"] = self.validation_type
        if self.request_id:
            result["request_id"] = self.request_id
        if self.error_code:
            result["error_code"] = self.error_code
        if self.error_message:
            result["error_message"] = self.error_message
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpectedResultResponse':
        """从字典创建ExpectedResultResponse实例（基于模板输出）"""
        # 处理枚举字段
        validation_result = None
        if "validation_result" in data and data["validation_result"]:
            validation_result = ValidationResult(data["validation_result"])
        
        return cls(
            # 模板基础字段
            id=data["id"],
            description=data["description"],
            mode=data["mode"],
            is_pass=data["is_pass"],
            details=data["details"],
            screenshot_path=data.get("screenshot_path"),
            execution_timestamp=data["execution_timestamp"],
            execution_duration=data["execution_duration"],
            
            # 模式特定字段
            data_source=data.get("data_source"),
            validation_type=data.get("validation_type"),
            
            # 扩展字段
            request_id=data.get("request_id"),
            validation_result=validation_result,
            error_code=data.get("error_code"),
            error_message=data.get("error_message")
        )
    
    def set_success(self, details: str = ""):
        """设置成功结果"""
        self.is_pass = True
        self.validation_result = ValidationResult.PASS
        if details:
            self.details = details
    
    def set_failure(self, details: str = ""):
        """设置失败结果"""
        self.is_pass = False
        self.validation_result = ValidationResult.FAIL
        if details:
            self.details = details
    
    def set_error(self, error_code: int, error_message: str):
        """设置错误结果"""
        self.is_pass = False
        self.validation_result = ValidationResult.FAIL
        self.error_code = error_code
        self.error_message = error_message
        self.details = f"执行错误: {error_message}"


# 预定义的验证详情结构模板
class ValidationDetailsTemplates:
    """验证详情模板"""
    
    @staticmethod
    def agent_details_template() -> Dict[str, Any]:
        """Agent模式验证详情模板"""
        return {
            "similarity_score": 0.0,           # 相似度分数
            "matched_bbox": [0, 0, 0, 0],      # 实际匹配的边界框
            "target_found": False,             # 是否找到目标
            "match_method": "template_matching", # 匹配方法
            "processing_time": 0.0,            # 图像处理耗时
            "image_quality_score": 0.0,        # 图像质量分数
            "scale_factor": 1.0,               # 缩放因子
            "rotation_angle": 0.0,             # 旋转角度
            "color_variance": 0.0              # 颜色方差
        }
    
    @staticmethod
    def manual_details_template() -> Dict[str, Any]:
        """手动模式验证详情模板"""
        return {
            "data_source_info": {
                "source_type": "",             # 数据源类型
                "capture_time": "",            # 采集时间
                "image_size": [0, 0],          # 图像尺寸
                "file_size": 0                 # 文件大小
            },
            "validation_info": {
                "validation_type": "",         # 验证类型
                "processing_method": "",       # 处理方法
                "confidence_threshold": 0.0    # 置信度阈值
            },
            "ocr_results": {                   # OCR结果（文本验证时）
                "detected_text": "",
                "confidence": 0.0,
                "language": "",
                "text_regions": []
            },
            "image_match_results": {           # 图像匹配结果（图像验证时）
                "similarity_score": 0.0,
                "matched_regions": [],
                "match_method": ""
            }
        }





