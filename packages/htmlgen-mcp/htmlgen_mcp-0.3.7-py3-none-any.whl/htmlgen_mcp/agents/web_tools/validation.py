"""HTML 验证与移动端检查工具"""
from __future__ import annotations

import re


def validate_html(file_path: str):
    """简单的HTML语法验证"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 基础检查
        issues = []
        if "<!DOCTYPE html>" not in content:
            issues.append("缺少DOCTYPE声明")
        if "<html" not in content:
            issues.append("缺少html标签")
        if "<head>" not in content:
            issues.append("缺少head标签")
        if "<body>" not in content:
            issues.append("缺少body标签")
        if 'charset="UTF-8"' not in content and 'charset=utf-8' not in content:
            issues.append("建议添加UTF-8字符编码")

        if issues:
            return f"HTML验证发现问题: {', '.join(issues)}"
        else:
            return "HTML结构验证通过"
    except Exception as e:
        return f"HTML验证失败: {str(e)}"


def check_mobile_friendly(file_path: str):
    """检查移动端友好性"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        checks = []

        # 检查viewport meta标签
        if 'name="viewport"' in content:
            checks.append("✓ 包含viewport meta标签")
        else:
            checks.append("✗ 缺少viewport meta标签")

        # 检查响应式CSS
        if "@media" in content or "bootstrap" in content.lower():
            checks.append("✓ 包含响应式设计")
        else:
            checks.append("! 可能缺少响应式设计")

        # 检查图片优化
        if 'style="max-width: 100%"' in content or 'class="img-fluid"' in content:
            checks.append("✓ 图片已优化")
        else:
            checks.append("! 建议为图片添加响应式类")

        return "移动端友好性检查:\n" + "\n".join(checks)

    except Exception as e:
        return f"移动端检查失败: {str(e)}"

__all__ = ["validate_html", "check_mobile_friendly"]
