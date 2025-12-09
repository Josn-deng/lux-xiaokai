from PyQt5 import QtWidgets, QtCore, QtGui
import os
import sys


class SettingsBubble(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Settings")
        self.setGeometry(220, 220, 380, 300)
        # 移除无边框窗口标志，使用标准窗口样式
        window_flag = getattr(QtCore.Qt, 'Window')
        self.setWindowFlags(window_flag)
        # 关闭该窗口不退出主程序
        try:
            self.setAttribute(getattr(QtCore.Qt, 'WA_QuitOnClose'), False)
        except Exception:
            pass
        
        # 设置窗口图标
        try:
            # 使用正确的相对路径
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "settings.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
            else:
                # 调试信息
                print(f"设置图标未找到: {icon_path}")
        except Exception as e:
            print(f"设置图标时出错: {e}")
        
        self.setup_modern_ui()
        self._load_config_values()

    def setup_modern_ui(self):
        """设置现代化UI"""
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # 设置样式表
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 12px;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QComboBox, QCheckBox {
                border: 2px solid #95a5a6;
                border-radius: 8px;
                padding: 8px;
                background-color: white;
                font-size: 11px;
                selection-background-color: #95a5a6;
                selection-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #7f8c8d;
            }
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: 600;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7a7b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QFormLayout {
                border-spacing: 10px;
            }
            QFormLayout QLabel {
                font-weight: 600;
            }
        """)
        
        # 标题
        title_label = QtWidgets.QLabel("Application Settings")
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #7f8c8d;")
        
        # 表单布局
        form_layout = QtWidgets.QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)
        align_right = getattr(QtCore.Qt, 'AlignRight')
        form_layout.setLabelAlignment(align_right)
        
        self.ai_server_input = QtWidgets.QLineEdit()
        self.model_input = QtWidgets.QLineEdit()
        self.key_input = QtWidgets.QLineEdit()
        self.key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.language_select = QtWidgets.QComboBox()
        self.language_select.addItems(["zh (Chinese)", "en (English)", "vi (Vietnamese)"])
        self.auto_start_checkbox = QtWidgets.QCheckBox("Auto-start on boot")
        
        form_layout.addRow("AI Server:", self.ai_server_input)
        form_layout.addRow("Model:", self.model_input)
        form_layout.addRow("API Key:", self.key_input)
        form_layout.addRow("Target Language:", self.language_select)
        form_layout.addRow("", self.auto_start_checkbox)
        
        # 保存按钮
        self.save_button = QtWidgets.QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        pointing_hand_cursor = getattr(QtCore.Qt, 'PointingHandCursor')
        self.save_button.setCursor(pointing_hand_cursor)
        
        # 添加控件到布局
        main_layout.addWidget(title_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.save_button)
        main_layout.addStretch()
        
        self.setLayout(main_layout)

    def _load_config_values(self):
        self.ai_server_input.setText(self.config.ai_server)
        self.model_input.setText(self.config.model)
        self.key_input.setText(self.config.api_key)
        
        # 映射语言代码到显示文本
        lang_map = {
            "zh": "zh (Chinese)",
            "en": "en (English)", 
            "vi": "vi (Vietnamese)"
        }
        self.language_select.setCurrentText(lang_map.get(self.config.target_language, "en (English)"))
        self.auto_start_checkbox.setChecked(self.config.auto_start)

    def save_settings(self):
        # 保存设置
        self.config.ai_server = self.ai_server_input.text().strip() or self.config.ai_server
        self.config.model = self.model_input.text().strip() or self.config.model
        entered_key = self.key_input.text().strip()
        if entered_key:
            self.config.api_key = entered_key
            
        # 映射显示文本到语言代码
        lang_map = {
            "zh (Chinese)": "zh",
            "en (English)": "en", 
            "vi (Vietnamese)": "vi"
        }
        self.config.target_language = lang_map.get(self.language_select.currentText(), "en")
        self.config.auto_start = self.auto_start_checkbox.isChecked()
        self.config.save_config()
        QtWidgets.QMessageBox.information(self, "Settings Saved", "Configuration has been saved successfully.")
        # 只隐藏，不影响应用生命周期
        self.hide()

    def closeEvent(self, event):
        event.accept()

def main():
    from config.app_config import AppConfig
    cfg = AppConfig()
    app = QtWidgets.QApplication(sys.argv)
    settings_bubble = SettingsBubble(cfg)
    settings_bubble.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()