import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon

class SimpleChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("立铠智能助手--内部知识库")
        self.setGeometry(100, 100, 500, 600)
        self.setWindowIcon(QIcon.fromTheme("applications-internet"))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建 WebView
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://chatai.luxcaseict.com/chat/1cedc8977503e931"))
        
        # 添加到布局
        layout.addWidget(self.web_view)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
        """)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AI 聊天助手")
    
    window = SimpleChatWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()