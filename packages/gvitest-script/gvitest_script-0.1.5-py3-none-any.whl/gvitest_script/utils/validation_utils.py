"""
验证工具函数
处理废弃的验证函数，提供迁移指导和替代方案
包含新的统一验证函数
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ========== 统一验证函数 ==========

def validate_validation_model(validation_model: Dict[str, Any], device=None, runner_dir=None, screenshot_count=0, can_file_path=None) -> Dict[str, Any]:
    """
    验证ValidationModel - 统一的验证模型处理函数（基于result_validation_v2.j2的验证算法）
    
    支持的验证类型：
    - image: 图像验证
    - text: 文本验证
    
    支持的数据源类型 (data_source)：
    - adb_screenshot: ADB截图
    - camera: 摄像头拍照

    支持的模式：
    - manual: 手动验证模式（默认）
    - agent: 智能代理验证模式
    
    Args:
        validation_model: 验证模型数据，包含以下字段：
            - id: 验证ID
            - mode: 验证模式 (agent/manual)
            - data_source: 数据源类型 (adb_screenshot/camera_photo/file/url/can_signal)  
            - validation_type: 验证类型 (image/text)
            - expect_exists: 是否期望存在
            - target_image_path: 目标图像路径（小图）
            - reference_image_path: 参考图像路径（大图）
            - target_text: 目标文本
            - target_bbox: 目标边界框 [x1, y1, x2, y2]
            - roi_coordinates: ROI坐标 [x1, y1, x2, y2]
            - wait_time: 等待时间
            - timeout: 超时时间
            - description: 验证描述
        device: uiautomator2设备对象（用于截图和UI操作）
        runner_dir: 运行目录（用于保存截图）
        screenshot_count: 截图计数
    
    Returns:
        Dict: 验证结果，包含：
            - is_pass: 验证是否通过
            - message: 验证消息
            - validation_type: 验证类型
            - data_source: 数据源类型
            - mode: 验证模式
            - details: 详细信息
            - validation_screenshot_path: 验证截图路径
            - target_image_path: 目标图像路径
            - reference_image_path: 参考图像路径
            - execution_duration: 执行时长
            - execution_timestamp: 执行时间戳
    """
    import time
    from datetime import datetime
    from pathlib import Path
    
    start_time = time.time()
    
    # 初始化验证结果数据
    result_data = {
        "id": validation_model.get("id", ""),
        "description": validation_model.get("description", ""),
        "mode": validation_model.get("mode", "manual"),
        "data_source": validation_model.get("data_source", "adb_screenshot"),
        "validation_type": validation_model.get("validation_type", "image"),
        "is_pass": False,
        "message": "",
        "details": "",
        "validation_screenshot_path": "",
        "target_image_path": "",
        "reference_image_path": "",
        "execution_timestamp": datetime.now().isoformat(),
        "execution_duration": 0
    }
    
    try:
        # 检查是否有预定义的验证结果（用于测试）
        if 'expected_result' in validation_model:
            expected_result = validation_model['expected_result']
            result_data.update({
                "is_pass": expected_result.get('is_pass', True),
                "message": expected_result.get('message', '预定义验证结果'),
                "execution_duration": round(time.time() - start_time, 3)
            })
            return result_data
        
        # 获取基本参数
        mode = validation_model.get('mode', 'manual')
        data_source = validation_model.get('data_source', 'adb_screenshot')
        validation_type = validation_model.get('validation_type', 'image')
        expect_exists = validation_model.get('expect_exists', True)
        
        logger.info(f"{'='*50}")
        logger.info(f"开始验证: {result_data['description']}")
        logger.info(f"验证ID: {result_data['id']}")
        logger.info(f"验证模式: {mode}")
        logger.info(f"数据来源: {data_source}")
        logger.info(f"验证类型: {validation_type}")
        logger.info(f"期望存在: {expect_exists}")
        logger.info(f"{'='*50}")
        
        # 统一验证处理 - Debug信息
        logger.info(f"🔧 [DEBUG] 验证分支判断:")
        logger.info(f"🔧 [DEBUG]   validation_type = '{validation_type}' (type: {type(validation_type)})")
        logger.info(f"🔧 [DEBUG]   data_source = '{data_source}' (type: {type(data_source)})")
        logger.info(f"🔧 [DEBUG]   条件1: validation_type == 'signal' = {validation_type == 'signal'}")
        logger.info(f"🔧 [DEBUG]   条件2: data_source == 'can_signal' = {data_source == 'can_signal'}")
        logger.info(f"🔧 [DEBUG]   整体条件: {validation_type == 'signal' and data_source == 'can_signal'}")
        
        if validation_type == 'signal' and data_source == 'can_signal':
            # CAN 信号验证
            logger.info("🚗 [DEBUG] 进入CAN信号验证分支 (_validate_can_signal)")
            result_data = _validate_can_signal(validation_model, result_data, can_file_path)
        else:
            # 传统的图像/文本验证
            logger.info("📱 [DEBUG] 进入传统验证分支 (_execute_validation)")
            result_data = _execute_validation(validation_model, result_data, device, runner_dir, screenshot_count, can_file_path)
        
    except Exception as validation_error:
        result_data.update({
            "is_pass": False,
            "message": f"验证过程出错: {validation_error}",
            "details": str(validation_error)
        })
        logger.error(f"验证异常: {validation_error}")
    
    # 设置执行时长
    result_data["execution_duration"] = round(time.time() - start_time, 3)
    
    # 输出验证结果
    result_status = "[PASS]" if result_data['is_pass'] else "[FAIL]"
    logger.info(f"{result_status} {result_data['message']}")
    
    return result_data


def _validate_can_signal(validation_model: Dict[str, Any], result_data: Dict[str, Any], can_file_path: str = None) -> Dict[str, Any]:
    """
    CAN 信号验证函数 - 实际调用 judge_signal 进行验证
    
    Args:
        validation_model: 验证模型数据
        result_data: 结果数据
        can_file_path: CAN信号文件路径
        
    Returns:
        Dict: 更新后的结果数据
    """
    try:
        # 获取 CAN 验证参数
        can_title = validation_model.get('can_title')
        can_values = validation_model.get('can_values', [])
        condition_id = validation_model.get('id', 'can_condition')
        
        if not can_title:
            result_data.update({
                "is_pass": False,
                "message": "CAN 验证失败：缺少 can_title",
                "details": "CAN 信号验证需要指定信号名称"
            })
            return result_data
        
        if not can_values:
            result_data.update({
                "is_pass": False,
                "message": "CAN 验证失败：缺少 can_values",
                "details": "CAN 信号验证需要指定验证规则"
            })
            return result_data
        
        if not can_file_path:
            result_data.update({
                "is_pass": False,
                "message": "CAN 验证失败：缺少信号文件路径",
                "details": "CAN 信号验证需要信号文件路径"
            })
            return result_data
        
        # 调用 judge_signal 进行实际验证
        from src.utils.can_utils import judge_signal
        
        # 构造 judge_signal 需要的格式
        target_signals = [{
            "title": can_title,
            "values": can_values,
            "logic_id": condition_id
        }]
        
        logger.info(f"🚗 开始CAN信号验证: {can_title}")
        logger.info(f"  信号文件: {can_file_path}")
        logger.info(f"  验证规则: {can_values}")
        
        # 调用 judge_signal 函数
        judge_results = judge_signal(target_signals, can_file_path)
        
        # 解析验证结果
        if judge_results and len(judge_results) > 0:
            judge_result = judge_results[0]
            is_pass = judge_result.get('is_pass', False)
            
            result_data.update({
                "is_pass": is_pass,
                "message": f"CAN 信号验证{'通过' if is_pass else '失败'}: {can_title}",
                "details": f"信号名称: {can_title}, 验证规则: {len(can_values)}个, 结果: {'通过' if is_pass else '失败'}",
                "can_title": can_title,
                "can_values": can_values,
                "can_file_path": can_file_path
            })
            
            logger.info(f"✅ CAN信号验证完成: {can_title} -> {'通过' if is_pass else '失败'}")
        else:
            result_data.update({
                "is_pass": False,
                "message": f"CAN 信号验证失败: {can_title}",
                "details": "judge_signal 返回空结果"
            })
            logger.error(f"❌ CAN信号验证失败: judge_signal 返回空结果")
        
    except Exception as e:
        logger.error(f"CAN 信号验证异常: {e}")
        result_data.update({
            "is_pass": False,
            "message": f"CAN 验证异常: {str(e)}",
            "details": str(e)
        })
    
    return result_data


def _execute_validation(validation_model: Dict[str, Any], result_data: Dict[str, Any], device, runner_dir, screenshot_count, can_file_path: str = None) -> Dict[str, Any]:
    """
    统一验证执行函数 - 支持Agent和Manual两种模式
    """
    from pathlib import Path
    from src.utils.image_utils import take_screenshot_and_save, locate_small_via_dynamic_medium, extract_screen_from_camera_image
    import requests
    
    mode = validation_model.get('mode', 'manual')
    data_source = validation_model.get('data_source', 'adb_screenshot')
    validation_type = validation_model.get('validation_type', 'image')
    
    # Agent模式的特殊处理
    if mode == 'agent':
        # Agent模式固定使用ADB截图
        data_source = 'adb_screenshot'
        # Agent模式需要device和runner_dir
        if not device or not runner_dir:
            result_data.update({
                "is_pass": False,
                "message": f"{mode.title()}模式需要device和runner_dir参数",
                "details": "缺少必要的设备或目录参数"
            })
            return result_data
    
    mode_prefix = f"[{mode.upper()}]" if mode == 'agent' else ""
    logger.info(f"{mode_prefix} {mode.title()}模式验证 - 数据来源: {data_source}, 验证类型: {validation_type}")
    
    try:
        # 根据验证类型进行不同的处理
        logger.info(f"🔧 [DEBUG] _execute_validation 验证类型判断:")
        logger.info(f"🔧 [DEBUG]   validation_type = '{validation_type}' (type: {type(validation_type)})")
        logger.info(f"🔧 [DEBUG]   支持的类型: ['image', 'text', 'can']")
        
        if validation_type == 'image':
            # 图像验证需要先获取数据来源
            source_image_path = _get_data_source(validation_model, result_data, device, runner_dir, screenshot_count, mode)
            
            if source_image_path:
                result_data["validation_screenshot_path"] = source_image_path
                result_data = _validate_image(validation_model, result_data, source_image_path, mode)
            else:
                result_data.update({
                    "is_pass": False,
                    "message": f"{mode.title()}模式数据来源获取失败: {data_source}",
                    "details": "无法获取数据源图像"
                })
                
        elif validation_type == 'text':
            # 文本验证处理
            source_image_path = None
            
            # 如果需要截图（Agent模式或Manual模式的ADB数据源）
            if (mode == 'agent') or (mode == 'manual' and data_source == 'adb_screenshot' and device and runner_dir):
                try:
                    source_image_path = _get_data_source(validation_model, result_data, device, runner_dir, screenshot_count, mode)
                    if source_image_path:
                        result_data["validation_screenshot_path"] = source_image_path
                except Exception as e:
                    logger.warning(f"获取数据源失败，但文本验证可以继续: {e}")
            
            # 执行文本验证
            result_data = _validate_text(validation_model, result_data, source_image_path, device, mode)
            

        else:
            result_data.update({
                "is_pass": False,
                "message": f"{mode.title()}模式不支持的验证类型: {validation_type}",
                "details": f"支持的验证类型: image, text"
            })
            logger.error(f"{mode.title()}模式不支持的验证类型: {validation_type}")
    
    except Exception as e:
        result_data.update({
            "is_pass": False,
            "message": f"{mode.title()}模式验证异常",
            "details": str(e)
        })
        logger.error(f"{mode.title()}模式验证异常: {e}")
    
    return result_data


def _get_data_source(validation_model: Dict[str, Any], result_data: Dict[str, Any], device, runner_dir, screenshot_count, mode: str = 'manual') -> str:
    """
    获取数据源图像路径（基于result_validation_v2.j2的数据源获取逻辑）
    """
    from pathlib import Path
    from src.utils.image_utils import take_screenshot_and_save, extract_screen_from_camera_image
    import requests
    
    data_source = validation_model.get('data_source', 'adb_screenshot')
    source_image_path = None
    
    if data_source == 'adb_screenshot':
        # 使用ADB截图作为数据来源
        mode_label = f"[{mode.upper()}]" if mode == 'agent' else "[ADB]"
        logger.info(f"{mode_label} 开始ADB截图获取...")
        source_image_path = take_screenshot_and_save(
            device, runner_dir, screenshot_count, f"validation_{mode}_adb_{result_data['id']}"
        )
        if source_image_path:
            logger.info(f"[SUCCESS] ADB截图成功: {source_image_path}")
        else:
            logger.error("[ERROR] ADB截图失败")
            
    elif data_source == 'camera_photo':
        # 使用摄像头拍照作为数据来源
        logger.info("[CAMERA] 开始摄像头拍照获取...")
        logger.info("   [API] 调用摄像头服务: http://localhost:8082/v1/device/get_camera_image")
        try:
            response = requests.post(
                "http://localhost:8082/v1/device/get_camera_image",
                json={"picture_name": f"validation_camera_{result_data['id']}"},
                timeout=30
            )
            
            if response.status_code == 200:
                camera_result = response.json()
                if camera_result.get("status") == "success" and "local_path" in camera_result:
                    local_path = camera_result["local_path"]
                    if Path(local_path).exists():
                        logger.info(f"[SUCCESS] 摄像头拍照成功: {local_path}")
                        
                        # 摄像头图像处理逻辑：根据ROI参数决定是否进行屏幕检测
                        roi_coordinates = validation_model.get('roi_coordinates')
                        if roi_coordinates:
                            # 有ROI坐标，不进行屏幕检测，直接使用原始图像
                            source_image_path = local_path
                            logger.info("[ROI_MODE] 检测到ROI坐标，跳过屏幕检测，直接使用原始摄像头图像")
                            logger.info(f"   [ROI] 感兴趣区域: {roi_coordinates}")
                        else:
                            # 没有ROI坐标，进行屏幕检测
                            logger.info("[SCREEN_EXTRACT] 未设置ROI坐标，开始从摄像头图像中提取屏幕区域...")
                            screen_extract_path = str(Path(local_path).parent / f"screen_extracted_{result_data['id']}.png")
                            
                            try:
                                screen_result = extract_screen_from_camera_image(local_path, screen_extract_path)
                                
                                if screen_result:
                                    extracted_screen_path, screen_bbox = screen_result
                                    source_image_path = extracted_screen_path
                                    logger.info(f"[SUCCESS] 屏幕提取成功: {extracted_screen_path}")
                                    logger.info(f"   [BBOX] 屏幕边界框: {screen_bbox}")
                                else:
                                    # 屏幕提取失败，使用原始图像
                                    source_image_path = local_path
                                    logger.warning("[FALLBACK] 屏幕提取失败，使用原始摄像头图像")
                                    
                            except Exception as extract_error:
                                # 屏幕提取出错，使用原始图像
                                source_image_path = local_path
                                logger.error(f"[ERROR] 屏幕提取出错: {extract_error}")
                                logger.info("[FALLBACK] 屏幕提取出错，使用原始摄像头图像")
                    else:
                        logger.error(f"[ERROR] 摄像头图像文件不存在: {local_path}")
                else:
                    logger.error(f"[ERROR] 摄像头接口调用失败: {camera_result}")
            else:
                logger.error(f"[ERROR] 摄像头接口请求失败: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"[ERROR] 摄像头拍照异常: {e}")
    else:
        # 未知数据来源
        logger.error(f"未支持的数据来源: {data_source}")
    
    return source_image_path


def _validate_image(validation_model: Dict[str, Any], result_data: Dict[str, Any], source_image_path: str, mode: str = 'manual') -> Dict[str, Any]:
    """
    统一图像验证（支持Agent和Manual模式）
    """
    from src.utils.image_utils import locate_small_via_dynamic_medium
    
    target_image_path = validation_model.get('target_image_path')
    reference_image_path = validation_model.get('reference_image_path')
    target_bbox = validation_model.get('target_bbox')
    
    if target_image_path and reference_image_path and target_bbox:
        result_data["target_image_path"] = target_image_path
        result_data["reference_image_path"] = reference_image_path
        
        # 根据数据源类型设置不同的相似度阈值
        data_source = validation_model.get('data_source', 'adb_screenshot')
        if data_source == 'camera_photo':
            similarity_threshold = 0.5  # 摄像头图像使用较低阈值
            data_source_type = "摄像头"
        else:
            similarity_threshold = 0.8  # ADB截图使用较高阈值
            data_source_type = "ADB截图"
        
        # 打印图像路径信息
        logger.info(f"[IMAGES] {mode.title()}模式图像路径信息:")
        logger.info(f"  [TARGET] 目标图像(小图): {target_image_path}")
        logger.info(f"  [REFERENCE] 参考图像(大图): {reference_image_path}")
        logger.info(f"  [SOURCE] 数据来源图像: {source_image_path}")
        logger.info(f"  [BBOX] 目标坐标: {target_bbox}")
        logger.info(f"  [THRESHOLD] 相似度阈值: {similarity_threshold} (数据源: {data_source_type})")
        
        roi_coordinates = validation_model.get('roi_coordinates')
        
        # ROI坐标保护机制（基本验证，详细验证在 locate_small_via_dynamic_medium 中进行）
        if roi_coordinates is not None:
            logger.info(f"  [ROI] 原始ROI坐标: {roi_coordinates}")
            
            # 检查是否为4个元素的列表/元组
            if not isinstance(roi_coordinates, (list, tuple)) or len(roi_coordinates) != 4:
                logger.warning(f"ROI坐标格式无效: {roi_coordinates} (需要4个数值的列表或元组)，将使用全图")
                roi_coordinates = None
            else:
                # 基本验证（详细边界检查在 locate_small_via_dynamic_medium 中进行）
                roi_x1, roi_y1, roi_x2, roi_y2 = roi_coordinates
                validation_errors = []
                
                # 检查数据类型
                if not all(isinstance(x, (int, float)) for x in roi_coordinates):
                    validation_errors.append("坐标值必须是数字类型")
                
                # 检查坐标逻辑关系
                if roi_x1 >= roi_x2:
                    validation_errors.append(f"x1({roi_x1:.2f}) >= x2({roi_x2:.2f})")
                if roi_y1 >= roi_y2:
                    validation_errors.append(f"y1({roi_y1:.2f}) >= y2({roi_y2:.2f})")
                
                # 检查负值
                if roi_x1 < 0:
                    validation_errors.append(f"x1({roi_x1:.2f}) < 0")
                if roi_y1 < 0:
                    validation_errors.append(f"y1({roi_y1:.2f}) < 0")
                
                if validation_errors:
                    logger.warning(f"ROI坐标基本验证失败: {'; '.join(validation_errors)}，将使用全图")
                    roi_coordinates = None
                else:
                    logger.info(f"  [ROI] 坐标基本验证通过: x1={roi_x1:.2f}, y1={roi_y1:.2f}, x2={roi_x2:.2f}, y2={roi_y2:.2f}")
        
        if roi_coordinates:
            logger.info(f"  [ROI] 感兴趣区域: {roi_coordinates}")
        else:
            logger.info(f"  [ROI] 全图检测模式")
        
        logger.info(f"开始{mode.title()}模式图像验证: 阈值={similarity_threshold}")
        
        # 使用locate_small_via_dynamic_medium进行智能定位
        try:
            detection_result = locate_small_via_dynamic_medium(
                reference_image_data=reference_image_path,  # 历史参考图路径
                target_image_data=target_image_path,        # 目标图像路径
                target_bbox=target_bbox,                    # 目标边界框 [x1, y1, x2, y2]
                detect_image_data=source_image_path,        # 当前数据来源图路径
                roi_coordinates=roi_coordinates,            # ROI区域坐标
                threshold=similarity_threshold              # 动态阈值
            )
            
            expect_exists = validation_model.get('expect_exists', True)
            
            if detection_result:
                # 检测到目标
                x1, y1, x2, y2 = detection_result
                if expect_exists:
                    result_data.update({
                        "is_pass": True,
                        "message": f"{mode.title()}模式图像智能定位成功",
                        "details": f"位置({x1}, {y1}, {x2}, {y2}) - 符合期望存在"
                    })
                else:
                    result_data.update({
                        "is_pass": False,
                        "message": f"{mode.title()}模式图像智能定位成功",
                        "details": f"位置({x1}, {y1}, {x2}, {y2}) - 但期望不存在，验证失败"
                    })
            else:
                # 未检测到目标
                if expect_exists:
                    result_data.update({
                        "is_pass": False,
                        "message": f"{mode.title()}模式图像验证失败",
                        "details": "智能定位失败 - 期望存在但未找到"
                    })
                else:
                    result_data.update({
                        "is_pass": True,
                        "message": f"{mode.title()}模式图像验证成功",
                        "details": "未检测到目标 - 符合期望不存在"
                    })
            
        except Exception as detection_error:
            result_data.update({
                "is_pass": False,
                "message": f"{mode.title()}模式图像检测出错",
                "details": str(detection_error)
            })
    else:
        result_data.update({
            "is_pass": False,
            "message": f"{mode.title()}模式图像验证缺少必要配置",
            "details": "需要target_image_path, reference_image_path, target_bbox"
        })
    
    return result_data


def _validate_text(validation_model: Dict[str, Any], result_data: Dict[str, Any], source_image_path: str, device, mode: str = 'manual') -> Dict[str, Any]:
    """
    统一文本验证（支持Agent和Manual模式）
    """
    target_text = validation_model.get('target_text')
    
    if target_text:
        mode_prefix = f"[{mode.upper()}]" if mode == 'agent' else ""
        logger.info(f"{mode_prefix} 开始{mode.title()}模式文本验证: 目标文本='{target_text}'")
        
        text_found = False
        found_methods = []
        
        # 方法1: 屏幕元素检测
        try:
            if device:
                ui_dump = device.dump_hierarchy()
                if ui_dump and target_text in ui_dump:
                    text_found = True
                    found_methods.append("元素检测")
                    logger.info(f"{mode_prefix} 通过屏幕元素检测找到文本: '{target_text}'")
        except Exception as element_error:
            logger.warning(f"屏幕元素检测失败: {element_error}")
        
        # 方法2: OCR识别（如果元素检测失败）
        if not text_found:
            try:
                # TODO: 实现OCR文本识别功能
                # 这里先使用简单的屏幕文本检测模拟
                logger.warning(f"{mode_prefix} OCR功能待实现，当前使用屏幕元素检测模拟")
                # 可以集成 pytesseract 或其他OCR库
                # ocr_text = extract_text_from_image(source_image_path)
                # if target_text in ocr_text:
                #     text_found = True
                #     found_methods.append("OCR识别")
            except Exception as ocr_error:
                logger.warning(f"OCR识别失败: {ocr_error}")
        
        expect_exists = validation_model.get('expect_exists', True)
        
        # 根据期望存在和实际检测结果判断验证结果（完全按照模板逻辑）
        if expect_exists:
            # 期望存在
            result_data["is_pass"] = text_found
            if text_found:
                result_data["details"] = f"{mode.title()}模式文本验证成功: 通过{', '.join(found_methods)}找到'{target_text}' - 符合期望存在"
            else:
                result_data["details"] = f"{mode.title()}模式文本验证失败: 未找到'{target_text}' - 期望存在但未找到"
        else:
            # 期望不存在
            result_data["is_pass"] = not text_found
            if text_found:
                result_data["details"] = f"{mode.title()}模式文本验证失败: 通过{', '.join(found_methods)}找到'{target_text}' - 但期望不存在"
            else:
                result_data["details"] = f"{mode.title()}模式文本验证成功: 未找到'{target_text}' - 符合期望不存在"
        
        # 设置统一的message
        result_data["message"] = f"{mode.title()}模式文本验证成功" if result_data["is_pass"] else f"{mode.title()}模式文本验证失败"
        
    else:
        result_data["is_pass"] = False
        result_data["details"] = f"{mode.title()}模式文本验证缺少必要配置: target_text"
        result_data["message"] = f"{mode.title()}模式文本验证缺少必要配置"
    
    return result_data

