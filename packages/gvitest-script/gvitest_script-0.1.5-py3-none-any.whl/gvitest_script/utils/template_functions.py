"""
自定义Jinja2模板全局函数
为脚本生成提供专用的全局函数
"""

import os
import uuid
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib
import json
import base64

from ..utils.validation_utils import validate_validation_model


def generate_uuid(version: int = 4) -> str:
    """生成UUID"""
    if version == 1:
        return str(uuid.uuid1())
    elif version == 4:
        return str(uuid.uuid4())
    else:
        return str(uuid.uuid4())


def generate_random_string(length: int = 8, charset: str = "alphanumeric") -> str:
    """生成随机字符串"""
    if charset == "alphanumeric":
        chars = string.ascii_letters + string.digits
    elif charset == "alpha":
        chars = string.ascii_letters
    elif charset == "numeric":
        chars = string.digits
    elif charset == "lowercase":
        chars = string.ascii_lowercase
    elif charset == "uppercase":
        chars = string.ascii_uppercase
    elif charset == "hex":
        chars = string.hexdigits.lower()
    else:
        chars = charset
    
    return ''.join(random.choice(chars) for _ in range(length))


def generate_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """生成时间戳字符串"""
    return datetime.now().strftime(format_str)


def generate_filename(prefix: str = "", suffix: str = "", extension: str = "txt") -> str:
    """生成文件名"""
    timestamp = generate_timestamp()
    random_part = generate_random_string(6)
    
    parts = [part for part in [prefix, timestamp, random_part, suffix] if part]
    basename = "_".join(parts)
    
    return f"{basename}.{extension.lstrip('.')}"


def calculate_checksum(content: Union[str, bytes], algorithm: str = "md5") -> str:
    """计算内容校验和"""
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    if algorithm.lower() == "md5":
        return hashlib.md5(content).hexdigest()
    elif algorithm.lower() == "sha1":
        return hashlib.sha1(content).hexdigest()
    elif algorithm.lower() == "sha256":
        return hashlib.sha256(content).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def format_python_dict(data: Dict[str, Any], indent: int = 4) -> str:
    """格式化Python字典为字符串"""
    import pprint
    return pprint.pformat(data, indent=indent, width=120)


def format_python_list(data: List[Any], indent: int = 4) -> str:
    """格式化Python列表为字符串"""
    import pprint
    return pprint.pformat(data, indent=indent, width=120)


def escape_quotes(text: str, quote_type: str = "double") -> str:
    """转义引号"""
    if quote_type == "double":
        return text.replace('"', '\\"')
    elif quote_type == "single":
        return text.replace("'", "\\'")
    else:
        return text.replace('"', '\\"').replace("'", "\\'")


def join_lines(*lines) -> str:
    """连接多行文本"""
    return '\n'.join(str(line) for line in lines if line is not None)


def indent_lines(text: str, level: int = 1, indent_char: str = "    ") -> str:
    """为每行添加缩进"""
    indent = indent_char * level
    lines = text.split('\n')
    return '\n'.join(indent + line if line.strip() else line for line in lines)


def create_comment_block(text: str, style: str = "python", width: int = 80) -> str:
    """创建注释块"""
    if style == "python":
        comment_char = "#"
    elif style == "javascript":
        comment_char = "//"
    elif style == "sql":
        comment_char = "--"
    else:
        comment_char = "#"
    
    lines = text.split('\n')
    result = []
    
    # 顶部边框
    result.append(comment_char + " " + "=" * (width - 3))
    
    # 内容行
    for line in lines:
        if len(line) > width - 5:
            # 长行需要换行
            import textwrap
            wrapped_lines = textwrap.wrap(line, width - 5)
            for wrapped_line in wrapped_lines:
                result.append(f"{comment_char} {wrapped_line}")
        else:
            result.append(f"{comment_char} {line}")
    
    # 底部边框
    result.append(comment_char + " " + "=" * (width - 3))
    
    return '\n'.join(result)


def get_env_var(name: str, default: str = "") -> str:
    """获取环境变量"""
    return os.environ.get(name, default)


def file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return Path(filepath).exists()


def dir_exists(dirpath: str) -> bool:
    """检查目录是否存在"""
    return Path(dirpath).is_dir()


def get_file_size(filepath: str) -> int:
    """获取文件大小（字节）"""
    try:
        return Path(filepath).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def get_file_mtime(filepath: str) -> Optional[datetime]:
    """获取文件修改时间"""
    try:
        timestamp = Path(filepath).stat().st_mtime
        return datetime.fromtimestamp(timestamp)
    except (OSError, FileNotFoundError):
        return None


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> List[str]:
    """列出目录中的文件"""
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        
        if recursive:
            files = dir_path.rglob(pattern)
        else:
            files = dir_path.glob(pattern)
        
        return [str(f) for f in files if f.is_file()]
    except Exception:
        return []


def make_dirs(directory: str) -> bool:
    """创建目录（包括父目录）"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def read_text_file(filepath: str, encoding: str = "utf-8") -> str:
    """读取文本文件内容"""
    try:
        return Path(filepath).read_text(encoding=encoding)
    except Exception:
        return ""


def write_text_file(filepath: str, content: str, encoding: str = "utf-8") -> bool:
    """写入文本文件"""
    try:
        Path(filepath).write_text(content, encoding=encoding)
        return True
    except Exception:
        return False


def range_list(start: int, stop: int = None, step: int = 1) -> List[int]:
    """生成范围列表"""
    if stop is None:
        stop = start
        start = 0
    return list(range(start, stop, step))


def zip_lists(*lists) -> List[tuple]:
    """压缩多个列表"""
    return list(zip(*lists))


def enumerate_list(lst: List[Any], start: int = 0) -> List[tuple]:
    """枚举列表"""
    return list(enumerate(lst, start))


def filter_list(lst: List[Any], key: str, value: Any) -> List[Any]:
    """过滤列表（基于字典键值）"""
    return [item for item in lst if isinstance(item, dict) and item.get(key) == value]


def sort_list(lst: List[Any], key: str = None, reverse: bool = False) -> List[Any]:
    """排序列表"""
    if key and all(isinstance(item, dict) for item in lst):
        return sorted(lst, key=lambda x: x.get(key, ""), reverse=reverse)
    else:
        return sorted(lst, reverse=reverse)


def group_by(lst: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    """按键分组列表"""
    groups = {}
    for item in lst:
        if isinstance(item, dict):
            group_key = item.get(key, "unknown")
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
    return groups


def merge_dicts(*dicts) -> Dict[str, Any]:
    """合并多个字典"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def get_dict_path(data: Dict[str, Any], path: str, separator: str = ".") -> Any:
    """获取嵌套字典的值（通过路径）"""
    keys = path.split(separator)
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return None


def set_dict_path(data: Dict[str, Any], path: str, value: Any, separator: str = ".") -> Dict[str, Any]:
    """设置嵌套字典的值（通过路径）"""
    keys = path.split(separator)
    current = data
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return data


def calculate_percentage(part: Union[int, float], total: Union[int, float], decimal_places: int = 1) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimal_places)


def clamp_value(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """限制数值范围"""
    return max(min_val, min(value, max_val))


def round_number(value: Union[int, float], decimal_places: int = 2) -> float:
    """四舍五入数字"""
    return round(float(value), decimal_places)


def format_number(value: Union[int, float], thousands_sep: str = ",") -> str:
    """格式化数字（添加千位分隔符）"""
    return f"{value:,}".replace(",", thousands_sep)


def parse_json_safe(text: str, default: Any = None) -> Any:
    """安全解析JSON"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def to_json_string(data: Any, indent: int = None, ensure_ascii: bool = False) -> str:
    """转换为JSON字符串"""
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, default=str)


def base64_encode_string(text: str) -> str:
    """Base64编码字符串"""
    return base64.b64encode(text.encode('utf-8')).decode('ascii')


def base64_decode_string(encoded: str) -> str:
    """Base64解码字符串"""
    try:
        return base64.b64decode(encoded).decode('utf-8')
    except Exception:
        return encoded


def url_join(*parts) -> str:
    """拼接URL路径"""
    from urllib.parse import urljoin
    result = parts[0] if parts else ""
    for part in parts[1:]:
        result = urljoin(result.rstrip('/') + '/', part.lstrip('/'))
    return result


def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间字符串"""
    return datetime.now().strftime(format_str)


def add_time_delta(base_time: str, **kwargs) -> str:
    """时间增加/减少"""
    try:
        # 尝试解析时间字符串
        dt = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
    except ValueError:
        # 如果解析失败，使用当前时间
        dt = datetime.now()
    
    delta = timedelta(**kwargs)
    result = dt + delta
    return result.isoformat()


def get_template_functions() -> Dict[str, Any]:
    """获取所有自定义模板函数"""
    return {
        # 生成器函数
        'generate_uuid': generate_uuid,
        'generate_random_string': generate_random_string,
        'generate_timestamp': generate_timestamp,
        'generate_filename': generate_filename,
        
        # 哈希和校验
        'calculate_checksum': calculate_checksum,
        
        # 格式化
        'format_python_dict': format_python_dict,
        'format_python_list': format_python_list,
        'escape_quotes': escape_quotes,
        'join_lines': join_lines,
        'indent_lines': indent_lines,
        'create_comment_block': create_comment_block,
        
        # 环境和系统
        'get_env_var': get_env_var,
        
        # 文件操作
        'file_exists': file_exists,
        'dir_exists': dir_exists,
        'get_file_size': get_file_size,
        'get_file_mtime': get_file_mtime,
        'list_files': list_files,
        'make_dirs': make_dirs,
        'read_text_file': read_text_file,
        'write_text_file': write_text_file,
        
        # 列表操作
        'range_list': range_list,
        'zip_lists': zip_lists,
        'enumerate_list': enumerate_list,
        'filter_list': filter_list,
        'sort_list': sort_list,
        'group_by': group_by,
        
        # 字典操作
        'merge_dicts': merge_dicts,
        'get_dict_path': get_dict_path,
        'set_dict_path': set_dict_path,
        
        # 数学计算
        'calculate_percentage': calculate_percentage,
        'clamp_value': clamp_value,
        'round_number': round_number,
        'format_number': format_number,
        
        # JSON处理
        'parse_json_safe': parse_json_safe,
        'to_json_string': to_json_string,
        
        # 编码处理
        'base64_encode_string': base64_encode_string,
        'base64_decode_string': base64_decode_string,
        
        # URL处理
        'url_join': url_join,
        
        # 时间处理
        'get_current_time': get_current_time,
        'add_time_delta': add_time_delta,
        
        # 控制流函数
        'evaluate_condition_expression': evaluate_condition_expression,
        'validate_validation_model': validate_validation_model,
        
        # CAN 相关函数
        'start_can_capture': start_can_capture,
        'stop_can_capture': stop_can_capture,
        'get_current_can_file_path': get_current_can_file_path,
        'check_remaining_verify_steps': check_remaining_verify_steps,
        'is_can_capture_running': is_can_capture_running,
        'get_can_capture_status': get_can_capture_status,
    }


# 导入表达式工具函数
from .expression_utils import evaluate_condition_expression

# CAN 相关函数定义
def start_can_capture(task_id: str, can_capture_config: dict, runner_dir: str) -> str:
    """
    启动CAN信号采集 - 模板函数包装器
    
    Args:
        task_id: 任务ID
        can_capture_config: CAN采集配置
        runner_dir: 运行目录
    
    Returns:
        str: 采集文件路径
    """
    # 这个函数在生成的脚本中会被utilities.j2中的实际实现覆盖
    # 这里提供一个占位符实现，确保模板编译时不会报错
    import os
    can_dir = os.path.join(runner_dir, 'can_signals')
    os.makedirs(can_dir, exist_ok=True)
    return os.path.join(can_dir, f'{task_id}_signals.txt')


def stop_can_capture(task_id: str) -> bool:
    """
    停止CAN信号采集 - 模板函数包装器
    
    Args:
        task_id: 任务ID
    
    Returns:
        bool: 是否成功停止
    """
    # 占位符实现
    return True


def get_current_can_file_path(task_id: str) -> str:
    """
    获取当前CAN采集文件路径 - 模板函数包装器
    
    Args:
        task_id: 任务ID
    
    Returns:
        str: 文件路径
    """
    # 占位符实现
    import time
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    return f"/workspace/can/{task_id}_signals_{timestamp}.txt"


def check_remaining_verify_steps(action_sequence: list, current_index: int, task_id: str) -> bool:
    """
    检查是否还有后续验证步骤 - 模板函数包装器
    
    Args:
        action_sequence: 动作序列
        current_index: 当前索引
        task_id: 任务ID
    
    Returns:
        bool: 是否还有后续验证步骤
    """
    # 占位符实现
    for i in range(current_index + 1, len(action_sequence)):
        step = action_sequence[i]
        if (step.get('source_task_id') == task_id and 
            step.get('verify_after') == True):
            return True
    return False


def is_can_capture_running(task_id: str) -> bool:
    """
    检查CAN采集是否正在运行 - 模板函数包装器
    
    Args:
        task_id: 任务ID
    
    Returns:
        bool: 是否正在运行
    """
    # 占位符实现
    return False


def get_can_capture_status(task_id: str) -> dict:
    """
    获取CAN采集状态 - 模板函数包装器
    
    Args:
        task_id: 任务ID
    
    Returns:
        dict: 状态信息
    """
    # 占位符实现
    return {
        'running': False,
        'task_id': task_id
    }


def register_custom_functions(env):
    """注册自定义函数到Jinja2环境"""
    functions = get_template_functions()
    for name, func in functions.items():
        env.globals[name] = func
    
    # 注册基础类型转换函数
    env.globals['str'] = str
    env.globals['int'] = int
    env.globals['float'] = float
    env.globals['bool'] = bool
    env.globals['list'] = list
    env.globals['dict'] = dict