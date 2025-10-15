# Gvitest Script - 自动化脚本生成器

基于 Jinja2 模板引擎的自动化脚本生成系统，支持 Agent/Manual 双模式执行、控制流、条件表达式和预期结果验证。

## 🚀 快速开始

### 1. 安装

```bash
# 从 PyPI 安装（推荐）
pip install gvitest-script

# 或从源码安装
git clone <repository-url>
cd script_server
uv sync
source .venv/bin/activate
```

### 2. 启动

```bash
# 使用默认配置启动
gvitest-script
```

### 3. 文件服务器配置

默认文件服务器URL：`http://localhost:8080`

```bash
# 使用默认文件服务器（推荐）
gvitest-script

# 自定义文件服务器URL
gvitest-script --file-server-url http://{FILE_SERVER_URL}

# 通过环境变量设置文件服务器
export FILE_SERVER_URL=http://localhost:3000
gvitest-script

# 本地模式（不支持文件服务器的下载和上传，使用和返回本地文件）
gvitest-script --file-server-url ""
```

### 4. 工作空间配置

默认工作空间路径：`项目目录/script_workspace`

```bash
# 使用默认工作空间（推荐）
gvitest-script

# 自定义工作空间路径
gvitest-script --workspace /path/to/custom/workspace

# 通过环境变量设置工作空间
export WORKSPACE_PATH=/path/to/custom/workspace
gvitest-script
```

## 📦 PyPI 包信息

- **包名**: `gvitest-script`
- **版本**: `0.1.0`
- **PyPI**: https://pypi.org/project/gvitest-script/
- **安装**: `pip install gvitest-script`




