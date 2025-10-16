"""修复后的图片生成与注入工具"""
from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path


def inject_images_fixed(
    file_path: str,
    provider: str = "pollinations",
    topics: list | str | None = None,
    size: str = "800x600",
    seed: str | int | None = None,
    save: bool = True,
    subdir: str = "assets/images",
    prefix: str = "bg",
) -> str:
    """修复版本的图片注入函数

    专门修复原版本中的以下问题：
    1. 占位符URL损坏
    2. 重复的img标签
    3. 图片下载失败
    4. HTML结构混乱
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析尺寸
        try:
            w, h = [int(x) for x in str(size).lower().replace("*", "x").split("x")[:2]]
        except Exception:
            w, h = 800, 600

        # 统一处理topics
        if topics is None:
            topics = []
        elif isinstance(topics, str):
            if topics.startswith("["):
                try:
                    topics = json.loads(topics)
                except Exception:
                    topics = [t.strip() for t in topics.split(",") if t.strip()]
            else:
                topics = [t.strip() for t in topics.split(",") if t.strip()]

        # 如果没有提供topics，使用默认的运势相关主题
        if not topics:
            topics = [
                "scorpio constellation night sky stars",
                "mystic tarot cards purple background",
                "golden astrology symbols",
                "crystal ball fortune telling",
                "zodiac wheel cosmic background"
            ]

        def build_url(topic: str, idx: int) -> tuple[str, str | None]:
            """构建图片URL并可选下载"""
            # 清理topic，避免包含HTML或特殊字符
            clean_topic = re.sub(r'[<>"\']', '', str(topic)).strip()
            clean_topic = clean_topic[:50]  # 限制长度

            if not clean_topic:
                clean_topic = f"image-{idx + 1}"

            topic_encoded = urllib.parse.quote_plus(clean_topic)

            if provider.lower() in ("pollinations", "poll"):
                url = f"https://image.pollinations.ai/prompt/{topic_encoded}?width={w}&height={h}&seed={seed or idx}"
                ext = "jpg"
            elif provider.lower() in ("dicebear", "avatar"):
                url = f"https://api.dicebear.com/7.x/bottts/svg?seed={topic_encoded}"
                ext = "svg"
            elif provider.lower() in ("robohash", "robo"):
                url = f"https://robohash.org/{topic_encoded}.png?size={w}x{h}"
                ext = "png"
            else:
                # 默认使用pollinations
                url = f"https://image.pollinations.ai/prompt/{topic_encoded}?width={w}&height={h}&seed={seed or idx}"
                ext = "jpg"

            saved_path = None
            if save:
                try:
                    root = Path(file_path).parent
                    out_dir = root / subdir
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"{prefix}-{idx + 1}.{ext}"

                    # 下载图片
                    with urllib.request.urlopen(url, timeout=15) as resp:
                        data = resp.read()
                    with open(out_file, "wb") as fo:
                        fo.write(data)
                    saved_path = str(out_file)
                except Exception as e:
                    print(f"下载图片失败: {e}")
                    saved_path = None

            return url, saved_path

        def build_clean_placeholder(topic: str, idx: int) -> str:
            """构建干净的占位符URL"""
            clean_topic = re.sub(r'[<>"\']', '', str(topic)).strip()
            clean_topic = clean_topic[:20] if clean_topic else f"image-{idx + 1}"
            encoded = urllib.parse.quote_plus(clean_topic)
            return f"https://placehold.co/{w}x{h}/444/fff?text={encoded}"

        # 清理现有的损坏图片标签
        # 移除所有包含损坏URL的img标签
        content = re.sub(r'<img[^>]*?placehold\.co/&lt;re\.Match[^>]*?>', '', content, flags=re.IGNORECASE | re.DOTALL)

        # 移除重复的空img标签
        content = re.sub(r'<img[^>]*?data-topic="image-\d+"[^>]*?>\s*', '', content, flags=re.IGNORECASE)

        # 寻找需要插入图片的位置
        # 1. 首先处理hero背景图
        hero_match = re.search(r'(<section[^>]*?class="[^"]*hero-section[^"]*"[^>]*>)', content, re.IGNORECASE)
        if hero_match and topics:
            url, saved = build_url(topics[0], 0)
            target_url = saved or url
            old_section = hero_match.group(1)

            # 更新背景图片
            bg_style = f"background-image: url('{target_url}'); background-size: cover; background-position: center; background-repeat: no-repeat;"

            if 'style=' in old_section:
                new_section = re.sub(r'style="([^"]*)"', lambda m: f'style="{m.group(1)}; {bg_style}"', old_section)
            else:
                new_section = old_section.replace('>', f' style="{bg_style}">')

            content = content.replace(old_section, new_section)

        # 2. 为每个卡片添加图片
        card_pattern = r'(<div[^>]*?class="[^"]*card[^"]*"[^>]*>)\s*(<div[^>]*?class="[^"]*card-body[^"]*"[^>]*>)'
        cards = list(re.finditer(card_pattern, content, re.IGNORECASE))

        offset = 0
        for i, match in enumerate(cards):
            if i + 1 < len(topics):
                topic = topics[i + 1]
            else:
                topic = f"mystical fortune symbol {i + 1}"

            url, saved = build_url(topic, i + 1)
            target_url = saved or url
            placeholder = build_clean_placeholder(topic, i + 1)

            # 创建图片标签
            img_tag = f'''<img src="{target_url}" alt="{topic}" class="card-img-top" style="height: 200px; object-fit: cover;" loading="lazy" onerror="this.src='{placeholder}'">'''

            # 插入到card-body之前
            insert_pos = match.end(1) + offset
            content = content[:insert_pos] + '\n        ' + img_tag + '\n        ' + content[insert_pos:]
            offset += len(img_tag) + 10  # 考虑换行和缩进

        # 保存修复后的文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"图片注入完成: 处理了 {len(cards) + 1} 个位置 (hero + {len(cards)} 张卡片图)"

    except Exception as e:
        return f"图片注入失败: {str(e)}"


if __name__ == "__main__":
    # 测试函数
    test_file = "/Users/fengjinchao/Desktop/2/html/scorpio-daily-fortune/index.html"
    result = inject_images_fixed(
        test_file,
        provider="pollinations",
        topics=[
            "scorpio constellation night sky stars mystical",
            "love heart tarot cards romantic fortune",
            "business career success symbols gold",
            "money coins financial luck prosperity",
            "lucky colors yellow golden sunshine",
            "lucky numbers 2 mystical numerology",
            "compass north direction feng shui",
            "clock time 18:00 evening golden hour"
        ],
        size="800x600",
        save=True,
        subdir="assets/images",
        prefix="scorpio"
    )
    print(result)