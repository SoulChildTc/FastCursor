import psutil
from logger import logging  
import time
import subprocess
import os
import platform

def get_cursor_path():
    """
    获取 Cursor 可执行文件的路径
    """
    system = platform.system()
    if system == "Windows":
        # Windows 默认安装路径
        paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Cursor', 'Cursor.exe'),
            os.path.join(os.environ.get('APPDATA', ''), 'Programs', 'Cursor', 'Cursor.exe')
        ]
    elif system == "Darwin":  # macOS
        paths = [
            '/Applications/Cursor.app/Contents/MacOS/Cursor'
        ]
    elif system == "Linux":
        paths = [
            '/usr/bin/cursor',
            '/usr/local/bin/cursor'
        ]
    else:
        raise OSError(f"不支持的操作系统: {system}")

    for path in paths:
        if os.path.exists(path):
            return path
            
    raise FileNotFoundError("未找到 Cursor 可执行文件")

def RestartCursor():
    """
    重启 Cursor 进程
    """
    try:
        logging.info("开始重启Cursor...")
        # 先关闭现有进程
        if not ExitCursor():
            logging.error("无法正确关闭现有 Cursor 进程, 请手动重启 Cursor")
            return False
            
        time.sleep(1)  # 等待进程完全关闭
        
        # 获取 Cursor 可执行文件路径
        try:
            cursor_path = get_cursor_path()
        except (FileNotFoundError, OSError) as e:
            logging.error(f"获取 Cursor 路径失败: {str(e)}")
            return False
            
        # 启动新的 Cursor 进程
        try:
            subprocess.Popen([cursor_path], start_new_session=True)
            logging.info("Cursor 已重启")
            return True
        except subprocess.SubprocessError as e:
            logging.error(f"启动 Cursor 失败: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"重启 Cursor 时发生错误: {str(e)}")
        return False

def ExitCursor(timeout=10):
    """
    温和地关闭 Cursor 进程，失败后强制关闭
    
    Args:
        timeout (int): 等待进程自然终止的超时时间（秒）
    Returns:
        bool: 是否成功关闭所有进程
    """
    try:
        logging.info("开始退出Cursor...")
        cursor_processes = []
        # 收集所有 Cursor 进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in ['cursor.exe', 'cursor']:
                    cursor_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not cursor_processes:
            logging.info("未发现运行中的 Cursor 进程")
            return True

        # 先尝试温和地请求进程终止
        for proc in cursor_processes:
            try:
                if proc.is_running():
                    proc.terminate()  # 发送终止信号
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 等待进程自然终止
        start_time = time.time()
        while time.time() - start_time < timeout / 2:  # 先等待一半时间
            still_running = []
            for proc in cursor_processes:
                try:
                    if proc.is_running():
                        still_running.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not still_running:
                logging.info("所有 Cursor 进程已正常关闭")
                return True
                
            time.sleep(0.5)
            
        # 如果温和终止后仍有进程，强制终止
        if still_running:
            logging.warning(f"尝试强制终止未关闭的进程")
            for proc in still_running:
                try:
                    if proc.is_running():
                        proc.kill()  # 强制终止
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # 再等待剩余时间
            time.sleep(1)  # 给强制终止一点时间
            
            # 最终检查
            still_running = [p for p in cursor_processes if p.is_running()]
            if still_running:
                process_list = ", ".join([str(p.pid) for p in still_running])
                logging.warning(f"以下进程未能关闭: {process_list}")
                return False
            
        return True

    except Exception as e:
        logging.error(f"关闭 Cursor 进程时发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    ExitCursor()
