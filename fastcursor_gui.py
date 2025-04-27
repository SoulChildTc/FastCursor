import sys
import os
import time
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QTextEdit, QLabel, QFrame,
                            QGraphicsDropShadowEffect, QSizePolicy, QGridLayout,
                            QLineEdit, QCheckBox, QTabWidget, QComboBox, QDialog,
                            QDialogButtonBox, QFormLayout, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QEvent
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap, QPalette, QLinearGradient, QGradient
import logging

# 导入需要的函数
from register_account import register_account
from change_account import reset_cursor_machine_id
from config import Config

# 设置日志处理器，将日志重定向到GUI
class QTextEditLogger(QObject, logging.Handler):
    log_signal = pyqtSignal(str)
    
    # 保持一个全局引用
    _instances = []

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.log_signal.connect(self.append_log)
        # 添加到实例列表中
        QTextEditLogger._instances.append(self)

    def emit(self, record):
        try:
            log_message = self.format(record)
            self.log_signal.emit(log_message)
        except Exception:
            # 捕获所有异常，防止日志记录失败导致应用崩溃
            pass

    def append_log(self, message):
        try:
            if not self.text_edit:
                return
                
            self.text_text = message.replace("INFO", "<span style='color:#4fc1e9;font-weight:bold;'>INFO</span>") \
                           .replace("ERROR", "<span style='color:#ed5565;font-weight:bold;'>ERROR</span>") \
                           .replace("WARNING", "<span style='color:#ffce54;font-weight:bold;'>WARNING</span>")
            
            self.text_edit.append(self.text_text)
            scrollbar = self.text_edit.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
        except Exception:
            # 捕获所有异常，防止日志记录失败导致应用崩溃
            pass
    
    @classmethod
    def cleanup(cls):
        """清理所有实例"""
        for instance in cls._instances:
            try:
                if hasattr(instance, 'log_signal') and instance.log_signal:
                    instance.log_signal.disconnect()
            except Exception:
                pass
        cls._instances.clear()

# 自定义按钮类
class ModernButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        if icon_text:
            text = f"{icon_text}  {text}"
        super().__init__(text, parent)
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # 设置鼠标指针为手型
        self.setCursor(Qt.CursorShape.PointingHandCursor)

# 配置对话框
class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("配置设置")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #292d3e;
            }
            QGroupBox {
                font-weight: bold;
                color: #c3cee3;
                border: 1px solid #3b4064;
                border-radius: 8px;
                margin-top: 1.5ex;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #a6accd;
                font-size: 14px;
                margin-right: 10px;
            }
            QLineEdit, QComboBox {
                background-color: #202331;
                color: #eeffff;
                border: 1px solid #3b4064;
                border-radius: 4px;
                padding: 8px;
                min-height: 30px;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #202331;
                color: #eeffff;
                border: 1px solid #3b4064;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-height: 80px;
            }
            QCheckBox {
                color: #a6accd;
                font-size: 14px;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QTabWidget {
                background-color: transparent;
            }
            QTabWidget::pane {
                border: 1px solid #3b4064;
                border-radius: 8px;
                background-color: #292d3e;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #202331;
                color: #a6accd;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 14px;
            }
            QTabBar::tab:hover {
                background-color: #2a2f42;
                color: #d5defa;
            }
            QTabBar::tab:selected {
                background-color: #3b4064;
                color: #eeffff;
                font-weight: bold;
            }
            QDialogButtonBox {
                padding: 10px;
            }
            QDialogButtonBox QPushButton {
                min-width: 100px;
                min-height: 35px;
            }
        """)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 临时邮箱选项卡
        temp_mail_tab = QWidget()
        temp_mail_layout = QFormLayout(temp_mail_tab)
        temp_mail_layout.setSpacing(15)
        temp_mail_layout.setContentsMargins(20, 20, 20, 20)
        
        self.temp_mail_edit = QLineEdit(self.config.get_temp_mail())
        self.temp_mail_epin_edit = QLineEdit(self.config.get_temp_mail_epin())
        self.temp_mail_ext_edit = QLineEdit(self.config.get_temp_mail_ext() or "@mailto.plus")
        self.domain_edit = QTextEdit()
        self.domain_edit.setText(", ".join(self.config.domains))
        self.domain_edit.setMinimumHeight(80)
        
        # 设置输入框最小宽度
        self.temp_mail_edit.setMinimumWidth(300)
        self.temp_mail_epin_edit.setMinimumWidth(300)
        self.temp_mail_ext_edit.setMinimumWidth(300)
        self.domain_edit.setMinimumWidth(300)
        
        temp_mail_layout.addRow("临时邮箱用户名:", self.temp_mail_edit)
        temp_mail_layout.addRow("临时邮箱PIN码:", self.temp_mail_epin_edit)
        temp_mail_layout.addRow("临时邮箱后缀:", self.temp_mail_ext_edit)
        
        # 删除原来的单独布局，直接添加到表单布局中，与其他输入框保持一致
        temp_mail_layout.addRow("可用域名 (多个用逗号分隔):", self.domain_edit)
        
        # 常规设置选项卡
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        general_layout.setSpacing(15)
        general_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建普通复选框
        self.headless_checkbox = QCheckBox("")
        self.headless_checkbox.setChecked(self.config.browser_headless)
        self.headless_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.user_agent_edit = QLineEdit(self.config.browser_user_agent)
        self.browser_proxy_edit = QLineEdit(self.config.browser_proxy)
        
        # 设置输入框最小宽度
        self.user_agent_edit.setMinimumWidth(300)
        self.browser_proxy_edit.setMinimumWidth(300)
        
        general_layout.addRow("浏览器无头模式:", self.headless_checkbox)
        general_layout.addRow("浏览器用户代理:", self.user_agent_edit)
        general_layout.addRow("浏览器代理:", self.browser_proxy_edit)
        
        # 添加选项卡到选项卡控件
        tab_widget.addTab(temp_mail_tab, "临时邮箱配置")
        tab_widget.addTab(general_tab, "常规设置")
        
        # 设置默认选中临时邮箱选项卡
        tab_widget.setCurrentIndex(0)
        
        # 为选项卡设置手型指针
        tab_widget.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_config)
        buttons.rejected.connect(self.reject)
        
        # 设置按钮样式
        for button in buttons.buttons():
            if buttons.buttonRole(button) == QDialogButtonBox.ButtonRole.AcceptRole:
                button.setStyleSheet("""
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #4facfe, stop:1 #00f2fe);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                """)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                button.setStyleSheet("""
                    background-color: #3b4064;
                    color: #a6accd;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                """)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(buttons)
    
    def save_config(self):
        try:
            config_dict = {
                "TEMP_MAIL": self.temp_mail_edit.text(),
                "TEMP_MAIL_EPIN": self.temp_mail_epin_edit.text(),
                "TEMP_MAIL_EXT": self.temp_mail_ext_edit.text(),
                "DOMAIN": self.domain_edit.toPlainText(),
                "BROWSER_HEADLESS": "True" if self.headless_checkbox.isChecked() else "False",
                "BROWSER_USER_AGENT": self.user_agent_edit.text(),
                "BROWSER_PROXY": self.browser_proxy_edit.text()
            }
            
            success = self.config.save_env_config(config_dict)
            if success:
                self.accept()
            else:
                # 可以添加一个错误提示对话框
                self.reject()
        except Exception as e:
            logging.error(f"保存配置时出错: {e}")
            self.reject()

# 主窗口类
class FastCursorGUI(QMainWindow):
    # 定义信号用于线程间通信
    update_ui_signal = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        try:
            self.setup_ui()
            self.setup_logger()
            self.setWindowTitle("Fast Cursor 助手")
            
            # 连接信号到槽函数
            self.update_ui_signal.connect(self.update_ui_status)
            
            # 设置按钮鼠标指针样式
            self.config_button.setCursor(Qt.CursorShape.PointingHandCursor)
        except Exception as e:
            print(f"初始化错误: {e}")
            # 紧急后备UI，确保窗口至少能显示
            self.setMinimumSize(600, 400)
            self.setWindowTitle("Fast Cursor 助手 (错误)")
            
            layout = QVBoxLayout()
            error_label = QLabel(f"初始化错误: {e}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
            
            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

    def setup_ui(self):
        self.setMinimumSize(1000, 650)
        
        # 设置全局样式
        self.setStyleSheet("""
            /* 全局样式 */
            QMainWindow {
                background-color: #292d3e;
            }
            
            /* 侧边栏样式 */
            #sidebar {
                background-color: #292d3e;
                border-radius: 12px;
                margin: 10px 0 10px 10px;
            }
            
            QLabel#appTitle {
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding: 15px 0;
            }
            
            QLabel#appVersion {
                color: #676f8a;
                font-size: 12px;
                margin-top: -10px;
            }
            
            /* 按钮样式 */
            QPushButton {
                border: none;
                border-radius: 10px;
                padding: 15px;
                font-size: 15px;
                font-weight: 500;
                letter-spacing: 0.3px;
            }
            
            QPushButton#primaryButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #4facfe, stop:1 #00f2fe);
                color: white;
            }
            
            QPushButton#primaryButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #5dbcff, stop:1 #4dfffe);
            }
            
            QPushButton#primaryButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #4498e5, stop:1 #00d8e4);
            }
            
            QPushButton#primaryButton:disabled {
                background-color: #a9b7c6;
                color: #e1e1e1;
            }
            
            QPushButton#secondaryButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #ff9966, stop:1 #ff5e62);
                color: white;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #ffa97a, stop:1 #ff7377);
            }
            
            QPushButton#secondaryButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop:0 #e58c5c, stop:1 #e55459);
            }
            
            QPushButton#secondaryButton:disabled {
                background-color: #a9b7c6;
                color: #e1e1e1;
            }
            
            /* 标签样式 */
            QLabel {
                color: #a6accd;
                font-size: 14px;
            }
            
            QLabel#menuTitle {
                color: #c3cee3;
                font-size: 14px;
                font-weight: 600;
                margin-top: 10px;
                margin-bottom: 5px;
                padding-left: 5px;
            }
            
            QLabel#statusLabel {
                color: #676f8a;
                font-size: 13px;
                padding: 10px 0;
                margin: 10px 0;
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }
            
            /* 日志区域样式 */
            #logContainer {
                background-color: #292d3e;
                border-radius: 12px;
                margin: 10px 10px 10px 5px;
                border: 1px solid #3b4064;
            }
            
            /* 日志标题栏 */
            #logHeader {
                background-color: #2f3447;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                padding: 15px;
                border-bottom: 1px solid #3b4064;
            }
            
            #logTitle {
                color: #d5defa;
                font-size: 16px;
                font-weight: bold;
            }
            
            /* 日志标签标题 */
            #logTabTitle {
                color: #a6accd;
                font-size: 14px;
                font-weight: 600;
                padding: 5px 15px;
                background-color: #2f3447;
                border-top-right-radius: 8px;
                border-top-left-radius: 8px;
                border: 1px solid #3b4064;
                border-bottom: none;
            }
            
            QTextEdit {
                background-color: #202331;
                border: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                padding: 15px;
                color: #eeffff;
                font-family: 'Menlo', 'Monaco', monospace;
                font-size: 13px;
                selection-background-color: #717cb4;
                selection-color: white;
                line-height: 150%;
            }
            
            /* 滚动条样式 */
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                min-height: 30px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # 创建主窗口布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建侧边栏容器
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(250)
        sidebar.setMaximumWidth(300)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(15)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        
        # 应用标题
        app_title = QLabel("Fast Cursor 助手")
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        app_version = QLabel("v1.0.0")
        app_version.setObjectName("appVersion")
        app_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加功能按钮
        account_label = QLabel("账号管理")
        account_label.setObjectName("menuTitle")
        
        self.register_button = ModernButton("注册账号", "🚀")
        self.register_button.setObjectName("primaryButton")
        self.register_button.clicked.connect(self.on_register_clicked)
        
        self.reset_button = ModernButton("重置机器ID", "🔄")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.clicked.connect(self.on_reset_clicked)
        
        # 添加配置按钮
        settings_label = QLabel("系统设置")
        settings_label.setObjectName("menuTitle")
        
        self.config_button = ModernButton("配置设置", "⚙️")
        self.config_button.setObjectName("primaryButton")
        self.config_button.clicked.connect(self.on_config_clicked)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 添加组件到侧边栏
        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(app_version)
        sidebar_layout.addStretch(1)
        sidebar_layout.addWidget(account_label)
        sidebar_layout.addWidget(self.register_button)
        sidebar_layout.addWidget(self.reset_button)
        sidebar_layout.addStretch(1)
        sidebar_layout.addWidget(settings_label)
        sidebar_layout.addWidget(self.config_button)
        sidebar_layout.addStretch(2)
        sidebar_layout.addWidget(self.status_label)
        
        # 创建日志区域
        log_container = QFrame()
        log_container.setObjectName("logContainer")
        
        log_layout = QVBoxLayout(log_container)
        log_layout.setSpacing(0)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志标题栏
        log_header = QFrame()
        log_header.setObjectName("logHeader")
        log_header.setFixedHeight(50)
        
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(15, 0, 15, 0)
        
        log_title = QLabel("系统日志")
        log_title.setObjectName("logTitle")
        
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()
        
        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        # 添加组件到日志容器
        log_layout.addWidget(log_header)
        log_layout.addWidget(self.log_display)
        
        # 添加侧边栏和日志区域到主布局
        main_layout.addWidget(sidebar)
        main_layout.addWidget(log_container)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        
        self.setCentralWidget(central_widget)
    
    def setup_logger(self):
        # 设置日志处理器
        self.log_handler = QTextEditLogger(self.log_display)
        
        # 获取根日志记录器并添加处理器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 移除现有的处理器以避免重复输出
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        root_logger.addHandler(self.log_handler)
        
        # 初始日志消息
        logging.info("FastCursor 助手已启动")
        logging.info("界面已初始化完成，等待操作...")

    def on_register_clicked(self):
        self.toggle_buttons(False)
        self.status_label.setText("正在切换账号，请稍候...")
        
        # 使用线程执行函数，避免UI卡死
        threading.Thread(target=self.run_register_account, daemon=True).start()

    def run_register_account(self):
        try:
            logging.info("开始执行一键切换账号流程...")
            # 调用register_account函数，参数为(False, True)
            register_account(False, True)
            logging.info("一键切换账号完成")
        except Exception as e:
            logging.error(f"一键切换账号失败: {str(e)}")
        finally:
            # 使用信号更新UI，避免线程问题
            self.update_ui_signal.emit(True, "系统就绪，等待操作...")

    def on_reset_clicked(self):
        self.toggle_buttons(False)
        self.status_label.setText("正在重置机器ID，请稍候...")
        
        # 使用线程执行函数，避免UI卡死
        threading.Thread(target=self.run_reset_machine_id, daemon=True).start()

    def run_reset_machine_id(self):
        try:
            logging.info("开始执行重置机器ID流程...")
            # 调用reset_cursor_machine_id函数，参数为True
            reset_cursor_machine_id(True)
            logging.info("重置机器ID完成")
        except Exception as e:
            logging.error(f"重置机器ID失败: {str(e)}")
        finally:
            # 使用信号更新UI，避免线程问题
            self.update_ui_signal.emit(True, "系统就绪，等待操作...")

    def toggle_buttons(self, enabled):
        self.register_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        
    def update_ui_status(self, enabled, status_text):
        """安全地从任何线程更新UI状态"""
        self.toggle_buttons(enabled)
        self.status_label.setText(status_text)

    def on_config_clicked(self):
        """打开配置对话框"""
        dialog = ConfigDialog(self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.status_label.setText("配置已更新")
            logging.info("配置已成功保存")
        else:
            logging.info("配置未修改")

if __name__ == "__main__":
    try:
        # 初始化应用
        app = QApplication(sys.argv)
        
        # 设置应用字体 - 使用系统默认字体
        app_font = QFont()
        if sys.platform == "darwin":  # macOS
            app_font = QFont(".AppleSystemUIFont", 10)  # 使用macOS系统默认字体
        else:  # Windows/Linux
            app_font = QFont("Segoe UI", 10)
        app.setFont(app_font)
        
        # 创建主窗口
        window = FastCursorGUI()
        window.show()
        
        # 程序结束前清理日志处理器
        app.aboutToQuit.connect(QTextEditLogger.cleanup)
        
        # 运行应用
        sys.exit(app.exec())
    except Exception as e:
        # 如果启动过程中出现错误，显示一个最简单的错误窗口
        error_app = QApplication(sys.argv)
        error_window = QMainWindow()
        error_window.setWindowTitle("启动错误")
        error_window.setMinimumSize(500, 200)
        
        layout = QVBoxLayout()
        error_label = QLabel(f"应用启动失败: {e}")
        error_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(error_label)
        
        # 添加退出按钮
        exit_button = QPushButton("退出应用")
        exit_button.clicked.connect(error_app.quit)
        layout.addWidget(exit_button)
        
        container = QWidget()
        container.setLayout(layout)
        error_window.setCentralWidget(container)
        
        error_window.show()
        sys.exit(error_app.exec()) 