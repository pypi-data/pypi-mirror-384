"""浏览器预览与本地服务器工具"""
from __future__ import annotations

import os
import subprocess
import webbrowser


def open_in_browser(file_path: str):
    """在默认浏览器中打开HTML文件"""
    try:
        abs_path = os.path.abspath(file_path)
        webbrowser.open(f"file://{abs_path}")
        return f"已在浏览器中打开: {abs_path}"
    except Exception as e:
        return f"打开浏览器失败: {str(e)}"


def start_live_server(directory: str, port: int = 8000):
    """启动简单的HTTP服务器用于预览"""
    try:
        cmd = f"cd {directory} && python -m http.server {port}"
        subprocess.Popen(cmd, shell=True)
        return f"开发服务器已启动: http://localhost:{port}"
    except Exception as e:
        return f"启动服务器失败: {str(e)}"

__all__ = ["open_in_browser", "start_live_server"]
