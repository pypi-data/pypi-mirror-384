"""改进版页面模板工具 - 支持 AI 生成和个性化内容"""
from __future__ import annotations

import html
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List


def create_menu_page(
    file_path: str, 
    project_name: str | None = None,
    context: Dict[str, Any] | None = None,
    ai_content: Dict[str, Any] | None = None
) -> str:
    """创建餐厅/咖啡店的"菜单"页面 - 支持 AI 生成内容
    
    Args:
        file_path: 目标HTML文件路径
        project_name: 项目名称
        context: 项目上下文信息（描述、特色、位置等）
        ai_content: AI 生成的菜单内容（可选）
    """
    brand = (project_name or "Coffee & Menu").strip()
    title = f"{brand} · 菜单 Menu"
    ctx = context or {}
    
    # 如果提供了 AI 生成的内容，使用它；否则生成智能默认值
    if ai_content and "categories" in ai_content:
        menu_data = ai_content
    else:
        menu_data = _generate_smart_menu_defaults(brand, ctx)
    
    # 生成菜单HTML
    menu_sections = ""
    for idx, category in enumerate(menu_data.get("categories", [])):
        section_class = "section section-alt" if idx % 2 == 1 else "section"
        category_name = category.get("name", "菜单")
        items_html = ""
        
        for item in category.get("items", []):
            items_html += f"""
          <article class="menu-card reveal col-md-4">
            <img data-topic="{html.escape(item.get('image_topic', item.get('name', 'menu item')))}" 
                 alt="{html.escape(item.get('name', ''))}" 
                 class="img-fluid rounded shadow-sm">
            <div class="d-flex justify-content-between align-items-center mt-3">
              <h3 class="h5 mb-0">{html.escape(item.get('name', ''))}</h3>
              <span class="price">{html.escape(str(item.get('price', '')))}</span>
            </div>
            <p class="text-muted mt-2">{html.escape(item.get('description', ''))}</p>
          </article>"""
        
        menu_sections += f"""
    <section class="{section_class}" id="category-{idx}">
      <div class="container">
        <h2 class="h3 text-center mb-4">{html.escape(category_name)}</h2>
        <div class="row g-4">
{items_html}
        </div>
      </div>
    </section>"""
    
    # 生成导航标签
    nav_pills = ""
    for idx, category in enumerate(menu_data.get("categories", [])):
        active_class = "active" if idx == 0 else ""
        nav_pills += f"""
          <li class="nav-item">
            <a class="nav-link {active_class}" href="#category-{idx}">
              {html.escape(category.get('name', ''))}
            </a>
          </li>"""
    
    # 获取页面描述和副标题
    page_description = ctx.get('menu_description', menu_data.get('description', '精品咖啡与精致甜点的完美搭配'))
    
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="assets/css/style.css" />
</head>
<body>
  <header class="hero hero-ultra section text-center" 
          data-bg-topic="{ctx.get('hero_bg_topic', 'cozy coffee shop interior, warm light')}" 
          id="home">
    <div class="container hero-inner">
      <span class="badge badge-soft mb-3">菜单 MENU</span>
      <h1 class="display-5 mb-2">{html.escape(brand)}</h1>
      <p class="section-lead mx-auto">{html.escape(page_description)}</p>
    </div>
  </header>

  <main>
    <nav class="section section-sm" aria-label="菜单分类导航">
      <div class="container">
        <ul class="nav nav-pills justify-content-center gap-2">
{nav_pills}
        </ul>
      </div>
    </nav>

{menu_sections}
  </main>

  <footer class="footer-minimal">
    <div class="container">
      <div class="footer-brand">
        <span>{html.escape(brand)}</span>
        <p>{html.escape(ctx.get('footer_text', 'See you in our cafe'))}</p>
      </div>
      <div class="footer-meta">
        <span>© {html.escape(brand)}</span>
        <a href="mailto:{html.escape(ctx.get('email', 'hello@example.com'))}">
          {html.escape(ctx.get('email', 'hello@example.com'))}
        </a>
      </div>
    </div>
  </footer>
  <script src="assets/js/main.js"></script>
</body>
</html>"""
    
    # 保存文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    
    return f"菜单页面已创建：{file_path}"


def _generate_smart_menu_defaults(brand: str, context: Dict) -> Dict:
    """根据项目类型生成智能的默认菜单"""
    description = str(context.get('description', '')).lower()
    features = str(context.get('features', '')).lower()
    
    # 根据关键词判断项目类型并生成相应菜单
    if '咖啡' in description or 'coffee' in description or '咖啡' in brand:
        # 咖啡店菜单
        categories = [
            {
                "name": "精品咖啡",
                "items": [
                    {
                        "name": f"{brand}特调",
                        "price": "¥ 42",
                        "description": f"独家配方，{brand}的招牌饮品",
                        "image_topic": "signature coffee drink"
                    },
                    {
                        "name": "手冲单品",
                        "price": "¥ 38-68",
                        "description": "每日精选单一产区咖啡豆，手工冲泡",
                        "image_topic": "pour over coffee"
                    },
                    {
                        "name": "意式浓缩",
                        "price": "¥ 28",
                        "description": "经典意式，醇厚浓郁",
                        "image_topic": "espresso shot"
                    }
                ]
            },
            {
                "name": "轻食甜点",
                "items": [
                    {
                        "name": "招牌蛋糕",
                        "price": "¥ 35",
                        "description": "每日新鲜烘焙，搭配咖啡的完美选择",
                        "image_topic": "cake dessert"
                    }
                ]
            }
        ]
    elif '餐厅' in description or 'restaurant' in description:
        # 餐厅菜单
        categories = [
            {
                "name": "招牌主菜",
                "items": [
                    {
                        "name": f"{brand}招牌菜",
                        "price": "¥ 88",
                        "description": "主厨特别推荐，独家秘制",
                        "image_topic": "signature dish"
                    }
                ]
            }
        ]
    elif '茶' in description or 'tea' in description:
        # 茶馆菜单
        categories = [
            {
                "name": "精选好茶",
                "items": [
                    {
                        "name": "特级龙井",
                        "price": "¥ 58/壶",
                        "description": "明前龙井，清香淡雅",
                        "image_topic": "green tea"
                    }
                ]
            }
        ]
    else:
        # 通用服务菜单
        categories = [
            {
                "name": "服务项目",
                "items": [
                    {
                        "name": "基础套餐",
                        "price": "咨询报价",
                        "description": "包含标准服务流程",
                        "image_topic": "service package"
                    }
                ]
            }
        ]
    
    # 如果上下文中有具体的菜单项，添加进去
    if 'menu_items' in context:
        # 合并用户提供的菜单项
        user_items = context['menu_items']
        if isinstance(user_items, list) and user_items:
            categories[0]['items'].extend(user_items[:3])  # 最多添加3个
    
    return {
        "categories": categories,
        "description": context.get('menu_description', '为您提供优质的产品与服务')
    }


def create_about_page(
    file_path: str,
    project_name: str | None = None,
    context: Dict[str, Any] | None = None,
    ai_content: Dict[str, Any] | None = None
) -> str:
    """创建"关于我们"页面 - 支持 AI 生成内容
    
    Args:
        file_path: 目标HTML文件路径
        project_name: 项目名称  
        context: 项目上下文信息
        ai_content: AI 生成的关于页面内容（可选）
    """
    brand = (project_name or "Modern Brand").strip()
    ctx = context or {}
    
    # 使用 AI 内容或生成默认内容
    if ai_content:
        content_data = ai_content
    else:
        content_data = _generate_about_defaults(brand, ctx)
    
    # 生成品牌故事区块
    story_html = ""
    if content_data.get('story'):
        story_html = f"""
  <section class="section" id="story">
    <div class="container">
      <div class="row g-5 align-items-center">
        <div class="col-lg-6">
          <div class="vision-capsule reveal">
            <span class="eyebrow">品牌故事</span>
            <h2 class="h3">{html.escape(content_data['story'].get('title', '我们的故事'))}</h2>
            <p class="text-muted">{html.escape(content_data['story'].get('content', ''))}</p>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="vision-media reveal" 
               data-bg-topic="{html.escape(content_data['story'].get('image_topic', 'brand story'))}">
          </div>
        </div>
      </div>
    </div>
  </section>"""
    
    # 生成核心价值观区块
    values_html = ""
    if content_data.get('values'):
        values_list = ""
        for value in content_data['values']:
            values_list += f"<li>{html.escape(value)}</li>\n"
        
        values_html = f"""
  <section class="section section-alt" id="values">
    <div class="container">
      <h2 class="h3 text-center mb-4">核心价值观</h2>
      <ul class="list-check mx-auto" style="max-width: 600px;">
        {values_list}
      </ul>
    </div>
  </section>"""
    
    # 生成团队介绍区块
    team_html = ""
    if content_data.get('team'):
        team_cards = ""
        for member in content_data['team']:
            team_cards += f"""
        <article class="team-card reveal col-md-3">
          <img data-topic="{html.escape(member.get('image_topic', 'team member portrait'))}" 
               alt="{html.escape(member.get('role', ''))}" 
               class="img-fluid rounded shadow-sm">
          <h3 class="h6 mt-3">{html.escape(member.get('name', ''))}</h3>
          <p class="text-muted">{html.escape(member.get('description', ''))}</p>
        </article>"""
        
        team_html = f"""
  <section class="section" id="team">
    <div class="container">
      <span class="eyebrow">团队</span>
      <h2 class="h3">核心团队</h2>
      <div class="row g-4">
        {team_cards}
      </div>
    </div>
  </section>"""
    
    # 生成成就/数据区块
    metrics_html = ""
    if content_data.get('achievements'):
        metric_cards = ""
        for achievement in content_data['achievements']:
            metric_cards += f"""
        <div class="col-md-3">
          <div class="feature-card glass p-4 reveal" data-tilt>
            <div class="display-6 fw-bold">{html.escape(str(achievement.get('value', '')))}</div>
            <div class="text-muted mt-2">{html.escape(achievement.get('label', ''))}</div>
          </div>
        </div>"""
        
        metrics_html = f"""
  <section class="section section-sm">
    <div class="container">
      <div class="row g-4 text-center">
        {metric_cards}
      </div>
    </div>
  </section>"""
    
    # 使用实际联系信息
    contact_email = ctx.get('email', 'hello@example.com')
    
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(brand)} · 关于我们</title>
  <link rel="stylesheet" href="assets/css/style.css" />
</head>
<body>

  <header class="hero hero-minimal section" id="home">
    <div class="container hero-inner">
      <span class="tagline">{html.escape(brand)}</span>
      <h1 class="display-4">{html.escape(content_data.get('headline', f'了解{brand}'))}</h1>
      <p class="section-lead">{html.escape(content_data.get('subtitle', ''))}</p>
    </div>
  </header>

  <main>
{metrics_html}
{story_html}
{values_html}
{team_html}

    <section class="section" id="cta">
      <div class="container">
        <div class="cta-card reveal text-center">
          <h2 class="h3">{html.escape(content_data.get('cta_title', '与我们合作'))}</h2>
          <p class="text-muted">{html.escape(content_data.get('cta_text', '期待与您的合作'))}</p>
          <a class="btn btn-primary btn-lg" href="contact.html">联系我们</a>
        </div>
      </div>
    </section>
  </main>

  <footer class="footer-minimal">
    <div class="container">
      <div class="footer-brand">
        <span>{html.escape(brand)}</span>
        <p>{html.escape(ctx.get('footer_text', '与我们一起创造价值'))}</p>
      </div>
      <div class="footer-meta">
        <span>© {html.escape(brand)}</span>
        <a href="mailto:{html.escape(contact_email)}">{html.escape(contact_email)}</a>
      </div>
    </div>
  </footer>
  <script src="assets/js/main.js"></script>
</body>
</html>"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    
    return f"关于页面已创建：{file_path}"


def _generate_about_defaults(brand: str, context: Dict) -> Dict:
    """生成关于页面的智能默认内容"""
    description = str(context.get('description', '')).lower()
    
    # 根据描述生成合适的内容
    if '咖啡' in description or 'coffee' in description:
        return {
            'headline': f'{brand} 的故事',
            'subtitle': '用心制作每一杯咖啡，创造温暖的社区空间',
            'story': {
                'title': '从一粒咖啡豆开始',
                'content': f'{brand}始于对咖啡的热爱。我们相信一杯好咖啡不仅是味觉享受，更是生活态度的体现。',
                'image_topic': 'coffee roasting process'
            },
            'values': [
                '精选全球优质咖啡豆',
                '坚持手工烘焙与冲泡',
                '营造温馨舒适的环境',
                '支持可持续发展'
            ],
            'team': [
                {
                    'name': context.get('founder_name', '创始人'),
                    'role': '创始人/首席咖啡师',
                    'description': '10年咖啡行业经验，Q-Grader认证',
                    'image_topic': 'coffee master at work'
                }
            ],
            'achievements': [
                {'value': context.get('years', '5') + '年', 'label': '品牌历程'},
                {'value': '1000+', 'label': '每日服务顾客'},
                {'value': '20+', 'label': '咖啡品种'},
                {'value': '98%', 'label': '顾客满意度'}
            ],
            'cta_title': '欢迎来店品尝',
            'cta_text': '体验我们的咖啡文化'
        }
    else:
        # 通用企业默认内容
        return {
            'headline': f'关于{brand}',
            'subtitle': context.get('mission', '致力于提供优质的产品与服务'),
            'story': {
                'title': '我们的使命',
                'content': context.get('story', f'{brand}专注于为客户创造价值，通过创新和品质赢得信任。'),
                'image_topic': 'modern office team'
            },
            'values': [
                '客户至上',
                '持续创新',
                '品质保证',
                '团队协作'
            ],
            'team': [],
            'achievements': [
                {'value': '100+', 'label': '服务客户'},
                {'value': '50+', 'label': '成功案例'},
                {'value': '10+', 'label': '专业团队'},
                {'value': '5星', 'label': '客户评价'}
            ],
            'cta_title': '开始合作',
            'cta_text': '让我们一起实现目标'
        }


def create_contact_page(
    file_path: str, 
    project_name: str | None = None,
    context: Dict[str, Any] | None = None,
    ai_content: Dict[str, Any] | None = None
) -> str:
    """创建"联系我们"页面 - 使用真实联系信息
    
    Args:
        file_path: 目标HTML文件路径
        project_name: 项目名称
        context: 包含实际联系信息的上下文
        ai_content: AI 生成的文案内容（可选）
    """
    brand = (project_name or "Modern Brand").strip()
    ctx = context or {}
    
    # 获取实际联系信息
    contact_info = {
        'address': ctx.get('address', '请在context中提供address'),
        'phone': ctx.get('phone', '请在context中提供phone'),
        'email': ctx.get('email', f'contact@{brand.lower().replace(" ", "")}.com'),
        'hours': ctx.get('business_hours', '周一至周五 9:00-18:00'),
        'wechat': ctx.get('wechat', ''),
        'social_media': ctx.get('social_media', {})
    }
    
    # 使用 AI 内容或默认文案
    if ai_content:
        content_data = ai_content
    else:
        content_data = {
            'headline': f'联系{brand}',
            'subtitle': '我们期待听到您的声音',
            'form_title': '发送消息',
            'form_text': '请留下您的联系方式和需求，我们会尽快回复',
            'response_time': '我们通常在24小时内回复'
        }
    
    # 生成社交媒体链接
    social_links = ""
    if contact_info['social_media']:
        for platform, link in contact_info['social_media'].items():
            social_links += f"""
        <a class="btn btn-outline-light btn-sm" href="{html.escape(link)}">
          {html.escape(platform)}
        </a>"""
    
    # 生成营业时间详情
    hours_detail = ""
    if isinstance(contact_info['hours'], dict):
        for day, time in contact_info['hours'].items():
            hours_detail += f"<li>{html.escape(day)}: {html.escape(time)}</li>\n"
    else:
        hours_detail = f"<li>{html.escape(contact_info['hours'])}</li>"
    
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(brand)} · 联系我们</title>
  <link rel="stylesheet" href="assets/css/style.css" />
</head>
<body>
  <header class="hero hero-ultra section text-center" 
          data-bg-topic="{ctx.get('hero_bg_topic', 'modern office reception')}" 
          id="home">
    <div class="container hero-inner">
      <span class="badge badge-soft mb-3">Contact</span>
      <h1 class="display-5 mb-2">{html.escape(content_data.get('headline', f'联系{brand}'))}</h1>
      <p class="section-lead mx-auto">{html.escape(content_data.get('subtitle', ''))}</p>
    </div>
  </header>

  <main>
    <section class="section">
      <div class="container">
        <div class="row g-4">
          <div class="col-md-5">
            <div class="contact-info-card reveal">
              <h2 class="h4 mb-3">联系方式</h2>
              <ul class="list-unstyled text-muted">
                <li class="mb-2">
                  <strong>地址</strong>：{html.escape(contact_info['address'])}
                </li>
                <li class="mb-2">
                  <strong>电话</strong>：{html.escape(contact_info['phone'])}
                </li>
                <li class="mb-2">
                  <strong>邮箱</strong>：{html.escape(contact_info['email'])}
                </li>
                {f'<li class="mb-2"><strong>微信</strong>：{html.escape(contact_info["wechat"])}</li>' if contact_info['wechat'] else ''}
              </ul>
              
              <h3 class="h5 mt-4 mb-2">营业时间</h3>
              <ul class="list-unstyled text-muted">
                {hours_detail}
              </ul>
              
              {f'<div class="d-flex gap-2 mt-3">{social_links}</div>' if social_links else ''}
            </div>
          </div>
          
          <div class="col-md-7">
            <h2 class="h4 mb-3">{html.escape(content_data.get('form_title', '发送消息'))}</h2>
            <p class="text-muted mb-3">{html.escape(content_data.get('form_text', ''))}</p>
            
            <form class="contact-form reveal" action="{ctx.get('form_action', '#')}" method="POST">
              <div class="field-pair">
                <label>姓名 *</label>
                <input type="text" name="name" placeholder="您的名字" required>
              </div>
              <div class="field-pair">
                <label>邮箱 *</label>
                <input type="email" name="email" placeholder="name@example.com" required>
              </div>
              <div class="field-pair">
                <label>电话</label>
                <input type="tel" name="phone" placeholder="您的联系电话">
              </div>
              <div class="field-pair">
                <label>主题</label>
                <select name="subject">
                  <option>一般咨询</option>
                  <option>商务合作</option>
                  <option>预约/预订</option>
                  <option>意见反馈</option>
                  <option>其他</option>
                </select>
              </div>
              <div class="field-pair">
                <label>留言 *</label>
                <textarea name="message" rows="4" 
                          placeholder="请描述您的需求或问题" required></textarea>
              </div>
              <p class="text-muted small">{html.escape(content_data.get('response_time', ''))}</p>
              <button class="btn btn-primary" type="submit">发送消息</button>
            </form>
          </div>
        </div>
      </div>
    </section>

    {_generate_map_section(contact_info['address']) if ctx.get('show_map', False) else ''}
    
    <section class="section section-alt">
      <div class="container">
        <h2 class="h3 text-center mb-4">常见问题</h2>
        <div class="mx-auto" style="max-width: 700px;">
          <details class="feature-card mb-3">
            <summary class="fw-semibold">如何到达？</summary>
            <div class="mt-2 text-muted">
              {html.escape(ctx.get('directions', f'我们位于{contact_info["address"]}，交通便利。'))}
            </div>
          </details>
          <details class="feature-card mb-3">
            <summary class="fw-semibold">是否提供停车位？</summary>
            <div class="mt-2 text-muted">
              {html.escape(ctx.get('parking_info', '提供免费停车位，请咨询工作人员。'))}
            </div>
          </details>
          <details class="feature-card mb-3">
            <summary class="fw-semibold">是否需要预约？</summary>
            <div class="mt-2 text-muted">
              {html.escape(ctx.get('reservation_info', '建议提前预约以确保最佳服务体验。'))}
            </div>
          </details>
        </div>
      </div>
    </section>
  </main>

  <footer class="footer-minimal">
    <div class="container">
      <div class="footer-brand">
        <span>{html.escape(brand)}</span>
        <p>期待与您见面</p>
      </div>
      <div class="footer-meta">
        <span>© {html.escape(brand)}</span>
        <a href="mailto:{html.escape(contact_info['email'])}">{html.escape(contact_info['email'])}</a>
      </div>
    </div>
  </footer>
  <script src="assets/js/main.js"></script>
</body>
</html>"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    
    return f"联系页面已创建：{file_path}"


def _generate_map_section(address: str) -> str:
    """生成地图区块（可选）"""
    return f"""
    <section class="section">
      <div class="container">
        <h2 class="h3 text-center mb-4">位置地图</h2>
        <div class="feature-card glass p-3 reveal" 
             data-bg-topic="city map with location pin" 
             style="height:400px; border-radius: var(--radius-lg);" 
             aria-label="地图显示：{html.escape(address)}">
          <div class="text-center" style="padding-top: 180px;">
            <p class="text-muted">地图加载中...</p>
            <p class="text-muted small">{html.escape(address)}</p>
          </div>
        </div>
      </div>
    </section>"""


# 保留原有的 create_html_file 函数以保证兼容性
from .html_templates import create_html_file


__all__ = [
    "create_html_file",
    "create_menu_page", 
    "create_about_page",
    "create_contact_page",
]