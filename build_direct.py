#!/usr/bin/env python3
"""
FastCursor GUI 最简打包脚本
使用直接的shell命令安装依赖和执行PyInstaller

使用方法:
    python build_direct.py
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# 检测操作系统
PLATFORM = platform.system().lower()
print(f"当前平台: {PLATFORM}")

# 应用程序信息
APP_NAME = "FastCursor"
MAIN_SCRIPT = "fastcursor_gui.py"

def run_command(cmd, shell=False):
    """运行命令并返回成功/失败"""
    print(f"执行: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    try:
        subprocess.run(cmd, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

# 安装依赖
print("正在安装所需依赖...")
if os.path.exists(".venv"):
    # 尝试使用uv
    success = run_command("uv pip install PyQt6 pillow pyinstaller", shell=True)
else:
    # 尝试使用pip
    success = run_command([sys.executable, "-m", "pip", "install", "PyQt6", "pillow", "pyinstaller"])

if not success:
    print("安装依赖失败。您可以尝试手动安装:")
    print("uv pip install PyQt6 pillow pyinstaller")
    print("或")
    print("pip install PyQt6 pillow pyinstaller")
    sys.exit(1)

# 打包命令
print("\n正在构建应用...")

# 根据平台选择合适的参数
if PLATFORM == "darwin":  # macOS
    cmd = f"pyinstaller --name={APP_NAME} --windowed --onefile --clean --noconfirm {MAIN_SCRIPT}"
elif PLATFORM == "windows":  # Windows
    cmd = f"pyinstaller --name={APP_NAME} --windowed --onefile --clean --noconfirm {MAIN_SCRIPT}"
else:  # Linux或其他
    cmd = f"pyinstaller --name={APP_NAME} --windowed --onefile --clean --noconfirm {MAIN_SCRIPT}"

# 执行打包命令
success = run_command(cmd, shell=True)

if success:
    # 根据平台确定输出路径
    if PLATFORM == "darwin":
        output_path = f"./dist/{APP_NAME}.app"
    elif PLATFORM == "windows":
        output_path = f"./dist/{APP_NAME}.exe"
    else:
        output_path = f"./dist/{APP_NAME}"
        
    print(f"\n✅ 打包完成! 输出位置: {output_path}")
else:
    print("\n❌ 打包失败!")
    # 尝试用uv run的方式运行pyinstaller
    print("\n尝试使用uv run方式:")
    alt_cmd = f"uv run -m PyInstaller --name={APP_NAME} --windowed --onefile --clean --noconfirm {MAIN_SCRIPT}"
    print(f"执行: {alt_cmd}")
    subprocess.run(alt_cmd, shell=True) 