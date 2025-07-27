#!/usr/bin/env python3
"""
启动Web应用 - 确保使用正确的虚拟环境和设置
"""

import os
import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent

# 设置工作目录为项目根目录
os.chdir(project_root)

# 添加项目根目录到Python路径
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['PYTHONPATH'] = str(project_root)

print(f"🚀 启动Web应用...")
print(f"📁 工作目录: {os.getcwd()}")
print(f"🐍 Python路径: {sys.executable}")
print(f"📦 项目根目录: {project_root}")

# 设置数据库为离线模式
os.environ['TRADINGAGENTS_DB_ENABLED'] = 'false'
os.environ['TRADINGAGENTS_REDIS_ENABLED'] = 'false'
print("🔧 已设置数据库为离线模式")

# 启动Streamlit
import subprocess
streamlit_cmd = [
    sys.executable, 
    "-m", "streamlit", 
    "run", 
    str(project_root / "web" / "app.py"),
    "--server.port=8501",
    "--server.address=localhost"
]

print(f"💫 启动命令: {' '.join(streamlit_cmd)}")
subprocess.run(streamlit_cmd)
