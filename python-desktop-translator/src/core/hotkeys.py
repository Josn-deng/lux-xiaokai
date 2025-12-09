"""全局热键支持。

如果运行环境未安装 pynput，则热键功能自动降级为 no-op，避免启动时报错。
"""

try:
    from pynput import keyboard  # type: ignore
except ImportError:  # 环境缺失依赖时的降级处理
    keyboard = None  # type: ignore
    print("[HotkeyManager] pynput 未安装，已禁用全局热键功能。请执行: pip install pynput")

class HotkeyManager:
    """简单全局热键管理：支持类似 'ctrl+alt+t' 的组合。"""

    def __init__(self):
        self.hotkeys = {}  # combination string -> callback
        self._pressed = set()  # 当前按下的键（str）
        self.listener = None

    def register_hotkey(self, key_combination: str, callback):
        combo_norm = self._normalize(key_combination)
        self.hotkeys[combo_norm] = callback
        if keyboard is None:
            # 依赖缺失时直接返回，不启动监听
            return
        self._start_listener()

    def _start_listener(self):
        if keyboard is None:
            return
        if self.listener is None:
            self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self.listener.start()

    def _on_press(self, key):
        key_str = self._key_to_str(key)
        if key_str:
            self._pressed.add(key_str)
        self._check_hotkeys()

    def _on_release(self, key):
        key_str = self._key_to_str(key)
        if key_str and key_str in self._pressed:
            self._pressed.remove(key_str)

    def _check_hotkeys(self):
        for combo, callback in self.hotkeys.items():
            parts = combo.split('+')
            if all(p in self._pressed for p in parts):
                try:
                    callback()
                except Exception as e:
                    print(f"Hotkey callback error for {combo}: {e}")

    def _key_to_str(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            name = str(key).replace('Key.', '').lower()
            return name
        except Exception:
            return None

    def _normalize(self, combo: str):
        parts = [p.strip().lower() for p in combo.split('+') if p.strip()]
        return '+'.join(parts)

    def stop_listener(self):
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None