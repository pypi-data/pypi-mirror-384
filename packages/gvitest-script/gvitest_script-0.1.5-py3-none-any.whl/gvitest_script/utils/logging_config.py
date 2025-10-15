#!/usr/bin/env python3
"""
日志配置模块 - 处理跨平台编码问题
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import atexit


def setup_cross_platform_logging(log_level: str = "INFO", log_file: str = "script_server.log"):
    """设置跨平台兼容的日志配置"""
    # Windows系统设置UTF-8编码
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        except:
            pass
    
    # 创建处理器
    handlers = [
        logging.StreamHandler(sys.stdout if sys.platform.startswith('win') else None),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )



def setup_safe_loguru_logging(
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = False,
    log_file: Optional[str] = None
) -> None:
    """设置安全的loguru日志配置，解决缓冲区分离问题"""
    try:
        from loguru import logger
        
        # 移除所有现有的处理器
        logger.remove()
        
        # 注册退出时的清理函数
        atexit.register(lambda: logger.remove() if logger else None)
        
        # 控制台输出
        if enable_console:
            logger.add(
                sys.stdout,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                enqueue=True, catch=True, backtrace=False, diagnose=False, serialize=False
            )
        
        # 文件输出
        if enable_file and log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                log_file,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation="10 MB", retention=5, compression="gz",
                enqueue=True, catch=True, backtrace=False, diagnose=False, serialize=False,
                encoding="utf-8"
            )
            
    except Exception:
        # 回退到标准logging
        setup_cross_platform_logging(log_level, log_file or "script_server.log")

def create_task_logger_config(task_id: str, workspace_root: Path, log_level: str = "INFO") -> Dict[str, Any]:
    """为特定任务创建安全的日志配置"""
    from datetime import datetime
    
    log_dir = workspace_root / task_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"script_{task_id}_{timestamp}.log"
    
    return {
        "log_file": str(log_file),
        "log_level": log_level,
        "enable_console": True,
        "enable_file": True,
        "rotation": "10 MB",
        "retention": 10,
        "compression": "gz",
        "enqueue": True,
        "catch": True
    }


def get_safe_emoji(emoji: str, fallback: str = "") -> str:
    """获取安全的emoji字符，在Windows系统上可能返回备用字符"""
    if sys.platform.startswith('win'):
        try:
            emoji.encode('utf-8')
            return emoji
        except UnicodeEncodeError:
            return fallback
    return emoji


# 预定义的安全emoji
SAFE_EMOJIS = {
    'success': get_safe_emoji('✅', '[OK]'),
    'error': get_safe_emoji('❌', '[ERROR]'),
    'warning': get_safe_emoji('⚠️', '[WARN]'),
    'info': get_safe_emoji('ℹ️', '[INFO]'),
    'debug': get_safe_emoji('🔍', '[DEBUG]'),
    'connect': get_safe_emoji('🔌', '[CONNECT]'),
    'disconnect': get_safe_emoji('🔌', '[DISCONNECT]'),
    'global': get_safe_emoji('🌍', '[GLOBAL]'),
    'rocket': get_safe_emoji('🚀', '[START]'),
    'target': get_safe_emoji('🎯', '[TARGET]'),
    'note': get_safe_emoji('📝', '[NOTE]'),
    'lightning': get_safe_emoji('⚡', '[FAST]'),
    'bulb': get_safe_emoji('💡', '[IDEA]'),
    'fire': get_safe_emoji('🔥', '[HOT]'),
    'check': get_safe_emoji('✅', '[PASS]'),
    'cross': get_safe_emoji('❌', '[FAIL]'),
} 