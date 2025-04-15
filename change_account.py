from cursor_auth_manager import CursorAuthManager
from reset_machine_v2 import reset_machine_id
from logger import logging
from exit_cursor import RestartCursor
from account_manager import AccountManager, AccountStatus
from config import Config

config = Config()
account_manager = AccountManager()

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

def change_cursor_account(account_id=None):
    """
    更换 Cursor 账号
    """
    try:
        if account_id:
            account_data = account_manager.get_account_by_id(account_id)
        else:
            account_data = account_manager.get_available_account()

        email = account_data.get("email")
        token = account_data.get("token")
        
        if not email or not token:
            logging.error("暂无可用账号")
            return
            
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
