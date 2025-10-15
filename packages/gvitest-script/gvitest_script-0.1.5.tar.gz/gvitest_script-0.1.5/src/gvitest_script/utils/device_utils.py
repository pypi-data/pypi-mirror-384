"""
设备操作工具函数
从现有的script_utils.py迁移而来，提供设备操作和ADB相关功能
"""

import json
import logging
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def run_adb_command(command: str, device_serial: Optional[str] = None, timeout: int = 15) -> str:
    """
    运行ADB命令并返回结果
    
    Args:
        command: ADB命令（不包含"adb"前缀）
        device_serial: 设备序列号，如果为None则使用默认设备
        timeout: 命令超时时间（秒）
        
    Returns:
        str: 命令执行结果
        
    Raises:
        ConnectionAbortedError: 设备连接错误
        ValueError: 多设备错误
        TimeoutError: 命令超时
        RuntimeError: 其他执行错误
    """
    if device_serial:
        full_command = f"adb -s {device_serial} {command}"
    else:
        full_command = f"adb {command}"

    # 检查是否为复杂命令（包含管道操作）
    is_complex_command = "|" in command and ("grep" in command or "find" in command)

    try:
        logger.info(f"执行ADB命令: {full_command}")
        
        if is_complex_command:
            # 复杂命令使用shell=True
            result = subprocess.check_output(
                full_command, 
                shell=True, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=timeout
            )
        elif sys.platform != "win32":
            # Unix系统使用shlex分割
            result = subprocess.check_output(
                shlex.split(full_command), 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=timeout
            )
        else:
            # Windows系统使用shell=True
            result = subprocess.check_output(
                full_command, 
                shell=True, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=timeout
            )
        
        logger.debug(f"ADB命令执行成功: {result.strip()[:100]}...")
        return result.strip()
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e.output)
        
        if "device not found" in str(error_msg) or "no devices/emulators found" in str(error_msg):
            error = f"ADB设备连接错误: 找不到设备 {device_serial}"
            logger.error(error)
            raise ConnectionAbortedError(error) from e
        elif "device offline" in str(error_msg):
            error = f"ADB设备离线: {device_serial}"
            logger.error(error)
            raise ConnectionAbortedError(error) from e
        elif "more than one device/emulator" in str(error_msg):
            error = "发现多个设备，请指定device_serial参数"
            logger.error(error)
            raise ValueError(error) from e
        else:
            error = f"ADB命令执行失败 ({full_command}): {error_msg}"
            logger.error(error)
            raise RuntimeError(error) from e
            
    except subprocess.TimeoutExpired as e:
        error = f"ADB命令执行超时 ({full_command})"
        logger.error(error)
        raise TimeoutError(error) from e
        
    except Exception as e:
        error = f"ADB命令执行异常 ({full_command}): {str(e)}"
        logger.error(error)
        raise RuntimeError(error) from e


def wait_for_ui_stability(
    device, 
    timeout: float = 5.0, 
    check_interval: float = 0.5, 
    max_retries: int = 3, 
    retry_delay: float = 1.0
) -> bool:
    """
    等待UI稳定（通过比较连续截图检测）
    
    Args:
        device: uiautomator2设备对象
        timeout: 总超时时间（秒）
        check_interval: 检查间隔（秒）
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        
    Returns:
        bool: UI是否稳定
    """
    try:
        logger.info(f"等待UI稳定 (超时: {timeout}s, 间隔: {check_interval}s)")
        
        for retry in range(max_retries):
            try:
                start_time = time.time()
                previous_screenshot = None
                stable_count = 0
                required_stable_count = 2  # 需要连续2次相同才认为稳定
                
                while time.time() - start_time < timeout:
                    try:
                        # 获取当前截图
                        current_screenshot = device.screenshot()
                        
                        if current_screenshot is None:
                            logger.warning("截图为空，继续等待...")
                            time.sleep(check_interval)
                            continue
                        
                        # 与前一次截图比较
                        if previous_screenshot is not None:
                            # 简单的像素级比较
                            if _compare_screenshots(previous_screenshot, current_screenshot):
                                stable_count += 1
                                logger.debug(f"UI稳定计数: {stable_count}/{required_stable_count}")
                                
                                if stable_count >= required_stable_count:
                                    logger.info("UI已稳定")
                                    return True
                            else:
                                stable_count = 0
                                logger.debug("UI仍在变化，重置稳定计数")
                        
                        previous_screenshot = current_screenshot
                        time.sleep(check_interval)
                        
                    except Exception as inner_e:
                        logger.warning(f"UI稳定检查内部错误: {inner_e}")
                        time.sleep(check_interval)
                        continue
                
                logger.warning(f"UI稳定检查超时 (重试 {retry + 1}/{max_retries})")
                
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    
            except Exception as retry_e:
                logger.warning(f"UI稳定检查重试 {retry + 1} 失败: {retry_e}")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.warning("UI稳定检查最终失败")
        return False
        
    except Exception as e:
        logger.error(f"UI稳定检查异常: {e}")
        return False


def _compare_screenshots(img1, img2, threshold: float = 0.95) -> bool:
    """
    比较两个截图是否相似
    
    Args:
        img1: 第一个截图（PIL Image）
        img2: 第二个截图（PIL Image）
        threshold: 相似度阈值
        
    Returns:
        bool: 是否相似
    """
    try:
        # 转换为相同大小
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)
        
        # 简单的像素级比较
        import numpy as np
        
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # 计算相似度
        diff = np.abs(arr1.astype(float) - arr2.astype(float))
        similarity = 1 - (diff.mean() / 255.0)
        
        return similarity >= threshold
        
    except Exception as e:
        logger.warning(f"截图比较失败: {e}")
        return False


def check_text_input_state(
    device
) -> Dict[str, Union[bool, str]]:
    """
    检查文本输入状态
    
    Args:
        device: uiautomator2设备对象
        icon_path: 图标路径（保留兼容性，暂未使用）
        screenshot_path: 截图路径（保留兼容性，暂未使用）
        
    Returns:
        Dict: 输入状态信息
    """
    try:
        logger.info("检查文本输入状态...")
        
        # 获取当前焦点元素
        try:
            focused_element = device(focused=True)
            if focused_element.exists:
                element_info = focused_element.info
                logger.info(f"找到焦点元素: {element_info.get('className', 'Unknown')}")
                
                # 检查是否为输入元素
                class_name = element_info.get('className', '').lower()
                is_input_element = any(input_class in class_name for input_class in [
                    'edittext', 'textfield', 'input', 'textview'
                ])
                
                if is_input_element and element_info.get('focusable', False):
                    return {
                        "is_input_active": True,
                        "has_input_field": True,
                        "details": f"输入框已激活: {class_name}",
                        "element_info": element_info
                    }
        except Exception as focus_e:
            logger.debug(f"获取焦点元素失败: {focus_e}")
        
        # 检查是否有可编辑的元素
        try:
            editable_elements = device(editable=True)
            if editable_elements.exists:
                logger.info("找到可编辑元素")
                return {
                    "is_input_active": False,
                    "has_input_field": True,
                    "details": "发现可编辑元素但未激活",
                    "element_count": len(editable_elements)
                }
        except Exception as edit_e:
            logger.debug(f"查找可编辑元素失败: {edit_e}")
        
        # 检查软键盘状态
        try:
            # 通过检查屏幕高度变化来判断软键盘状态
            info = device.info
            display_height = info.get('displayHeight', 0)
            
            # 获取当前窗口信息
            window_info = device.window_size()
            current_height = window_info[1] if window_info else display_height
            
            # 如果当前高度明显小于显示高度，可能软键盘已打开
            height_ratio = current_height / display_height if display_height > 0 else 1
            
            if height_ratio < 0.8:  # 高度减少超过20%
                logger.info("检测到软键盘可能已打开")
                return {
                    "is_input_active": True,
                    "has_input_field": True,
                    "details": f"软键盘已打开 (高度比例: {height_ratio:.2f})",
                    "keyboard_detected": True
                }
                
        except Exception as keyboard_e:
            logger.debug(f"软键盘检测失败: {keyboard_e}")
        
        # 默认情况
        logger.info("未检测到激活的输入状态")
        return {
            "is_input_active": False,
            "has_input_field": False,
            "details": "未找到激活的输入框或软键盘",
            "keyboard_detected": False
        }
        
    except Exception as e:
        logger.error(f"检查文本输入状态失败: {e}")
        return {
            "is_input_active": False,
            "has_input_field": False,
            "details": f"检查失败: {str(e)}",
            "error": str(e)
        }


def get_device_info(device) -> Dict[str, Union[str, int, bool]]:
    """
    获取设备信息
    
    Args:
        device: uiautomator2设备对象
        
    Returns:
        Dict: 设备信息
    """
    try:
        info = device.info
        return {
            "device_serial": getattr(device, 'serial', 'unknown'),
            "display_width": info.get('displayWidth', 0),
            "display_height": info.get('displayHeight', 0),
            "display_rotation": info.get('displayRotation', 0),
            "screen_on": info.get('screenOn', False),
            "sdk_version": info.get('sdkInt', 0),
            "product_name": info.get('productName', 'unknown'),
            "model": info.get('model', 'unknown'),
            "brand": info.get('brand', 'unknown')
        }
    except Exception as e:
        logger.error(f"获取设备信息失败: {e}")
        return {"error": str(e)}


def ensure_device_awake(device) -> bool:
    """
    确保设备处于唤醒状态
    
    Args:
        device: uiautomator2设备对象
        
    Returns:
        bool: 是否成功唤醒
    """
    try:
        info = device.info
        if not info.get('screenOn', False):
            logger.info("设备屏幕已关闭，正在唤醒...")
            device.screen_on()
            time.sleep(1)
            
            # 检查是否需要解锁
            device.unlock()
            time.sleep(1)
            
            # 再次检查屏幕状态
            info = device.info
            if info.get('screenOn', False):
                logger.info("设备已成功唤醒")
                return True
            else:
                logger.warning("设备唤醒可能失败")
                return False
        else:
            logger.debug("设备屏幕已开启")
            return True
            
    except Exception as e:
        logger.error(f"唤醒设备失败: {e}")
        return False


def get_current_app_info(device) -> Dict[str, str]:
    """
    获取当前应用信息
    
    Args:
        device: uiautomator2设备对象
        
    Returns:
        Dict: 当前应用信息
    """
    try:
        app_info = device.app_current()
        return {
            "package": app_info.get('package', 'unknown'),
            "activity": app_info.get('activity', 'unknown'),
            "pid": str(app_info.get('pid', 0))
        }
    except Exception as e:
        logger.error(f"获取当前应用信息失败: {e}")
        return {"error": str(e)}


def wait_for_element(
    device, 
    selector: Dict[str, str], 
    timeout: float = 10.0, 
    check_interval: float = 0.5
) -> bool:
    """
    等待元素出现
    
    Args:
        device: uiautomator2设备对象
        selector: 元素选择器，如 {"text": "确定"} 或 {"resourceId": "com.example:id/button"}
        timeout: 超时时间（秒）
        check_interval: 检查间隔（秒）
        
    Returns:
        bool: 元素是否出现
    """
    try:
        logger.info(f"等待元素出现: {selector} (超时: {timeout}s)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                element = device(**selector)
                if element.exists:
                    logger.info(f"元素已出现: {selector}")
                    return True
            except Exception as check_e:
                logger.debug(f"元素检查失败: {check_e}")
            
            time.sleep(check_interval)
        
        logger.warning(f"元素等待超时: {selector}")
        return False
        
    except Exception as e:
        logger.error(f"等待元素异常: {e}")
        return False


# ========== 废弃函数警告 ==========

def check_tap_target(*args, **kwargs):
    """⚠️ 此函数已废弃，请使用locate_small_via_dynamic_medium替代"""
    import warnings
    warnings.warn(
        "check_tap_target() 已废弃。"
        "请使用 locate_small_via_dynamic_medium() 替代："
        "- 更智能的目标区域检测和验证"
        "- 支持动态缩放匹配，提高准确率"
        "- 统一的返回格式和错误处理",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("check_tap_target() 已由locate_small_via_dynamic_medium替代")


def save_action_sequence(*args, **kwargs):
    """⚠️ 此函数已废弃，请使用新的替代方案"""
    import warnings
    warnings.warn(
        "save_action_sequence() 已废弃。"
        "请使用以下替代方案："
        "1. 使用实时状态追踪进行状态保存"
        "2. 使用独立日志文件记录执行历史"
        "3. 使用预期结果验证系统保存验证数据",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("save_action_sequence() 功能已由新的实时追踪和日志系统替代")


def check_expected_checkpoint(*args, **kwargs):
    """⚠️ 此函数已废弃，请使用新的预期结果验证系统替代"""
    import warnings
    warnings.warn(
        "check_expected_checkpoint() 已废弃。"
        "新架构使用预期结果验证系统替代："
        "- 使用 ExpectedResult 数据模型定义预期结果"
        "- 支持 Agent/手动双模式验证"
        "- 通过 result_validation_v2.j2 模板自动化处理"
        "- 支持多种验证类型：image、text、camera"
        "- 注意：预期检查点概念已被预期结果概念替代",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("check_expected_checkpoint() 已由新的预期结果验证系统替代") 