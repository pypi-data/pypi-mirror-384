"""
统一API数据格式模型
定义标准的请求/响应格式，支持版本控制和数据验证
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import json


class APIVersion(Enum):
    """API版本枚举"""
    V1 = "v1"
    V2 = "v2"  # 新的Jinja2架构版本


class ResponseStatus(Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"  # 部分成功


class ErrorCode(Enum):
    """统一错误码体系"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    INVALID_REQUEST = 1001
    MISSING_PARAMETER = 1002
    INVALID_PARAMETER = 1003
    AUTHENTICATION_FAILED = 1004
    AUTHORIZATION_FAILED = 1005
    RATE_LIMIT_EXCEEDED = 1006
    
    # 脚本生成错误 (2000-2999)
    SCRIPT_GENERATION_FAILED = 2000
    TEMPLATE_NOT_FOUND = 2001
    TEMPLATE_RENDER_ERROR = 2002
    ACTION_VALIDATION_FAILED = 2003
    CONTEXT_VALIDATION_FAILED = 2004
    
    # 执行错误 (3000-3999)
    DEVICE_CONNECTION_FAILED = 3000
    DEVICE_OPERATION_FAILED = 3001
    SCREENSHOT_FAILED = 3002
    UI_STABILITY_TIMEOUT = 3003
    ACTION_EXECUTION_FAILED = 3004
    
    # 验证错误 (4000-4999)
    CHECKPOINT_VALIDATION_FAILED = 4000
    EXPECTED_RESULT_VALIDATION_FAILED = 4001
    IMAGE_COMPARISON_FAILED = 4002
    TEXT_VERIFICATION_FAILED = 4003
    
    # 系统错误 (5000-5999)
    FILE_OPERATION_FAILED = 5000
    DATABASE_ERROR = 5001
    NETWORK_ERROR = 5002
    RESOURCE_EXHAUSTED = 5003


@dataclass
class APIRequest:
    """标准API请求格式"""
    timestamp: Optional[str] = None
    client_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "client_info": self.client_info
        }


@dataclass
class APIResponse:
    """标准API响应格式"""
    status: str
    timestamp: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "status": self.status,
            "timestamp": self.timestamp
        }
        
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.warnings:
            result["warnings"] = self.warnings
        if self.metadata is not None:
            result["metadata"] = self.metadata
            
        return result
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, default=str)


@dataclass
class ErrorInfo:
    """错误信息格式"""
    code: int
    message: str
    details: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": self.message
        }
        
        if self.details:
            result["details"] = self.details
        if self.context:
            result["context"] = self.context
        if self.suggestions:
            result["suggestions"] = self.suggestions
            
        return result


# 注释：旧版本的ScriptGenerationRequest已被下方的平铺动作序列版本替代


@dataclass
class ScriptGenerationResponse(APIResponse):
    """脚本生成响应"""
    script_url: Optional[str] = None
    script_content: Optional[str] = None
    generation_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        
        # 将脚本相关信息放入data字段
        if self.status == ResponseStatus.SUCCESS.value:
            script_data = {}
            if self.script_url:
                script_data["script_url"] = self.script_url
            if self.script_content:
                script_data["script_content"] = self.script_content
            if self.generation_info:
                script_data["generation_info"] = self.generation_info
            
            result["data"] = script_data
        
        return result





@dataclass
class ScriptExecutionRequest(APIRequest):
    """脚本执行请求"""
    script_id: str = ""
    execution_config: Optional[Dict[str, Any]] = None
    device_config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "script_id": self.script_id,
            "execution_config": self.execution_config,
            "device_config": self.device_config
        })
        return result


@dataclass
class ScriptExecutionResponse(APIResponse):
    """脚本执行响应"""
    execution_id: Optional[str] = None
    task_status: Optional[str] = None  # "started", "running", "completed", "failed"
    execution_summary: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        
        if self.status == ResponseStatus.SUCCESS.value:
            execution_data = {}
            if self.execution_id:
                execution_data["execution_id"] = self.execution_id
            if self.task_status:
                execution_data["task_status"] = self.task_status
            if self.execution_summary:
                execution_data["execution_summary"] = self.execution_summary
            
            result["data"] = execution_data
        
        return result





@dataclass
class RealTimeStatusRequest(APIRequest):
    """实时综合状态查询请求"""
    script_id: str = ""
    include_logs: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "script_id": self.script_id,
            "include_logs": self.include_logs
        })
        return result


@dataclass
class RealTimeStatusResponse(APIResponse):
    """实时综合状态响应"""
    execution_status: Optional[Dict[str, Any]] = None
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    expected_results: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        
        if self.status == ResponseStatus.SUCCESS.value:
            realtime_data = {
                "execution_status": self.execution_status,
                "checkpoints": self.checkpoints,
                "expected_results": self.expected_results,
                "summary": self.summary
            }
            result["data"] = realtime_data
        
        return result


@dataclass
class FinalExecutionResultRequest(APIRequest):
    """最终执行结果查询请求"""
    script_id: str = ""
    include_details: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "script_id": self.script_id,
            "include_details": self.include_details
        })
        return result


@dataclass
class FinalExecutionResultResponse(APIResponse):
    """最终执行结果响应"""
    script_id: Optional[str] = None
    action_sequence: List[Dict[str, Any]] = field(default_factory=list)
    expected_results: List[Dict[str, Any]] = field(default_factory=list)
    execution_summary: Optional[Dict[str, Any]] = None
    check_cameral: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        
        if self.status == ResponseStatus.SUCCESS.value:
            result["data"] = {
                "script_id": self.script_id,
                "action_sequence": self.action_sequence,
                "expected_results": self.expected_results,
                "execution_summary": self.execution_summary,
                "check_cameral": self.check_cameral
            }
        
        return result


# 工具函数
def create_success_response(
    data: Any = None, 
    warnings: List[str] = None,
    metadata: Dict[str, Any] = None
) -> APIResponse:
    """创建成功响应"""
    return APIResponse(
        status=ResponseStatus.SUCCESS.value,
        data=data,
        warnings=warnings or [],
        metadata=metadata
    )


def create_error_response(
    error_code: ErrorCode,
    error_message: str,
    error_details: str = None,
    error_context: Dict[str, Any] = None,
    suggestions: List[str] = None
) -> APIResponse:
    """创建错误响应"""
    error_info = ErrorInfo(
        code=error_code.value,
        message=error_message,
        details=error_details,
        context=error_context,
        suggestions=suggestions or []
    )
    
    return APIResponse(
        status=ResponseStatus.ERROR.value,
        error=error_info.to_dict()
    )


def create_partial_response(
    data: Any,
    warnings: List[str],
    request_id: str = None,
    metadata: Dict[str, Any] = None
) -> APIResponse:
    """创建部分成功响应"""
    return APIResponse(
        status=ResponseStatus.PARTIAL.value,
        request_id=request_id,
        data=data,
        warnings=warnings,
        metadata=metadata
    )


# 数据验证函数
def validate_request_format(request_data: Dict[str, Any]) -> Optional[ErrorInfo]:
    """验证请求格式"""
    # 基础请求格式验证
    # 目前没有基础必需字段，所有验证都在具体的请求类型中进行
    
    return None


def validate_script_generation_request(request_data: Dict[str, Any]) -> Optional[ErrorInfo]:
    """验证脚本生成请求"""
    # 先验证基本格式
    base_error = validate_request_format(request_data)
    if base_error:
        return base_error
    
    # 验证脚本生成特有字段
    required_fields = ["script_id"]
    
    for field in required_fields:
        if field not in request_data:
            return ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER.value,
                message=f"脚本生成请求缺少必需参数: {field}",
                suggestions=["请确保包含script_id参数"]
            )
    
    # 验证action_sequence格式
    action_sequence = request_data.get("action_sequence", [])
    if not isinstance(action_sequence, list):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message="action_sequence必须是数组格式",
            suggestions=["请确保action_sequence是包含步骤对象的数组"]
        )
    
    # 验证action_sequence中的每个步骤
    for i, action in enumerate(action_sequence):
        if not isinstance(action, dict):
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"action_sequence[{i}]必须是对象格式",
                suggestions=["请确保每个步骤都是对象格式"]
            )
        
        # 验证步骤必需字段
        if "operation_type" not in action:
            return ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER.value,
                message=f"action_sequence[{i}]缺少必需字段: operation_type",
                suggestions=["请确保每个步骤都包含operation_type字段"]
            )
        
        # 验证控制流配置
        if "control_flow_config" in action:
            control_flow_error = validate_control_flow_config(action["control_flow_config"], f"action_sequence[{i}].control_flow_config")
            if control_flow_error:
                return control_flow_error
    
    # 验证expected_results格式（新的统一结构）
    expected_results = request_data.get("expected_results", {})
    if not isinstance(expected_results, dict):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message="expected_results必须是对象格式",
            suggestions=["请确保expected_results是对象格式，支持expression和conditions结构"]
        )
    
    # 验证每个预期结果组
    for task_id, result_group in expected_results.items():
        if not isinstance(result_group, dict):
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"expected_results[{task_id}]必须是对象格式",
                suggestions=["请确保每个预期结果组都是对象格式"]
            )
        
        # 验证条件表达式语法
        if "expression" in result_group:
            expression_error = validate_condition_expression_syntax(
                result_group["expression"], 
                f"expected_results[{task_id}].expression"
            )
            if expression_error:
                return expression_error
        
        # 验证ValidationModel列表
        if "conditions" in result_group:
            conditions_error = validate_validation_models(
                result_group["conditions"], 
                f"expected_results[{task_id}].conditions"
            )
            if conditions_error:
                return conditions_error
    
    return None


def validate_control_flow_config(control_flow: Dict[str, Any], path: str) -> Optional[ErrorInfo]:
    """验证控制流配置"""
    if not isinstance(control_flow, dict):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}必须是对象格式",
            suggestions=["请确保控制流配置是对象格式"]
        )
    
    control_type = control_flow.get("control_type")
    if not control_type:
        return ErrorInfo(
            code=ErrorCode.MISSING_PARAMETER.value,
            message=f"{path}缺少必需字段: control_type",
            suggestions=["请确保控制流配置包含control_type字段"]
        )
    
    valid_control_types = ["if_elseif_else", "for", "while"]
    if control_type not in valid_control_types:
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}.control_type必须是以下值之一: {', '.join(valid_control_types)}",
            suggestions=[f"请使用有效的控制流类型: {', '.join(valid_control_types)}"]
        )
    
    # 根据控制流类型验证特定字段
    if control_type == "if_elseif_else":
        if "branches" not in control_flow:
            return ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER.value,
                message=f"{path}缺少必需字段: branches",
                suggestions=["if_elseif_else控制流必须包含branches字段"]
            )
        
        branches = control_flow["branches"]
        if not isinstance(branches, list) or len(branches) == 0:
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.branches必须是非空数组",
                suggestions=["请确保branches是包含至少一个分支的数组"]
            )
        
        # 验证每个分支
        for i, branch in enumerate(branches):
            branch_error = validate_branch_config(branch, f"{path}.branches[{i}]")
            if branch_error:
                return branch_error
    
    elif control_type == "while":
        if "while_config" not in control_flow:
            return ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER.value,
                message=f"{path}缺少必需字段: while_config",
                suggestions=["while控制流必须包含while_config字段"]
            )
        
        while_config_error = validate_while_config(
            control_flow["while_config"], 
            f"{path}.while_config"
        )
        if while_config_error:
            return while_config_error
            
        # 🚫 验证while循环体内的步骤不能设置verify_after=true
        loop_body_error = validate_loop_body_no_verify_after(
            control_flow.get("loop_body", []),
            f"{path}.loop_body",
            "while"
        )
        if loop_body_error:
            return loop_body_error
    
    elif control_type == "for":
        if "for_config" not in control_flow:
            return ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER.value,
                message=f"{path}缺少必需字段: for_config",
                suggestions=["for控制流必须包含for_config字段"]
            )
        
        for_config_error = validate_for_config(
            control_flow["for_config"], 
            f"{path}.for_config"
        )
        if for_config_error:
            return for_config_error
            
        # 🚫 验证for循环体内的步骤不能设置verify_after=true
        loop_body_error = validate_loop_body_no_verify_after(
            control_flow.get("loop_body", []),
            f"{path}.loop_body",
            "for"
        )
        if loop_body_error:
            return loop_body_error
    
    return None


def validate_branch_config(branch: Dict[str, Any], path: str) -> Optional[ErrorInfo]:
    """验证分支配置"""
    if not isinstance(branch, dict):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}必须是对象格式",
            suggestions=["请确保分支配置是对象格式"]
        )
    
    # 验证条件表达式语法
    if "expression" in branch:
        expression_error = validate_condition_expression_syntax(
            branch["expression"], 
            f"{path}.expression"
        )
        if expression_error:
            return expression_error
    
    # 验证ValidationModel列表
    if "conditions" in branch:
        conditions_error = validate_validation_models(
            branch["conditions"], 
            f"{path}.conditions"
        )
        if conditions_error:
            return conditions_error
    
    # 验证步骤列表
    if "steps" in branch:
        steps = branch["steps"]
        if not isinstance(steps, list):
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.steps必须是数组格式",
                suggestions=["请确保steps是数组格式"]
            )
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                return ErrorInfo(
                    code=ErrorCode.INVALID_PARAMETER.value,
                    message=f"{path}.steps[{i}]必须是对象格式",
                    suggestions=["请确保每个步骤都是对象格式"]
                )
    
    return None


def validate_while_config(while_config: Dict[str, Any], path: str) -> Optional[ErrorInfo]:
    """验证while循环配置"""
    if not isinstance(while_config, dict):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}必须是对象格式",
            suggestions=["请确保while配置是对象格式"]
        )
    
    # 验证条件表达式语法
    if "expression" in while_config:
        expression_error = validate_condition_expression_syntax(
            while_config["expression"], 
            f"{path}.expression"
        )
        if expression_error:
            return expression_error
    
    # 验证ValidationModel列表
    if "conditions" in while_config:
        conditions_error = validate_validation_models(
            while_config["conditions"], 
            f"{path}.conditions"
        )
        if conditions_error:
            return conditions_error
    
    # 验证max_iterations（可选）
    if "max_iterations" in while_config:
        max_iterations = while_config["max_iterations"]
        if max_iterations is not None and (not isinstance(max_iterations, int) or max_iterations < 1):
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.max_iterations必须是大于0的整数或null",
                suggestions=["请确保max_iterations是大于0的整数或null（表示无限制）"]
            )
    
    return None


def validate_for_config(for_config: Dict[str, Any], path: str) -> Optional[ErrorInfo]:
    """验证for循环配置"""
    if not isinstance(for_config, dict):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}必须是对象格式",
            suggestions=["请确保for配置是对象格式"]
        )
    
    # 验证variable
    if "variable" in for_config:
        variable = for_config["variable"]
        valid_variables = ["count", "i", "item"]
        if variable not in valid_variables:
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.variable必须是以下值之一: {', '.join(valid_variables)}",
                suggestions=[f"请使用有效的变量名: {', '.join(valid_variables)}"]
            )
    
    # 验证count
    if "count" in for_config:
        count = for_config["count"]
        if not isinstance(count, int) or count < 1:
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.count必须是大于0的整数",
                suggestions=["请确保count是大于0的整数"]
            )
    
    return None


def validate_condition_expression_syntax(expression: str, path: str) -> Optional[ErrorInfo]:
    """验证条件表达式语法"""
    if not isinstance(expression, str):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}必须是字符串格式",
            suggestions=["请确保条件表达式是字符串格式"]
        )
    
    # 只验证是否为字符串，允许空字符串
    
    return None


def validate_validation_models(conditions: List[Dict[str, Any]], path: str) -> Optional[ErrorInfo]:
    """验证ValidationModel列表"""
    if not isinstance(conditions, list):
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}必须是数组格式",
            suggestions=["请确保conditions是数组格式"]
        )
    
    for i, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}[{i}]必须是对象格式",
                suggestions=["请确保每个条件都是对象格式"]
            )
        
        # 验证ValidationModel必需字段
        validation_error = validate_single_validation_model(
            condition, 
            f"{path}[{i}]"
        )
        if validation_error:
            return validation_error
    
    return None


def validate_single_validation_model(validation_model: Dict[str, Any], path: str) -> Optional[ErrorInfo]:
    """验证单个ValidationModel"""
    # 验证必需字段
    required_fields = ["validation_type", "data_source"]
    for field in required_fields:
        if field not in validation_model:
            return ErrorInfo(
                code=ErrorCode.MISSING_PARAMETER.value,
                message=f"{path}缺少必需字段: {field}",
                suggestions=[f"请确保包含{field}字段"]
            )
    
    # 验证validation_type
    validation_type = validation_model["validation_type"]
    valid_types = ["image", "text", "signal"]
    if validation_type not in valid_types:
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}.validation_type必须是以下值之一: {', '.join(valid_types)}",
            suggestions=[f"请使用有效的验证类型: {', '.join(valid_types)}"]
        )
    
    # 验证data_source
    data_source = validation_model["data_source"]
    valid_sources = ["adb_screenshot", "camera_photo", "file", "url", "can_signal"]
    if data_source not in valid_sources:
        return ErrorInfo(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=f"{path}.data_source必须是以下值之一: {', '.join(valid_sources)}",
            suggestions=[f"请使用有效的数据源: {', '.join(valid_sources)}"]
        )
    
    # 验证mode（可选）
    if "mode" in validation_model:
        mode = validation_model["mode"]
        valid_modes = ["agent", "manual"]
        if mode not in valid_modes:
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.mode必须是以下值之一: {', '.join(valid_modes)}",
                suggestions=[f"请使用有效的模式: {', '.join(valid_modes)}"]
            )
    
    # 验证expect_exists（可选）
    if "expect_exists" in validation_model:
        expect_exists = validation_model["expect_exists"]
        if not isinstance(expect_exists, bool):
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{path}.expect_exists必须是布尔值",
                suggestions=["请确保expect_exists是true或false"]
            )
    
    return None


def validate_loop_body_no_verify_after(loop_body: List[Dict[str, Any]], path: str, loop_type: str) -> Optional[ErrorInfo]:
    """
    验证循环体内的步骤不能设置verify_after=true
    
    Args:
        loop_body: 循环体步骤列表
        path: 路径用于错误信息
        loop_type: 循环类型 (while/for)
        
    Returns:
        Optional[ErrorInfo]: 如果验证失败返回错误信息
    """
    if not isinstance(loop_body, list):
        return None  # 不是列表则跳过验证
    
    for i, step in enumerate(loop_body):
        if not isinstance(step, dict):
            continue  # 不是字典则跳过
            
        verify_after = step.get("verify_after", False)
        if verify_after:
            step_name = step.get("step_name", f"步骤{i+1}")
            return ErrorInfo(
                code=ErrorCode.INVALID_PARAMETER.value,
                message=f"{loop_type}循环体内的步骤不允许设置verify_after=true",
                details=f"步骤 '{step_name}' ({path}[{i}]) 设置了verify_after=true，这在循环体内是不允许的",
                suggestions=[
                    "循环体内的步骤会被重复执行，不适合进行预期结果验证",
                    "请将verify_after设为false",
                    "如需验证，请在循环结束后的步骤中设置verify_after=true"
                ],
                context={
                    "field_path": f"{path}[{i}].verify_after",
                    "step_name": step_name,
                    "loop_type": loop_type
                }
            )
    
    return None


# 更新ScriptGenerationRequest以支持平铺结构（使用字典传输）  
@dataclass
class ScriptGenerationRequest(APIRequest):
    """脚本生成请求 - 平铺动作序列版本（使用字典传输）"""
    script_id: str = ""
    action_sequence: List[Dict[str, Any]] = field(default_factory=list)  # 使用字典传输
    expected_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # 使用字典传输，支持表达式
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        result.update({
            "script_id": self.script_id,
            "action_sequence": self.action_sequence,  # 已经是字典列表
            "expected_results": self.expected_results  # 已经是字典，支持表达式
        })
        return result   