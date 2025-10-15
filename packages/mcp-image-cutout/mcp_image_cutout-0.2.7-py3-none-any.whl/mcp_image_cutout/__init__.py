"""
MCP 图像抠图服务器

基于Model Context Protocol (MCP)的服务器，专门提供火山引擎图像抠图功能。
使用显著性分割技术，自动识别并抠出图像中的主要对象。
"""

__version__ = "0.2.1"
__author__ = "fengjinchao"
__email__ = "fengjinchao@example.com"

# 导入主要模块和函数
from .server import main, VolcImageCutter

__all__ = [
    "main",
    "VolcImageCutter"
]
