#!/usr/bin/env python3
"""
本地运行MCP抠图服务的启动脚本
"""
import sys
import os

# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行主函数
from mcp_image_cutout.server import main

if __name__ == "__main__":
    main()
