from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import os

class SystemTray(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(SystemTray, self).__init__(icon, parent)
        self.setToolTip("桌面翻译软件")
        self.menu = QtWidgets.QMenu(parent)
        self.init_menu()
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_tray_icon_activated)

    def init_menu(self):
        self.menu.addAction("AI翻译", self.open_ai_translate)
        self.menu.addAction("文本润色", self.open_text_polish)
        self.menu.addAction("AI问答", self.open_ai_qa)
        self.menu.addAction("语音翻译", self.open_speech_translate)
        self.menu.addAction("设置", self.open_settings)
        self.menu.addSeparator()
        self.menu.addAction("退出", self.exit_application)

    def on_tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.menu.exec_(QtGui.QCursor.pos())

    def open_ai_translate(self):
        # 这里调用AI翻译功能
        pass

    def open_text_polish(self):
        # 这里调用文本润色功能
        pass

    def open_ai_qa(self):
        # 这里调用AI问答功能
        pass

    def open_speech_translate(self):
        # 这里调用语音翻译功能
        pass

    def open_settings(self):
        # 这里调用设置功能
        pass

    def exit_application(self):
        QtWidgets.qApp.quit()

def main():
    app = QtWidgets.QApplication(sys.argv)
    icon = QtGui.QIcon("path/to/icon.png")  # 替换为实际图标路径
    tray = SystemTray(icon)
    tray.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()