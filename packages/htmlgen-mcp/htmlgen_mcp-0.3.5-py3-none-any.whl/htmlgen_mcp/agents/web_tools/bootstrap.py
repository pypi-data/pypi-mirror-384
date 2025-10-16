"""Bootstrap 相关工具"""
from __future__ import annotations

import re
from pathlib import Path


def add_bootstrap(project_path: str):
    """为项目添加Bootstrap CSS/JS（递归处理所有HTML）"""
    try:
        base = Path(project_path)
        html_files = list(base.rglob("*.html"))

        bootstrap_css = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
        bootstrap_js = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>'

        for html_file in html_files:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 先移除所有重复的 bootstrap 片段，稍后统一按规范插入一次
            content = re.sub(re.escape(bootstrap_css) + r"\s*", "", content)
            content = re.sub(re.escape(bootstrap_js) + r"\s*", "", content)

            # 添加Bootstrap CSS到head（带兜底）
            if "</head>" in content:
                content = content.replace("</head>", f"    {bootstrap_css}\n</head>")
            elif "<head>" in content:
                content = content.replace("<head>", f"<head>\n    {bootstrap_css}\n")
            else:
                # 没有head，前置插入
                content = bootstrap_css + "\n" + content

            # 添加Bootstrap JS到body末尾（带兜底）
            if "</body>" in content:
                content = content.replace("</body>", f"    {bootstrap_js}\n</body>")
            else:
                content = content + "\n" + bootstrap_js

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(content)

        return f"Bootstrap已添加到 {len(html_files)} 个HTML文件"
    except Exception as e:
        raise RuntimeError(f"添加Bootstrap失败: {str(e)}")



__all__ = ["add_bootstrap"]
