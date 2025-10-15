"""
Jinja2模板引擎核心类
负责模板加载、缓存、渲染和自定义功能注册
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Callable, Union
from datetime import datetime
import hashlib

from jinja2 import (
    Environment, 
    FileSystemLoader, 
    select_autoescape,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
    UndefinedError
)
from jinja2.ext import Extension

from ..models.script_context import ScriptContext

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Jinja2模板引擎封装类
    提供模板加载、缓存、渲染和自定义功能管理
    """
    
    def __init__(
        self, 
        template_dirs: List[Union[str, Path]] = None,
        enable_cache: bool = True,
        cache_size: int = 100,
        auto_reload: bool = True,
        enable_autoescape: bool = True
    ):
        """
        初始化模板引擎
        
        Args:
            template_dirs: 模板目录列表
            enable_cache: 是否启用模板缓存
            cache_size: 缓存大小
            auto_reload: 是否自动重载模板
            enable_autoescape: 是否启用自动转义
        """
        self.template_dirs = self._prepare_template_dirs(template_dirs)
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self.auto_reload = auto_reload
        self.enable_autoescape = enable_autoescape
        
        # 初始化Jinja2环境
        self.env = self._create_environment()
        
        # 模板缓存
        self._template_cache: Dict[str, Template] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # 自定义过滤器和函数
        self._custom_filters: Dict[str, Callable] = {}
        self._custom_functions: Dict[str, Callable] = {}
        self._custom_tests: Dict[str, Callable] = {}
        
        # 注册默认过滤器和函数
        self._register_default_filters()
        self._register_default_functions()
        
        logger.info(f"模板引擎初始化完成，模板目录: {self.template_dirs}")
    
    def _prepare_template_dirs(self, template_dirs: List[Union[str, Path]] = None) -> List[Path]:
        """准备模板目录列表"""
        if template_dirs is None:
            root_dir = Path(__file__).resolve().parent.parent
            template_dirs = [
                root_dir / "templates",
                root_dir / "templates" / "base",
                root_dir / "templates" / "handlers",
                root_dir / "templates" / "main"
            ]
        
        # 转换为Path对象并验证
        prepared_dirs = []
        for template_dir in template_dirs:
            path = Path(template_dir)
            if path.exists() and path.is_dir():
                prepared_dirs.append(path)
            else:
                logger.warning(f"模板目录不存在或不是目录: {path}")
        
        if not prepared_dirs:
            raise ValueError("没有有效的模板目录")
        
        return prepared_dirs
    
    def _create_environment(self) -> Environment:
        """创建Jinja2环境"""
        # 创建文件系统加载器
        loader = FileSystemLoader(
            searchpath=[str(d) for d in self.template_dirs],
            encoding='utf-8'
        )
        
        # 配置自动转义
        autoescape = select_autoescape(['html', 'xml', 'j2']) if self.enable_autoescape else False
        
        # 创建环境
        env = Environment(
            loader=loader,
            autoescape=autoescape,
            auto_reload=self.auto_reload,
            cache_size=self.cache_size if self.enable_cache else 0,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        return env
    
    def _register_default_filters(self):
        """注册默认过滤器"""
        
        def tojson_filter(value, indent=None, ensure_ascii=False):
            """JSON序列化过滤器 - 修复null值和布尔值问题"""
            json_str = json.dumps(value, indent=indent, ensure_ascii=ensure_ascii, default=str)
            # 将JSON的null替换为Python的None
            json_str = json_str.replace(': null', ': None')
            json_str = json_str.replace('[null', '[None')
            json_str = json_str.replace(',null', ',None')
            json_str = json_str.replace('null,', 'None,')
            json_str = json_str.replace('null]', 'None]')
            json_str = json_str.replace('null}', 'None}')
            # 处理单独的null值
            if json_str == 'null':
                json_str = 'None'
            
            # 将JSON的布尔值替换为Python的布尔值
            json_str = json_str.replace(': true', ': True')
            json_str = json_str.replace('[true', '[True')
            json_str = json_str.replace(',true', ',True')
            json_str = json_str.replace('true,', 'True,')
            json_str = json_str.replace('true]', 'True]')
            json_str = json_str.replace('true}', 'True}')
            
            json_str = json_str.replace(': false', ': False')
            json_str = json_str.replace('[false', '[False')
            json_str = json_str.replace(',false', ',False')
            json_str = json_str.replace('false,', 'False,')
            json_str = json_str.replace('false]', 'False]')
            json_str = json_str.replace('false}', 'False}')
            
            # 处理单独的布尔值
            if json_str == 'true':
                json_str = 'True'
            elif json_str == 'false':
                json_str = 'False'
                
            return json_str
        
        def timestamp_filter(value=None, format_str="%Y-%m-%d %H:%M:%S"):
            """时间戳格式化过滤器"""
            if value is None:
                value = datetime.now()
            elif isinstance(value, (int, float)):
                value = datetime.fromtimestamp(value)
            return value.strftime(format_str)
        
        def basename_filter(value):
            """获取文件名过滤器"""
            return Path(value).name
        
        def dirname_filter(value):
            """获取目录名过滤器"""
            return str(Path(value).parent)
        
        def hash_filter(value, algorithm='md5'):
            """哈希过滤器"""
            if algorithm == 'md5':
                return hashlib.md5(str(value).encode()).hexdigest()
            elif algorithm == 'sha1':
                return hashlib.sha1(str(value).encode()).hexdigest()
            elif algorithm == 'sha256':
                return hashlib.sha256(str(value).encode()).hexdigest()
            else:
                raise ValueError(f"不支持的哈希算法: {algorithm}")
        
        def safe_get_filter(value, key, default=None):
            """安全获取字典值过滤器"""
            if isinstance(value, dict):
                return value.get(key, default)
            return default
        
        def string_filter(value):
            """字符串转换过滤器"""
            return str(value)
        
        # 注册过滤器
        self.register_filter('tojson', tojson_filter)
        self.register_filter('timestamp', timestamp_filter)
        self.register_filter('basename', basename_filter)
        self.register_filter('dirname', dirname_filter)
        self.register_filter('hash', hash_filter)
        self.register_filter('safe_get', safe_get_filter)
        self.register_filter('string', string_filter)
    
    def _register_default_functions(self):
        """注册默认全局函数"""
        
        def now_function(format_str="%Y-%m-%d %H:%M:%S"):
            """获取当前时间"""
            return datetime.now().strftime(format_str)
        
        def range_function(*args):
            """范围函数"""
            return list(range(*args))
        
        def len_function(value):
            """长度函数"""
            return len(value) if hasattr(value, '__len__') else 0
        
        def bool_function(value):
            """布尔转换函数"""
            return bool(value)
        
        def str_function(value):
            """字符串转换函数"""
            return str(value)
        
        def int_function(value, default=0):
            """整数转换函数"""
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        def float_function(value, default=0.0):
            """浮点数转换函数"""
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # 注册全局函数
        self.register_function('now', now_function)
        self.register_function('range', range_function)
        self.register_function('len', len_function)
        self.register_function('bool', bool_function)
        self.register_function('str', str_function)
        self.register_function('int', int_function)
        self.register_function('float', float_function)
    
    def register_filter(self, name: str, filter_func: Callable):
        """注册自定义过滤器"""
        self._custom_filters[name] = filter_func
        self.env.filters[name] = filter_func
        logger.debug(f"注册过滤器: {name}")
    
    def register_function(self, name: str, func: Callable):
        """注册自定义全局函数"""
        self._custom_functions[name] = func
        self.env.globals[name] = func
        logger.debug(f"注册全局函数: {name}")
    
    def register_test(self, name: str, test_func: Callable):
        """注册自定义测试函数"""
        self._custom_tests[name] = test_func
        self.env.tests[name] = test_func
        logger.debug(f"注册测试函数: {name}")
    
    def register_extension(self, extension: Union[str, Extension]):
        """注册Jinja2扩展"""
        if isinstance(extension, str):
            self.env.add_extension(extension)
        else:
            self.env.add_extension(extension)
        logger.debug(f"注册扩展: {extension}")
    
    def get_template(self, template_name: str, use_cache: bool = True) -> Template:
        """
        获取模板对象
        
        Args:
            template_name: 模板名称
            use_cache: 是否使用缓存
            
        Returns:
            Template: 模板对象
            
        Raises:
            TemplateNotFound: 模板不存在
            TemplateSyntaxError: 模板语法错误
        """
        # 检查缓存
        if use_cache and self.enable_cache and template_name in self._template_cache:
            # 检查模板文件是否更新
            if self._is_template_fresh(template_name):
                return self._template_cache[template_name]
        
        try:
            # 加载模板
            template = self.env.get_template(template_name)
            
            # 缓存模板
            if use_cache and self.enable_cache:
                self._cache_template(template_name, template)
            
            return template
            
        except TemplateNotFound as e:
            logger.error(f"模板不存在: {template_name}")
            raise e
        except TemplateSyntaxError as e:
            logger.error(f"模板语法错误: {template_name}, 错误: {e}")
            raise e
    
    def _is_template_fresh(self, template_name: str) -> bool:
        """检查模板是否是最新的"""
        if not self.auto_reload:
            return True
        
        cached_time = self._cache_timestamps.get(template_name, 0)
        
        # 查找模板文件
        for template_dir in self.template_dirs:
            template_path = template_dir / template_name
            if template_path.exists():
                file_time = template_path.stat().st_mtime
                return file_time <= cached_time
        
        return False
    
    def _cache_template(self, template_name: str, template: Template):
        """缓存模板"""
        # 清理缓存（如果超出大小限制）
        if len(self._template_cache) >= self.cache_size:
            # 移除最旧的模板
            oldest_name = min(self._cache_timestamps.keys(), 
                            key=lambda k: self._cache_timestamps[k])
            del self._template_cache[oldest_name]
            del self._cache_timestamps[oldest_name]
        
        # 缓存模板
        self._template_cache[template_name] = template
        self._cache_timestamps[template_name] = datetime.now().timestamp()
    
    def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            context: 模板上下文数据
            use_cache: 是否使用缓存
            
        Returns:
            str: 渲染结果
            
        Raises:
            TemplateNotFound: 模板不存在
            TemplateSyntaxError: 模板语法错误
            UndefinedError: 未定义变量错误
        """
        if context is None:
            context = {}
        
        try:
            template = self.get_template(template_name, use_cache)
            result = template.render(context)
            
            logger.debug(f"模板渲染成功: {template_name}")
            return result
            
        except UndefinedError as e:
            logger.error(f"模板变量未定义: {template_name}, 错误: {e}")
            raise e
        except Exception as e:
            logger.error(f"模板渲染失败: {template_name}, 错误: {e}")
            raise e
    
    def render_string(self, template_string: str, context: Dict[str, Any] = None) -> str:
        """
        渲染模板字符串
        
        Args:
            template_string: 模板字符串
            context: 模板上下文数据
            
        Returns:
            str: 渲染结果
        """
        if context is None:
            context = {}
        
        try:
            template = self.env.from_string(template_string)
            result = template.render(context)
            
            logger.debug("模板字符串渲染成功")
            return result
            
        except Exception as e:
            logger.error(f"模板字符串渲染失败: {e}")
            raise e
    
    def list_templates(self, pattern: str = None) -> List[str]:
        """
        列出所有可用模板
        
        Args:
            pattern: 过滤模式（支持通配符）
            
        Returns:
            List[str]: 模板名称列表
        """
        try:
            templates = self.env.list_templates()
            
            if pattern:
                import fnmatch
                templates = [t for t in templates if fnmatch.fnmatch(t, pattern)]
            
            return sorted(templates)
            
        except Exception as e:
            logger.error(f"列出模板失败: {e}")
            return []
    
    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """
        验证模板语法
        
        Args:
            template_name: 模板名称
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            template = self.get_template(template_name, use_cache=False)
            
            # 尝试渲染空上下文
            try:
                template.render({})
                result["valid"] = True
            except UndefinedError as e:
                result["warnings"].append(f"未定义变量: {e}")
                result["valid"] = True  # 语法正确，只是缺少变量
            except Exception as e:
                result["errors"].append(f"渲染错误: {e}")
                
        except TemplateSyntaxError as e:
            result["errors"].append(f"语法错误: {e}")
        except TemplateNotFound as e:
            result["errors"].append(f"模板不存在: {e}")
        except Exception as e:
            result["errors"].append(f"未知错误: {e}")
        
        return result
    
    def clear_cache(self):
        """清空模板缓存"""
        self._template_cache.clear()
        self._cache_timestamps.clear()
        logger.info("模板缓存已清空")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cache_enabled": self.enable_cache,
            "cache_size": len(self._template_cache),
            "max_cache_size": self.cache_size,
            "cached_templates": list(self._template_cache.keys())
        }
    
    def reload_templates(self):
        """重新加载所有模板"""
        self.clear_cache()
        # 重新创建环境以确保重新加载
        self.env = self._create_environment()
        # 重新注册自定义功能
        for name, func in self._custom_filters.items():
            self.env.filters[name] = func
        for name, func in self._custom_functions.items():
            self.env.globals[name] = func
        for name, func in self._custom_tests.items():
            self.env.tests[name] = func
        
        logger.info("模板已重新加载")
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            Dict[str, Any]: 模板信息
        """
        info = {
            "name": template_name,
            "exists": False,
            "path": None,
            "size": 0,
            "modified_time": None,
            "cached": template_name in self._template_cache
        }
        
        # 查找模板文件
        for template_dir in self.template_dirs:
            template_path = template_dir / template_name
            if template_path.exists():
                info["exists"] = True
                info["path"] = str(template_path)
                info["size"] = template_path.stat().st_size
                info["modified_time"] = datetime.fromtimestamp(
                    template_path.stat().st_mtime
                ).isoformat()
                break
        
        return info


# 默认模板引擎实例
default_template_engine = TemplateEngine()


def get_template_engine() -> TemplateEngine:
    """获取默认模板引擎实例"""
    return default_template_engine


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """便捷的模板渲染函数"""
    return default_template_engine.render_template(template_name, context)


def render_script(context: ScriptContext) -> str:
    """便捷的脚本生成函数"""
    return default_template_engine.render_script(context) 