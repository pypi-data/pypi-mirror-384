"""
自定义Jinja2模板过滤器
为脚本生成提供专用的过滤器功能
"""

import re
import json
import base64
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import quote, unquote


def escape_python_string(value: str) -> str:
    """转义Python字符串中的特殊字符"""
    if not isinstance(value, str):
        value = str(value)
    
    # 转义特殊字符
    value = value.replace('\\', '\\\\')  # 反斜杠
    value = value.replace('"', '\\"')    # 双引号
    value = value.replace("'", "\\'")    # 单引号
    value = value.replace('\n', '\\n')   # 换行符
    value = value.replace('\r', '\\r')   # 回车符
    value = value.replace('\t', '\\t')   # 制表符
    
    return value


def escape_path_for_python(path: str) -> str:
    """专门用于转义路径字符串，使其在Python代码中安全使用"""
    if not isinstance(path, str):
        path = str(path)
    
    # 将反斜杠转换为正斜杠（跨平台兼容）或转义反斜杠
    # Python的Path类可以处理正斜杠，这是最安全的方法
    path = path.replace('\\', '/')
    
    # 转义其他特殊字符
    path = path.replace('"', '\\"')    # 双引号
    path = path.replace("'", "\\'")    # 单引号
    
    return path


def format_coordinates(x: Union[int, float], y: Union[int, float], precision: int = 2) -> str:
    """格式化坐标为字符串"""
    if isinstance(x, float) and isinstance(y, float):
        return f"({x:.{precision}f}, {y:.{precision}f})"
    else:
        return f"({int(x)}, {int(y)})"


def format_duration(seconds: Union[int, float]) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


def snake_to_camel(snake_str: str) -> str:
    """将蛇形命名转换为驼峰命名"""
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """将驼峰命名转换为蛇形命名"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def slugify(value: str) -> str:
    """将字符串转换为URL友好的slug格式"""
    # 转换为小写
    value = value.lower()
    # 替换空格和特殊字符为连字符
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[-\s]+', '-', value)
    # 去除首尾连字符
    return value.strip('-')


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """截断文本并添加后缀"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def indent_text(text: str, indent: int = 4, first_line: bool = True) -> str:
    """为文本添加缩进"""
    lines = text.split('\n')
    indent_str = ' ' * indent
    
    if first_line:
        return '\n'.join(indent_str + line for line in lines)
    else:
        if lines:
            return lines[0] + '\n' + '\n'.join(indent_str + line for line in lines[1:])
        return text


def wrap_text(text: str, width: int = 80) -> str:
    """文本换行"""
    import textwrap
    return '\n'.join(textwrap.wrap(text, width=width))


def extract_numbers(text: str) -> List[float]:
    """从文本中提取所有数字"""
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]


def extract_coordinates(text: str) -> Optional[Dict[str, float]]:
    """从文本中提取坐标信息"""
    # 匹配 (x, y) 格式
    pattern = r'\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?'
    match = re.search(pattern, text)
    
    if match:
        return {
            'x': float(match.group(1)),
            'y': float(match.group(2))
        }
    return None


def validate_url(url: str) -> bool:
    """验证URL格式"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def format_json_compact(value: Any) -> str:
    """紧凑格式的JSON序列化"""
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False, default=str)


def format_json_pretty(value: Any, indent: int = 2) -> str:
    """美化格式的JSON序列化"""
    return json.dumps(value, indent=indent, ensure_ascii=False, default=str)


def base64_encode(value: Union[str, bytes]) -> str:
    """Base64编码"""
    if isinstance(value, str):
        value = value.encode('utf-8')
    return base64.b64encode(value).decode('ascii')


def base64_decode(value: str) -> str:
    """Base64解码"""
    try:
        return base64.b64decode(value).decode('utf-8')
    except Exception:
        return value


def url_encode(value: str) -> str:
    """URL编码"""
    return quote(value, safe='')


def url_decode(value: str) -> str:
    """URL解码"""
    return unquote(value)


def hash_md5(value: str) -> str:
    """计算MD5哈希"""
    return hashlib.md5(value.encode('utf-8')).hexdigest()


def hash_sha256(value: str) -> str:
    """计算SHA256哈希"""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lstrip('.')


def file_basename(filepath: str) -> str:
    """获取文件基础名（不含扩展名）"""
    return Path(filepath).stem


def path_join(*parts) -> str:
    """路径拼接"""
    return str(Path(*parts))


def path_normalize(path: str) -> str:
    """路径规范化"""
    return str(Path(path).resolve())


def relative_time(timestamp: Union[datetime, float, int]) -> str:
    """相对时间格式化"""
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"


def format_percentage(value: Union[int, float], decimal_places: int = 1) -> str:
    """格式化百分比"""
    return f"{value:.{decimal_places}f}%"


def list_chunk(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def dict_get_nested(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """获取嵌套字典的值"""
    keys = key_path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def list_unique(lst: List[Any]) -> List[Any]:
    """去重列表（保持顺序）"""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def string_contains_any(text: str, patterns: List[str], case_sensitive: bool = False) -> bool:
    """检查字符串是否包含任意一个模式"""
    if not case_sensitive:
        text = text.lower()
        patterns = [p.lower() for p in patterns]
    
    return any(pattern in text for pattern in patterns)


def string_matches_pattern(text: str, pattern: str) -> bool:
    """检查字符串是否匹配正则表达式模式"""
    try:
        return bool(re.search(pattern, text))
    except re.error:
        return False


def format_step_name(step_name: str, max_length: int = 30) -> str:
    """格式化步骤名称，确保长度适中"""
    if len(step_name) <= max_length:
        return step_name
    
    # 尝试在空格处截断
    if ' ' in step_name:
        words = step_name.split(' ')
        result = words[0]
        for word in words[1:]:
            if len(result + ' ' + word) <= max_length - 3:
                result += ' ' + word
            else:
                break
        return result + '...'
    else:
        return step_name[:max_length - 3] + '...'


def format_action_type(action_type: str) -> str:
    """格式化动作类型显示名称"""
    type_mapping = {
        'click': '点击',
        'tap': '点击',
        'long_click': '长按',
        'double_click': '双击',
        'type': '输入',
        'input': '输入',
        'swipe': '滑动',
        'scroll': '滚动',
        'drag': '拖拽',
        'key': '按键',
        'wait': '等待',
        'app': '应用操作',
        'manual': '手动操作'
    }
    return type_mapping.get(action_type.lower(), action_type)


def format_checkpoint_status(is_pass: Optional[bool]) -> str:
    """格式化检查点状态"""
    if is_pass is True:
        return "通过"
    elif is_pass is False:
        return "失败"
    else:
        return "等待"


def to_python_dict(value: Any) -> str:
    """
    将Python对象转换为Python字典字符串，确保null值被转换为None，布尔值正确转换
    这是为了解决tojson过滤器产生的null值在Python中未定义的问题
    """
    # 先转换为JSON字符串
    json_str = json.dumps(value, ensure_ascii=False, default=str)
    
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


def get_template_filters() -> Dict[str, Any]:
    """获取所有自定义过滤器"""
    return {
        # 字符串处理
        'escape_python_string': escape_python_string,
        'escape_path_for_python': escape_path_for_python,
        'snake_to_camel': snake_to_camel,
        'camel_to_snake': camel_to_snake,
        'slugify': slugify,
        'truncate_text': truncate_text,
        'indent_text': indent_text,
        'wrap_text': wrap_text,
        
        # 格式化
        'format_coordinates': format_coordinates,
        'format_duration': format_duration,
        'format_file_size': format_file_size,
        'format_percentage': format_percentage,
        'format_step_name': format_step_name,
        'format_action_type': format_action_type,
        'format_checkpoint_status': format_checkpoint_status,
        
        # 数据提取
        'extract_numbers': extract_numbers,
        'extract_coordinates': extract_coordinates,
        
        # 验证
        'validate_url': validate_url,
        
        # JSON处理
        'format_json_compact': format_json_compact,
        'format_json_pretty': format_json_pretty,
        'to_python_dict': to_python_dict,  # Python字典转换
        
        # 编码解码
        'base64_encode': base64_encode,
        'base64_decode': base64_decode,
        'url_encode': url_encode,
        'url_decode': url_decode,
        
        # 哈希
        'hash_md5': hash_md5,
        'hash_sha256': hash_sha256,
        
        # 文件路径
        'file_extension': file_extension,
        'file_basename': file_basename,
        'path_join': path_join,
        'path_normalize': path_normalize,
        
        # 时间
        'relative_time': relative_time,
        
        # 列表和字典
        'list_chunk': list_chunk,
        'list_unique': list_unique,
        'dict_get_nested': dict_get_nested,
        
        # 字符串匹配
        'string_contains_any': string_contains_any,
        'string_matches_pattern': string_matches_pattern,
    }


def register_custom_filters(env):
    """注册自定义过滤器到Jinja2环境"""
    filters = get_template_filters()
    for name, filter_func in filters.items():
        env.filters[name] = filter_func
    
    # 注册Python字典转换过滤器
    env.filters['to_python_dict'] = to_python_dict
    
    # 注册string过滤器，用于字符串转换
    env.filters['string'] = str