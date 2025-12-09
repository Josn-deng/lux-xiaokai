from PyQt5 import QtWidgets, QtCore

class WindowManager:
    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.floating_window = None
        self.tray_icon = None

    def create_floating_window(self):
        self.floating_window = QtWidgets.QWidget()
        self.floating_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.floating_window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.floating_window.setGeometry(100, 100, 300, 200)  # Example geometry
        self.floating_window.setStyleSheet("background-color: rgba(255, 255, 255, 200);")

    def create_tray_icon(self):
        self.tray_icon = QtWidgets.QSystemTrayIcon()
        self.tray_icon.setIcon(QtWidgets.QIcon("path/to/icon.png"))  # Replace with actual icon path
        self.tray_icon.setVisible(True)

    def show(self):
        self.create_floating_window()
        self.create_tray_icon()
        self.floating_window.show()
        self.app.exec_()

if __name__ == "__main__":
    window_manager = WindowManager()
    window_manager.show()