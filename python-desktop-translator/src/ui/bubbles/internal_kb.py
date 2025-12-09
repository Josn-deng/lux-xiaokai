from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView


class InternalKBWidget(QtWidgets.QWidget):
    """内部知识库页：紧凑头部 + WebEngine 内容视图。
    发出 back_requested 信号用于返回 QA 页。
    """
    back_requested = QtCore.pyqtSignal()

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._init_ui(url)

    def _init_ui(self, url: str):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 头部
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(8)
        header.setFixedHeight(40)

        title = QtWidgets.QLabel("LuxCase-ICT 知识库")
        title.setStyleSheet("QLabel {font-size: 14px; font-weight: 600; color: #d35400; padding: 0;}" )

        back_btn = QtWidgets.QPushButton("返回QA")
        back_btn.setCursor(QtGui.QCursor(getattr(QtCore.Qt, 'PointingHandCursor')))
        back_btn.clicked.connect(self.back_requested.emit)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)

        # 内容视图
        self.view = QWebEngineView()
        self.view.setUrl(QtCore.QUrl(url))

        layout.addWidget(header)
        layout.addWidget(self.view)
