"""图片生成与注入工具"""
from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path


def fetch_generated_images(
    project_path: str,
    provider: str = "pollinations",
    prompts: list | str | None = None,
    count: int = 1,
    size: str = "1200x800",
    seed: str | int | None = None,
    save: bool = False,
    subdir: str = "assets/images",
    prefix: str = "img",
):
    """获取生成图片（支持 Pollinations、DiceBear、RoboHash）

    Args:
        project_path: 项目根目录（用于保存到 assets/images）。
        provider: 图片提供方：pollinations | dicebear | robohash。
        prompts: 提示词/种子列表；字符串时支持 JSON 或逗号分隔。
        count: 数量；当 prompts 为空时，根据 count 生成占位提示。
        size: 像素尺寸，例如 "1200x800"。
        seed: 基础种子；对 pollinations 可与提示组合、对 dicebear 为 seed、对 robohash 为文本的一部分。
        save: 是否下载到本地 assets/images 目录。
        subdir: 保存子目录，默认 assets/images。
        prefix: 文件名前缀。

    Returns:
        字符串：列出生成的图片URL与本地保存路径（如有）。
    """
    try:
        # 解析尺寸
        try:
            width_px, height_px = [int(x) for x in str(size).lower().replace("*", "x").split("x")[:2]]
        except Exception:
            width_px, height_px = 1200, 800

        # 归一化 prompts
        if prompts is None:
            prompts = []
        if isinstance(prompts, str):
            s = prompts.strip()
            if s.startswith("["):
                try:
                    prompts = json.loads(s)
                except Exception:
                    prompts = [p.strip() for p in s.split(",") if p.strip()]
            else:
                prompts = [p.strip() for p in s.split(",") if p.strip()]
        if not isinstance(prompts, list):
            prompts = [str(prompts)]
        if not prompts:
            # 默认主题占位
            base = provider or "image"
            prompts = [f"{base}-{i+1}" for i in range(max(1, int(count)))]

        results = []
        base_path = Path(project_path)
        save_dir = base_path / subdir
        if save:
            save_dir.mkdir(parents=True, exist_ok=True)

        for i, prompt in enumerate(prompts):
            prompt_str = str(prompt)
            item_seed = str(seed) if seed is not None else str(i + 1)
            url = ""
            ext = "jpg"

            if provider.lower() in ("pollinations", "polls", "poll"):  # 文生图
                q = urllib.parse.quote(prompt_str)
                url = (
                    f"https://image.pollinations.ai/prompt/{q}?nologo=true&seed={item_seed}&width={width_px}&height={height_px}"
                )
                ext = "jpg"

            elif provider.lower() in ("dicebear", "avatar", "bottts"):  # 矢量头像
                # 采用 bottts 风格
                seed_val = urllib.parse.quote(prompt_str or item_seed)
                url = f"https://api.dicebear.com/7.x/bottts/svg?seed={seed_val}"
                ext = "svg"

            elif provider.lower() in ("robohash", "robo", "cats"):  # PNG 头像
                text = urllib.parse.quote(prompt_str or item_seed)
                url = f"https://robohash.org/{text}.png?set=set4&bgset=bg1&size={width_px}x{height_px}"
                ext = "png"
            else:
                raise ValueError("不支持的 provider，可用：pollinations | dicebear | robohash")

            saved_path = None
            if save:
                try:
                    filename = f"{prefix}-{provider}-{i+1}.{ext}"
                    out_path = save_dir / filename
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        data = resp.read()
                    with open(out_path, "wb") as f:
                        f.write(data)
                    saved_path = str(out_path)
                except Exception:
                    # 网络不可用或失败时仅返回URL
                    saved_path = None

            results.append({
                "provider": provider,
                "prompt": prompt_str,
                "url": url,
                "saved_path": saved_path,
            })

        # 组装结果
        lines = [
            f"图片生成完成（provider={provider}, save={'yes' if save else 'no'}）: {len(results)} 张",
        ]
        for r in results:
            loc = r["saved_path"] or "(未保存)"
            lines.append(f"- {r['prompt']}: {r['url']} -> {loc}")
        return "\n".join(lines)

    except Exception as e:
        raise RuntimeError(f"获取图片失败: {str(e)}")


def inject_images(
    file_path: str,
    provider: str = "pollinations",
    topics: list | str | None = None,
    size: str = "1200x800",
    seed: str | int | None = None,
    save: bool = False,
    subdir: str = "assets/images",
    prefix: str = "img",
) -> str:
    """将生成图片注入到现有HTML中。

    行为：
    - 识别 data-bg-topic 用于为容器（如 header.hero）设置背景图。
    - 识别 <img data-topic> 占位并填充 src、alt、loading。
    - 识别 <svg data-topic> 占位并整体替换为 <img ...> 注入。
    - 若页面没有任何占位，但存在 hero/header/section（类名含 hero|banner|masthead|showcase），则使用 topics 的第一个为背景。

    Args:
        file_path: 目标HTML文件
        provider: pollinations | dicebear | robohash
        topics: 主题/提示词列表；若省略且页面含占位则按占位抓取
        size: 尺寸字符串，如 1200x800
        seed: 种子
        save: 是否下载到本地 assets/images
        subdir: 保存目录（相对 HTML 所在目录）
        prefix: 保存文件名前缀
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析尺寸
        try:
            width_px, height_px = [int(x) for x in str(size).lower().replace("*", "x").split("x")[:2]]
        except Exception:
            width_px, height_px = 1200, 800

        # 收集页面占位符
        bg_matches = list(re.finditer(r"<([a-zA-Z0-9]+)([^>]*?)\\sdata-bg-topic=\"([^\"]+)\"([^>]*)>", content))
        img_matches = list(re.finditer(r"<img([^>]*?)\\sdata-topic=\"([^\"]+)\"([^>]*)>", content))
        # 新增：识别 <svg data-topic> ... </svg> 占位
        svg_matches = list(re.finditer(r"<svg([^>]*?)\\sdata-topic=\"([^\"]+)\"([^>]*)>.*?</svg>", content, re.I | re.S))

        # 将 topics 统一为列表；若缺省或为 "<auto>"，则基于页面文本与路径自动生成
        page_topics = []
        page_topics += [m.group(3).strip() for m in bg_matches]
        page_topics += [m.group(2).strip() for m in img_matches]
        page_topics += [m.group(2).strip() for m in svg_matches]

        def _to_list(val):
            if val is None:
                return []
            if isinstance(val, str):
                s = val.strip()
                return json.loads(s) if s.startswith("[") else [t.strip() for t in s.split(",") if t.strip()]
            if isinstance(val, list):
                return val
            return [str(val)]

        topics = _to_list(topics)

        def _extract_text(html: str) -> str:
            # 抽取 title/h1/h2 文本作为语义参考
            text = []
            for pat in [r"<title[^>]*>(.*?)</title>", r"<h1[^>]*>(.*?)</h1>", r"<h2[^>]*>(.*?)</h2>"]:
                for m in re.finditer(pat, html, re.I | re.S):
                    t = re.sub(r"<[^>]+>", " ", m.group(1))
                    text.append(t)
            head = " ".join(text)
            return re.sub(r"\s+", " ", head).strip().lower()

        def _guess_topics(html: str, path: str, n: int = 3) -> list:
            base = _extract_text(html)
            base += " " + os.path.basename(path).replace('-', ' ').lower()
            # 关键词 → 主题基
            mapping = [
                (("phone", "mobile", "smartphone", "iphone", "android"), [
                    "modern smartphone store interior, depth of field, soft lighting",
                    "close-up product photo of latest smartphone on gradient background",
                    "lifestyle shot using smartphone in cafe daylight"
                ]),
                (("cafe", "coffee", "latte", "espresso", "barista"), [
                    "coffee shop interior hero, warm light, depth of field",
                    "close-up latte art on wooden table, high detail",
                    "lifestyle shot people enjoying coffee"
                ]),
                (("restaurant", "food", "menu", "dishes", "burger", "pizza"), [
                    "restaurant hero background, cozy interior, bokeh",
                    "close-up gourmet dish, food photography",
                    "lifestyle people dining, warm ambience"
                ]),
                (("saas", "software", "startup", "app", "tech"), [
                    "abstract tech hero background, gradient, 3d shapes",
                    "dashboard ui on laptop close-up, product shot",
                    "team collaboration lifestyle office scene"
                ]),
                (("education", "course", "school", "study"), [
                    "education hero background, campus or classroom light",
                    "notebook and laptop study flat lay",
                    "students studying lifestyle"
                ]),
            ]
            for keys, topics_tpl in mapping:
                if any(k in base for k in keys):
                    return topics_tpl[:n]
            # 兜底：通用现代风格
            return [
                "modern gradient abstract background, soft shapes",
                "product close-up on neutral background",
                "lifestyle people using product"
            ][:n]

        if not topics or topics == ["<auto>"]:
            # 若页面已有占位主题，优先使用占位；否则基于文本猜测
            topics = page_topics if page_topics else _guess_topics(content, file_path, 3)

        # 辅助：构造 URL + 可选保存（支持直接传入外链URL）
        def build_url(topic: str, idx: int) -> tuple[str, str | None, str]:
            prov = provider.lower().strip()
            topic_q = urllib.parse.quote_plus(topic)
            if prov in ("pollinations", "pollination", "image", "ai"):
                url = f"https://image.pollinations.ai/prompt/{topic_q}?width={width_px}&height={height_px}"
                ext = "jpg"
            elif prov in ("dicebear", "avatar", "bottts"):
                q = urllib.parse.quote(topic)
                url = f"https://api.dicebear.com/7.x/bottts/svg?seed={q}"
                ext = "svg"
            elif prov in ("robohash", "robo", "cats"):
                q = urllib.parse.quote(topic)
                url = f"https://robohash.org/{q}.png?set=set4&bgset=bg1&size={width_px}x{height_px}"
                ext = "png"
            else:
                raise ValueError("不支持的 provider")

            saved_path = None
            if save:
                try:
                    root = Path(file_path).parent
                    out_dir = root / subdir
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"{prefix}-{idx+1}.{ext}"
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        data = resp.read()
                    with open(out_file, "wb") as fo:
                        fo.write(data)
                    saved_path = str(out_file)
                except Exception:
                    saved_path = None
            return url, saved_path, ext

        def build_placeholder(topic: str) -> str:
            plain = re.sub(r"\s+", " ", topic).strip()
            plain = plain[:24] if plain else "Placeholder"
            encoded = urllib.parse.quote_plus(plain)
            return f"https://placehold.co/{width_px}x{height_px}/EEE/31343C?text={encoded}"


        # 背景设置：更新 style 中的 background-image
        def set_bg(tag_html: str, url: str) -> str:
            style_re = re.compile(r"style=\"([^\"]*)\"")
            css = f"background-image:url('{url}');background-size:cover;background-position:center;background-repeat:no-repeat;"
            if style_re.search(tag_html):
                def _repl(m):
                    val = m.group(1)
                    # 去掉原有 background-image
                    val = re.sub(r"background-image\s*:[^;]*;?", "", val)
                    val = (val + (";" if val and not val.strip().endswith(";") else "") + css).strip(";")
                    return f"style=\"{val}\""
                tag_html = style_re.sub(_repl, tag_html, count=1)
            else:
                tag_html = tag_html.replace(">", f" style=\"{css}\">")
            # 标记属性，便于下次识别
            if "data-ai-image=\"bg\"" not in tag_html:
                tag_html = tag_html.replace(">", " data-ai-image=\"bg\">")
            return tag_html

        # img 占位设置/替换
        def set_img(tag_html: str, url: str, topic: str, placeholder_url: str, remote_url: str | None = None) -> str:
            # 解析原有属性
            tag = tag_html.strip()
            self_closing = tag.endswith('/>')
            body_match = re.match(r'<img\s*(.*?)(/?>)$', tag_html, re.I | re.S)
            original_attrs = body_match.group(1) if body_match else ''
            terminator = body_match.group(2) if body_match else ('/>' if tag_html.strip().endswith('/>') else '>')

            attr_pattern = re.compile(r'([a-zA-Z_:][\w:.-]*)\s*=\s*"([^"]*)"')
            attrs = OrderedDict()
            order = []
            for name, value in attr_pattern.findall(original_attrs):
                lower = name.lower()
                if lower not in order:
                    order.append(lower)
                attrs[lower] = [name, value]

            def set_attr(name: str, value: str):
                lower = name.lower()
                if lower in attrs:
                    attrs[lower][1] = value
                else:
                    attrs[lower] = [name, value]
                    order.append(lower)

            def get_attr(lower_name: str) -> str | None:
                item = attrs.get(lower_name)
                return item[1] if item else None

            set_attr('src', url)
            set_attr('alt', topic or '网站图片')
            set_attr('loading', 'lazy')

            classes = get_attr('class') or ''
            class_parts = [c for c in classes.split() if c]
            if 'img-fluid' not in class_parts:
                class_parts.append('img-fluid')
            set_attr('class', ' '.join(class_parts))

            set_attr('data-ai-image', 'img')
            if topic:
                set_attr('data-topic', attrs.get('data-topic', ['data-topic', topic])[1])
            set_attr('data-placeholder', placeholder_url)
            if remote_url:
                set_attr('data-remote-src', remote_url)
            escaped_placeholder = html.escape(placeholder_url, quote=True)
            set_attr('onerror', f"this.onerror=null;this.src='{escaped_placeholder}'")

            rebuilt = ['<img']
            for lower in order:
                name, value = attrs[lower]
                escaped_val = html.escape(value, quote=True)
                rebuilt.append(f" {name}={chr(34)}{escaped_val}{chr(34)}")
            rebuilt.append(f"{terminator if terminator else '>'}")
            return ''.join(rebuilt)

        replacements = 0
        hero_used = False
        # 1) 背景占位处理
        for idx, m in enumerate(bg_matches):
            topic = m.group(3).strip()
            url, saved, _ = build_url(topic, idx)
            placeholder_url = build_placeholder(topic)
            target = saved or url
            if save and not saved:
                target = placeholder_url
            old = m.group(0)
            new = set_bg(old, target)
            if url != target:
                escaped = html.escape(url, quote=True)
                if 'data-remote-bg' not in new:
                    new = new.replace('>', f" data-remote-bg=\"{escaped}\">", 1)
            content = content.replace(old, new, 1)
            replacements += 1
            hero_used = True


        # 2) img 占位处理
        for jdx, m in enumerate(img_matches):
            topic = m.group(2).strip()
            url, saved, _ = build_url(topic, len(bg_matches) + jdx)
            placeholder_url = build_placeholder(topic)
            target = saved or url
            if save and not saved:
                target = placeholder_url
            old = m.group(0)
            new = set_img(old, target, topic, placeholder_url, url)
            content = content.replace(old, new, 1)
            replacements += 1


        # 2b) svg 占位处理：整体替换为 <img ...>
        if svg_matches:
            offset = 0
            for sdx, m in enumerate(svg_matches):
                topic = m.group(2).strip()
                url, saved, _ = build_url(topic, len(bg_matches) + len(img_matches) + sdx)
                placeholder_url = build_placeholder(topic)
                target = saved or url
                if save and not saved:
                    target = placeholder_url
                img_tag = set_img(
                    f"<img data-topic=\"{topic}\" class=\"img-fluid mb-3 rounded shadow-sm\" />",
                    target,
                    topic,
                    placeholder_url,
                    url,
                )
                old = m.group(0)
                start_pos = m.start() + offset
                end_pos = m.end() + offset
                content = content[:start_pos] + img_tag + content[end_pos:]
                offset += len(img_tag) - (end_pos - start_pos)
                replacements += 1


        # 3) 无占位但存在 hero/header：使用 topics 第一个设置背景
        if replacements == 0 and topics:
            # 扩展：支持 header/section，且类名包含 hero|banner|masthead|showcase 之一
            m = re.search(r"<(header|section)[^>]*(id=\"home\"|class=\"[^\"]*(hero|banner|masthead|showcase)[^\"]*\")[^>]*>", content, re.I)
            if m:
                topic = topics[0]
                url, saved, _ = build_url(topic, 0)
                placeholder_url = build_placeholder(topic)
                target = saved or url
                if save and not saved:
                    target = placeholder_url
                old = m.group(0)
                new = set_bg(old, target)
                if url != target:
                    escaped = html.escape(url, quote=True)
                    if 'data-remote-bg' not in new:
                        new = new.replace('>', f" data-remote-bg=\"{escaped}\">", 1)
                if 'data-bg-topic="' not in new:
                    new = new.replace('>', f' data-bg-topic="{topic}">', 1)
                content = content.replace(old, new, 1)
                replacements += 1
                hero_used = True


        # 4) 若页面没有 <img data-topic> 占位，但存在卡片容器，则自动插入到卡片顶部
        #    使用 topics（或页面收集的），按顺序填充
        if not img_matches:
            # 扩展：识别更多容器与类名（div/section/article + feature-card|card|product-card|device-card|item-card|phone-card）
            wrappers = list(re.finditer(r"(<(div|section|article)[^>]*class=\"[^\"]*(feature-card|card|product-card|device-card|item-card|phone-card)[^\"]*\"[^>]*>)", content, re.I))
            if wrappers:
                start_idx = 1 if hero_used else 0
                # 合并 topics & 默认占位
                fill_topics = topics[:] if topics else []
                # 逐个卡片插入
                inserted = 0
                offset = 0
                for wrapper_idx, wrapper_match in enumerate(wrappers):
                    class_match = re.search(r'class=\"([^\"]+)\"', wrapper_match.group(0), re.I)
                    if class_match:
                        tokens = {tok.strip().lower() for tok in class_match.group(1).split() if tok.strip()}
                        if tokens & {"card-body", "card-text", "card-footer", "card-header"}:
                            continue
                        if not tokens & {"card", "feature-card", "product-card", "device-card", "item-card", "phone-card"}:
                            continue
                    # 查看该卡片块内是否已有 <img>（向后检查最多1200字符）
                    look_ahead = content[wrapper_match.end()+offset:wrapper_match.end()+offset+1200]
                    if re.search(r"<img", look_ahead, re.I):
                        continue
                    if "${" in look_ahead:
                        continue
                    # 选择主题
                    t_index = start_idx + inserted
                    topic = (fill_topics[t_index] if t_index < len(fill_topics) else f"image-{wrapper_idx+1}")
                    url, saved, _ = build_url(topic, t_index)
                    placeholder_url = build_placeholder(topic)
                    target = saved or url
                    if save and not saved:
                        target = placeholder_url
                    img_tag = set_img(
                        f"<img data-topic=\"{topic}\" class=\"img-fluid mb-3 rounded shadow-sm\" />",
                        target,
                        topic,
                        placeholder_url,
                        url,
                    )
                    insert_pos = wrapper_match.end() + offset
                    injection = "\n                " + img_tag
                    content = content[:insert_pos] + injection + content[insert_pos:]
                    offset += len(injection)
                    inserted += 1
                    replacements += 1

            # 额外兜底：总是尝试 product-grid（若存在且内部尚无 <img>）
            grid_m = re.search(r"(<div[^>]*(?:id=(?:\"|')product-grid(?:\"|')|class=(?:\"|')[^\"']*\bproduct-grid\b[^\"']*(?:\"|'))[^>]*>)", content, re.I)
            if grid_m and (topics or page_topics):
                # 仅当容器内部尚无 <img> 时插入（向前窥视一段内容判断）
                peek = content[grid_m.end():grid_m.end()+1200]
                if not re.search(r"<img\b", peek, re.I):
                    start_idx = 1 if hero_used else 0
                    fill_topics = topics[:] if topics else page_topics[:]

                    def detect_brand(t: str) -> str:
                        s = t.lower()
                        for key in [
                            ("apple", "apple"), ("iphone", "apple"),
                            ("samsung", "samsung"), ("galaxy", "samsung"),
                            ("google", "google"), ("pixel", "google"),
                            ("xiaomi", "xiaomi"), ("mi ", "xiaomi"), ("redmi", "xiaomi"),
                            ("huawei", "huawei"), ("mate", "huawei"), ("p60", "huawei"),
                            ("oneplus", "oneplus"), ("oppo", "oppo"), ("vivo", "vivo"), ("honor", "honor")
                        ]:
                            if key[0] in s:
                                return key[1]
                        return "other"

                    price_table = [4699, 5199, 5799, 6299, 6899, 7399, 7999, 8599, 9199]

                    cards = []
                    for i, topic in enumerate(fill_topics[start_idx:], start=start_idx):
                        url, saved, _ = build_url(topic, i)
                        target = saved or url
                        brand = detect_brand(topic)
                        price = price_table[(i - start_idx) % len(price_table)]
                        title = topic.split(",")[0][:80]
                        card_html = (
                            f"\n          <div class=\"card\" data-brand=\"{brand}\" data-price=\"{price}\">\n"
                            f"            <img data-ai-image=\"img\" data-topic=\"{topic}\" class=\"img-fluid mb-3 rounded shadow-sm\" loading=\"lazy\" alt=\"{topic}\" src=\"{target}\">\n"
                            f"            <h3 style=\"font-size:1.125rem; margin-bottom:0.5rem;\">{title}</h3>\n"
                            f"            <div style=\"display:flex; align-items:center; justify-content:space-between;\">\n"
                            f"              <span style=\"font-weight:700; color:#111827;\">¥{price}</span>\n"
                            f"              <a href=\"#\" class=\"btn btn-primary\">立即购买</a>\n"
                            f"            </div>\n"
                            f"          </div>"
                        )
                        cards.append(card_html)
                        replacements += 1

                    cards_html = "\n".join(cards) + "\n"
                    insert_pos = grid_m.end(1)
                    content = content[:insert_pos] + cards_html + content[insert_pos:]

        # 5) 清理指向不存在本地文件的图片，自动切换为在线占位
        missing_pattern = re.compile(r"<img([^>]*?)src=\"([^\"]+)\"([^>]*)>", re.I | re.S)
        search_offset = 0
        missing_counter = 0
        base_dir = Path(file_path).parent

        while True:
            m = missing_pattern.search(content, search_offset)
            if not m:
                break
            before, src, after = m.groups()
            src_stripped = src.strip()
            lower_src = src_stripped.lower()
            if lower_src.startswith(('http://', 'https://', 'data:')):
                search_offset = m.end()
                continue

            candidate_path = (base_dir / src_stripped).resolve()
            if candidate_path.exists():
                search_offset = m.end()
                continue

            attr_pattern_local = re.compile(r'([a-zA-Z_:][\w:.-]*)\s*=\s*"([^"]*)"')
            attrs_local = {name.lower(): value for name, value in attr_pattern_local.findall(before + after)}
            topic_source = attrs_local.get('data-topic') or attrs_local.get('alt') or Path(src_stripped).stem or 'image'
            topic_source = re.sub(r"\s+", " ", topic_source).strip()
            topic = topic_source or "image"

            inject_idx = len(bg_matches) + len(img_matches) + len(svg_matches) + missing_counter
            url, saved, _ = build_url(topic, inject_idx)
            placeholder_url = build_placeholder(topic)
            target = saved or url
            if save and not saved:
                target = placeholder_url

            original_tag = m.group(0)
            new_tag = set_img(original_tag, target, topic, placeholder_url, url)
            content = content[:m.start()] + new_tag + content[m.end():]
            search_offset = m.start() + len(new_tag)
            replacements += 1
            missing_counter += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"已注入图片: {replacements} 处（provider={provider}, save={'yes' if save else 'no'}）"

    except Exception as e:
        raise RuntimeError(f"注入图片失败: {str(e)}")



__all__ = ["fetch_generated_images", "inject_images"]
