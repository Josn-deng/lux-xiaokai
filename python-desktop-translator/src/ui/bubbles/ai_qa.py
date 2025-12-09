from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox, QAbstractItemView, QStackedWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore, QtGui, QtWidgets
import os
import sys
from services.ai_client import AIClientError
from ui.theme_manager import theme_manager
from ui.bubbles.chat_history_area import ChatHistoryArea
from ui.bubbles.internal_kb import InternalKBWidget
import importlib.util
import pathlib


class AIQAWidget(QWidget):
    def __init__(self, config, client):
        super().__init__()
        self.config = config
        self.client = client
        self.setWindowTitle("AI Q&A")
        self.setGeometry(180, 180, 500, 600)
        # 关闭该窗口不退出主程序（与托盘常驻一致）
        try:
            self.setAttribute(getattr(QtCore.Qt, 'WA_QuitOnClose'), False)
        except Exception:
            pass
        
        # 设置窗口图标
        try:
            # 使用正确的相对路径
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "ai_qa.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
            else:
                # 调试信息
                print(f"AI问答图标未找到: {icon_path}")
        except Exception as e:
            print(f"设置AI问答图标时出错: {e}")
        
        self.setup_chat_ui()

    def setup_chat_ui(self):
        """设置聊天界面UI"""
        # 主布局 + 分页容器
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.stacked = QStackedWidget()
        
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
                selection-background-color: #e67e22;
                selection-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #e67e22;
                outline: none;
            }
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #a04000;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }"""
        )
        
        # 标题
        title_label = QLabel("AI Question & Answer")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px; 
                font-weight: 600; 
                color: #d35400;
                padding: 15px;
                border-bottom: 1px solid #eee;
            }
        """)
        
        # ------- Page 0: QA 聊天页 -------
        qa_page = QWidget()
        qa_layout = QVBoxLayout(qa_page)
        qa_layout.setContentsMargins(0, 0, 0, 0)
        qa_layout.setSpacing(0)

        self.history = ChatHistoryArea()

        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(15, 10, 15, 15)
        input_layout.setSpacing(10)

        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("Ask a question...")
        self.question_input.setMaximumHeight(100)
        self.question_input.setFixedHeight(80)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        self.ask_button = QPushButton("Ask AI")
        self.ask_button.clicked.connect(self._ask)
        pointing_hand_cursor = getattr(QtCore.Qt, 'PointingHandCursor')
        self.ask_button.setCursor(QtGui.QCursor(pointing_hand_cursor))

        self.kb_button = QPushButton("内部知识库")
        self.kb_button.setCursor(QtGui.QCursor(pointing_hand_cursor))
        self.kb_button.clicked.connect(self._open_internal_kb)
        button_layout.addStretch()
        button_layout.addWidget(self.kb_button)
        button_layout.addWidget(self.ask_button)

        input_layout.addWidget(self.question_input)
        input_layout.addLayout(button_layout)

        qa_layout.addWidget(title_label)
        qa_layout.addWidget(self.history)
        qa_layout.addLayout(input_layout)

        # ------- Page 1: 内部知识库页 -------
        # 使用独立组件 InternalKBWidget
        kb_widget = InternalKBWidget(url="https://chatai.luxcaseict.com/chat/1cedc8977503e931")
        kb_widget.back_requested.connect(lambda: self._flip_to(0))

        # 堆叠页组装
        self.stacked.addWidget(qa_page)
        self.stacked.addWidget(kb_widget)
        self.stacked.setCurrentIndex(0)
        main_layout.addWidget(self.stacked)
        self.setLayout(main_layout)

    def _ask(self):
        question = self.question_input.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "Empty Question", "Please enter a question.")
            return
        
        # 添加用户消息到对话历史
        self.add_message("user", question)
        
        # 清空输入框
        self.question_input.clear()
        
        # 禁用按钮并显示正在处理状态
        self.ask_button.setEnabled(False)
        self.ask_button.setText("Asking...")
        QtWidgets.QApplication.processEvents()
        
        try:
            # 创建AI消息气泡但暂时不设置内容
            ai_message = self.add_message("ai", "")
            ai_message.start_streaming()
            
            # 构造请求参数
            payload = self.config.build_qa_prompt(question)
            
            # 流式获取AI响应
            for chunk in self.client.chat_stream(payload):
                ai_message.stream_text(chunk)
                QtWidgets.QApplication.processEvents()  # 保持UI响应
            
            # 结束流式输出
            ai_message.end_streaming()
            # 通知全局 AI 完成事件（用于更新悬浮窗图标等）
            try:
                theme_manager.ai_response_complete.emit()
            except Exception:
                pass
        except AIClientError as e:
            # 添加错误消息到对话历史
            self.add_message("ai", f"Error: {str(e)}")
        finally:
            self.ask_button.setEnabled(True)
            self.ask_button.setText("Ask AI")
            
        # 聚焦到输入框
        self.question_input.setFocus()

    def _open_internal_kb(self):
        """切换到内部知识库页面，并执行翻页动画。"""
        try:
            print("[AIQA] 内部知识库按钮点击，准备切换到页1")
        except Exception:
            pass
        # 先直接切到目标页，避免动画失败导致无反应
        try:
            self.stacked.setCurrentIndex(1)
        except Exception:
            pass
        # 再执行动画，使体验更平滑
        self._flip_to(1)

    def _flip_to(self, index: int):
        """3D 翻卡片切页：500ms，中点略缩放产生透视（使用页面快照避免嵌入错误）。"""
        current = self.stacked.currentWidget()
        nextw = self.stacked.widget(index)
        if current is None or nextw is None or current is nextw:
            return
        try:
            print(f"[AIQA] 卡片翻转：{self.stacked.currentIndex()} -> {index}")
        except Exception:
            pass

        # 容器与场景/视图
        container = self.stacked
        rect = container.rect()
        scene = QGraphicsScene(container)
        view = QGraphicsView(scene, container)
        view.setFrameShape(QtWidgets.QFrame.NoFrame)
        view.setHorizontalScrollBarPolicy(getattr(QtCore.Qt, 'ScrollBarAlwaysOff'))
        view.setVerticalScrollBarPolicy(getattr(QtCore.Qt, 'ScrollBarAlwaysOff'))
        view.setStyleSheet("background: transparent;")
        view.setAttribute(getattr(QtCore.Qt, 'WA_TransparentForMouseEvents'), True)
        view.setGeometry(rect)
        view.raise_()
        view.show()

        # 页面截图（必须在当前可见状态下抓取）
        cur_pix = current.grab()
        # 切到目标页以便抓取其截图（暂时切过去，稍后动画开始再切回）
        prev_index = self.stacked.currentIndex()
        self.stacked.setCurrentWidget(nextw)
        next_pix = nextw.grab()
        # 还原显示当前页
        self.stacked.setCurrentIndex(prev_index)

        # 建立图元
        cur_item = QGraphicsPixmapItem(cur_pix)
        next_item = QGraphicsPixmapItem(next_pix)
        scene.addItem(cur_item)
        scene.addItem(next_item)
        next_item.setOpacity(0.0)
        # 设置变换中心为中点
        cur_item.setTransformOriginPoint(cur_item.boundingRect().center())
        next_item.setTransformOriginPoint(next_item.boundingRect().center())
        # 居中放置
        scene.setSceneRect(0, 0, rect.width(), rect.height())
        cur_item.setPos((rect.width() - cur_item.boundingRect().width()) / 2,
                        (rect.height() - cur_item.boundingRect().height()) / 2)
        next_item.setPos((rect.width() - next_item.boundingRect().width()) / 2,
                         (rect.height() - next_item.boundingRect().height()) / 2)

        # 定时驱动动画
        steps = 50
        duration = 500
        interval = int(duration / steps)
        counter = {"i": 0}

        def step_fn():
            i = counter["i"]
            t = i / steps
            if t <= 0.5:
                p = t / 0.5
                angle = 0 + p * 90
                scale = 1.0 - 0.06 * p
                cur_item.setOpacity(1.0 - p)
                cur_item.setRotation(angle)
                cur_item.setScale(scale)
            else:
                # 在中点后确保真正切换到下一页组件
                if self.stacked.currentWidget() is not nextw:
                    self.stacked.setCurrentWidget(nextw)
                p = (t - 0.5) / 0.5
                angle = 270 + p * 90
                scale = 0.94 + 0.06 * p
                next_item.setOpacity(p)
                next_item.setRotation(angle)
                next_item.setScale(scale)
            counter["i"] = i + 1
            if counter["i"] > steps:
                timer.stop()
                # 清理临时视图
                scene.removeItem(cur_item)
                scene.removeItem(next_item)
                view.hide()
                view.deleteLater()

        timer = QtCore.QTimer(self)
        timer.timeout.connect(step_fn)
        timer.start(interval)
