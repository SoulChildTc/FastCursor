import pymysql
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
import json
import os
from dotenv import load_dotenv
from logger import logging
from cursor_auth_manager import get_account_token

class AccountStatus(Enum):
    """账号状态枚举"""
    AVAILABLE = 'available'  # 可用
    ALLOCATED = 'allocated'  # 已分配
    INVALID = 'invalid'      # 无效

class AccountManager:
    def __init__(self):
        """初始化账号管理器"""
        load_dotenv()
        self.db_name = os.getenv('MYSQL_DATABASE', 'cursor_accounts')
        # 初始配置不包含数据库名，用于创建数据库
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'charset': 'utf8mb4'
        }
        self.init_db()
        # 添加数据库名到配置中
        self.db_config['database'] = self.db_name
    
    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config)
    
    def init_db(self):
        """初始化数据库和表结构"""
        # 创建数据库连接（不指定数据库）
        conn = pymysql.connect(**self.db_config)
        try:
            with conn.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute("SHOW DATABASES LIKE %s", (self.db_name,))
                if not cursor.fetchone():
                    logging.info(f"数据库 {self.db_name} 不存在，开始创建")
                    # 创建数据库
                    cursor.execute(
                        f"CREATE DATABASE {self.db_name} "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                    logging.info(f"数据库 {self.db_name} 创建成功")
                
                # 选择数据库
                cursor.execute(f"USE {self.db_name}")
                
                # 创建表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        status VARCHAR(20) NOT NULL,
                        register_time TIMESTAMP NOT NULL,
                        last_allocated_time TIMESTAMP NULL,
                        metadata JSON,
                        token TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                conn.commit()
        except pymysql.Error as e:
            logging.error(f"数据库初始化错误: {e}")
            raise
        finally:
            conn.close()
    
    def add_account(self, email: str, password: str, first_name: str = None, 
                   last_name: str = None, metadata: Dict = None, token: str = None) -> bool:
        """添加新账号
        
        Args:
            email: 邮箱地址
            password: 密码
            first_name: 名
            last_name: 姓
            metadata: 其他元数据
            token: 账号令牌
        
        Returns:
            bool: 是否添加成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO accounts (email, password, first_name, last_name, 
                                       status, register_time, metadata, token)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    email, password, first_name, last_name,
                    AccountStatus.AVAILABLE.value,
                    datetime.now(),
                    json.dumps(metadata) if metadata else None,
                    token
                ))
                conn.commit()
                return True
        except pymysql.IntegrityError:
            return False
    
    def update_account_token(self, email: str, token: str) -> bool:
        """更新账号令牌
        
        Args:
            email: 邮箱地址
            token: 账号令牌
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts 
                SET token = %s 
                WHERE email = %s
            ''', (token, email))
            conn.commit()
            return cursor.rowcount > 0

    def get_account_by_id(self, account_id: int) -> Optional[Dict]:
        """根据账号ID获取账号信息
        
        Args:
            account_id: 账号ID
        Returns:
            Dict: 账号信息，如果没有找到则返回 None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, email, password, token
                FROM accounts 
                WHERE id = %s
            ''', (account_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
            
            self.mark_account_status(result['email'], AccountStatus.ALLOCATED, True)
            return result
    
    def get_available_account(self) -> Optional[Dict]:
        """获取一个可用的账号并标记为已分配
        
        Returns:
            Dict: 账号信息，如果没有可用账号则返回 None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, email, password, token
                FROM accounts 
                WHERE status = %s
                ORDER BY register_time ASC
                LIMIT 1
            ''', (AccountStatus.AVAILABLE.value,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # 更新账号状态
            cursor.execute('''
                UPDATE accounts 
                SET status = %s, last_allocated_time = %s
                WHERE id = %s
            ''', (
                AccountStatus.ALLOCATED.value,
                datetime.now(),
                result[0]
            ))
            conn.commit()
            
            account_id, email, password, token = result
            
            if token is None:
                logging.info(f"未发现账号令牌, 获取账号令牌: {email}")
                token = get_account_token(email, password)
                if token:
                    self.update_account_token(email, token)

            return {
                'email': email,
                'password': password,
                'token': token
            }
    
    def mark_account_status(self, email: str, status: AccountStatus, is_allocated: bool = False) -> bool:
        """标记账号状态
        
        Args:
            email: 邮箱地址
            status: 新状态
            is_allocated: 是否更新分配时间
        Returns:
            bool: 是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if is_allocated:
                last_allocated_time = datetime.now()

                cursor.execute('''
                    UPDATE accounts 
                    SET status = %s, last_allocated_time = %s
                    WHERE email = %s
                ''', (status.value, last_allocated_time, email))
            else:
                cursor.execute('''
                    UPDATE accounts 
                    SET status = %s,
                    WHERE email = %s
                ''', (status.value, email))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_accounts_stats(self) -> Dict:
        """获取账号统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM accounts 
                GROUP BY status
            ''')
            stats = {row[0]: row[1] for row in cursor.fetchall()}
            return {
                'total': sum(stats.values()),
                'available': stats.get(AccountStatus.AVAILABLE.value, 0),
                'allocated': stats.get(AccountStatus.ALLOCATED.value, 0),
                'invalid': stats.get(AccountStatus.INVALID.value, 0)
            } 

    def get_all_accounts(self) -> List[Dict]:
        """获取所有账号列表
        
        Returns:
            List[Dict]: 账号列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute('''
                SELECT id, email, password, token, status, register_time, last_allocated_time
                FROM accounts
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def batch_mark_invalid_by_suffix(self, suffix: str) -> bool:
        """批量标记指定后缀的邮箱为无效状态
        
        Args:
            suffix: 邮箱后缀
            
        Returns:
            bool: 是否更新成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts 
                SET status = %s
                WHERE email LIKE %s
            ''', (AccountStatus.INVALID.value, f'%{suffix}'))
            conn.commit()
            return cursor.rowcount > 0

    def reset_old_accounts(self) -> int:
        """重置注册时间超过30天且非无效状态的账号为可用状态
        
        Returns:
            int: 更新的账号数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounts 
                SET status = %s
                WHERE status != %s 
                AND DATEDIFF(CURRENT_TIMESTAMP, register_time) > 30
            ''', (AccountStatus.AVAILABLE.value, AccountStatus.INVALID.value))
            conn.commit()
            return cursor.rowcount


if __name__ == "__main__":
    account_manager = AccountManager()
    # account = account_manager.add_account(email="jeylin7@steven111.filegear-sg.me", password="fJoQ$bSqI!Wj", first_name="test", last_name="test")
    account = account_manager.get_available_account()
    account_manager.mark_account_status(account['email'], AccountStatus.AVAILABLE)
    logging.info(account)