"""配色相关的工具函数与调色板生成逻辑"""
from __future__ import annotations

import colorsys
import json


def _normalize_hex_color(color: str) -> str:
    """规范化十六进制颜色字符串，支持 #RGB 与 #RRGGBB"""
    if not color:
        return "#000000"
    value = color.strip().lstrip('#')
    if len(value) == 3:
        value = ''.join(ch * 2 for ch in value)
    if len(value) != 6:
        return "#000000"
    try:
        int(value, 16)
    except ValueError:
        return "#000000"
    return f"#{value.lower()}"


def _hex_to_rgb_tuple(color: str) -> tuple[int, int, int]:
    """将十六进制颜色转换为 RGB 元组"""
    normalized = _normalize_hex_color(color)[1:]
    return tuple(int(normalized[i:i + 2], 16) for i in (0, 2, 4))


def _hex_to_rgb_string(color: str) -> str:
    """将十六进制颜色转换为 r, g, b 字符串"""
    r, g, b = _hex_to_rgb_tuple(color)
    return f"{r}, {g}, {b}"


def _hls_to_hex(h: float, l: float, s: float) -> str:
    """将 HLS 颜色转换为十六进制颜色字符串"""
    r, g, b = colorsys.hls_to_rgb(h % 1.0, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return "#" + ''.join(f"{int(round(channel * 255)):02x}" for channel in (r, g, b))


def _shift_lightness(color: str, delta: float) -> str:
    """调节颜色亮度"""
    r, g, b = [c / 255.0 for c in _hex_to_rgb_tuple(color)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return _hls_to_hex(h, max(0.0, min(1.0, l + delta)), s)


def _shift_hue(color: str, delta: float, saturation_scale: float = 1.0, lightness_delta: float = 0.0) -> str:
    """在 HLS 空间中调整色相/饱和/亮度"""
    r, g, b = [c / 255.0 for c in _hex_to_rgb_tuple(color)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return _hls_to_hex(
        h + delta,
        max(0.0, min(1.0, l + lightness_delta)),
        max(0.0, min(1.0, s * saturation_scale)),
    )


def generate_color_scheme(base_color: str = "#007bff") -> str:
    """生成进阶配色方案，返回JSON与CSS示例"""
    try:
        base = _normalize_hex_color(base_color or "#007bff")
        accent = _shift_hue(base, 0.12, 1.05, 0.02)
        accent_alt = _shift_hue(base, -0.08, 1.08, 0.08)
        secondary = _shift_hue(base, 0.55, 0.7, 0.04)
        success = _shift_hue(base, 0.33, 0.6, 0.08)
        warning = _shift_hue(base, -0.18, 0.55, 0.18)
        danger = _shift_hue(base, -0.08, 0.8, -0.22)

        palette = {
            "primary": base,
            "primary_light": _shift_lightness(base, 0.2),
            "primary_dark": _shift_lightness(base, -0.2),
            "accent": accent,
            "accent_light": _shift_lightness(accent, 0.18),
            "accent_alt": accent_alt,
            "secondary": secondary,
            "neutral_light": "#f6f7fb",
            "neutral_dark": "#171a23",
            "dark_primary": _shift_lightness(base, -0.1),
            "dark_accent": _shift_lightness(accent, -0.15),
            "support": {
                "success": success,
                "warning": warning,
                "danger": danger,
                "info": _shift_hue(base, 0.2, 0.8, 0.05),
            },
            "gradients": {
                "primary": f"linear-gradient(135deg, {base} 0%, {_shift_lightness(accent, 0.25)} 100%)",
                "warm": f"linear-gradient(135deg, {warning} 0%, {_shift_lightness(warning, 0.18)} 100%)",
                "cool": f"linear-gradient(135deg, {secondary} 0%, {accent} 100%)",
            },
        }

        css_preview = (
            f":root {{\n"
            f"  --primary: {palette['primary']};\n"
            f"  --primary-light: {palette['primary_light']};\n"
            f"  --primary-dark: {palette['primary_dark']};\n"
            f"  --accent: {palette['accent']};\n"
            f"  --accent-rgb: {_hex_to_rgb_string(palette['accent'])};\n"
            f"  --secondary: {palette['secondary']};\n"
            f"  --gray-50: {palette['neutral_light']};\n"
            f"  --gray-900: {palette['neutral_dark']};\n"
            f"  --gradient-primary: {palette['gradients']['primary']};\n"
            f"  --gradient-cool: {palette['gradients']['cool']};\n"
            f"}}\n"
            f":root[data-theme='dark'] {{\n"
            f"  --primary: {palette['dark_primary']};\n"
            f"  --accent: {palette['dark_accent']};\n"
            f"  --gradient-primary: linear-gradient(135deg, {palette['dark_primary']} 0%, {palette['dark_accent']} 100%);\n"
            f"}}"
        )

        palette_json = json.dumps(palette, ensure_ascii=False, indent=2)
        guidance = (
            "配色方案生成完成。\n"
            f"palette = {palette_json}\n\n"
            "✅ 可用于 create_css_file(path, palette=palette) 自动写入 CSS 变量。\n"
            "✅ 支持在 HTML/JS 中引用 palette['gradients'] 做背景或按钮。\n"
            "CSS 变量示例：\n" + css_preview
        )
        return guidance
    except Exception as exc:  # noqa: BLE001
        return f"生成配色方案失败: {str(exc)}"


__all__ = [
    "generate_color_scheme",
    "_normalize_hex_color",
    "_hex_to_rgb_tuple",
    "_hex_to_rgb_string",
    "_hls_to_hex",
    "_shift_lightness",
    "_shift_hue",
]
