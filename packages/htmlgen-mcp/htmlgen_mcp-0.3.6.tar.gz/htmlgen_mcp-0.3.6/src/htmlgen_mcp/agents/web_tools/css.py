"""CSS 样式生成相关工具"""
from __future__ import annotations

import json
from pathlib import Path

from .colors import (
    _hex_to_rgb_string,
    _normalize_hex_color,
    _shift_hue,
    _shift_lightness,
)


def create_css_file(file_path: str, content: str = "", palette: dict | str | None = None):
    """创建CSS文件，包含现代化设计系统，可传入自定义调色板"""

    palette_dict: dict | None = None
    if palette:
        if isinstance(palette, str):
            try:
                palette_dict = json.loads(palette)
            except json.JSONDecodeError:
                palette_dict = None
        elif isinstance(palette, dict):
            palette_dict = palette

    primary = _normalize_hex_color(palette_dict["primary"]) if palette_dict and palette_dict.get("primary") else "#0d6efd"
    accent = _normalize_hex_color(palette_dict["accent"]) if palette_dict and palette_dict.get("accent") else _shift_hue(primary, 0.12, 1.05, 0.02)
    secondary = _normalize_hex_color(palette_dict["secondary"]) if palette_dict and palette_dict.get("secondary") else _shift_hue(primary, 0.52, 0.75, 0.04)
    primary_light = _normalize_hex_color(palette_dict["primary_light"]) if palette_dict and palette_dict.get("primary_light") else _shift_lightness(primary, 0.18)
    primary_dark = _normalize_hex_color(palette_dict["primary_dark"]) if palette_dict and palette_dict.get("primary_dark") else _shift_lightness(primary, -0.18)
    accent_light = _normalize_hex_color(palette_dict["accent_light"]) if palette_dict and palette_dict.get("accent_light") else _shift_lightness(accent, 0.15)
    neutral_light = _normalize_hex_color(palette_dict["neutral_light"]) if palette_dict and palette_dict.get("neutral_light") else "#f8f9fa"
    neutral_dark = _normalize_hex_color(palette_dict["neutral_dark"]) if palette_dict and palette_dict.get("neutral_dark") else "#212529"
    dark_primary = _normalize_hex_color(palette_dict["dark_primary"]) if palette_dict and palette_dict.get("dark_primary") else _shift_lightness(primary, -0.1)
    dark_accent = _normalize_hex_color(palette_dict["dark_accent"]) if palette_dict and palette_dict.get("dark_accent") else _shift_lightness(accent, 0.1)

    support_colors: dict[str, str] = {}
    if isinstance(palette_dict, dict):
        maybe_support = palette_dict.get("support")
        if isinstance(maybe_support, dict):
            support_colors = maybe_support

    success_color = _normalize_hex_color(support_colors["success"]) if support_colors.get("success") else _shift_hue(primary, 0.33, 0.6, 0.08)
    warning_color = _normalize_hex_color(support_colors["warning"]) if support_colors.get("warning") else _shift_hue(primary, -0.18, 0.55, 0.18)
    danger_color = _normalize_hex_color(support_colors["danger"]) if support_colors.get("danger") else _shift_hue(primary, -0.08, 0.8, -0.22)
    info_color = _normalize_hex_color(support_colors["info"]) if support_colors.get("info") else _shift_hue(primary, 0.18, 0.75, 0.05)

    palette_block = ""
    if palette_dict:
        palette_block = f"""
/* 🎨 自定义配色覆盖 */
:root {{
  --primary: {primary};
  --primary-rgb: {_hex_to_rgb_string(primary)};
  --primary-dark: {primary_dark};
  --primary-light: {primary_light};
  --secondary: {secondary};
  --secondary-rgb: {_hex_to_rgb_string(secondary)};
  --accent: {accent};
  --accent-rgb: {_hex_to_rgb_string(accent)};
  --success: {success_color};
  --warning: {warning_color};
  --danger: {danger_color};
  --info: {info_color};
  --gray-50: {neutral_light};
  --gray-100: {neutral_light};
  --gray-900: {neutral_dark};
  --gradient-primary: linear-gradient(135deg, {primary} 0%, {accent_light} 100%);
  --gradient-secondary: linear-gradient(135deg, {accent} 0%, {primary_light} 100%);
  --gradient-cool: linear-gradient(135deg, {primary} 0%, {accent} 100%);
  --glass-bg: rgba(255, 255, 255, 0.78);
  --glass-border: rgba(255, 255, 255, 0.22);
}}

:root[data-theme='dark'] {{
  --primary: {dark_primary};
  --primary-rgb: {_hex_to_rgb_string(dark_primary)};
  --primary-light: {primary};
  --accent: {dark_accent};
  --accent-rgb: {_hex_to_rgb_string(dark_accent)};
  --gray-50: #0f1115;
  --gray-900: #eef1f6;
  --gradient-primary: linear-gradient(135deg, {dark_primary} 0%, {dark_accent} 100%);
  --gradient-cool: linear-gradient(135deg, {dark_primary} 0%, {accent} 100%);
  --glass-bg: rgba(20, 24, 32, 0.55);
  --glass-border: rgba(255, 255, 255, 0.14);
}}
"""

    css_template = f"""/* 🎨 现代化设计系统 - Design System v2.0 */

/* ==================== 设计变量系统 ==================== */
:root {{
  /* 色彩系统 - Color System */
  --primary: #0d6efd;
  --primary-rgb: 13, 110, 253;
  --primary-dark: #0b5ed7;
  --primary-light: #3d8bfd;
  --secondary: #6c757d;
  --secondary-rgb: 108, 117, 125;
  --accent: #6610f2;
  --accent-rgb: 102, 16, 242;
  --success: #198754;
  --warning: #ffc107;
  --danger: #dc3545;
  --info: #0dcaf0;

  /* 中性色 - Neutral Colors */
  --white: #ffffff;
  --gray-50: #f8f9fa;
  --gray-100: #f1f3f5;
  --gray-200: #e9ecef;
  --gray-300: #dee2e6;
  --gray-400: #ced4da;
  --gray-500: #adb5bd;
  --gray-600: #6c757d;
  --gray-700: #495057;
  --gray-800: #343a40;
  --gray-900: #212529;
  --black: #000000;

  /* 渐变系统 - Gradients */
  --gradient-primary: linear-gradient(135deg, var(--primary) 0%, #5a8bff 50%, var(--accent) 100%);
  --gradient-secondary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-success: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  --gradient-warm: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  --gradient-cool: linear-gradient(135deg, #30cfd0 0%, #330867 100%);
  --gradient-mesh: radial-gradient(at 40% 20%, hsla(28,100%,74%,1) 0px, transparent 50%),
                   radial-gradient(at 80% 0%, hsla(189,100%,56%,1) 0px, transparent 50%),
                   radial-gradient(at 0% 50%, hsla(355,100%,93%,1) 0px, transparent 50%);

  /* 间距系统 - Spacing System */
  --space-xxs: 0.25rem;
  --space-xs: 0.5rem;
  --space-sm: 1rem;
  --space-md: 1.5rem;
  --space-lg: 2rem;
  --space-xl: 3rem;
  --space-xxl: 5rem;
  --space-xxxl: 8rem;

  /* 字体系统 - Typography System */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
               Arial, 'Noto Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  --font-size-4xl: 2.25rem;
  --font-size-5xl: 3rem;
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* 圆角系统 - Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-xl: 1.5rem;
  --radius-2xl: 2rem;
  --radius-full: 9999px;

  /* 阴影系统 - Shadow System */
  --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  --shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
  --shadow-colored: 0 10px 40px -10px rgba(var(--primary-rgb), 0.3);
  --shadow-glass: 0 8px 32px 0 rgba(31, 38, 135, 0.37);

  /* 动画时长 - Animation Duration */
  --duration-fast: 150ms;
  --duration-base: 250ms;
  --duration-slow: 400ms;
  --duration-slower: 600ms;

  /* 动画缓动 - Animation Easing */
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);

  /* 毛玻璃效果 - Glassmorphism */
  --glass-bg: rgba(255, 255, 255, 0.75);
  --glass-border: rgba(255, 255, 255, 0.18);
  --glass-blur: blur(10px);
  --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}}

/* 暗色主题变量覆盖（高端深色质感） */
:root[data-theme='dark'] {{
  --white: #0f1115;
  --gray-50: #0f1115;
  --gray-100: #12151c;
  --gray-200: #161a22;
  --gray-300: #1b202a;
  --gray-400: #242b38;
  --gray-500: #5a667a;
  --gray-600: #7e8aa3;
  --gray-700: #a5b1c7;
  --gray-800: #d2d7e1;
  --gray-900: #eef1f6;
  --black: #ffffff;

  --primary: #5a8bff;
  --primary-rgb: 90, 139, 255;
  --primary-dark: #3c66d7;
  --primary-light: #8bb0ff;
  --accent: #8b5cf6;
  --accent-rgb: 139, 92, 246;
  --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  --gradient-mesh: radial-gradient(at 30% 20%, rgba(99,102,241,.35) 0px, transparent 50%),
                   radial-gradient(at 80% 10%, rgba(56,189,248,.25) 0px, transparent 50%),
                   radial-gradient(at 10% 60%, rgba(139,92,246,.25) 0px, transparent 50%);

  --glass-bg: rgba(20, 24, 32, 0.55);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-blur: blur(12px);
  --glass-shadow: 0 8px 32px rgba(0,0,0,.45);
}}

{palette_block}

/* ==================== 基础重置 ==================== */
*, *::before, *::after {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html {{
  scroll-behavior: smooth;
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
}}

body {{
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  color: var(--gray-900);
  background: var(--gray-50);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
  position: relative;
}}

/* 响应式字体大小 */
@media (max-width: 768px) {{
  html {{ font-size: 14px; }}
}}

/* ==================== 媒体元素 ==================== */
img, picture, video, canvas, svg {{
  display: block;
  max-width: 100%;
  height: auto;
}}

img {{
  object-fit: cover;
  font-style: italic;
}}

/* 图片加载优化 */
img[loading="lazy"] {{
  background: linear-gradient(135deg, var(--gray-100) 0%, var(--gray-200) 100%);
}}

/* ==================== 布局系统 ==================== */
.section {{
  padding: var(--space-xxl) 0;
  position: relative;
  overflow: hidden;
}}

.section-sm {{
  padding: var(--space-xl) 0;
}}

.section-lg {{
  padding: var(--space-xxxl) 0;
}}

/* 标题系统 */
.section-title {{
  font-size: clamp(var(--font-size-2xl), 5vw, var(--font-size-4xl));
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  margin-bottom: var(--space-md);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
}}

.section-lead {{
  font-size: var(--font-size-lg);
  color: var(--gray-600);
  max-width: 720px;
  margin: 0 auto var(--space-xl);
  text-align: center;
  line-height: var(--line-height-relaxed);
}}

/* 容器系统 */
.container {{
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}}

@media (min-width: 768px) {{
  .container {{
    padding: 0 var(--space-lg);
  }}
}}

/* ==================== Hero 区域 ==================== */
.hero {{
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  color: var(--white);
  overflow: hidden;
}}

/* 动态背景效果 */
.hero::before {{
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: var(--gradient-mesh);
  opacity: 0.3;
  animation: heroFloat 20s ease-in-out infinite;
}}

.hero-overlay {{
  position: relative;
  overflow: hidden;
}}

.hero-overlay .overlay {{
  position: absolute;
  inset: 0;
  background: linear-gradient(200deg, rgba(17, 24, 39, 0.65) 0%, rgba(17, 24, 39, 0.35) 55%, rgba(17, 24, 39, 0.08) 100%);
  mix-blend-mode: multiply;
  backdrop-filter: blur(6px);
  z-index: 0;
}}

.hero-overlay .container {{
  position: relative;
  z-index: 1;
}}

@keyframes heroFloat {{
  0%, 100% {{ transform: rotate(0deg) scale(1); }}
  33% {{ transform: rotate(10deg) scale(1.1); }}
  66% {{ transform: rotate(-10deg) scale(0.95); }}
}}

.hero-inner {{
  position: relative;
  z-index: 1;
  padding: var(--space-xxl) 0;
  text-align: center;
}}

.hero h1 {{
  font-size: clamp(var(--font-size-3xl), 7vw, var(--font-size-5xl));
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--space-md);
  animation: fadeInUp 0.8s ease-out;
}}

.hero .lead {{
  font-size: clamp(var(--font-size-lg), 3vw, var(--font-size-xl));
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto var(--space-lg);
  animation: fadeInUp 0.8s ease-out 0.2s both;
}}

/* 波浪分割 */
.shape-bottom {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  line-height: 0;
  z-index: 1;
}}

  .shape-bottom svg {{
    display: block;
    width: calc(100% + 1.3px);
    height: clamp(30px, 10vw, 120px);
  }}

/* ==================== 扩展风格布局 ==================== */
.badge-soft {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.4rem 1rem;
  border-radius: var(--radius-full);
  background: rgba(var(--primary-rgb), 0.12);
  color: var(--primary);
  font-weight: var(--font-weight-medium);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.hero-floating {{
  position: absolute;
  inset: -10%;
  pointer-events: none;
  overflow: hidden;
}}

.floating-shape {{
  position: absolute;
  border-radius: 50%;
  width: clamp(180px, 22vw, 320px);
  height: clamp(180px, 22vw, 320px);
  background: var(--gradient-primary);
  filter: blur(50px);
  opacity: 0.35;
  animation: float-large 12s ease-in-out infinite;
}}

.floating-shape.shape-one {{ top: 10%; left: -4%; }}
.floating-shape.shape-two {{ bottom: -6%; right: -2%; animation-delay: 4s; }}

@keyframes float-large {{
  0%, 100% {{ transform: translate3d(0, 0, 0) scale(1); }}
  50% {{ transform: translate3d(20px, -20px, 0) scale(1.05); }}
}}

[data-parallax] {{
  --parallax-offset: 0px;
  will-change: transform;
}}

[data-parallax]:not([data-tilt]) {{
  transform: translate3d(0, var(--parallax-offset), 0);
}}

[data-tilt] {{
  --tilt-rotate-x: 0deg;
  --tilt-rotate-y: 0deg;
  --tilt-translate-z: 0px;
  transform-style: preserve-3d;
  transition: transform var(--duration-base) var(--ease-out);
  will-change: transform;
  transform: translate3d(0, var(--parallax-offset, 0px), 0) rotateX(var(--tilt-rotate-x)) rotateY(var(--tilt-rotate-y)) translateZ(var(--tilt-translate-z));
}}

.marquee-clients {{
  gap: clamp(1.5rem, 4vw, 3rem) !important;
  font-size: 1.05rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}}

.form-floating-cards {{
  background: rgba(var(--primary-rgb), 0.04);
  border-radius: var(--radius-2xl);
  padding: var(--space-xl);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(var(--primary-rgb), 0.08);
}}

.hero-minimal {{
  min-height: 100vh;
  display: flex;
  align-items: center;
  background: radial-gradient(circle at 0 0, rgba(var(--primary-rgb), 0.14) 0%, transparent 55%),
              radial-gradient(circle at 100% 100%, rgba(var(--accent-rgb), 0.18) 0%, transparent 45%),
              var(--gradient-primary);
  color: var(--white);
  position: relative;
  overflow: hidden;
}}

.hero-minimal .container {{ position: relative; z-index: 2; }}

.minimal-grid {{
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: clamp(2rem, 6vw, 6rem);
  align-items: center;
}}

.hero-minimal__content {{
  text-align: left;
  color: rgba(255, 255, 255, 0.92);
  max-width: 540px;
}}

.hero-minimal__content .display-4 {{
  font-weight: var(--font-weight-semibold);
  letter-spacing: -0.01em;
  margin-bottom: var(--space-md);
}}

.hero-minimal__cta {{
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}}

.tagline {{
  display: inline-block;
  font-size: var(--font-size-sm);
  letter-spacing: 0.22em;
  text-transform: uppercase;
  opacity: 0.7;
  margin-bottom: var(--space-xs);
}}

.hero-minimal__gallery {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-md);
}}

.hero-minimal__gallery .gallery-card {{
  aspect-ratio: 4 / 3;
  border-radius: var(--radius-2xl);
  background: rgba(255, 255, 255, 0.15);
  overflow: hidden;
  position: relative;
  box-shadow: var(--shadow-xl);
}}

.hero-minimal__gallery .gallery-card::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent, rgba(0,0,0,0.45));
}}

.hero-minimal__gallery .gallery-card.tall {{ grid-row: span 2; aspect-ratio: 3 / 5; }}

.section-alt {{
  background: var(--gray-50);
  color: var(--gray-900);
  padding-top: var(--space-xxl);
  padding-bottom: var(--space-xxl);
}}

:root[data-theme='dark'] .section-alt {{
  background: rgba(18, 22, 30, 0.75);
  color: var(--gray-100);
}}

.section-heading {{
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  margin-bottom: var(--space-xl);
  max-width: 720px;
}}

.section-heading .eyebrow {{
  font-size: var(--font-size-sm);
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(var(--primary-rgb), 0.65);
}}

.brand-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--space-lg);
  text-align: center;
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.7;
}}

.service-columns {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-lg);
}}

.service-card {{
  padding: var(--space-xl);
  border-radius: var(--radius-2xl);
  background: var(--white);
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: var(--shadow-sm);
}}

:root[data-theme='dark'] .service-card {{
  background: rgba(20, 24, 32, 0.9);
  border-color: rgba(255,255,255,0.06);
}}

.case-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}}

.case-card {{
  border-radius: var(--radius-2xl);
  overflow: hidden;
  background: var(--white);
  box-shadow: var(--shadow-xl);
  display: grid;
  grid-template-rows: auto 1fr;
}}

.case-card.tall {{ grid-row: span 2; }}

.case-image {{
  aspect-ratio: 4 / 3;
  background: rgba(var(--primary-rgb), 0.12);
}}

.case-meta {{
  padding: var(--space-lg);
}}

.testimonial-spotlight {{
  display: grid;
  gap: var(--space-xl);
  grid-template-columns: minmax(0, 1fr) minmax(0, 420px);
  align-items: center;
}}

.testimonial-copy blockquote {{
  font-size: var(--font-size-xl);
  line-height: 1.75;
  margin: var(--space-md) 0;
}}

.testimonial-portrait {{
  aspect-ratio: 3 / 4;
  border-radius: var(--radius-2xl);
  overflow: hidden;
  box-shadow: var(--shadow-2xl);
}}

.pricing-stack {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-lg);
}}

.pricing-card {{
  background: var(--white);
  border-radius: var(--radius-2xl);
  padding: var(--space-xl);
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(0,0,0,0.04);
}}

.pricing-card.featured {{
  background: var(--gradient-primary);
  color: var(--white);
  box-shadow: var(--shadow-xl);
}}

.pricing-card ul {{
  list-style: none;
  margin: var(--space-md) 0 0;
  padding: 0;
}}

.pricing-card li {{
  margin-bottom: var(--space-xs);
  opacity: 0.8;
}}

.faq-accordion details {{
  border-bottom: 1px solid rgba(0,0,0,0.1);
  padding: var(--space-md) 0;
}}

.faq-accordion summary {{
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}}

.contact-intro {{
  max-width: 520px;
  margin-bottom: var(--space-lg);
}}

.contact-form {{
  display: grid;
  gap: var(--space-md);
  background: var(--white);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  box-shadow: var(--shadow-lg);
}}

.contact-form .field-pair {{
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}}

.footer-minimal {{
  background: var(--gray-900);
  color: var(--white);
  padding: var(--space-xl) 0;
}}

.footer-minimal .container {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}}

.footer-minimal .footer-brand {{
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: var(--font-size-lg);
}}

.footer-minimal .footer-meta {{
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  opacity: 0.7;
}}

.hero-creative {{
  position: relative;
  min-height: 90vh;
  color: var(--white);
  background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.18), transparent 55%),
              radial-gradient(circle at 80% 0%, rgba(255,255,255,0.18), transparent 45%),
              var(--gradient-cool);
  overflow: hidden;
}}

.hero-noise {{
  position: absolute;
  inset: 0;
  opacity: 0.15;
}}

.hero-creative__orbit {{
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}}

.orbit {{
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.35);
  animation: orbit-rotate 24s linear infinite;
}}

.orbit-primary {{ width: 60vw; height: 60vw; }}
.orbit-accent {{ width: 40vw; height: 40vw; animation-duration: 18s; }}

@keyframes orbit-rotate {{
  0% {{ transform: rotate(0deg); }}
  100% {{ transform: rotate(360deg); }}
}}

.timeline {{
  display: grid;
  gap: var(--space-lg);
  position: relative;
  padding-left: 1.5rem;
}}

.timeline::before {{
  content: '';
  position: absolute;
  left: 0.4rem;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.2), rgba(var(--accent-rgb), 0.4));
}}

.timeline-item {{
  display: grid;
  gap: var(--space-xs);
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
}}

.timeline-dot {{
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary);
  margin-top: 6px;
  box-shadow: 0 0 0 6px rgba(var(--primary-rgb), 0.15);
}}

.ability-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}}

.ability-card {{
  padding: var(--space-xl);
  border-radius: var(--radius-2xl);
  color: var(--white);
  position: relative;
  overflow: hidden;
  min-height: 320px;
}}

.ability-card::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.55) 100%);
}}

.ability-card h3,
.ability-card p {{
  position: relative;
  z-index: 2;
}}

.nebula-grid {{
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}}

.nebula-card {{
  padding: var(--space-lg);
  border-radius: var(--radius-2xl);
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: var(--glass-shadow);
}}

.nebula-card__media {{
  border-radius: var(--radius-xl);
  aspect-ratio: 16 / 10;
  margin-bottom: var(--space-md);
  background: rgba(255,255,255,0.18);
}}

.gradient-panels {{
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}}

.panel-card {{
  padding: var(--space-xl);
  border-radius: var(--radius-2xl);
  background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.12), rgba(var(--accent-rgb), 0.2));
  color: var(--gray-900);
  min-height: 220px;
}}

.pricing-orbits {{
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}}

.orbit-card {{
  border-radius: var(--radius-2xl);
  padding: var(--space-xl);
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  color: var(--white);
}}

.orbit-card ul {{
  list-style: none;
  margin: var(--space-md) 0 0;
  padding: 0;
  opacity: 0.8;
}}

.contact-capsule {{
  padding: var(--space-xxl) var(--space-xl);
  border-radius: var(--radius-2xl);
  background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.3), rgba(var(--accent-rgb), 0.3));
  color: var(--white);
  box-shadow: var(--shadow-2xl);
  position: relative;
  overflow: hidden;
}}

.capsule-form {{
  display: grid;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}}

.capsule-form input,
.capsule-form textarea {{
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  color: var(--white);
}}

.footer-creative {{
  background: radial-gradient(circle at top, rgba(var(--primary-rgb), 0.18), transparent 70%), #040510;
  color: rgba(255,255,255,0.85);
  padding: var(--space-xl) 0;
}}

.footer-creative .container {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}}

.footer-creative__links {{
  display: flex;
  gap: var(--space-md);
}}

.footer-creative__links a {{
  color: inherit;
  text-decoration: none;
  opacity: 0.7;
}}

.footer-creative__links a:hover {{
  opacity: 1;
}}

@media (max-width: 991px) {{
  .minimal-grid {{ grid-template-columns: 1fr; }}
  .hero-minimal__content {{ text-align: center; margin: 0 auto; }}
  .hero-minimal__cta {{ justify-content: center; }}
  .hero-minimal__gallery {{ grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }}
  .testimonial-spotlight {{ grid-template-columns: 1fr; }}
  .footer-minimal .container,
  .footer-creative .container {{ flex-direction: column; text-align: center; }}
}}

/* ==================== 玻璃态导航 ==================== */
.navbar-glass {{
  position: sticky;
  top: 0;
  z-index: 1000;
  background: linear-gradient(to bottom, rgba(255,255,255,0.72), rgba(255,255,255,0.42));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.25);
  transition: all var(--duration-base) var(--ease-out);
}}

:root[data-theme='dark'] .navbar-glass {{
  background: linear-gradient(to bottom, rgba(16,18,24,0.65), rgba(16,18,24,0.35));
  border-bottom-color: rgba(255,255,255,0.06);
}}

.navbar-glass.scrolled {{
  box-shadow: 0 10px 30px -10px rgba(0,0,0,.2);
  background: linear-gradient(to bottom, rgba(255,255,255,0.82), rgba(255,255,255,0.52));
}}

:root[data-theme='dark'] .navbar-glass.scrolled {{
  background: linear-gradient(to bottom, rgba(16,18,24,0.75), rgba(16,18,24,0.45));
}}

.navbar-brand {{
  font-weight: 700;
  letter-spacing: .2px;
}}

.theme-toggle-btn {{
  border: 2px solid var(--gray-300);
  background: transparent;
  color: var(--gray-900);
  border-radius: var(--radius-full);
  padding: .4rem .8rem;
}}

:root[data-theme='dark'] .theme-toggle-btn {{
  color: var(--gray-800);
  border-color: var(--gray-400);
}}

/* ==================== 卡片系统 ==================== */
.feature-card {{
  background: var(--white);
  border-radius: var(--radius-xl);
  padding: var(--space-lg);
  height: 100%;
  position: relative;
  overflow: hidden;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-sm);
  --card-translate-y: 0px;
  --card-scale: 1;
  transform: translate3d(0, var(--parallax-offset, 0px), 0)
             translateY(var(--card-translate-y))
             scale(var(--card-scale))
             rotateX(var(--tilt-rotate-x, 0deg))
             rotateY(var(--tilt-rotate-y, 0deg))
             translateZ(var(--tilt-translate-z, 0px));
  transform-style: preserve-3d;
}}

/* 新拟态效果 */
.feature-card.neumorphic {{
  background: linear-gradient(145deg, #f0f0f0, #ffffff);
  box-shadow: 20px 20px 60px #d9d9d9, -20px -20px 60px #ffffff;
}}

/* 毛玻璃效果 */
.feature-card.glass {{
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
}}

.feature-card:hover {{
  --card-translate-y: -8px;
  --card-scale: 1.02;
  box-shadow: var(--shadow-2xl);
}}

/* 卡片悬停光效 */
.feature-card::before {{
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(var(--primary-rgb), 0.1), transparent);
  transition: left var(--duration-slow) var(--ease-out);
}}

.feature-card:hover::before {{
  left: 100%;
}}

/* 图标系统 */
.feature-icon {{
  width: 60px;
  height: 60px;
  border-radius: var(--radius-lg);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-primary);
  color: var(--white);
  font-size: 24px;
  margin-bottom: var(--space-md);
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-colored);
}}

.feature-icon::after {{
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
  transform: translate(-50%, -50%) scale(0);
  transition: transform var(--duration-base) var(--ease-out);
}}

.feature-card:hover .feature-icon::after {{
  transform: translate(-50%, -50%) scale(2);
}}

.feature-card h3 {{
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-sm);
  color: var(--gray-900);
}}

.feature-card p {{
  font-size: var(--font-size-base);
  color: var(--gray-600);
  line-height: var(--line-height-relaxed);
}}

.shadow-soft {{
  background: var(--white);
  border-radius: var(--radius-xl);
  box-shadow: 0 22px 45px -28px rgba(17, 24, 39, 0.4);
  transition: transform var(--duration-base) var(--ease-out), box-shadow var(--duration-base) var(--ease-out);
}}

.shadow-soft:hover {{
  transform: translateY(-6px);
  box-shadow: 0 30px 55px -26px rgba(17, 24, 39, 0.45);
}}

.icon-badge {{
  display: inline-flex;
  width: 3rem;
  height: 3rem;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  color: var(--white);
  box-shadow: var(--shadow-md);
  font-size: 1.35rem;
}}

.border-gradient {{
  border-radius: var(--radius-xl);
  border: 1px solid transparent;
  background:
    linear-gradient(var(--white), var(--white)) padding-box,
    linear-gradient(135deg, rgba(var(--primary-rgb), 0.28), rgba(255, 255, 255, 0.08)) border-box;
}}

.membership-card {{
  background: rgba(255, 255, 255, 0.94);
  border-radius: var(--radius-xl);
  border: 1px solid rgba(148, 163, 184, 0.18);
  transition: transform var(--duration-base) var(--ease-out), box-shadow var(--duration-base) var(--ease-out);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  color: var(--gray-800);
}}

.membership-card:hover {{
  transform: translateY(-6px);
  box-shadow: var(--shadow-2xl);
}}

.membership-card.highlight {{
  background: linear-gradient(135deg, rgba(30, 58, 138, 0.95) 0%, rgba(67, 56, 202, 0.95) 35%, rgba(245, 158, 11, 0.95) 100%);
  color: var(--white);
}}

.membership-card.highlight p,
.membership-card.highlight li {{
  color: rgba(255, 255, 255, 0.86);
}}

.testimonial-card {{
  border-radius: var(--radius-xl);
  border: 1px solid rgba(148, 163, 184, 0.25);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: var(--shadow-md);
  transition: transform var(--duration-base) var(--ease-out), box-shadow var(--duration-base) var(--ease-out);
}}

.testimonial-card:hover {{
  transform: translateY(-4px);
  box-shadow: var(--shadow-2xl);
}}

.avatar {{
  width: 64px;
  height: 64px;
  object-fit: cover;
}}

/* ==================== CTA 区域 ==================== */
.cta {{
  background: var(--gradient-primary);
  color: var(--white);
  border-radius: var(--radius-2xl);
  padding: var(--space-xxl) var(--space-xl);
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
}}

/* 动态背景粒子 */
.cta::before,
.cta::after {{
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}}

.cta::before {{
  width: 100px;
  height: 100px;
  top: -50px;
  left: -50px;
}}

.cta::after {{
  width: 150px;
  height: 150px;
  bottom: -75px;
  right: -75px;
  animation-delay: 3s;
}}

@keyframes float {{
  0%, 100% {{ transform: translateY(0) rotate(0deg); }}
  50% {{ transform: translateY(-20px) rotate(180deg); }}
}}

.cta h2 {{
  font-size: var(--font-size-3xl);
  margin-bottom: var(--space-md);
  position: relative;
  z-index: 1;
}}

.cta p {{
  font-size: var(--font-size-lg);
  margin-bottom: var(--space-lg);
  opacity: 0.95;
  position: relative;
  z-index: 1;
}}

/* ==================== 表单样式 ==================== */
.form-control {{
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--gray-900);
  background: var(--white);
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--ease-out);
}}

.form-control:hover {{
  border-color: var(--gray-300);
}}

.form-control:focus {{
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
}}

.form-control::placeholder {{
  color: var(--gray-500);
}}

/* 表单标签 */
.form-label {{
  display: block;
  margin-bottom: var(--space-xs);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--gray-700);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

/* ==================== 动画系统 ==================== */
/* 滚动显示动画 */
.reveal {{
  opacity: 0;
  transform: translateY(30px);
  transition: all var(--duration-slower) var(--ease-out);
}}

.reveal.revealed {{
  opacity: 1;
  transform: translateY(0);
}}

/* 渐入动画变体 */
.fade-in-up {{
  animation: fadeInUp 0.8s ease-out both;
}}

.fade-in-left {{
  animation: fadeInLeft 0.8s ease-out both;
}}

.fade-in-right {{
  animation: fadeInRight 0.8s ease-out both;
}}

.fade-in-scale {{
  animation: fadeInScale 0.8s ease-out both;
}}

@keyframes fadeInUp {{
  from {{
    opacity: 0;
    transform: translateY(30px);
  }}
  to {{
    opacity: 1;
    transform: translateY(0);
  }}
}}

@keyframes fadeInLeft {{
  from {{
    opacity: 0;
    transform: translateX(-30px);
  }}
  to {{
    opacity: 1;
    transform: translateX(0);
  }}
}}

@keyframes fadeInRight {{
  from {{
    opacity: 0;
    transform: translateX(30px);
  }}
  to {{
    opacity: 1;
    transform: translateX(0);
  }}
}}

@keyframes fadeInScale {{
  from {{
    opacity: 0;
    transform: scale(0.9);
  }}
  to {{
    opacity: 1;
    transform: scale(1);
  }}
}}

/* 打字机效果 */
.typewriter {{
  overflow: hidden;
  border-right: 3px solid var(--primary);
  white-space: nowrap;
  animation: typewriter 3s steps(40, end), blink 0.75s step-end infinite;
}}

@keyframes typewriter {{
  from {{ width: 0; }}
  to {{ width: 100%; }}
}}

@keyframes blink {{
  from, to {{ border-color: transparent; }}
  50% {{ border-color: var(--primary); }}
}}

/* 脉冲动画 */
.pulse {{
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.5; }}
}}

/* 弹跳动画 */
.bounce {{
  animation: bounce 1s infinite;
}}

@keyframes bounce {{
  0%, 100% {{
    transform: translateY(-25%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }}
  50% {{
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }}
}}

/* ==================== 按钮系统 ==================== */
.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
  border-radius: var(--radius-lg);
  border: none;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  position: relative;
  overflow: hidden;
  text-decoration: none;
  white-space: nowrap;
}}

/* 主按钮 */
.btn-primary {{
  background: var(--gradient-primary);
  color: var(--white);
  box-shadow: var(--shadow-colored);
}}

.btn-primary:hover {{
  transform: translateY(-2px);
  box-shadow: 0 15px 40px -5px rgba(var(--primary-rgb), 0.4);
}}

.btn-primary:active {{
  transform: translateY(0);
}}

/* 次要按钮 */
.btn-secondary {{
  background: var(--white);
  color: var(--gray-900);
  border: 2px solid var(--gray-200);
  box-shadow: var(--shadow-sm);
}}

.btn-secondary:hover {{
  background: var(--gray-50);
  border-color: var(--gray-300);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}}

/* 大按钮 */
.btn-lg {{
  padding: var(--space-md) var(--space-xl);
  font-size: var(--font-size-lg);
  border-radius: var(--radius-xl);
}}

.btn-gradient {{
  background: var(--gradient-primary);
  color: var(--white);
  border: none;
  box-shadow: var(--shadow-lg);
}}

.btn-gradient:hover {{
  transform: translateY(-2px);
  box-shadow: 0 18px 45px -12px rgba(var(--primary-rgb), 0.45);
  opacity: 0.95;
}}

.btn-dark-gradient {{
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(55, 65, 81, 0.95) 100%);
  color: var(--white);
  border: none;
  box-shadow: var(--shadow-lg);
}}

.btn-dark-gradient:hover {{
  transform: translateY(-2px);
  box-shadow: 0 20px 50px -15px rgba(17, 24, 39, 0.55);
}}

.btn-outline-primary {{
  color: var(--primary);
  border: 2px solid var(--primary);
  background: transparent;
}}

.btn-outline-primary:hover {{
  background: var(--primary);
  color: var(--white);
  box-shadow: var(--shadow-md);
}}

.btn-outline-light {{
  color: var(--white);
  border: 2px solid rgba(255, 255, 255, 0.6);
  background: transparent;
}}

.btn-outline-light:hover {{
  background: rgba(255, 255, 255, 0.15);
  color: var(--white);
  border-color: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}}

/* 按钮涟漪效果 */
.btn::before {{
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}}

.btn:active::before {{
  width: 300px;
  height: 300px;
}}

/* ==================== 工具类 ==================== */
.text-center {{ text-align: center !important; }}
.text-left {{ text-align: left !important; }}
.text-right {{ text-align: right !important; }}

.text-primary {{ color: var(--primary) !important; }}
.text-secondary {{ color: var(--secondary) !important; }}
.text-muted {{ color: var(--gray-600) !important; }}

.bg-primary {{ background-color: var(--primary) !important; }}
.bg-secondary {{ background-color: var(--secondary) !important; }}
.bg-light {{ background-color: var(--gray-50) !important; }}
.bg-dark {{ background-color: var(--gray-900) !important; }}

.img-fluid {{ max-width: 100%; height: auto; }}

.mt-1 {{ margin-top: var(--space-xs) !important; }}
.mt-2 {{ margin-top: var(--space-sm) !important; }}
.mt-3 {{ margin-top: var(--space-md) !important; }}
.mt-4 {{ margin-top: var(--space-lg) !important; }}
.mt-5 {{ margin-top: var(--space-xl) !important; }}

.mb-1 {{ margin-bottom: var(--space-xs) !important; }}
.mb-2 {{ margin-bottom: var(--space-sm) !important; }}
.mb-3 {{ margin-bottom: var(--space-md) !important; }}
.mb-4 {{ margin-bottom: var(--space-lg) !important; }}
.mb-5 {{ margin-bottom: var(--space-xl) !important; }}

.py-3 {{ padding-top: var(--space-md) !important; padding-bottom: var(--space-md) !important; }}
.py-4 {{ padding-top: var(--space-lg) !important; padding-bottom: var(--space-lg) !important; }}
.py-5 {{ padding-top: var(--space-xl) !important; padding-bottom: var(--space-xl) !important; }}

/* ==================== 响应式网格 ==================== */
.row {{
  display: flex;
  flex-wrap: wrap;
  margin: 0 calc(var(--space-md) * -1);
}}

.col {{
  flex: 1;
  padding: 0 var(--space-md);
}}

.col-12 {{ flex: 0 0 100%; max-width: 100%; }}
.col-md-6 {{ flex: 0 0 100%; max-width: 100%; }}
.col-md-4 {{ flex: 0 0 100%; max-width: 100%; }}
.col-md-3 {{ flex: 0 0 100%; max-width: 100%; }}

@media (min-width: 768px) {{
  .col-md-6 {{ flex: 0 0 50%; max-width: 50%; }}
  .col-md-4 {{ flex: 0 0 33.333333%; max-width: 33.333333%; }}
  .col-md-3 {{ flex: 0 0 25%; max-width: 25%; }}
}}

.g-4 > * {{ padding: var(--space-md); }}

{content}
"""

    try:
        # 确保父目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(css_template)
        return f"CSS文件创建成功: {file_path}"
    except Exception as e:
        raise RuntimeError(f"创建CSS文件失败: {str(e)}")



__all__ = ["create_css_file"]
