#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制流处理器 - 处理if/for/while等控制结构
支持控制流步骤的递归处理和循环变量替换
"""

from typing import Dict, List, Optional, Any
from loguru import logger

from ..models.script_context import ActionStep


class ControlFlowProcessor:
    """
    控制流处理器 - 专门处理控制流相关的逻辑
    
    功能：
    - 处理if条件分支逻辑
    - 处理for循环逻辑
    - 处理while循环逻辑
    - 支持循环变量替换
    - 支持条件表达式求值
    """
    
    def __init__(self):
        """初始化控制流处理器"""
        pass
    
    def process_control_flow(self, control_step: ActionStep) -> List[ActionStep]:
        """
        处理控制流步骤 - 支持if/for/while等控制结构
        
        Args:
            control_step: 控制流步骤
            
        Returns:
            List[ActionStep]: 处理后的动作序列
        """
        if not control_step.control_flow_config:
            logger.warning(f"控制流步骤 {control_step.step_name} 缺少控制流配置")
            return [control_step]
        
        control_type = control_step.control_flow_config.control_type
        logger.info(f"处理控制流: {control_type} - {control_step.step_name}")
        
        if control_type == "if_elseif_else":
            return self._process_if_elseif_else_control_flow(control_step)
        elif control_type == "for":
            return self._process_for_control_flow(control_step)
        elif control_type == "while":
            return self._process_while_control_flow(control_step)
        else:
            logger.warning(f"不支持的控制流类型: {control_type}")
            return [control_step]
    
    def _process_if_elseif_else_control_flow(self, control_step: ActionStep) -> List[ActionStep]:
        """
        处理if-elseif-else条件分支逻辑 - 保持控制流为整体控制流步骤
        
        Args:
            control_step: if_elseif_else控制流步骤
            
        Returns:
            List[ActionStep]: 处理后的动作序列 (返回原始的控制流步骤)
        """
        # 🔄 修改：if_elseif_else控制流应该作为一个整体的控制流步骤来处理
        # 不再分解成多个步骤，而是保持原样，让模板引擎在运行时处理条件逻辑
        
        # 为if_elseif_else控制流设置正确的模板
        control_step.template_name = "handlers/control_flow_handler.j2"
        
        # 🚫 确保分支内的步骤不会有verify_after验证
        if control_step.control_flow_config and control_step.control_flow_config.branches:
            for branch in control_step.control_flow_config.branches:
                if hasattr(branch, 'steps') and branch.steps:
                    for step in branch.steps:
                        if step.verify_after:
                            logger.warning(f"if_elseif_else分支内的步骤 {step.step_name} 不允许设置 verify_after=True，已自动设为False")
                            step.verify_after = False
        
        # 返回原始的if_elseif_else控制流步骤，不进行分解
        return [control_step]
    
    def _process_for_control_flow(self, control_step: ActionStep) -> List[ActionStep]:
        """
        处理for循环逻辑 - 保持for循环为整体控制流步骤
        
        Args:
            control_step: for控制流步骤
            
        Returns:
            List[ActionStep]: 处理后的动作序列 (返回原始的for控制流步骤)
        """
        # 🔄 修改：for循环应该作为一个整体的控制流步骤来处理
        # 不再分解成多个步骤，而是保持原样，让模板引擎在运行时处理循环逻辑
        
        # 为for循环设置正确的模板
        control_step.template_name = "handlers/control_flow_handler.j2"
        
        # 🚫 确保循环体内的步骤不会有verify_after验证
        if control_step.control_flow_config and control_step.control_flow_config.loop_body:
            for step in control_step.control_flow_config.loop_body:
                if step.verify_after:
                    logger.warning(f"for循环体内的步骤 {step.step_name} 不允许设置 verify_after=True，已自动设为False")
                    step.verify_after = False
        
        # 返回原始的for控制流步骤，不进行分解
        return [control_step]
    
    def _process_while_control_flow(self, control_step: ActionStep) -> List[ActionStep]:
        """
        处理while循环逻辑 - 保持while循环为整体控制流步骤
        
        Args:
            control_step: while控制流步骤
            
        Returns:
            List[ActionStep]: 处理后的动作序列 (返回原始的while控制流步骤)
        """
        # 🔄 修改：while循环应该作为一个整体的控制流步骤来处理
        # 不再分解成多个步骤，而是保持原样，让模板引擎在运行时处理循环逻辑
        
        # 为while循环设置正确的模板
        control_step.template_name = "handlers/control_flow_handler.j2"
        
        # 🚫 确保循环体内的步骤不会有verify_after验证
        if control_step.control_flow_config and control_step.control_flow_config.loop_body:
            for step in control_step.control_flow_config.loop_body:
                if step.verify_after:
                    logger.warning(f"while循环体内的步骤 {step.step_name} 不允许设置 verify_after=True，已自动设为False")
                    step.verify_after = False
        
        # 返回原始的while控制流步骤，不进行分解
        return [control_step]
    
    def _process_loop_body(self, steps: List[ActionStep], context_name: str) -> List[ActionStep]:
        """
        处理循环体中的步骤 - 支持循环变量的替换
        
        Args:
            steps: 循环体步骤列表
            context_name: 上下文名称
            
        Returns:
            List[ActionStep]: 处理后的动作序列
        """
        processed_actions = []
        
        for i, step in enumerate(steps):
            # 复制步骤以避免修改原始对象
            processed_step = self._copy_action_step(step)
            
            # 更新步骤名称以包含上下文
            processed_step.step_name = f"{context_name}_{processed_step.step_name}"
            
            # 🚫 循环体内的步骤不允许进行verify_after验证
            # 这是因为循环体会被重复执行，不适合进行预期结果验证
            if processed_step.verify_after:
                logger.warning(f"循环体内的步骤 {processed_step.step_name} 不允许设置 verify_after=True，已自动设为False")
                processed_step.verify_after = False
            
            # 🔄 TODO: 支持循环变量的替换（{{variable}}）
            # 预留开发空间，后续可以实现循环变量替换功能
            pass
            
            processed_actions.append(processed_step)
        
        return processed_actions
    
    def _copy_action_step(self, step: ActionStep) -> ActionStep:
        """
        复制动作步骤以避免修改原始对象
        
        Args:
            step: 原始动作步骤
            
        Returns:
            ActionStep: 复制的动作步骤
        """
        # 创建新的ActionStep实例，复制所有属性
        new_step = ActionStep(
            id=step.id,
            step_name=step.step_name,
            step_type=step.step_type,
            operation_type=step.operation_type,
            step_number=step.step_number,
            template_name=step.template_name,
            mode=step.mode,
            element_info=step.element_info,
            checkpoint=step.checkpoint,
            control_flow_config=step.control_flow_config,
            source_task_id=step.source_task_id,
            verify_after=step.verify_after
        )
        
        return new_step
    
    def _replace_loop_variables(self, text: str, context_name: str, index: int) -> str:
        """
        替换循环变量（{{variable}}）- 预留开发空间
        
        Args:
            text: 原始文本
            context_name: 上下文名称
            index: 循环索引
            
        Returns:
            str: 替换后的文本
        """
        # TODO: 实现循环变量替换功能
        # 可以支持 {{index}}, {{context}}, {{iteration}} 等变量
        # 当前返回原文本，预留开发空间
        return text
    
    def evaluate_condition_expression(self, condition_expr: str, context: Dict[str, Any]) -> bool:
        """
        调用条件表达式解析函数进行条件判断
        
        Args:
            condition_expr: 条件表达式
            context: 上下文变量
            
        Returns:
            bool: 条件判断结果
        """
        try:
            # 🔄 新增：调用验证工具中的条件表达式解析函数
            from src.utils.validation_utils import evaluate_condition_expression
            return evaluate_condition_expression(condition_expr, context)
        except ImportError:
            logger.warning("条件表达式解析函数未找到，使用简单字符串匹配")
            # 简单的字符串匹配作为后备方案
            return self._simple_condition_evaluation(condition_expr, context)
        except Exception as e:
            logger.error(f"条件表达式解析失败: {e}")
            return False
    
    def _simple_condition_evaluation(self, condition_expr: str, context: Dict[str, Any]) -> bool:
        """
        简单的条件表达式求值（后备方案）
        
        Args:
            condition_expr: 条件表达式
            context: 上下文变量
            
        Returns:
            bool: 条件判断结果
        """
        # 简单的字符串匹配逻辑
        if "&&" in condition_expr:
            parts = condition_expr.split("&&")
            return all(self._simple_condition_evaluation(part.strip(), context) for part in parts)
        elif "||" in condition_expr:
            parts = condition_expr.split("||")
            return any(self._simple_condition_evaluation(part.strip(), context) for part in parts)
        else:
            # 简单的变量存在性检查
            return condition_expr.strip() in context


# 全局实例
control_flow_processor = ControlFlowProcessor() 