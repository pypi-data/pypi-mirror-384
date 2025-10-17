#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速单页网站生成器 - 优化生成速度"""

from typing import Dict, Any, List
import json
import textwrap


class QuickSiteGenerator:
    """快速生成单页面网站的辅助类"""
    
    @staticmethod
    def create_single_page_plan(
        project_name: str,
        site_type: str,
        description: str
    ) -> Dict[str, Any]:
        """创建单页面网站的简化计划
        
        Args:
            project_name: 项目名称
            site_type: 网站类型（咖啡店、企业、作品集等）
            description: 用户需求描述
            
        Returns:
            简化的执行计划
        """
        
        # 基础步骤（所有类型通用）
        base_steps = [
            {
                "step": 1,
                "tool": "create_project_structure",
                "params": {
                    "project_name": project_name,
                    "project_path": "."
                },
                "description": "创建项目目录结构",
                "rationale": "建立规范的项目结构"
            },
            {
                "step": 2,
                "tool": "create_css_file",
                "params": {
                    "file_path": "assets/css/style.css"
                },
                "description": "创建样式文件",
                "rationale": "定义网站视觉风格"
            },
            {
                "step": 3,
                "tool": "create_js_file",
                "params": {
                    "file_path": "assets/js/main.js"
                },
                "description": "创建交互脚本",
                "rationale": "添加动态效果和交互"
            },
            {
                "step": 4,
                "tool": "create_html_file",
                "params": {
                    "file_path": "index.html",
                    "title": f"{project_name} - 首页",
                    "style": "ultra_modern",
                    "sections": QuickSiteGenerator._get_sections(
                        site_type, project_name, description
                    )
                },
                "description": "创建单页面网站主文件",
                "rationale": "生成包含所有内容的单页面"
            },
            {
                "step": 5,
                "tool": "add_bootstrap",
                "params": {
                    "project_path": "."
                },
                "description": "添加Bootstrap框架",
                "rationale": "加速响应式开发"
            },
            {
                "step": 6,
                "tool": "inject_images",
                "params": {
                    "file_path": "index.html",
                    "provider": "pollinations",
                    "topics": QuickSiteGenerator._get_image_topics(site_type),
                    "size": "1920x1080",
                    "save": True
                },
                "description": "注入AI生成图片",
                "rationale": "添加视觉内容"
            },
            {
                "step": 7,
                "tool": "open_in_browser",
                "params": {
                    "file_path": "index.html"
                },
                "description": "浏览器预览",
                "rationale": "查看最终效果"
            }
        ]
        
        # 根据网站类型定制配色
        color_scheme = QuickSiteGenerator._get_color_scheme(site_type)
        
        return {
            "task_analysis": f"快速生成{site_type}单页面网站",
            "project_name": project_name,
            "site_type": site_type,
            "design_style": "现代简洁",
            "color_scheme": color_scheme,
            "estimated_time": "2-3分钟",
            "tools_sequence": base_steps
        }

    @staticmethod
    def _get_sections(site_type: str, project_name: str, description: str) -> List[str]:
        """根据网站类型生成单页面的内容区块"""
        pretty_name = project_name.replace("-", " ").strip().title() or project_name
        lower_type = site_type.lower()
        is_cafe = any(keyword in lower_type for keyword in ["咖啡", "餐厅", "cafe", "coffee", "restaurant"])
        is_mall = any(keyword in lower_type for keyword in ["购物", "商场", "mall", "plaza", "retail"])

        summary = (description or "").strip().replace("\n", " ")
        if len(summary) > 120:
            summary = summary[:117] + "..."

        primary_cta = "了解亮点"
        secondary_cta = "预约参观"
        if is_cafe:
            hero_topic = "artisanal coffee shop interior, warm light, cozy atmosphere"
            default_intro = "精品烘焙、当季风味与沉浸式空间，让每一杯咖啡都成为值得记录的瞬间。"
            primary_cta = "查看菜单"
            secondary_cta = "预订座位"
        elif is_mall:
            hero_topic = "luxury shopping mall atrium at night, cinematic lighting, people shopping"
            default_intro = "星光购物中心集合潮流品牌、餐饮娱乐与沉浸式体验，一站式点亮城市生活。"
            primary_cta = "了解亮点"
            secondary_cta = "预约参观"
        else:
            hero_topic = "modern creative studio, gradient lighting, professional team"
            default_intro = "以策略、设计与工程为驱动，为品牌打造兼具审美与增长的数字体验。"
            primary_cta = "查看服务"
            secondary_cta = "联系团队"

        hero_section = textwrap.dedent(
            f"""
            <header id="hero" class="hero hero-ultra hero-overlay section text-center" data-bg-topic="{hero_topic}" data-parallax="0.22">
              <div class="overlay"></div>
              <div class="container hero-inner">
                <span class="badge badge-soft mb-3">全新体验上线</span>
                <h1 class="display-5 mb-3">{pretty_name}</h1>
                <p class="section-lead mx-auto">{summary or default_intro}</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap mt-4">
                  <a class="btn btn-gradient btn-lg px-4" href="#services">{primary_cta}</a>
                  <a class="btn btn-outline-light btn-lg px-4" href="#contact">{secondary_cta}</a>
                </div>
              </div>
            </header>
            """
        ).strip()

        sections: List[str] = [hero_section]

        if is_mall:
            sections.append(
                textwrap.dedent(
                    """
                    <section id="services" class="section">
                      <div class="container">
                        <div class="row g-4 align-items-stretch">
                          <div class="col-md-4">
                            <div class="feature-card glass h-100 p-4 reveal" data-tilt>
                              <div class="icon-badge bg-warning mb-3">🌃</div>
                              <h2 class="h5 mb-2">夜色生活目的地</h2>
                              <p class="text-muted small mb-0">精选网红餐饮、酒吧与夜市市集，营业至深夜，打造不夜城市心脏。</p>
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="feature-card glass h-100 p-4 reveal" data-tilt>
                              <div class="icon-badge bg-primary mb-3">🛍️</div>
                              <h2 class="h5 mb-2">国际潮流品牌矩阵</h2>
                              <p class="text-muted small mb-0">集合 200+ 国际与设计师品牌，提供季节限定快闪与 VIP 专属体验。</p>
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="feature-card glass h-100 p-4 reveal" data-tilt>
                              <div class="icon-badge bg-success mb-3">🎡</div>
                              <h2 class="h5 mb-2">家庭娱乐社交场</h2>
                              <p class="text-muted small mb-0">沉浸式亲子乐园、艺术展演与影院集群，同步举办主题活动与周末市集。</p>
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
                        <p class="section-lead text-center text-muted mb-5">精选品牌旗舰店与主题街区，打造全景式消费体验。</p>
                        <div class="row g-4">
                          <article class="col-lg-4">
                            <div class="card h-100 p-4 shadow-soft reveal" data-tilt>
                              <img data-topic="luxury fashion flagship store interior, soft lighting" alt="星光旗舰时尚馆" class="rounded-4 shadow-sm mb-3">
                              <h3 class="h6 mb-2">星光旗舰时尚馆</h3>
                              <ul class="text-muted small list-unstyled vstack gap-1">
                                <li>• 集结 30+ 国际轻奢品牌</li>
                                <li>• 私享试衣间与造型顾问</li>
                                <li>• 独家联名限量系列</li>
                              </ul>
                            </div>
                          </article>
                          <article class="col-lg-4">
                            <div class="card h-100 p-4 shadow-soft reveal" data-tilt>
                              <img data-topic="gourmet food court night market, neon lighting" alt="夜焰美食街区" class="rounded-4 shadow-sm mb-3">
                              <h3 class="h6 mb-2">夜焰美食街区</h3>
                              <ul class="text-muted small list-unstyled vstack gap-1">
                                <li>• 40+ 全球料理与主理人餐厅</li>
                                <li>• 24 小时营业，夜间限定菜单</li>
                                <li>• Live 音乐与沉浸式主题演出</li>
                              </ul>
                            </div>
                          </article>
                          <article class="col-lg-4">
                            <div class="card h-100 p-4 shadow-soft reveal" data-tilt>
                              <img data-topic="family entertainment center with interactive games, bright colors" alt="星空亲子探索乐园" class="rounded-4 shadow-sm mb-3">
                              <h3 class="h6 mb-2">星空亲子探索乐园</h3>
                              <ul class="text-muted small list-unstyled vstack gap-1">
                                <li>• 3000㎡ 沉浸式互动儿童乐园</li>
                                <li>• 每周主题教育与艺术工作坊</li>
                                <li>• 家庭影院与休闲书吧</li>
                              </ul>
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
                        <p class="section-lead text-center text-muted mb-5">尊享专属权益，体验尊贵服务与生活方式福利。</p>
                        <div class="row g-4">
                          <div class="col-md-4">
                            <div class="membership-card shadow-soft h-100 p-4 border-gradient">
                              <h3 class="h6 mb-3">星耀卡 · ¥699 / 年</h3>
                              <ul class="small text-muted list-unstyled vstack gap-1">
                                <li>• 免费停车 120 小时</li>
                                <li>• 生日专属礼包与积分翻倍</li>
                                <li>• 合作品牌限时优惠券</li>
                                <li>• 活动优先报名席位</li>
                              </ul>
                              <a class="btn btn-gradient w-100 mt-3" href="#contact">立即办理</a>
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="membership-card shadow-soft h-100 p-4 border-gradient highlight">
                              <h3 class="h6 mb-3">星耀黑金卡 · ¥1999 / 年</h3>
                              <ul class="small text-muted list-unstyled vstack gap-1">
                                <li>• 私人购物顾问与专属休息室</li>
                                <li>• 家庭影厅 / 艺术沙龙优先预约</li>
                                <li>• 免费代客泊车与礼宾服务</li>
                                <li>• 限量快闪及首发活动专属邀请</li>
                              </ul>
                              <a class="btn btn-dark-gradient w-100 mt-3" href="#contact">预约办理</a>
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="membership-card shadow-soft h-100 p-4 border-gradient">
                              <h3 class="h6 mb-3">星悦家庭卡 · ¥1299 / 年</h3>
                              <ul class="small text-muted list-unstyled vstack gap-1">
                                <li>• 亲子乐园畅玩与课程折扣</li>
                                <li>• 周末家庭影院专属包场</li>
                                <li>• 健康管理&运动社群活动</li>
                                <li>• 节日专属定制惊喜</li>
                              </ul>
                              <a class="btn btn-outline-primary w-100 mt-3" href="#contact">了解详情</a>
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
                                <img data-topic="fashion influencer woman portrait, studio lighting" alt="顾客" class="avatar rounded-circle shadow-sm">
                                <div>
                                  <div class="fw-semibold">刘倩 · 时尚博主</div>
                                  <small class="text-muted">常驻 VIP 会员</small>
                                </div>
                              </div>
                              <p class="text-muted small mb-0">“星光购物中心不仅是购物目的地，更是城市生活方式的策展地。每月都有新惊喜。”</p>
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
                              <p class="text-muted small mb-0">“孩子最喜欢亲子探索乐园，周末打卡电影院与艺术工坊，已经成为我们的固定行程。”</p>
                            </div>
                          </article>
                        </div>
                      </div>
                    </section>
                    """
                ).strip()
            )

        elif is_cafe:
            sections.append(
                textwrap.dedent(
                    """
                    <section id="menu" class="section">
                      <div class="container">
                        <h2 class="h3 text-center mb-4">招牌菜单</h2>
                        <p class="section-lead text-center text-muted mb-5">慢火烘焙、手工调制与限定甜点，在这里相遇。</p>
                        <div class="row g-4">
                          <article class="col-md-4">
                            <div class="glass p-4 h-100 reveal" data-tilt>
                              <img data-topic="signature latte art with croissant" alt="手工拿铁" class="rounded shadow-sm mb-3">
                              <h3 class="h6 mb-1">手工拿铁</h3>
                              <p class="text-muted small mb-0">自家烘焙豆搭配丝滑绵密奶泡，入口香气层层绽放。</p>
                            </div>
                          </article>
                          <article class="col-md-4">
                            <div class="glass p-4 h-100 reveal" data-tilt>
                              <img data-topic="pour over coffee minimal setup" alt="单品手冲" class="rounded shadow-sm mb-3">
                              <h3 class="h6 mb-1">单品手冲</h3>
                              <p class="text-muted small mb-0">严选产区豆种与手冲曲线，呈现清晰果酸与花香层次。</p>
                            </div>
                          </article>
                          <article class="col-md-4">
                            <div class="glass p-4 h-100 reveal" data-tilt>
                              <img data-topic="dessert display minimal cafe" alt="限定甜品" class="rounded shadow-sm mb-3">
                              <h3 class="h6 mb-1">限定甜品</h3>
                              <p class="text-muted small mb-0">每日新鲜出炉的法式甜点，与咖啡香气打造完美平衡。</p>
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
                    <section id="about" class="section section-alt">
                      <div class="container">
                        <div class="row g-4 align-items-center">
                          <div class="col-lg-6">
                            <img data-topic="coffee shop barista team smiling" alt="咖啡师团队" class="rounded-4 shadow-lg w-100">
                          </div>
                          <div class="col-lg-6">
                            <h2 class="h3 mb-3">关于我们 · 一杯咖啡的旅程</h2>
                            <p class="text-muted">从产地杯测、烘焙曲线到杯中呈现，我们坚持手作与温度，打造城市中最松弛的第三生活空间。</p>
                            <ul class="list-unstyled vstack gap-2 text-muted small mb-0">
                              <li>✔️ SCA 认证咖啡师与烘焙师团队</li>
                              <li>✔️ 直采可持续农场豆种，月度主题更新</li>
                              <li>✔️ 定制音乐与香氛，营造层次丰富的沉浸体验</li>
                            </ul>
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
                    <section id="services" class="section">
                      <div class="container">
                        <div class="row g-4">
                          <div class="col-lg-5">
                            <h2 class="h3 mb-3">空间亮点</h2>
                            <p class="text-muted">无论是独处阅读、灵感共创还是快闪活动，我们都为你准备好了理想场景。</p>
                            <div class="d-flex flex-column gap-3 text-muted small">
                              <div class="glass p-3 rounded-4">🌿 原木系家具与植物搭配，营造自然呼吸感</div>
                              <div class="glass p-3 rounded-4">⚡ 全场高速 Wi-Fi 与充电座，随时投入创作</div>
                              <div class="glass p-3 rounded-4">🎧 低语音控制 + 细分区域，兼顾独处与社交</div>
                            </div>
                          </div>
                          <div class="col-lg-7">
                            <img data-topic="cozy cafe interior with plants" alt="店内环境" class="rounded-4 shadow-lg w-100">
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
                    f"""
                    <section id="about" class="section">
                      <div class="container">
                        <div class="row g-4 align-items-center">
                          <div class="col-lg-5">
                            <h2 class="h3 mb-3">关于我们 · Strategy × Design × Tech</h2>
                            <p class="text-muted">服务来自科技、消费、企业服务等多个行业的伙伴，擅长以系统化方法论驱动品牌增长。</p>
                            <ul class="list-unstyled vstack gap-2 text-muted small mb-0">
                              <li>✔️ 8+ 年数字化品牌建设经验</li>
                              <li>✔️ 120+ 成功案例覆盖 12 个细分领域</li>
                              <li>✔️ 与 {pretty_name} 一同打造可持续的体验资产</li>
                            </ul>
                          </div>
                          <div class="col-lg-7">
                            <img data-topic="modern creative studio teamwork" alt="团队协作" class="rounded-4 shadow-lg w-100">
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
                    <section id="services" class="section section-alt">
                      <div class="container">
                        <h2 class="h3 text-center mb-3">核心服务</h2>
                        <p class="section-lead text-center text-muted mb-5">用一体化团队，将商业目标转化为可感知的用户体验。</p>
                        <div class="row g-4">
                          <div class="col-md-4">
                            <div class="glass p-4 h-100 reveal" data-tilt>
                              <img data-topic="brand strategy workshop" alt="品牌策略" class="rounded shadow-sm mb-3">
                              <h3 class="h6 mb-1">品牌策略</h3>
                              <p class="text-muted small mb-0">市场洞察、价值主张、用户旅程梳理与品牌调性定义。</p>
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="glass p-4 h-100 reveal" data-tilt>
                              <img data-topic="design system ui kit" alt="设计系统" class="rounded shadow-sm mb-3">
                              <h3 class="h6 mb-1">设计系统</h3>
                              <p class="text-muted small mb-0">多端统一的组件资产、主题配色、动效规范与文档体系。</p>
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="glass p-4 h-100 reveal" data-tilt>
                              <img data-topic="web development collaboration" alt="工程交付" class="rounded shadow-sm mb-3">
                              <h3 class="h6 mb-1">工程交付</h3>
                              <p class="text-muted small mb-0">高性能 Web 前端、可视化内容管理与持续迭代支持。</p>
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
                    <section id="cases" class="section">
                      <div class="container">
                        <div class="row g-4 align-items-center">
                          <div class="col-lg-6">
                            <img data-topic="business team presentation success" alt="项目成果" class="rounded-4 shadow-lg w-100">
                          </div>
                          <div class="col-lg-6">
                            <h2 class="h3 mb-3">客户赞誉</h2>
                            <p class="text-muted">我们与成长型品牌和上市公司保持长期合作，用数据验证每一次设计决策。</p>
                            <div class="glass p-4 rounded-4 text-muted small">
                              <p class="mb-2">“团队在两周内交付了全新的品牌站点，性能与转化率均超出预期。”</p>
                              <div class="fw-semibold">— 合作伙伴 CEO</div>
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
                <section id="contact" class="section section-sm">
                  <div class="container">
                    <div class="row g-4 align-items-center">
                      <div class="col-lg-5">
                        <h2 class="h4 mb-3">预约体验</h2>
                        <p class="text-muted">填写表单或直接通过电话/邮件与我们联系，获取专属方案。</p>
                        <ul class="list-unstyled text-muted small mb-0">
                          <li>📞 电话：400-123-4567</li>
                          <li>📧 邮箱：hello@example.com</li>
                          <li>📍 地址：上海市静安区灵感路 88 号</li>
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
                            <input type="text" class="form-control" placeholder="邮箱或手机号" required>
                          </div>
                          <div class="col-12">
                            <label class="form-label">需求描述</label>
                            <textarea class="form-control" rows="3" placeholder="请描述项目目标与时间节点"></textarea>
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
                    <div>{pretty_name} · All Rights Reserved</div>
                    <div class="mt-1">Designed for modern single-page experiences.</div>
                  </div>
                </footer>
                """
            ).strip()
        )

        return [section for section in sections if section]
    
    @staticmethod
    def _get_image_topics(site_type: str) -> List[str]:
        """根据网站类型返回图片主题"""
        
        topics_map = {
            "咖啡": ["coffee shop interior modern", "latte art", "coffee beans", "cozy cafe"],
            "餐厅": ["restaurant interior elegant", "gourmet food", "dining table", "chef cooking"],
            "企业": ["modern office", "business team", "corporate building", "technology workspace"],
            "作品集": ["creative workspace", "design portfolio", "artistic studio", "digital art"],
            "电商": ["product showcase", "online shopping", "ecommerce", "shopping cart"],
            "博客": ["writing desk", "laptop workspace", "books and coffee", "minimal desk setup"],
            "购物": [
                "luxury shopping mall atrium, cinematic lighting",
                "night market food street, neon",
                "family entertainment center modern",
                "vip shopping lounge interior"
            ],
            "商场": [
                "retail fashion flagship store interior",
                "premium shopping mall exterior evening",
                "gourmet food court lifestyle",
                "interactive family entertainment zone"
            ],
            "mall": [
                "modern shopping mall architecture",
                "luxury retail display glass storefront",
                "shopping mall lounge cafe",
                "city shopping plaza aerial night"
            ]
        }

        # 查找匹配的主题
        for key, topics in topics_map.items():
            if key in site_type:
                return topics
        for key, topics in topics_map.items():
            if key in site_type.lower():
                return topics

        # 默认主题
        return ["modern website hero", "business concept", "technology background", "professional workspace"]
    
    @staticmethod
    def _get_color_scheme(site_type: str) -> Dict[str, str]:
        """根据网站类型返回配色方案"""
        
        schemes = {
            "咖啡": {
                "primary": "#6F4E37",  # 咖啡棕
                "secondary": "#C8A882",  # 奶泡色
                "accent": "#D2691E"  # 焦糖色
            },
            "餐厅": {
                "primary": "#8B0000",  # 深红
                "secondary": "#FFD700",  # 金色
                "accent": "#228B22"  # 森林绿
            },
            "企业": {
                "primary": "#003366",  # 企业蓝
                "secondary": "#F0F0F0",  # 浅灰
                "accent": "#FF6B35"  # 橙色
            },
            "作品集": {
                "primary": "#2C3E50",  # 深蓝灰
                "secondary": "#ECF0F1",  # 云白
                "accent": "#E74C3C"  # 红色
            },
            "电商": {
                "primary": "#FF6B6B",  # 珊瑚红
                "secondary": "#4ECDC4",  # 青绿
                "accent": "#FFE66D"  # 黄色
            }
        }
        
        # 查找匹配的配色
        for key, scheme in schemes.items():
            if key in site_type:
                return scheme
        
        # 默认配色（现代通用）
        return {
            "primary": "#3B82F6",  # 蓝色
            "secondary": "#F3F4F6",  # 浅灰
            "accent": "#10B981"  # 绿色
        }
    
    @staticmethod
    def optimize_for_speed(plan: Dict[str, Any]) -> Dict[str, Any]:
        """优化计划以提升生成速度
        
        - 移除不必要的验证步骤
        - 简化图片生成
        - 减少工具调用次数
        """
        optimized_steps = []
        
        for step in plan.get("tools_sequence", []):
            tool = step.get("tool", "")
            
            # 跳过验证类工具（可选）
            if tool in ["validate_html", "check_mobile_friendly"]:
                continue
                
            # 简化图片参数
            if tool == "inject_images":
                params = step.get("params", {})
                # 限制图片数量
                if "topics" in params and len(params["topics"]) > 3:
                    params["topics"] = params["topics"][:3]
                # 使用较小的尺寸
                if "size" in params:
                    params["size"] = "1280x720"
                step["params"] = params
            
            optimized_steps.append(step)
        
        plan["tools_sequence"] = optimized_steps
        plan["estimated_time"] = "1-2分钟"
        
        return plan
