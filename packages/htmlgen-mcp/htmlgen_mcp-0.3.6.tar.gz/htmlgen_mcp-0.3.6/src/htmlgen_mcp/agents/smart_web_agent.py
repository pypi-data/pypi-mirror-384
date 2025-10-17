#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能批量工具调用Web Agent - 2025年最佳实践
预先规划，用户确认，批量执行 - 完美解决轮数不确定问题
增强版：包含错误恢复、重试机制、进度显示等优化
"""

import os
import sys
import json
import copy
import click
import time
import textwrap
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import traceback

# 确保UTF-8编码支持（容忍异常字符）
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout.reconfigure(errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stderr.reconfigure(errors="replace")

# 导入工具函数
from .web_tools import *
from .quick_generator import QuickSiteGenerator


class SmartWebAgent:
    def __init__(
        self,
        project_directory: str,
        model: str = "qwen3-coder-plus-2025-09-23",
        show_code: bool = False,
        verbose: bool = False,
        show_plan_stream: bool = False,
        save_output: bool = False,
        force_single_page: bool = True,
    ):
        self.project_directory = project_directory
        self.model = model
        self.show_code = show_code
        self.verbose = verbose  # 新增：详细输出模式
        self.show_plan_stream = show_plan_stream  # 新增：流式显示计划生成
        self.save_output = save_output  # 新增：保存输出到日志
        self.force_single_page = force_single_page
        api_key, base_url = self._resolve_api_credentials()
        self.client = self._build_client(api_key, base_url)

        # 工具函数映射
        self.tool_functions = {
            "create_project_structure": create_project_structure,
            "create_html_file": create_html_file,
            "create_css_file": create_css_file,
            "create_js_file": create_js_file,
            "add_bootstrap": add_bootstrap,
            "create_responsive_navbar": create_responsive_navbar,
            "fetch_generated_images": fetch_generated_images,
            "inject_images": inject_images,
            "open_in_browser": open_in_browser,
            "validate_html": validate_html,
            "check_mobile_friendly": check_mobile_friendly,
            # 新增：专用页面生成工具（餐饮类）
            "create_menu_page": create_menu_page,
            "create_about_page": create_about_page,
            "create_contact_page": create_contact_page,
        }

        # 执行历史记录
        self.execution_history = []
        self.created_files = []
        self.execution_start_time = None

        # 日志文件设置
        if self.save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = os.path.join(
                project_directory, f"agent_log_{timestamp}.txt"
            )
            self._log(
                f"=== Agent 执行日志 ===\n时间: {datetime.now()}\n目录: {project_directory}\n"
            )

    def _resolve_api_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """解析API凭据，支持多家兼容厂商"""
        load_dotenv()

        # 从环境变量获取API密钥和基础URL
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("AI_BASE_URL")

        # 如果未配置，给出提示
        if not api_key:
            print(
                "Warning: No API key found. Please set OPENAI_API_KEY or AI_API_KEY environment variable."
            )
            return None, None

        # 默认基础URL（阿里云兼容模式）
        if not base_url:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        return api_key, base_url

    def _build_client(
        self, api_key: Optional[str], base_url: Optional[str]
    ) -> Optional[OpenAI]:
        """根据凭据初始化 OpenAI 客户端"""
        if not api_key:
            return None
        try:
            if base_url:
                return OpenAI(base_url=base_url, api_key=api_key)
            return OpenAI(api_key=api_key)
        except Exception:
            return None

    def _step_requires_content(self, tool_name: str) -> bool:
        """判断该步骤是否需要即时生成代码内容"""
        return tool_name in {"create_html_file", "create_css_file", "create_js_file"}

    def _plan_outline_for_prompt(self, plan: dict, limit: int = 8) -> str:
        outline: list[str] = []
        steps = plan.get("tools_sequence", []) or []
        for spec in steps[:limit]:
            step_no = spec.get("step") or len(outline) + 1
            outline.append(
                f"{step_no}. {spec.get('tool', 'unknown_tool')} - {spec.get('description', '')}"
            )
        if len(steps) > limit:
            outline.append("...")
        return "\n".join(outline) or "无计划步骤"

    def _recent_execution_summary(self, limit: int = 3) -> str:
        if not self.execution_history:
            return "暂无执行记录"
        recent: list[str] = []
        for item in self.execution_history[-limit:]:
            message = item.get("result", "")
            if isinstance(message, str) and len(message) > 80:
                message = message[:77] + "..."
            recent.append(f"步骤{item.get('step')} {item.get('tool')}: {message}")
        return "\n".join(recent)

    def _collect_existing_assets(
        self, plan: dict, tool_spec: dict, max_files: int = 5, max_chars: int = 800
    ) -> str:
        project_root = Path(self._project_root(plan)).resolve()
        if not project_root.exists():
            return "暂无已生成内容"

        params = tool_spec.get("params", {}) or {}
        raw_target = params.get("file_path")
        target_path: Optional[Path] = None
        if raw_target:
            candidate = Path(raw_target)
            if not candidate.is_absolute():
                candidate = (project_root / candidate).resolve()
            else:
                candidate = candidate.resolve()
            if candidate.exists():
                target_path = candidate

        tool_name = tool_spec.get("tool", "")
        if tool_name == "create_css_file":
            patterns = ["*.css", "*.html"]
        elif tool_name == "create_js_file":
            patterns = ["*.js", "*.html", "*.css"]
        else:
            patterns = ["*.html", "*.css"]

        snippets: list[str] = []
        seen: set[Path] = set()
        total_chars = 0

        def add_file(fp: Path, label: str) -> None:
            nonlocal total_chars
            resolved = fp.resolve()
            if not resolved.exists() or not resolved.is_file():
                return
            if resolved in seen:
                return
            try:
                raw_text = resolved.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return
            snippet = raw_text.strip()
            if not snippet:
                return
            if len(snippet) > max_chars:
                snippet = snippet[:max_chars] + "..."
            try:
                rel_path = resolved.relative_to(project_root)
            except ValueError:
                rel_path = resolved.name
            snippets.append(f"[{label}] {rel_path}:{snippet}")
            seen.add(resolved)
            total_chars += len(snippet)

        if target_path:
            add_file(target_path, "当前文件")

        for pattern in patterns:
            for fp in sorted(project_root.rglob(pattern)):
                if len(snippets) >= max_files or total_chars >= max_files * max_chars:
                    break
                if target_path and fp.resolve() == target_path:
                    continue
                add_file(fp, "已有文件")
            if len(snippets) >= max_files or total_chars >= max_files * max_chars:
                break

        if not snippets:
            return "暂无已生成内容"
        return "\n\n".join(snippets)

    def _code_generation_system_prompt(self) -> str:
        return (
            "你是通义千问 Qwen 上的网页生成工程师，专注高端站点开发。"
            "按照网站构建计划逐步产出高质量代码，保持语义化、可访问性、响应式与性能优化。"
            "所有回复必须是JSON，对象包含content字段，值为需要写入文件的完整代码字符串，不能包含Markdown或其它解释。"
        )

    def _build_code_generation_prompt(self, tool_spec: dict, plan: dict) -> str:
        tool_name = tool_spec.get("tool", "")
        params = tool_spec.get("params", {}) or {}
        description = tool_spec.get("description", "")
        rationale = tool_spec.get("rationale", "")
        user_need = getattr(self, "latest_user_request", "")
        plan_outline = self._plan_outline_for_prompt(plan)
        previous = self._recent_execution_summary()
        color_scheme = plan.get("color_scheme") or {}
        param_clone = {k: v for k, v in params.items() if k != "content"}
        param_json = json.dumps(param_clone, ensure_ascii=False, indent=2)
        project_context = self._collect_existing_assets(plan, tool_spec)
        instructions = ""
        if tool_name == "create_html_file":
            instructions = (
                "生成完整HTML5文档，包含<head>、<body>、语义化结构、meta描述、OpenGraph标签和响应式布局。"
                "如果提供nav_items，请渲染导航并正确标记active状态。"
                "结合步骤描述组织Hero区、服务/功能区、CTA、页脚等模块，融入设计风格与品牌调性。"
            )
        elif tool_name == "create_css_file":
            instructions = (
                "生成覆盖站点的CSS样式表，构建变量系统、排版、栅格与间距、动画、暗色模式切换、组件样式。"
                "结合color_scheme定义CSS变量，提供按钮、卡片、导航、section等现代样式。"
            )
        elif tool_name == "create_js_file":
            instructions = (
                "生成现代前端脚本，包含平滑滚动、导航栏滚动态、IntersectionObserver显隐动画、"
                "返回顶部、主题切换、表单校验、数字动画等交互，确保模块化与可维护性。"
            )
        else:
            instructions = "根据步骤描述生成与该工具匹配的内容。"

        if color_scheme:
            instructions += (
                f" 请优先使用配色方案: {json.dumps(color_scheme, ensure_ascii=False)}。"
            )

        prompt = textwrap.dedent(
            f"""
            用户原始需求:
            {user_need}

            执行纲要概览:
            {plan_outline}

            已完成步骤:
            {previous}

            已有项目上下文:
            {project_context}

            当前步骤: {description} ({tool_name})
            步骤目的: {rationale}
            目标参数:
            {param_json}

            生成要求:
            {instructions}

            输出JSON，格式:
            {{"content": "<代码字符串>"}}
            """
        ).strip()
        return prompt

    def _generate_step_content(self, tool_spec: dict, plan: dict) -> str:
        if self.client is None:
            return ""
        prompt = self._build_code_generation_prompt(tool_spec, plan)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._code_generation_system_prompt(),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            message = response.choices[0].message.content or ""
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = {"content": message}
            content = data.get("content") or data.get("code") or ""
            if self.save_output:
                step_id = tool_spec.get("step")
                self._log(
                    f"=== 生成内容 Step {step_id} ({tool_spec.get('tool')}) ===\n{content}\n"
                )
            return content
        except Exception as exc:
            print(f"⚠️ 内容生成失败: {exc}")
            if self.verbose:
                print(traceback.format_exc())
            return ""

    def _ensure_step_content(self, tool_spec: dict, params: dict, plan: dict) -> dict:
        tool_name = tool_spec.get("tool", "")
        if not self._step_requires_content(tool_name):
            return params
        if params.get("content"):
            return params
        if self.client is None:
            return params
        print("🧠 正在生成代码内容，请稍候...")
        content = self._generate_step_content(tool_spec, plan)
        if not content:
            print("⚠️ 未能生成内容，将使用工具默认模板。")
            return params
        params["content"] = content
        tool_spec.setdefault("params", {})["content"] = content
        if self.show_code or self.verbose:
            preview = content[:500]
            print("📝 内容预览:")
            print("=" * 40)
            print(preview)
            if len(content) > 500:
                print(f"... (共 {len(content)} 字符)")
            print("=" * 40)
        return params

    def _log(self, message: str):
        """记录日志到文件"""
        if self.save_output and hasattr(self, "log_file"):
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(message + "\n")
            except Exception:
                pass  # 日志失败不影响主流程

    def run(
        self,
        user_input: str,
        auto_execute: bool = False,
        confirm_each_step: bool = None,
        progress_callback=None,
    ):
        """智能批量工具调用 - 增强版流程"""
        self.execution_start_time = time.time()
        self.execution_history = []
        self.created_files = []
        self.latest_user_request = user_input
        self.current_plan: dict[str, Any] | None = None

        # 默认策略：
        # - auto_execute=True 时，关闭逐步确认
        # - auto_execute=False 时，开启逐步确认
        if confirm_each_step is None:
            confirm_each_step = not auto_execute

        print("🧠 第一步：智能规划任务...")
        print("=" * 60)

        # 增强用户输入，添加默认要求
        enhanced_input = self._enhance_user_input(user_input)

        # 第一步：让模型制定详细的执行计划（带重试机制，含离线回退）
        plan = self._get_execution_plan_with_retry(enhanced_input)
        if not plan:
            return "❌ 无法生成执行计划，请重试"

        # 显示执行计划
        self._display_execution_plan(plan)
        # 进度：计划已生成
        if callable(progress_callback):
            try:
                progress_callback(
                    {
                        "type": "plan",
                        "status": "ready",
                        "percent": 0.0,
                        "description": "执行计划已生成",
                        "thought": plan.get("task_analysis"),
                    }
                )
            except Exception:
                pass

        # 询问用户确认
        if not auto_execute:
            confirm = self._get_user_confirmation(plan)
            if not confirm:
                return "❌ 用户取消执行"

        # 第二步：执行计划
        print(f"\n🚀 开始执行任务...")
        print("=" * 60)

        results = self._execute_plan_with_recovery(
            plan,
            confirm_each_step=confirm_each_step,
            progress_callback=progress_callback,
        )

        if any(
            r.get("status") == "success"
            and r.get("tool") in {"create_html_file", "create_css_file"}
            for r in results
        ):
            self._run_consistency_review(plan)

        # 生成执行报告
        report = self._generate_execution_report(plan, results)

        return report

    def _get_execution_plan_with_retry(
        self, user_input: str, max_retries: int = 3
    ) -> Optional[dict]:
        """获取执行计划，带重试机制"""
        
        # 判断是否使用快速模式
        if self._should_use_quick_mode(user_input):
            print("⚡ 启用快速模式：生成单页面网站")
            site_type = self._extract_site_type(user_input)
            project_name = self._extract_project_name(user_input, site_type)
            
            plan = QuickSiteGenerator.create_single_page_plan(
                project_name=project_name,
                site_type=site_type,
                description=user_input
            )
            
            # 进一步优化速度
            plan = QuickSiteGenerator.optimize_for_speed(plan)
            self.current_plan = plan
            return plan
        
        # 若无客户端，直接走离线计划
        if self.client is None:
            plan = self._build_fallback_plan(user_input)
            plan = self._repair_plan_tools_sequence(plan)
            self.current_plan = plan
            return plan if self._validate_plan(plan) else None

        for attempt in range(max_retries):
            try:
                print(
                    f"⚡ 正在分析需求并生成执行计划... (尝试 {attempt + 1}/{max_retries})"
                )
                plan = self._get_execution_plan(user_input)
                plan = self._repair_plan_tools_sequence(plan)
                if self._validate_plan(plan):
                    self.current_plan = plan
                    return plan
            except Exception as e:
                print(f"⚠️ 生成计划失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试

        # 远程多次失败后启用离线回退
        print("🔁 使用离线回退计划")
        plan = self._build_fallback_plan(user_input)
        plan = self._repair_plan_tools_sequence(plan)
        self.current_plan = plan
        return plan if self._validate_plan(plan) else None

    def _get_execution_plan(self, user_input: str) -> dict:
        """获取执行计划 - 支持流式输出"""

        if self.client is None:
            # 由上层回退
            raise RuntimeError("没有可用的LLM客户端")

        # 第一步：让模型制定详细的执行计划
        planning_prompt_template = """你是一个专业的网页设计与前端开发专家，精通现代Web技术、设计系统和用户体验。
请分析用户需求并制定执行计划，创建高质量、现代化、专业的网站。

🎨 核心设计理念：
• 现代美观：采用当前流行的设计趋势（如新拟态、毛玻璃、渐变、3D效果）
• 用户体验：移动优先、快速加载、流畅交互、无障碍访问
• 视觉层次：合理的留白、清晰的信息架构、引导性的视觉流
• 品牌一致：统一的设计语言、配色方案、字体系统

📊 **页面生成策略**：
• 快速模式（默认）：仅生成一个完整的首页，包含所有核心内容部分
• 多页面模式：仅当用户明确提到"多页面"、"多个页面"、"分别创建"或列出具体页面名称时启用
• 判断规则：如果用户只说"咖啡店网站"、"企业官网"等，默认使用单页面滚动式设计

用户需求：<<USER_INPUT>>
工作目录：<<PROJECT_DIR>>

可用工具：
- create_project_structure(project_name, project_path): 创建项目目录结构
- create_html_file(file_path, title, content): 创建HTML文件
- create_css_file(file_path, content): 创建CSS文件
- create_js_file(file_path, content): 创建JavaScript文件
- add_bootstrap(project_path): 添加Bootstrap框架
- create_responsive_navbar(file_path, brand_name, nav_items): 创建响应式导航栏
- fetch_generated_images(project_path, provider, prompts, count, size, seed, save, subdir, prefix): 获取/下载生成图片
- inject_images(file_path, provider, topics, size, seed, save, subdir, prefix): 将生成图片注入到HTML（支持 data-bg-topic / data-topic）
- open_in_browser(file_path): 在浏览器中预览
- validate_html(file_path): 验证HTML语法
- check_mobile_friendly(file_path): 检查移动端友好性
 - create_menu_page(file_path, project_name): 专用“菜单”页面（餐饮/咖啡站点，分类清晰、价格醒目）
 - create_about_page(file_path, project_name): 专用“关于我们”页面（品牌故事/理念/团队）
 - create_contact_page(file_path, project_name): 专用“联系我们”页面（营业时间/地址/表单/地图）

输出JSON格式的执行计划：
{
  "task_analysis": "详细的任务分析，包括网站类型、风格定位、目标用户",
  "project_name": "项目名称（英文，如：modern-portfolio）",
  "site_type": "网站类型",
  "design_style": "设计风格",
  "color_scheme": {
    "primary": "#主色",
    "secondary": "#辅助色",
    "accent": "#强调色"
  },
  "estimated_time": "预计执行时间",
  "tools_sequence": [
    {
      "step": 1,
      "tool": "工具名",
      "params": {},
      "description": "步骤描述",
      "rationale": "执行原因"
    }
  ]
}

📋 执行规范：

⚠️ **重要提示**：优先速度！除非用户明确要求，否则只生成一个页面。

1. **项目结构**（简化流程）：
   - 第1步：create_project_structure - 创建完整目录结构
   - 第2步：create_css_file - 创建样式文件(assets/css/style.css)
   - 第3步：create_js_file - 创建脚本文件(assets/js/main.js)
   - 第4步：create_html_file - 创建主页面
   - 第5步：add_bootstrap - 添加框架支持
   - 第6步：create_responsive_navbar - 创建导航组件
   - 🎨 **第7步：inject_images - 智能图片注入（必须包含！）**
   - 第8步：验证HTML（可选）
   - 第9步：open_in_browser - 预览效果
   - 仅在用户明确要求多页面时，才为每个页面单独安排步骤

⚠️ **重要：第7步图片注入是必需的！**
使用 inject_images 为网站添加美观的AI生成图片：
- provider="pollinations": 万能AI图片生成（场景、产品图）
- provider="dicebear": SVG头像（团队成员、用户头像）
- provider="robohash": 个性化头像（可爱风格）

图片注入要求：
- 每个页面创建后必须立即跟随图片注入步骤
- 根据页面类型和用户需求智能选择图片主题
- 为不同区域使用合适的图片尺寸
- 确保图片主题与网站整体风格一致
- 支持用户自定义图片风格和主题
- 智能匹配行业特定的图片内容

2. **网站类型适配**：
   📱 **作品集/Portfolio**：
   - Hero区：个人介绍+技能标签+CTA
   - 作品展示：网格布局+悬停效果+分类筛选
   - 关于我：个人故事+技能进度条+工作经历时间线
   - 客户评价：轮播展示
   - 联系方式：表单+社交媒体链接

   🏢 **企业官网**：
   - Hero区：价值主张+视频背景（占位）+双CTA按钮
   - 服务介绍：图标卡片+悬停动画
   - 数据展示：动态数字+图表占位
   - 团队介绍：人员卡片+职位信息
   - 合作伙伴：Logo墙+滚动动画

   🍔 **餐厅网站 / 咖啡店**：
   - 默认生成单页面版本：Hero区+菜单展示+营业信息+联系方式（全部在首页）
   - 多页面版本（仅在用户要求时）：
     * 菜单页：使用 create_menu_page
     * 关于页：使用 create_about_page  
     * 联系页：使用 create_contact_page

   🛍️ **电商着陆页**：
   - Hero区：产品大图+限时优惠倒计时
   - 产品特性：对比表格+规格参数
   - 用户评价：评分分布+真实评论
   - FAQ：折叠面板+搜索功能
   - 购买区：价格方案+支付图标

   📰 **博客/内容站**：
   - Hero区：精选文章+订阅框
   - 文章列表：卡片布局+阅读时间+标签
   - 侧边栏：分类导航+热门文章+广告位
   - 作者信息：头像+简介+社交链接

3. **CSS生成要求**：
   ```css
   /* 必须包含的设计系统 */
   :root {
     /* 色彩系统 */
     --primary: #主色;
     --primary-rgb: r,g,b;
     --secondary: #辅助色;
     --accent: #强调色;
     --gradient-1: linear-gradient(...);
     --gradient-2: radial-gradient(...);

     /* 间距系统 */
     --space-xs: 0.5rem;
     --space-sm: 1rem;
     --space-md: 2rem;
     --space-lg: 3rem;
     --space-xl: 5rem;

     /* 阴影系统 */
     --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
     --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
     --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
     --shadow-xl: 0 20px 25px rgba(0,0,0,0.15);

     /* 动画时长 */
     --transition-fast: 150ms;
     --transition-base: 250ms;
     --transition-slow: 400ms;
   }
   ```

   **现代效果实现**：
   - 毛玻璃：backdrop-filter: blur(10px)
   - 新拟态：多层阴影组合
   - 渐变叠加：background-blend-mode
   - 平滑滚动：scroll-behavior: smooth
   - 视差效果：transform3d + perspective
   - 文字渐变：background-clip: text
   - 悬停缩放：transform: scale(1.05)
   - 加载动画：@keyframes + animation

4. **JavaScript功能增强**：
   - 平滑滚动导航
   - 滚动显示动画（IntersectionObserver）
   - 导航栏滚动变化（透明→实色）
   - 返回顶部按钮
   - 表单验证反馈
   - 图片懒加载
   - 数字动态增长
   - 打字机效果
   - 主题切换（明/暗）

5. **HTML内容要求**：
   - 语义化标签：header, nav, main, section, article, aside, footer
   - SEO优化：合理的h1-h6层级，meta描述
   - 性能优化：图片lazy loading，关键CSS内联
   - 无障碍：ARIA标签，焦点管理，键盘导航
   - 微数据：结构化数据标记（组织、产品、评论）

6. **响应式断点**：
   - 移动端优先：320px起
   - 平板：768px
   - 桌面：1024px
   - 大屏：1440px
   - 超大屏：1920px

7. **性能优化**：
   - 关键CSS内联
   - 字体预加载
   - 图片格式：WebP + fallback
   - 代码分割：异步加载非关键JS
   - 缓存策略：设置合理的cache headers

8. **质量保证**：
   - 代码整洁：合理缩进，注释清晰
   - 跨浏览器：Chrome, Firefox, Safari, Edge兼容
   - 性能分数：Lighthouse得分>90
   - 安全性：XSS防护，HTTPS就绪

⚠️ 当前阶段仅需输出执行纲要，不要直接生成 HTML/CSS/JS 代码。对于 create_html_file / create_css_file / create_js_file 请将 params.content 留空字符串或直接省略，该内容会在后续步骤单独生成。
请为每个步骤提供清晰的 description（做什么）与 rationale（为什么要这么做），方便用户确认。

只输出JSON格式，不要其他内容。"""

        # 使用实际值替换占位符
        planning_prompt = planning_prompt_template.replace(
            "<<USER_INPUT>>", user_input
        ).replace("<<PROJECT_DIR>>", self.project_directory)

        # 获取执行计划 - 支持流式输出
        if self.show_plan_stream:
            print("\n📝 AI思考中（实时显示）：")
            print("-" * 60)

            # 启用流式输出
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": planning_prompt}],
                response_format={"type": "json_object"},
                stream=True,  # 启用流式
            )

            # 收集流式响应
            full_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    # 实时显示生成的JSON（仅在verbose模式）
                    if self.verbose:
                        print(content, end="", flush=True)

            if self.verbose:
                print("\n" + "-" * 60)
            else:
                print("✅ 计划生成完成")
                print("-" * 60)

            plan_content = full_content
        else:
            # 非流式模式
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": planning_prompt}],
                response_format={"type": "json_object"},
            )
            plan_content = response.choices[0].message.content

        # 保存原始计划到日志
        if self.save_output:
            self._log(f"\n=== 原始执行计划 ===\n{plan_content}\n")

        # 默认不打印原始JSON，避免干扰交互；如需调试可开启环境变量 DEBUG_PLAN=1
        if os.getenv("DEBUG_PLAN") == "1":
            print(plan_content)

        try:
            plan = json.loads(plan_content)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败: {e}")
            if self.verbose:
                print(f"原始内容前500字符: {plan_content[:500]}...")
            raise

        self.current_plan = plan
        return plan

    # ---------------- 离线回退：确定性执行计划 ----------------
    def _slugify(self, text: str, default: str = "web-project") -> str:
        allow = "abcdefghijklmnopqrstuvwxyz0123456789-"
        slug = []
        text = (text or "").lower().strip().replace(" ", "-")
        for ch in text:
            if ch.isalnum():
                slug.append(ch)
            elif ch in ["_", "-", "/", "\\", "."]:
                slug.append("-")
        s = "".join(slug).strip("-")
        return s[:32] or default

    def _should_use_quick_mode(self, user_input: str) -> bool:
        """判断是否应该使用快速模式
        
        快速模式条件：
        1. 用户未明确要求多页面
        2. 用户未列出具体的页面名称
        3. 用户未要求复杂的功能
        """
        if getattr(self, "force_single_page", False):
            return True
        
        lower_input = user_input.lower()
        
        # 检查是否明确要求多页面
        multi_page_keywords = [
            "多页面", "多个页面", "分别创建", "分别生成",
            "菜单页", "关于页", "联系页", "产品页",
            "multiple pages", "separate pages", "menu page", "about page"
        ]
        
        for keyword in multi_page_keywords:
            if keyword in lower_input:
                return False
        
        # 检查是否有复杂功能要求
        complex_keywords = [
            "复杂", "详细", "完整", "全面", "多功能",
            "complex", "detailed", "complete", "comprehensive"
        ]
        
        for keyword in complex_keywords:
            if keyword in lower_input:
                return False
        
        # 默认使用快速模式
        return True
    
    def _extract_site_type(self, user_input: str) -> str:
        """从用户输入中提取网站类型"""
        lower_input = user_input.lower()
        
        type_keywords = {
            "咖啡店": ["咖啡", "coffee", "cafe"],
            "餐厅": ["餐厅", "餐饮", "美食", "restaurant", "dining"],
            "企业": ["企业", "公司", "商业", "company", "corporate", "business"],
            "作品集": ["作品集", "个人", "portfolio", "personal"],
            "电商": ["电商", "商店", "购物", "shop", "store", "ecommerce"],
            "博客": ["博客", "文章", "内容", "blog", "article"]
        }
        
        for site_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in lower_input:
                    return site_type
        
        return "通用网站"
    
    def _extract_project_name(self, user_input: str, site_type: str) -> str:
        """从用户输入提取或生成项目名称"""
        # 尝试提取引号中的名称
        import re
        match = re.search(r'[“"「]([\w\s\u4e00-\u9fa5]+)[”"」]', user_input)
        if match:
            name = match.group(1)
            # 转换为英文项目名
            name = name.replace(' ', '-').lower()
            # 如果是中文，使用类型作为前缀
            if any(ord(c) > 127 for c in name):
                return f"{site_type.replace('网站', '').lower()}-site"
            return name
        
        # 默认项目名
        type_to_name = {
            "咖啡店": "coffee-shop",
            "餐厅": "restaurant",
            "企业": "corporate",
            "作品集": "portfolio",
            "电商": "ecommerce",
            "博客": "blog",
            "通用网站": "modern-site"
        }
        
        return type_to_name.get(site_type, "website")
    
    def _build_fallback_plan(self, user_input: str) -> dict:
        """在无网络/无密钥时的本地执行计划：生成一个现代化的基础站点骨架"""
        project_name = self._slugify(user_input)
        project_root = os.path.join(self.project_directory, project_name)

        # 简单餐饮类识别（咖啡/餐厅/菜单关键字）
        key = user_input.lower()
        is_restaurant = any(
            k in key
            for k in [
                "餐厅",
                "餐馆",
                "咖啡",
                "咖啡店",
                "cafe",
                "coffee",
                "菜单",
                "menu",
            ]
        )
        is_mall = any(
            k in key
            for k in [
                "购物",
                "商场",
                "mall",
                "plaza",
                "零售",
                "shopping",
            ]
        )

        single_page_mode = getattr(self, "force_single_page", False)

        if not single_page_mode:
            if is_restaurant:
                nav_structure = [
                    {"name": "首页", "href": "index.html"},
                    {"name": "菜单", "href": "menu.html"},
                    {"name": "关于我们", "href": "about.html"},
                    {"name": "联系我们", "href": "contact.html"},
                ]
            else:
                nav_structure = [
                    {"name": "首页", "href": "index.html"},
                    {"name": "关于我们", "href": "about.html"},
                    {"name": "服务体系", "href": "services.html"},
                    {"name": "联系我们", "href": "contact.html"},
                ]

            def build_nav(active_href: str) -> list:
                return [
                    {**item, "active": item["href"] == active_href}
                    for item in nav_structure
                ]
        else:
            nav_structure = []

            def build_nav(_: str) -> list:
                return []

        plan: dict = {
            "task_analysis": "离线回退：根据描述创建现代化基础网站骨架",
            "project_name": project_name,
            "site_type": "restaurant" if is_restaurant else ("shopping-mall" if is_mall else "basic-landing"),
            "design_style": "modern, responsive, glassmorphism",
            "color_scheme": {
                "primary": "#0d6efd",
                "secondary": "#6c757d",
                "accent": "#6610f2",
            },
            "estimated_time": "约10秒",
            "tools_sequence": [],
        }

        steps = plan["tools_sequence"]
        # 1-3 基础设施
        steps.append(
            {
                "step": 1,
                "tool": "create_project_structure",
                "params": {
                    "project_name": project_name,
                    "project_path": self.project_directory,
                },
                "description": "创建项目目录结构",
                "rationale": "确保 assets/css, assets/js 等目录就绪",
            }
        )
        # 为不同站点类型提供更有“品牌感”的默认配色
        cafe_palette = {
            "primary": "#6B4F3A",
            "secondary": "#8C5E3C",
            "accent": "#D0A97A",
            "neutral_light": "#F7F3EE",
            "neutral_dark": "#201A16",
        } if is_restaurant else {
            "primary": "#1E3A8A" if is_mall else "#0d6efd",
            "secondary": "#4338CA" if is_mall else "#6c757d",
            "accent": "#F59E0B" if is_mall else "#6610f2",
            "neutral_light": "#F3F4F6",
            "neutral_dark": "#111827" if is_mall else "#212529",
        }

        steps.append(
            {
                "step": 2,
                "tool": "create_css_file",
                "params": {
                    "file_path": os.path.join(project_root, "assets/css/style.css"),
                    "content": "",
                    "palette": cafe_palette,
                },
                "description": "创建全局样式文件",
                "rationale": "提供设计系统、响应式、动画等基础样式，并注入更契合场景的品牌配色",
            }
        )
        steps.append(
            {
                "step": 3,
                "tool": "create_js_file",
                "params": {
                    "file_path": os.path.join(project_root, "assets/js/main.js"),
                    "content": "",
                },
                "description": "创建全局脚本文件",
                "rationale": "提供导航、滚动显示、返回顶部等基础交互",
            }
        )

        # 页面创建
        pretty_name = project_name.title()

        def build_single_page_sections() -> list[str]:
            """生成单页滚动式布局的各个版块"""
            hero_topic = "artisanal coffee shop interior, warm light, cinematic"
            lead_text = "星光级烘焙、当季风味和沉浸式空间，打造城市中的第三生活场景。"
            primary_cta = "查看菜单"
            secondary_cta = "预订座位"
            if is_mall:
                hero_topic = "luxury shopping mall atrium at night, cinematic lighting, visitors"
                lead_text = "星光购物中心聚合潮流零售、夜间餐饮与家庭娱乐，一站式点亮城市生活。"
                primary_cta = "了解亮点"
                secondary_cta = "预约参观"
            elif not is_restaurant:
                hero_topic = "modern business hero, gradient lighting, professional team"
                lead_text = "用策略、设计与工程思维，为品牌打造兼顾颜值与增长的数字体验。"
                primary_cta = "查看服务"
                secondary_cta = "联系团队"

            sections = [
                textwrap.dedent(
                    f"""
                    <header id="hero" class="hero hero-ultra hero-overlay section text-center" data-bg-topic="{hero_topic}" data-parallax="0.25">
                      <div class="overlay"></div>
                      <div class="container hero-inner">
                        <span class="badge badge-soft mb-3">全新体验</span>
                        <h1 class="display-5 mb-3">{pretty_name}</h1>
                        <p class="section-lead mx-auto">{lead_text}</p>
                        <div class="mt-4 d-flex justify-content-center gap-3 flex-wrap">
                          <a class="btn btn-gradient btn-lg px-4" href="#services">{primary_cta}</a>
                          <a class="btn btn-outline-light btn-lg px-4" href="#contact">{secondary_cta}</a>
                        </div>
                      </div>
                    </header>
                    """
                ).strip()
            ]

            if is_mall:
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="services" class="section">
                          <div class="container">
                            <div class="row g-4">
                              <div class="col-md-4">
                                <div class="feature-card glass h-100 p-4 reveal" data-tilt>
                                  <div class="icon-badge bg-warning mb-3">🌃</div>
                                  <h2 class="h5 mb-2">夜色生活目的地</h2>
                                  <p class="text-muted small mb-0">夜间餐饮、潮玩市集与沉浸演出齐聚，打造城市夜经济主场。</p>
                                </div>
                              </div>
                              <div class="col-md-4">
                                <div class="feature-card glass h-100 p-4 reveal" data-tilt>
                                  <div class="icon-badge bg-primary mb-3">🛍️</div>
                                  <h2 class="h5 mb-2">国际品牌旗舰矩阵</h2>
                                  <p class="text-muted small mb-0">200+ 国际与设计师品牌入驻，专属造型顾问与会员定制服务。</p>
                                </div>
                              </div>
                              <div class="col-md-4">
                                <div class="feature-card glass h-100 p-4 reveal" data-tilt>
                                  <div class="icon-badge bg-success mb-3">🎡</div>
                                  <h2 class="h5 mb-2">家庭娱乐社交场</h2>
                                  <p class="text-muted small mb-0">亲子探索乐园、家庭影院与艺术展演，满足全龄客群周末生活。</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="flagship" class="section section-alt">
                          <div class="container">
                            <h2 class="h3 text-center mb-4">主力店铺</h2>
                            <div class="row g-4">
                              <article class="col-lg-4">
                                <div class="card h-100 p-4 shadow-soft reveal" data-tilt>
                                  <img data-topic="luxury fashion flagship store interior" alt="星光旗舰时装馆" class="rounded-4 shadow-sm mb-3">
                                  <h3 class="h6 mb-2">星光旗舰时装馆</h3>
                                  <p class="text-muted small mb-0">轻奢首发系列、私享试衣间与造型顾问服务，重塑高端购物体验。</p>
                                </div>
                              </article>
                              <article class="col-lg-4">
                                <div class="card h-100 p-4 shadow-soft reveal" data-tilt>
                                  <img data-topic="gourmet food court night market neon" alt="夜焰美食街区" class="rounded-4 shadow-sm mb-3">
                                  <h3 class="h6 mb-2">夜焰美食街区</h3>
                                  <p class="text-muted small mb-0">40+ 全球料理、全天候营业与快闪主题活动，夜间精彩不停。</p>
                                </div>
                              </article>
                              <article class="col-lg-4">
                                <div class="card h-100 p-4 shadow-soft reveal" data-tilt>
                                  <img data-topic="family entertainment center modern play" alt="星空亲子探索乐园" class="rounded-4 shadow-sm mb-3">
                                  <h3 class="h6 mb-2">星空亲子探索乐园</h3>
                                  <p class="text-muted small mb-0">互动装置、科学实验与家庭影院，亲子共创灵感与回忆。</p>
                                </div>
                              </article>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="membership" class="section">
                          <div class="container">
                            <h2 class="h3 text-center mb-4">会员礼遇</h2>
                            <div class="row g-4">
                              <div class="col-md-4">
                                <div class="membership-card shadow-soft h-100 p-4 border-gradient">
                                  <h3 class="h6 mb-3">星耀卡 · ¥699 / 年</h3>
                                  <p class="text-muted small mb-0">免费停车 120 小时 · 生日礼遇 · 合作品牌限量优惠券。</p>
                                </div>
                              </div>
                              <div class="col-md-4">
                                <div class="membership-card shadow-soft h-100 p-4 border-gradient highlight">
                                  <h3 class="h6 mb-3">星耀黑金卡 · ¥1999 / 年</h3>
                                  <p class="text-muted small mb-0">私人购物顾问 · VIP 休息室 · 礼宾代客泊车 · 首发活动优先席位。</p>
                                </div>
                              </div>
                              <div class="col-md-4">
                                <div class="membership-card shadow-soft h-100 p-4 border-gradient">
                                  <h3 class="h6 mb-3">星悦家庭卡 · ¥1299 / 年</h3>
                                  <p class="text-muted small mb-0">亲子乐园畅玩 · 周末家庭影院 · 主题课程折扣与节日惊喜。</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="stories" class="section section-alt">
                          <div class="container">
                            <h2 class="h3 text-center mb-4">顾客见证</h2>
                            <div class="row g-4">
                              <article class="col-md-6">
                                <div class="testimonial-card glass h-100 p-4">
                                  <div class="d-flex align-items-center gap-3 mb-3">
                                    <img data-topic="fashion influencer portrait studio" alt="顾客" class="avatar rounded-circle shadow-sm">
                                    <div>
                                      <div class="fw-semibold">刘倩 · 时尚博主</div>
                                      <small class="text-muted">星耀黑金卡会员</small>
                                    </div>
                                  </div>
                                  <p class="text-muted small mb-0">“这里像是城市生活方式策展地，每月都能找到惊喜活动。”</p>
                                </div>
                              </article>
                              <article class="col-md-6">
                                <div class="testimonial-card glass h-100 p-4">
                                  <div class="d-flex align-items-center gap-3 mb-3">
                                    <img data-topic="happy asian family portrait lifestyle" alt="家庭用户" class="avatar rounded-circle shadow-sm">
                                    <div>
                                      <div class="fw-semibold">周末家庭 · 城市新锐</div>
                                      <small class="text-muted">星悦家庭卡会员</small>
                                    </div>
                                  </div>
                                  <p class="text-muted small mb-0">“亲子乐园与夜焰美食街已成为周末必打卡，活动福利超值。”</p>
                                </div>
                              </article>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )
            elif is_restaurant:
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="menu" class="section">
                          <div class="container">
                            <div class="row align-items-center g-5">
                              <div class="col-lg-5">
                                <h2 class="h3 mb-3">招牌菜单 · 星光甄选</h2>
                                <p class="text-muted">每日现烘豆种、季节限定特调与匠心甜点，恰到好处的甜与苦。</p>
                                <ul class="list-unstyled vstack gap-3 mt-4 text-muted small">
                                  <li>☕️ 精品单品手冲 · 果酸层次丰富</li>
                                  <li>🥐 法式可颂每日新鲜出炉</li>
                                  <li>🥤 冷萃与气泡咖啡带来夏日灵感</li>
                                </ul>
                              </div>
                              <div class="col-lg-7">
                                <div class="row g-4">
                                  <article class="col-sm-6">
                                    <div class="glass p-4 h-100 reveal" data-tilt>
                                      <img data-topic="signature latte art, golden hour" alt="拿铁" class="rounded shadow-sm mb-3">
                                      <div class="d-flex justify-content-between">
                                        <h3 class="h5 mb-0">星光拿铁</h3>
                                        <span class="badge bg-primary-subtle text-primary fw-semibold">¥36</span>
                                      </div>
                                      <p class="text-muted mt-2 small">丝滑奶泡配自家烘焙浓缩，口感层层递进。</p>
                                    </div>
                                  </article>
                                  <article class="col-sm-6">
                                    <div class="glass p-4 h-100 reveal" data-tilt>
                                      <img data-topic="pour over coffee setup minimal" alt="手冲咖啡" class="rounded shadow-sm mb-3">
                                      <div class="d-flex justify-content-between">
                                        <h3 class="h5 mb-0">北海道手冲</h3>
                                        <span class="badge bg-primary-subtle text-primary fw-semibold">¥42</span>
                                      </div>
                                      <p class="text-muted mt-2 small">慢萃 16 小时带来清爽果香与轻盈坚果尾韵。</p>
                                    </div>
                                  </article>
                                </div>
                              </div>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )
                sections.append(
                    textwrap.dedent(
                        f"""
                        <section id="about" class="section section-alt">
                          <div class="container">
                            <div class="row g-4 align-items-center">
                              <div class="col-lg-6">
                                <img data-topic="coffee roastery studio, warm tone" alt="{pretty_name} 空间" class="rounded-4 shadow-lg w-100">
                              </div>
                              <div class="col-lg-6">
                                <h2 class="h3 mb-3">空间故事 · 一杯咖啡的旅程</h2>
                                <p class="text-muted">我们从产地挑豆、烘焙到杯中，所有步骤都由资深咖啡师亲自把关，确保每一口都带着温度与惊喜。</p>
                                <div class="row g-3 mt-4 text-muted small">
                                  <div class="col-sm-6"><div class="glass p-3 h-100">🌱 直采可持续农场</div></div>
                                  <div class="col-sm-6"><div class="glass p-3 h-100">👩‍🍳 世界冠军团队驻店</div></div>
                                  <div class="col-sm-6"><div class="glass p-3 h-100">🎵 手工黑胶沉浸配乐</div></div>
                                  <div class="col-sm-6"><div class="glass p-3 h-100">📍 城市中最松弛的角落</div></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )
            else:
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="about" class="section">
                          <div class="container">
                            <div class="row g-4 align-items-center">
                              <div class="col-lg-5">
                                <h2 class="h3 mb-3">关于我们 · Strategy × Design × Tech</h2>
                                <p class="text-muted">十年数字化品牌经验，聚焦增长体验、可持续设计系统与落地执行力。</p>
                                <ul class="list-unstyled vstack gap-2 small text-muted">
                                  <li>✔️ 服务 80+ 创新品牌与上市企业</li>
                                  <li>✔️ 多端一致的组件化设计系统</li>
                                  <li>✔️ 数据驱动的转化优化闭环</li>
                                </ul>
                              </div>
                              <div class="col-lg-7">
                                <div class="row g-3">
                                  <div class="col-sm-6">
                                    <div class="glass p-4 h-100 reveal" data-tilt>
                                      <span class="display-5 fw-bold text-primary">98%</span>
                                      <p class="text-muted small mb-0">客户满意度，连续三年领跑行业。</p>
                                    </div>
                                  </div>
                                  <div class="col-sm-6">
                                    <div class="glass p-4 h-100 reveal" data-tilt>
                                      <span class="display-5 fw-bold text-primary">120+</span>
                                      <p class="text-muted small mb-0">完成项目，总计覆盖 12 个细分行业。</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )

            if not is_mall:
                sections.append(
                    textwrap.dedent(
                        """
                        <section id="services" class="section">
                          <div class="container">
                            <h2 class="h3 text-center mb-3">服务矩阵</h2>
                            <p class="section-lead text-center text-muted mb-5">从品牌策略、视觉系统到线上交付，一站式协同推进。</p>
                            <div class="row g-4">
                              <div class="col-md-4">
                                <div class="service-card glass p-4 h-100 reveal" data-tilt>
                                  <img data-topic="creative workshop, design sprint" alt="策略工作坊" class="rounded shadow-sm mb-3">
                                  <h3 class="h5">策略定位</h3>
                                  <p class="text-muted small mb-0">品牌北极星梳理、价值主张共创与产品架构重构。</p>
                                </div>
                              </div>
                              <div class="col-md-4">
                                <div class="service-card glass p-4 h-100 reveal" data-tilt>
                                  <img data-topic="modern ui design system" alt="设计系统" class="rounded shadow-sm mb-3">
                                  <h3 class="h5">设计系统</h3>
                                  <p class="text-muted small mb-0">跨平台组件库、主题配色、动态规范与品牌资产管理。</p>
                                </div>
                              </div>
                              <div class="col-md-4">
                                <div class="service-card glass p-4 h-100 reveal" data-tilt>
                                  <img data-topic="web development team collaboration" alt="工程交付" class="rounded shadow-sm mb-3">
                                  <h3 class="h5">工程落地</h3>
                                  <p class="text-muted small mb-0">高性能前端、内容管理、可观测性与持续迭代机制。</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </section>
                        """
                    ).strip()
                )

            sections.append(
                textwrap.dedent(
                    f"""
                    <section id="contact" class="section section-sm">
                      <div class="container">
                        <div class="row g-4 align-items-center">
                          <div class="col-lg-5">
                            <h2 class="h4 mb-3">马上联系 · 预约体验</h2>
                            <p class="text-muted">留下联系方式，我们将在 24 小时内回电，提供定制化方案。</p>
                            <ul class="list-unstyled small text-muted">
                              <li>📞 电话：400-123-4567</li>
                              <li>📍 地址：上海市静安区星光路 88 号</li>
                              <li>🕒 营业：周一至周日 09:00 - 22:00</li>
                            </ul>
                          </div>
                          <div class="col-lg-7">
                            <form class="glass p-4 rounded-4 shadow-sm row g-3">
                              <div class="col-md-6">
                                <label class="form-label">姓名</label>
                                <input type="text" class="form-control" placeholder="请输入姓名" required>
                              </div>
                              <div class="col-md-6">
                                <label class="form-label">联系方式</label>
                                <input type="tel" class="form-control" placeholder="手机或邮箱" required>
                              </div>
                              <div class="col-12">
                                <label class="form-label">需求概述</label>
                                <textarea class="form-control" rows="3" placeholder="请说明项目类型、预算或时间节点"></textarea>
                              </div>
                              <div class="col-12 d-grid">
                                <button class="btn btn-primary" type="submit">提交信息</button>
                              </div>
                            </form>
                          </div>
                        </div>
                      </div>
                    </section>
                    """
                ).strip()
            )

            sections.append(
                textwrap.dedent(
                    f"""
                    <footer class="footer-creative text-center py-4">
                      <div class="container small text-muted">
                        <div>{pretty_name} · 现代品牌体验实验室</div>
                        <div class="mt-1">© {datetime.now().year} All rights reserved.</div>
                      </div>
                    </footer>
                    """
                ).strip()
            )
            return sections

        single_page_sections = build_single_page_sections() if single_page_mode else None

        create_index_params = {
            "file_path": os.path.join(project_root, "index.html"),
            "title": pretty_name,
            "content": "",
            "style": "ultra_modern",
        }
        if single_page_sections:
            create_index_params["sections"] = single_page_sections

        steps.append(
            {
                "step": 4,
                "tool": "create_html_file",
                "params": create_index_params,
                "description": "创建首页",
                "rationale": "生成结构化HTML并挂接CSS/JS",
            }
        )

        if not single_page_mode:
            if is_restaurant:
                steps.append(
                    {
                        "step": 5,
                        "tool": "create_menu_page",
                        "params": {
                            "file_path": os.path.join(project_root, "menu.html"),
                            "project_name": pretty_name,
                        },
                        "description": "创建菜单页面",
                        "rationale": "餐饮类站点专用模板，分类清晰、价格醒目",
                    }
                )
                steps.append(
                    {
                        "step": 6,
                        "tool": "create_about_page",
                        "params": {
                            "file_path": os.path.join(project_root, "about.html"),
                            "project_name": pretty_name,
                            "context": {
                                "site_type": "restaurant",
                                "project_description": plan.get("task_analysis"),
                                "nav_items": build_nav("about.html"),
                            },
                        },
                        "description": "创建关于页面",
                        "rationale": "品牌故事、理念与团队展示",
                    }
                )
                steps.append(
                    {
                        "step": 7,
                        "tool": "create_contact_page",
                        "params": {
                            "file_path": os.path.join(project_root, "contact.html"),
                            "project_name": pretty_name,
                        },
                        "description": "创建联系页面",
                        "rationale": "营业时间、地址、联系表单与地图占位",
                    }
                )
            else:
                steps.append(
                    {
                        "step": 5,
                        "tool": "create_about_page",
                        "params": {
                            "file_path": os.path.join(project_root, "about.html"),
                            "project_name": pretty_name,
                            "context": {
                                "site_type": plan.get("site_type"),
                                "project_description": plan.get("task_analysis"),
                                "nav_items": build_nav("about.html"),
                            },
                        },
                        "description": "创建关于页面",
                        "rationale": "补充团队故事、理念与品牌背景",
                    }
                )
                steps.append(
                    {
                        "step": 6,
                        "tool": "create_html_file",
                        "params": {
                            "file_path": os.path.join(project_root, "services.html"),
                            "title": f"{pretty_name} · 服务体系",
                            "content": "",
                            "style": "creative_gradient",
                        },
                        "description": "创建服务页面",
                        "rationale": "呈现产品/服务矩阵与亮点",
                    }
                )
                steps.append(
                    {
                        "step": 7,
                        "tool": "create_html_file",
                        "params": {
                            "file_path": os.path.join(project_root, "contact.html"),
                            "title": f"{pretty_name} · 联系我们",
                            "content": "",
                            "style": "minimal_elegant",
                        },
                        "description": "创建联系页面",
                        "rationale": "提供表单、地图与联系方式",
                    }
                )

        # 框架与导航
        steps.append(
            {
                "step": 5 if single_page_mode else 8,
                "tool": "add_bootstrap",
                "params": {"project_path": project_root},
                "description": "接入Bootstrap以增强组件与响应式",
                "rationale": "快速获得导航栏、栅格与表单样式",
            }
        )

        if not single_page_mode:
            for idx, page in enumerate(
                ["index.html"]
                + (
                    ["menu.html", "about.html", "contact.html"]
                    if is_restaurant
                    else ["about.html", "services.html", "contact.html"]
                ),
                start=9,
            ):
                steps.append(
                    {
                        "step": idx,
                        "tool": "create_responsive_navbar",
                        "params": {
                            "file_path": os.path.join(project_root, page),
                            "brand_name": pretty_name,
                            "nav_items": build_nav(page),
                        },
                        "description": f"同步 {page} 导航",
                        "rationale": "保持跨页面导航一致、定位正确",
                    }
                )

        # 图片注入
        next_step = steps[-1]["step"] + 1
        if single_page_mode:
            if is_restaurant:
                sections_topics = ["signature coffee bar interior", "artisan baristas working", "minimalist cafe seating", "latte art macro"]
            elif is_mall:
                sections_topics = [
                    "luxury shopping mall atrium night, cinematic lighting",
                    "gourmet food court lifestyle photography",
                    "vip shopping lounge interior, warm lighting",
                    "family entertainment center vibrant"
                ]
            else:
                sections_topics = ["modern business team collaboration", "digital product design workspace", "technology innovation hub", "professional meeting room"]
            steps.append(
                {
                    "step": next_step,
                    "tool": "inject_images",
                    "params": {
                        "file_path": os.path.join(project_root, "index.html"),
                        "provider": "pollinations",
                        "topics": sections_topics,
                        "size": "1280x720",
                        "seed": 42,
                        "save": True,
                        "subdir": "assets/images",
                        "prefix": "index",
                    },
                    "description": "注入首页图片",
                    "rationale": "为单页面各版块填充视觉素材",
                }
            )
            next_step += 1
        else:
            steps.append(
                {
                    "step": next_step,
                    "tool": "inject_images",
                    "params": {
                        "file_path": os.path.join(project_root, "index.html"),
                        "provider": "pollinations",
                        "topics": ["cozy coffee hero, gradient glassmorphism"],
                        "size": "1200x800",
                        "seed": 42,
                        "save": True,
                        "subdir": "assets/images",
                        "prefix": "img",
                    },
                    "description": "首页图片注入",
                    "rationale": "让页面更具视觉表现",
                }
            )
            next_step += 1
            if is_restaurant:
                steps.append(
                    {
                        "step": next_step,
                        "tool": "inject_images",
                        "params": {
                            "file_path": os.path.join(project_root, "menu.html"),
                            "provider": "pollinations",
                            "topics": ["latte art", "espresso shot", "pastry dessert"],
                            "size": "1024x768",
                            "seed": 7,
                            "save": True,
                            "subdir": "assets/images",
                            "prefix": "menu",
                        },
                        "description": "为菜单页注入图片",
                        "rationale": "展示咖啡/甜点，更贴合餐饮场景",
                    }
                )
                next_step += 1
            steps.append(
                {
                    "step": next_step,
                    "tool": "inject_images",
                    "params": {
                        "file_path": os.path.join(project_root, "about.html"),
                        "provider": "pollinations",
                        "topics": ["barista portrait", "coffee roasting", "cafe community"],
                        "size": "1024x768",
                        "seed": 11,
                        "save": True,
                        "subdir": "assets/images",
                        "prefix": "about",
                    },
                    "description": "关于页图片注入",
                    "rationale": "呈现团队与品牌氛围",
                }
            )
            next_step += 1
            steps.append(
                {
                    "step": next_step,
                    "tool": "inject_images",
                    "params": {
                        "file_path": os.path.join(project_root, "contact.html"),
                        "provider": "pollinations",
                        "topics": ["coffee shop storefront", "map pin"],
                        "size": "1024x768",
                        "seed": 13,
                        "save": True,
                        "subdir": "assets/images",
                        "prefix": "contact",
                    },
                    "description": "联系页图片注入",
                    "rationale": "增强门店信息表现",
                }
            )
            next_step += 1

        # 校验与预览
        steps.append(
            {
                "step": next_step,
                "tool": "validate_html",
                "params": {"file_path": os.path.join(project_root, "index.html")},
                "description": "验证首页HTML结构",
                "rationale": "保证基础结构完整",
            }
        )
        next_step += 1
        if is_restaurant:
            steps.append(
                {
                    "step": next_step,
                    "tool": "validate_html",
                    "params": {"file_path": os.path.join(project_root, "menu.html")},
                    "description": "验证菜单页HTML结构",
                    "rationale": "避免语法问题",
                }
            )
            next_step += 1
        steps.append(
            {
                "step": next_step,
                "tool": "check_mobile_friendly",
                "params": {"file_path": os.path.join(project_root, "index.html")},
                "description": "检查移动端友好性",
                "rationale": "确认viewport与响应式",
            }
        )
        next_step += 1
        steps.append(
            {
                "step": next_step,
                "tool": "open_in_browser",
                "params": {"file_path": os.path.join(project_root, "index.html")},
                "description": "本地预览页面",
                "rationale": "快速查看效果（可在无头环境忽略）",
            }
        )

        return plan

    def _repair_plan_tools_sequence(self, plan: dict) -> dict:
        """修复模型返回的错误结构：
        - 有时会把步骤对象错放成顶层 key（如 "create_js_file": {...}）。
        - 这里尝试将这些对象归并回 tools_sequence。
        """
        if not isinstance(plan, dict):
            return plan

        single_page_mode = getattr(self, "force_single_page", False)

        seq = plan.get("tools_sequence")
        if not isinstance(seq, list):
            seq = []

        known = {
            "create_project_structure",
            "create_html_file",
            "create_css_file",
            "create_js_file",
            "add_bootstrap",
            "create_responsive_navbar",
            "fetch_generated_images",
            "inject_images",
            "open_in_browser",
            "validate_html",
            "check_mobile_friendly",
        }

        # 收集顶层误放的步骤
        extra_steps = []
        for key, val in list(plan.items()):
            if key in known and isinstance(val, dict):
                step_obj = dict(val)
                # 确保 tool 字段正确
                step_obj.setdefault("tool", key)
                # 只接受包含 params 的对象
                if not isinstance(step_obj.get("params"), (dict, str, type(None))):
                    continue
                extra_steps.append(step_obj)

        # 合并
        all_steps = []
        for obj in seq + extra_steps:
            if not isinstance(obj, dict):
                continue
            tool = obj.get("tool")
            if not tool:
                continue
            # 兜底字段
            obj.setdefault("step", len(all_steps) + 1)
            obj.setdefault("description", f"Run {tool}")
            if not isinstance(obj.get("params"), dict):
                # 将字符串参数尝试包装为 file_path
                p = obj.get("params")
                obj["params"] = {"file_path": p} if isinstance(p, str) else {}
            all_steps.append(obj)

        if single_page_mode:
            filtered_steps: list[dict] = []
            for obj in all_steps:
                tool = obj.get("tool")
                if tool in {
                    "create_menu_page",
                    "create_about_page",
                    "create_contact_page",
                    "create_responsive_navbar",
                }:
                    continue
                params = obj.get("params") if isinstance(obj.get("params"), dict) else {}
                file_path = params.get("file_path")
                if file_path and str(file_path).lower().endswith(".html"):
                    if os.path.basename(str(file_path)).lower() != "index.html":
                        continue
                filtered_steps.append(obj)
            all_steps = filtered_steps

        # 为导航中引用的页面补齐生成步骤（若规划中缺失）
        page_tools = {
            "create_html_file",
            "create_menu_page",
            "create_about_page",
            "create_contact_page",
        }

        existing_pages = set()
        for obj in all_steps:
            if obj.get("tool") in page_tools:
                params = (
                    obj.get("params") if isinstance(obj.get("params"), dict) else {}
                )
                file_path = params.get("file_path")
                if file_path:
                    existing_pages.add(os.path.basename(file_path))

        nav_required: dict[str, str] = {}
        nav_step_refs: list[tuple[int, int]] = []  # (index, step)
        nav_templates: list[dict[str, Any]] = []

        if not single_page_mode:
            for idx, obj in enumerate(all_steps):
                if obj.get("tool") != "create_responsive_navbar":
                    continue
                params = obj.get("params") if isinstance(obj.get("params"), dict) else {}
                nav_items = params.get("nav_items") or []
                if isinstance(nav_items, list):
                    cleaned_items = []
                    for item in nav_items:
                        if not isinstance(item, dict):
                            cleaned_items.append(item)
                            continue
                        href = str(item.get("href", "")).strip()
                        if href and href.lower().endswith(".html"):
                            normalized = href.lstrip("./")
                            basename = os.path.basename(normalized)
                            if basename != href:
                                item = dict(item)
                                item["href"] = basename
                            nav_required.setdefault(
                                basename, str(item.get("name") or basename)
                            )
                        cleaned_items.append(item)
                    params["nav_items"] = cleaned_items
                nav_step_refs.append((idx, obj.get("step", idx + 1)))
                nav_templates.append(
                    {
                        "params": copy.deepcopy(params) if isinstance(params, dict) else {},
                        "step": obj.get("step", idx + 1),
                    }
                )

        if nav_required:
            project_slug = plan.get("project_name") or "web-project"
            project_label = (
                project_slug.replace("-", " ").strip().title() or "Web Project"
            )
            # 选择插入位置：默认落在首个导航步骤之前
            insert_anchor = (
                min((s for _, s in nav_step_refs), default=len(all_steps) + 1)
                if nav_step_refs
                else len(all_steps) + 1
            )

            for offset, (href, label) in enumerate(nav_required.items()):
                basename = os.path.basename(href)
                if basename in existing_pages:
                    continue

                lower = basename.lower()
                if "about" in lower:
                    tool_name = "create_about_page"
                    params = {
                        "file_path": basename,
                        "project_name": project_label,
                    }
                elif any(key in lower for key in ["contact", "connect", "联系"]):
                    tool_name = "create_contact_page"
                    params = {"file_path": basename, "project_name": project_label}
                elif "menu" in lower:
                    tool_name = "create_menu_page"
                    params = {"file_path": basename, "project_name": project_label}
                else:
                    tool_name = "create_html_file"
                    params = {
                        "file_path": basename,
                        "title": f"{project_label} · {label}",
                        "content": "",
                        "style": "minimal_elegant",
                    }

                context_payload = {
                    "site_type": plan.get("site_type"),
                    "project_description": plan.get("task_analysis"),
                    "project_name": project_label,
                    "target_page": basename,
                }
                if nav_templates:
                    context_payload["nav_items"] = nav_templates[0]["params"].get(
                        "nav_items"
                    )

                if tool_name == "create_about_page":
                    params["context"] = context_payload

                new_step = {
                    "tool": tool_name,
                    "description": f"创建导航引用页面: {basename}",
                    "rationale": "确保导航链接的页面实际存在，避免访问404",
                    "params": params,
                    "step": insert_anchor - 0.5 + offset * 0.01,
                }
                all_steps.append(new_step)
                existing_pages.add(basename)

                # 为新创建的页面同步生成导航栏
                if nav_templates:
                    template_params = copy.deepcopy(nav_templates[0]["params"])
                    nav_items_tpl = template_params.get("nav_items") or []
                    cloned_items = []
                    for entry in nav_items_tpl:
                        if isinstance(entry, dict):
                            cloned = dict(entry)
                            cloned["active"] = cloned.get("href") == basename
                            cloned.setdefault("href", basename)
                            cloned_items.append(cloned)
                        else:
                            cloned_items.append(entry)
                    template_params["nav_items"] = cloned_items
                    template_params["file_path"] = basename
                    nav_step = {
                        "tool": "create_responsive_navbar",
                        "description": f"为 {basename} 注入统一导航",
                        "rationale": "保持跨页面导航一致性",
                        "params": template_params,
                        "step": insert_anchor - 0.4 + offset * 0.01,
                    }
                    all_steps.append(nav_step)

        # 为每一个页面创建步骤，确保紧跟一个 inject_images（未存在时自动追加）
        for idx, obj in list(enumerate(all_steps)):
            tool = obj.get("tool")
            if tool not in page_tools:
                continue
            params = obj.get("params") if isinstance(obj.get("params"), dict) else {}
            file_path = params.get("file_path")
            if not file_path:
                continue
            # 检查是否已有对应的注入步骤
            already = False
            for later in all_steps[idx + 1 :]:
                if later.get("tool") == "inject_images":
                    p = (
                        later.get("params")
                        if isinstance(later.get("params"), dict)
                        else {}
                    )
                    if p.get("file_path") == file_path:
                        already = True
                        break
            if already:
                continue
            prefix = os.path.splitext(os.path.basename(file_path))[0]
            inject_step = {
                "tool": "inject_images",
                "description": f"为页面注入智能生成的图片: {prefix}",
                "rationale": "保证每个页面 data-topic 占位得到实际图片，避免空白",
                "params": {
                    "file_path": file_path,
                    "provider": "pollinations",
                    "topics": None,
                    "size": "1200x800",
                    "seed": 42,
                    "save": False,
                    "subdir": "assets/images",
                    "prefix": prefix,
                },
                "step": obj.get("step", idx + 2),
            }
            # 插入紧随其后
            all_steps.insert(idx + 1, inject_step)

        # 按 step 排序并重新编号
        all_steps.sort(key=lambda x: x.get("step", 0))
        for i, obj in enumerate(all_steps, start=1):
            obj["step"] = i

        plan["tools_sequence"] = all_steps
        return plan

    def _display_execution_plan(self, plan: dict):
        """显示执行计划"""
        print("\n" + "=" * 60)
        print("📋 智能执行计划")
        print("=" * 60)
        print(f"🎯 任务分析: {plan.get('task_analysis', 'N/A')}")
        print(f"📁 项目名称: {plan.get('project_name', 'N/A')}")
        print(f"🎨 网站类型: {plan.get('site_type', 'N/A')}")
        print(f"🎭 设计风格: {plan.get('design_style', 'N/A')}")

        if "color_scheme" in plan:
            colors = plan["color_scheme"]
            print(
                f"🎨 配色方案: 主色 {colors.get('primary', 'N/A')} | 辅助 {colors.get('secondary', 'N/A')} | 强调 {colors.get('accent', 'N/A')}"
            )

        print(f"⏱️ 预计耗时: {plan.get('estimated_time', 'N/A')}")
        print(f"📊 总步骤数: {len(plan.get('tools_sequence', []))}")

        print(f"\n🛠️ 执行步骤预览:")
        for tool_spec in plan.get("tools_sequence", []):
            step = tool_spec.get("step", 0)
            description = tool_spec.get("description", "N/A")
            tool_name = tool_spec.get("tool", "unknown_tool")
            rationale = tool_spec.get("rationale", "")
            print(f"  {step}. {description} ({tool_name})")
            if rationale:
                print(f"     理由: {rationale}")

        print("💡 提示：HTML/CSS/JS 将在执行阶段逐步生成，可在每一步使用 d 查看详情。")
        print("=" * 60)

    def _get_user_confirmation(self, plan: dict) -> bool:
        """获取用户确认"""
        while True:
            try:
                confirm = input(f"\n✅ 是否执行此计划？(y/N/d): ").lower().strip()
            except EOFError:
                confirm = "n"

            if confirm in ["y", "yes"]:
                return True
            elif confirm in ["", "n", "no"]:
                return False
            elif confirm == "d":
                # 显示详细参数
                self._display_detailed_params(plan)
            else:
                print("请输入 y(执行)、n(取消) 或 d(查看详细参数)")

    def _display_detailed_params(self, plan: dict):
        """显示详细参数"""
        print("\n📝 详细参数预览:")
        for tool_spec in plan.get("tools_sequence", []):
            step = tool_spec.get("step", 0)
            print(f"\n步骤 {step}: {tool_spec.get('tool', 'N/A')}")
            print(
                f"参数: {json.dumps(tool_spec.get('params', {}), ensure_ascii=False, indent=2)}"
            )

            # 如果有content参数，单独显示
            if "content" in tool_spec.get("params", {}) and tool_spec.get(
                "params", {}
            ).get("content"):
                print("生成的代码内容:")
                content = tool_spec.get("params", {}).get("content", "")
                # 只显示前1000个字符
                if len(content) > 1000:
                    print(f"{content[:1000]}...")
                else:
                    print(content)

    def _execute_plan_with_recovery(
        self, plan: dict, confirm_each_step: bool = False, progress_callback=None
    ) -> List[dict]:
        """执行计划，带错误恢复机制 - 增强输出
        progress_callback: 可选回调，签名 progress_callback(dict)，用于上报：
          {type:'step'|'plan'|'done', status, step, total, percent, description, tool, message, rationale}
        """
        tools_sequence = plan.get("tools_sequence", [])
        total_steps = len(tools_sequence)
        results = []
        success_count = 0
        failed_critical = False

        for i, tool_spec in enumerate(tools_sequence):
            step = tool_spec.get("step", i + 1)
            tool_name = tool_spec.get("tool", "unknown_tool")
            raw_params = tool_spec.get("params", {})
            params = self._normalize_tool_params(tool_name, raw_params, plan)
            description = tool_spec.get("description", "N/A")

            # 显示进度
            progress = (i + 1) / total_steps * 100
            print(f"\n[{step}/{total_steps}] ({progress:.1f}%) {description}")
            print(f"🔧 执行工具: {tool_name}")

            skip_step = False
            user_cancelled = False

            if confirm_each_step:
                while True:
                    try:
                        preview = {
                            k: v
                            for k, v in (raw_params or {}).items()
                            if k in ("file_path", "project_path", "title")
                        }
                        ans = (
                            input(
                                f"继续执行步骤 {step}? (y=执行 / s=跳过 / d=详情 / q=终止) [{preview}]: "
                            )
                            .strip()
                            .lower()
                        )
                    except EOFError:
                        ans = "y"

                    if ans in ("", "y", "yes"):
                        break
                    if ans == "s":
                        results.append(
                            {
                                "step": step,
                                "tool": tool_name,
                                "status": "skipped",
                                "message": "用户跳过",
                                "description": description,
                            }
                        )
                        print("⏭️ 跳过此步骤")
                        skip_step = True
                        break
                    if ans == "d":
                        params = self._ensure_step_content(tool_spec, params, plan)
                        detail_params = tool_spec.get("params", {}) or {}
                        print(
                            f"参数详情: {json.dumps(detail_params, ensure_ascii=False, indent=2)}"
                        )
                        content_text = detail_params.get("content")
                        if content_text:
                            preview_text = content_text[:500]
                            print("内容预览（前500字符）：")
                            print("=" * 40)
                            print(preview_text)
                            if len(content_text) > 500:
                                print(f"... (共 {len(content_text)} 字符)")
                            print("=" * 40)
                        continue
                    if ans == "q":
                        print("⛔ 用户终止执行")
                        user_cancelled = True
                        break
                    print("请输入 y(执行)、s(跳过)、d(查看详情) 或 q(终止)")

                if user_cancelled:
                    break
                if skip_step:
                    continue

            params = self._ensure_step_content(tool_spec, params, plan)

            # 记录执行开始时间
            step_start_time = time.time()

            # 进度：步骤开始
            if callable(progress_callback):
                try:
                    progress_callback(
                        {
                            "type": "step",
                            "status": "start",
                            "step": step,
                            "total": total_steps,
                            "percent": (i / max(1, total_steps)) * 100.0,
                            "tool": tool_name,
                            "description": description,
                            "rationale": tool_spec.get("rationale"),
                        }
                    )
                except Exception:
                    pass

            # 执行工具（带重试）
            result = self._execute_tool_with_retry(tool_name, params, description, step)

            # 记录执行时间
            step_duration = time.time() - step_start_time
            result["duration"] = step_duration

            results.append(result)

            if result["status"] == "success":
                success_count += 1
                print(f"✅ 成功 ({step_duration:.2f}秒): {result['message']}")
                if callable(progress_callback):
                    try:
                        progress_callback(
                            {
                                "type": "step",
                                "status": "success",
                                "step": step,
                                "total": total_steps,
                                "percent": ((i + 1) / max(1, total_steps)) * 100.0,
                                "tool": tool_name,
                                "description": description,
                                "message": result.get("message"),
                            }
                        )
                    except Exception:
                        pass

                # 显示生成文件的路径和大小
                if "file_path" in params:
                    file_path = params["file_path"]
                    self.created_files.append(file_path)
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        print(f"   📁 文件: {file_path} ({size} 字节)")
            elif result["status"] == "skipped":
                print(f"⏭️ 跳过: {result['message']}")
            else:
                print(f"❌ 失败: {result['message']}")
                if callable(progress_callback):
                    try:
                        progress_callback(
                            {
                                "type": "step",
                                "status": "failed",
                                "step": step,
                                "total": total_steps,
                                "percent": ((i + 1) / max(1, total_steps)) * 100.0,
                                "tool": tool_name,
                                "description": description,
                                "message": result.get("message"),
                            }
                        )
                    except Exception:
                        pass
                # 显示详细错误信息
                if "error_detail" in result:
                    detail = result["error_detail"]
                    print(f"   错误类型: {detail.get('type')}")
                    print(f"   错误详情: {detail.get('message')}")
                    if self.verbose:
                        print(
                            f"   参数: {json.dumps(detail.get('params', {}), ensure_ascii=False, indent=2)[:500]}"
                        )

                # 检查是否是关键步骤
                if self._is_critical_step(tool_name):
                    print("⚠️ 关键步骤失败，停止执行")
                    failed_critical = True
                    break

            # 显示预计剩余时间
            if i < total_steps - 1:
                avg_time = sum(r.get("duration", 0) for r in results) / len(results)
                remaining_time = avg_time * (total_steps - i - 1)
                print(f"⏳ 预计剩余时间: {remaining_time:.1f}秒")

            print("-" * 50)

        # 进度：结束
        if callable(progress_callback):
            try:
                progress_callback(
                    {
                        "type": "done",
                        "status": "completed",
                        "percent": 100.0,
                        "description": "全部步骤完成",
                    }
                )
            except Exception:
                pass
        return results

    def _execute_tool_with_retry(
        self,
        tool_name: str,
        params: dict,
        description: str,
        step: int,
        max_retries: int = 2,
    ) -> dict:
        """执行工具，带重试机制 - 增强输出"""
        for attempt in range(max_retries):
            try:
                # 检查工具是否存在
                if tool_name not in self.tool_functions:
                    return {
                        "step": step,
                        "tool": tool_name,
                        "status": "failed",
                        "message": f"未知工具: {tool_name}",
                        "description": description,
                    }

                # 显示关键参数
                if "file_path" in params:
                    print(f"📁 文件路径: {params['file_path']}")
                if "title" in params:
                    print(f"📄 页面标题: {params['title']}")

                # === 新增：显示工具执行详情 ===
                if self.verbose:
                    print(f"\n🔍 执行详情:")
                    print(f"  - 工具: {tool_name}")
                    params_preview = json.dumps(params, ensure_ascii=False, indent=2)
                    if len(params_preview) > 500:
                        params_preview = params_preview[:500] + "..."
                    print(f"  - 参数: {params_preview}")

                # 执行工具
                result = self.tool_functions[tool_name](**params)

                # === 新增：显示实际生成的内容 ===
                if tool_name in [
                    "create_html_file",
                    "create_css_file",
                    "create_js_file",
                ]:
                    content = params.get("content", "")
                    if content and self.verbose:
                        print(f"\n📄 生成内容预览（前500字符）:")
                        print("=" * 40)
                        preview = content[:500] if len(content) > 500 else content
                        print(preview)
                        if len(content) > 500:
                            print(f"... (共 {len(content)} 字符)")
                        print("=" * 40)

                # 记录到历史
                self.execution_history.append(
                    {
                        "step": step,
                        "tool": tool_name,
                        "params": params,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # 保存到日志
                if self.save_output:
                    self._log(f"\n步骤 {step}: {tool_name}\n结果: {result}\n")

                # 成功后按需展示代码片段
                try:
                    if self.show_code and tool_name in (
                        "create_html_file",
                        "create_css_file",
                        "create_js_file",
                        "create_responsive_navbar",
                    ):
                        fp = params.get("file_path")
                        if isinstance(fp, str) and fp:
                            self._preview_file(fp)
                except Exception as _e:
                    # 预览失败不影响主流程
                    print(f"ℹ️  代码预览跳过: {str(_e)}")

                return {
                    "step": step,
                    "tool": tool_name,
                    "status": "success",
                    "message": result,
                    "description": description,
                }

            except Exception as e:
                # === 改进错误信息 ===
                error_msg = str(e)
                error_detail = traceback.format_exc()

                print(f"\n❌ 错误详情:")
                print(f"  - 工具: {tool_name}")
                print(f"  - 错误类型: {type(e).__name__}")
                print(f"  - 错误信息: {error_msg}")
                if self.verbose:
                    print(f"  - 堆栈跟踪:\n{error_detail[:1000]}")
                    params_preview = json.dumps(params, ensure_ascii=False, indent=2)
                    if len(params_preview) > 500:
                        params_preview = params_preview[:500] + "..."
                    print(f"  - 参数: {params_preview}")

                if attempt < max_retries - 1:
                    print(f"⚠️ 执行失败，重试中... ({attempt + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    # 返回更详细的错误信息
                    return {
                        "step": step,
                        "tool": tool_name,
                        "status": "failed",
                        "message": f"{type(e).__name__}: {error_msg}",
                        "error_detail": {
                            "type": type(e).__name__,
                            "message": error_msg,
                            "traceback": error_detail[:1000],
                            "params": params,
                        },
                        "description": description,
                    }

    def _is_critical_step(self, tool_name: str) -> bool:
        """判断是否是关键步骤"""
        critical_tools = ["create_project_structure", "create_html_file"]
        return tool_name in critical_tools

    def _run_consistency_review(self, plan: dict) -> None:
        if self.client is None:
            print("ℹ️ 自动巡检跳过：当前无可用模型。")
            return

        project_root = Path(self._project_root(plan)).resolve()
        if not project_root.exists():
            return

        collected: list[str] = []
        total_chars = 0
        max_chars = 8000
        for pattern in ("*.html", "*.css"):
            for fp in sorted(project_root.rglob(pattern)):
                if total_chars >= max_chars:
                    break
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore").strip()
                except Exception:
                    continue
                if not content:
                    continue
                snippet = content if len(content) <= 2000 else content[:2000] + "..."
                try:
                    rel = fp.relative_to(project_root)
                except ValueError:
                    rel = fp.name
                context_entry = f"[{rel}]\n{snippet}"
                collected.append(context_entry)
                total_chars += len(snippet)
            if total_chars >= max_chars:
                break

        if not collected:
            return

        outline = self._plan_outline_for_prompt(plan, limit=12)
        context_block = "\n\n".join(collected)
        prompt = textwrap.dedent(
            f"""
            你是一名资深前端代码审查专家，需要检查整个网站在设计语言、组件命名、排版、配色与可访问性方面是否一致。
            用户原始需求:
            {self.latest_user_request}

            执行纲要概览:
            {outline}

            以下是网站已生成的 HTML/CSS 核心文件，请结合整体风格给出需要统一或改进的要点，并提供简明行动建议:
            {context_block}
            """
        ).strip()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一名细致的前端代码审查专家，关注一致性、命名、排版与可访问性。",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            summary = response.choices[0].message.content.strip()
            print("\n🔍 自动巡检建议:")
            print(summary)
            if self.save_output:
                self._log(f"\n=== 自动巡检报告 ===\n{summary}\n")
        except Exception as exc:
            print(f"⚠️ 自动巡检失败: {exc}")
            if self.verbose:
                print(traceback.format_exc())

    def _generate_execution_report(self, plan: dict, results: List[dict]) -> str:
        """生成执行报告"""
        planned_total = len(plan.get("tools_sequence", []))
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        skipped_logged = sum(1 for r in results if r["status"] == "skipped")
        # 若中途终止，未执行的视为跳过
        skipped_missing = max(0, planned_total - len(results))
        skipped_count = skipped_logged + skipped_missing

        # 计算总执行时间
        total_duration = time.time() - self.execution_start_time

        print("\n" + "=" * 60)
        print("📊 执行报告")
        print("=" * 60)
        print(f"✅ 成功步骤: {success_count}/{planned_total}")
        print(f"❌ 失败步骤: {failed_count}/{planned_total}")
        print(f"⏭️ 跳过步骤: {skipped_count}/{planned_total}")
        print(f"⏱️ 总执行时间: {total_duration:.2f}秒")
        print(
            f"📁 项目位置: {self.project_directory}/{plan.get('project_name', 'N/A')}"
        )

        if self.created_files:
            print(f"\n📄 创建的文件:")
            for file_path in self.created_files:
                print(f"  - {file_path}")

        if success_count == planned_total and failed_count == 0:
            print("\n🌟 所有步骤执行成功！")
            status_msg = "完美完成"
        elif success_count > 0:
            print("\n⚠️ 部分步骤执行失败，请检查错误信息")
            status_msg = "部分完成"
        else:
            print("\n❌ 执行失败，请检查错误信息")
            status_msg = "执行失败"

        print("\n📋 详细结果:")
        for result in results:
            status_icon = (
                "✅"
                if result["status"] == "success"
                else "❌"
                if result["status"] == "failed"
                else "⏭️"
            )
            duration = result.get("duration", 0)
            print(
                f"  {status_icon} 步骤{result['step']}: {result['description']} ({duration:.2f}秒)"
            )
            if result["status"] == "failed":
                print(f"     错误: {result['message']}")

        denom = planned_total if planned_total else 1
        return f"\n🎉 执行完成！状态: {status_msg} | 成功率: {success_count}/{planned_total} ({success_count / denom * 100:.1f}%)"

    # ---------------- 代码预览工具 ----------------
    def _preview_file(
        self, file_path: str, max_lines: int = 120, max_chars: int = 10000
    ):
        """在控制台打印文件前若干行，避免刷屏"""
        try:
            if not os.path.exists(file_path):
                print(f"⚠️  预览失败：文件不存在 {file_path}")
                return
            print("\n" + "-" * 60)
            print(f"📄 代码预览: {file_path} (前 {max_lines} 行, ≤{max_chars} 字符)")
            print("-" * 60)
            printed = 0
            total_chars = 0
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if printed >= max_lines or total_chars >= max_chars:
                        break
                    # 避免超长行
                    if len(line) > 800:
                        line = line[:800] + "…\n"
                    print(line.rstrip("\n"))
                    printed += 1
                    total_chars += len(line)
            print("-" * 60)
            if printed == 0:
                print("(空文件或无法读取内容)")
            else:
                print(f"↑ 已显示 {printed} 行")
        except Exception as e:
            print(f"⚠️  预览异常: {str(e)}")

    def quick_templates(self):
        """提供快速模板选择"""
        templates = {
            "1": "创建一个现代化的个人作品集网站，展示我的设计作品",
            "2": "创建一个专业的企业官网，展示公司业务和服务",
            "3": "创建一个高端餐厅网站，包含菜单展示和预订功能",
            "4": "创建一个科技产品着陆页，强调产品特性和用户价值",
            "5": "创建一个教育培训网站，展示课程信息和师资力量",
            "6": "创建一个SaaS产品官网，突出功能特点和定价方案",
            "7": "创建一个时尚博客网站，注重内容展示和阅读体验",
            "8": "创建一个活动会议网站，包含日程安排和报名功能",
            "9": "创建一个公益组织网站，展示使命愿景和项目成果",
            "10": "创建一个创意工作室网站，体现创新和艺术感",
        }

        print("\n🎯 快速模板选择:")
        print("=" * 50)
        for key, desc in templates.items():
            print(f"  {key:2}. {desc}")
        print("=" * 50)

        choice = input("\n选择模板编号 (1-10) 或直接描述需求: ").strip()

        if choice in templates:
            selected = templates[choice]
            print(f"\n✅ 已选择: {selected}")
            return selected
        else:
            return choice

    def _enhance_user_input(self, user_input: str) -> str:
        """增强用户输入，添加默认质量要求"""
        # 检查是否已包含关键词
        quality_keywords = ["现代", "专业", "高质量", "响应式", "美观"]
        has_quality_req = any(keyword in user_input for keyword in quality_keywords)

        if not has_quality_req:
            # 添加默认质量要求
            enhanced = f"{user_input}。要求：现代化设计，响应式布局，专业美观，动画流畅，用户体验优秀。"
        else:
            enhanced = user_input

        return enhanced

    def _validate_plan(self, plan: dict) -> bool:
        """验证执行计划的完整性"""
        required_fields = ["task_analysis", "project_name", "tools_sequence"]
        for field in required_fields:
            if field not in plan:
                print(f"⚠️ 计划缺少必要字段: {field}")
                return False

        if (
            not isinstance(plan["tools_sequence"], list)
            or len(plan["tools_sequence"]) == 0
        ):
            print("⚠️ 工具序列为空或格式错误")
            return False

        return True

    # ---------------- 参数规范化与容错 ----------------
    def _project_root(self, plan: dict) -> str:
        project_name = plan.get("project_name", "project")
        return os.path.join(self.project_directory, project_name)

    def _is_inside(self, base: str, path: str) -> bool:
        try:
            base = os.path.abspath(base)
            path = os.path.abspath(path)
            return os.path.commonpath([base]) == os.path.commonpath([base, path])
        except Exception:
            return False

    def _normalize_tool_params(self, tool_name: str, params: dict, plan: dict) -> dict:
        params = dict(params or {})
        project_root = self._project_root(plan)

        # 强制 project_path 到项目根目录（用于 add_bootstrap 等）
        if tool_name in ["add_bootstrap"]:
            params["project_path"] = project_root

        # create_project_structure 固定为在工作目录下创建项目名目录
        if tool_name == "create_project_structure":
            params["project_name"] = plan.get("project_name")
            params["project_path"] = self.project_directory
            return params

        # 标准化 file_path
        if "file_path" in params:
            input_path = params.get("file_path") or ""
            # 若给的是目录，则兜底到 index.html
            if os.path.isdir(input_path):
                input_path = os.path.join(input_path, "index.html")

            # 将相对路径解析到项目根
            if not os.path.isabs(input_path):
                input_path = os.path.join(project_root, input_path)

            # 针对不同工具限定路径与扩展名
            if tool_name == "create_css_file":
                # 目标必须在 assets/css
                filename = os.path.basename(input_path) or "style.css"
                if not filename.endswith(".css"):
                    filename += ".css"
                input_path = os.path.join(project_root, "assets", "css", filename)

            elif tool_name == "create_js_file":
                filename = os.path.basename(input_path) or "main.js"
                if not filename.endswith(".js"):
                    filename += ".js"
                input_path = os.path.join(project_root, "assets", "js", filename)

            elif tool_name in [
                "create_html_file",
                "create_menu_page",
                "create_about_page",
                "create_contact_page",
                "validate_html",
                "check_mobile_friendly",
                "open_in_browser",
            ]:
                # 统一落在项目根，默认 index.html
                filename = os.path.basename(input_path) or "index.html"
                if not filename.endswith(".html"):
                    filename = "index.html"
                input_path = os.path.join(project_root, filename)

            # 最终确保在项目根内部
            if not self._is_inside(project_root, input_path):
                # 回退到项目内的合理位置
                if tool_name == "create_css_file":
                    input_path = os.path.join(
                        project_root, "assets", "css", "style.css"
                    )
                elif tool_name == "create_js_file":
                    input_path = os.path.join(project_root, "assets", "js", "main.js")
                elif tool_name in [
                    "create_html_file",
                    "create_menu_page",
                    "create_about_page",
                    "create_contact_page",
                    "validate_html",
                    "check_mobile_friendly",
                    "open_in_browser",
                    "create_responsive_navbar",
                ]:
                    input_path = os.path.join(project_root, "index.html")

            params["file_path"] = input_path

        # 规范化导航项（增强别名兼容）
        if tool_name == "create_responsive_navbar":
            nav_items = params.get("nav_items")
            if isinstance(nav_items, str):
                try:
                    nav_items = json.loads(nav_items)
                except Exception:
                    nav_items = None

            # 情况1：字符串数组 -> 结构化
            if (
                isinstance(nav_items, list)
                and nav_items
                and isinstance(nav_items[0], str)
            ):
                nav_items = [
                    {"name": name, "href": f"#{self._slugify(name)}", "active": i == 0}
                    for i, name in enumerate(nav_items)
                ]

            # 情况2：字典数组但使用了别名键 -> 归一化
            if (
                isinstance(nav_items, list)
                and nav_items
                and isinstance(nav_items[0], dict)
            ):
                normalized = []
                for i, item in enumerate(nav_items):
                    if not isinstance(item, dict):
                        normalized.append(
                            {"name": str(item), "href": "#", "active": i == 0}
                        )
                        continue
                    name = (
                        item.get("name")
                        or item.get("text")
                        or item.get("title")
                        or item.get("label")
                    )
                    href = item.get("href") or item.get("url") or item.get("link")
                    if not name:
                        name = f"导航{i + 1}"
                    if not href:
                        href = f"#{self._slugify(name)}"
                    active = item.get("active")
                    if active is None:
                        active = i == 0
                    normalized.append(
                        {"name": name, "href": href, "active": bool(active)}
                    )
                nav_items = normalized

            params["nav_items"] = nav_items

            cta = params.get("cta")
            if isinstance(cta, str):
                try:
                    cta = json.loads(cta)
                except Exception:
                    cta = None
            if isinstance(cta, dict):
                params["cta"] = cta
            else:
                params.pop("cta", None)

        if tool_name == "create_about_page":
            ctx = params.get("context")
            if isinstance(ctx, str):
                try:
                    ctx = json.loads(ctx)
                except Exception:
                    ctx = None
            if not isinstance(ctx, dict):
                ctx = None
            params["context"] = ctx

        # 对 fetch_generated_images：强制 project_path 为项目根；清洗 prompts
        if tool_name == "fetch_generated_images":
            params["project_path"] = project_root
            prm = params.get("prompts")
            if isinstance(prm, str):
                s = prm.strip()
                if s.startswith("["):
                    try:
                        prm = json.loads(s)
                    except Exception:
                        prm = [p.strip() for p in s.split(",") if p.strip()]
                else:
                    prm = [p.strip() for p in s.split(",") if p.strip()]
            if prm is not None and not isinstance(prm, list):
                prm = [str(prm)]
            params["prompts"] = prm

        # 对 inject_images：标准化 file_path，清洗 topics 列表
        if tool_name == "inject_images":
            # 若计划未提供具体页面，默认回退到首页
            target_path = params.get("file_path")
            if not target_path:
                params["file_path"] = os.path.join(project_root, "index.html")
            else:
                # 确保路径位于项目内且指向HTML文件
                normalized_path = target_path
                if not os.path.isabs(normalized_path):
                    normalized_path = os.path.join(project_root, normalized_path)
                if not normalized_path.endswith(".html"):
                    normalized_path = os.path.splitext(normalized_path)[0] + ".html"
                if not self._is_inside(project_root, normalized_path):
                    normalized_path = os.path.join(project_root, "index.html")
                params["file_path"] = normalized_path
            tps = params.get("topics")
            if isinstance(tps, str):
                s = tps.strip()
                if s.startswith("["):
                    try:
                        tps = json.loads(s)
                    except Exception:
                        tps = [p.strip() for p in s.split(",") if p.strip()]
                else:
                    tps = [p.strip() for p in s.split(",") if p.strip()]
            if tps is not None and not isinstance(tps, list):
                tps = [str(tps)]
            params["topics"] = tps

        # 对需要AI生成内容的工具，确保在联网模式下不沿用旧的 content
        if self.client is not None and self._step_requires_content(tool_name):
            if params.get("content"):
                params["content"] = ""

        # 最后一步：按工具白名单过滤参数，剔除 description/rationale 等无关键
        allowed = {
            "create_project_structure": {"project_name", "project_path"},
            "create_html_file": {"file_path", "title", "content", "style", "sections"},
            "create_css_file": {"file_path", "content"},
            "create_js_file": {"file_path", "content"},
            "add_bootstrap": {"project_path"},
            "create_responsive_navbar": {"file_path", "brand_name", "nav_items", "cta"},
            "create_about_page": {"file_path", "project_name", "context", "theme"},
            "fetch_generated_images": {
                "project_path",
                "provider",
                "prompts",
                "count",
                "size",
                "seed",
                "save",
                "subdir",
                "prefix",
            },
            "inject_images": {
                "file_path",
                "provider",
                "topics",
                "size",
                "seed",
                "save",
                "subdir",
                "prefix",
            },
            "validate_html": {"file_path"},
            "check_mobile_friendly": {"file_path"},
            "open_in_browser": {"file_path"},
        }.get(tool_name, set())

        if allowed:
            params = {k: v for k, v in params.items() if k in allowed}

        return params


@click.command()
@click.argument(
    "project_directory", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--model", default="qwen3-coder-plus-2025-09-23", help="AI模型选择")
@click.option("--template", is_flag=True, help="使用快速模板选择")
@click.option("--yes", is_flag=True, help="直接执行计划（跳过确认）")
@click.option(
    "--confirm-each/--no-confirm-each", default=True, help="每个步骤执行前进行确认"
)
@click.option(
    "--show-code/--no-show-code",
    default=False,
    help="在每个创建/修改文件的步骤后打印代码片段",
)
@click.option("--verbose", is_flag=True, help="显示详细执行信息")
@click.option("--save-output", is_flag=True, help="保存所有生成的内容到日志文件")
@click.option("--stream", is_flag=True, help="启用流式输出显示AI思考过程")
@click.option(
    "--single-page/--multi-page",
    default=True,
    help="强制生成单页面滚动站点；如需保留多页面流程可切换为 --multi-page",
)
def main(
    project_directory,
    model,
    template,
    yes,
    confirm_each,
    show_code,
    verbose,
    save_output,
    stream,
    single_page,
):
    """
    🧠 智能批量Web Agent - 2025年最佳实践

    特点：
    ✅ 预先规划 - 用户可以看到完整执行计划
    ✅ 成本可控 - 只需要1次API调用
    ✅ 灵活强大 - 支持复杂的自定义需求
    ✅ 逐步执行 - 每个步骤执行前可确认
    ✅ 流式输出 - 实时显示AI思考过程
    ✅ 详细输出 - 可查看生成的所有内容

    使用示例：
    python smart_web_agent.py ./projects
    python smart_web_agent.py ./projects --template
    python smart_web_agent.py ./projects --verbose --stream
    python smart_web_agent.py ./projects --yes --save-output
    """

    project_dir = os.path.abspath(project_directory)
    agent = SmartWebAgent(
        project_directory=project_dir,
        model=model,
        show_code=show_code,
        verbose=verbose,
        show_plan_stream=stream,
        save_output=save_output,
        force_single_page=single_page,
    )

    print("🧠 智能批量Web Agent启动！")
    print(f"📁 工作目录: {project_dir}")
    print(f"🤖 使用模型: {model}")
    print("⚡ 特点: 预先规划 + 逐步执行 = 成本可控 + 结果可预期")

    if show_code:
        print("👀 代码预览已开启：创建/修改文件后将展示前120行")
    if verbose:
        print("🔍 详细模式已开启：将显示详细执行信息和内容预览")
    if stream:
        print("⚡ 流式输出已开启：将实时显示AI思考过程")
    if save_output:
        print(f"💾 日志保存已开启：日志将保存到 agent_log_*.txt")

    print("\n" + "=" * 60)
    print("💡 使用说明：")
    print("1. 描述您的需求")
    print("2. AI分析并生成执行计划")
    print("3. 您确认计划后逐步执行")
    print("4. 每个步骤执行前可确认")
    print("=" * 60)

    while True:
        try:
            if template:
                user_input = agent.quick_templates()
                template = False  # 只在第一次使用
            else:
                user_input = input(
                    "\n🎯 请描述您的网页制作需求 (输入 'quit' 退出, 'template' 选择模板): "
                ).strip()

            if user_input.lower() in ["quit", "exit", "退出"]:
                print("👋 感谢使用智能批量Web Agent！")
                break

            if user_input.lower() == "template":
                user_input = agent.quick_templates()

            if not user_input:
                print("❌ 请输入具体需求")
                continue

            print("\n" + "🔄" * 20)
            # --yes 仅跳过“计划确认”，是否逐步确认由 --confirm-each 控制
            result = agent.run(
                user_input, auto_execute=yes, confirm_each_step=confirm_each
            )
            print("\n" + "🎉" * 20)
            print(result)

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            print("请重试或检查配置")


if __name__ == "__main__":
    main()
