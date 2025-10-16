"""项目结构相关工具"""
from __future__ import annotations

from pathlib import Path


def create_project_structure(project_name: str, project_path: str) -> str:
    """创建网页项目的基础文件夹结构"""
    if project_name in project_path:
        base_path = Path(project_path)
    else:
        base_path = Path(project_path) / project_name

    dirs = [
        "assets",
        "assets/css",
        "assets/js",
        "assets/images",
    ]

    try:
        base_path.mkdir(parents=True, exist_ok=True)
        for dir_name in dirs:
            (base_path / dir_name).mkdir(parents=True, exist_ok=True)
        return f"项目结构创建成功: {base_path}"
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"创建项目结构失败: {str(exc)}")


__all__ = ["create_project_structure"]
