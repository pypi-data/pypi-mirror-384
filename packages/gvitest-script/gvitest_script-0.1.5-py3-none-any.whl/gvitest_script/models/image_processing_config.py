from typing import Any, Dict, List
from pydantic import BaseModel, Field, validator
from pathlib import Path


class ImageProcessingConfig(BaseModel):
    """图像处理配置模型
    
    统一管理脚本生成器中所有图像处理相关的配置参数，
    包括URL格式转换、base64编码、图像质量控制等核心功能
    """
    
    # 🌐 工作空间URL配置（基于现有workspace架构）
    workspace_url_prefix: str = Field(
        default="/workspace", 
        description="工作空间URL前缀，用于生成图像访问URL"
    )
    
    # 📊 Base64编码配置
    base64_prefix: str = Field(
        default="data:image/png;base64,", 
        description="Base64图像数据前缀，用于前端直接显示图像"
    )
    max_image_size: int = Field(
        default=5*1024*1024, 
        description="最大图像文件大小(字节)，超过此大小的图像将被压缩或拒绝处理"
    )
    supported_formats: List[str] = Field(
        default_factory=lambda: ["png", "jpg", "jpeg", "bmp", "gif", "webp"],
        description="支持的图像格式列表，用于验证和转换"
    )
    
    # 🎨 图像质量和尺寸控制
    default_quality: int = Field(
        default=85, 
        description="默认图像压缩质量(1-100)，平衡文件大小和图像清晰度"
    )
    auto_resize: bool = Field(
        default=True, 
        description="是否自动调整过大图像的尺寸，避免内存溢出和传输延迟"
    )
    max_width: int = Field(
        default=1920, 
        description="图像最大宽度(像素)，超过此宽度的图像将被等比缩放"
    )
    max_height: int = Field(
        default=1080, 
        description="图像最大高度(像素)，超过此高度的图像将被等比缩放"
    )
    
    # 📁 临时文件管理配置
    temp_dir_name: str = Field(
        default="temp_images", 
        description="临时图像目录名，用于存储处理过程中的中间文件"
    )
    cleanup_temp_files: bool = Field(
        default=True, 
        description="是否自动清理临时文件，避免磁盘空间占用过多"
    )
    temp_file_ttl: int = Field(
        default=3600, 
        description="临时文件生存时间(秒)，超时文件将被自动删除"
    )
    
    # 🔄 错误处理和重试配置
    retry_count: int = Field(
        default=3, 
        description="图像处理失败时的重试次数"
    )
    timeout: float = Field(
        default=30.0, 
        description="图像处理操作的超时时间(秒)，防止长时间阻塞"
    )
    
    @validator('max_image_size')
    def validate_max_image_size(cls, v):
        if v <= 0:
            raise ValueError("最大图像大小必须大于0")
        if v > 50*1024*1024:  # 50MB
            raise ValueError("最大图像大小不能超过50MB")
        return v
    
    @validator('default_quality')
    def validate_quality(cls, v):
        if not 1 <= v <= 100:
            raise ValueError("图像质量必须在1-100之间")
        return v
    
    @validator('supported_formats')
    def validate_formats(cls, v):
        valid_formats = ["png", "jpg", "jpeg", "bmp", "gif", "webp", "tiff"]
        for fmt in v:
            if fmt.lower() not in valid_formats:
                raise ValueError(f"不支持的图像格式: {fmt}")
        return [fmt.lower() for fmt in v]

    
    def is_supported_format(self, format_or_filename: str) -> bool:
        """检查是否为支持的图像格式"""
        if '.' in format_or_filename:
            # 如果是文件名，提取扩展名
            ext = format_or_filename.split('.')[-1].lower()
        else:
            # 如果是格式名
            ext = format_or_filename.lower()
        
        return ext in self.supported_formats
    
    def get_base64_with_prefix(self, base64_data: str) -> str:
        """为base64数据添加前缀"""
        if base64_data.startswith('data:'):
            return base64_data
        return f"{self.base64_prefix}{base64_data}"
    
    def remove_base64_prefix(self, base64_with_prefix: str) -> str:
        """移除base64数据的前缀"""
        if base64_with_prefix.startswith('data:'):
            # 查找逗号位置，逗号后面是实际的base64数据
            comma_index = base64_with_prefix.find(',')
            if comma_index != -1:
                return base64_with_prefix[comma_index + 1:]
        return base64_with_prefix
    
    def get_temp_dir_path(self, workspace_root: Path, task_id: str = None) -> Path:
        """获取临时目录路径
        
        Args:
            workspace_root: 工作空间根目录
            task_id: 任务ID，如果提供则在任务目录下创建临时目录
            
        Returns:
            临时目录的Path对象
        """
        if task_id:
            return workspace_root / task_id / self.temp_dir_name
        else:
            return workspace_root / self.temp_dir_name
    
    def should_resize_image(self, width: int, height: int) -> bool:
        """判断图像是否需要调整大小"""
        if not self.auto_resize:
            return False
        return width > self.max_width or height > self.max_height
    
    def calculate_resize_dimensions(self, original_width: int, original_height: int) -> tuple[int, int]:
        """计算调整后的图像尺寸"""
        if not self.should_resize_image(original_width, original_height):
            return original_width, original_height
        
        # 计算缩放比例，保持宽高比
        width_ratio = self.max_width / original_width if original_width > self.max_width else 1
        height_ratio = self.max_height / original_height if original_height > self.max_height else 1
        scale_ratio = min(width_ratio, height_ratio)
        
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        
        return new_width, new_height
    
    class Config:
        json_encoders = {
            Path: str
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，保持与其他模型的一致性"""
        return self.model_dump()


# 默认配置实例
DEFAULT_IMAGE_CONFIG = ImageProcessingConfig() 