"""
图像处理工具函数
从现有的script_utils.py和image_utils.py迁移而来，提供图像处理和比较功能
"""

import base64
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


def compare_images_ssim(img1_path: Union[str, Path], img2_path: Union[str, Path]) -> float:
    """
    计算两张图片的结构相似度 (SSIM)
    
    Args:
        img1_path: 第一张图片路径
        img2_path: 第二张图片路径
        
    Returns:
        float: 相似度分数 (0.0-1.0)
        
    Raises:
        ValueError: 如果图片加载失败
    """
    try:
        img1 = cv2.imread(str(img1_path), cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(str(img2_path), cv2.IMREAD_GRAYSCALE)

        if img1 is None:
            raise ValueError(f"无法加载图像1: {img1_path}")
        if img2 is None:
            raise ValueError(f"无法加载图像2: {img2_path}")

        # 如果尺寸不匹配，调整第二张图片的尺寸
        if img1.shape != img2.shape:
            logger.warning(f"图像尺寸不匹配，将调整图像2尺寸从 {img2.shape} 到 {img1.shape}")
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # 计算SSIM
        score, _ = ssim(img1, img2, full=True, data_range=img1.max() - img1.min())
        return float(score)
        
    except Exception as e:
        logger.error(f"计算图像相似度失败: {img1_path} vs {img2_path}, 错误: {e}")
        raise


def take_screenshot(device, save_path: Union[str, Path]) -> Dict[str, Union[str, bool]]:
    """
    使用uiautomator2设备截图并保存到指定路径
    
    Args:
        device: uiautomator2设备对象
        save_path: 保存路径
        
    Returns:
        Dict: 包含状态和路径信息的字典
    """
    try:
        save_path = Path(save_path)
        
        # 确保目录存在
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 截图
        screenshot = device.screenshot()
        if screenshot is None:
            raise ValueError("设备返回的截图为空")
        
        # 保存截图
        screenshot.save(str(save_path))
        
        logger.info(f"截图已保存: {save_path}")
        return {
            "status": "success",
            "screenshot_path": str(save_path),
            "exists": save_path.exists()
        }
        
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "screenshot_path": str(save_path) if 'save_path' in locals() else "",
            "exists": False
        }


def take_screenshot_and_save(
    device, 
    save_dir: Union[str, Path], 
    screenshot_count: int,
    filename_prefix: str = "screenshot"
) -> Optional[str]:
    """
    截图并保存到本地，返回文件路径
    
    Args:
        device: uiautomator2设备对象
        save_dir: 保存目录
        screenshot_count: 截图计数
        filename_prefix: 文件名前缀
        
    Returns:
        Optional[str]: 保存的文件路径，失败返回None
    """
    try:
        save_dir = Path(save_dir)
        images_dir = save_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{filename_prefix}_{screenshot_count}.png"
        save_path = images_dir / filename
        
        # 截图
        result = take_screenshot(device, save_path)
        
        if result["status"] != "success":
            logger.error(f"截图失败: {result.get('error', 'Unknown error')}")
            return None
        
        return str(save_path)
        
    except Exception as e:
        logger.error(f"截图并保存失败: {e}")
        return None


def resize_image(
    image_path: Union[str, Path], 
    max_width: int = 1920, 
    max_height: int = 1080,
    quality: int = 85,
    save_path: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    调整图像尺寸
    
    Args:
        image_path: 原图像路径
        max_width: 最大宽度
        max_height: 最大高度
        quality: 压缩质量（1-100）
        save_path: 保存路径，如果不提供则覆盖原文件
        
    Returns:
        Optional[Path]: 处理后的图像路径，失败返回None
    """
    try:
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"图像文件不存在: {image_path}")
            return None
        
        # 打开图像
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            
            # 检查是否需要调整尺寸
            if original_width <= max_width and original_height <= max_height:
                # 不需要调整，直接返回原路径
                return image_path
            
            # 计算新尺寸（保持宽高比）
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # 调整尺寸
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 确定保存路径
            if save_path is None:
                save_path = image_path
            else:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图像
            save_kwargs = {}
            if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            resized_img.save(save_path, **save_kwargs)
            
            logger.info(f"图像已调整: {original_width}x{original_height} -> {new_width}x{new_height}")
            return save_path
            
    except Exception as e:
        logger.error(f"调整图像尺寸失败: {image_path}, 错误: {e}")
        return None


def match_template(image, template, method=cv2.TM_CCOEFF_NORMED):
    h, w = template.shape[:2]
    result = cv2.matchTemplate(image, template, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    confidence = max_val if method not in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED] else min_val

    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc

    bottom_right = (top_left[0] + w, top_left[1] + h)
    return top_left, bottom_right, confidence


def match_template_with_blocks(detect_img, medium_img, block_size=(3, 3), threshold=0.8):
    """
    使用分块匹配中图在目标图像中的位置。
    返回匹配位置和块匹配置信度（匹配成功的块比例）。
    """
    # 首先进行整个中图的初步匹配，使用较低阈值
    prelim_threshold = threshold * 0.6  # 初步匹配阈值较低
    top_left, bottom_right, conf = match_template(detect_img, medium_img)
    if conf < prelim_threshold:
        return None, 0.0

    # 将中图切分成块
    h, w = medium_img.shape[:2]
    block_h = h // block_size[0]
    block_w = w // block_size[1]
    total_blocks = block_size[0] * block_size[1]
    matched_blocks = 0

    for i in range(block_size[0]):
        for j in range(block_size[1]):
            # 截取中图的小块
            y1 = i * block_h
            y2 = y1 + block_h
            x1 = j * block_w
            x2 = x1 + block_w
            block = medium_img[y1:y2, x1:x2]
            
            # 如果块为空，跳过
            if block.size == 0:
                continue
                
            # 在目标图像中对应位置截取相同大小的区域
            detect_y1 = top_left[1] + y1
            detect_y2 = detect_y1 + block_h
            detect_x1 = top_left[0] + x1
            detect_x2 = detect_x1 + block_w
            # 确保不越界
            if detect_y2 > detect_img.shape[0] or detect_x2 > detect_img.shape[1]:
                continue
            detect_block = detect_img[detect_y1:detect_y2, detect_x1:detect_x2]
            
            # 如果块大小不匹配，跳过
            if block.shape[:2] != detect_block.shape[:2]:
                continue
            
            # 匹配小块
            _, _, block_conf = match_template(detect_block, block)
            if block_conf >= threshold:
                matched_blocks += 1

    block_confidence = matched_blocks / total_blocks
    return top_left, block_confidence


def locate_small_via_dynamic_medium(
        reference_image_data,  # 截取小图时的大图
        target_image_data,     # 操作的目标（截出的小图）
        target_bbox,           # 截取小图时小图的坐标 [x1, y1, x2, y2]
        detect_image_data,     # 最后要检测的图像
        roi_coordinates=None,  # 检测区域 (x1, y1, x2, y2)，None 表示全图
        threshold=0.7,
        block_size=(3,3)):
    """
    图像定位函数 
    当 roi_coordinates=None 时 → 逻辑与旧版一致；
    当 roi_coordinates!=None 时 → 使用 ROI + 坐标缩放 的新逻辑。
    """
    try:
        logger.info("开始三步匹配算法...")
        logger.info(f"参考图像: {reference_image_data}")
        logger.info(f"目标图像: {target_image_data}")
        logger.info(f"检测图像: {detect_image_data}")
        logger.info(f"目标边界框: {target_bbox}")
        logger.info(f"ROI区域: {roi_coordinates}")

        # 读取图像
        reference_image = cv2.imread(reference_image_data)
        target_image = cv2.imread(target_image_data)
        detect_image = cv2.imread(detect_image_data)

        if any(img is None for img in [reference_image, target_image, detect_image]):
            logger.error("图像加载失败，请检查路径")
            return None

        # 基本尺寸
        detect_h, detect_w = detect_image.shape[:2]
        reference_h, reference_w = reference_image.shape[:2]
        target_x1, target_y1, target_x2, target_y2 = target_bbox

        # ========== ROI 校验 ==========
        if roi_coordinates:
            roi_x1, roi_y1, roi_x2, roi_y2 = roi_coordinates
            roi_valid = (
                roi_x1 >= 0 and roi_x1 < roi_x2 and
                roi_y1 >= 0 and roi_y1 < roi_y2 
            )

            if roi_valid:
                roi_x1 = int(max(0, min(roi_x1, detect_w)))
                roi_y1 = int(max(0, min(roi_y1, detect_h)))
                roi_x2 = int(min(max(roi_x1 + 50, roi_x2), detect_w))
                roi_y2 = int(min(max(roi_y1 + 50, roi_y2), detect_h))
                logger.info(f"使用有效ROI区域: ({roi_x1}, {roi_y1}, {roi_x2}, {roi_y2})")
            else:
                roi_x1, roi_y1, roi_x2, roi_y2 = 0, 0, detect_w, detect_h
                logger.warning(f"ROI区域无效或未覆盖目标区域，将使用全图")
        else:
            roi_x1, roi_y1, roi_x2, roi_y2 = 0, 0, detect_w, detect_h
            logger.info("未提供ROI坐标，使用全图检测")

        # ========== 分支 1：ROI=全图（即 roi_coordinates 无或无效） ==========
        if (roi_x1, roi_y1, roi_x2, roi_y2) == (0, 0, detect_w, detect_h):
            logger.info("执行旧逻辑（无缩放）")

            x1, y1, x2, y2 = map(round, target_bbox)
            img_h, img_w = reference_image.shape[:2]

            # 构造中图
            extend = 100
            medium_y1 = max(0, y1 - extend)
            medium_y2 = min(img_h, y2 + extend)
            medium_x1 = 0
            medium_x2 = img_w
            medium_img = reference_image[medium_y1:medium_y2, medium_x1:medium_x2]

            # Step1: 阔大感受域
            medium_top_left, block_confidence = match_template_with_blocks(detect_image, medium_img, block_size, threshold)
            if medium_top_left is None or block_confidence < threshold:
                return None  # 中图匹配失败


            # Step2: 小图匹配
            small_top_left, small_bottom_right, small_conf = match_template(medium_img, target_image)
            if small_conf < threshold:
                logger.warning("小图匹配失败")
                return None

            # Step3: 坐标映射
            final_bbox = (
                medium_top_left[0] + small_top_left[0],
                medium_top_left[1] + small_top_left[1],
                medium_top_left[0] + small_bottom_right[0],
                medium_top_left[1] + small_bottom_right[1],
            )
            logger.info(f"成功定位目标，位置: {final_bbox}")
            return final_bbox

        # ========== 分支 2：ROI 有效 → 新逻辑 ==========
        detect_roi = detect_image[roi_y1:roi_y2, roi_x1:roi_x2]
        roi_w, roi_h = roi_x2 - roi_x1, roi_y2 - roi_y1

        # 缩放比例
        scale_x = roi_w / reference_w
        scale_y = roi_h / reference_h

        # 缩放小图
        target_w = int((target_x2 - target_x1) * scale_x)
        target_h = int((target_y2 - target_y1) * scale_y)
        scaled_target_image = cv2.resize(target_image, (target_w, target_h))

        # 缩放参考图
        scaled_reference_image = cv2.resize(reference_image, (roi_w, roi_h))
        scaled_x1 = round(target_x1 * scale_x)
        scaled_y1 = round(target_y1 * scale_y)
        scaled_x2 = round(target_x2 * scale_x)
        scaled_y2 = round(target_y2 * scale_y)

        # 构造中图
        extend = 100
        medium_y1 = max(0, scaled_y1 - extend)
        medium_y2 = min(roi_h, scaled_y2 + extend)
        medium_x1 = max(0, scaled_x1 - extend)
        medium_x2 = min(roi_w, scaled_x2 + extend)
        medium_img = scaled_reference_image[medium_y1:medium_y2, medium_x1:medium_x2]

        # Step1: 中图匹配
        medium_top_left, medium_bottom_right, medium_conf = match_template(detect_roi, medium_img)
        if medium_conf < threshold:
            logger.warning("中图匹配失败")
            return None

        # Step2: 小图匹配
        small_top_left, small_bottom_right, small_conf = match_template(medium_img, scaled_target_image)
        if small_conf < threshold:
            logger.warning("小图匹配失败")
            return None

        # Step3: 映射回 detect 原图
        final_bbox = (
            medium_top_left[0] + small_top_left[0] + roi_x1,
            medium_top_left[1] + small_top_left[1] + roi_y1,
            medium_top_left[0] + small_bottom_right[0] + roi_x1,
            medium_top_left[1] + small_bottom_right[1] + roi_y1,
        )
        logger.info(f"成功定位目标，位置: {final_bbox}")
        return final_bbox

    except Exception as e:
        logger.error(f"定位过程出错: {str(e)}", exc_info=True)
        return None


def get_screen_size(device) -> Tuple[int, int]:
    """
    获取设备屏幕尺寸
    
    Args:
        device: uiautomator2设备对象
        
    Returns:
        Tuple[int, int]: (width, height)
    """
    try:
        info = device.info
        return info['displayWidth'], info['displayHeight']
    except Exception as e:
        logger.error(f"获取屏幕尺寸失败: {e}")
        # 返回默认值
        return 1080, 1920


def validate_image_format(image_path: Union[str, Path]) -> bool:
    """
    验证图像格式是否支持
    
    Args:
        image_path: 图像路径
        
    Returns:
        bool: 是否支持
    """
    try:
        image_path = Path(image_path)
        supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
        return image_path.suffix.lower() in supported_formats
    except Exception:
        return False


def get_image_info(image_path: Union[str, Path]) -> Dict[str, Union[int, str]]:
    """
    获取图像信息
    
    Args:
        image_path: 图像路径
        
    Returns:
        Dict: 图像信息
    """
    try:
        image_path = Path(image_path)
        
        if not image_path.exists():
            return {"error": "文件不存在"}
        
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_bytes": image_path.stat().st_size
            }
            
    except Exception as e:
        return {"error": str(e)}


# ========== 废弃函数警告 ==========

def find_image_occurrence(*args, **kwargs):
    """⚠️ 此函数已废弃，请使用locate_small_via_dynamic_medium替代"""
    import warnings
    warnings.warn(
        "find_image_occurrence() 已废弃。"
        "请使用 locate_small_via_dynamic_medium() 替代："
        "- 支持动态缩放匹配，适应不同屏幕分辨率"
        "- 更智能的图像识别算法，提高匹配准确率"
        "- 返回详细的位置和相似度信息",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("find_image_occurrence() 已由locate_small_via_dynamic_medium替代")


def check_image_exists(*args, **kwargs):
    """⚠️ 此函数已废弃，请使用locate_small_via_dynamic_medium替代"""
    import warnings
    warnings.warn(
        "check_image_exists() 已废弃。"
        "请使用 locate_small_via_dynamic_medium() 替代："
        "- 统一的图像定位和验证接口"
        "- 支持多种匹配算法和动态缩放"
        "- 返回详细的位置坐标和相似度信息",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("check_image_exists() 已由locate_small_via_dynamic_medium替代")


def find_icon_coordinates(*args, **kwargs):
    """⚠️ 此函数已废弃，请使用locate_small_via_dynamic_medium替代"""
    import warnings
    warnings.warn(
        "find_icon_coordinates() 已废弃。"
        "请使用 locate_small_via_dynamic_medium() 替代："
        "- 更智能的目标区域检测和验证"
        "- 支持动态缩放匹配，提高准确率"
        "- 统一的返回格式和错误处理",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("find_icon_coordinates() 已由locate_small_via_dynamic_medium替代")



def draw_point(*args, **kwargs):
    """⚠️ 此函数已废弃，使用频率极低且依赖链断裂"""
    import warnings
    warnings.warn(
        "draw_point() 已废弃。"
        "替代方案："
        "- 如需图像标记功能，请直接使用 PIL 或 OpenCV 库"
        "- 大多数调试需求可通过日志记录坐标信息替代"
        "- 例如：使用 PIL.ImageDraw.Draw.ellipse() 绘制标记点",
        DeprecationWarning, stacklevel=2
    )
    raise DeprecationWarning("draw_point() 已废弃，使用频率极低且依赖链断裂") 



def extract_screen_from_camera_image(image_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Optional[Tuple[str, Tuple[int, int, int, int]]]:
    """
    从摄像头拍摄的图像中提取屏幕区域（仅使用边缘检测）
    
    Args:
        image_path: 摄像头图像路径
        output_path: 提取的屏幕区域保存路径（可选）
        
    Returns:
        Optional[Tuple[str, Tuple[int, int, int, int]]]: (屏幕图像路径, 屏幕边界框) 或 None
    """
    try:
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"图像文件不存在: {image_path}")
            return None
        
        # 读取图像
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"无法读取图像: {image_path}")
            return None
            
        logger.info(f"开始从摄像头图像中提取屏幕区域: {image_path}")
        logger.info(f"原始图像尺寸: {image.shape}")
        
        # 边缘检测方法
        screen_rect, confidence = _detect_screen_by_edges(image)
        
        if screen_rect is None or confidence < 0.3:
            logger.warning(f"屏幕检测失败，置信度: {confidence}")
            return None
        
        logger.info(f"屏幕检测成功，置信度: {confidence:.3f}")
        
        # 提取屏幕区域
        screen_image = _extract_screen_region(image, screen_rect)
        
        # 确定保存路径
        if output_path is None:
            output_path = image_path.parent / f"screen_{image_path.stem}.png"
        else:
            output_path = Path(output_path)
        
        # 保存屏幕区域
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), screen_image)
        
        logger.info(f"屏幕区域已保存: {output_path}")
        logger.info(f"提取的屏幕尺寸: {screen_image.shape}")
        
        return str(output_path), screen_rect
        
    except Exception as e:
        logger.error(f"屏幕提取失败: {image_path}, 错误: {e}")
        return None


def _detect_screen_by_edges(image: np.ndarray) -> Tuple[Optional[Tuple[int, int, int, int]], float]:
    """
    使用边缘检测方法检测屏幕区域
    
    Args:
        image: 输入图像
        
    Returns:
        Tuple[Optional[Tuple[int, int, int, int]], float]: (屏幕边界框, 置信度)
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny边缘检测
        edges = cv2.Canny(blurred, 50, 150)
        
        # 形态学操作
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 筛选轮廓
        screen_candidates = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50000:  # 屏幕应该足够大
                continue
                
            # 近似轮廓
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 检查是否为矩形（4个顶点）
            if len(approx) == 4:
                # 计算矩形性
                rect = cv2.boundingRect(approx)
                aspect_ratio = rect[2] / rect[3]
                
                # 屏幕通常是横屏或竖屏
                if 0.5 < aspect_ratio < 2.0:
                    screen_candidates.append((contour, area, rect))
        
        if screen_candidates:
            # 选择面积最大的
            best_contour, best_area, best_rect = max(screen_candidates, key=lambda x: x[1])
            confidence = min(1.0, best_area / (image.shape[0] * image.shape[1]) * 3)
            
            return best_rect, confidence
        
        return None, 0.0
        
    except Exception as e:
        logger.error(f"边缘检测失败: {e}")
        return None, 0.0


def _extract_screen_region(image: np.ndarray, rect: Tuple[int, int, int, int]) -> np.ndarray:
    """
    提取屏幕区域
    
    Args:
        image: 原始图像
        rect: 屏幕边界框 (x, y, w, h)
        
    Returns:
        np.ndarray: 提取的屏幕区域
    """
    x, y, w, h = rect
    
    # 添加一些边距
    margin = 10
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(image.shape[1] - x, w + 2 * margin)
    h = min(image.shape[0] - y, h + 2 * margin)
    
    screen_image = image[y:y+h, x:x+w]
    return screen_image


# if __name__ == "__main__":
#     x1, y1, x2, y2 = 
#     print()