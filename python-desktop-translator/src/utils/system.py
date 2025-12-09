def get_system_info():
    import platform
    import os

    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "os_env": os.environ
    }
    
    return system_info

def check_internet_connection():
    import socket

    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def open_url(url):
    import webbrowser

    webbrowser.open(url)

def restart_application():
    """重启应用程序"""
    import sys
    import os
    import platform

    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包的应用
            system = platform.system().lower()
            if system == "darwin":  # macOS
                # 在 macOS .app 中，重启整个应用
                app_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
                os.execv(sys.executable, [sys.executable])
            else:
                # Windows 或其他系统
                os.execv(sys.executable, [sys.executable] + sys.argv[1:])
        else:
            # 开发环境
            os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        print(f"Failed to restart application: {e}")
        # 如果重启失败，至少尝试退出，让用户手动重启
        sys.exit(0)