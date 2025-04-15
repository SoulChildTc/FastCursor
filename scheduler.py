import schedule
import time
import random
import subprocess
import sys
import os
from datetime import datetime, timedelta
from logger import logging
from config import Config
from account_manager import AccountManager

class AccountScheduler:
    def __init__(self, enable_register=True, enable_reset=True, reset_time="02:00"):
        """初始化账号调度器
        
        Args:
            enable_register: 是否启用账号注册任务，默认True
            enable_reset: 是否启用旧账号重置任务，默认True
            reset_time: 重置任务执行时间，格式"HH:MM"，默认"02:00"
        """
        self.config = Config()
        self.account_manager = AccountManager()
        self.next_run_time = None
        
        # 根据配置启动任务
        if enable_register:
            self.schedule_next_run()
            logging.info("已启用账号注册任务")
        else:
            logging.info("账号注册任务已禁用")
            
        if enable_reset:
            self.schedule_daily_reset(reset_time)
            logging.info(f"已启用旧账号重置任务，执行时间: {reset_time}")
        else:
            logging.info("旧账号重置任务已禁用")

    def register_account(self):
        """运行账号注册脚本"""
        try:
            logging.info("=== 开始执行账号注册任务 ===")
            
            # 获取当前脚本的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            register_script = os.path.join(current_dir, "register_account.py")
            
            # 使用Python解释器运行register_account.py
            python_executable = sys.executable
            
            # 直接使用subprocess.run执行脚本，并将输出直接传递到当前进程的标准输出和标准错误
            result = subprocess.run(
                [python_executable, register_script],
                stdout=None,  # 使用None表示继承父进程的标准输出
                stderr=None,  # 使用None表示继承父进程的标准错误
                check=False
            )
            
            # 检查返回码
            if result.returncode == 0:
                logging.info("账号注册任务执行成功")
            else:
                logging.error(f"账号注册任务执行失败，返回码: {result.returncode}")
            
            # 安排下一次运行
            self.schedule_next_run()
            
        except Exception as e:
            logging.error(f"执行账号注册任务时发生错误: {str(e)}")
            # 即使发生错误，也安排下一次运行
            self.schedule_next_run()
    
    def schedule_next_run(self):
        """安排下一次运行的时间（随机1-3小时）"""
        # 清除之前的所有任务
        schedule.clear()
        
        # 随机生成1-3小时的间隔（以秒为单位）
        hours = random.uniform(1, 3)
        seconds = int(hours * 3600)
        
        # 计算下一次运行的时间
        self.next_run_time = datetime.now() + timedelta(seconds=seconds)
        formatted_time = self.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        
        logging.info(f"下一次账号注册任务将在 {formatted_time} 执行（{hours:.2f}小时后）")
        
        # 安排任务
        schedule.every(seconds).seconds.do(self.register_account).tag('register')
    
    def get_next_run_info(self):
        """获取下一次运行的信息"""
        if self.next_run_time:
            now = datetime.now()
            time_left = self.next_run_time - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return {
                "next_run_time": self.next_run_time.strftime("%Y-%m-%d %H:%M:%S"),
                "time_left": f"{hours}小时 {minutes}分钟 {seconds}秒"
            }
        return {"next_run_time": "未安排", "time_left": "无"}
    
    def run(self):
        """运行调度器"""
        logging.info("定时调度器已启动")
        logging.info(f"可用域名: {', '.join(self.config.domains)}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("调度器已手动停止")
        except Exception as e:
            logging.error(f"调度器运行出错: {str(e)}")
    
    def reset_old_accounts(self):
        """执行重置旧账号的任务"""
        try:
            logging.info("=== 开始执行重置旧账号任务 ===")
            reset_count = self.account_manager.reset_old_accounts()
            logging.info(f"成功重置 {reset_count} 个旧账号为可用状态")
        except Exception as e:
            logging.error(f"重置旧账号任务执行出错: {str(e)}")
    
    def schedule_daily_reset(self, reset_time="02:00"):
        """设置每天运行重置旧账号任务
        
        Args:
            reset_time: 重置任务执行时间，格式"HH:MM"
        """
        schedule.every().day.at(reset_time).do(self.reset_old_accounts).tag('reset')

# 如果直接运行此脚本
if __name__ == "__main__":
    scheduler = AccountScheduler()
    scheduler.run()
