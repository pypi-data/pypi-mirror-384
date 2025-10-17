"""导航栏生成工具"""
from __future__ import annotations

import html
import os
import re
from pathlib import Path


def create_responsive_navbar(file_path: str, brand_name: str = "公司名称", nav_items: list = None, cta: dict | None = None, theme: dict | None = None):
    """创建响应式导航栏组件

    参数说明：
    - file_path: 目标HTML文件路径；若非 .html 则会创建为独立组件片段。
    - brand_name: 品牌名称（导航左侧）。
    - nav_items: 导航项列表。标准结构为：
      [{"name": "首页", "href": "#home", "active": true}]
      为增强容错，也兼容以下别名键：
        • 名称：name | text | title | label
        • 链接：href | url | link
      active 缺省时默认第一个为 True，其他为 False。
    - cta: 可选字典，用于自定义右侧按钮。可包含键：
      text / short_text / href / icon / style / size_class / extra_class / visible。
      当不给出或缺少字段时，会结合导航项自动推导合适的 CTA（如"联系我们""查看菜单"等）。
    - theme: 可选字典，用于自定义导航栏主题。可包含键：
      primary_color / secondary_color / text_color / bg_opacity / use_gradient / custom_class。
      例如：{"primary_color": "#8B4513", "text_color": "white", "use_gradient": false}
    """
    # 处理主题配置
    theme = theme or {}
    primary_color = theme.get("primary_color", "#0d6efd")
    secondary_color = theme.get("secondary_color", "#6610f2")
    text_color = theme.get("text_color", "white")
    bg_opacity = theme.get("bg_opacity", "0.95")
    use_gradient = theme.get("use_gradient", True)
    custom_class = theme.get("custom_class", "navbar-glass")

    # 根据主题生成导航栏背景样式
    if use_gradient:
        navbar_bg_style = f"background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);"
    else:
        # 如果primary_color是RGB格式，转换为rgba
        if primary_color.startswith("#"):
            # 简单的hex到rgba转换
            navbar_bg_style = f"background: {primary_color}; opacity: {bg_opacity};"
        elif primary_color.startswith("rgb"):
            # 将rgb转换为rgba
            navbar_bg_style = f"background: {primary_color.replace('rgb', 'rgba').replace(')', f', {bg_opacity})')};"
        else:
            navbar_bg_style = f"background: rgba({primary_color}, {bg_opacity});"

    navbar_bg_style += " backdrop-filter: blur(10px);"

    # 默认导航项
    if nav_items is None:
        nav_items = [
            {"name": "首页", "href": "#home", "active": True},
            {"name": "服务", "href": "#services", "active": False},
            {"name": "联系", "href": "#contact", "active": False}
        ]
    elif not nav_items:
        return "导航栏未生成：nav_items 为空，已跳过注入导航组件"

    # 归一化单个导航项，避免 KeyError
    def _normalize_item(raw: object, index: int) -> tuple[dict, bool]:
        explicit_active = False
        if not isinstance(raw, dict):
            return {"name": str(raw), "href": "#", "active": index == 0}, False
        name = (
            raw.get("name")
            or raw.get("text")
            or raw.get("title")
            or raw.get("label")
        )
        href = (
            raw.get("href")
            or raw.get("url")
            or raw.get("link")
        )
        explicit_active = "active" in raw
        active = raw.get("active")
        if not name:
            name = f"导航{index + 1}"
        if not href:
            # 尝试基于名称生成一个简易锚点（仅作为兜底）
            base = ''.join(ch.lower() if ch.isalnum() else '-' for ch in str(name))
            base = base.strip('-') or 'section'
            href = f"#{base}"
        if active is None:
            active = index == 0
        return {"name": name, "href": href, "active": bool(active)}, explicit_active

    normalized_items: list[dict] = []
    explicit_flags: list[bool] = []
    for i, item in enumerate(nav_items or []):
        normalized, explicit = _normalize_item(item, i)
        normalized_items.append(normalized)
        explicit_flags.append(explicit)

    # 基于当前文件自动高亮对应导航项（仅在未显式指定 active 时处理）
    current_page = os.path.basename(file_path).lower()
    if not current_page.endswith(".html"):
        current_page = ""

    highlighted = False
    for idx, item in enumerate(normalized_items):
        if explicit_flags[idx]:
            highlighted = highlighted or item.get("active", False)
            continue

        href = (item.get("href") or "").lower()
        match_current = False
        if current_page:
            if href.endswith(current_page):
                match_current = True
            elif current_page == "index.html" and href in {"index.html", "./", "#", "#home"}:
                match_current = True

        if match_current:
            item["active"] = True
            highlighted = True
        else:
            item["active"] = False

    if not highlighted and normalized_items:
        # 若仍未有激活项，默认第一个为 active
        normalized_items[0]["active"] = True

    # 生成导航项HTML
    nav_items_html = ""
    for item in normalized_items:
        active_class = " active" if item.get("active", False) else ""
        nav_items_html += (
            f'        <li class="nav-item"><a class="nav-link{active_class}" '
            f'href="{item["href"]}" style="color: {text_color};">{item["name"]}</a></li>\n'
        )

    # 品牌链接：优先跳转到第一个导航项（通常为首页），避免在子页上指向不存在的 #home
    brand_href = normalized_items[0]["href"] if normalized_items else "#home"

    def _find_item(keywords: tuple[str, ...]) -> dict | None:
        for item in normalized_items:
            name = (item.get("name") or "").lower()
            href = (item.get("href") or "").lower()
            if any(key in name for key in keywords) or any(key in href for key in keywords):
                return item
        return None

    def _derive_cta(raw_cta: dict | None) -> dict:
        # 根据主题决定CTA按钮的默认样式
        if use_gradient:
            style_default = (
                f"background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);"
                f" border: none; box-shadow: 0 10px 24px rgba({int(primary_color[1:3], 16)}, {int(primary_color[3:5], 16)}, {int(primary_color[5:7], 16)}, 0.35);"
                if primary_color.startswith("#") else
                "background: linear-gradient(135deg, #0d6efd 0%, #6610f2 100%);"
                " border: none; box-shadow: 0 10px 24px rgba(13, 110, 253, 0.35);"
            )
        else:
            # 使用单色按钮，稍微变亮作为按钮色
            style_default = (
                f"background: {secondary_color or primary_color};"
                f" border: 1px solid {primary_color}; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);"
            )

        base = {
            "text": "立即咨询",
            "short_text": "咨询",
            "href": (normalized_items[0]["href"] if normalized_items else "#home"),
            "icon": "fas fa-arrow-right",
            "style": style_default,
            "size_class": "btn-sm",
            "extra_class": "",
            "visible": True,
        }

        booking_item = _find_item(("预约", "预订", "booking", "reserve"))
        contact_item = _find_item(("联系", "contact", "call", "客服"))
        menu_item = _find_item(("menu", "菜单", "products", "服务"))
        about_item = _find_item(("about", "关于", "故事", "团队"))

        if booking_item:
            base.update({
                "text": "立即预约",
                "short_text": "预约",
                "href": booking_item.get("href", base["href"]),
                "icon": "fas fa-calendar-check",
            })
        elif contact_item:
            base.update({
                "text": "联系我们",
                "short_text": "联系",
                "href": contact_item.get("href", base["href"]),
                "icon": "fas fa-headset",
            })
        elif menu_item:
            base.update({
                "text": "查看菜单",
                "short_text": "菜单",
                "href": menu_item.get("href", base["href"]),
                "icon": "fas fa-book-open",
            })
        elif about_item:
            base.update({
                "text": "认识我们",
                "short_text": "了解",
                "href": about_item.get("href", base["href"]),
                "icon": "fas fa-user-friends",
            })

        if isinstance(raw_cta, dict):
            user_defined = {k: v for k, v in raw_cta.items() if v is not None}
            base.update(user_defined)

        return base

    def _render_cta(cfg: dict) -> str:
        if not cfg.get("visible", True):
            return ""
        text = cfg.get("text") or "立即咨询"
        short_text = cfg.get("short_text") or text
        href = cfg.get("href") or "#"
        icon_class = cfg.get("icon") or ""
        style = cfg.get("style") or (
            "background: linear-gradient(135deg, #0d6efd 0%, #6610f2 100%);"
            " border: none; box-shadow: 0 10px 24px rgba(13, 110, 253, 0.35);"
        )
        size_class = cfg.get("size_class") or "btn-sm"
        extra_class = cfg.get("extra_class") or ""
        classes = f"btn btn-gradient {size_class} rounded-pill px-3 text-white fw-bold"
        if extra_class:
            classes += f" {extra_class.strip()}"
        icon_html = f"<i class=\"{icon_class} me-1\"></i>" if icon_class else ""
        return (
            f"        <a class=\"{classes}\" href=\"{href}\" style=\"{style}\">\n"
            f"          {icon_html}<span class=\"d-none d-md-inline\">{text}</span>"
            f"<span class=\"d-md-none\">{short_text}</span>\n"
            f"        </a>\n"
        )

    cta_block = _render_cta(_derive_cta(cta))

    navbar_core = (
        f"<nav class=\"navbar navbar-expand-lg navbar-dark {custom_class}\" style=\"{navbar_bg_style}\">\n"
        f"  <div class=\"container-xxl\">\n"
        f"    <a class=\"navbar-brand d-flex align-items-center\" href=\"{brand_href}\" style=\"color: {text_color};\">\n"
        f"      <span class=\"me-2\">☕</span>{brand_name}\n"
        f"    </a>\n"
        f"    <button class=\"navbar-toggler border-0\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#navbarNav\" aria-controls=\"navbarNav\" aria-expanded=\"false\" aria-label=\"切换导航\">\n"
        f"      <span class=\"navbar-toggler-icon\"></span>\n"
        f"    </button>\n"
        f"    <div class=\"collapse navbar-collapse\" id=\"navbarNav\">\n"
        f"      <ul class=\"navbar-nav ms-auto\">\n"
        f"{nav_items_html}      </ul>\n"
        f"      <div class=\"d-flex align-items-center ms-3 gap-2\">\n"
        f"        <button class=\"theme-toggle-btn btn btn-outline-light btn-sm rounded-pill px-3\" type=\"button\" aria-label=\"切换主题\" data-action=\"toggle-theme\" style=\"border: 1px solid rgba(255,255,255,0.3); backdrop-filter: blur(10px); color: {text_color};\">\n"
        f"          <i class=\"fas fa-moon me-1\"></i><span class=\"d-none d-md-inline\">夜间</span>\n"
        f"        </button>\n"
        f"{cta_block}"
        f"      </div>\n"
        f"    </div>\n"
        f"  </div>\n"
        f"</nav>"
    )
    # 用标记包裹，便于重复调用时检测并替换，保证幂等
    navbar_html = "<!-- AI-Navbar: start -->\n" + navbar_core + "\n<!-- AI-Navbar: end -->"

    try:
        # 如果是HTML文件，直接插入导航栏
        if file_path.endswith('.html'):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 移除遗留的 script.js 引用，避免指向不存在的脚本
            content = re.sub(
                r"\s*<script[^>]*assets/js/script\.js[^>]*>\s*</script>",
                "",
                content,
                flags=re.I,
            )

            # 尝试清理页面顶部的“简易锚点列表导航”（ul>li>a href="#..."），避免出现两个导航
            try:
                low = content.lower()
                body_idx = low.find('<body')
                insert_start = 0
                if body_idx != -1:
                    gt = low.find('>', body_idx)
                    insert_start = gt + 1 if gt != -1 else 0
                # 仅在文首 4000 字符内查找，降低误删风险
                window_end = min(len(content), insert_start + 4000)
                head_slice = content[insert_start:window_end]

                ul_pattern = re.compile(r"<ul[^>]*>(?P<items>(?:\s*<li[^>]*>\s*<a[^>]*href=\s*['\"]#.+?['\"][^>]*>.*?</a>\s*</li>){3,}\s*)</ul>", re.I | re.S)
                candidates = list(ul_pattern.finditer(head_slice))
                for m in candidates:
                    items = m.group('items')
                    li_count = len(re.findall(r"<li\b", items, re.I))
                    anchor_count = len(re.findall(r"href=\s*['\"]#", items, re.I))
                    label_texts = [t.strip().lower() for t in re.findall(r">\s*([^<]{1,30})\s*</a>", items)]
                    common_labels = {"home", "products", "reviews", "contact", "about", "services", "案例", "产品", "联系", "关于", "首页", "服务"}
                    has_common = any(txt in common_labels for txt in label_texts)
                    # 需满足：至少3项内部锚点，且匹配常见导航标签或 ul 上 class 提示
                    ul_tag_open = head_slice[max(0, m.start()-200):m.end()]
                    class_hint = bool(re.search(r"class=\"[^\"]*(nav|menu|links)\b", ul_tag_open, re.I))
                    if li_count >= 3 and anchor_count >= 3 and (has_common or class_hint):
                        # 删除该 UL，避免重复导航
                        abs_start = insert_start + m.start()
                        abs_end = insert_start + m.end()
                        content = content[:abs_start] + content[abs_end:]
                        break
            except Exception:
                # 清理失败不影响主流程
                pass

            # 1) 已存在我们插入的导航，直接替换
            if "<!-- AI-Navbar: start -->" in content and "<!-- AI-Navbar: end -->" in content:
                content = re.sub(r"<!-- AI-Navbar: start -->.*?<!-- AI-Navbar: end -->", navbar_html, content, flags=re.S)
            else:
                # 2) 若存在任何带 .navbar 的 <nav>，替换第一个为我们的导航
                pattern = re.compile(r"<nav[^>]*class=\"[^\"]*navbar[^\"]*\"[^>]*>.*?</nav>", re.S | re.I)
                if pattern.search(content):
                    content = pattern.sub(navbar_html, content, count=1)
                else:
                    # 3) 否则在 <body...> 标签闭合后插入
                    lower = content.lower()
                    body_idx = lower.find('<body')
                    if body_idx != -1:
                        gt_idx = lower.find('>', body_idx)
                        if gt_idx != -1:
                            content = content[:gt_idx+1] + "\n    " + navbar_html + "\n" + content[gt_idx+1:]
                        else:
                            content = content.replace("<body>", f"<body>\n    {navbar_html}\n")
                    else:
                        # 没找到 body，兜底：前置插入
                        content = navbar_html + "\n" + content

            # 确保 Bootstrap 依赖存在（导航栏需要）
            bootstrap_css = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'
            bootstrap_js = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>'
            fontawesome_css = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'
            
            # 添加 Bootstrap CSS（如果不存在）
            if 'bootstrap' not in content.lower():
                if '</head>' in content:
                    # 在 </head> 前插入，但要在自定义 CSS 之前
                    if '<link rel="stylesheet" href="assets/css/style.css">' in content:
                        content = content.replace(
                            '<link rel="stylesheet" href="assets/css/style.css">',
                            f'{bootstrap_css}\n    {fontawesome_css}\n    <link rel="stylesheet" href="assets/css/style.css">'
                        )
                    else:
                        content = content.replace('</head>', f'    {bootstrap_css}\n    {fontawesome_css}\n</head>')
            
            # 添加 Bootstrap JS（如果不存在）
            if 'bootstrap.bundle' not in content.lower():
                if '</body>' in content:
                    # 在 </body> 前插入
                    if '<script src="assets/js/main.js"></script>' in content:
                        content = content.replace(
                            '<script src="assets/js/main.js"></script>',
                            f'{bootstrap_js}\n    <script src="assets/js/main.js"></script>'
                        )
                    else:
                        content = content.replace('</body>', f'    {bootstrap_js}\n</body>')
            
            # 确保导航锚点对应的区块存在
            id_pattern = re.compile(r'id\s*=\s*["\']([^"\']+)["\']', re.I)
            existing_ids = {m.group(1).strip().lower() for m in id_pattern.finditer(content)}
            missing_sections: list[str] = []
            for item in normalized_items:
                href = (item.get("href") or "").strip()
                if not href.startswith("#") or len(href) <= 1:
                    continue
                anchor = href[1:].strip()
                if not anchor:
                    continue
                if anchor.lower() in existing_ids:
                    continue
                heading = html.escape(item.get("name") or anchor)
                placeholder = (
                    f"\n    <section id=\"{anchor}\" class=\"section py-5 bg-light ai-nav-placeholder\">\n"
                    "      <div class=\"container text-center\">\n"
                    f"        <h2 class=\"h4 text-secondary mb-3\">{heading}</h2>\n"
                    "        <p class=\"text-muted\">此区块由导航自动生成，请替换为真实内容。</p>\n"
                    "      </div>\n"
                    "    </section>\n"
                )
                missing_sections.append(placeholder)
                existing_ids.add(anchor.lower())

            if missing_sections:
                insertion = "".join(missing_sections)
                body_close = re.search(r"</body>", content, re.I)
                if body_close:
                    idx = body_close.start()
                    content = content[:idx] + insertion + "\n" + content[idx:]
                else:
                    content = content + insertion

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"响应式导航栏已添加到: {file_path}"
        else:
            # 创建独立的导航栏组件文件
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(navbar_html)
            return f"导航栏组件文件已创建: {file_path}"

    except Exception as e:
        raise RuntimeError(f"创建导航栏失败: {str(e)}")



__all__ = ["create_responsive_navbar"]
