from enum import Enum
from typing import Optional
from colorama import Fore, Style
import time
import random
from browser_utils import BrowserManager
from get_email_code import EmailVerificationHandler
from config import Config
from datetime import datetime
from logger import logging
import os
import hashlib
import base64
import uuid
import secrets
import sys
import tempfile

class VerificationStatus(Enum):
    """验证状态枚举"""

    PASSWORD_PAGE = "@name=password"
    CAPTCHA_PAGE = "@data-index=0"
    ACCOUNT_SETTINGS = "Account Settings"


class TurnstileError(Exception):
    """Turnstile 验证相关异常"""

    pass

def check_verification_success(tab) -> Optional[VerificationStatus]:
    """
    检查验证是否成功

    Returns:
        VerificationStatus: 验证成功时返回对应状态，失败返回 None
    """
    for status in VerificationStatus:
        if tab.ele(status.value):
            save_screenshot(tab, "success")
            logging.info(f"验证成功 - 已到达{status.name}页面")
            return status
    return None


def handle_turnstile(tab, max_retries: int = 2, retry_interval: tuple = (1, 2)) -> bool:
    """
    处理 Turnstile 验证

    Args:
        tab: 浏览器标签页对象
        max_retries: 最大重试次数
        retry_interval: 重试间隔时间范围(最小值, 最大值)

    Returns:
        bool: 验证是否成功

    Raises:
        TurnstileError: 验证过程中出现异常
    """
    logging.info("正在检测 Turnstile 验证...")
    # save_screenshot(tab, "start")

    retry_count = 0

    try:
        while retry_count < max_retries:
            retry_count += 1
            logging.debug(f"第 {retry_count} 次尝试验证")

            try:
                save_screenshot(tab, "start")
                # 定位验证框元素
                challenge_check = (
                    tab.ele("@id=cf-turnstile", timeout=2)
                    .child()
                    .shadow_root.ele("tag:iframe")
                    .ele("tag:body")
                    .sr("tag:input")
                )
                if challenge_check:
                    logging.info("检测到 Turnstile 验证框，开始处理...")
                    # 随机延时后点击验证
                    time.sleep(random.uniform(1, 3))
                    challenge_check.click()
                    time.sleep(2)

                    保存验证后的截图
                    save_screenshot(tab, "clicked")

                    # 检查验证结果
                    if check_verification_success(tab):
                        logging.info("Turnstile 验证通过")
                        # save_screenshot(tab, "success")
                        return True

            except Exception as e:
                logging.debug(f"当前尝试未成功: {str(e)}")

            # 检查是否已经验证成功
            if check_verification_success(tab):
                return True
            # 随机延时后继续下一次尝试
            time.sleep(random.uniform(*retry_interval))

        # 超出最大重试次数
        logging.error(f"验证失败 - 已达到最大重试次数 {max_retries}")
      
        save_screenshot(tab, "failed")
        return False

    except Exception as e:
        error_msg = f"Turnstile 验证过程发生异常: {str(e)}"
        logging.error(error_msg)
        save_screenshot(tab, "error")
        raise TurnstileError(error_msg)


class EmailGenerator:
    def __init__(
        self,
        password="".join(
            random.choices(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
                k=12,
            )
        ),
    ):
        configInstance = Config()
        configInstance.print_config()
        self.domain = configInstance.get_domain()
        self.names = self.load_names()
        self.default_password = password
        self.default_first_name = self.generate_random_name()
        self.default_last_name = self.generate_random_name()

    def load_names(self):
        """加载名字数据集，支持开发环境和打包后的环境"""
        try:
            # 尝试直接从当前目录读取
            with open("names-dataset.txt", "r") as file:
                return file.read().split()
        except FileNotFoundError:
            # 如果直接读取失败，尝试从应用程序路径读取
            try:
                # 获取应用程序根路径
                if getattr(sys, 'frozen', False):
                    # 打包后的环境
                    base_path = sys._MEIPASS
                else:
                    # 开发环境
                    base_path = os.path.dirname(os.path.abspath(__file__))
                
                file_path = os.path.join(base_path, "names-dataset.txt")
                # logging.info(f"尝试从路径读取名字数据: {file_path}")
                
                with open(file_path, "r") as file:
                    return file.read().split()
            except Exception as e:
                logging.error(f"加载名字数据集失败: {str(e)}")
                # 提供一个最小的备用名字列表，确保程序不会崩溃
                logging.warning("使用备用名字列表")
                return ["Alex", "Sam", "Taylor", "Jordan", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Quinn"]

    def generate_random_name(self):
        """生成随机用户名"""
        return random.choice(self.names)

    def generate_email(self, length=4):
        """生成随机邮箱地址"""
        length = random.randint(0, length)  # 生成0到length之间的随机整数
        timestamp = str(int(time.time()))[-length:]  # 使用时间戳后length位
        return f"{self.default_first_name}{timestamp}@{self.domain}"  #

    def get_account_info(self):
        """获取完整的账号信息"""
        return {
            "email": self.generate_email(),
            "password": self.default_password,
            "first_name": self.default_first_name,
            "last_name": self.default_last_name,
        }


def get_user_agent():
    """获取user_agent"""
    try:
        # 使用JavaScript获取user agent
        browser_manager = BrowserManager()
        browser = browser_manager.init_browser()
        user_agent = browser.latest_tab.run_js("return navigator.userAgent")
        browser_manager.quit()
        return user_agent
    except Exception as e:
        logging.error(f"获取user agent失败: {str(e)}")
        return None


def save_screenshot(tab, stage: str, timestamp: bool = True) -> None:
    """
    保存页面截图

    Args:
        tab: 浏览器标签页对象
        stage: 截图阶段标识
        timestamp: 是否添加时间戳
    """
    try:
        # 直接使用系统临时目录
        screenshot_dir = tempfile.gettempdir()
        
        # 创建FastCursor子目录（如果可能）
        try:
            fastcursor_temp_dir = os.path.join(screenshot_dir, "FastCursor")
            if not os.path.exists(fastcursor_temp_dir):
                os.makedirs(fastcursor_temp_dir, exist_ok=True)
            screenshot_dir = fastcursor_temp_dir
        except Exception:
            # 如果创建子目录失败，就使用系统临时目录根目录
            pass

        # 生成文件名
        if timestamp:
            filename = f"turnstile_{stage}_{int(time.time())}.png"
        else:
            filename = f"turnstile_{stage}.png"

        filepath = os.path.join(screenshot_dir, filename)

        # 保存截图
        tab.get_screenshot(filepath)
        logging.info(f"截图已保存: {filepath}")
    except Exception as e:
        logging.warning(f"截图保存失败: {str(e)}")
        # 最后备用方案：直接创建临时文件
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tab.get_screenshot(temp_file.name)
            logging.info(f"截图已保存到临时文件: {temp_file.name}")
        except Exception as e2:
            logging.error(f"无法保存截图到临时文件: {str(e2)}")


class PKCEInfo:
    def generate_uuid():
        return str(uuid.uuid4())


    def generate_pkce_code_verifier(length=43):
        if length < 43 or length > 128:
            raise ValueError("PKCE 要求 code_verifier 长度为 43~128 字符")

        # 生成密码学安全的随机字节（长度计算确保 Base64 编码后足够）
        byte_length = (length * 3 + 3) // 4  # Base64 长度换算
        random_bytes = secrets.token_bytes(byte_length)
        
        # 转换为 Base64URL 格式（无填充符 =）
        verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8')[:length]
        
        # 确保首字符不是连字符（某些 OAuth 实现可能敏感）
        if verifier.startswith('-'):
            verifier = 'A' + verifier[1:]
        
        return verifier


    def generate_challenge(verifier):
        # 计算 SHA-256 哈希
        sha256_hash = hashlib.sha256(verifier.encode('utf-8')).digest()

        # Base64URL 编码（去除末尾的 =）
        code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').replace('=', '')
        return code_challenge

    @classmethod
    def generate(cls):
        code_uuid=cls.generate_uuid()
        code_verifier=cls.generate_pkce_code_verifier()
        code_challenge=cls.generate_challenge(code_verifier)

        logging.debug(f"uuid: {code_uuid}")
        logging.debug(f"verifier: {code_verifier}")
        logging.debug(f"challenge: {code_challenge}")
        return code_uuid,code_verifier,code_challenge