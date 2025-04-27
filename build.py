#!/usr/bin/env python3
"""
FastCursor GUI 通用打包脚本
根据当前操作系统自动选择合适的打包方式

使用方法:
    python build.py

支持平台:
    - Windows: 生成 FastCursor.exe
    - macOS: 生成 FastCursor.app
    - Linux: 生成 FastCursor 可执行文件
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# 检测操作系统
PLATFORM = platform.system().lower()

print(f"============================================")
print(f"FastCursor GUI 打包工具 - 当前平台: {PLATFORM}")
print(f"============================================")

# 检测环境
USING_UV = os.path.exists(".venv") and not subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                                        shell=False, 
                                                        capture_output=True).returncode == 0

# 确保必要的包已安装
def ensure_dependencies():
    """确保必要的依赖包已安装"""
    dependencies = ["pyinstaller", "PyQt6", "pillow"]
    
    for dep in dependencies:
        try:
            __import__(dep.lower().replace("-", "_"))
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"正在安装 {dep}...")
            
            if USING_UV:
                # 使用uv安装
                try:
                    subprocess.run(["uv", "pip", "install", dep], check=True)
                except subprocess.CalledProcessError:
                    # 尝试不带路径直接运行
                    subprocess.run([sys.executable, "-m", "uv", "pip", "install", dep], check=True)
            else:
                # 使用标准pip安装
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                
            print(f"✓ {dep} 安装完成")

# 应用程序信息
APP_NAME = "FastCursor"
MAIN_SCRIPT = "fastcursor_gui.py"

# 创建图标
def create_icon():
    """为应用创建图标文件"""
    if PLATFORM == "darwin":  # macOS
        icon_file = "icon.icns"
    elif PLATFORM == "windows":  # Windows
        icon_file = "icon.ico"
    else:  # Linux或其他
        icon_file = "icon.png"
    
    # 如果图标已存在，直接返回
    if os.path.exists(icon_file):
        print(f"✓ 使用已有图标: {icon_file}")
        return icon_file
    
    try:
        from PIL import Image, ImageDraw
        
        # 为避免重复代码，创建统一的PNG图标
        img = Image.new('RGB', (512, 512), color=(41, 45, 62))
        d = ImageDraw.Draw(img)
        
        # 绘制一个圆形
        d.ellipse((156, 156, 356, 356), fill=(79, 172, 254))
        
        # 添加一些简单细节
        d.rectangle((226, 246, 286, 266), fill=(41, 45, 62))
        
        # 保存PNG图标
        png_path = Path("icon.png")
        img.save(png_path)
        print(f"✓ 创建临时图标: {png_path}")
        
        # 根据平台转换为适当的图标格式
        if PLATFORM == "darwin":  # macOS
            # 使用sips转换为icns (macOS专用工具)
            try:
                subprocess.run(["sips", "-s", "format", "icns", png_path, "--out", icon_file], 
                               check=True, stdout=subprocess.DEVNULL)
                print(f"✓ 创建macOS图标: {icon_file}")
                os.remove(png_path)
            except Exception:
                # 如果sips命令失败，保留PNG图标
                icon_file = png_path
        elif PLATFORM == "windows":  # Windows
            # 直接用PIL保存为ICO
            img.save(icon_file, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"✓ 创建Windows图标: {icon_file}")
            os.remove(png_path)
        else:  # Linux或其他
            # Linux通常只需要PNG图标
            icon_file = png_path
            print(f"✓ 使用PNG图标: {icon_file}")
            
        return icon_file
        
    except Exception as e:
        print(f"! 创建图标时出错: {e}")
        return None

# 检查必需文件是否存在
def check_required_files():
    """检查必需的文件是否存在"""
    required_files = ["names-dataset.txt"]
    required_dirs = ["turnstilePatch"]
    
    for file in required_files:
        if not os.path.isfile(file):
            print(f"❌ 错误: 缺少必需文件 {file}")
            return False
            
    for directory in required_dirs:
        if not os.path.isdir(directory):
            print(f"❌ 错误: 缺少必需目录 {directory}")
            return False
    
    print("✓ 所有必需文件和目录已检查")
    return True

# 打包应用
def build_app(icon_file):
    """使用PyInstaller打包应用"""
    print("\n开始打包应用程序...")
    
    # 查找pyinstaller可执行文件
    pyinstaller_cmd = "pyinstaller"
    
    # 构建基本命令
    cmd = [
        pyinstaller_cmd,
        "--name=" + APP_NAME,
        "--windowed",  # GUI模式，不显示控制台
        "--clean",     # 清理临时文件
        "--noconfirm", # 不提示确认
    ]
    
    # 根据平台添加特定选项
    if PLATFORM == "darwin":  # macOS
        cmd.append("--onedir")   # macOS使用目录模式
    else:
        cmd.append("--onefile")  # 其他平台使用单文件模式
    
    # 添加图标
    if icon_file and os.path.exists(icon_file):
        cmd.append(f"--icon={icon_file}")
        
        # 添加资源文件
        if PLATFORM == "darwin":  # macOS
            cmd.extend(["--add-data", f"{icon_file}:."])
        elif PLATFORM == "windows":  # Windows
            cmd.extend(["--add-data", f"{icon_file};."])
        else:  # Linux
            cmd.extend(["--add-data", f"{icon_file}:."])
    
    # 添加其他必需文件
    if PLATFORM == "darwin":  # macOS
        cmd.extend(["--add-data", "names-dataset.txt:."])
        cmd.extend(["--add-data", "turnstilePatch:turnstilePatch"])
    elif PLATFORM == "windows":  # Windows
        cmd.extend(["--add-data", "names-dataset.txt;."])
        cmd.extend(["--add-data", "turnstilePatch;turnstilePatch"])
    else:  # Linux
        cmd.extend(["--add-data", "names-dataset.txt:."])
        cmd.extend(["--add-data", "turnstilePatch:turnstilePatch"])
    
    # 如果是macOS，添加额外选项
    if PLATFORM == "darwin":
        cmd.append("--osx-bundle-identifier=com.fastcursor.app")
    
    # 添加主脚本
    cmd.append(MAIN_SCRIPT)
    
    # 执行打包命令
    try:
        print("执行命令:", " ".join(cmd))
        subprocess.run(cmd, check=True)
        
        # 输出路径
        if PLATFORM == "darwin":
            output_path = f"./dist/{APP_NAME}.app"
        elif PLATFORM == "windows":
            output_path = f"./dist/{APP_NAME}.exe"
        else:
            output_path = f"./dist/{APP_NAME}"
            
        print(f"\n✅ 打包完成! 输出位置: {output_path}")
        
        # 平台特定提示
        if PLATFORM == "darwin":
            print("\n提示: 在macOS上，如果遇到'未验证的开发者'警告，")
            print("     请在 系统偏好设置 > 安全性与隐私 中允许运行该应用。")
        elif PLATFORM == "windows":
            print("\n提示: 在Windows上，可能会出现SmartScreen警告，")
            print("     选择'更多信息'并'仍要运行'即可。")
        
    except Exception as e:
        print(f"\n❌ 打包过程中出错: {e}")
        print("\n尝试使用: uv pip install pyinstaller && uv run -m PyInstaller ...")
        sys.exit(1)

if __name__ == "__main__":
    # 确保依赖已安装
    ensure_dependencies()
    
    # 检查必需文件
    if not check_required_files():
        sys.exit(1)
    
    # 创建图标
    icon_file = create_icon()
    
    # 打包应用
    build_app(icon_file) 