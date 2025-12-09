import os
import sys
import winreg as reg

def add_to_startup():
    # 获取当前脚本的绝对路径
    script_path = os.path.abspath(sys.argv[0])
    
    # 注册表路径
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_SET_VALUE)
    
    # 添加开机自启项
    reg.SetValueEx(key, 'PythonDesktopTranslator', 0, reg.REG_SZ, script_path)
    reg.CloseKey(key)

if __name__ == "__main__":
    add_to_startup()