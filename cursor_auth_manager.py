from browser_utils import BrowserManager
from utils import handle_turnstile, get_user_agent, save_screenshot
import time
import random
from logger import logging
import sqlite3
import os
import sys


class CursorAuthManager:
    """Cursor认证信息管理器"""

    def __init__(self):
        # 判断操作系统
        if sys.platform == "win32":  # Windows
            appdata = os.getenv("APPDATA")
            if appdata is None:
                raise EnvironmentError("APPDATA 环境变量未设置")
            self.db_path = os.path.join(
                appdata, "Cursor", "User", "globalStorage", "state.vscdb"
            )
        elif sys.platform == "darwin": # macOS
            self.db_path = os.path.abspath(os.path.expanduser(
                "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
            ))
        elif sys.platform == "linux" : # Linux 和其他类Unix系统
            self.db_path = os.path.abspath(os.path.expanduser(
                "~/.config/Cursor/User/globalStorage/state.vscdb"
            ))
        else:
            raise NotImplementedError(f"不支持的操作系统: {sys.platform}")

    def update_auth(self, email=None, access_token=None, refresh_token=None):
        """
        更新Cursor的认证信息
        :param email: 新的邮箱地址
        :param access_token: 新的访问令牌
        :param refresh_token: 新的刷新令牌
        :return: bool 是否成功更新
        """
        updates = []
        # 登录状态
        updates.append(("cursorAuth/cachedSignUpType", "Auth_0"))

        if email is not None:
            updates.append(("cursorAuth/cachedEmail", email))
        if access_token is not None:
            updates.append(("cursorAuth/accessToken", access_token))
        if refresh_token is not None:
            updates.append(("cursorAuth/refreshToken", refresh_token))

        if not updates:
            print("没有提供任何要更新的值")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for key, value in updates:

                # 如果没有更新任何行,说明key不存在,执行插入
                # 检查 accessToken 是否存在
                check_query = f"SELECT COUNT(*) FROM itemTable WHERE key = ?"
                cursor.execute(check_query, (key,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO itemTable (key, value) VALUES (?, ?)"
                    cursor.execute(insert_query, (key, value))
                else:
                    update_query = "UPDATE itemTable SET value = ? WHERE key = ?"
                    cursor.execute(update_query, (value, key))

                if cursor.rowcount > 0:
                    print(f"成功更新 {key.split('/')[-1]}")
                else:
                    print(f"未找到 {key.split('/')[-1]} 或值未变化")

            conn.commit()
            return True

        except sqlite3.Error as e:
            print("数据库错误:", str(e))
            return False
        except Exception as e:
            print("发生错误:", str(e))
            return False
        finally:
            if conn:
                conn.close()


def login_cursor(email, password):
    login_url = "https://authenticator.cursor.sh"
    settings_url = "https://www.cursor.com/settings"
    # 获取user_agent
    user_agent = get_user_agent()
    if not user_agent:
        logging.error("获取user agent失败，使用默认值")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # 剔除user_agent中的"HeadlessChrome"
    user_agent = user_agent.replace("HeadlessChrome", "Chrome")
    browser_manager = BrowserManager()
    browser = browser_manager.init_browser(user_agent)
    logging.info("开始登录")

    # # 获取并打印浏览器的user-agent
    # user_agent = browser.latest_tab.run_js("return navigator.userAgent")
    tab = browser.latest_tab
    tab.get(login_url)
    tab.actions.click("@name=email").input(email)
    tab.actions.click("@type=submit")

    tab.actions.click("@name=password").input(password)
    tab.actions.click("@type=submit")


    # 检查是否登录成功
    while True:
        if tab.ele("@type=submit"):
            time.sleep(0.5)  # 等待页面加载
            continue
        else:
            break
            
    handle_turnstile(tab)

    # # 检查是否需要处理邮箱验证码, 尝试 2 次
    for _ in range(2):
        try:
            if tab.ele('@class="rt-Text rt-r-weight-bold"'):
                logging.info("正在获取邮箱验证码...")
                code = EmailVerificationHandler(email).get_verification_code()
                if not code:
                    logging.error("获取验证码失败")
                    return False

                logging.info(f"成功获取验证码: {code}")
                logging.info("正在输入验证码...")
                i = 0
                for digit in code:
                    tab.ele(f"@data-index={i}").input(digit)
                    time.sleep(random.uniform(0.1, 0.3))
                    i += 1
                logging.info("验证码输入完成")
                break
        except Exception as e:
            logging.error(f"验证码处理过程出错: {str(e)}")

    # tab.get(settings_url)
    # try:
    #     usage_selector = (
    #         "css:div.col-span-2 > div > div > div > div > "
    #         "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
    #         "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
    #     )
    #     usage_ele = tab.ele(usage_selector)
    #     if usage_ele:
    #         usage_info = usage_ele.text
    #         total_usage = usage_info.split("/")[-1].strip()
    #         logging.info(f"账户可用额度上限: {total_usage}")
    #         return tab
    # except Exception as e:
    #     logging.error(f"获取账户额度信息失败: {str(e)}")

    return tab

def get_cursor_session_token(tab, max_attempts=3, retry_interval=2):
    """
    获取Cursor会话token，带有重试机制
    :param tab: 浏览器标签页
    :param max_attempts: 最大尝试次数
    :param retry_interval: 重试间隔(秒)
    :return: session token 或 None
    """
    logging.info("开始获取cookie")
    attempts = 0

    while attempts < max_attempts:
        try:
            cookies = tab.cookies()
            for cookie in cookies:
                if cookie.get("name") == "WorkosCursorSessionToken":
                    return cookie["value"].split("%3A%3A")[1]

            attempts += 1
            if attempts < max_attempts:
                logging.warning(
                    f"第 {attempts} 次尝试未获取到CursorSessionToken，{retry_interval}秒后重试..."
                )
                time.sleep(retry_interval)
            else:
                logging.error(
                    f"已达到最大尝试次数({max_attempts})，获取CursorSessionToken失败"
                )

        except Exception as e:
            logging.error(f"获取cookie失败: {str(e)}")
            attempts += 1
            if attempts < max_attempts:
                logging.info(f"将在 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
    logging.error("获取cookie失败")
    return None

def get_account_token(email, password):
    """
    获取账号的认证令牌
    
    Args:
        email: 邮箱地址
        password: 密码
        
    Returns:
        str: 认证令牌，如果获取失败则返回 None
    """
    tab = login_cursor(email, password)
    if tab:
        return get_cursor_session_token(tab)
    return None

if __name__ == "__main__":
    email = "jeylin7@steven111.filegear-sg.me"
    password = "fJoQ$bSqI!Wj"
    print(get_account_token(email, password))
