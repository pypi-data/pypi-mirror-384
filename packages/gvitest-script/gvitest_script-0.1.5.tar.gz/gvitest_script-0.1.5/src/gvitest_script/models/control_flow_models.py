"""
控制流数据模型

包含循环、条件分支等控制流相关的数据结构
用于支持if-elseif-else、for、while等控制流逻辑
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from loguru import logger

# 避免循环导入，使用TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .script_context import ActionStep
from .validation_model import ValidationModel, ExpectedResultGroup


@dataclass
class ConditionExpression:
    """
    条件表达式 - 支持validation_model组 + expression的格式
    
    结构：
    {
        "conditions": [ValidationModel1, ValidationModel2, ...],
        "expression": "([预期结果1] || [预期结果2]) && ([预期结果3])"
    }
    """
    conditions: List[ValidationModel] = None  # 验证模型列表
    expression: Optional[str] = None  # 条件表达式字符串
    
    def __post_init__(self):
        """初始化后处理"""
        if self.conditions is None:
            self.conditions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "conditions": [c.to_dict() for c in self.conditions]
        }
        
        if self.expression:
            result["expression"] = self.expression
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionExpression':
        """从字典创建ConditionExpression实例"""
        conditions = []
        if "conditions" in data and data["conditions"]:
            conditions = [ValidationModel.from_dict(c) for c in data["conditions"]]
        
        return cls(
            conditions=conditions,
            expression=data.get("expression")
        )


@dataclass
class ForConfig:
    """for循环配置 - 支持count和values两种方式"""
    variable: str = "count"  # 循环变量名：count, i, item
    count: Optional[int] = 0           # 循环次数（当使用count方式时）
    values: Optional[List[Any]] = field(default_factory=list)  # 值列表（当使用values方式时）
    
    def __post_init__(self):
        """验证配置"""
        # 简单验证：必须指定count或values其中之一
        has_count = self.count is not None and self.count > 0
        has_values = self.values and len(self.values) > 0
        
        if not has_count and not has_values:
            raise ValueError("必须指定count（大于0）或values（非空列表）")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "variable": self.variable,
            "count": self.count or 0,
            "values": self.values or []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForConfig':
        """从字典创建ForConfig实例"""
        return cls(
            variable=data.get("variable", "count"),
            count=data.get("count", 0),
            values=data.get("values", [])
        )


@dataclass
class WhileConfig:
    """while循环配置"""
    conditions: List[ValidationModel] = None  # 验证模型列表 (改为复数)
    expression: Optional[str] = None  # 条件表达式字符串
    max_iterations: Optional[int] = None  # 最大迭代次数（可选，None表示无限制）
    can_capture: Optional[Dict[str, Any]] = None  # CAN 采集配置
    
    def __post_init__(self):
        """初始化后处理"""
        if self.conditions is None:
            self.conditions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "conditions": [c.to_dict() for c in self.conditions],  # 改为复数
        }
        
        if self.expression:
            result["expression"] = self.expression
        if self.max_iterations is not None:
            result["max_iterations"] = self.max_iterations
        if self.can_capture:
            result["can_capture"] = self.can_capture
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WhileConfig':
        """从字典创建WhileConfig实例"""
        conditions = []
        if "conditions" in data and data["conditions"]:
            conditions = [ValidationModel.from_dict(c) for c in data["conditions"]]
        
        return cls(
            conditions=conditions,
            expression=data.get("expression"),
            max_iterations=data.get("max_iterations"),
            can_capture=data.get("can_capture")
        )


@dataclass
class Branch:
    """条件分支"""
    id: Optional[str] = None  # 分支ID
    branch_type: Optional[str] = None  # 分支类型：if, elseif, else
    conditions: List[ValidationModel] = None  # 验证模型列表
    expression: Optional[str] = None  # 条件表达式字符串
    steps: List['ActionStep'] = None
    can_capture: Optional[Dict[str, Any]] = None  # CAN 采集配置
    
    def __post_init__(self):
        """初始化后处理"""
        if self.conditions is None:
            self.conditions = []
        if self.steps is None:
            self.steps = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "conditions": [c.to_dict() for c in self.conditions],  
            "steps": [s.to_dict() for s in self.steps]
        }
        
        if self.id:
            result["id"] = self.id
        if self.branch_type:
            result["branch_type"] = self.branch_type
        if self.expression:
            result["expression"] = self.expression
        if self.can_capture:
            result["can_capture"] = self.can_capture
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Branch':
        """从字典创建Branch实例"""
        # 延迟导入避免循环依赖
        from .script_context import ActionStep
        
        conditions = []
        if "conditions" in data and data["conditions"]:
            conditions = [ValidationModel.from_dict(c) for c in data["conditions"]]
        
        steps = []
        if "steps" in data and data["steps"]:
            steps = [ActionStep.from_dict(s) for s in data["steps"]]
        
        return cls(
            id=data.get("id"),
            branch_type=data.get("branch_type"),
            conditions=conditions,
            expression=data.get("expression"),
            steps=steps,
            can_capture=data.get("can_capture")
        )


@dataclass
class ControlFlowConfig:
    """控制流配置"""
    control_type: str  # "if_elseif_else", "for", "while"
    
    # 条件字段（根据control_type使用）
    branches: Optional[List[Branch]] = None  # if_elseif_else
    while_config: Optional[WhileConfig] = None  # while
    for_config: Optional[ForConfig] = None  # for
    loop_body: Optional[List['ActionStep']] = None  # for/while
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {"control_type": self.control_type}
        
        if self.branches:
            result["branches"] = [b.to_dict() for b in self.branches]
        if self.while_config:
            result["while_config"] = self.while_config.to_dict()
        if self.for_config:
            result["for_config"] = self.for_config.to_dict()
        if self.loop_body:
            # 延迟导入避免循环依赖  
            from .script_context import ActionStep
            result["loop_body"] = [s.to_dict() for s in self.loop_body]
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ControlFlowConfig':
        """从字典创建ControlFlowConfig实例"""
        control_type = data["control_type"]
        
        result = cls(control_type=control_type)
        
        if "branches" in data and data["branches"]:
            result.branches = [Branch.from_dict(b) for b in data["branches"]]
        if "while_config" in data and data["while_config"]:
            result.while_config = WhileConfig.from_dict(data["while_config"])
        if "for_config" in data and data["for_config"]:
            result.for_config = ForConfig.from_dict(data["for_config"])
        if "loop_body" in data and data["loop_body"]:
            # 延迟导入避免循环依赖
            from .script_context import ActionStep
            result.loop_body = [ActionStep.from_dict(s) for s in data["loop_body"]]
            
        return result 