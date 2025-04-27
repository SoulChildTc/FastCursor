from dotenv import load_dotenv
import os
import sys
import random
from logger import logging
import codecs

class Config:
    def __init__(self):
        # 获取应用程序的根目录路径
        if getattr(sys, "frozen", False):
            # 如果是打包后的可执行文件
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))

        # 指定 .env 文件的路径
        self.dotenv_path = os.path.join(application_path, ".env")

        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(self.dotenv_path):
            logging.info(f"配置文件 {self.dotenv_path} 不存在，正在创建默认配置...")
            self.create_default_config()

        # 自定义加载 .env 文件，支持多种编码
        self.load_env_file()
        
        self.imap = False
        self.temp_mail = os.getenv("TEMP_MAIL", "").strip().split("@")[0]
        self.temp_mail_epin = os.getenv("TEMP_MAIL_EPIN", "").strip()
        self.temp_mail_ext = os.getenv("TEMP_MAIL_EXT", "").strip()
        
        # 处理多个域名，以逗号分隔
        domain_str = os.getenv("DOMAIN", "").strip()
        self.domains = [d.strip() for d in domain_str.split(',') if d.strip()]
        
        # 如果临时邮箱为null则加载IMAP
        if self.temp_mail == "null":
            self.imap = True
            self.imap_server = os.getenv("IMAP_SERVER", "").strip()
            self.imap_port = os.getenv("IMAP_PORT", "").strip()
            self.imap_user = os.getenv("IMAP_USER", "").strip()
            self.imap_pass = os.getenv("IMAP_PASS", "").strip()
            self.imap_dir = os.getenv("IMAP_DIR", "inbox").strip()

        # 启用定时注册
        self.enable_register = os.getenv("ENABLE_REGISTER", "false").strip() == "true"

        self.browser_path = os.getenv("BROWSER_PATH", "").strip()
        self.browser_headless = os.getenv("BROWSER_HEADLESS", "True").strip() == "True"
        self.browser_user_agent = os.getenv("BROWSER_USER_AGENT", "").strip()
        self.browser_proxy = os.getenv("BROWSER_PROXY", "").strip()
        self.mail_protocol = os.getenv("MAIL_PROTOCOL", "POP3").strip()

        self.check_config()

    def load_env_file(self):
        """自定义加载.env文件，支持多种编码"""
        if not os.path.exists(self.dotenv_path):
            logging.warning(f"配置文件不存在: {self.dotenv_path}")
            return
            
        # 尝试不同的编码方式读取文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'utf-16']
        env_contents = None
        
        for encoding in encodings:
            try:
                with codecs.open(self.dotenv_path, 'r', encoding=encoding) as f:
                    env_contents = f.read()
                logging.info(f"成功使用 {encoding} 编码读取配置文件")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logging.error(f"读取配置文件时出错 ({encoding}): {str(e)}")
                continue
        
        if env_contents is None:
            logging.error("无法使用任何编码读取配置文件，将使用默认配置")
            self.create_default_config()
            return
            
        # 手动解析环境变量并设置
        for line in env_contents.splitlines():
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
                
            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # 设置环境变量
                os.environ[key] = value
                
        logging.info("配置文件加载完成")

    def create_default_config(self):
        """创建默认的配置文件"""
        default_config = """# FastCursor 配置文件
# 临时邮箱配置
TEMP_MAIL=example
TEMP_MAIL_EPIN=
TEMP_MAIL_EXT=@mailto.plus

# 域名配置 (多个域名用逗号分隔)
DOMAIN=example.com,another-example.com

# 浏览器配置
BROWSER_PATH=
BROWSER_HEADLESS=True
BROWSER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.92 Safari/537.36
BROWSER_PROXY=
"""
        try:
            with codecs.open(self.dotenv_path, "w", "utf-8") as f:
                f.write(default_config)
            logging.info(f"默认配置文件已创建: {self.dotenv_path}")
        except Exception as e:
            logging.error(f"创建默认配置文件失败: {e}")
            raise

    def save_env_config(self, config_dict):
        """保存配置到 .env 文件"""
        current_config = {}
        
        # 首先尝试读取现有配置
        if os.path.exists(self.dotenv_path):
            # 尝试不同的编码方式读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'utf-16']
            for encoding in encodings:
                try:
                    with codecs.open(self.dotenv_path, 'r', encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                current_config[key.strip()] = value.strip()
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logging.error(f"读取配置文件失败 ({encoding}): {e}")
                    continue
        
        # 更新配置
        current_config.update(config_dict)
        
        config_str = ""
        config_str += "# 临时邮箱配置\n"
        for key in ["TEMP_MAIL", "TEMP_MAIL_EPIN", "TEMP_MAIL_EXT"]:
            if key in current_config:
                config_str += f"{key}={current_config[key]}\n"
        
        config_str += "\n# 域名配置\n"
        if "DOMAIN" in current_config:
            config_str += f"DOMAIN={current_config['DOMAIN']}\n"
        
        config_str += "\n# 浏览器配置\n"
        for key in ["BROWSER_PATH", "BROWSER_HEADLESS", "BROWSER_USER_AGENT", "BROWSER_PROXY"]:
            if key in current_config:
                config_str += f"{key}={current_config[key]}\n"
        
        try:
            # 始终使用UTF-8编码保存
            with codecs.open(self.dotenv_path, "w", "utf-8") as f:
                f.write(config_str)
            
            # 重新加载配置
            self.load_env_file()
            return True
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
            return False
    
    def get_temp_mail(self):
        return self.temp_mail

    def get_temp_mail_epin(self):
        return self.temp_mail_epin

    def get_temp_mail_ext(self):
        return self.temp_mail_ext

    def get_imap(self):
        if not self.imap:
            return False
        return {
            "imap_server": self.imap_server,
            "imap_port": self.imap_port,
            "imap_user": self.imap_user,
            "imap_pass": self.imap_pass,
            "imap_dir": self.imap_dir,
        }

    def get_domain(self):
        """随机返回一个域名
        
        Returns:
            str: 随机选择的域名
        """
        if not self.domains:
            return ""
        return random.choice(self.domains)

    def get_protocol(self):
        """获取邮件协议类型
        
        Returns:
            str: 'IMAP' 或 'POP3'
        """
        return os.getenv('IMAP_PROTOCOL', 'POP3')

    def check_config(self):
        """检查配置项是否有效

        检查规则：
        1. 如果使用 tempmail.plus，需要配置 TEMP_MAIL 和 DOMAIN
        2. 如果使用 IMAP，需要配置 IMAP_SERVER、IMAP_PORT、IMAP_USER、IMAP_PASS
        3. IMAP_DIR 是可选的
        """
        # 基础配置检查
        required_configs = {
            "domains": "域名",
        }

        # 检查基础配置
        for key, name in required_configs.items():
            if key == "domains" and not self.domains:
                raise ValueError(f"{name}未配置，请在 .env 文件中设置 DOMAIN")
            elif key != "domains" and not self.check_is_valid(getattr(self, key)):
                raise ValueError(f"{name}未配置，请在 .env 文件中设置 {key.upper()}")

        # 检查邮箱配置
        if self.temp_mail != "null":
            # tempmail.plus 模式
            if not self.check_is_valid(self.temp_mail):
                raise ValueError("临时邮箱未配置，请在 .env 文件中设置 TEMP_MAIL")
        else:
            # IMAP 模式
            imap_configs = {
                "imap_server": "IMAP服务器",
                "imap_port": "IMAP端口",
                "imap_user": "IMAP用户名",
                "imap_pass": "IMAP密码",
            }

            for key, name in imap_configs.items():
                value = getattr(self, key)
                if value == "null" or not self.check_is_valid(value):
                    raise ValueError(
                        f"{name}未配置，请在 .env 文件中设置 {key.upper()}"
                    )

            # IMAP_DIR 是可选的，如果设置了就检查其有效性
            if self.imap_dir != "null" and not self.check_is_valid(self.imap_dir):
                raise ValueError(
                    "IMAP收件箱目录配置无效，请在 .env 文件中正确设置 IMAP_DIR"
                )

    def check_is_valid(self, value):
        """检查配置项是否有效

        Args:
            value: 配置项的值

        Returns:
            bool: 配置项是否有效
        """
        return isinstance(value, str) and len(str(value).strip()) > 0

    def print_config(self):
        if self.imap:
            logging.info(f"IMAP服务器: {self.imap_server}")
            logging.info(f"IMAP端口: {self.imap_port}")
            logging.info(f"IMAP用户名: {self.imap_user}")
            logging.info(f"IMAP密码: {'*' * len(self.imap_pass)}")
            logging.info(f"IMAP收件箱目录: {self.imap_dir}")
        if self.temp_mail != "null":
            logging.info(f"临时邮箱: {self.temp_mail}{self.temp_mail_ext}")
        logging.info(f"可用域名: {', '.join(self.domains)}")
        logging.info(f"当前使用域名: {self.get_domain()}")


# 使用示例
if __name__ == "__main__":
    try:
        config = Config()
        print("环境变量加载成功！")
        config.print_config()
    except ValueError as e:
        print(f"错误: {e}")
