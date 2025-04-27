import os
import sys
import argparse
from account_manager import AccountManager
from change_account import change_cursor_account

os.environ["PYTHONVERBOSE"] = "0"
os.environ["PYINSTALLER_VERBOSE"] = "0"


from utils import *
from cursor_auth_manager import get_cursor_session_token

login_url = "https://authenticator.cursor.sh"
sign_up_url = "https://authenticator.cursor.sh/sign-up"
settings_url = "https://www.cursor.com/settings"


def add_account(email, password, first_name, last_name, token):
    account_manager = AccountManager()
    account_manager.add_account(email=email, password=password, first_name=first_name, last_name=last_name, token=token)


def sign_up_account(browser, tab, account, first_name, last_name, password, email_handler, save_to_db=True, change_account=False):
    logging.info("=== 开始注册账号流程 ===")
    logging.info(f"正在访问注册页面: {sign_up_url}")
    tab.get(sign_up_url)

    try:
        if tab.ele("@name=first_name"):
            logging.info("正在填写个人信息...")
            tab.actions.click("@name=first_name").input(first_name)
            logging.info(f"已输入名字: {first_name}")
            time.sleep(random.uniform(1, 3))

            tab.actions.click("@name=last_name").input(last_name)
            logging.info(f"已输入姓氏: {last_name}")
            time.sleep(random.uniform(1, 3))

            tab.actions.click("@name=email").input(account)
            logging.info(f"已输入邮箱: {account}")
            time.sleep(random.uniform(1, 3))

            logging.info("提交个人信息...")
            tab.actions.click("@type=submit")

    except Exception as e:
        logging.error(f"注册页面访问失败: {str(e)}")
        return False

    handle_turnstile(tab)

    try:
        if tab.ele("@name=password"):
            logging.info("正在设置密码...")
            tab.ele("@name=password").input(password)
            time.sleep(random.uniform(1, 3))

            logging.info("提交密码...")
            tab.ele("@type=submit").click()
            logging.info("密码设置完成，等待系统响应...")

    except Exception as e:
        logging.error(f"密码设置失败: {str(e)}")
        return False

    if tab.ele("This email is not available."):
        logging.error("注册失败：邮箱已被使用")
        return False

    handle_turnstile(tab)

    while True:
        try:
            if tab.ele("Account Settings"):
                logging.info("注册成功 - 已进入账户设置页面")
                break
            if tab.ele("@data-index=0"):
                logging.info("正在获取邮箱验证码...")
                code = email_handler.get_verification_code()
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

    handle_turnstile(tab)
    
    # wait_time = random.randint(3, 6)
    # for i in range(wait_time):
    #     logging.info(f"等待系统处理中... 剩余 {wait_time-i} 秒")
    #     time.sleep(1)

    # logging.info("正在获取账户信息...")
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

    # except Exception as e:
    #     logging.error(f"获取账户额度信息失败: {str(e)}")



    logging.info("正在获取会话令牌...")
    token = get_cursor_session_token(tab)


    logging.info("\n=== 注册完成 ===")
    logging.info(f"Cursor 账号信息:\n邮箱: {account}\n密码: {password}")

    if save_to_db:
        logging.info("正在将账号信息保存到数据库...")
        add_account(account, password, first_name, last_name, token)
        logging.info("账号信息已保存到数据库")
    else:
        logging.info("根据设置，账号信息不会保存到数据库")
    
    if change_account:
        change_cursor_account(None, account, token)

    return True


def register_account(save_to_db=True, change_account=False):
    """
    账号注册
    
    Args:
        save_to_db: 是否将账号保存到数据库，默认为True
    
    Returns:
        注册成功与否
    """
    browser_manager = None
    try:
        logging.info("\n=== 初始化程序 ===")

        logging.info("正在初始化浏览器...")

        # 获取user_agent
        user_agent = get_user_agent()
        if not user_agent:
            logging.error("获取user agent失败，使用默认值")
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # 剔除user_agent中的"HeadlessChrome"
        user_agent = user_agent.replace("HeadlessChrome", "Chrome")

        browser_manager = BrowserManager()
        browser = browser_manager.init_browser(user_agent)

        # 获取并打印浏览器的user-agent
        user_agent = browser.latest_tab.run_js("return navigator.userAgent")


        logging.info("正在生成随机账号信息...")

        email_generator = EmailGenerator()
        first_name = email_generator.default_first_name
        last_name = email_generator.default_last_name
        account = email_generator.generate_email()
        password = email_generator.default_password

        logging.info(f"生成的邮箱账号: {account}")

        logging.info("正在初始化邮箱验证模块...")
        email_handler = EmailVerificationHandler(account)

        auto_update_cursor_auth = True

        tab = browser.latest_tab

        tab.run_js("try { turnstile.reset() } catch(e) { }")

        logging.info("\n=== 开始注册流程 ===")
        logging.info(f"正在访问登录页面: {login_url}")
        tab.get(login_url)

        sign_up_account(browser, tab, account, first_name, last_name, password, email_handler, save_to_db, change_account)
            

    except Exception as e:
        logging.error(f"程序执行出现错误: {str(e)}")
        import traceback

        logging.error(traceback.format_exc())
    finally:
        if browser_manager:
            browser_manager.quit()


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='注册Cursor账号')
    parser.add_argument('--no-save', action='store_true', help='不将账号保存到数据库')
    parser.add_argument('--change-account', action='store_true', help='不将账号保存到数据库')
    args = parser.parse_args()
    
    # 根据参数决定是否保存账号
    save_to_db = not args.no_save
    change_account = args.change_account
    
    if not save_to_db:
        logging.info("启用了--no-save参数，账号将不会保存到数据库")
    
    register_account(save_to_db, change_account)