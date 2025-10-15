#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新版脚本生成器 - 基于Jinja2模板引擎
支持模板化的动作处理和智能脚本生成
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from ..models.script_context import ScriptContext
from ..models.script_context import ActionStep
from ..utils.template_filters import register_custom_filters
from ..utils.template_functions import register_custom_functions
from ..core.control_flow_processor import control_flow_processor

def default_template_dir() -> str:
    return str(Path(__file__).resolve().parent.parent / "templates")

@dataclass
class ScriptGenerationConfig:
    """脚本生成配置"""
    template_dir: str = field(default_factory=default_template_dir)
    output_encoding: str = "utf-8"
    enable_autoescape: bool = True
    template_cache_size: int = 100
    strict_undefined: bool = True
    enable_async: bool = False


class ScriptGeneratorV2:
    """
    新版脚本生成器 - 基于Jinja2模板引擎
    
    特性：
    - 模板与逻辑分离
    - 动作类型分发
    - 智能脚本组装
    - 实时状态追踪集成
    - 预期结果验证支持
    """
    
    def __init__(self, config: Optional[ScriptGenerationConfig] = None):
        self.config = config or ScriptGenerationConfig()
        self.template_env = self._setup_template_environment()
        self.action_handlers = self._register_action_handlers()
        
    def _setup_template_environment(self) -> Environment:
        """设置Jinja2模板环境"""
        template_loader = FileSystemLoader(
            searchpath=self.config.template_dir,
            encoding=self.config.output_encoding
        )
        
        from jinja2 import StrictUndefined, Undefined

        env = Environment(
            loader=template_loader,
            autoescape=select_autoescape(['html', 'xml']) if self.config.enable_autoescape else False,
            cache_size=self.config.template_cache_size,
            undefined=StrictUndefined if self.config.strict_undefined else Undefined,
            enable_async=self.config.enable_async
        )
        
        # 注册自定义过滤器和函数
        register_custom_filters(env)
        register_custom_functions(env)
        
        return env
    
    def _register_action_handlers(self) -> Dict[str, str]:
        """注册动作处理器映射 - 基于operation_type，不依赖mode"""
        return {
            # 🎯 专用处理器 - 复杂操作，需要特殊逻辑
            'click': 'handlers/click_handler.j2',        # 点击操作 - 坐标定位、图像处理
            'tap': 'handlers/click_handler.j2',          # 点击操作别名
            'long_click': 'handlers/click_handler.j2',   # 长按操作
            'double_click': 'handlers/click_handler.j2', # 双击操作
            
            'type': 'handlers/type_handler.j2',          # 文本输入 - 文本验证
            'input': 'handlers/type_handler.j2',         # 输入操作别名
            
            'swipe': 'handlers/swipe_handler.j2',        # 滑动操作 - 轨迹识别
            'drag': 'handlers/swipe_handler.j2',         # 拖拽操作（复用滑动处理器）
            
            'scroll': 'handlers/scroll_handler.j2',      # 滚动操作 - 方向检测
            
            'can_send': 'handlers/can_handler.j2',       # CAN发送 - 信号处理
            
            'control_flow': 'handlers/control_flow_handler.j2',  # 控制流 - 条件判断
            
            # 🛠️ 特殊处理器
            'error': 'handlers/error_handler.j2',        # 错误处理器
            
            # 🔧 通用处理器 - 简单操作，标准流程即可
            'key': 'handlers/default_handler.j2',        # 按键操作
            'wait': 'handlers/default_handler.j2',       # 等待操作
            'app': 'handlers/default_handler.j2',        # 应用操作
            'start_app': 'handlers/default_handler.j2',  # 启动应用
            'stop_app': 'handlers/default_handler.j2',   # 停止应用
            'kill_all': 'handlers/default_handler.j2',   # 关闭所有应用
            
            # 📱 摄像头检测操作 - 使用default_handler
            'black_open': 'handlers/default_handler.j2',      # 黑屏检测开始
            'black_close': 'handlers/default_handler.j2',     # 黑屏检测结束
            'flower_open': 'handlers/default_handler.j2',     # 花屏检测开始
            'flower_close': 'handlers/default_handler.j2',    # 花屏检测结束
            'lag_open': 'handlers/default_handler.j2',        # 卡顿检测开始
            'lag_close': 'handlers/default_handler.j2',       # 卡顿检测结束
            'flash_open': 'handlers/default_handler.j2',      # 闪屏检测开始
            'flash_close': 'handlers/default_handler.j2',     # 闪屏检测结束
            
            # 🔧 其他操作 - 使用默认处理器
            'custom': 'handlers/default_handler.j2',     # 自定义操作
        }
    
    def generate_script(
        self, 
        script_context: ScriptContext,
        template_name: str = "main/script_base.j2"
    ) -> str:
        """
        生成完整的自动化脚本 - 支持新的平铺动作序列结构
        
        Args:
            script_context: 脚本上下文
            template_name: 主模板名称
            
        Returns:
            str: 生成的脚本内容
        """
        try:
            logger.info(f"开始生成脚本: {script_context.script_id}")
            
            # 🔄 重构：从处理 tasks 改为处理 action_sequence
            processed_actions = self._process_action_sequence(script_context.action_sequence)
            
            # 🔄 新增：添加验证步骤
            enhanced_actions = self._add_validation_steps(processed_actions, script_context)
            
            # 更新上下文
            script_context.action_sequence = enhanced_actions
            
            # 加载主模板
            main_template = self.template_env.get_template(template_name)
            
            # 渲染脚本
            script_content = main_template.render(
                context=script_context,
                timestamp=datetime.now().isoformat(),
                generator_version="2.1.0",  # 更新版本号
                **script_context.template_vars  # 传递额外的模板变量
            )
            
            logger.info(f"脚本生成完成: {script_context.script_id}")
            return script_content
            
        except Exception as e:
            logger.error(f"脚本生成失败: {e}")
            raise RuntimeError(f"脚本生成失败: {e}") from e
    
    def _process_action_sequence(self, actions: List[ActionStep]) -> List[ActionStep]:
        """
        处理动作序列 - 支持控制流步骤的递归处理
        
        Args:
            actions: 原始动作序列
            
        Returns:
            List[ActionStep]: 处理后的动作序列
        """
        processed_actions = []
        
        for i, action in enumerate(actions):
            try:
                # 设置步骤序号
                if not hasattr(action, 'step_number') or action.step_number is None:
                    action.step_number = i
                
                # 🔄 新增：检查是否为控制流步骤
                if action.step_type == "control_flow":
                    # 处理控制流步骤
                    control_flow_actions = control_flow_processor.process_control_flow(action)
                    processed_actions.extend(control_flow_actions)
                else:
                    # 处理普通动作步骤
                    processed_action = self._preprocess_single_action(action)
                    processed_actions.append(processed_action)
                
            except Exception as e:
                logger.error(f"处理动作 {i} 失败: {e}")
                # 创建错误处理的动作
                error_action = self._create_error_action(action, str(e))
                processed_actions.append(error_action)
        
        return processed_actions
    

    
    def _preprocess_single_action(self, action: ActionStep) -> ActionStep:
        """
        预处理单个动作步骤 - 基于operation_type选择处理器，不依赖mode
        
        Args:
            action: 动作步骤
            
        Returns:
            ActionStep: 处理后的动作步骤
        """
        # 🔄 重构：基于operation_type选择处理器，不依赖mode
        operation_type = action.operation_type.lower()
        handler_template = self.action_handlers.get(operation_type)
        
        if not handler_template:
            logger.warning(f"未找到操作类型 '{operation_type}' 的处理器，使用默认处理器")
            handler_template = 'handlers/default_handler.j2'
        
        action.template_name = handler_template
        
        # 验证必要字段
        self._validate_action_context(action)
        
        return action
    
    def _validate_action_context(self, action: ActionStep) -> None:
        """
        验证动作上下文的必要字段 - 基于operation_type和mode的组合验证
        
        Args:
            action: 动作上下文
            
        Raises:
            ValueError: 缺少必要字段时抛出
        """
        # 1. 基础字段验证
        required_fields = ['step_name', 'operation_type']
        for field in required_fields:
            if not hasattr(action, field) or getattr(action, field) is None:
                raise ValueError(f"动作上下文缺少必要字段: {field}")
        
        # 2. 验证element_info结构
        if not hasattr(action, 'element_info') or action.element_info is None:
            from ..models.script_context import ElementInfo
            action.element_info = ElementInfo()
        
        # 3. 验证检查点结构
        if not hasattr(action, 'checkpoint') or action.checkpoint is None:
            from ..models.checkpoint import CheckpointInfo
            action.checkpoint = CheckpointInfo()
        
        # 4. 操作特定验证（基于operation_type，不依赖mode）
        if action.operation_type == 'can_send':
            if not hasattr(action, 'can_configs') or action.can_configs is None:
                from ..models.can_models import CanConfigs
                action.can_configs = CanConfigs(
                    channel_id="CAN1",
                    frame_id="0x000",
                    signals=[],
                    duration=1000,
                    interval=100
                )
        
        # 5. 检查点相关验证（基于mode和operation_type的组合）
        if action.mode == 'agent':
            # agent模式：需要完整的检查点配置
            self._validate_agent_mode_config(action)
        elif action.mode == 'manual':
            # manual模式：根据操作类型决定检查点支持
            self._validate_manual_mode_config(action)
    
    def _validate_agent_mode_config(self, action: ActionStep) -> None:
        """验证agent模式的配置"""
        # agent模式通常需要更完整的配置
        # 具体验证逻辑可以根据需要扩展
        pass
    
    def _validate_manual_mode_config(self, action: ActionStep) -> None:
        """验证manual模式的配置"""
        # manual模式click动作的特殊验证
        if action.operation_type == 'click':
            element_info = action.element_info
            has_coordinates = element_info.start_x is not None and element_info.start_y is not None
            has_image_locating = (element_info.icon_path and 
                                element_info.bbox and 
                                len(element_info.bbox) >= 4)
            
            if not has_coordinates and not has_image_locating:
                raise ValueError("manual模式点击操作缺少坐标或图像定位信息")
    
    def _add_validation_steps(self, actions: List[ActionStep], script_context: ScriptContext) -> List[ActionStep]:
        """
        添加验证步骤 - 支持 verify_after 触发机制
        
        Args:
            actions: 原始动作序列
            script_context: 脚本上下文
            
        Returns:
            List[ActionStep]: 添加验证步骤后的动作序列
        """
        enhanced_actions = []
        
        for action in actions:
            # 添加原始动作
            enhanced_actions.append(action)
            
            # 🔄 verify_after 验证已改为在动作执行后立即进行，不再创建独立验证步骤
        
        return enhanced_actions
    
    # _create_validation_steps 方法已删除，verify_after 验证改为在动作执行后立即进行
    
    def _get_expected_results_for_task(self, task_id: str, script_context: ScriptContext) -> Dict[str, Any]:
        """
        按 source_task_id 查找对应的预期结果组（支持表达式和条件）
        
        Args:
            task_id: 任务ID
            script_context: 脚本上下文
            
        Returns:
            Dict[str, Any]: 预期结果组，包含expression和conditions
        """
        # 🔄 新增：从脚本上下文中查找预期结果组
        if hasattr(script_context, 'expected_results') and script_context.expected_results:
            expected_result_group = script_context.expected_results.get(task_id, {})
            
            # 确保返回的是字典格式
            if isinstance(expected_result_group, dict):
                return expected_result_group
            else:
                # 向后兼容：如果是列表格式，转换为新的字典格式
                logger.warning(f"任务 {task_id} 的预期结果格式已过时，自动转换为新格式")
                return {
                    "expression": None,
                    "conditions": expected_result_group if isinstance(expected_result_group, list) else []
                }
        
        # 如果没有找到，返回空字典
        logger.warning(f"未找到任务 {task_id} 的预期结果")
        return {}
    

    
    def _create_error_action(self, original_action: ActionStep, error_msg: str) -> ActionStep:
        """
        创建错误处理的动作
        
        Args:
            original_action: 原始动作
            error_msg: 错误信息
            
        Returns:
            ActionStep: 错误处理动作
        """
        from ..models.script_context import ElementInfo
        from ..models.checkpoint import CheckpointInfo
        
        error_checkpoint = CheckpointInfo(
            is_pass=False,
            detail=f"步骤预处理失败: {error_msg}",
            screenshot_path=''
        )
        
        error_action = ActionStep(
            id=getattr(original_action, 'id', 'error_step'),
            step_number=getattr(original_action, 'step_number', 0),
            step_name=f"错误处理: {getattr(original_action, 'step_name', '未知步骤')}",
            operation_type='error',
            element_info=ElementInfo(),
            checkpoint=error_checkpoint,
            mode='agent',
            template_name='handlers/error_handler.j2'
        )
        
        return error_action
    
    def generate_action_script(
        self, 
        action: ActionStep,
        context_vars: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成单个动作的脚本片段
        
        Args:
            action: 动作上下文
            context_vars: 额外的上下文变量
            
        Returns:
            str: 动作脚本片段
        """
        try:
            # 获取处理器模板（已在 _preprocess_actions 中设置）
            template_name = getattr(action, 'template_name', 'handlers/default_handler.j2')
            
            # 加载模板
            template = self.template_env.get_template(template_name)
            
            # 准备渲染上下文
            render_context = {
                'action': action,
                'operation_type': action.operation_type,
                **(context_vars or {})
            }
            
            # 渲染脚本片段
            script_fragment = template.render(**render_context)
            
            return script_fragment
            
        except Exception as e:
            logger.error(f"生成动作脚本失败: {e}")
            # 返回错误处理脚本
            return self._generate_error_script(action, str(e))
    
    def _generate_error_script(self, action: ActionStep, error_msg: str) -> str:
        """
        生成错误处理脚本
        
        Args:
            action: 动作上下文
            error_msg: 错误信息
            
        Returns:
            str: 错误处理脚本
        """
        return f'''
# 错误处理脚本 - 步骤: {action.step_name}
logging.error("步骤执行失败: {error_msg}")
step_context = {action.__dict__}
step_context['checkpoint']['is_pass'] = False
step_context['checkpoint']['detail'] = "脚本生成失败: {error_msg}"
'''
    

    
    def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        渲染指定模板
        
        Args:
            template_name: 模板名称
            context: 渲染上下文
            
        Returns:
            str: 渲染结果
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"模板渲染失败: {template_name}, 错误: {e}")
            raise
    
    def validate_template(self, template_name: str) -> bool:
        """
        验证模板是否存在且有效
        
        Args:
            template_name: 模板名称
            
        Returns:
            bool: 模板是否有效
        """
        try:
            self.template_env.get_template(template_name)
            return True
        except Exception as e:
            logger.warning(f"模板验证失败: {template_name}, 错误: {e}")
            return False
    
    def list_available_templates(self) -> List[str]:
        """
        列出所有可用的模板
        
        Returns:
            List[str]: 模板名称列表
        """
        try:
            return self.template_env.list_templates()
        except Exception as e:
            logger.error(f"列出模板失败: {e}")
            return []
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            Dict[str, Any]: 模板信息
        """
        try:
            template = self.template_env.get_template(template_name)
            source = self.template_env.loader.get_source(self.template_env, template_name)
            
            return {
                'name': template_name,
                'filename': source.filename,
                'uptodate': source.uptodate,
                'exists': True,
                'size': len(source.source) if source.source else 0
            }
        except Exception as e:
            return {
                'name': template_name,
                'exists': False,
                'error': str(e)
            }


# 向后兼容函数已删除 - 直接使用新的数据结构 