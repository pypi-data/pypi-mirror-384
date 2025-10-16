"""简单网页模板工具 - 无预设内容，纯净样式"""
from __future__ import annotations

from pathlib import Path


def create_simple_html_file(
    file_path: str,
    title: str = "新页面",
    content: str = "",
    style: str = "clean"
) -> str:
    """创建简单HTML文件，无预设内容，只有基础结构"""

    # 如果没有提供内容，创建基础结构
    if not content.strip():
        content = f"""    <header>
        <h1>{title}</h1>
        <nav>
            <a href="#home">首页</a>
            <a href="#about">关于</a>
            <a href="#contact">联系</a>
        </nav>
    </header>

    <main>
        <section id="home">
            <h2>欢迎访问</h2>
            <p>这里是页面的主要内容区域。</p>
        </section>

        <section id="about">
            <h2>关于我们</h2>
            <p>在这里介绍您的内容。</p>
        </section>

        <section id="contact">
            <h2>联系方式</h2>
            <p>邮箱：your-email@example.com</p>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 {title}. 保留所有权利。</p>
    </footer>"""

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="assets/css/{style}.css">
</head>
<body>
{content}
</body>
</html>"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        return f"简单HTML文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建HTML文件失败: {str(exc)}")


def create_blank_html_file(file_path: str, title: str = "空白页面") -> str:
    """创建完全空白的HTML文件，只有基础结构"""

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="assets/css/clean.css">
</head>
<body>
    <h1>{title}</h1>
    <p>开始编写您的内容...</p>
</body>
</html>"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        return f"空白HTML文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建HTML文件失败: {str(exc)}")


def create_landing_page(file_path: str, title: str = "着陆页", description: str = "") -> str:
    """创建简单的着陆页"""

    desc = description or "这是一个简洁的着陆页面"

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="assets/css/landing.css">
</head>
<body>
    <div class="container">
        <header class="hero">
            <h1>{title}</h1>
            <p class="subtitle">{desc}</p>
            <button class="cta-button">开始使用</button>
        </header>

        <section class="features">
            <div class="feature">
                <h3>特点一</h3>
                <p>描述第一个特点</p>
            </div>
            <div class="feature">
                <h3>特点二</h3>
                <p>描述第二个特点</p>
            </div>
            <div class="feature">
                <h3>特点三</h3>
                <p>描述第三个特点</p>
            </div>
        </section>

        <footer>
            <p>联系我们：contact@example.com</p>
        </footer>
    </div>
</body>
</html>"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        return f"着陆页创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建着陆页失败: {str(exc)}")


def create_blog_page(file_path: str, title: str = "我的博客") -> str:
    """创建简单的博客页面"""

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="assets/css/blog.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <nav>
                <a href="#home">首页</a>
                <a href="#posts">文章</a>
                <a href="#about">关于</a>
            </nav>
        </header>

        <main>
            <article class="post">
                <h2>第一篇文章标题</h2>
                <p class="meta">发布时间：2024年1月1日</p>
                <p>这里是文章的内容。您可以在这里分享您的想法、经验或故事。</p>
            </article>

            <article class="post">
                <h2>第二篇文章标题</h2>
                <p class="meta">发布时间：2024年1月2日</p>
                <p>另一篇文章的内容。继续添加更多有趣的内容。</p>
            </article>
        </main>

        <aside class="sidebar">
            <div class="widget">
                <h3>关于作者</h3>
                <p>在这里介绍一下您自己。</p>
            </div>

            <div class="widget">
                <h3>最近文章</h3>
                <ul>
                    <li><a href="#">文章标题一</a></li>
                    <li><a href="#">文章标题二</a></li>
                    <li><a href="#">文章标题三</a></li>
                </ul>
            </div>
        </aside>

        <footer>
            <p>&copy; 2024 {title}. 保留所有权利。</p>
        </footer>
    </div>
</body>
</html>"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        return f"博客页面创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建博客页面失败: {str(exc)}")


__all__ = [
    "create_simple_html_file",
    "create_blank_html_file",
    "create_landing_page",
    "create_blog_page"
]