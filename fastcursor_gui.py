import sys
import os
import time
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QTextEdit, QLabel, QFrame,
                            QGraphicsDropShadowEffect, QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QEvent
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap, QPalette, QLinearGradient, QGradient
import logging

# 导入需要的函数
from register_account import register_account
from change_account import reset_cursor_machine_id

# 设置日志处理器，将日志重定向到GUI
class QTextEditLogger(QObject, logging.Handler):
    log_signal = pyqtSignal(str)

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.log_signal.connect(self.append_log)

    def emit(self, record):
        log_message = self.format(record)
        self.log_signal.emit(log_message)

    def append_log(self, message):
        self.text_text = message.replace("INFO", "<span style='color:#4fc1e9;font-weight:bold;'>INFO</span>") \
                        .replace("ERROR", "<span style='color:#ed5565;font-weight:bold;'>ERROR</span>") \
                        .replace("WARNING", "<span style='color:#ffce54;font-weight:bold;'>WARNING</span>")
        
        self.text_edit.append(self.text_text)
        self.text_edit.verticalScrollBar().setValue(
            self.text_edit.verticalScrollBar().maximum()
        )

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

# 主窗口类
class FastCursorGUI(QMainWindow):
    # 定义信号用于线程间通信
    update_ui_signal = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_logger()
        self.setWindowTitle("Fast Cursor 助手")
        
        # 连接信号到槽函数
        self.update_ui_signal.connect(self.update_ui_status)

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
                font-family: 'Menlo', 'Consolas', monospace;
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

        # 创建主布局
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建侧边栏
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 25, 20, 20)
        sidebar_layout.setSpacing(15)
        
        # 侧边栏标题和版本号
        app_title = QLabel("Fast Cursor 助手")
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(app_title)
        
        app_version = QLabel("v1.0.0")
        app_version.setObjectName("appVersion")
        app_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(app_version)
        
        sidebar_layout.addSpacing(20)
        
        # 功能菜单标题
        menu_title = QLabel("功能菜单")
        menu_title.setObjectName("menuTitle")
        sidebar_layout.addWidget(menu_title)
        
        # 一键切换按钮 - 蓝色渐变
        self.register_btn = QPushButton("一键切换账号")
        self.register_btn.setObjectName("primaryButton")
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.setMinimumHeight(50)
        self.register_btn.clicked.connect(self.on_register_clicked)
        sidebar_layout.addWidget(self.register_btn)
        
        sidebar_layout.addSpacing(15)
        
        # 重置按钮 - 橙色渐变
        self.reset_btn = QPushButton("重置机器ID")
        self.reset_btn.setObjectName("secondaryButton")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setMinimumHeight(50)
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        sidebar_layout.addWidget(self.reset_btn)
        
        # 添加弹性空间
        sidebar_layout.addStretch(1)
        
        # 状态信息
        self.status_label = QLabel("系统就绪，等待操作...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.status_label)
        
        # 为侧边栏添加阴影效果
        sidebar_shadow = QGraphicsDropShadowEffect()
        sidebar_shadow.setBlurRadius(20)
        sidebar_shadow.setColor(QColor(0, 0, 0, 70))
        sidebar_shadow.setOffset(0, 0)
        sidebar.setGraphicsEffect(sidebar_shadow)
        
        # 创建日志区域容器
        log_container_wrapper = QWidget()
        log_container_wrapper_layout = QVBoxLayout(log_container_wrapper)
        log_container_wrapper_layout.setContentsMargins(0, 5, 0, 0)
        log_container_wrapper_layout.setSpacing(0)
        
        # 日志标签标题
        log_tab = QLabel("操作日志")
        log_tab.setObjectName("logTabTitle")
        log_tab.setFixedWidth(100)
        log_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        log_tab_container = QWidget()
        log_tab_layout = QHBoxLayout(log_tab_container)
        log_tab_layout.setContentsMargins(20, 0, 0, 0)
        log_tab_layout.setSpacing(0)
        log_tab_layout.addWidget(log_tab)
        log_tab_layout.addStretch()
        
        log_container_wrapper_layout.addWidget(log_tab_container)
        
        # 创建主内容区（日志区域）
        log_container = QWidget()
        log_container.setObjectName("logContainer")
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(0)
        
        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.log_text.setAcceptRichText(True)
        log_layout.addWidget(self.log_text)
        
        log_container_wrapper_layout.addWidget(log_container)
        
        # 为日志容器添加阴影
        log_shadow = QGraphicsDropShadowEffect()
        log_shadow.setBlurRadius(20)
        log_shadow.setColor(QColor(0, 0, 0, 70))
        log_shadow.setOffset(0, 0)
        log_container.setGraphicsEffect(log_shadow)
        
        # 添加侧边栏和主内容区到主布局
        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(log_container_wrapper, 3)  # 日志区占更多空间
        
        self.setCentralWidget(central_widget)

    def setup_logger(self):
        # 设置日志处理器
        self.log_handler = QTextEditLogger(self.log_text)
        
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
        self.register_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        
    def update_ui_status(self, enabled, status_text):
        """安全地从任何线程更新UI状态"""
        self.toggle_buttons(enabled)
        self.status_label.setText(status_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用字体 - 简化以避免兼容性问题
    app_font = QFont()
    if sys.platform == "darwin":  # macOS
        app_font = QFont("SF Pro", 10)
    else:  # Windows/Linux
        app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)
    
    window = FastCursorGUI()
    window.show()
    sys.exit(app.exec()) 