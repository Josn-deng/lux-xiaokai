from PyQt5 import QtWidgets, QtCore, QtGui
import os
import sys
from services.ai_client import AIClientError
from ui.bubbles.chat_history_area import ChatHistoryArea
from ui.theme_manager import theme_manager


class AITranslateBubble(QtWidgets.QWidget):
    def __init__(self, config, client):
        super().__init__()
        self.config = config
        self.client = client
        self.setWindowTitle("AI Translation")
        self.setGeometry(140, 140, 500, 600)
        # 关闭该窗口不退出主程序
        try:
            self.setAttribute(getattr(QtCore.Qt, 'WA_QuitOnClose'), False)
        except Exception:
            pass
        
        # 设置窗口图标
        try:
            # 使用正确的相对路径
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "ai_translate.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
            else:
                # 调试信息
                print(f"AI翻译图标未找到: {icon_path}")
        except Exception as e:
            print(f"设置AI翻译图标时出错: {e}")
        
        self.chat_history = []  # 存储对话历史
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
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #3498db;
                outline: none;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 18px;
                padding: 8px 15px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                border-radius: 18px;
            }"""
        )
        
        # 顶部工具栏
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setContentsMargins(15, 15, 15, 10)
        
        lang_label = QtWidgets.QLabel("Target Language:")
        self.lang_select = QtWidgets.QComboBox()
        self.lang_select.addItems(["zh (Chinese)", "en (English)", "vi (Vietnamese)"])
        self.lang_select.setCurrentText({
            "zh": "zh (Chinese)",
            "en": "en (English)", 
            "vi": "vi (Vietnamese)"
        }.get(self.config.target_language, "en (English)"))
        
        toolbar.addWidget(lang_label)
        toolbar.addWidget(self.lang_select)
        toolbar.addStretch()
        
        # 对话历史区域改为滚动区域 + 垂直布局
        self.history = ChatHistoryArea()
        
        # 输入区域
        input_layout = QtWidgets.QVBoxLayout()
        input_layout.setContentsMargins(15, 10, 15, 15)
        input_layout.setSpacing(10)
        
        self.input_text = QtWidgets.QTextEdit()
        self.input_text.setPlaceholderText("Enter text to translate...")
        self.input_text.setMaximumHeight(100)
        self.input_text.setFixedHeight(80)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.translate_button = QtWidgets.QPushButton("Translate")
        self.translate_button.clicked.connect(self.translate_text)
        pointing_hand_cursor = getattr(QtCore.Qt, 'PointingHandCursor')
        self.translate_button.setCursor(QtGui.QCursor(pointing_hand_cursor))
        button_layout.addStretch()
        button_layout.addWidget(self.translate_button)
        
        input_layout.addWidget(self.input_text)
        input_layout.addLayout(button_layout)
        
        # 添加控件到布局
        main_layout.addLayout(toolbar)
        main_layout.addWidget(self.history)
        main_layout.addLayout(input_layout)
        
        self.setLayout(main_layout)

    def add_message(self, role, content):
        styles = theme_manager.get_styles()
        msg = self.history.add_message(role, content, styles['message_user'], styles['message_ai'])
        return msg

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 滚动区域内部自适应宽度
        self.history._reflow_widths()

    def apply_theme_to_messages(self):
        self.history.apply_theme()

    def showEvent(self, event):
        super().showEvent(event)
        # 订阅主题变化
        try:
            theme_manager.theme_changed.disconnect(self._on_theme_changed)  # 防止重复连接
        except Exception:
            pass
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def closeEvent(self, event):
        event.accept()

    def _on_theme_changed(self, theme_name: str):
        self.apply_theme_to_messages()
        self.setStyleSheet(theme_manager.style_for('window_bg'))

    def translate_text(self):
        # 映射显示文本到语言代码
        lang_map = {
            "zh (Chinese)": "zh",
            "en (English)": "en", 
            "vi (Vietnamese)": "vi"
        }
        self.config.target_language = lang_map.get(self.lang_select.currentText(), "en")
        
        original = self.input_text.toPlainText().strip()
        if not original:
            QtWidgets.QMessageBox.warning(self, "Empty Input", "Please enter text to translate.")
            return
            
        # 添加用户消息到对话历史
        self.add_message("user", original)
        
        # 清空输入框
        self.input_text.clear()
        
        # 禁用按钮并显示正在处理状态
        self.translate_button.setEnabled(False)
        self.translate_button.setText("Translating...")
        QtWidgets.QApplication.processEvents()
        
        try:
            # 创建AI消息气泡但暂时不设置内容
            ai_message = self.add_message("ai", "")
            ai_message.start_streaming()
            
            # 构造请求参数
            payload = self.config.build_translation_prompt(original)
            
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
            self.translate_button.setEnabled(True)
            self.translate_button.setText("Translate")
            
        # 聚焦到输入框
        self.input_text.setFocus()
