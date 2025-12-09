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
    import sys
    import os

    os.execv(sys.executable, ['python'] + sys.argv)