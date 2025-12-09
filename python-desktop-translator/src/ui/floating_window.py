from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtSvg import QSvgRenderer
import sys
import math
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ai_client import AIClient, AIClientError
from ui.bubbles.ai_translate import AITranslateBubble
from ui.bubbles.text_polish import TextPolishBubble
from ui.bubbles.ai_qa import AIQAWidget
from ui.bubbles.speech_translate import SpeechTranslateBubble
from ui.bubbles.settings import SettingsBubble
from core.hotkeys import HotkeyManager
from ui.theme_manager import theme_manager


class FloatingWindow(QtWidgets.QWidget):
    def __init__(self, config, client: AIClient, translation_service):
        super().__init__()
        self.config = config
        self.client = client
        self.translation_service = translation_service
        
        # 设置窗口属性
        stay_on_top_flag = getattr(QtCore.Qt, 'WindowStaysOnTopHint')
        frameless_flag = getattr(QtCore.Qt, 'FramelessWindowHint')
        tool_flag = getattr(QtCore.Qt, 'Tool')
        # 使用 Qt.Tool 让悬浮窗不出现在任务栏
        self.setWindowFlags(stay_on_top_flag | frameless_flag | tool_flag)
        translucent_flag = getattr(QtCore.Qt, 'WA_TranslucentBackground')
        self.setAttribute(translucent_flag)
        
        # 设置窗口大小和位置
        self.resize(80, 80)
        self.setWindowTitle("小铠同学")
        
        # 子气泡实例（懒加载）
        self._translate_bubble = None
        self._polish_bubble = None
        self._qa_bubble = None
        self._speech_bubble = None
        self._settings_bubble = None
        
        # 子气泡窗口列表
        self.bubble_windows = []
        
        # 鼠标跟踪
        self.setMouseTracking(True)
        self.is_hovered = False

        # --- 中心图标（根据状态变化） ---
        icons_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'icons'))
        self.icon_paths = {
            'idle': os.path.join(icons_dir, 'Wait.png'),
            'active': os.path.join(icons_dir, 'Conduct.png'),
            'complete': os.path.join(icons_dir, 'Complete.png')
        }
        self.icon_pixmaps = {}
        for k, p in self.icon_paths.items():
            try:
                if os.path.exists(p):
                    self.icon_pixmaps[k] = QtGui.QPixmap(p)
                else:
                    self.icon_pixmaps[k] = None
            except Exception:
                self.icon_pixmaps[k] = None

        # 状态： 'active' | 'idle' | 'complete'
        self._status = 'active'

        # 空闲检测：30s 没有触碰悬浮窗后进入 idle
        self._idle_timer = QtCore.QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(30000)  # 30秒
        self._idle_timer.timeout.connect(lambda: self._set_status('idle'))
        # 启动初始倒计时
        self._start_idle_timer()
        
        # 定时器用于延迟隐藏气泡
        self.hide_timer = QtCore.QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_bubbles)
        
        # 波纹动画相关
        self.ripple_radius = 0
        # 使用普通动画替代属性动画
        self.ripple_animation = QtCore.QVariantAnimation(self)
        self.ripple_animation.setDuration(1000)
        self.ripple_animation.setStartValue(0)
        self.ripple_animation.setEndValue(40)
        self.ripple_animation.valueChanged.connect(self._on_ripple_value_changed)
        self.ripple_animation.finished.connect(self.reset_ripple)
        
        # 气泡动画相关
        self.bubble_animations = []
        
        # 拖动状态
        self.is_dragging = False

        # 热键管理：注册切换主题快捷键 Ctrl+Alt+T
        self.hotkeys = HotkeyManager()
        self.hotkeys.register_hotkey('ctrl+alt+t', self._toggle_theme_hotkey)

        # 订阅全局 AI 完成信号以切换为 complete 图标
        try:
            theme_manager.ai_response_complete.connect(lambda: self._set_status('complete'))
        except Exception:
            pass

        # --- 系统托盘图标（出现在任务栏右侧系统托盘） ---
        try:
            tray_icon = None
            # 优先使用加载的 active pixmap
            pix = self.icon_pixmaps.get('active')
            if pix and not pix.isNull():
                tray_icon = QtGui.QIcon(pix)
            else:
                # fallback to path
                active_path = self.icon_paths.get('active')
                if active_path and os.path.exists(active_path):
                    tray_icon = QtGui.QIcon(active_path)
            if tray_icon is None:
                tray_icon = QtGui.QIcon()

            self.tray = QtWidgets.QSystemTrayIcon(tray_icon, self)
            self.tray.setToolTip('AI助手')

            # 构建菜单
            tray_menu = QtWidgets.QMenu()
            action_settings = tray_menu.addAction('设置')
            action_exit = tray_menu.addAction('退出')
            action_settings.triggered.connect(self.open_settings) # type: ignore
            # 修复：避免 Pylance 报告 OptionalMemberAccess 错误
            app_instance = QtWidgets.QApplication.instance()
            if app_instance is not None:
                action_exit.triggered.connect(app_instance.quit)# type: ignore
            else:
                action_exit.triggered.connect(QtWidgets.QApplication.quit)# type: ignore
            self.tray.setContextMenu(tray_menu)

            # 双击托盘图标切换悬浮窗显示
            def _on_tray_activated(reason):
                # 2 is double click in some bindings, use enum
                try:
                    act = QtWidgets.QSystemTrayIcon.ActivationReason
                    if reason == act.DoubleClick:
                        if self.isVisible():
                            self.hide()
                        else:
                            self.show()
                            self.raise_()
                            self.activateWindow()
                except Exception:
                    pass
            self.tray.activated.connect(_on_tray_activated)
            self.tray.show()
        except Exception:
            self.tray = None

    def _toggle_theme_hotkey(self):
        theme_manager.toggle_theme()

    def _on_ripple_value_changed(self, value):
        """波纹动画值变化时的处理"""
        self.ripple_radius = value
        self.update()

    def paintEvent(self, event):
        """绘制圆形悬浮窗"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 仅在鼠标悬停时绘制背景与波纹
        if self.is_hovered:
            # 绘制波纹效果
            if self.ripple_radius > 0:
                ripple_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 100), 2)
                painter.setPen(ripple_pen)
                painter.drawEllipse(
                    int(self.width() / 2 - self.ripple_radius),
                    int(self.height() / 2 - self.ripple_radius),
                    int(self.ripple_radius * 2),
                    int(self.ripple_radius * 2)
                )
            # 背景色作为整体
            painter.setBrush(QtGui.QBrush(QtGui.QColor(70, 130, 180, 120)))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 100), 2))
            painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        
        # 绘制中心图标（根据状态显示对应 PNG）
        icon = self.icon_pixmaps.get(self._status)
        if icon and not icon.isNull():
            # 缩放图标以适配更大的内圈（减小边距以放大图标）
            inner_rect = QtCore.QRect(10, 10, self.width() - 20, self.height() - 20)
            icon_size = min(inner_rect.width(), inner_rect.height())
            keep_aspect = getattr(QtCore.Qt, 'KeepAspectRatio')
            smooth = getattr(QtCore.Qt, 'SmoothTransformation')
            scaled = icon.scaled(icon_size, icon_size, keep_aspect, smooth)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            # 回退到文字显示
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
            painter.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
            align_center = getattr(QtCore.Qt, 'AlignCenter')
            painter.drawText(self.rect(), align_center, "小铠")

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        left_button = getattr(QtCore.Qt, 'LeftButton')
        if event.button() == left_button:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            self.is_dragging = True
            # 开始拖动时隐藏气泡
            if self.bubble_windows:
                self.retract_bubbles()
        # 视为用户活动，切换到 active 并重启空闲计时器
        self._on_user_activity()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        left_button = getattr(QtCore.Qt, 'LeftButton')
        if event.buttons() == left_button and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
        # 重置隐藏定时器
        self.hide_timer.stop()
        # 用户活动
        self._on_user_activity()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        left_button = getattr(QtCore.Qt, 'LeftButton')
        if event.button() == left_button:
            self.is_dragging = False
            # 拖动结束后不立即显示气泡
        # 用户活动
        self._on_user_activity()

    def enterEvent(self, event):
        """鼠标进入窗口事件"""
        self.is_hovered = True
        # 只有在非拖动状态下才显示气泡
        if not self.is_dragging:
            self.show_bubbles()
        self.hide_timer.stop()
        
        # 启动波纹动画
        self.ripple_animation.stop()
        self.ripple_radius = 0
        self.ripple_animation.start()
        # 用户活动
        self._on_user_activity()

    def leaveEvent(self, event):
        """鼠标离开窗口事件"""
        self.is_hovered = False
        # 设置延迟隐藏
        self.hide_timer.start(1000)  # 1秒后隐藏
        # 离开窗口不视为活动，空闲计时继续运行，若达到30s会进入 idle

    def reset_ripple(self):
        """重置波纹效果"""
        self.ripple_radius = 0
        self.update()

    def show_bubbles(self):
        """显示子气泡窗口"""
        self.hide_bubbles()  # 先隐藏现有的气泡
        
        # 气泡名称和对应的创建函数
        bubble_configs = [
            ("AI翻译", self.open_ai_translate),
            ("文本润色", self.open_text_polish),
            ("AI问答", self.open_ai_qa),
            ("语音翻译", self.open_speech_translate),
            ("设置", self.open_settings),
        ]
        
        # 计算气泡位置（围绕圆形主窗口）
        center_x = self.x() + self.width() // 2
        center_y = self.y() + self.height() // 2
        radius = 65  # 气泡距离中心的距离
        bubble_size = 40  # 气泡大小
        
        # 清空旧的动画
        self.bubble_animations.clear()
        
        for i, (name, create_func) in enumerate(bubble_configs):
            # 计算气泡最终位置（顺时针排列）
            angle = (i * (360 / len(bubble_configs)) - 90) * 3.14159 / 180  # 从顶部开始，顺时针
            bubble_x = int(center_x + radius * math.cos(angle) - bubble_size // 2)
            bubble_y = int(center_y + radius * math.sin(angle) - bubble_size // 2)
            
            # 创建临时按钮样式的气泡（初始位置在中心）
            center_bubble_x = int(center_x - bubble_size // 2)
            center_bubble_y = int(center_y - bubble_size // 2)
            
            bubble = BubbleWidget(name, center_bubble_x, center_bubble_y, bubble_size, create_func)
            bubble.show()
            self.bubble_windows.append(bubble)
            
            # 创建动画
            animation = QtCore.QPropertyAnimation(bubble, b"geometry")
            animation.setDuration(500)
            animation.setStartValue(QtCore.QRect(center_bubble_x, center_bubble_y, bubble_size, bubble_size))
            animation.setEndValue(QtCore.QRect(bubble_x, bubble_y, bubble_size, bubble_size))
            animation.setEasingCurve(QtCore.QEasingCurve.OutBack)
            
            # 添加延迟，实现顺时针依次出现的效果
            QtCore.QTimer.singleShot(i * 100, animation.start)
            self.bubble_animations.append(animation)

    def retract_bubbles(self):
        """缩回子气泡到中心并添加渐隐效果"""
        # 创建一个定时器来更新气泡位置到悬浮窗实时中心位置
        self.retract_timer = QtCore.QTimer(self)
        self.retract_timer.timeout.connect(self._update_bubble_target_positions)
        self.retract_timer.start(10)  # 每10毫秒更新一次位置
        
        # 设置动画结束后停止定时器
        QtCore.QTimer.singleShot(150, self._stop_retract_timer)
        
        # 计算当前窗口实时中心位置
        center_x = self.x() + self.width() // 2
        center_y = self.y() + self.height() // 2
        bubble_size = 60
        
        center_bubble_x = int(center_x - bubble_size // 2)
        center_bubble_y = int(center_y - bubble_size // 2)
        
        # 清空旧的动画
        self.bubble_animations.clear()
        
        # 为每个气泡创建返回中心的动画（更快的速度）
        for i, bubble in enumerate(self.bubble_windows):
            # 位置动画
            pos_animation = QtCore.QPropertyAnimation(bubble, b"geometry")
            pos_animation.setDuration(150)  # 更快的动画速度（原来是300ms，现在是150ms）
            pos_animation.setStartValue(bubble.geometry())
            pos_animation.setEndValue(QtCore.QRect(center_bubble_x, center_bubble_y, bubble_size, bubble_size))
            pos_animation.setEasingCurve(QtCore.QEasingCurve.InBack)
            
            # 渐隐动画
            opacity_effect = QtWidgets.QGraphicsOpacityEffect(bubble)
            bubble.setGraphicsEffect(opacity_effect)
            opacity_animation = QtCore.QPropertyAnimation(opacity_effect, b"opacity")
            opacity_animation.setDuration(150)
            opacity_animation.setStartValue(1.0)
            opacity_animation.setEndValue(0.0)
            opacity_animation.setEasingCurve(QtCore.QEasingCurve.InQuad)
            
            # 添加延迟，实现顺时针依次收回的效果（更短的延迟）
            QtCore.QTimer.singleShot(i * 25, pos_animation.start)
            QtCore.QTimer.singleShot(i * 25, opacity_animation.start)
            
            self.bubble_animations.append(pos_animation)
            self.bubble_animations.append(opacity_animation)

    def _update_bubble_target_positions(self):
        """更新气泡目标位置到悬浮窗实时中心位置"""
        # 计算当前窗口实时中心位置
        center_x = self.x() + self.width() // 2
        center_y = self.y() + self.height() // 2
        bubble_size = 60
        
        center_bubble_x = int(center_x - bubble_size // 2)
        center_bubble_y = int(center_y - bubble_size // 2)
        
        # 更新所有正在进行的位置动画的目标位置
        running_state = getattr(QtCore.QAbstractAnimation, 'Running')
        for animation in self.bubble_animations:
            # 只更新位置动画的目标位置，不更新透明度动画
            if (animation.state() == running_state and 
                animation.propertyName() == b"geometry"):
                animation.setEndValue(QtCore.QRect(center_bubble_x, center_bubble_y, bubble_size, bubble_size))

    def _stop_retract_timer(self):
        """停止位置更新定时器"""
        if hasattr(self, 'retract_timer'):
            self.retract_timer.stop()
            
        # 动画结束后隐藏气泡
        QtCore.QTimer.singleShot(150 + (len(self.bubble_windows) - 1) * 25, self.hide_bubbles)

    def hide_bubbles(self):
        """隐藏所有气泡窗口"""
        for bubble in self.bubble_windows:
            bubble.close()
        self.bubble_windows.clear()
        self.bubble_animations.clear()

    # ---------------- 状态与空闲检测 ----------------
    def _start_idle_timer(self):
        try:
            self._idle_timer.start()
        except Exception:
            pass

    def _on_user_activity(self):
        """用户发生交互时调用：将状态设为 active 并重启空闲计时器"""
        # 若之前处于 complete 状态，不自动切回 active，除非显式调用
        if self._status != 'complete':
            self._set_status('active')
        # 重启定时器
        try:
            self._idle_timer.stop()
            self._idle_timer.start()
        except Exception:
            pass

    def _set_status(self, status: str):
        """设置当前状态并触发重绘。status in {'active','idle','complete'}"""
        if status not in ('active', 'idle', 'complete'):
            return
        if self._status == status:
            return
        self._status = status
        # 如果是 complete 状态，确保动画停止
        if status == 'complete':
            try:
                self.ripple_animation.stop()
            except Exception:
                pass
        # 触发重绘
        self.update()

    # --------- 打开各气泡窗口 ---------
    def open_ai_translate(self):
        self.hide_bubbles()
        if self._translate_bubble is None:
            self._translate_bubble = AITranslateBubble(self.config, self.client)
        self._translate_bubble.show()

    def open_text_polish(self):
        self.hide_bubbles()
        if self._polish_bubble is None:
            self._polish_bubble = TextPolishBubble(self.config, self.client)
        self._polish_bubble.show()

    def open_ai_qa(self):
        self.hide_bubbles()
        if self._qa_bubble is None:
            self._qa_bubble = AIQAWidget(self.config, self.client)
        self._qa_bubble.show()

    def open_speech_translate(self):
        self.hide_bubbles()
        if self._speech_bubble is None:
            self._speech_bubble = SpeechTranslateBubble(self.config, self.client)
        self._speech_bubble.show()

    def open_settings(self):
        self.hide_bubbles()
        if self._settings_bubble is None:
            self._settings_bubble = SettingsBubble(self.config)
        self._settings_bubble.show()


class BubbleWidget(QtWidgets.QWidget):
    """气泡部件"""
    def __init__(self, text, x, y, size, callback):
        super().__init__()
        self.text = text
        self.callback = callback
        self.size = size
        
        # 设置窗口属性
        frameless_flag = getattr(QtCore.Qt, 'FramelessWindowHint')
        tool_flag = getattr(QtCore.Qt, 'Tool')
        self.setWindowFlags(frameless_flag | tool_flag)
        translucent_flag = getattr(QtCore.Qt, 'WA_TranslucentBackground')
        self.setAttribute(translucent_flag)
        
        # 设置位置和大小
        self.setGeometry(x, y, size, size)
        self.setFixedSize(size, size)
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        
        # 根据文本设置对应的图标路径
        icon_map = {
            "AI翻译": os.path.join(os.path.dirname(__file__), "..", "icons", "ai_translate.png"),
            "文本润色": os.path.join(os.path.dirname(__file__), "..", "icons", "text_polish.png"),
            "AI问答": os.path.join(os.path.dirname(__file__), "..", "icons", "ai_qa.png"),
            "语音翻译": os.path.join(os.path.dirname(__file__), "..", "icons", "speech_translate.png"),
            "设置": os.path.join(os.path.dirname(__file__), "..", "icons", "settings.png")
        }
        self.icon_path = icon_map.get(text, "")
        self.icon_pixmap = None
        if self.icon_path and os.path.exists(self.icon_path):
            # 尝试加载图标
            try:
                self.icon_pixmap = QtGui.QPixmap(self.icon_path)
            except Exception as e:
                print(f"无法加载图标 {self.icon_path}: {e}")
                self.icon_pixmap = None

    def paintEvent(self, event):
        """绘制气泡"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 绘制气泡背景
        gradient = QtGui.QRadialGradient(
            self.width() / 2, self.height() / 2, self.width() / 2
        )
        gradient.setColorAt(0, QtGui.QColor(240, 248, 255, 120))  # Alice blue
        gradient.setColorAt(1, QtGui.QColor(176, 224, 230, 120))  # Powder blue
        
        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(QtGui.QPen(QtGui.QColor(70, 130, 180), 1))
        painter.drawEllipse(1, 1, self.width() - 2, self.height() - 2)
        
        # 绘制图标或文字
        if self.icon_pixmap and not self.icon_pixmap.isNull():
            # 绘制PNG图标
            icon_size = min(self.width(), self.height()) * 0.6
            icon_x = (self.width() - icon_size) / 2
            icon_y = (self.height() - icon_size) / 2
            # 缩放图标以适应指定大小
            keep_aspect_ratio = getattr(QtCore.Qt, 'KeepAspectRatio')
            smooth_transformation = getattr(QtCore.Qt, 'SmoothTransformation')
            scaled_pixmap = self.icon_pixmap.scaled(
                int(icon_size), 
                int(icon_size), 
                keep_aspect_ratio, 
                smooth_transformation
            )
            painter.drawPixmap(int(icon_x), int(icon_y), scaled_pixmap)
        else:
            # 如果图标加载失败，则绘制文字
            painter.setPen(QtGui.QColor(30, 30, 30))
            painter.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Normal))
            align_center = getattr(QtCore.Qt, 'AlignCenter')
            painter.drawText(self.rect(), align_center, self.text)

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        left_button = getattr(QtCore.Qt, 'LeftButton')
        if event.button() == left_button:
            self.callback()
            event.accept()

    def enterEvent(self, event):
        """鼠标进入事件"""
        pointing_hand_cursor = getattr(QtCore.Qt, 'PointingHandCursor')
        self.setCursor(pointing_hand_cursor)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        arrow_cursor = getattr(QtCore.Qt, 'ArrowCursor')
        self.setCursor(arrow_cursor)


def main():  # 独立运行调试入口
    from config.app_config import AppConfig
    from services.ai_client import AIClient
    from services.translation_service import TranslationService
    app = QtWidgets.QApplication(sys.argv)
    cfg = AppConfig()
    client = AIClient(cfg.ai_server, cfg.api_key)
    trans = TranslationService(client, cfg)
    floating_window = FloatingWindow(cfg, client, trans)
    floating_window.show()
    sys.exit(app.exec_())