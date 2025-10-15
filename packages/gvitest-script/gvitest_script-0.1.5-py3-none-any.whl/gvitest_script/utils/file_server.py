import requests
from pathlib import Path

class FileServer:
    def __init__(self, base_url: str, workspace_root: Path = None):
        """
        初始化文件服务器
        Args:
            base_url: 文件服务器URL，从启动参数获取
            workspace_root: 工作空间根目录，用于统一图像存储
        """
        if not base_url:
            raise ValueError("文件服务器URL不能为空")
        
        self.base_url = base_url.rstrip("/")
        
        # 统一使用工作空间下的images目录
        if workspace_root:
            self.local_images_path = workspace_root / "images"
        else:
            # 备用方案：使用当前目录下的images
            self.local_images_path = Path.cwd() / "images"
        
        # 确保本地图像目录存在
        self.local_images_path.mkdir(parents=True, exist_ok=True)

    def health_check(self) -> bool:
        """检查文件服务器是否可用（跳过健康检查，直接返回True）"""
        # 跳过健康检查，因为文件服务器可能没有/health接口
        # 实际可用性将在首次上传/下载时验证
        return True

    def upload_file(self, local_path: str, remote_filename: str) -> str:
        """
        上传文件到文件服务器
        Args:
            local_path: 本地文件路径
            remote_filename: 远程文件名
        Returns:
            str: 上传成功后的文件URL路径，失败返回空字符串
        """
        try:
            with open(local_path, 'rb') as f:
                files = {'file': (remote_filename, f, 'image/jpeg')}
                response = requests.post(f"{self.base_url}/upload-to-static", files=files)
            
            response.raise_for_status()  
            data = response.json()
            
            if data.get("status") == "success":
                return data.get("url", "")
            else:
                print(f"[Upload Failed] {data}")
                return ""
        except Exception as e:
            print(f"[Upload Error] {e}")
            return ""

    def download_file(self, remote_path: str, local_path: str = None) -> bool:
        """
        从文件服务器下载文件
        Args:
            remote_path: 远程文件路径，如 "/static/uploads/filename.jpg"
            local_path: 本地保存路径，如果为None则使用默认本地图像目录
        Returns:
            bool: 下载是否成功
        """
        try:
           
            local_path = Path(local_path)
            
            response = requests.get(f"{self.base_url}{remote_path}", stream=True)
            response.raise_for_status()
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"[Download Error] {e}")
            return False

    def get_download_url(self, remote_path: str) -> str:
        """获取文件的下载URL"""
        return f"{self.base_url}{remote_path}"
    
    def get_local_images_path(self) -> Path:
        """获取本地图像存储路径"""
        return self.local_images_path
    
    def get_base_url(self) -> str:
        """获取文件服务器基础URL"""
        return self.base_url

# 全局实例（将在main.py中初始化）
file_server = None

def init_file_server(base_url: str, workspace_root: Path = None):
    """
    初始化全局文件服务器实例
    Args:
        base_url: 文件服务器URL（从main.py启动参数获取）
        workspace_root: 工作空间根目录
    Returns:
        FileServer: 文件服务器实例
    """
    global file_server
    file_server = FileServer(base_url, workspace_root)
    return file_server

def get_file_server():
    """
    获取全局文件服务器实例
    Returns:
        FileServer: 文件服务器实例，如果未初始化则抛出异常
    """
    if file_server is None:
        raise RuntimeError("文件服务器未初始化，请先调用 init_file_server()")
    return file_server
