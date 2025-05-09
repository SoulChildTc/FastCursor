from cursor_auth_manager import CursorAuthManager
from reset_machine_v2 import reset_machine_id
from logger import logging
from exit_cursor import RestartCursor
from account_manager import AccountManager, AccountStatus
from config import Config
from exchange_token import get_new_token

config = Config()

def update_cursor_auth(email=None, access_token=None, refresh_token=None):
    """
    更新Cursor的认证信息的便捷函数
    """
    auth_manager = CursorAuthManager()
    return auth_manager.update_auth(email, access_token, refresh_token)

def reset_cursor_machine_id(restart=True):
    """
    重置Cursor的机器ID
    """
    reset_machine_id()
    if restart:
        RestartCursor()

def change_cursor_account(account_id=None, email=None, token=None):
    """
    更换 Cursor 账号
    """
    try:
        if email is not None and token is not None:
            account_data = {
                "email": email,
                "token": token
            }

        elif account_id:
            account_manager = AccountManager()

            account_data = account_manager.get_account_by_id(account_id)
        else:
            account_manager = AccountManager()
            account_data = account_manager.get_available_account()

        email = account_data.get("email")
        token = account_data.get("token")
        
        if not email or not token:
            logging.error("暂无可用账号")
            return
            
        token = get_new_token(token)

        update_cursor_auth(
            email=email, 
            access_token=token, 
            refresh_token=token
        )
        reset_cursor_machine_id(restart=True)
        
    except Exception as e:
        logging.error(f"更换账号失败: {e}")

if __name__ == "__main__":
    change_cursor_account()
