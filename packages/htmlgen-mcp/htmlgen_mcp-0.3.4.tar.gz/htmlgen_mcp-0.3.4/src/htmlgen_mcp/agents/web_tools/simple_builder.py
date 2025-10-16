"""简单网页工具 - 集成函数"""
from __future__ import annotations

from pathlib import Path
from .simple_templates import create_simple_html_file, create_blank_html_file, create_landing_page, create_blog_page
from .simple_css import create_clean_css_file, create_landing_css_file, create_blog_css_file, create_minimal_css_file
from .simple_js import create_simple_js_file, create_minimal_js_file, create_interactive_js_file


def create_simple_website(
    project_path: str,
    site_type: str = "basic",
    site_title: str = "我的网站"
) -> str:
    """创建完整的简单网站"""

    try:
        project_dir = Path(project_path)
        project_dir.mkdir(parents=True, exist_ok=True)

        # 创建目录结构
        (project_dir / "assets" / "css").mkdir(parents=True, exist_ok=True)
        (project_dir / "assets" / "js").mkdir(parents=True, exist_ok=True)

        if site_type == "basic":
            # 基础网站
            create_simple_html_file(
                str(project_dir / "index.html"),
                title=site_title
            )
            create_clean_css_file(str(project_dir / "assets" / "css" / "clean.css"))
            create_simple_js_file(str(project_dir / "assets" / "js" / "main.js"))

        elif site_type == "landing":
            # 着陆页
            create_landing_page(
                str(project_dir / "index.html"),
                title=site_title,
                description="欢迎来到我们的网站"
            )
            create_landing_css_file(str(project_dir / "assets" / "css" / "landing.css"))
            create_simple_js_file(str(project_dir / "assets" / "js" / "main.js"))

        elif site_type == "blog":
            # 博客网站
            create_blog_page(
                str(project_dir / "index.html"),
                title=site_title
            )
            create_blog_css_file(str(project_dir / "assets" / "css" / "blog.css"))
            create_interactive_js_file(str(project_dir / "assets" / "js" / "main.js"))

        elif site_type == "minimal":
            # 极简网站
            create_blank_html_file(
                str(project_dir / "index.html"),
                title=site_title
            )
            create_minimal_css_file(str(project_dir / "assets" / "css" / "clean.css"))
            create_minimal_js_file(str(project_dir / "assets" / "js" / "main.js"))

        else:
            return f"不支持的网站类型: {site_type}。支持的类型：basic, landing, blog, minimal"

        return f"简单网站创建成功: {project_path} (类型: {site_type})"

    except Exception as exc:
        raise RuntimeError(f"创建简单网站失败: {str(exc)}")


def create_simple_page_set(
    project_path: str,
    site_title: str = "我的网站"
) -> str:
    """创建一套简单的多页面网站"""

    try:
        project_dir = Path(project_path)
        project_dir.mkdir(parents=True, exist_ok=True)

        # 创建目录结构
        (project_dir / "assets" / "css").mkdir(parents=True, exist_ok=True)
        (project_dir / "assets" / "js").mkdir(parents=True, exist_ok=True)

        # 首页
        create_simple_html_file(
            str(project_dir / "index.html"),
            title=f"{site_title} - 首页",
            content=f"""    <header>
        <h1>{site_title}</h1>
        <nav>
            <a href="index.html">首页</a>
            <a href="about.html">关于我们</a>
            <a href="services.html">服务</a>
            <a href="contact.html">联系我们</a>
        </nav>
    </header>

    <main>
        <section class="hero">
            <h2>欢迎访问{site_title}</h2>
            <p>这里是我们的主页，展示我们的核心业务和服务。</p>
            <a href="services.html" class="button">了解我们的服务</a>
        </section>

        <section>
            <h3>我们的特色</h3>
            <div class="features">
                <div class="feature">
                    <h4>专业服务</h4>
                    <p>提供专业的解决方案</p>
                </div>
                <div class="feature">
                    <h4>优质体验</h4>
                    <p>为客户提供优质的用户体验</p>
                </div>
                <div class="feature">
                    <h4>可靠支持</h4>
                    <p>7x24小时技术支持</p>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 {site_title}. 保留所有权利。</p>
    </footer>"""
        )

        # 关于页面
        create_simple_html_file(
            str(project_dir / "about.html"),
            title=f"{site_title} - 关于我们",
            content=f"""    <header>
        <h1>{site_title}</h1>
        <nav>
            <a href="index.html">首页</a>
            <a href="about.html">关于我们</a>
            <a href="services.html">服务</a>
            <a href="contact.html">联系我们</a>
        </nav>
    </header>

    <main>
        <section>
            <h2>关于我们</h2>
            <p>我们是一家专注于提供优质服务的公司。</p>

            <h3>我们的故事</h3>
            <p>成立于2020年，我们致力于为客户提供最好的解决方案。经过几年的发展，我们已经服务了众多客户，获得了良好的口碑。</p>

            <h3>我们的团队</h3>
            <p>我们拥有一支专业的团队，包括设计师、开发者、项目经理等，能够为客户提供全方位的服务。</p>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 {site_title}. 保留所有权利。</p>
    </footer>"""
        )

        # 服务页面
        create_simple_html_file(
            str(project_dir / "services.html"),
            title=f"{site_title} - 服务",
            content=f"""    <header>
        <h1>{site_title}</h1>
        <nav>
            <a href="index.html">首页</a>
            <a href="about.html">关于我们</a>
            <a href="services.html">服务</a>
            <a href="contact.html">联系我们</a>
        </nav>
    </header>

    <main>
        <section>
            <h2>我们的服务</h2>
            <p>我们提供以下专业服务：</p>

            <div class="services">
                <div class="service">
                    <h3>网站设计</h3>
                    <p>专业的网站设计服务，为您打造独特的在线形象。</p>
                </div>

                <div class="service">
                    <h3>应用开发</h3>
                    <p>移动应用和Web应用开发，满足您的业务需求。</p>
                </div>

                <div class="service">
                    <h3>品牌设计</h3>
                    <p>完整的品牌视觉设计，提升您的品牌价值。</p>
                </div>

                <div class="service">
                    <h3>技术咨询</h3>
                    <p>专业的技术咨询服务，帮助您做出正确的技术决策。</p>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 {site_title}. 保留所有权利。</p>
    </footer>"""
        )

        # 联系页面
        create_simple_html_file(
            str(project_dir / "contact.html"),
            title=f"{site_title} - 联系我们",
            content=f"""    <header>
        <h1>{site_title}</h1>
        <nav>
            <a href="index.html">首页</a>
            <a href="about.html">关于我们</a>
            <a href="services.html">服务</a>
            <a href="contact.html">联系我们</a>
        </nav>
    </header>

    <main>
        <section>
            <h2>联系我们</h2>
            <p>有任何问题或需求，请随时联系我们。</p>

            <div class="contact-info">
                <h3>联系方式</h3>
                <p><strong>邮箱：</strong>contact@example.com</p>
                <p><strong>电话：</strong>+86 138 0000 0000</p>
                <p><strong>地址：</strong>北京市朝阳区示例街道123号</p>
            </div>

            <form class="contact-form">
                <h3>发送消息</h3>

                <label for="name">姓名：</label>
                <input type="text" id="name" name="name" required>

                <label for="email">邮箱：</label>
                <input type="email" id="email" name="email" required>

                <label for="message">消息：</label>
                <textarea id="message" name="message" rows="5" required></textarea>

                <button type="submit">发送</button>
            </form>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 {site_title}. 保留所有权利。</p>
    </footer>"""
        )

        # 创建样式文件
        create_clean_css_file(str(project_dir / "assets" / "css" / "clean.css"))

        # 创建增强的CSS (添加特殊样式)
        enhanced_css = """
/* 增强样式 */
.hero {
    background-color: #f8f9fa;
    padding: 3rem 1rem;
    text-align: center;
    margin: 2rem 0;
    border-radius: 8px;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.feature {
    padding: 1.5rem;
    background-color: #f8f9fa;
    border-radius: 8px;
    text-align: center;
}

.services {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.service {
    padding: 2rem;
    border: 1px solid #e9ecef;
    border-radius: 8px;
}

.contact-info {
    background-color: #f8f9fa;
    padding: 2rem;
    border-radius: 8px;
    margin: 2rem 0;
}

.contact-form {
    max-width: 600px;
    margin: 2rem 0;
}

.contact-form label {
    display: block;
    margin: 1rem 0 0.5rem 0;
    font-weight: 600;
}

.contact-form input,
.contact-form textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 1rem;
}

.contact-form button {
    margin-top: 1rem;
}"""

        # 追加样式到CSS文件
        with open(project_dir / "assets" / "css" / "clean.css", "a", encoding="utf-8") as f:
            f.write(enhanced_css)

        # 创建JavaScript文件
        create_simple_js_file(str(project_dir / "assets" / "js" / "main.js"))

        return f"简单多页面网站创建成功: {project_path} (包含4个页面)"

    except Exception as exc:
        raise RuntimeError(f"创建多页面网站失败: {str(exc)}")


__all__ = [
    "create_simple_website",
    "create_simple_page_set"
]