import pymysql
import sqlite3
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

class _MySQLAdapter:
    def __init__(self, db_config, db_name):
        self.db_config = db_config.copy()
        self.db_name = db_name
        self.init_db()
        self.db_config['database'] = self.db_name
    def get_connection(self):
        return pymysql.connect(**self.db_config)
    def init_db(self):
        config = self.db_config.copy()
        config.pop('database', None)
        conn = pymysql.connect(**config)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES LIKE %s", (self.db_name,))
                if not cursor.fetchone():
                    logging.info(f"数据库 {self.db_name} 不存在，开始创建")
                    cursor.execute(
                        f"CREATE DATABASE {self.db_name} "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                    logging.info(f"数据库 {self.db_name} 创建成功")
                cursor.execute(f"USE {self.db_name}")
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
    def paramstyle(self):
        return '%s'
    def dict_cursor(self):
        return pymysql.cursors.DictCursor
    def integrity_error(self):
        return pymysql.IntegrityError

class _SQLiteAdapter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    status TEXT NOT NULL,
                    register_time TEXT NOT NULL,
                    last_allocated_time TEXT,
                    metadata TEXT,
                    token TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            conn.commit()
        finally:
            conn.close()
    def paramstyle(self):
        return '?'
    def dict_cursor(self):
        return None  # 用 row_factory 直接转 dict
    def integrity_error(self):
        return sqlite3.IntegrityError

class AccountManager:
    def __init__(self):
        """初始化账号管理器"""
        load_dotenv()
        db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        if db_type == 'sqlite':
            self.adapter = _SQLiteAdapter(os.getenv('SQLITE_DB_PATH', './cursor_accounts.sqlite3'))
            self.is_sqlite = True
        else:
            self.db_name = os.getenv('MYSQL_DATABASE', 'cursor_accounts')
            self.db_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'charset': 'utf8mb4'
            }
            self.adapter = _MySQLAdapter(self.db_config, self.db_name)
            self.is_sqlite = False

    def get_connection(self):
        return self.adapter.get_connection()

    def init_db(self):
        self.adapter.init_db()

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
                param = self.adapter.paramstyle()
                sql = f'''
                    INSERT INTO accounts (email, password, first_name, last_name, 
                                       status, register_time, metadata, token)
                    VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param})
                '''
                values = (
                    email, password, first_name, last_name,
                    AccountStatus.AVAILABLE.value,
                    datetime.now().isoformat() if self.is_sqlite else datetime.now(),
                    json.dumps(metadata) if metadata else None,
                    token
                )
                cursor.execute(sql, values)
                conn.commit()
                return True
        except self.adapter.integrity_error():
            return False

    def update_account_token(self, email: str, token: str) -> bool:
        """更新账号令牌
        
        Args:
            email: 邮箱地址
            token: 账号令牌
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            param = self.adapter.paramstyle()
            sql = f'UPDATE accounts SET token = {param} WHERE email = {param}'
            cursor.execute(sql, (token, email))
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
            if self.is_sqlite:
                cursor = conn.cursor()
                param = self.adapter.paramstyle()
                sql = f'SELECT id, email, password, token FROM accounts WHERE id = {param}'
                cursor.execute(sql, (account_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                result = dict(result)
            else:
                cursor = conn.cursor(self.adapter.dict_cursor())
                param = self.adapter.paramstyle()
                sql = f'SELECT id, email, password, token FROM accounts WHERE id = {param}'
                cursor.execute(sql, (account_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                    
            if result['token'] is None or result['token'] == '':
                logging.info(f"未发现账号令牌, 获取账号令牌: {result['email']}")
                token = get_account_token(result['email'], result['password'])
                if token:
                    self.update_account_token(result['email'], token)
            self.mark_account_status(result['email'], AccountStatus.ALLOCATED, True)
            return {
                'email': result['email'],
                'password': result['password'],
                'token': token
            }

    def get_available_account(self) -> Optional[Dict]:
        """获取一个可用的账号并标记为已分配
        
        Returns:
            Dict: 账号信息，如果没有可用账号则返回 None
        """
        with self.get_connection() as conn:
            if self.is_sqlite:
                cursor = conn.cursor()
                param = self.adapter.paramstyle()
                sql = f'SELECT id, email, password, token FROM accounts WHERE status = {param} ORDER BY register_time ASC LIMIT 1'
                cursor.execute(sql, (AccountStatus.AVAILABLE.value,))
                result = cursor.fetchone()
                if not result:
                    return None
                result = dict(result)
                update_sql = f'UPDATE accounts SET status = {param}, last_allocated_time = {param} WHERE id = {param}'
                cursor.execute(update_sql, (
                    AccountStatus.ALLOCATED.value,
                    datetime.now().isoformat(),
                    result['id']
                ))
                conn.commit()
                email, password, token = result['email'], result['password'], result['token']
            else:
                cursor = conn.cursor()
                param = self.adapter.paramstyle()
                sql = f'SELECT id, email, password, token FROM accounts WHERE status = {param} ORDER BY register_time ASC LIMIT 1'
                cursor.execute(sql, (AccountStatus.AVAILABLE.value,))
                result = cursor.fetchone()
                if not result:
                    return None
                update_sql = f'UPDATE accounts SET status = {param}, last_allocated_time = {param} WHERE id = {param}'
                cursor.execute(update_sql, (
                    AccountStatus.ALLOCATED.value,
                    datetime.now(),
                    result[0]
                ))
                conn.commit()
                _, email, password, token = result
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
            param = self.adapter.paramstyle()
            if is_allocated:
                last_allocated_time = datetime.now().isoformat() if self.is_sqlite else datetime.now()
                sql = f'UPDATE accounts SET status = {param}, last_allocated_time = {param} WHERE email = {param}'
                cursor.execute(sql, (status.value, last_allocated_time, email))
            else:
                sql = f'UPDATE accounts SET status = {param} WHERE email = {param}'
                cursor.execute(sql, (status.value, email))
            conn.commit()
            return cursor.rowcount > 0

    def get_accounts_stats(self) -> Dict:
        """获取账号统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = 'SELECT status, COUNT(*) FROM accounts GROUP BY status'
            cursor.execute(sql)
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
            if self.is_sqlite:
                cursor = conn.cursor()
                sql = 'SELECT id, email, password, token, status, register_time, last_allocated_time FROM accounts'
                cursor.execute(sql)
                return [dict(row) for row in cursor.fetchall()]
            else:
                cursor = conn.cursor(self.adapter.dict_cursor())
                sql = 'SELECT id, email, password, token, status, register_time, last_allocated_time FROM accounts'
                cursor.execute(sql)
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
            param = self.adapter.paramstyle()
            sql = f'UPDATE accounts SET status = {param} WHERE email LIKE {param}'
            cursor.execute(sql, (AccountStatus.INVALID.value, f'%{suffix}'))
            conn.commit()
            return cursor.rowcount > 0

    def reset_old_accounts(self) -> int:
        """重置注册时间超过30天且非无效状态的账号为可用状态
        
        Returns:
            int: 更新的账号数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.is_sqlite:
                sql = """
                    UPDATE accounts 
                    SET status = ?
                    WHERE status != ? 
                    AND julianday('now') - julianday(register_time) > 30
                """
                cursor.execute(sql, (AccountStatus.AVAILABLE.value, AccountStatus.INVALID.value))
            else:
                sql = '''
                    UPDATE accounts 
                    SET status = %s
                    WHERE status != %s 
                    AND DATEDIFF(CURRENT_TIMESTAMP, register_time) > 30
                '''
                cursor.execute(sql, (AccountStatus.AVAILABLE.value, AccountStatus.INVALID.value))
            conn.commit()
            return cursor.rowcount

if __name__ == "__main__":
    account_manager = AccountManager()
    # account = account_manager.add_account(email="jeylin7@steven111.filegear-sg.me", password="fJoQ$bSqI!Wj", first_name="test", last_name="test")
    account = account_manager.get_available_account()
    account_manager.mark_account_status(account['email'], AccountStatus.AVAILABLE)
    logging.info(account)