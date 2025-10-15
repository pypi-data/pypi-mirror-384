"""
表达式工具函数
专门处理条件表达式的解析和评估

支持的功能：
- 条件表达式解析（支持 &&、||、() 运算符）
- 复杂逻辑表达式评估
- 嵌套括号处理
- 布尔字面量支持
"""

import re
import logging
from typing import List, Dict, Any, Union, Optional

logger = logging.getLogger(__name__)


def evaluate_condition_expression(condition: List[Dict[str, Any]], expression: str) -> bool:
    """
    评估条件表达式
    
    支持的条件表达式格式：
    - 简单条件: "[BAffi]"
    - AND逻辑: "[BAffi] && [8DAZR]"
    - OR逻辑: "[BAffi] || [8DAZR]"
    - 复杂组合: "([BAffi] || [8DAZR]) && [XY123]"
    - 嵌套括号: "(([BAffi] && [8DAZR]) || [XY123]) && [ABC12]"
    
    Args:
        condition: 条件列表，每个元素是一个ValidationModel
        expression: 条件表达式字符串，支持 &&、||、() 运算符
    
    Returns:
        bool: 条件是否满足
    """
    try:
        # 如果没有条件列表，直接返回True
        if not condition:
            return True
        
        # 如果没有表达式，默认所有条件都要满足（AND逻辑）
        if not expression or not expression.strip():
            return _evaluate_all_conditions(condition)
        
        # 解析并评估表达式
        return _evaluate_expression(condition, expression.strip())
        
    except Exception as e:
        logger.error(f"条件表达式评估异常: {e}")
        return False


def _evaluate_all_conditions(condition: List[Dict[str, Any]]) -> bool:
    """
    评估所有条件（AND逻辑）
    
    Args:
        condition: 条件列表
    
    Returns:
        bool: 所有条件是否都满足
    """
    try:
        # 导入验证函数，避免循环导入
        from .validation_utils import validate_validation_model
        
        for validation_model in condition:
            result = validate_validation_model(validation_model)
            if not result.get('is_pass', False):
                return False
        return True
    except Exception as e:
        logger.error(f"评估所有条件异常: {e}")
        return False


def _evaluate_expression(condition: List[Dict[str, Any]], expression: str) -> bool:
    """
    解析并评估条件表达式
    
    Args:
        condition: 条件列表
        expression: 条件表达式字符串
    
    Returns:
        bool: 表达式评估结果
    """
    # 创建条件映射表
    condition_map = _create_condition_map(condition)
    
    # 解析表达式
    return _parse_expression(expression, condition_map)


def _create_condition_map(condition: List[Dict[str, Any]]) -> Dict[str, bool]:
    """
    创建条件映射表，将条件列表转换为名称到结果的映射
    
    支持的条件类型：
    1. ValidationModel: 验证模型（预期结果验证或控制流条件判断）
    2. 简单条件: 包含 is_pass 字段的简单条件对象
    3. 布尔条件: 直接包含布尔值的条件对象
    
    映射策略：
    - 优先使用条件的 id 字段作为键
    - 如果没有 id，则使用默认的 condition1, condition2, ... 命名
    
    Args:
        condition: 条件列表，每个元素可能是ValidationModel或其他类型的条件
    
    Returns:
        Dict[str, bool]: 条件名称到验证结果的映射
    """
    condition_map = {}
    
    try:
        # 导入验证函数，避免循环导入
        from .validation_utils import validate_validation_model
        
        for i, condition_item in enumerate(condition):
            # 确定条件名称（优先级：id > 默认名称）
            condition_name = None
            if condition_item.get('id'):
                condition_name = condition_item['id']
            else:
                condition_name = f"condition{i+1}"
            
            # 判断条件类型并评估
            if _is_validation_model(condition_item):
                # ValidationModel类型：调用验证函数
                result = validate_validation_model(condition_item)
                condition_map[condition_name] = result.get('is_pass', False)
                    
            elif _is_simple_condition(condition_item):
                # 简单条件类型：直接获取is_pass字段
                condition_map[condition_name] = condition_item.get('is_pass', False)
                    
            elif _is_boolean_condition(condition_item):
                # 布尔条件类型：直接获取布尔值
                condition_map[condition_name] = condition_item.get('value', False)
                    
            else:
                # 未知类型：记录警告并默认为False
                logger.warning(f"未知的条件类型: {type(condition_item)}, 内容: {condition_item}")
                condition_map[condition_name] = False
        
        return condition_map
    except Exception as e:
        logger.error(f"创建条件映射表异常: {e}")
        return {}


def _is_validation_model(condition_item: Dict[str, Any]) -> bool:
    """
    判断是否为ValidationModel类型
    
    Args:
        condition_item: 条件项
    
    Returns:
        bool: 是否为ValidationModel
    """
    # 检查是否包含ValidationModel的特征字段
    validation_fields = ['data_source', 'validation_type', 'expect_exists', 'target_image_path', 'reference_image_path', 'target_text']
    return any(field in condition_item for field in validation_fields)


def _is_simple_condition(condition_item: Dict[str, Any]) -> bool:
    """
    判断是否为简单条件类型（包含is_pass字段）
    
    Args:
        condition_item: 条件项
    
    Returns:
        bool: 是否为简单条件
    """
    return 'is_pass' in condition_item


def _is_boolean_condition(condition_item: Dict[str, Any]) -> bool:
    """
    判断是否为布尔条件类型（包含value字段）
    
    Args:
        condition_item: 条件项
    
    Returns:
        bool: 是否为布尔条件
    """
    return 'value' in condition_item and isinstance(condition_item['value'], bool)


def _parse_expression(expression: str, condition_map: Dict[str, bool]) -> bool:
    """
    解析条件表达式
    
    支持的语法：
    - [BAffi]: 单个条件
    - [BAffi] && [8DAZR]: AND逻辑
    - [BAffi] || [8DAZR]: OR逻辑
    - ([BAffi] || [8DAZR]) && [XY123]: 复杂组合
    - true/false: 字面值
    
    Args:
        expression: 条件表达式字符串
        condition_map: 条件映射表
    
    Returns:
        bool: 表达式评估结果
    """
    try:
        # 预处理表达式，标准化空格
        expression = re.sub(r'\s+', ' ', expression.strip())
        
        # 处理特殊的字面值
        if expression.lower() == 'true':
            return True
        elif expression.lower() == 'false':
            return False
        
        # 处理括号
        while '(' in expression:
            expression = _evaluate_parentheses(expression, condition_map)
        
        # 处理AND和OR逻辑
        return _evaluate_logical_expression(expression, condition_map)
        
    except Exception as e:
        logger.error(f"表达式解析异常: {e}")
        return False


def _evaluate_parentheses(expression: str, condition_map: Dict[str, bool]) -> str:
    """
    处理括号内的表达式
    
    Args:
        expression: 包含括号的表达式
        condition_map: 条件映射表
    
    Returns:
        str: 处理后的表达式
    """
    # 找到最内层的括号
    start = expression.rfind('(')
    if start == -1:
        return expression
    
    end = expression.find(')', start)
    if end == -1:
        return expression
    
    # 提取括号内的表达式
    inner_expr = expression[start + 1:end]
    
    # 评估括号内的表达式
    inner_result = _evaluate_logical_expression(inner_expr, condition_map)
    
    # 替换括号内的表达式为结果
    result_str = "true" if inner_result else "false"
    new_expression = expression[:start] + result_str + expression[end + 1:]
    
    return new_expression


def _evaluate_logical_expression(expression: str, condition_map: Dict[str, bool]) -> bool:
    """
    评估逻辑表达式（AND/OR）
    
    Args:
        expression: 逻辑表达式
        condition_map: 条件映射表
    
    Returns:
        bool: 逻辑表达式结果
    """
    # 分割表达式为条件列表
    conditions = _split_expression(expression)
    
    if not conditions:
        return True
    
    # 如果只有一个条件
    if len(conditions) == 1:
        return _evaluate_single_condition(conditions[0]['condition'], condition_map)
    
    # 处理多个条件的逻辑组合
    result = _evaluate_single_condition(conditions[0]['condition'], condition_map)
    
    for i in range(1, len(conditions)):
        operator = conditions[i].get('operator')
        condition = conditions[i].get('condition')
        
        if operator == '&&':
            result = result and _evaluate_single_condition(condition, condition_map)
        elif operator == '||':
            result = result or _evaluate_single_condition(condition, condition_map)
    
    return result


def _split_expression(expression: str) -> List[Dict[str, str]]:
    """
    分割表达式为条件列表
    
    Args:
        expression: 逻辑表达式
    
    Returns:
        List[Dict[str, str]]: 条件列表，每个元素包含condition和operator
    """
    # 移除多余空格
    expression = expression.strip()
    
    # 分割AND和OR操作，支持操作符前后有无空格的情况
    parts = re.split(r'\s*(&&|\|\|)\s*', expression)
    
    conditions = []
    for i, part in enumerate(parts):
        if i == 0:
            # 第一个条件
            conditions.append({'condition': part.strip()})
        elif i % 2 == 1:
            # 操作符
            operator = part
            if i + 1 < len(parts):
                next_condition = parts[i + 1].strip()
                conditions.append({
                    'operator': operator,
                    'condition': next_condition
                })
    
    return conditions


def _evaluate_single_condition(condition: str, condition_map: Dict[str, bool]) -> bool:
    """
    评估单个条件
    
    支持的条件格式：
    - [id]: 方括号包围的条件ID，如 [BAffi]、[8DAZR]
    - true/false: 布尔字面量
    
    Args:
        condition: 单个条件字符串
        condition_map: 条件映射表
    
    Returns:
        bool: 条件评估结果
    """
    condition = condition.strip()
    
    # 处理布尔字面量（不区分大小写）
    if condition.lower() == 'true':
        return True
    elif condition.lower() == 'false':
        return False
    
    # 处理 [id] 格式的条件
    if condition.startswith('[') and condition.endswith(']'):
        # 提取方括号内的id
        condition_id = condition[1:-1]
        
        # 查找条件映射（优先查找不带方括号的ID）
        if condition_id in condition_map:
            return condition_map[condition_id]
        
        # 如果找不到，尝试查找带方括号的完整ID
        if condition in condition_map:
            return condition_map[condition]
        
        # 如果都找不到条件，返回False
        logger.warning(f"未找到条件ID '{condition_id}' 或 '{condition}'")
        return False
    
    # 兼容处理：直接查找条件映射（用于向后兼容）
    if condition in condition_map:
        return condition_map[condition]
    
    # 如果找不到条件，返回False
    logger.warning(f"未找到条件 '{condition}'")
    return False


def validate_expression_syntax(expression: str) -> Dict[str, Any]:
    """
    验证表达式语法是否正确
    
    Args:
        expression: 条件表达式字符串
    
    Returns:
        Dict[str, Any]: 验证结果
    """
    try:
        # 检查括号匹配
        if not _check_parentheses_balance(expression):
            return {
                "is_valid": False,
                "error": "括号不匹配",
                "expression": expression
            }
        
        # 检查操作符语法
        if not _check_operator_syntax(expression):
            return {
                "is_valid": False,
                "error": "操作符语法错误",
                "expression": expression
            }
        
        return {
            "is_valid": True,
            "expression": expression
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "error": f"语法验证异常: {e}",
            "expression": expression
        }


def _check_parentheses_balance(expression: str) -> bool:
    """
    检查括号是否匹配
    
    Args:
        expression: 表达式字符串
    
    Returns:
        bool: 括号是否匹配
    """
    stack = []
    
    for char in expression:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    
    return len(stack) == 0


def _check_operator_syntax(expression: str) -> bool:
    """
    检查操作符语法是否正确
    
    Args:
        expression: 表达式字符串
    
    Returns:
        bool: 操作符语法是否正确
    """
    # 检查连续操作符
    if re.search(r'(&&|\|\|)\s*(&&|\|\|)', expression):
        return False
    
    # 检查操作符在开头或结尾
    if re.match(r'^\s*(&&|\|\|)', expression) or re.search(r'(&&|\|\|)\s*$', expression):
        return False
    
    return True


def format_expression(expression: str) -> str:
    """
    格式化条件表达式，标准化空格和格式
    
    Args:
        expression: 原始表达式
    
    Returns:
        str: 格式化后的表达式
    """
    try:
        # 移除多余空格
        expression = re.sub(r'\s+', ' ', expression.strip())
        
        # 标准化操作符周围的空格
        expression = re.sub(r'\s*(&&|\|\|)\s*', r' \1 ', expression)
        
        # 标准化括号周围的空格
        expression = re.sub(r'\s*\(\s*', '(', expression)
        expression = re.sub(r'\s*\)\s*', ')', expression)
        
        # 修复括号后的操作符空格
        expression = re.sub(r'\)\s*(&&|\|\|)', r') \1', expression)
        
        # 移除开头和结尾的空格
        expression = expression.strip()
        
        return expression
        
    except Exception as e:
        logger.error(f"格式化表达式异常: {e}")
        return expression


def get_expression_variables(expression: str) -> List[str]:
    """
    提取表达式中的变量名
    
    支持 [id] 格式的条件引用，提取方括号内的 id
    
    Args:
        expression: 条件表达式字符串
    
    Returns:
        List[str]: 变量名列表（不包含方括号）
    """
    try:
        # 移除括号和操作符
        cleaned = re.sub(r'[()&|]', ' ', expression)
        
        # 分割并提取变量名
        variables = []
        for part in cleaned.split():
            part = part.strip()
            if part and part not in ['true', 'false', '&&', '||']:
                # 处理 [id] 格式
                if part.startswith('[') and part.endswith(']'):
                    # 提取方括号内的 id
                    variable_id = part[1:-1]
                    if variable_id:  # 确保不是空的方括号
                        variables.append(variable_id)
                else:
                    # 向后兼容：直接的变量名
                    variables.append(part)
        
        # 去重
        return list(set(variables))
        
    except Exception as e:
        logger.error(f"提取表达式变量异常: {e}")
        return [] 