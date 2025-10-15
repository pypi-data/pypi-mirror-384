"""
独立脚本生成服务
提供脚本生成、执行状态查询、验证等功能
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import time
import hashlib
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from ..models.api_models import (
    ErrorCode,
    ScriptGenerationRequest,
    ScriptExecutionRequest,
    validate_script_generation_request,
)
from ..core.error_handler import (
    init_error_handler,
)
from ..core.template_engine import TemplateEngine
from ..core.script_generator import ScriptGeneratorV2
from ..models.expected_result import (
    DataSource,
    ValidationType,
)
from ..models.script_context import (
    ExecutionConfig,
    ScriptContext,
    ElementInfo,
    ActionStep,
)
from ..models.checkpoint import CheckpointInfo
from ..models.validation_model import ValidationModel, ValidationMode
from .log_query import  create_log_query_service
from ..utils.file_server import init_file_server, get_file_server
from ..utils.logging_config import setup_cross_platform_logging
from .status_tracking import StatusTrackingService

root_dir = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_DIR = root_dir / "templates"


class Service:
    """独立脚本生成服务类"""

    def __init__(self, 
        workspace_root: Path,
        file_server_config: Optional[Dict[str, Any]] = None,
        log_level: str = "INFO",
        enable_file_server: bool = True,
        file_server_host: str = "localhost",
        file_server_port: int = 8080,
        ):
        self.workspace_root = workspace_root
        self.log_level = log_level
        self.enable_file_server = enable_file_server
        self.file_server_host = file_server_host
        self.file_server_port = file_server_port

        # 调用内部初始化方法
        self._initialize()
    
    def _init_logging(self):
        """初始化日志系统"""
        try:
            setup_cross_platform_logging(log_level=self.log_level)
        except Exception as e:
            logging.basicConfig(
                level=getattr(logging, self.log_level.upper(), logging.INFO),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _initialize(self):
        """内部初始化服务"""
        # 创建专用线程池解决并发文件I/O问题
        self.thread_pool = ThreadPoolExecutor(
            max_workers=20, thread_name_prefix="script_service"
        )
        # 设置为asyncio的默认线程池
        asyncio.get_event_loop().set_default_executor(self.thread_pool)

        # 初始化日志系统
        self._init_logging()
        
        # 初始化工作空间目录
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.error_handler = init_error_handler(self.workspace_root)
        self.execution_config = ExecutionConfig(self.workspace_root)

        self.template_engine = TemplateEngine([DEFAULT_TEMPLATE_DIR])

        # 初始化文件服务器
        self.file_server_config = None
        if self.enable_file_server:
            try:
                # 构建文件服务器URL
                base_url = f"http://{self.file_server_host}:{self.file_server_port}"
                init_file_server(base_url=base_url, workspace_root=self.workspace_root)
                
                # 获取文件服务器配置
                file_server = get_file_server()
                self.file_server_config = {
                    "base_url": file_server.get_base_url(),
                    "local_images_path": str(file_server.get_local_images_path()),
                }
            except Exception as e:
                logging.warning(f"文件服务器初始化失败: {e}")
                self.file_server_config = None
                self.enable_file_server = False

        # 初始化脚本生成器
        self.script_generator = ScriptGeneratorV2()

        # 初始化日志查询服务
        self.log_query_service = create_log_query_service(self.workspace_root)
        
        # 初始化状态跟踪服务
        self.status_tracking_service = StatusTrackingService(self.workspace_root)

        # 执行状态存储
        self.execution_status: Dict[str, Dict[str, Any]] = {}
        
        # 文件上传缓存：防止重复上传相同文件
        # 结构：{file_hash: {"url": server_url, "remote_filename": filename, "upload_time": timestamp}}
        self.upload_cache: Dict[str, Dict[str, Any]] = {}
        
        # 文件路径到URL的映射缓存：用于快速查找已上传文件
        # 结构：{local_path: server_url}
        self.path_to_url_cache: Dict[str, str] = {}
        
        logging.info(f"脚本生成服务已初始化，工作空间: {self.workspace_root}")
        return True
    
    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """计算文件的MD5哈希值，用于去重判断"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.warning(f"计算文件哈希失败 {file_path}: {e}")
            return None
    
    def _is_file_already_uploaded(self, file_path: Path) -> Optional[str]:
        """检查文件是否已经上传，返回服务器URL或None"""
        try:
            # 先检查路径缓存（最快）
            file_path_str = str(file_path)
            if file_path_str in self.path_to_url_cache:
                cached_url = self.path_to_url_cache[file_path_str]
                logging.debug(f"文件路径缓存命中: {file_path.name} -> {cached_url}")
                return cached_url
            
            # 检查文件是否存在
            if not file_path.exists():
                return None
            
            # 计算文件哈希并检查哈希缓存
            file_hash = self._calculate_file_hash(file_path)
            if file_hash and file_hash in self.upload_cache:
                cache_entry = self.upload_cache[file_hash]
                server_url = cache_entry["url"]
                
                # 更新路径缓存
                self.path_to_url_cache[file_path_str] = server_url
                
                logging.debug(f"文件哈希缓存命中: {file_path.name} (hash: {file_hash[:8]}...) -> {server_url}")
                return server_url
            
            return None
        except Exception as e:
            logging.warning(f"检查文件上传状态失败 {file_path}: {e}")
            return None
    
    def _cache_uploaded_file(self, file_path: Path, server_url: str, remote_filename: str):
        """缓存已上传的文件信息"""
        try:
            file_path_str = str(file_path)
            
            # 更新路径缓存
            self.path_to_url_cache[file_path_str] = server_url
            
            # 计算并缓存文件哈希
            file_hash = self._calculate_file_hash(file_path)
            if file_hash:
                self.upload_cache[file_hash] = {
                    "url": server_url,
                    "remote_filename": remote_filename,
                    "upload_time": datetime.now().isoformat(),
                    "local_path": file_path_str
                }
                logging.debug(f"缓存上传文件: {file_path.name} (hash: {file_hash[:8]}...) -> {server_url}")
        except Exception as e:
            logging.warning(f"缓存上传文件信息失败 {file_path}: {e}")
    
    def _clear_upload_cache_for_script(self, script_id: str):
        """清理指定脚本的上传缓存（重新生成脚本时调用）"""
        try:
            # 清理路径缓存中与该script_id相关的条目
            script_path_prefix = str(self.workspace_root / script_id)
            paths_to_remove = [path for path in self.path_to_url_cache.keys() 
                             if path.startswith(script_path_prefix)]
            
            for path in paths_to_remove:
                del self.path_to_url_cache[path]
            
            # 清理哈希缓存中与该script_id相关的条目
            hashes_to_remove = []
            for file_hash, cache_entry in self.upload_cache.items():
                local_path = cache_entry.get("local_path", "")
                if local_path.startswith(script_path_prefix):
                    hashes_to_remove.append(file_hash)
            
            for file_hash in hashes_to_remove:
                del self.upload_cache[file_hash]
            
            if paths_to_remove or hashes_to_remove:
                logging.info(f"已清理脚本 {script_id} 的上传缓存: {len(paths_to_remove)} 个路径缓存, {len(hashes_to_remove)} 个哈希缓存")
                
        except Exception as e:
            logging.warning(f"清理脚本上传缓存失败: {e}")
     
    async def generate_script(self, request_data: dict) -> Dict[str, Any]:
        """生成脚本"""
        try:
            # 验证请求格式
            validation_error = validate_script_generation_request(request_data)
            if validation_error:
                return {
                    "success": False,
                    "error": validation_error.message,
                    "details": validation_error.details,
                    "error_code": ErrorCode.INVALID_REQUEST.value
                }

            # 创建请求对象
            generation_request = ScriptGenerationRequest(
                script_id=request_data["script_id"],
                action_sequence=request_data.get("action_sequence", []),
                expected_results=request_data.get("expected_results", {})
            )

            # 在线程池中执行脚本生成（避免阻塞事件循环）
            script_url = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_script_sync, generation_request
            )

            return {
                "success": True,
                "script_url": script_url,
                "generation_info": {
                    "template_used": "main/script_base.j2",
                    "generation_time": datetime.now().isoformat(),
                    "action_count": len(generation_request.action_sequence),
                    "expected_result_count": len(generation_request.expected_results),
                    "control_flow_support": True,
                    "expression_support": True,
                    "validation_model_support": True,
                    "verify_after_support": True
                }
            }

        except Exception as e:
            logging.error(f"脚本生成异常: {e}")
            return {
                "success": False,
                "error": f"脚本生成失败: {str(e)}",
                "error_code": ErrorCode.SCRIPT_GENERATION_FAILED.value
            }

    async def execute_script(self, request_data: dict) -> Dict[str, Any]:
        """执行脚本"""
        try:
            # 创建执行请求对象
            execution_request = ScriptExecutionRequest(
                script_id=request_data["script_id"],
                execution_config=request_data.get("execution_config"),
                device_config=request_data.get("device_config"),
            )

            # 启动脚本执行
            execution_result = await self._execute_script_async(execution_request, None)
            return execution_result

        except Exception as e:
            logging.error(f"脚本执行异常: {e}")
            return {
                "success": False,
                "error": f"脚本执行失败: {str(e)}",
                "error_code": ErrorCode.ACTION_EXECUTION_FAILED.value
            }

    async def get_realtime_status(self, script_id: str, include_logs: bool = False) -> Dict[str, Any]:
        """获取实时状态"""
        try:
            result = await self._get_realtime_status_async(script_id, include_logs)
            
            if result["found"]:
                # 获取摄像头操作记录
                check_cameral = await asyncio.get_event_loop().run_in_executor(
                    None, self._read_camera_operations, script_id
                )
                
                result["check_cameral"] = check_cameral
                return result
            else:
                return {
                    "success": False,
                    "error": f"任务 {script_id} 的执行数据不存在",
                    "error_code": ErrorCode.INVALID_PARAMETER.value
                }

        except Exception as e:
            logging.error(f"获取实时状态异常: {e}")
            return {
                "success": False,
                "error": f"获取实时状态失败: {str(e)}",
                "error_code": ErrorCode.UNKNOWN_ERROR.value
            }

    async def get_final_execution_result(self, script_id: str, include_details: bool = True) -> Dict[str, Any]:
        """获取最终执行结果"""
        try:
            result = await self._get_final_execution_result_async(script_id, include_details)
            
            if result["found"]:
                # 获取摄像头操作记录
                check_cameral = await asyncio.get_event_loop().run_in_executor(
                    None, self._read_camera_operations, script_id
                )
                
                result["result_data"]["check_cameral"] = check_cameral
                return result
            else:
                return {
                    "success": False,
                    "error": f"任务 {script_id} 的执行结果数据不存在",
                    "error_code": ErrorCode.INVALID_PARAMETER.value
                }

        except Exception as e:
            logging.error(f"获取最终执行结果异常: {e}")
            return {
                "success": False,
                "error": f"获取最终执行结果失败: {str(e)}",
                "error_code": ErrorCode.INVALID_PARAMETER.value
            }

    async def get_task_logs(self, script_id: str) -> Dict[str, Any]:
        """获取任务的所有日志文件列表"""
        return await self.log_query_service.get_task_logs(script_id)
    
    async def get_latest_log(self, script_id: str, lines: Optional[int] = None, from_end: bool = True) -> Dict[str, Any]:
        """获取任务的最新日志内容"""
        return await self.log_query_service.get_latest_log(script_id, lines, from_end)
    
    async def get_specific_log(self, script_id: str, log_filename: str, lines: Optional[int] = None, from_end: bool = True) -> Dict[str, Any]:
        """获取指定日志文件的内容"""
        return await self.log_query_service.get_specific_log(script_id, log_filename, lines, from_end)

    def get_upload_cache_status(self) -> Dict[str, Any]:
        """获取文件上传缓存状态"""
        try:
            cache_stats = {
                "cache_size": {
                    "hash_cache_entries": len(self.upload_cache),
                    "path_cache_entries": len(self.path_to_url_cache)
                },
                "cache_details": {
                    "hash_cache_sample": dict(list(self.upload_cache.items())[:5]) if self.upload_cache else {},
                    "path_cache_sample": dict(list(self.path_to_url_cache.items())[:5]) if self.path_to_url_cache else {}
                },
                "memory_usage_estimate": {
                    "hash_cache_kb": len(str(self.upload_cache)) / 1024,
                    "path_cache_kb": len(str(self.path_to_url_cache)) / 1024
                }
            }
            return cache_stats
        except Exception as e:
            return {"error": f"获取缓存状态失败: {str(e)}"}
    

    def _generate_script_sync(self, request: ScriptGenerationRequest) -> str:
        """同步生成脚本（在线程池中执行）"""
        # 转换动作序列
        action_contexts = []
        for i, action in enumerate(request.action_sequence):
            # 转换element_info字典为ElementInfo对象
            element_info_data = action.get("element_info", {})
            element_info = (
                ElementInfo(
                    **{
                        k: v
                        for k, v in element_info_data.items()
                        if k in ElementInfo.__dataclass_fields__
                    }
                )
                if element_info_data
                else ElementInfo()
            )

            # 转换checkpoint字典为CheckpointInfo对象
            checkpoint_data = action.get('checkpoint', {})
            # 如果没有type字段，设置默认值为"none"
            if not checkpoint_data.get('type'):
                checkpoint_data = {'type': 'none', **checkpoint_data}
            checkpoint = CheckpointInfo(**checkpoint_data)

            # 转换控制流配置（如果存在）
            control_flow_config = None
            if 'control_flow_config' in action:
                from ..models.control_flow_models import ControlFlowConfig
                control_flow_config = ControlFlowConfig.from_dict(action['control_flow_config'])

            # 转换CAN配置（如果存在）
            can_configs = None
            if 'can_configs' in action:
                from ..models.can_models import CanConfigs
                can_configs = CanConfigs.from_dict(action['can_configs'])

            action_context = ActionStep(
                id=action.get('id', f"{request.script_id}_step_{i + 1}"),
                step_name=action.get('step_name', action.get('stepName', f'步骤{i + 1}')),
                step_type=action.get('step_type', 'action'),  # 新字段
                mode=action.get('mode', 'manual' if action.get('is_manual_add', False) else 'agent'),
                source_task_id=action.get('source_task_id', request.script_id),  # 新字段
                verify_after=action.get('verify_after', False),  # 新字段
                step_group_id=action.get('step_group_id', ''),
                step_number=action.get('step_number', action.get('stepNumber', i + 1)),
                screenshot_path=action.get('screenshot_path'),
                operation_type=action.get('operation_type', action.get('operationType', 'unknown')),
                element_info=element_info,
                checkpoint=checkpoint,
                control_flow_config=control_flow_config,  # 新增控制流支持
                can_configs=can_configs  # 新增CAN配置支持
            )
            action_contexts.append(action_context)

        # 预处理：下载所有远程图像到本地，替换路径
        action_contexts = self._preprocess_images_in_actions(action_contexts, request.script_id)
        
        # 处理新的expected_results结构（字典格式，支持表达式）
        processed_expected_results = self._preprocess_expected_results(request.expected_results, request.script_id)

        # 创建脚本上下文（使用本地路径）
        script_context = ScriptContext(
            script_id=request.script_id,
            action_sequence=action_contexts,
            expected_results=processed_expected_results,  # 直接使用处理后的字典
            execution_config=ExecutionConfig(workspace_root=str(self.workspace_root))
        )

        # 生成脚本内容（不再传递文件服务器配置）
        script_content = self.script_generator.generate_script(script_context)

        # 保存脚本文件
        script_dir = self.workspace_root / request.script_id / "coder"
        script_dir.mkdir(parents=True, exist_ok=True)

        # 清理旧的摄像头操作记录（重新生成脚本时重置）
        self._cleanup_camera_operations(request.script_id)

        # 清理旧的执行结果文件（重新生成脚本时重置）
        self._cleanup_execution_results(request.script_id)
        
        # 清理上传缓存（重新生成脚本时重置）
        self._clear_upload_cache_for_script(request.script_id)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        script_filename = f"script_{timestamp}.py"
        script_path = script_dir / script_filename

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        # 保存脚本配置文件，包含action_sequence，用作备用数据源
        script_config = {
            "script_id": request.script_id,
            "action_sequence": request.action_sequence,
            "expected_results": request.expected_results,
            "generation_time": datetime.now().isoformat(),
            "script_filename": script_filename,
        }

        script_config_path = script_dir / "script_config.json"
        with open(script_config_path, "w", encoding="utf-8") as f:
            json.dump(script_config, f, ensure_ascii=False, indent=2, default=str)

        # 返回脚本URL路径
        return f"/{request.script_id}/coder/{script_filename}"
    
    def _preprocess_images_in_actions(self, action_contexts: List, script_id: str) -> List:
        """预处理动作序列中的图像，下载远程图像到本地"""
        if not self.file_server_config:
            logging.info("文件服务器未配置，跳过图像预处理")
            return action_contexts

        processed_actions = []

        for action in action_contexts:
            processed_action = action

            try:
                # 处理步骤截图路径
                if hasattr(action, 'screenshot_path') and action.screenshot_path:
                    local_path = self._download_image_to_local(action.screenshot_path, script_id, "step_screenshots")
                    if local_path:
                        processed_action.screenshot_path = local_path

                # 处理元素图标路径
                if hasattr(action, 'element_info') and action.element_info and hasattr(action.element_info, 'icon_path') and action.element_info.icon_path:
                    local_path = self._download_image_to_local(action.element_info.icon_path, script_id, "element_icons")
                    if local_path:
                        processed_action.element_info.icon_path = local_path
                
                # 处理检查点期望数据（新格式）
                if hasattr(action, 'checkpoint') and action.checkpoint:
                    checkpoint = action.checkpoint
                    # 如果是图像类型的检查点，且expected字段包含图像路径
                    if (checkpoint.type == "image" and checkpoint.expected and 
                        (checkpoint.expected.startswith("http://") or checkpoint.expected.startswith("https://"))):
                        local_path = self._download_image_to_local(checkpoint.expected, script_id, "checkpoint_images")
                        if local_path:
                            processed_action.checkpoint.expected = local_path
                
                # 处理控制流配置中的条件判断图像路径
                if hasattr(action, 'control_flow_config') and action.control_flow_config:
                    control_flow_config = action.control_flow_config
                    # 统一处理字典类型和对象类型
                    control_type = None
                    
                    # 获取控制流类型
                    if isinstance(control_flow_config, dict):
                        control_type = control_flow_config.get('control_type')
                    else:
                        control_type = control_flow_config.control_type if hasattr(control_flow_config, 'control_type') else None
                    
                    # 处理if-elseif-else类型
                    if control_type == 'if_elseif_else':
                        # 处理分支
                        branches = []
                        if isinstance(control_flow_config, dict) and 'branches' in control_flow_config:
                            branches = control_flow_config['branches']
                        elif hasattr(control_flow_config, 'branches') and control_flow_config.branches:
                            branches = control_flow_config.branches
                        
                        # 遍历分支
                        for branch in branches:
                            # 获取条件
                            conditions = []
                            if isinstance(branch, dict) and 'conditions' in branch and isinstance(branch['conditions'], list):
                                conditions = branch['conditions']
                            elif hasattr(branch, 'conditions') and branch.conditions:
                                conditions = branch.conditions
                            
                            # 处理条件中的图像路径
                            for condition in conditions:
                                # 处理target_image_path
                                target_path = None
                                if isinstance(condition, dict) and 'target_image_path' in condition:
                                    target_path = condition['target_image_path']
                                elif hasattr(condition, 'target_image_path'):
                                    target_path = condition.target_image_path
                                
                                if target_path:
                                    local_path = self._download_image_to_local(target_path, script_id, "condition_targets")
                                    if local_path:
                                        if isinstance(condition, dict):
                                            condition['target_image_path'] = local_path
                                        else:
                                            condition.target_image_path = local_path
                                
                                # 处理reference_image_path
                                ref_path = None
                                if isinstance(condition, dict) and 'reference_image_path' in condition:
                                    ref_path = condition['reference_image_path']
                                elif hasattr(condition, 'reference_image_path'):
                                    ref_path = condition.reference_image_path
                                
                                if ref_path:
                                    local_path = self._download_image_to_local(ref_path, script_id, "condition_references")
                                    if local_path:
                                        if isinstance(condition, dict):
                                            condition['reference_image_path'] = local_path
                                        else:
                                            condition.reference_image_path = local_path
                    
                    # 处理while类型
                    elif control_type == 'while':
                        # 获取while配置
                        while_config = None
                        if isinstance(control_flow_config, dict) and 'while_config' in control_flow_config:
                            while_config = control_flow_config.get('while_config', {})
                        elif hasattr(control_flow_config, 'while_config') and control_flow_config.while_config:
                            while_config = control_flow_config.while_config
                        
                        # 获取条件
                        conditions = []
                        if isinstance(while_config, dict) and 'conditions' in while_config and isinstance(while_config['conditions'], list):
                            conditions = while_config['conditions']
                        elif hasattr(while_config, 'conditions') and while_config.conditions:
                            conditions = while_config.conditions
                        
                        # 处理条件中的图像路径
                        for condition in conditions:
                            # 处理target_image_path
                            target_path = None
                            if isinstance(condition, dict) and 'target_image_path' in condition:
                                target_path = condition['target_image_path']
                            elif hasattr(condition, 'target_image_path'):
                                target_path = condition.target_image_path
                            
                            if target_path:
                                local_path = self._download_image_to_local(target_path, script_id, "condition_targets")
                                if local_path:
                                    if isinstance(condition, dict):
                                        condition['target_image_path'] = local_path
                                    else:
                                        condition.target_image_path = local_path
                            
                            # 处理reference_image_path
                            ref_path = None
                            if isinstance(condition, dict) and 'reference_image_path' in condition:
                                ref_path = condition['reference_image_path']
                            elif hasattr(condition, 'reference_image_path'):
                                ref_path = condition.reference_image_path
                            
                            if ref_path:
                                local_path = self._download_image_to_local(ref_path, script_id, "condition_references")
                                if local_path:
                                    if isinstance(condition, dict):
                                        condition['reference_image_path'] = local_path
                                    else:
                                        condition.reference_image_path = local_path
                    
                    # 处理for类型
                    elif control_type == 'for':
                        # 获取for配置
                        for_config = None
                        if isinstance(control_flow_config, dict) and 'for_config' in control_flow_config:
                            for_config = control_flow_config.get('for_config', {})
                        elif hasattr(control_flow_config, 'for_config') and control_flow_config.for_config:
                            for_config = control_flow_config.for_config
                        
                        # 获取条件
                        conditions = []
                        if isinstance(for_config, dict) and 'conditions' in for_config and isinstance(for_config['conditions'], list):
                            conditions = for_config['conditions']
                        elif hasattr(for_config, 'conditions') and for_config.conditions:
                            conditions = for_config.conditions
                        
                        # 处理条件中的图像路径
                        for condition in conditions:
                            # 处理target_image_path
                            target_path = None
                            if isinstance(condition, dict) and 'target_image_path' in condition:
                                target_path = condition['target_image_path']
                            elif hasattr(condition, 'target_image_path'):
                                target_path = condition.target_image_path
                            
                            if target_path:
                                local_path = self._download_image_to_local(target_path, script_id, "condition_targets")
                                if local_path:
                                    if isinstance(condition, dict):
                                        condition['target_image_path'] = local_path
                                    else:
                                        condition.target_image_path = local_path
                            
                            # 处理reference_image_path
                            ref_path = None
                            if isinstance(condition, dict) and 'reference_image_path' in condition:
                                ref_path = condition['reference_image_path']
                            elif hasattr(condition, 'reference_image_path'):
                                ref_path = condition.reference_image_path
                            
                            if ref_path:
                                local_path = self._download_image_to_local(ref_path, script_id, "condition_references")
                                if local_path:
                                    if isinstance(condition, dict):
                                        condition['reference_image_path'] = local_path
                                    else:
                                        condition.reference_image_path = local_path
                        
            except Exception as e:
                logging.warning(f"处理动作 {action.step_number} 的图像时出错: {e}")

            processed_actions.append(processed_action)

        return processed_actions
    

    def _preprocess_expected_results(self, expected_results: Dict[str, Dict[str, Any]], script_id: str) -> Dict[str, Dict[str, Any]]:
        """预处理新的expected_results结构（字典格式，支持表达式）"""
        if not self.file_server_config:
            logging.info("文件服务器未配置，跳过预期结果图像预处理")
            return expected_results
        
        processed_results = {}
        
        for task_id_key, result_group in expected_results.items():
            if isinstance(result_group, dict):
                processed_group = result_group.copy()
                
                # 处理conditions列表中的ValidationModel
                if 'conditions' in processed_group and isinstance(processed_group['conditions'], list):
                    processed_conditions = []
                    for condition in processed_group['conditions']:
                        if isinstance(condition, dict):
                            processed_condition = condition.copy()
                            
                            try:
                                # 处理target_image_path
                                if processed_condition.get('target_image_path'):
                                    local_path = self._download_image_to_local(processed_condition['target_image_path'], script_id, "expected_targets")
                                    if local_path:
                                        processed_condition['target_image_path'] = local_path
                                
                                # 处理reference_image_path
                                if processed_condition.get('reference_image_path'):
                                    local_path = self._download_image_to_local(processed_condition['reference_image_path'], script_id, "expected_references")
                                    if local_path:
                                        processed_condition['reference_image_path'] = local_path
                                        
                            except Exception as e:
                                logging.warning(f"处理预期结果条件 {condition.get('id', 'unknown')} 的图像时出错: {e}")
                            
                            processed_conditions.append(processed_condition)
                        else:
                            processed_conditions.append(condition)
                    
                    processed_group['conditions'] = processed_conditions
                
                processed_results[task_id_key] = processed_group
            else:
                processed_results[task_id_key] = result_group
        
        return processed_results
    
    def _download_image_to_local(self, remote_path: str, script_id: str, category: str) -> Optional[str]:
        """下载远程图像到本地目录"""
        try:
            # 判断是否是远程路径（简单检查是否以http开头或者是文件服务器路径格式）
            if not (
                remote_path.startswith("http")
                or remote_path.startswith("/static/")
                or remote_path.startswith("/api/files/")
            ):
                # 已经是本地路径，直接返回
                return remote_path

            file_server = get_file_server()

            # 创建本地目录结构
            local_images_dir = self.workspace_root / script_id / "images" / category
            local_images_dir.mkdir(parents=True, exist_ok=True)

            # 生成本地文件名
            import os

            filename = os.path.basename(remote_path)
            if not filename:
                filename = f"image_{int(time.time())}.png"

            local_file_path = local_images_dir / filename
            
            # 检查文件是否已存在（避免重复下载）
            if local_file_path.exists():
                logging.debug(f"图像已存在，跳过下载: {remote_path} -> {local_file_path}")
                return str(local_file_path)
            
            # 下载文件
            if file_server.download_file(remote_path, str(local_file_path)):
                logging.info(f"图像下载成功: {remote_path} -> {local_file_path}")
                return str(local_file_path)
            else:
                logging.warning(f"图像下载失败: {remote_path}")
                return remote_path  # 下载失败时返回原路径

        except Exception as e:
            logging.error(f"下载图像异常: {remote_path}, 错误: {e}")
            return remote_path  # 异常时返回原路径
    
    async def _upload_execution_results(self, script_id: str):
        """上传脚本执行结果中的图像文件到文件服务器，智能分类不同类型的图像"""
        if not self.file_server_config:
            logging.info("文件服务器未配置，跳过结果上传")
            return

        try:
            from ..utils.file_server import get_file_server

            file_server = get_file_server()

            # 定义需要搜索的目录
            task_dir = self.workspace_root / script_id
            search_directories = ["runner", "images"]

            uploaded_files = []

            for local_dir in search_directories:
                local_path = task_dir / local_dir
                if not local_path.exists():
                    continue

                # 查找所有图像文件
                image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"]
                for extension in image_extensions:
                    for image_file in local_path.rglob(extension):
                        try:
                            # 检查文件是否已上传（使用缓存去重）
                            cached_url = self._is_file_already_uploaded(image_file)
                            if cached_url:
                                # 智能分类图像文件
                                category = self._classify_image_file(image_file.name)
                                
                                # 生成远程文件名（保持一致性）
                                relative_path = image_file.relative_to(local_path)
                                remote_filename = f"{script_id}_{category}_{relative_path.name}"
                                
                                uploaded_files.append({
                                    "local_path": str(image_file),
                                    "remote_filename": remote_filename,
                                    "category": category,
                                    "file_type": self._get_file_type_description(category),
                                    "from_cache": True  # 标记为从缓存获取
                                })
                                logging.debug(f"结果文件使用缓存 [{category}]: {image_file.name} -> {cached_url}")
                                continue
                            
                            # 智能分类图像文件
                            category = self._classify_image_file(image_file.name)

                            # 生成远程文件名
                            relative_path = image_file.relative_to(local_path)
                            remote_filename = f"{script_id}_{category}_{relative_path.name}"
                            
                            # 上传文件并获取URL
                            server_url = file_server.upload_file(str(image_file), remote_filename)
                            if server_url:
                                # 缓存上传结果
                                self._cache_uploaded_file(image_file, server_url, remote_filename)
                                
                                uploaded_files.append({
                                    "local_path": str(image_file),
                                    "remote_filename": remote_filename,
                                    "category": category,
                                    "file_type": self._get_file_type_description(category),
                                    "from_cache": False  # 标记为新上传
                                })
                                logging.info(f"结果文件上传成功 [{category}]: {image_file.name} -> {remote_filename}")
                            else:
                                logging.warning(f"结果文件上传失败: {image_file}")

                        except Exception as e:
                            logging.error(f"上传单个文件失败 {image_file}: {e}")

            # 保存上传记录，按类别统计
            if uploaded_files:
                # 按类别统计
                category_stats = {}
                for file_info in uploaded_files:
                    category = file_info["category"]
                    if category not in category_stats:
                        category_stats[category] = {
                            "count": 0,
                            "files": [],
                            "description": file_info["file_type"],
                        }
                    category_stats[category]["count"] += 1
                    category_stats[category]["files"].append(
                        file_info["remote_filename"]
                    )

                upload_record_file = task_dir / "upload_record.json"
                # 计算缓存统计
                cached_count = sum(1 for f in uploaded_files if f.get("from_cache", False))
                new_upload_count = len(uploaded_files) - cached_count
                
                upload_record = {
                    "script_id": script_id,
                    "upload_time": datetime.now().isoformat(),
                    "uploaded_files": uploaded_files,
                    "category_statistics": category_stats,
                    "total_count": len(uploaded_files),
                    "cache_statistics": {
                        "total_files": len(uploaded_files),
                        "new_uploads": new_upload_count,
                        "cached_files": cached_count,
                        "cache_hit_rate": round(cached_count / len(uploaded_files) * 100, 2) if uploaded_files else 0
                    }
                }

                with open(upload_record_file, "w", encoding="utf-8") as f:
                    json.dump(
                        upload_record, f, ensure_ascii=False, indent=2, default=str
                    )

                # 输出详细的上传统计
                logging.info(f"任务 {script_id} 结果上传完成，共处理 {len(uploaded_files)} 个文件（新上传: {new_upload_count}, 缓存复用: {cached_count}）：")
                for category, stats in category_stats.items():
                    logging.info(f"  {stats['description']}: {stats['count']} 个文件")
            else:
                logging.info(f"任务 {script_id} 没有发现需要上传的图像文件")
            
        except Exception as e:
            logging.error(f"上传执行结果异常: {e}")

    def _classify_image_file(self, filename: str) -> str:
        """根据文件名智能分类图像文件"""
        filename_lower = filename.lower()

        # 摄像头相关截图
        if any(
            pattern in filename_lower
            for pattern in [
                "camera_capture_",
                "validation_manual_camera_",
                "camera_photo",
            ]
        ):
            return "camera_captures"

        # 预期结果验证截图
        elif any(
            pattern in filename_lower
            for pattern in [
                "validation_agent_",
                "validation_manual_adb_",
                "validation_",
            ]
        ):
            return "validation_screenshots"

        # 执行过程截图（包含前后截图）
        elif any(
            pattern in filename_lower
            for pattern in [
                "screenshot_",
                "step_",
                "error_",
                "after_",
                "before_",
                "manual_",
            ]
        ):
            return "execution_screenshots"

        # 其他图像文件
        else:
            return "execution_images"

    def _get_file_type_description(self, category: str) -> str:
        """获取文件类型的中文描述"""
        descriptions = {
            "camera_captures": "摄像头截图",
            "validation_screenshots": "验证截图",
            "execution_screenshots": "执行截图",
            "execution_images": "其他图像",
        }
        return descriptions.get(category, "未知类型")
    
    async def _get_execution_status_async(self, script_id: str, include_details: bool) -> Dict[str, Any]:
        """异步获取执行状态"""
        try:
            # 检查状态文件（优先从runner目录查找）
            status_file = self.workspace_root / script_id / "runner" / "task_status.json"
            if not status_file.exists():
                # 备用路径：根目录下的task_status.json
                status_file = self.workspace_root / script_id / "task_status.json"
            
            if not status_file.exists():
                return {"found": False}

            # 使用重试机制读取JSON文件，避免并发访问问题
            status_data = await self._read_json_file_with_retry(status_file)

            result = {
                "found": True,
                "task_status": status_data.get("status", "unknown"),
                "current_step": status_data.get("current_step"),
                "total_steps": status_data.get("total_steps"),
                "progress_percentage": status_data.get("progress_percentage", 0.0),
            }

            if include_details:
                # 获取步骤详情
                step_details = []
                action_sequence = status_data.get("action_sequence", [])
                for step in action_sequence:
                    # 创建步骤详情，排除重复的截图字段
                    step_detail = {}
                    for key, value in step.items():
                        # 排除根级别的截图路径字段，因为已经有execution_result.screenshots了
                        if key not in [
                            "before_execution_screenshot_path",
                            "after_execution_screenshot_path",
                        ]:
                            step_detail[key] = value

                    # 转换checkpoint中的screenshot_path为文件服务器路径
                    if (
                        "checkpoint" in step_detail
                        and "screenshot_path" in step_detail["checkpoint"]
                    ):
                        step_detail["checkpoint"]["screenshot_path"] = (
                            self._convert_local_path_to_server_path(
                                step_detail["checkpoint"]["screenshot_path"]
                            )
                        )

                    # 转换execution_result中的截图路径为文件服务器路径
                    if (
                        "execution_result" in step_detail
                        and "screenshots" in step_detail["execution_result"]
                    ):
                        screenshots = step_detail["execution_result"]["screenshots"]
                        if (
                            "before_execution" in screenshots
                            and screenshots["before_execution"]
                        ):
                            screenshots["before_execution"] = (
                                self._convert_local_path_to_server_path(
                                    screenshots["before_execution"]
                                )
                            )
                        if (
                            "after_execution" in screenshots
                            and screenshots["after_execution"]
                        ):
                            screenshots["after_execution"] = (
                                self._convert_local_path_to_server_path(
                                    screenshots["after_execution"]
                                )
                            )

                    step_details.append(step_detail)

                result["step_details"] = step_details
                result["execution_summary"] = {
                    "start_time": status_data.get("start_time"),
                    "end_time": status_data.get("end_time"),
                    "total_duration": status_data.get("total_duration"),
                    "successful_steps": status_data.get("successful_steps", 0),
                    "passed_checkpoints": status_data.get("passed_checkpoints", 0),
                    "execution_id": status_data.get("execution_id"),
                }

            return result

        except Exception as e:
            logging.error(f"获取执行状态异常: {e}")
            raise


    async def _execute_script_async(
        self, request: ScriptExecutionRequest, background_tasks=None
    ) -> Dict[str, Any]:
        """异步执行脚本"""
        try:
            # 根据script_id查找最新的脚本文件
            script_path = self._find_latest_script(request.script_id)
            if not script_path:
                return {
                    "success": False,
                    "error": f"未找到任务 {request.script_id} 的脚本文件",
                    "details": "请先生成脚本后再执行"
                }

            # 生成执行ID
            import uuid

            execution_id = str(uuid.uuid4())

            # 清理旧的执行结果文件，确保本次执行从干净状态开始
            self._cleanup_execution_results(request.script_id)
            
            # 初始化执行状态
            task_status = {
                "script_id": request.script_id,
                "execution_id": execution_id,
                "status": "started",
                "script_path": str(script_path),
                "start_time": datetime.now().isoformat(),
                "current_step": 0,
                "total_steps": 0,
                "progress_percentage": 0.0,
            }

            # 保存初始执行状态
            status_file = self.workspace_root / request.script_id / "task_status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(task_status, f, ensure_ascii=False, indent=2, default=str)

            # 广播任务开始通知到全局日志连接
            # 独立服务不需要WebSocket广播
            # await self.log_query_api.broadcast_to_global_connections({
            #     "type": "task_started",
            #     "script_id": request.script_id,
            #     "execution_id": execution_id,
            #     "message": f"任务 {request.script_id} 开始执行",
            #     "script_path": str(script_path),
            #     "timestamp": datetime.now().isoformat()
            # })
            
            # 在后台启动脚本执行
            asyncio.create_task(
                self._run_script_background(request, script_path, execution_id)
            )

            # 立即返回执行启动成功
            return {
                "success": True,
                "execution_id": execution_id,
                "task_status": "started",
                "execution_summary": {
                    "script_path": str(script_path),
                    "start_time": task_status["start_time"],
                },
            }

        except Exception as e:
            logging.error(f"启动脚本执行异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "details": f"任务ID: {request.script_id}"
            }
    
    def _find_latest_script(self, script_id: str) -> Optional[Path]:
        """根据script_id查找最新的脚本文件"""
        try:
            script_dir = self.workspace_root / script_id / "coder"
            if not script_dir.exists():
                return None

            # 查找所有script_*.py文件
            script_files = list(script_dir.glob("script_*.py"))
            if not script_files:
                return None

            # 返回最新的脚本文件（按修改时间）
            latest_script = max(script_files, key=lambda f: f.stat().st_mtime)
            return latest_script

        except Exception as e:
            logging.error(f"查找脚本文件异常: {e}")
            return None

    async def _run_script_background(
        self, request: ScriptExecutionRequest, script_path: Path, execution_id: str
    ):
        """在后台运行脚本"""
        try:
            import sys

            # 清理旧的摄像头操作记录（在脚本真正开始执行时进行）
            self._cleanup_camera_operations(request.script_id)
            
            # 更新状态为运行中
            await self._update_task_status(request.script_id, {
                "status": "running",
                "message": "脚本正在执行中..."
            })
            
            # 🔧 优化：不再重定向stdout，让脚本内部日志系统负责日志文件
            # 脚本会在内部创建 script_{script_id}_{timestamp}.log 文件
            
            # Windows兼容性：确保正确的工作目录和路径
            working_dir = str(script_path.parent)
            script_file = str(script_path)

            process = await asyncio.create_subprocess_exec(
                sys.executable,
                script_file,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,  # 捕获输出用于状态更新
                stderr=asyncio.subprocess.PIPE,  # 捕获错误输出
            )

            # 异步等待进程完成，设置超时
            try:
                # 等待进程完成并获取输出
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=3600,  # 1小时超时
                )

                # 解码输出
                stdout_text = stdout.decode("utf-8", errors="ignore") if stdout else ""
                stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""
                execution_output = stdout_text + stderr_text

                # 查找脚本内部生成的日志文件
                log_dir = self.workspace_root / request.script_id / "logs"
                script_log_files = list(log_dir.glob(f"script_{request.script_id}_*.log")) if log_dir.exists() else []
                latest_log_file = max(script_log_files, key=lambda f: f.stat().st_mtime) if script_log_files else None
                
                # 更新最终状态
                if process.returncode == 0:
                    # 脚本执行成功后，上传生成的图像文件
                    await self._upload_execution_results(request.script_id)
                    
                    status_update = {
                        "status": "completed",
                        "message": "脚本执行成功",
                        "end_time": datetime.now().isoformat(),
                        "exit_code": process.returncode,
                    }
                    if latest_log_file:
                        status_update["script_log_file"] = str(latest_log_file)
                    
                    await self._update_task_status(request.script_id, status_update)
                    
                    # 等待1秒确保日志完全写入文件
                    await asyncio.sleep(1.0)

                    # 广播任务成功完成通知
                    # 独立服务不需要WebSocket广播
                    # await self.log_query_api.broadcast_to_global_connections({
                    #     "type": "task_completed",
                    #     "script_id": request.script_id,
                    #     "execution_id": execution_id,
                    #     "success": True,
                    #     "message": f"任务 {request.script_id} 执行成功",
                    #     "exit_code": process.returncode,
                    #     "timestamp": datetime.now().isoformat()
                    # })
                else:
                    status_update = {
                        "status": "failed",
                        "message": "脚本执行失败",
                        "end_time": datetime.now().isoformat(),
                        "exit_code": process.returncode,
                        "error_output": execution_output[-1000:]
                        if execution_output
                        else "",  # 只保留最后1000个字符
                    }
                    if latest_log_file:
                        status_update["script_log_file"] = str(latest_log_file)
                        
                    await self._update_task_status(request.script_id, status_update)
                    
                    # 等待1秒确保日志完全写入文件
                    await asyncio.sleep(1.0)

                    # 广播任务失败通知
                    # 独立服务不需要WebSocket广播
                    # await self.log_query_api.broadcast_to_global_connections({
                    #     "type": "task_failed",
                    #     "script_id": request.script_id,
                    #     "execution_id": execution_id,
                    #     "success": False,
                    #     "message": f"任务 {request.script_id} 执行失败",
                    #     "exit_code": process.returncode,
                    #     "error_output": execution_output[-500:] if execution_output else "",
                    #     "timestamp": datetime.now().isoformat()
                    # })
            except asyncio.TimeoutError:
                # 超时时终止进程
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

                # 查找日志文件
                log_dir = self.workspace_root / request.script_id / "logs"
                script_log_files = list(log_dir.glob(f"script_{request.script_id}_*.log")) if log_dir.exists() else []
                latest_log_file = max(script_log_files, key=lambda f: f.stat().st_mtime) if script_log_files else None
                
                status_update = {
                    "status": "failed",
                    "message": "脚本执行超时",
                    "end_time": datetime.now().isoformat(),
                    "error": "execution_timeout",
                }
                if latest_log_file:
                    status_update["script_log_file"] = str(latest_log_file)
                    
                await self._update_task_status(request.script_id, status_update)
                
                # 等待1秒确保日志完全写入文件
                await asyncio.sleep(1.0)

                # 广播任务超时通知
                # 独立服务不需要WebSocket广播
                # await self.log_query_api.broadcast_to_global_connections({
                #     "type": "task_timeout",
                #     "script_id": request.script_id,
                #     "execution_id": execution_id,
                #     "success": False,
                #     "message": f"任务 {request.script_id} 执行超时",
                #     "timestamp": datetime.now().isoformat()
                # })
        except Exception as e:
            # 查找日志文件
            log_dir = self.workspace_root / request.script_id / "logs"
            script_log_files = list(log_dir.glob(f"script_{request.script_id}_*.log")) if log_dir.exists() else []
            latest_log_file = max(script_log_files, key=lambda f: f.stat().st_mtime) if script_log_files else None
            
            status_update = {
                "status": "failed",
                "message": f"脚本执行异常: {str(e)}",
                "end_time": datetime.now().isoformat(),
                "error": str(e),
            }
            if latest_log_file:
                status_update["script_log_file"] = str(latest_log_file)
                
            await self._update_task_status(request.script_id, status_update)
                
            # 等待1秒确保日志完全写入文件
            await asyncio.sleep(1.0)

            # 广播任务异常通知
            # 独立服务不需要WebSocket广播
            # await self.log_query_api.broadcast_to_global_connections(
            #     {
            #         "type": "task_error",
            #         "task_id": request.task_id,
            #         "execution_id": execution_id,
            #         "success": False,
            #         "message": f"任务 {request.task_id} 执行异常",
            #         "error": str(e),
            #         "timestamp": datetime.now().isoformat(),
            #     }
            # )
        except Exception as e:
            logging.error(f"广播任务异常通知失败: {e}")
    
    async def _update_task_status(self, script_id: str, status_update: Dict[str, Any]):
        """更新任务状态 - 优化文件I/O避免阻塞"""
        try:
            status_file = self.workspace_root / script_id / "task_status.json"
            
            # 使用线程池执行文件I/O操作，避免阻塞事件循环
            current_status = await asyncio.get_event_loop().run_in_executor(
                None, self._read_task_status_sync, status_file, script_id
            )

            # 更新状态
            current_status.update(status_update)
            current_status["last_update"] = datetime.now().isoformat()

            # 异步保存状态
            await asyncio.get_event_loop().run_in_executor(
                None, self._write_task_status_sync, status_file, current_status
            )

        except Exception as e:
            logging.error(f"更新任务状态异常: {e}")
    
    def _read_task_status_sync(self, status_file: Path, script_id: str) -> Dict[str, Any]:
        """同步读取任务状态文件"""
        try:
            if status_file.exists():
                with open(status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return {"script_id": script_id}
        except Exception as e:
            logging.error(f"读取任务状态文件异常: {e}")
            return {"script_id": script_id}
    
    def _write_task_status_sync(self, status_file: Path, status_data: Dict[str, Any]):
        """同步写入任务状态文件"""
        try:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logging.error(f"写入任务状态文件异常: {e}")

    def _read_json_file_sync(self, file_path: Path) -> Dict[str, Any]:
        """同步读取JSON文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"读取JSON文件异常 {file_path}: {e}")
            return {}

    async def _read_json_file_with_retry(
        self, file_path: Path, max_retries: int = 3, retry_delay: float = 0.1
    ) -> Dict[str, Any]:
        """带重试机制的异步读取JSON文件，处理并发访问问题"""
        import asyncio

        for attempt in range(max_retries):
            try:
                # 使用线程池执行文件读取，避免阻塞事件循环
                def read_file():
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if not content:  # 文件为空
                            raise json.JSONDecodeError("Empty file", "", 0)
                        return json.loads(content)

                return await asyncio.get_event_loop().run_in_executor(None, read_file)

            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    logging.debug(
                        f"JSON读取失败（尝试 {attempt + 1}/{max_retries}）: {file_path}, 错误: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logging.warning(
                        f"JSON文件读取失败，已重试 {max_retries} 次: {file_path}"
                    )
                    return {}
            except FileNotFoundError:
                logging.debug(f"文件不存在: {file_path}")
                return {}
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.debug(
                        f"文件读取异常（尝试 {attempt + 1}/{max_retries}）: {file_path}, 错误: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logging.error(f"读取JSON文件失败: {file_path}, 错误: {e}")
                    return {}

        return {}
    
    def _read_camera_operations(self, script_id: str) -> List[Dict[str, Any]]:
        """读取摄像头操作记录，每个操作独立返回，不再进行配对"""
        try:
            camera_log_file = self.workspace_root / script_id / "runner" / "camera_operations.json"
            if not camera_log_file.exists():
                return []

            camera_operations = self._read_json_file_sync(camera_log_file)
            if not camera_operations:
                return []

            # 转换为API响应格式，每个操作独立返回
            check_cameral = []

            # 按时间戳排序操作记录
            sorted_operations = sorted(
                camera_operations, key=lambda x: x.get("timestamp", "")
            )

            for operation in sorted_operations:
                camera_type = operation.get("type", "unknown")
                action = operation.get("action", "unknown")
                timestamp = operation.get("timestamp", "")
                step_group_id = operation.get("step_group_id", "")

                if action == "open":
                    # open操作返回start_time，end_time为空
                    check_cameral.append(
                        {
                            "type": camera_type,
                            "step_group_id": step_group_id,
                            "start_time": timestamp,
                            "end_time": "",
                        }
                    )
                elif action == "close":
                    # close操作返回end_time，start_time为空
                    check_cameral.append(
                        {
                            "type": camera_type,
                            "step_group_id": step_group_id,
                            "start_time": "",
                            "end_time": timestamp,
                        }
                    )

            return check_cameral

        except Exception as e:
            logging.error(f"读取摄像头操作记录异常: {e}")
            return []

    def _get_script_end_time(self, script_id: str) -> str:
        """获取脚本执行结束时间"""
        try:
            # 优先从runner目录的task_status.json读取
            status_file = self.workspace_root / script_id / "runner" / "task_status.json"
            if not status_file.exists():
                # 备用路径
                status_file = self.workspace_root / script_id / "task_status.json"
            
            if status_file.exists():
                status_data = self._read_json_file_sync(status_file)
                end_time = status_data.get("end_time")
                if end_time:
                    return end_time

                # 如果没有end_time，但状态是completed或failed，使用last_update时间
                if status_data.get("status") in ["completed", "failed"]:
                    return status_data.get("last_update", "")

            # 如果都没有，返回当前时间
            from datetime import datetime

            return datetime.now().isoformat()

        except Exception as e:
            logging.error(f"获取脚本结束时间异常: {e}")
            return ""
    
    def _cleanup_camera_operations(self, script_id: str):
        """清理旧的摄像头操作记录"""
        try:
            # 清理runner目录下的camera_operations.json
            camera_log_file = self.workspace_root / script_id / "runner" / "camera_operations.json"
            if camera_log_file.exists():
                camera_log_file.unlink()
                logging.info(f"已清理旧的摄像头操作记录: {camera_log_file}")

            # 清理根目录下的camera_operations.json（如果存在）
            root_camera_log_file = self.workspace_root / script_id / "camera_operations.json"
            if root_camera_log_file.exists():
                root_camera_log_file.unlink()
                logging.info(f"已清理旧的摄像头操作记录: {root_camera_log_file}")

        except Exception as e:
            logging.warning(f"清理摄像头操作记录时发生异常: {e}")
            # 不抛出异常，避免影响脚本生成流程
    
    def _cleanup_execution_results(self, script_id: str):
        """清理旧的执行结果文件，确保重新生成脚本时不会显示历史数据"""
        try:
            task_dir = self.workspace_root / script_id
            runner_dir = task_dir / "runner"
            runner_images_dir = runner_dir / "images"

            # 需要清理的执行结果文件列表
            files_to_cleanup = [
                runner_dir / "validation_results.json",  # 预期结果执行结果
                runner_dir / "execution_results.json",  # 步骤执行结果
                runner_dir / "task_status.json",  # 任务状态文件
                task_dir / "task_status.json",  # 根目录任务状态文件
            ]

            # 清理检查点状态文件（pattern匹配）
            if runner_dir.exists():
                checkpoint_files = list(
                    runner_dir.glob("checkpoint_status_step_*.json")
                )
                files_to_cleanup.extend(checkpoint_files)

            cleaned_count = 0
            for file_path in files_to_cleanup:
                if file_path.exists():
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logging.debug(f"已清理执行结果文件: {file_path}")
                    except Exception as e:
                        logging.warning(f"清理文件失败 {file_path}: {e}")

            # 额外：清空本次执行前的运行截图目录，避免历史图片累计
            if runner_images_dir.exists():
                try:
                    for image_file in runner_images_dir.rglob("*"):
                        try:
                            if image_file.is_file():
                                image_file.unlink()
                        except Exception as e:
                            logging.debug(f"删除历史运行截图失败 {image_file}: {e}")
                except Exception as e:
                    logging.warning(f"清空运行截图目录失败 {runner_images_dir}: {e}")

            if cleaned_count > 0:
                logging.info(f"已清理 {cleaned_count} 个旧的执行结果文件")

        except Exception as e:
            logging.warning(f"清理执行结果文件时发生异常: {e}")
            # 不抛出异常，避免影响脚本生成流程
    
    async def _get_checkpoint_status_async(self, script_id: str, step_number: Optional[int]) -> Dict[str, Any]:
        """异步获取检查点状态"""
        try:
            # 从执行结果文件中读取检查点信息
            execution_results_file = self.workspace_root / script_id / "runner" / "execution_results.json"
            task_status_file = self.workspace_root / script_id / "runner" / "task_status.json"
            
            checkpoints = []

            # 尝试从task_status.json中读取实时检查点状态
            if task_status_file.exists():
                # 使用线程池执行文件读取，避免阻塞
                task_status = await asyncio.get_event_loop().run_in_executor(
                    None, self._read_json_file_sync, task_status_file
                )

                # 从execution_history中提取检查点信息
                execution_history = task_status.get("execution_history", [])
                for checkpoint in execution_history:
                    checkpoint_data = {
                        "step_number": int(checkpoint.get("step_number", 0)),
                        "step_name": checkpoint.get("step_name", ""),
                        "operation_type": task_status.get("current_operation_type", ""),
                        "checkpoint_type": checkpoint.get("checkpoint_type", ""),
                        "status": checkpoint.get("status", "待执行"),
                        "is_pass": checkpoint.get("is_pass"),
                        "detail": checkpoint.get("detail", ""),
                        "similarity_score": checkpoint.get("similarity_score", 0),
                        "execution_time": checkpoint.get("validation_duration", 0),
                        "executed_at": checkpoint.get("completed_at", ""),
                        "error_message": checkpoint.get("detail", "")
                        if not checkpoint.get("is_pass", False)
                        else "",
                    }

                    # 转换截图路径为文件服务器路径
                    checkpoint_data["screenshot_path"] = (
                        self._convert_local_path_to_server_path(
                            checkpoint.get("screenshot_path", "")
                        )
                    )

                    # 如果指定了步骤号，只返回对应步骤的检查点
                    if (
                        step_number is None
                        or int(checkpoint.get("step_number", 0)) == step_number
                    ):
                        checkpoints.append(checkpoint_data)

            # 计算摘要信息
            summary = {
                "total_checkpoints": len(checkpoints),
                "passed_checkpoints": sum(
                    1 for cp in checkpoints if cp.get("is_pass") == True
                ),
                "failed_checkpoints": sum(
                    1 for cp in checkpoints if cp.get("is_pass") == False
                ),
                "pending_checkpoints": sum(
                    1 for cp in checkpoints if cp.get("is_pass") is None
                ),
            }

            return {
                "found": len(checkpoints) > 0,
                "checkpoints": checkpoints,
                "summary": summary,
            }

        except Exception as e:
            logging.error(f"获取检查点状态异常: {e}")
            raise
    
    async def _get_expected_result_status_async(self, script_id: str, result_id: Optional[str]) -> Dict[str, Any]:
        """异步获取预期结果状态"""
        try:
            # 从验证结果文件中读取预期结果信息
            validation_results_file = self.workspace_root / script_id / "runner" / "validation_results.json"
            
            expected_results = []

            if validation_results_file.exists():
                validation_data = await self._read_json_file_with_retry(validation_results_file)
                
                # 验证结果可能在verify_after_results字段中
                results_array = validation_data.get("verify_after_results", validation_data) if isinstance(validation_data, dict) else validation_data
                
                for result in results_array:
                    result_data = {
                        "id": result.get("id", ""),
                        "is_pass": result.get("is_pass", False),
                        "details": result.get("details", ""),
                        "execution_timestamp": result.get("execution_timestamp", ""),
                        "execution_duration": result.get("execution_duration", 0),
                        "validation_screenshot_path": self._convert_local_path_to_server_path(
                            result.get("validation_screenshot_path", "")
                        ),
                    }

                    # 如果指定了结果ID，只返回对应的结果
                    if result_id is None or result.get("id") == result_id:
                        expected_results.append(result_data)

            # 计算摘要信息
            summary = {
                "total_results": len(expected_results),
                "passed_results": sum(
                    1 for er in expected_results if er.get("is_pass") == True
                ),
                "failed_results": sum(
                    1 for er in expected_results if er.get("is_pass") == False
                ),
                "success_rate": round(
                    sum(1 for er in expected_results if er.get("is_pass") == True)
                    / len(expected_results)
                    * 100,
                    2,
                )
                if expected_results
                else 0,
            }

            return {
                "found": len(expected_results) > 0,
                "expected_results": expected_results,
                "summary": summary,
            }

        except Exception as e:
            logging.error(f"获取预期结果状态异常: {e}")
            raise

    async def _get_final_execution_result_async(self, script_id: str, include_details: bool) -> Dict[str, Any]:
        """异步获取最终执行结果 - 返回与请求结构对齐的数据"""
        try:
            # 获取执行状态
            execution_status = await self._get_execution_status_async(script_id, True)
            if not execution_status["found"]:
                return {"found": False}

            # 获取预期结果状态
            expected_results_data = await self._get_expected_result_status_async(script_id, None)
            
            # 读取原始的任务配置和执行结果
            task_status_file = self.workspace_root / script_id / "runner" / "task_status.json"
            if not task_status_file.exists():
                # 备用路径
                task_status_file = self.workspace_root / script_id / "task_status.json"
            
            if not task_status_file.exists():
                return {"found": False}

            # 读取任务状态数据
            task_data = await self._read_json_file_with_retry(task_status_file)
            
            # 🎯 简化逻辑：直接从task_status.json读取action_sequence
            original_action_sequence = task_data.get("action_sequence", [])

            # 备用方案：如果task_data中没有action_sequence，尝试从脚本文件中获取
            if not original_action_sequence:
                # 从脚本生成时的配置中获取（如果有保存的话）
                script_config_file = self.workspace_root / script_id / "coder" / "script_config.json"
                if script_config_file.exists():
                    try:
                        script_config = await self._read_json_file_with_retry(
                            script_config_file
                        )
                        original_action_sequence = script_config.get(
                            "action_sequence", []
                        )
                    except Exception as e:
                        logging.warning(f"读取脚本配置失败: {e}")

                # 如果仍然没有，返回空列表但添加说明
                if not original_action_sequence:
                    logging.warning(f"任务 {script_id} 缺少action_sequence数据，可能是旧版本执行的任务")
            
            # 处理action_sequence - 格式化为标准响应结构
            if original_action_sequence:
                original_action_sequence = self._format_execution_response_actions(
                    original_action_sequence
                )

            # 处理expected_results
            expected_results = []
            if expected_results_data["found"]:
                for result_item in expected_results_data["expected_results"]:
                    expected_result = {
                        "id": result_item.get("id", ""),
                        "is_pass": result_item.get("is_pass", False),
                        "details": result_item.get("details", ""),
                        "execution_timestamp": result_item.get("execution_timestamp", ""),
                        "execution_duration": result_item.get("execution_duration", 0)
                    }
                    expected_results.append(expected_result)

            # 计算总体统计信息
            total_steps = len(original_action_sequence)
            completed_steps = sum(1 for step in original_action_sequence 
                                if step.get("status") == "success")
            
            total_checkpoints = sum(1 for step in original_action_sequence 
                                  if step.get("checkpoint", {}).get("type"))
            passed_checkpoints = sum(1 for step in original_action_sequence 
                                   if step.get("checkpoint", {}).get("is_pass") == True)
            
            total_expected_results = len(expected_results)
            passed_expected_results = sum(
                1 for result in expected_results if result.get("is_pass") == True
            )

            # 计算overall_success的逻辑
            task_status = execution_status.get("task_status", "unknown")

            # 如果任务状态是failed，overall_success应该为False
            if task_status == "failed":
                overall_success = False
            # 如果有检查点或预期结果，基于它们的通过情况判断
            elif total_checkpoints > 0 or total_expected_results > 0:
                overall_success = (
                    passed_checkpoints == total_checkpoints
                    and passed_expected_results == total_expected_results
                )
            # 如果任务状态是completed且没有检查点和预期结果，认为成功
            elif task_status == "completed":
                overall_success = True
            # 其他情况（如running, unknown等）认为不成功
            else:
                overall_success = False

            # 构建响应结构
            result_data = {
                "script_id": task_data.get("script_id", script_id),
                "task_description": task_data.get("description", task_data.get("task_description", "")),
                "action_sequence": original_action_sequence,
                "expected_results": expected_results,
                "execution_summary": {
                    "task_status": task_status,
                    "total_steps": total_steps,
                    "completed_steps": completed_steps,
                    "total_checkpoints": total_checkpoints,
                    "passed_checkpoints": passed_checkpoints,
                    "total_expected_results": total_expected_results,
                    "passed_expected_results": passed_expected_results,
                    "overall_success": overall_success,
                    "success_rate": round(
                        (
                            (passed_checkpoints + passed_expected_results)
                            / (total_checkpoints + total_expected_results)
                            * 100
                        ),
                        2,
                    )
                    if (total_checkpoints + total_expected_results) > 0
                    else 0,
                    "execution_time": {
                        "start_time": execution_status.get("execution_summary", {}).get(
                            "start_time"
                        ),
                        "end_time": execution_status.get("execution_summary", {}).get(
                            "end_time"
                        ),
                        "total_duration": execution_status.get(
                            "execution_summary", {}
                        ).get("total_duration"),
                    },
                },
            }

            return {"found": True, "result_data": result_data}

        except Exception as e:
            logging.error(f"获取最终执行结果异常: {e}")
            raise
    
    async def _get_realtime_status_async(self, script_id: str, include_logs: bool) -> Dict[str, Any]:
        """异步获取实时综合状态 - 旧版本（保留作为备份）"""
        try:
            # 并发获取各种状态信息
            execution_status_task = self._get_execution_status_async(script_id, True)
            checkpoint_status_task = self._get_checkpoint_status_async(script_id, None)
            expected_result_status_task = self._get_expected_result_status_async(script_id, None)
            
            # 等待所有任务完成
            execution_result, checkpoint_result, expected_result = await asyncio.gather(
                execution_status_task,
                checkpoint_status_task,
                expected_result_status_task,
                return_exceptions=True,
            )

            # 检查是否找到任何数据
            found = False
            execution_status = None
            checkpoints = []
            expected_results = []

            # 处理执行状态
            if isinstance(execution_result, dict) and execution_result.get("found"):
                found = True
                execution_status = {
                    "task_status": execution_result.get("task_status", "unknown"),
                    "current_step": execution_result.get("current_step", 0),
                    "total_steps": execution_result.get("total_steps", 0),
                    "progress_percentage": execution_result.get(
                        "progress_percentage", 0.0
                    ),
                    "start_time": execution_result.get("execution_summary", {}).get(
                        "start_time"
                    ),
                    "end_time": execution_result.get("execution_summary", {}).get(
                        "end_time"
                    ),
                    "execution_duration": execution_result.get(
                        "execution_summary", {}
                    ).get("execution_duration"),
                }

            # 处理检查点状态
            if isinstance(checkpoint_result, dict) and checkpoint_result.get("found"):
                found = True
                checkpoints = checkpoint_result.get("checkpoints", [])

            # 处理预期结果状态
            if isinstance(expected_result, dict) and expected_result.get("found"):
                found = True
                expected_results = expected_result.get("expected_results", [])

            # 生成综合摘要
            summary = self._generate_realtime_summary(
                execution_status, checkpoints, expected_results
            )

            # 添加日志信息（如果需要）
            if include_logs and found:
                logs = await asyncio.get_event_loop().run_in_executor(
                    None, self._get_execution_logs, script_id
                )
                summary["recent_logs"] = logs[-20:] if logs else []  # 最近20条日志

            return {
                "found": found,
                "execution_status": execution_status,
                "checkpoints": checkpoints,
                "expected_results": expected_results,
                "summary": summary,
            }

        except Exception as e:
            logging.error(f"获取实时状态异常: {e}")
            return {
                "found": False,
                "execution_status": None,
                "checkpoints": [],
                "expected_results": [],
                "summary": {"error": str(e)},
            }

    def _generate_realtime_summary(
        self,
        execution_status: Optional[Dict],
        checkpoints: List[Dict],
        expected_results: List[Dict],
    ) -> Dict[str, Any]:
        """生成实时状态摘要"""
        summary = {"timestamp": datetime.now().isoformat(), "overall_status": "unknown"}

        # 执行状态摘要
        if execution_status:
            summary["execution"] = {
                "status": execution_status.get("task_status", "unknown"),
                "progress": execution_status.get("progress_percentage", 0.0),
                "current_step": execution_status.get("current_step", 0),
                "total_steps": execution_status.get("total_steps", 0),
            }
            summary["overall_status"] = execution_status.get("task_status", "unknown")

        # 检查点摘要
        if checkpoints:
            passed_checkpoints = sum(
                1 for cp in checkpoints if cp.get("is_pass") == True
            )
            failed_checkpoints = sum(
                1 for cp in checkpoints if cp.get("is_pass") == False
            )
            pending_checkpoints = sum(
                1 for cp in checkpoints if cp.get("is_pass") is None
            )

            summary["checkpoints"] = {
                "total": len(checkpoints),
                "passed": passed_checkpoints,
                "failed": failed_checkpoints,
                "pending": pending_checkpoints,
                "pass_rate": round(passed_checkpoints / len(checkpoints) * 100, 1)
                if checkpoints
                else 0,
            }

        # 预期结果摘要
        if expected_results:
            passed_results = sum(
                1 for er in expected_results if er.get("is_pass") == True
            )
            failed_results = sum(
                1 for er in expected_results if er.get("is_pass") == False
            )
            pending_results = sum(
                1 for er in expected_results if er.get("is_pass") is None
            )

            summary["expected_results"] = {
                "total": len(expected_results),
                "passed": passed_results,
                "failed": failed_results,
                "pending": pending_results,
                "pass_rate": round(passed_results / len(expected_results) * 100, 1)
                if expected_results
                else 0,
            }

        return summary

    def _get_execution_logs(self, script_id: str) -> List[str]:
        """获取执行日志 - 优化为读取脚本内部生成的日志文件"""
        try:
            # 查找脚本内部生成的日志文件
            log_dir = self.workspace_root / script_id / "logs"
            logs = []

            if log_dir.exists():
                # 查找脚本日志文件 (script_*.log)
                script_log_files = list(log_dir.glob(f"script_{script_id}_*.log"))
                if script_log_files:
                    # 按修改时间排序，取最新的
                    latest_log_file = max(
                        script_log_files, key=lambda f: f.stat().st_mtime
                    )
                    with open(latest_log_file, "r", encoding="utf-8") as f:
                        logs.extend(f.readlines()[-100:])  # 取最后100行

                # 查找其他日志文件
                other_log_files = [
                    log_dir / "execution.log",
                    log_dir / "script_server.log",
                ]

                for log_file in other_log_files:
                    if log_file.exists():
                        with open(log_file, "r", encoding="utf-8") as f:
                            logs.extend(f.readlines()[-50:])  # 取最后50行

            return logs[-150:] if logs else []  # 总共最多返回150行
        except Exception as e:
            logging.error(f"读取执行日志异常: {e}")
            return []

    def _convert_local_path_to_server_path(self, local_path: str) -> str:
        """将本地绝对路径上传到文件服务器并返回服务器URL"""
        if not local_path or not isinstance(local_path, str):
            return local_path

        try:
            local_path_obj = Path(local_path)

            # 检查文件是否存在
            if not local_path_obj.exists():
                logging.warning(f"文件不存在: {local_path}")
                return local_path

            # 检查路径是否在workspace目录下
            if (
                self.workspace_root in local_path_obj.parents
                or local_path_obj.parent == self.workspace_root
            ):
                # DEBUG模式：暂时不上传文件服务器，直接返回本地路径
                if self.file_server_config:
                    return self._upload_file_to_server(local_path_obj)
                # else:
                # 没有文件服务器配置，返回相对路径
                # relative_path = local_path_obj.relative_to(self.workspace_root)
                # return str(relative_path).replace("\\", "/")  # 确保使用正斜杠（Windows兼容）
            else:
                # 不在workspace下的路径保持原样
                return local_path
        except Exception as e:
            logging.warning(f"路径转换失败 {local_path}: {e}")
            return local_path

    def _upload_file_to_server(self, local_path_obj: Path) -> str:
        """上传文件到文件服务器并返回URL（带缓存去重）"""
        try:
            # 检查文件是否已上传（使用缓存去重）
            cached_url = self._is_file_already_uploaded(local_path_obj)
            if cached_url:
                logging.debug(f"文件上传使用缓存: {local_path_obj.name} -> {cached_url}")
                return cached_url
            
            from ..utils.file_server import get_file_server

            file_server = get_file_server()

            # 解析路径获取task_id和文件信息
            relative_path = local_path_obj.relative_to(self.workspace_root)
            path_parts = relative_path.parts

            if len(path_parts) >= 2:
                task_id = path_parts[0]  # 第一部分是task_id
                filename = local_path_obj.name

                # 复用现有的文件分类逻辑
                category = self._classify_image_file(filename)

                # 构建远程文件名（与批量上传时的命名规律一致）
                remote_filename = f"{task_id}_{category}_{filename}"

                # 上传文件并获取URL
                server_url = file_server.upload_file(
                    str(local_path_obj), remote_filename
                )

                if server_url:
                    # 缓存上传结果
                    self._cache_uploaded_file(local_path_obj, server_url, remote_filename)
                    logging.debug(f"文件上传成功: {local_path_obj.name} -> {server_url}")
                    return server_url
                else:
                    logging.warning(f"文件上传失败: {local_path_obj}")
                    # 上传失败，返回相对路径作为备选
                    return str(relative_path).replace("\\", "/")
            else:
                # 路径结构不符合预期，返回相对路径
                return str(relative_path).replace("\\", "/")

        except Exception as e:
            logging.warning(f"上传文件到服务器失败 {local_path_obj}: {e}")
            # 出错时返回相对路径作为备选
            try:
                relative_path = local_path_obj.relative_to(self.workspace_root)
                return str(relative_path).replace("\\", "/")
            except:
                return str(local_path_obj)


    def _format_execution_response_actions(self, action_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化执行响应中的动作序列，保持控制流结构完整性"""
        if not isinstance(action_sequence, list):
            return action_sequence

        # 需要移除的顶级字段
        exclude_fields = {'screenshot_url', 'script', 'template_name', 'custom_vars', 'duration', 'error_message',
                         'before_execution_screenshot_path', 'after_execution_screenshot_path', 'control_flow_config'}
        
        # 需要保留的checkpoint字段
        checkpoint_fields = {
            "type",
            "description",
            "screenshot_path",
            "is_pass",
            "detail",
            "similarity_score",
            "status",
            "execution_time",
            "executed_at",
            "error_message",
        }

        result = []
        for action in action_sequence:
            if not isinstance(action, dict):
                result.append(action)
                continue
            
            # 🎯 新逻辑：控制流步骤保持原有结构，但添加executed_sub_steps字段
            if action.get('step_type') == 'control_flow':
                # 格式化控制流步骤本身
                formatted_control_flow = self._format_single_action(action, exclude_fields, checkpoint_fields)
                
                # 获取并格式化执行的子步骤
                expanded_sub_steps = self._expand_control_flow_action(action)
                if expanded_sub_steps:
                    # 格式化每个子步骤
                    formatted_sub_steps = []
                    for sub_step in expanded_sub_steps:
                        formatted_sub_step = self._format_single_action(sub_step, exclude_fields, checkpoint_fields)
                        formatted_sub_steps.append(formatted_sub_step)
                    
                    # 将格式化后的子步骤添加到控制流步骤中
                    formatted_control_flow['executed_sub_steps'] = formatted_sub_steps
                
                result.append(formatted_control_flow)
                continue
            
            # 处理普通action
            formatted_action = self._format_single_action(action, exclude_fields, checkpoint_fields)
            result.append(formatted_action)

        return result

    def _format_single_action(self, action: Dict[str, Any], exclude_fields: set, checkpoint_fields: set) -> Dict[str, Any]:
        """格式化单个action"""
        # 复制action，移除不需要的字段
        formatted_action = {k: v for k, v in action.items() if k not in exclude_fields}
        
        # 确保每个action都有step_number字段
        if "step_number" not in formatted_action or formatted_action["step_number"] is None:
            formatted_action["step_number"] = action.get('step_number', 1)
        
        # 获取步骤执行时间
        step_duration = action.get('execution_duration', 0)
        
        # 处理element_info的图像路径转换
        if "element_info" in formatted_action and formatted_action["element_info"]:
            element_info = formatted_action["element_info"]
            # 转换图像路径
            if element_info.get("icon_path"):
                element_info["icon_path"] = self._convert_local_path_to_server_path(element_info["icon_path"])
        
        # 转换图像路径
        if formatted_action.get("screenshot_path"):
            formatted_action["screenshot_path"] = self._convert_local_path_to_server_path(formatted_action["screenshot_path"])
        
        # 处理checkpoint字段过滤和图像路径
        if "checkpoint" in formatted_action:
            checkpoint = formatted_action["checkpoint"]
            
            # 🎯 标准化空checkpoint：确保空配置时返回标准的none类型结构
            if not checkpoint or checkpoint == {}:
                # 空checkpoint配置，设置标准的none类型结构
                formatted_action["checkpoint"] = {
                    "type": "none",
                    "description": "",
                    "screenshot_path": None,
                    "is_pass": None,
                    "detail": "",
                    "similarity_score": None,
                    "status": "待执行",
                    "execution_time": None,
                    "executed_at": None,
                    "error_message": None
                }
            else:
                # 有checkpoint配置，过滤字段并转换路径
                formatted_checkpoint = {}
                for k, v in checkpoint.items():
                    if k in checkpoint_fields:
                        if k == "screenshot_path" and v:
                            formatted_checkpoint[k] = self._convert_local_path_to_server_path(v)
                        else:
                            formatted_checkpoint[k] = v
                
                # 确保所有必需字段都存在
                formatted_action["checkpoint"] = {
                    "type": formatted_checkpoint.get("type", "none"),
                    "description": formatted_checkpoint.get("description", ""),
                    "screenshot_path": formatted_checkpoint.get("screenshot_path"),
                    "is_pass": formatted_checkpoint.get("is_pass"),
                    "detail": formatted_checkpoint.get("detail", ""),
                    "similarity_score": formatted_checkpoint.get("similarity_score"),
                    "status": formatted_checkpoint.get("status", "待执行"),
                    "execution_time": formatted_checkpoint.get("execution_time"),
                    "executed_at": formatted_checkpoint.get("executed_at"),
                    "error_message": formatted_checkpoint.get("error_message")
                }
        
        # 统一处理截图路径（避免重复转换）
        before_screenshot = action.get('before_execution_screenshot_path')
        after_screenshot = action.get('after_execution_screenshot_path')
        
        # 转换路径（一次性处理）
        before_screenshot_converted = self._convert_local_path_to_server_path(before_screenshot) if before_screenshot else None
        after_screenshot_converted = self._convert_local_path_to_server_path(after_screenshot) if after_screenshot else None
        
        # 确保每个action都有execution_result字段（严格格式：只包含message、screenshots、duration）
        if "execution_result" not in formatted_action or not formatted_action["execution_result"]:
            formatted_action["execution_result"] = {
                "message": "步骤执行完成",
                "duration": step_duration,
                "screenshots": {
                    "before_execution": before_screenshot_converted,
                    "after_execution": after_screenshot_converted
                }
            }
        else:
            # 处理现有的execution_result，清理为严格格式
            existing_result = formatted_action["execution_result"]
            
            # 提取截图信息
            screenshots = existing_result.get("screenshots", {})
            if not screenshots:
                screenshots = {
                    "before_execution": before_screenshot_converted,
                    "after_execution": after_screenshot_converted
                }
            else:
                # 转换已有的screenshots路径
                for key in ["before_execution", "after_execution"]:
                    if screenshots.get(key):
                        screenshots[key] = self._convert_local_path_to_server_path(screenshots[key])
            
            # 重新构建execution_result，只保留3个核心字段
            formatted_action["execution_result"] = {
                "message": existing_result.get("message", "步骤执行完成"),
                "duration": step_duration,
                "screenshots": screenshots
            }
        
        # 确保每个action都有screenshot_path字段（使用after_execution作为主要截图）
        if "screenshot_path" not in formatted_action or not formatted_action["screenshot_path"]:
            formatted_action["screenshot_path"] = after_screenshot_converted or before_screenshot_converted
        
        return formatted_action

    def _expand_control_flow_action(self, control_flow_action: Dict[str, Any]) -> List[Dict[str, Any]]:
        """统一展开所有控制流的实际执行子步骤"""
        # 🎯 统一逻辑：所有控制流都使用相同的处理方式
        execution_result = control_flow_action.get('execution_result', {})
        executed_sub_steps = execution_result.get('executed_sub_steps', [])
        
        if executed_sub_steps:
            # ✅ 返回实际执行的子步骤（包含完整的执行状态和检查点信息）
            return executed_sub_steps
        
        # 🔄 回退：如果没有执行记录，返回空列表（保持一致性）
        logging.warning(f"控制流步骤没有找到执行记录，返回空列表")
        return []

    def _convert_dict_image_paths(self, data: dict, path_fields: List[str]) -> dict:
        """通用的字典图像路径转换方法"""
        for field in path_fields:
            if field in data and data[field]:
                data[field] = self._convert_local_path_to_server_path(data[field])
        return data

    def _convert_expected_results_to_objects(self, expected_results: List) -> List[ValidationModel]:
        """将预期结果列表转换为ValidationModel对象列表"""
        objects = []
        optional_fields = [
            "target_image_path",
            "reference_image_path",
            "target_bbox",
            "target_text",
            "wait_time",
            "timeout",
        ]

        for data in expected_results:
            try:
                converted = {
                    "id": str(data.get("id", "")),
                    "description": str(data.get("description", "")),
                    "mode": ValidationMode(data.get("mode", "manual")),
                    "data_source": DataSource(data.get("data_source", "adb_screenshot")),
                    "validation_type": ValidationType(data["validation_type"]) if data.get("validation_type") else None,
                    "similarity_threshold": float(data.get("similarity_threshold", 0.8)),
                    "expect_exists": bool(data.get("expect_exists", True)),
                    **{
                        k: v
                        for k, v in data.items()
                        if k in optional_fields and v is not None
                    },
                }
                
                objects.append(ValidationModel(**converted))
                
            except Exception as e:
                logging.warning(f"转换预期结果 {data.get('id', 'unknown')} 失败: {e}")
                continue

        return objects


# 便捷函数
def create_script_service(
    workspace_root: Path,
    log_level: str = "INFO",
    enable_file_server: bool = True,
    file_server_host: str = "localhost",
    file_server_port: int = 8080,
) -> Service:
    """创建并初始化脚本生成服务实例"""
    return Service(
        workspace_root=workspace_root,
        log_level=log_level,
        enable_file_server=enable_file_server,
        file_server_host=file_server_host,
        file_server_port=file_server_port,
    )


