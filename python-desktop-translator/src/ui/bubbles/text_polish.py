from PyQt5 import QtWidgets, QtCore, QtGui
import os
import sys
from services.ai_client import AIClientError
from ui.theme_manager import theme_manager
from ui.bubbles.chat_history_area import ChatHistoryArea


class TextPolishBubble(QtWidgets.QWidget):
    def __init__(self, config, client):
        super().__init__()
        self.config = config
        self.client = client
        self.setWindowTitle("Text Polishing")
        self.setGeometry(160, 160, 500, 600)
        # 关闭该窗口不退出主程序
        try:
            self.setAttribute(getattr(QtCore.Qt, 'WA_QuitOnClose'), False)
        except Exception:
            pass
        
        # 设置窗口图标
        try:
            # 使用正确的相对路径
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "text_polish.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
            else:
                # 调试信息
                print(f"文本润色图标未找到: {icon_path}")
        except Exception as e:
            print(f"设置文本润色图标时出错: {e}")
        
        self.setup_chat_ui()

    def setup_chat_ui(self):
        """设置聊天界面UI"""
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 设置样式表
        self.setStyleSheet(
            """QWidget {
                background-color: #ffffff;
                font-family: \"Segoe UI\", Arial, sans-serif;
            }
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QListWidget {
                background-color: #f5f5f5;
                border: none;
                selection-background-color: transparent;
                selection-color: black;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 18px;
                padding: 10px 15px;
                background-color: white;
                font-size: 13px;
                selection-background-color: #9b59b6;
                selection-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #9b59b6;
                outline: none;
            }
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }"""
        )
        
        # 标题
        title_label = QtWidgets.QLabel("Text Polishing")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: 600; 
                color: #8e44ad;
                padding: 15px;
                border-bottom: 1px solid #eee;
            }
        """)
        
        # 对话历史区域改为滚动区域
        self.history = ChatHistoryArea()
        
        # 输入区域
        input_layout = QtWidgets.QVBoxLayout()
        input_layout.setContentsMargins(15, 10, 15, 15)
        input_layout.setSpacing(10)
        
        self.input_text = QtWidgets.QTextEdit()
        self.input_text.setPlaceholderText("Enter text to polish...")
        self.input_text.setMaximumHeight(100)
        self.input_text.setFixedHeight(80)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.polish_button = QtWidgets.QPushButton("Polish Text")
        self.polish_button.clicked.connect(self._do_polish)
        pointing_hand_cursor = getattr(QtCore.Qt, 'PointingHandCursor')
        self.polish_button.setCursor(QtGui.QCursor(pointing_hand_cursor))
        button_layout.addStretch()
        button_layout.addWidget(self.polish_button)
        
        input_layout.addWidget(self.input_text)
        input_layout.addLayout(button_layout)
        
        # 添加控件到布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.history)
        main_layout.addLayout(input_layout)
        
        self.setLayout(main_layout)

    def add_message(self, role, content):
        styles = theme_manager.get_styles()
        return self.history.add_message(role, content, styles['message_user'], styles['message_ai'])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reflow message widths after window resize
        self.history._reflow_widths()

    def apply_theme_to_messages(self):
        self.history.apply_theme()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            theme_manager.theme_changed.disconnect(self._on_theme_changed)
        except Exception:
            pass
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def closeEvent(self, event):
        event.accept()

    def _on_theme_changed(self, theme_name: str):
        # Apply theme changes to existing messages and window background
        self.apply_theme_to_messages()
        self.setStyleSheet(theme_manager.style_for('window_bg'))

    def _do_polish(self):
        original = self.input_text.toPlainText().strip()
        if not original:
            QtWidgets.QMessageBox.warning(self, "Empty Input", "Please enter text to polish.")
            return
            
        # 添加用户消息到对话历史
        self.add_message("user", original)
        
        # 清空输入框
        self.input_text.clear()
        
        # 禁用按钮并显示正在处理状态
        self.polish_button.setEnabled(False)
        self.polish_button.setText("Polishing...")
        QtWidgets.QApplication.processEvents()
        
        try:
            # 创建AI消息气泡但暂时不设置内容
            ai_message = self.add_message("ai", "")
            ai_message.start_streaming()
            
            # 构造请求参数
            payload = self.config.build_polish_prompt(original)
            
            # 流式获取AI响应
            for chunk in self.client.chat_stream(payload):
                ai_message.stream_text(chunk)
                QtWidgets.QApplication.processEvents()  # 保持UI响应
            
            # 结束流式输出
            ai_message.end_streaming()
        except AIClientError as e:
            # 添加错误消息到对话历史
            self.add_message("ai", f"Error: {str(e)}")
        finally:
            self.polish_button.setEnabled(True)
            self.polish_button.setText("Polish Text")
            
        # 聚焦到输入框
        self.input_text.setFocus()
