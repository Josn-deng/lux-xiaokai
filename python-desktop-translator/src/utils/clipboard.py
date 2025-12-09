import pyperclip

def get_clipboard_text():
    """获取剪贴板中的文本"""
    return pyperclip.paste()

def set_clipboard_text(text):
    """设置剪贴板中的文本"""
    pyperclip.copy(text)

def clear_clipboard():
    """清空剪贴板"""
    pyperclip.copy("")