"""网页工具包模块化导出"""
from __future__ import annotations

from .bootstrap import add_bootstrap
from .browser import open_in_browser, start_live_server
from .css import create_css_file
# 使用改进版的页面生成工具
try:
    from .html_templates_improved import (
        create_html_file,
        create_menu_page,
        create_about_page,
        create_contact_page,
    )
except ImportError:
    # 如果改进版不存在，回退到原版
    from .html_templates import (
        create_html_file,
        create_menu_page,
        create_about_page,
        create_contact_page,
    )
from .images import fetch_generated_images, inject_images
from .js import create_js_file
from .navigation import create_responsive_navbar
from .project import create_project_structure
from .validation import check_mobile_friendly, validate_html
# from .colors import generate_color_scheme  # 暂停导出：无需在主流程中使用

# 新增简单模板支持（暂时注释，备用组件无需默认加载）
# from .simple_templates import (
#     create_simple_html_file,
#     create_blank_html_file,
#     create_landing_page,
#     create_blog_page,
# )
# from .simple_css import (
#     create_clean_css_file,
#     create_landing_css_file,
#     create_blog_css_file,
#     create_minimal_css_file,
# )
# from .simple_js import (
#     create_simple_js_file,
#     create_minimal_js_file,
#     create_interactive_js_file,
# )
# from .simple_builder import (
#     create_simple_website,
#     create_simple_page_set,
# )
from .edgeone_deploy import (
    deploy_folder_or_zip_to_edgeone,
    EdgeOneDeployer,
)

__all__ = [
    "create_project_structure",
    "create_html_file",
    "create_menu_page",
    "create_about_page",
    "create_contact_page",
    "create_css_file",
    "create_js_file",
    "add_bootstrap",
    "create_responsive_navbar",
    "fetch_generated_images",
    "inject_images",
    "open_in_browser",
    "start_live_server",
    "validate_html",
    "check_mobile_friendly",
    # "generate_color_scheme",
    # # 简单模板
    # "create_simple_html_file",
    # "create_blank_html_file",
    # "create_landing_page",
    # "create_blog_page",
    # # 简单CSS
    # "create_clean_css_file",
    # "create_landing_css_file",
    # "create_blog_css_file",
    # "create_minimal_css_file",
    # # 简单JS
    # "create_simple_js_file",
    # "create_minimal_js_file",
    # "create_interactive_js_file",
    # # 简单网站构建器
    # "create_simple_website",
    # "create_simple_page_set",
    # EdgeOne部署工具
    "deploy_folder_or_zip_to_edgeone",
    "EdgeOneDeployer",
]
