from PyQt5 import QtWidgets, QtCore, QtGui
from typing import List
from ui.bubbles.message_widget import ChatMessageWidget
from ui.theme_manager import theme_manager


class ChatHistoryArea(QtWidgets.QScrollArea):
    """可变高度聊天历史区域，使用 QVBoxLayout 自动管理消息组件。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 简化配置，使用窗口宽度的80%作为气泡宽度
        self.bubble_width_ratio = 0.8
        self.min_width = 150  # 最小宽度
        
        self.setWidgetResizable(True)
        self._container = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout(self._container)
        self._layout.setContentsMargins(15, 8, 15, 8)
        self._layout.setSpacing(12)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(getattr(QtCore.Qt, 'ScrollBarAlwaysOff'))
        self.setVerticalScrollBarPolicy(getattr(QtCore.Qt, 'ScrollBarAsNeeded'))
        self.setWidget(self._container)
        self.setStyleSheet("QScrollArea{background:transparent; border:none;} QWidget{background:transparent;}")

    def _compute_bubble_width(self, view_w: int) -> int:
        """计算气泡宽度为窗口宽度的80%"""
        width = int(view_w * self.bubble_width_ratio)
        return max(self.min_width, width)


    def add_message(self, role: str, content: str, user_style: str, ai_style: str):
        vw = self.viewport()
        view_w = vw.width() if vw is not None else 500
        bubble_w = self._compute_bubble_width(view_w)
        
        msg = ChatMessageWidget(role, content, bubble_w, user_style, ai_style)
        
        # 根据角色设置对齐方式
        align = (getattr(QtCore.Qt, 'AlignRight') if role == 'user' 
                else getattr(QtCore.Qt, 'AlignLeft'))
        
        self._layout.addWidget(msg, alignment=align)
        self._scroll_to_bottom_later()
        return msg

    def _scroll_to_bottom_later(self):
        QtCore.QTimer.singleShot(50, self.scrollToBottom)

    def scrollToBottom(self):
        bar = self.verticalScrollBar()
        if bar:
            bar.setValue(bar.maximum())

    def _reflow_widths(self):
        """重新计算所有消息的宽度"""
        vw = self.viewport()
        view_w = vw.width() if vw is not None else 500
        
        bubble_w = self._compute_bubble_width(view_w)
        for msg in self.get_messages():
            msg.update_width(bubble_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 延迟重排以确保尺寸正确
        QtCore.QTimer.singleShot(100, self._reflow_widths)

    def set_width_mode(self, mode: str):
        self._reflow_widths()

    def get_messages(self) -> List[ChatMessageWidget]:
        result = []
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item and (widget := item.widget()):
                if isinstance(widget, ChatMessageWidget):
                    result.append(widget)
        return result

    def apply_theme(self):
        styles = theme_manager.get_styles()
        for w in self.get_messages():
            w.apply_theme(styles['message_user'], styles['message_ai'])
