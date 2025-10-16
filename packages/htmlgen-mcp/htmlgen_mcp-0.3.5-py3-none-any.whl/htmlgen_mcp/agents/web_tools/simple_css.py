"""简单CSS样式工具 - 轻量级样式生成"""
from __future__ import annotations

from pathlib import Path


def create_clean_css_file(file_path: str) -> str:
    """创建干净简洁的CSS样式文件"""

    css_content = """/* 简洁干净的CSS样式 */

/* 基础重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
}

/* 布局 */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 标题 */
h1, h2, h3, h4, h5, h6 {
    margin-bottom: 1rem;
    font-weight: 600;
    line-height: 1.2;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }

/* 段落 */
p {
    margin-bottom: 1rem;
}

/* 链接 */
a {
    color: #007bff;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* 导航 */
nav {
    padding: 1rem 0;
}

nav a {
    margin-right: 2rem;
    font-weight: 500;
}

/* 区块 */
section {
    margin: 3rem 0;
    padding: 2rem 0;
}

/* 页脚 */
footer {
    background-color: #f8f9fa;
    padding: 2rem 0;
    text-align: center;
    margin-top: 3rem;
    border-top: 1px solid #e9ecef;
}

/* 按钮 */
button, .button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
}

button:hover, .button:hover {
    background-color: #0056b3;
}

/* 响应式 */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }

    h1 { font-size: 2rem; }
    h2 { font-size: 1.5rem; }

    nav a {
        margin-right: 1rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
}"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(css_content)
        return f"简洁CSS文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建CSS文件失败: {str(exc)}")


def create_landing_css_file(file_path: str) -> str:
    """创建着陆页CSS样式"""

    css_content = """/* 着陆页样式 */

/* 基础重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 主要区域 */
.hero {
    text-align: center;
    padding: 4rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 60vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    font-weight: 700;
}

.subtitle {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    opacity: 0.9;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

.cta-button {
    background-color: #fff;
    color: #667eea;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}

/* 特点区域 */
.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    padding: 4rem 0;
}

.feature {
    text-align: center;
    padding: 2rem;
    border-radius: 8px;
    background-color: #f8f9fa;
}

.feature h3 {
    margin-bottom: 1rem;
    color: #495057;
    font-size: 1.5rem;
}

.feature p {
    color: #6c757d;
    line-height: 1.6;
}

/* 页脚 */
footer {
    background-color: #343a40;
    color: white;
    text-align: center;
    padding: 2rem 0;
}

/* 响应式 */
@media (max-width: 768px) {
    .hero h1 {
        font-size: 2.25rem;
    }

    .subtitle {
        font-size: 1.1rem;
    }

    .features {
        grid-template-columns: 1fr;
        gap: 1.5rem;
    }
}"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(css_content)
        return f"着陆页CSS文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建CSS文件失败: {str(exc)}")


def create_blog_css_file(file_path: str) -> str:
    """创建博客CSS样式"""

    css_content = """/* 博客样式 */

/* 基础重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Georgia, "Times New Roman", serif;
    line-height: 1.7;
    color: #333;
    background-color: #fafafa;
}

.container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 20px;
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 3rem;
}

/* 头部 */
header {
    background-color: white;
    border-bottom: 1px solid #e9ecef;
    padding: 2rem 0;
    margin-bottom: 3rem;
    grid-column: 1 / -1;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #2c3e50;
}

nav a {
    margin-right: 2rem;
    color: #6c757d;
    text-decoration: none;
    font-weight: 500;
}

nav a:hover {
    color: #2c3e50;
}

/* 主要内容 */
main {
    background-color: white;
}

.post {
    background-color: white;
    padding: 2rem;
    margin-bottom: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.post h2 {
    color: #2c3e50;
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
}

.meta {
    color: #6c757d;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    font-style: italic;
}

.post p {
    font-size: 1.1rem;
    line-height: 1.8;
    margin-bottom: 1rem;
}

/* 侧边栏 */
.sidebar {
    padding-top: 0;
}

.widget {
    background-color: white;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.widget h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
    font-size: 1.25rem;
}

.widget ul {
    list-style: none;
}

.widget li {
    margin-bottom: 0.5rem;
}

.widget a {
    color: #6c757d;
    text-decoration: none;
}

.widget a:hover {
    color: #2c3e50;
}

/* 页脚 */
footer {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
    grid-column: 1 / -1;
}

/* 响应式 */
@media (max-width: 768px) {
    .container {
        grid-template-columns: 1fr;
        gap: 2rem;
    }

    header h1 {
        font-size: 2rem;
    }

    nav a {
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    .post {
        padding: 1.5rem;
    }
}"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(css_content)
        return f"博客CSS文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建CSS文件失败: {str(exc)}")


def create_minimal_css_file(file_path: str) -> str:
    """创建极简CSS样式"""

    css_content = """/* 极简样式 */

body {
    font-family: system-ui, sans-serif;
    line-height: 1.6;
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
    color: #333;
}

h1, h2, h3 {
    margin: 1.5rem 0 0.5rem 0;
}

p {
    margin-bottom: 1rem;
}

a {
    color: #0066cc;
}

button {
    background: #0066cc;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background: #0052a3;
}

footer {
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid #ddd;
    text-align: center;
    color: #666;
}"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(css_content)
        return f"极简CSS文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建CSS文件失败: {str(exc)}")


__all__ = [
    "create_clean_css_file",
    "create_landing_css_file",
    "create_blog_css_file",
    "create_minimal_css_file"
]